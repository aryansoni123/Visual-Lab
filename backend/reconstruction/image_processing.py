"""
Image Processing Module: 2D Orthographic View Vectorization

Pipeline:
1. Grayscale input
2. Adaptive threshold (binarize)
3. Canny edge detection
4. Probabilistic Hough line detection
5. Cluster segments by collinearity (angle + distance to line)
6. Fit global line per cluster via least squares
7. Sort segments along fitted line
8. Measure gap statistics
9. Classify: solid (continuous) vs hidden (dashed)
10. Extract 2D vertex/edge graph with visibility metadata

Input: Image file (JPG, PNG)
Output: (vertices, edges, edge_visibility)
  - vertices: list of (x, y) tuples
  - edges: list of (i, j) vertex index pairs
  - edge_visibility: list of bools (True=visible, False=hidden)
"""

import cv2
import numpy as np
from itertools import combinations

TOL = 1e-6
ANGLE_TOL = np.radians(2)  # 2 degrees for collinearity
DISTANCE_TOL = 2.0  # pixels, for distance to line
GAP_RATIO_THRESHOLD = 0.3  # gap/segment > 0.3 → dashed


class LineSegment:
    """Represents a detected line segment."""
    def __init__(self, x1, y1, x2, y2):
        self.p1 = np.array([x1, y1], dtype=float)
        self.p2 = np.array([x2, y2], dtype=float)
        self.length = np.linalg.norm(self.p2 - self.p1)
        
        # Direction vector (unit)
        if self.length > TOL:
            self.direction = (self.p2 - self.p1) / self.length
        else:
            self.direction = np.array([1.0, 0.0])
    
    def midpoint(self):
        return (self.p1 + self.p2) / 2
    
    def angle(self):
        """Angle of line in radians [-pi/2, pi/2]."""
        return np.arctan2(self.direction[1], self.direction[0])
    
    def distance_to_point(self, point):
        """Perpendicular distance from point to infinite line."""
        # Line through p1, p2; distance from point to line
        v = self.p2 - self.p1
        if np.linalg.norm(v) < TOL:
            return np.linalg.norm(point - self.p1)
        
        # ||(p - p1) - ((p - p1) · v / ||v||^2) v||
        w = point - self.p1
        c1 = np.dot(w, v)
        c2 = np.dot(v, v)
        
        if c2 < TOL:
            return np.linalg.norm(w)
        
        projection_length = c1 / c2
        projection = self.p1 + projection_length * v
        
        return np.linalg.norm(point - projection)
    
    def project_onto_line(self, point):
        """Project point onto infinite line, return coordinate along line."""
        v = self.p2 - self.p1
        if np.linalg.norm(v) < TOL:
            return 0.0
        
        w = point - self.p1
        t = np.dot(w, v) / np.dot(v, v)
        return t
    
    def __repr__(self):
        return f"LineSegment({self.p1[0]:.1f},{self.p1[1]:.1f})-({self.p2[0]:.1f},{self.p2[1]:.1f})"


def normalize_angle(angle):
    """Normalize angle to [-pi/2, pi/2] for comparison."""
    while angle > np.pi / 2:
        angle -= np.pi
    while angle < -np.pi / 2:
        angle += np.pi
    return angle


def angles_are_similar(angle1, angle2, tolerance=ANGLE_TOL):
    """Check if two angles are similar (account for 180° symmetry)."""
    angle1 = normalize_angle(angle1)
    angle2 = normalize_angle(angle2)
    diff = abs(angle1 - angle2)
    return diff < tolerance or abs(diff - np.pi) < tolerance


def detect_lines_from_image(image_path, min_line_length=20, max_line_gap=10):
    """
    Detect line segments from image using Canny + Probabilistic Hough.
    
    Args:
        image_path: Path to image file
        min_line_length: Minimum line length in pixels
        max_line_gap: Maximum gap to bridge collinear segments
    
    Returns:
        list of LineSegment objects
    """
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptive threshold (binarize)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Canny edge detection
    edges = cv2.Canny(binary, 50, 150)
    
    # Probabilistic Hough line detection
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50,
                           minLineLength=min_line_length, maxLineGap=max_line_gap)
    
    if lines is None:
        return []
    
    # Convert to LineSegment objects
    segments = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        segments.append(LineSegment(x1, y1, x2, y2))
    
    return segments


def cluster_collinear_segments(segments, angle_tol=ANGLE_TOL, distance_tol=DISTANCE_TOL):
    """
    Cluster segments by collinearity (similar angle + close distance to line).
    
    Args:
        segments: list of LineSegment objects
        angle_tol: angle tolerance in radians
        distance_tol: perpendicular distance tolerance in pixels
    
    Returns:
        list of clusters, each cluster is a list of LineSegment objects
    """
    if not segments:
        return []
    
    clusters = []
    used = set()
    
    for i, seg in enumerate(segments):
        if i in used:
            continue
        
        # Start new cluster with this segment
        cluster = [seg]
        used.add(i)
        
        # Find all collinear segments
        for j in range(i + 1, len(segments)):
            if j in used:
                continue
            
            other = segments[j]
            
            # Check angle similarity
            if not angles_are_similar(seg.angle(), other.angle(), angle_tol):
                continue
            
            # Check distance to line
            if seg.distance_to_point(other.p1) > distance_tol:
                continue
            if seg.distance_to_point(other.p2) > distance_tol:
                continue
            
            # This segment is collinear
            cluster.append(other)
            used.add(j)
        
        clusters.append(cluster)
    
    return clusters


def fit_line_to_cluster(cluster):
    """
    Fit a least-squares line to cluster endpoints.
    
    Args:
        cluster: list of LineSegment objects
    
    Returns:
        normal: unit normal to line (nx, ny)
        d: scalar in equation nx*x + ny*y = d
    """
    if not cluster:
        return None, None
    
    # Collect all endpoints
    points = []
    for seg in cluster:
        points.append(seg.p1)
        points.append(seg.p2)
    
    points = np.array(points)
    
    # Fit line via PCA
    mean = points.mean(axis=0)
    centered = points - mean
    
    # Covariance matrix
    cov = np.cov(centered.T)
    
    # Eigenvector with smallest eigenvalue is normal
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    normal = eigenvectors[:, 0]  # Smallest eigenvalue
    
    # Normalize
    normal = normal / np.linalg.norm(normal)
    
    # Compute d: normal · mean = d
    d = np.dot(normal, mean)
    
    return normal, d


def sort_segments_along_line(cluster, normal, d):
    """
    Sort segments in cluster by their position along the fitted line.
    
    Args:
        cluster: list of LineSegment objects
        normal: unit normal to line
        d: scalar in line equation
    
    Returns:
        list of segments sorted by position
    """
    # Direction along line (perpendicular to normal)
    direction = np.array([-normal[1], normal[0]])
    
    # Compute position of each segment along line
    positions = []
    for seg in cluster:
        mid = seg.midpoint()
        # Project midpoint onto line direction
        pos = np.dot(mid, direction)
        positions.append(pos)
    
    # Sort segments by position
    sorted_indices = np.argsort(positions)
    return [cluster[i] for i in sorted_indices]


def measure_gap_statistics(sorted_cluster):
    """
    Measure gap and segment lengths in sorted cluster.
    
    Args:
        sorted_cluster: list of LineSegment objects (sorted along line)
    
    Returns:
        (mean_segment_length, mean_gap_length, gap_ratio)
    """
    if len(sorted_cluster) < 2:
        return None, None, None
    
    # Segment lengths
    segment_lengths = [seg.length for seg in sorted_cluster]
    mean_segment = np.mean(segment_lengths)
    
    # Gap lengths (distance between consecutive segments)
    gaps = []
    for i in range(len(sorted_cluster) - 1):
        seg1 = sorted_cluster[i]
        seg2 = sorted_cluster[i + 1]
        
        # Distance from end of seg1 to start of seg2
        dist = np.linalg.norm(seg2.p1 - seg1.p2)
        gaps.append(dist)
    
    if gaps:
        mean_gap = np.mean(gaps)
    else:
        mean_gap = 0.0
    
    # Gap ratio
    if mean_segment > TOL:
        gap_ratio = mean_gap / mean_segment
    else:
        gap_ratio = 0.0
    
    return mean_segment, mean_gap, gap_ratio


def classify_clusters(clusters):
    """
    Classify each cluster as solid or hidden (dashed).
    
    Args:
        clusters: list of segment clusters
    
    Returns:
        list of (cluster, is_solid) tuples
    """
    classified = []
    
    for cluster in clusters:
        if len(cluster) == 1:
            # Single segment → solid
            classified.append((cluster, True))
            continue
        
        # Fit line to cluster
        normal, d = fit_line_to_cluster(cluster)
        if normal is None:
            classified.append((cluster, True))
            continue
        
        # Sort along line
        sorted_cluster = sort_segments_along_line(cluster, normal, d)
        
        # Measure gaps
        mean_seg, mean_gap, gap_ratio = measure_gap_statistics(sorted_cluster)
        
        # Classify
        if gap_ratio is None or gap_ratio < GAP_RATIO_THRESHOLD:
            # Solid (continuous or very small gaps)
            classified.append((cluster, True))
        else:
            # Hidden (dashed, periodic gaps)
            classified.append((cluster, False))
    
    return classified


def extract_vertices_from_segments(segments):
    """
    Extract unique vertices from line segments.
    
    Args:
        segments: list of LineSegment objects
    
    Returns:
        (vertices, vertex_index_map)
        - vertices: list of (x, y) tuples
        - vertex_index_map: dict mapping (x, y) → index
    """
    vertex_set = {}
    vertices = []
    
    for seg in segments:
        for point in [seg.p1, seg.p2]:
            # Round to avoid floating-point duplicates
            key = (round(point[0], 1), round(point[1], 1))
            
            if key not in vertex_set:
                vertex_set[key] = len(vertices)
                vertices.append(tuple(point))
    
    return vertices, vertex_set


def extract_edges_from_segments(segments, vertex_map):
    """
    Extract edges from line segments using vertex map.
    
    Args:
        segments: list of LineSegment objects
        vertex_map: dict mapping (x, y) → index
    
    Returns:
        list of (i, j) edge pairs
    """
    edges = []
    
    for seg in segments:
        key1 = (round(seg.p1[0], 1), round(seg.p1[1], 1))
        key2 = (round(seg.p2[0], 1), round(seg.p2[1], 1))
        
        i = vertex_map[key1]
        j = vertex_map[key2]
        
        # Avoid duplicate edges
        edge = (min(i, j), max(i, j))
        if edge not in edges:
            edges.append(edge)
    
    return edges


def image_to_2d_graph(image_path, min_line_length=20, max_line_gap=10):
    """
    Convert image to 2D orthographic graph.
    
    Args:
        image_path: Path to image
        min_line_length: Minimum line length (pixels)
        max_line_gap: Maximum gap to bridge (pixels)
    
    Returns:
        (vertices, edges, edge_visibility)
        - vertices: list of (x, y) tuples
        - edges: list of (i, j) index pairs
        - edge_visibility: list of bools (True=visible, False=hidden)
    """
    # Step 1: Detect line segments
    segments = detect_lines_from_image(image_path, min_line_length, max_line_gap)
    
    if not segments:
        return [], [], []
    
    # Step 2: Cluster by collinearity
    clusters = cluster_collinear_segments(segments)
    
    # Step 3: Classify solid vs hidden
    classified = classify_clusters(clusters)
    
    # Step 4: Extract vertices
    all_segments = [seg for cluster in [c[0] for c in classified] for seg in cluster]
    vertices, vertex_map = extract_vertices_from_segments(all_segments)
    
    # Step 5: Extract edges with visibility
    edges = []
    edge_visibility = []
    
    for cluster, is_solid in classified:
        cluster_edges = extract_edges_from_segments(cluster, vertex_map)
        for edge in cluster_edges:
            edges.append(edge)
            edge_visibility.append(is_solid)
    
    return vertices, edges, edge_visibility


def process_three_views(front_image, top_image, side_image):
    """
    Process three orthographic view images.
    
    Args:
        front_image: Path to front view image
        top_image: Path to top view image
        side_image: Path to side view image
    
    Returns:
        {
            'front': (vertices, edges, edge_visibility),
            'top': (vertices, edges, edge_visibility),
            'side': (vertices, edges, edge_visibility)
        }
    """
    results = {}
    
    for view_name, image_path in [
        ('front', front_image),
        ('top', top_image),
        ('side', side_image)
    ]:
        try:
            vertices, edges, visibility = image_to_2d_graph(image_path)
            results[view_name] = (vertices, edges, visibility)
            print(f"✓ {view_name.upper()}: {len(vertices)} vertices, {len(edges)} edges")
        except Exception as e:
            print(f"✗ {view_name.upper()}: {e}")
            results[view_name] = ([], [], [])
    
    return results


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    # Test placeholder (will use real images when available)
    print("Image processing module ready.")
    print("Usage: image_to_2d_graph(image_path) or process_three_views(front, top, side)")
