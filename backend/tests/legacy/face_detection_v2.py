# =========================================================
# FACE DETECTION FROM 3D WIREFRAME (V2)
# Using: Half-Edge Face Walking on Polyhedron
# 
# Key Insight:
# In a closed polyhedron (2-manifold), each directed edge
# belongs to exactly ONE face. Face walking deterministically
# traces faces by following geometric ordering around vertices.
# =========================================================

import numpy as np
from collections import defaultdict

TOL = 1e-6


# =========================================================
# ============== GEOMETRIC UTILITIES ======================
# =========================================================

def compute_vertex_normal(vertex, neighbors, lambda_vertices):
    """
    Approximate normal at vertex using neighboring vertices.
    
    This is used to define the plane for angular ordering.
    """
    neighbors_coords = np.array([lambda_vertices[n] for n in neighbors])
    vertex_coord = np.array(lambda_vertices[vertex])
    
    # Compute vectors to neighbors
    vectors = neighbors_coords - vertex_coord
    
    # Average cross products to approximate normal
    normal = np.zeros(3)
    for i in range(len(vectors)):
        v1 = vectors[i]
        v2 = vectors[(i + 1) % len(vectors)]
        normal += np.cross(v1, v2)
    
    norm = np.linalg.norm(normal)
    if norm > TOL:
        normal = normal / norm
    else:
        normal = np.array([0, 0, 1])
    
    return normal


def angle_between_edges_at_vertex(vertex, v1, v2, lambda_vertices):
    """
    Compute signed angle from edge (vertex→v1) to edge (vertex→v2).
    Positive angle is counterclockwise when viewed from above.
    """
    vertex_coord = np.array(lambda_vertices[vertex])
    v1_coord = np.array(lambda_vertices[v1])
    v2_coord = np.array(lambda_vertices[v2])
    
    vec1 = v1_coord - vertex_coord
    vec2 = v2_coord - vertex_coord
    
    # Compute angle using atan2
    angle1 = np.arctan2(vec1[1], vec1[0])
    angle2 = np.arctan2(vec2[1], vec2[0])
    
    angle_diff = angle2 - angle1
    
    # Normalize to [-pi, pi]
    while angle_diff > np.pi:
        angle_diff -= 2 * np.pi
    while angle_diff < -np.pi:
        angle_diff += 2 * np.pi
    
    return angle_diff


def sort_neighbors_by_angle(vertex, neighbors, lambda_vertices):
    """
    Sort neighbors around a vertex in angular order (counterclockwise from +x axis).
    
    Returns: sorted list of neighbor indices
    """
    if len(neighbors) <= 1:
        return neighbors
    
    vertex_coord = np.array(lambda_vertices[vertex])
    
    # Compute angle for each neighbor relative to +x axis
    angles = []
    for n in neighbors:
        n_coord = np.array(lambda_vertices[n])
        vec = n_coord - vertex_coord
        angle = np.arctan2(vec[1], vec[0])
        angles.append((n, angle))
    
    # Sort by angle
    angles.sort(key=lambda x: x[1])
    
    return [n for n, _ in angles]


# =========================================================
# ============= HALF-EDGE DATA STRUCTURE ====================
# =========================================================

class HalfEdgeGraph:
    """
    Represent polyhedron edges with geometric ordering.
    """
    
    def __init__(self, vertices, edges):
        """
        Args:
            vertices: list of 3D coordinates
            edges: list of (u, v) pairs
        """
        self.vertices = vertices
        self.edges = edges
        self.num_vertices = len(vertices)
        
        # Build adjacency list
        self.adjacency = defaultdict(list)
        for u, v in edges:
            self.adjacency[u].append(v)
            self.adjacency[v].append(u)
        
        # Remove duplicates and sort neighbors by angle
        self.ordered_neighbors = {}
        for vertex in range(self.num_vertices):
            neighbors = list(set(self.adjacency[vertex]))
            sorted_neighbors = sort_neighbors_by_angle(
                vertex, neighbors, vertices
            )
            self.ordered_neighbors[vertex] = sorted_neighbors
        
        # Track which half-edges have been used in faces
        self.visited_half_edges = set()
    
    def get_next_half_edge(self, u, v):
        """
        Given directed edge (u → v), return the next directed edge
        in the face boundary.
        
        At vertex v, find u in the ordered neighbor list.
        The next neighbor in circular order is w.
        Return (v → w).
        """
        neighbors = self.ordered_neighbors[v]
        
        if u not in neighbors:
            # This shouldn't happen in a valid 2-manifold
            return None
        
        idx = neighbors.index(u)
        next_neighbor = neighbors[(idx + 1) % len(neighbors)]
        
        return (v, next_neighbor)
    
    def walk_face(self, start_u, start_v):
        """
        Walk a face starting from directed edge (start_u → start_v).
        
        Returns: list of vertex indices forming the face, or None if invalid.
        """
        face = []
        current_u, current_v = start_u, start_v
        max_steps = self.num_vertices + 100  # Avoid infinite loops
        steps = 0
        
        while steps < max_steps:
            face.append(current_u)
            
            # Get next half-edge
            next_edge = self.get_next_half_edge(current_u, current_v)
            if next_edge is None:
                return None
            
            current_u, current_v = next_edge
            
            # Check if we've closed the face
            if current_u == start_u and current_v == start_v:
                return face
            
            steps += 1
        
        # Loop didn't close properly
        return None


# =========================================================
# ============== FACE DETECTION ==========================
# =========================================================

def detect_faces(lambda_vertices, theta_edges):
    """
    Extract all faces from a polyhedron using half-edge face walking.
    
    Args:
        lambda_vertices: list of 3D vertex coordinates
        theta_edges: list of (u, v) edge pairs
    
    Returns: list of faces, where each face is a list of vertex indices
    """
    graph = HalfEdgeGraph(lambda_vertices, theta_edges)
    faces = []
    
    print(f"Starting face detection with {len(lambda_vertices)} vertices and {len(theta_edges)} edges")
    
    # Try to walk a face from each half-edge
    for u, v in theta_edges:
        # Try direction (u → v)
        if (u, v) not in graph.visited_half_edges:
            face = graph.walk_face(u, v)
            if face is not None and len(face) >= 3:
                faces.append(face)
                # Mark all half-edges in this face as visited
                for i in range(len(face)):
                    v1 = face[i]
                    v2 = face[(i + 1) % len(face)]
                    graph.visited_half_edges.add((v1, v2))
        
        # Try direction (v → u)
        if (v, u) not in graph.visited_half_edges:
            face = graph.walk_face(v, u)
            if face is not None and len(face) >= 3:
                faces.append(face)
                # Mark all half-edges in this face as visited
                for i in range(len(face)):
                    v1 = face[i]
                    v2 = face[(i + 1) % len(face)]
                    graph.visited_half_edges.add((v1, v2))
    
    return faces


# =========================================================
# ============== MESH EXPORT ==============================
# =========================================================

def triangulate_polygon(polygon_indices, lambda_vertices):
    """
    Triangulate a planar polygon using fan triangulation.
    """
    if len(polygon_indices) < 3:
        return []
    
    triangles = []
    for i in range(1, len(polygon_indices) - 1):
        triangles.append([
            polygon_indices[0],
            polygon_indices[i],
            polygon_indices[i + 1]
        ])
    
    return triangles


def compute_face_normal(face_indices, lambda_vertices):
    """Compute normal vector for a face."""
    points = np.array([lambda_vertices[i] for i in face_indices])
    
    if len(points) < 3:
        return np.array([0, 0, 1])
    
    v1 = points[1] - points[0]
    v2 = points[2] - points[0]
    normal = np.cross(v1, v2)
    norm = np.linalg.norm(normal)
    
    if norm > TOL:
        return normal / norm
    return np.array([0, 0, 1])


def export_stl(faces, lambda_vertices, filename):
    """Export mesh to ASCII STL format."""
    triangles = []
    for face in faces:
        tris = triangulate_polygon(face, lambda_vertices)
        triangles.extend(tris)
    
    with open(filename, 'w') as f:
        f.write("solid mesh\n")
        
        for tri in triangles:
            v0 = np.array(lambda_vertices[tri[0]])
            v1 = np.array(lambda_vertices[tri[1]])
            v2 = np.array(lambda_vertices[tri[2]])
            
            # Compute normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            
            if norm > TOL:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1])
            
            # Write facet
            f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}\n")
            f.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
            f.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        
        f.write("endsolid mesh\n")


def validate_euler_formula(num_vertices, num_edges, num_faces):
    """Validate V - E + F = 2."""
    euler_char = num_vertices - num_edges + num_faces
    is_valid = abs(euler_char - 2) < 0.5
    return is_valid, euler_char


# =========================================================
# ===================== PIPELINE =========================
# =========================================================

def detect_faces_and_export(lambda_vertices, theta_edges, output_filename):
    """
    Complete pipeline: wireframe → faces → mesh → STL
    """
    print("\n" + "=" * 70)
    print("FACE DETECTION (Half-Edge Face Walking)")
    print("=" * 70)
    
    # Step 1: Detect faces
    print(f"\nStep 1: Walking faces...")
    faces = detect_faces(lambda_vertices, theta_edges)
    print(f"  Found {len(faces)} faces")
    
    # Step 2: Triangulate
    print(f"\nStep 2: Triangulating...")
    triangles = []
    for face in faces:
        tris = triangulate_polygon(face, lambda_vertices)
        triangles.extend(tris)
    print(f"  Total triangles: {len(triangles)}")
    
    # Step 3: Validate Euler
    print(f"\nStep 3: Validating Euler formula...")
    is_valid, euler_char = validate_euler_formula(
        len(lambda_vertices), len(theta_edges), len(faces)
    )
    print(f"  V={len(lambda_vertices)}, E={len(theta_edges)}, F={len(faces)}")
    print(f"  V - E + F = {euler_char} (valid: {is_valid})")
    
    # Step 4: Export STL
    print(f"\nStep 4: Exporting to STL...")
    export_stl(faces, lambda_vertices, output_filename)
    print(f"  Written to: {output_filename}")
    
    print("\n" + "=" * 70)
    return faces, triangles, is_valid, euler_char


# =========================================================
# ===================== TEST ==============================
# =========================================================

if __name__ == "__main__":
    from pseudo_wireframe import build_pseudo_wireframe
    
    front_vertices = [(0,0),(4,0),(4,3),(0,3)]
    front_edges = [(0,1),(1,2),(2,3),(3,0)]
    
    top_vertices = [(0,0),(4,0),(4,2),(0,2)]
    top_edges = [(0,1),(1,2),(2,3),(3,0)]
    
    side_vertices = [(0,0),(3,0),(3,2),(0,2)]
    side_edges = [(0,1),(1,2),(2,3),(3,0)]
    
    Lambda, Theta, _ = build_pseudo_wireframe(
        front_vertices, front_edges,
        top_vertices, top_edges,
        side_vertices, side_edges
    )
    
    lambda_coords = [[row[0], row[1], row[2]] for row in Lambda]
    
    print("\nTest: Cube Reconstruction")
    print(f"Input: {len(lambda_coords)} vertices, {len(Theta)} edges")
    
    faces, triangles, is_valid, euler = detect_faces_and_export(
        lambda_coords, Theta, "test_cube_v2.stl"
    )
    
    print("\nFaces found:")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {face}")
