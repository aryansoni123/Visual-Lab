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
from scipy.spatial import Delaunay

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


def ensure_outward_normals(triangles, Lambda):
    """
    Ensure all triangle normals point outward from mesh centroid.
    
    Flips triangle vertex order if normal points inward.
    
    Args:
        triangles: list of (i,j,k) vertex indices
        Lambda: vertices
    
    Returns:
        list of triangles with corrected orientation
    """
    # Compute mesh centroid
    points = np.array([v[:3] for v in Lambda])
    centroid = points.mean(axis=0)
    
    corrected = []
    for tri in triangles:
        i, j, k = tri
        p0 = np.array(Lambda[i][:3])
        p1 = np.array(Lambda[j][:3])
        p2 = np.array(Lambda[k][:3])
        
        # Triangle center
        tri_center = (p0 + p1 + p2) / 3
        
        # Vector from centroid to triangle center
        to_tri = tri_center - centroid
        
        # Current normal
        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)
        
        # Check if normal points outward
        dot_product = np.dot(normal, to_tri)
        
        if dot_product < 0:
            # Normal points inward → flip triangle
            corrected.append((i, k, j))
        else:
            # Normal points outward → keep as is
            corrected.append(tri)
    
    return corrected


def validate_euler_formula(num_vertices, num_edges, num_faces):
    """Check Euler formula: V - E + F = 2 for closed polyhedra."""
    euler = num_vertices - num_edges + num_faces
    return euler == 2


def generate_tetrahedral_mesh(Lambda, faces):
    """
    Generate tetrahedral mesh filling the interior volume.
    
    Uses Delaunay triangulation to decompose the convex hull into tetrahedra.
    
    Args:
        Lambda: list of [x, y, z, ...] vertices
        faces: list of boundary faces (polygons)
    
    Returns:
        (tetrahedra, boundary_triangles)
        - tetrahedra: list of (i,j,k,l) vertex indices forming tet
        - boundary_triangles: list of (i,j,k) surface triangles with correct normals
    """
    # Convert to numpy array for Delaunay
    points = np.array([v[:3] for v in Lambda])
    
    # Compute Delaunay triangulation
    print("  Computing Delaunay triangulation...")
    try:
        delaunay = Delaunay(points)
    except Exception as e:
        print(f"  ⚠ Delaunay failed: {e}")
        # Return empty; fall back to surface only
        tetrahedra = []
        boundary_triangles = []
        for face in faces:
            boundary_triangles.extend(triangulate_polygon(face, Lambda))
        # Fix normals
        boundary_triangles = ensure_outward_normals(boundary_triangles, Lambda)
        return tetrahedra, boundary_triangles
    
    # Extract tetrahedra
    tetrahedra = delaunay.simplices.tolist()
    
    # Triangulate boundary faces
    boundary_triangles = []
    for face in faces:
        boundary_triangles.extend(triangulate_polygon(face, Lambda))
    
    # Ensure all normals point outward
    print("  Correcting normal orientation...")
    boundary_triangles = ensure_outward_normals(boundary_triangles, Lambda)
    
    return tetrahedra, boundary_triangles


def classify_tetrahedra(tetrahedra, boundary_triangles, Lambda):
    """
    Classify tetrahedra as interior or exterior based on boundary.
    
    Interior tets: all 4 triangular faces are either on boundary or shared with other interior tet
    Exterior tets: have at least one face NOT on boundary and NOT shared → outside
    
    Args:
        tetrahedra: list of (i,j,k,l) tet vertex indices
        boundary_triangles: list of (i,j,k) surface triangles
        Lambda: vertices
    
    Returns:
        (interior_tets, exterior_tets)
    """
    # Build set of boundary triangle faces (as sorted tuples)
    boundary_set = set()
    for tri in boundary_triangles:
        face_key = tuple(sorted(tri))
        boundary_set.add(face_key)
    
    interior_tets = []
    exterior_tets = []
    
    for tet in tetrahedra:
        i, j, k, l = tet
        
        # Four faces of tetrahedron
        faces = [
            (i, j, k),
            (i, j, l),
            (i, k, l),
            (j, k, l)
        ]
        
        # Count how many faces are on boundary
        boundary_faces = 0
        for face in faces:
            face_key = tuple(sorted(face))
            if face_key in boundary_set:
                boundary_faces += 1
        
        # If all 4 faces are boundary (impossible for interior tet)
        # Or some faces are boundary → partially interior
        if boundary_faces >= 1:
            interior_tets.append(tet)
        else:
            exterior_tets.append(tet)
    
    return interior_tets, exterior_tets


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


def export_tetrahedral_mesh_vtu(filename, Lambda, tetrahedra, boundary_triangles):
    """
    Export tetrahedral mesh to VTU format (for viewing in ParaView/VisIt).
    
    Includes both interior tetrahedra and boundary surface.
    
    Args:
        filename: output VTU file path
        Lambda: vertices
        tetrahedra: list of tetrahedra (i,j,k,l)
        boundary_triangles: list of surface triangles
    """
    import xml.etree.ElementTree as ET
    
    # Create VTU XML structure
    vtu = ET.Element('VTKFile', type='UnstructuredGrid', version='0.1')
    unstructured_grid = ET.SubElement(vtu, 'UnstructuredGrid')
    piece = ET.SubElement(unstructured_grid, 'Piece', 
                          NumberOfPoints=str(len(Lambda)), 
                          NumberOfCells=str(len(tetrahedra) + len(boundary_triangles)))
    
    # Points
    points = ET.SubElement(piece, 'Points')
    data_array = ET.SubElement(points, 'DataArray', type='Float32', NumberOfComponents='3', format='ascii')
    for vertex in Lambda:
        data_array.text = (data_array.text or '') + f"{vertex[0]} {vertex[1]} {vertex[2]} "
    
    # Cells
    cells = ET.SubElement(piece, 'Cells')
    
    # Connectivity
    connectivity = ET.SubElement(cells, 'DataArray', type='Int32', Name='connectivity', format='ascii')
    conn_text = ""
    for tet in tetrahedra:
        conn_text += " ".join(map(str, tet)) + " "
    for tri in boundary_triangles:
        conn_text += " ".join(map(str, tri)) + " "
    connectivity.text = conn_text
    
    # Offsets
    offsets = ET.SubElement(cells, 'DataArray', type='Int32', Name='offsets', format='ascii')
    offset_text = ""
    offset = 0
    for tet in tetrahedra:
        offset += 4
        offset_text += f"{offset} "
    for tri in boundary_triangles:
        offset += 3
        offset_text += f"{offset} "
    offsets.text = offset_text
    
    # Types (10=tetrahedron, 5=triangle)
    types = ET.SubElement(cells, 'DataArray', type='UInt8', Name='types', format='ascii')
    type_text = " ".join(["10"] * len(tetrahedra) + ["5"] * len(boundary_triangles))
    types.text = type_text
    
    # Write file
    tree = ET.ElementTree(vtu)
    tree.write(filename)
    print(f"✓ VTU mesh exported: {filename}")


# ============================================================================
# Test: Cube
# ============================================================================

if __name__ == "__main__":
    # Test cube from pseudo_wireframe.py
    Lambda = [

    # Bottom main block
    [0, 0, 0, 0, 0, 0],   # 0
    [6, 0, 0, 0, 0, 0],   # 1
    [6, 4, 0, 0, 0, 0],   # 2
    [0, 4, 0, 0, 0, 0],   # 3

    # Top main block
    [0, 0, 8, 0, 0, 0],   # 4
    [6, 0, 8, 0, 0, 0],   # 5
    [6, 4, 8, 0, 0, 0],   # 6
    [0, 4, 8, 0, 0, 0],   # 7

    # Left extension (top level)
    [-3, 0, 8, 0, 0, 0],  # 8
    [-3, 4, 8, 0, 0, 0],  # 9
    [-3, 0, 5, 0, 0, 0],  # 10
    [-3, 4, 5, 0, 0, 0],  # 11

    [0, 0, 5, 0, 0, 0],   # 12
    [0, 4, 5, 0, 0, 0],   # 13

    # Lower vertical drop
    [0, 0, 4, 0, 0, 0],   # 14
    [0, 4, 4, 0, 0, 0],   # 15

    ]
    
    Theta = [

    # Main block bottom rectangle
    (0,1),(1,2),(2,3),(3,0),

    # Main block top rectangle
    (4,5),(5,6),(6,7),(7,4),

    # Main block vertical edges
    (0,4),(1,5),(2,6),(3,7),

    # Main block front face (y=0): (0,1,5,4)
    (4,0),

    # Main block back face (y=4): (3,2,6,7)
    (3,2),

    # Main block right face (x=6): (1,2,6,5)
    (5,1),

    # Left extension top face (z=8): (8,9,7,4)
    (8,9),(9,7),(7,4),(4,8),

    # Left extension vertical edges
    (8,10),(9,11),(10,12),(11,13),

    # Left extension inner step faces
    (12,4),(13,7),

    # Left extension back face (x=-3): (8,10,11,9)
    (11,9),

    # Lower ledge horizontal edges
    (12,14),(13,15),

    # Lower ledge inner edge
    (12,13),

    # Lower ledge bottom edge
    (14,15),

    # Lower drop vertical edges
    (14,0),(15,3),

    # Left extension depth edge
    (10,11),

    ]
    
    print("=" * 70)
    print("FACE DETECTION v5: PLANE CLUSTERING APPROACH")
    print("=" * 70)
    
    print("\nStep 1: Finding faces by plane clustering...")
    faces = find_all_faces_by_planes(Lambda, Theta)
    
    print(f"Found {len(faces)} faces:")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {len(face)}-gon {face}")
    
    print("\nStep 2: Generating tetrahedral mesh (interior filling)...")
    tetrahedra, boundary_triangles = generate_tetrahedral_mesh(Lambda, faces)
    
    print(f"Tetrahedra: {len(tetrahedra)}")
    print(f"Boundary triangles: {len(boundary_triangles)}")
    
    if tetrahedra:
        print("\nStep 3: Classifying tetrahedra (interior vs exterior)...")
        interior_tets, exterior_tets = classify_tetrahedra(tetrahedra, boundary_triangles, Lambda)
        print(f"Interior tets: {len(interior_tets)}")
        print(f"Exterior tets: {len(exterior_tets)}")
        print(f"Total tets: {len(tetrahedra)}")
    
    print("\nStep 4: Validating Euler formula...")
    num_v = len(Lambda)
    num_e = len(Theta)
    num_f = len(faces)
    
    euler_valid = validate_euler_formula(num_v, num_e, num_f)
    print(f"V={num_v}, E={num_e}, F={num_f}")
    print(f"V - E + F = {num_v - num_e + num_f} (valid: {euler_valid})")
    
    if euler_valid:
        print("\n✓ Euler formula valid for closed polyhedron")
        
        print("\nStep 5: Exporting STL (surface only)...")
        export_stl("test_cube_v5.stl", boundary_triangles, Lambda)
        print("✓ Exported to test_cube_v5.stl")
        
        if tetrahedra:
            print("\nStep 6: Exporting VTU (volumetric mesh)...")
            export_tetrahedral_mesh_vtu("test_cube_v5.vtu", Lambda, interior_tets if interior_tets else tetrahedra, boundary_triangles)
    else:
        print("\n✗ Euler formula INVALID - face detection failed")
