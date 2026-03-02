"""
Face Detection v5: Plane-Clustering Approach

Geometric principle:
- Faces are maximal planar vertex sets, not shortest cycles
- For each geometric plane: cluster vertices on that plane, extract boundary

Algorithm:
1. Generate plane hypotheses from all non-collinear vertex triples
2. For each plane: find all vertices lying on it (within tolerance)
3. Extract boundary cycle from induced subgraph of plane vertices
4. Validate: coplanarity, simple cycle, not already found
"""

import numpy as np
from itertools import combinations
from collections import defaultdict

TOL = 1e-6


def normalize_vector(v):
    """Normalize vector to unit length."""
    norm = np.linalg.norm(v)
    if norm < TOL:
        return v
    return v / norm


def compute_plane_equation(p1, p2, p3):
    """
    Compute plane equation from three points.
    
    Returns:
        normal: unit normal vector (nx, ny, nz)
        d: scalar in equation nx*x + ny*y + nz*z = d
        valid: bool, True if three points are non-collinear
    """
    # Vectors in the plane
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    
    # Normal = cross product
    normal = np.cross(v1, v2)
    
    # Check collinearity
    if np.linalg.norm(normal) < TOL:
        return None, None, False
    
    # Normalize
    normal = normalize_vector(normal)
    
    # Compute d: normal · p1 = d
    d = np.dot(normal, p1)
    
    # Ensure consistent orientation: normal points "outward" (positive z component, or if z~0, positive y, etc.)
    # For reproducibility, prefer first non-zero component positive
    for component in normal:
        if abs(component) > TOL:
            if component < 0:
                normal = -normal
                d = -d
            break
    
    return normal, d, True


def plane_to_key(normal, d):
    """
    Convert plane (normal, d) to hashable key for deduplication.
    
    Rounds to avoid floating-point differences.
    """
    normal = tuple(np.round(normal, decimals=6))
    d = round(d, 6)
    return (normal, d)


def point_distance_to_plane(point, normal, d):
    """Distance from point to plane (signed)."""
    return abs(np.dot(normal, point) - d)


def cluster_vertices_to_plane(Lambda, normal, d):
    """
    Find all vertex indices in Lambda that lie on the plane.
    
    Args:
        Lambda: list of [x, y, z, ...]
        normal: unit normal vector
        d: scalar
    
    Returns:
        list of vertex indices
    """
    indices = []
    for i, vertex in enumerate(Lambda):
        point = np.array(vertex[:3])
        dist = point_distance_to_plane(point, normal, d)
        if dist < TOL:
            indices.append(i)
    return indices


def build_adjacency_from_edges(vertex_indices, Theta):
    """
    Build adjacency list for vertices in vertex_indices using edges from Theta.
    
    Args:
        vertex_indices: set of vertex indices to include
        Theta: list of (u, v) edge tuples
    
    Returns:
        dict: vertex -> [neighbors]
    """
    adj = defaultdict(list)
    vertex_set = set(vertex_indices)
    
    for u, v in Theta:
        if u in vertex_set and v in vertex_set:
            if v not in adj[u]:
                adj[u].append(v)
            if u not in adj[v]:
                adj[v].append(u)
    
    return adj


def dfs_find_cycle_from_edge(start, neighbor, adjacency, visited_path=None):
    """
    DFS to find a simple cycle starting from edge (start, neighbor).
    
    Returns:
        list: cycle (vertex sequence), or None if no cycle found
    """
    if visited_path is None:
        visited_path = [start]
    
    current = neighbor
    
    while True:
        if current in visited_path:
            # Found a cycle
            if current == start:
                # Valid cycle back to start
                return visited_path[visited_path.index(start):]
            else:
                # Not a cycle back to start
                return None
        
        visited_path.append(current)
        
        # Find next neighbor (not the previous one)
        neighbors = adjacency[current]
        prev = visited_path[-2] if len(visited_path) > 1 else None
        
        next_neighbors = [n for n in neighbors if n != prev]
        
        if len(next_neighbors) == 0:
            return None  # Dead end
        
        if len(next_neighbors) > 1:
            # Ambiguous; try to pick the one that continues smoothly
            # For now, just pick first
            pass
        
        current = next_neighbors[0]


def extract_boundary_cycle(vertex_indices, Theta):
    """
    Extract the boundary cycle from induced subgraph.
    
    For a valid face: induced subgraph should be a simple cycle.
    
    Args:
        vertex_indices: list of vertices on the plane
        Theta: full edge list
    
    Returns:
        list: boundary cycle (vertex indices in order), or None if not a simple cycle
    """
    if len(vertex_indices) < 3:
        return None
    
    # Build adjacency for this subgraph
    adj = build_adjacency_from_edges(vertex_indices, Theta)
    
    # Check if every vertex has degree 2 (necessary for a simple cycle)
    for v in vertex_indices:
        if len(adj[v]) != 2:
            return None
    
    # Start from first vertex
    start = vertex_indices[0]
    neighbors = adj[start]
    
    # Walk the cycle
    cycle = [start]
    current = neighbors[0]
    prev = start
    
    while current != start:
        cycle.append(current)
        next_candidates = [n for n in adj[current] if n != prev]
        if len(next_candidates) != 1:
            return None  # Not a simple cycle
        prev = current
        current = next_candidates[0]
    
    return cycle


def validate_face(cycle, Lambda, normal, d):
    """
    Validate that a cycle forms a valid planar face.
    
    Checks:
    - All vertices coplanar
    - At least 3 vertices
    - Not collinear
    
    Args:
        cycle: list of vertex indices
        Lambda: vertex coordinates
        normal: plane normal
        d: plane scalar
    
    Returns:
        bool: True if valid face
    """
    if len(cycle) < 3:
        return False
    
    # Check all vertices coplanar
    for idx in cycle:
        point = np.array(Lambda[idx][:3])
        dist = point_distance_to_plane(point, normal, d)
        if dist > TOL:
            return False
    
    # Check not collinear (compute polygon normal)
    p0 = np.array(Lambda[cycle[0]][:3])
    p1 = np.array(Lambda[cycle[1]][:3])
    p2 = np.array(Lambda[cycle[2]][:3])
    
    v1 = p1 - p0
    v2 = p2 - p0
    poly_normal = np.cross(v1, v2)
    
    if np.linalg.norm(poly_normal) < TOL:
        return False  # Collinear vertices
    
    return True


def find_all_faces_by_planes(Lambda, Theta):
    """
    Find all faces using plane clustering approach.
    
    Algorithm:
    1. Generate plane hypotheses from all non-collinear triples
    2. For each plane: cluster vertices, extract boundary
    3. Deduplicate and validate
    
    Args:
        Lambda: list of [x, y, z, front_idx, top_idx, side_idx]
        Theta: list of (u, v) edges
    
    Returns:
        list of faces (each face is a list of vertex indices)
    """
    if len(Lambda) < 3:
        return []
    
    faces = []
    tried_planes = set()
    
    # Generate plane hypotheses
    num_vertices = len(Lambda)
    
    for i, j, k in combinations(range(num_vertices), 3):
        p1 = np.array(Lambda[i][:3])
        p2 = np.array(Lambda[j][:3])
        p3 = np.array(Lambda[k][:3])
        
        normal, d, valid = compute_plane_equation(p1, p2, p3)
        
        if not valid:
            continue  # Collinear points
        
        # Deduplicate planes
        plane_key = plane_to_key(normal, d)
        if plane_key in tried_planes:
            continue
        tried_planes.add(plane_key)
        
        # Cluster vertices on this plane
        plane_vertices = cluster_vertices_to_plane(Lambda, normal, d)
        
        if len(plane_vertices) < 3:
            continue  # Not enough vertices for a face
        
        # Extract boundary cycle
        cycle = extract_boundary_cycle(plane_vertices, Theta)
        
        if cycle is None or len(cycle) < 3:
            continue
        
        # Validate face
        if not validate_face(cycle, Lambda, normal, d):
            continue
        
        # Check for duplicates (same face in different orientation)
        cycle_normalized = tuple(sorted(cycle))
        is_duplicate = False
        for existing_face in faces:
            existing_normalized = tuple(sorted(existing_face))
            if cycle_normalized == existing_normalized:
                is_duplicate = True
                break
        
        if not is_duplicate:
            faces.append(cycle)
    
    return faces


def triangulate_polygon(face, Lambda):
    """
    Triangulate a planar polygon using fan triangulation.
    
    Args:
        face: list of vertex indices (in order)
        Lambda: vertex coordinates
    
    Returns:
        list of triangles, each triangle is (i, j, k) vertex indices
    """
    if len(face) < 3:
        return []
    
    triangles = []
    for i in range(1, len(face) - 1):
        triangles.append((face[0], face[i], face[i + 1]))
    
    return triangles


def compute_face_normal(triangle, Lambda):
    """Compute outward normal of a triangle."""
    i, j, k = triangle
    p0 = np.array(Lambda[i][:3])
    p1 = np.array(Lambda[j][:3])
    p2 = np.array(Lambda[k][:3])
    
    v1 = p1 - p0
    v2 = p2 - p0
    
    normal = np.cross(v1, v2)
    norm = np.linalg.norm(normal)
    
    if norm < TOL:
        return np.array([0, 0, 1])  # Degenerate
    
    return normal / norm


def validate_euler_formula(num_vertices, num_edges, num_faces):
    """Check Euler formula: V - E + F = 2 for closed polyhedra."""
    euler = num_vertices - num_edges + num_faces
    return euler == 2


def export_stl(filename, triangles, Lambda):
    """Export faces to ASCII STL format."""
    with open(filename, 'w') as f:
        f.write(f"solid object\n")
        
        for triangle in triangles:
            normal = compute_face_normal(triangle, Lambda)
            
            f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
            f.write(f"    outer loop\n")
            
            for vertex_idx in triangle:
                x, y, z = Lambda[vertex_idx][:3]
                f.write(f"      vertex {x} {y} {z}\n")
            
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        
        f.write(f"endsolid object\n")


# ============================================================================
# Test: Cube
# ============================================================================

if __name__ == "__main__":
    # Test cube from pseudo_wireframe.py
    Lambda = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0],
        [0.0, 3.0, 0.0],
        [0.0, 3.0, 2.0],
        [5.0, 0.0, 0.0],
        [5.0, 0.0, 2.0],
        [5.0, 3.0, 0.0],
        [5.0, 3.0, 2.0],
    ]
    
    Theta = [
        (0, 1),
        (0, 2),
        (0, 4),
        (1, 3),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 7),
        (4, 5),
        (4, 6),
        (5, 7),
        (6, 7),
    ]
    
    print("=" * 70)
    print("FACE DETECTION v5: PLANE CLUSTERING APPROACH")
    print("=" * 70)
    
    print("\nStep 1: Finding faces by plane clustering...")
    faces = find_all_faces_by_planes(Lambda, Theta)
    
    print(f"Found {len(faces)} faces:")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {len(face)}-gon {face}")
    
    print("\nStep 2: Triangulating faces...")
    triangles = []
    for face in faces:
        triangles.extend(triangulate_polygon(face, Lambda))
    
    print(f"Total triangles: {len(triangles)}")
    
    print("\nStep 3: Validating Euler formula...")
    num_v = len(Lambda)
    num_e = len(Theta)
    num_f = len(faces)
    
    euler_valid = validate_euler_formula(num_v, num_e, num_f)
    print(f"V={num_v}, E={num_e}, F={num_f}")
    print(f"V - E + F = {num_v - num_e + num_f} (valid: {euler_valid})")
    
    if euler_valid:
        print("\n✓ Euler formula valid for closed polyhedron")
        
        print("\nStep 4: Exporting STL...")
        export_stl("test_cube_v5.stl", triangles, Lambda)
        print("✓ Exported to test_cube_v5.stl")
    else:
        print("\n✗ Euler formula INVALID - face detection failed")
