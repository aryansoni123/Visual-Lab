"""
Face Detection: Euler-Driven Cycle Search Approach

Geometric principle:
- Use Euler's formula (V - E + F = 2) to CONSTRAIN face count upfront
- Search for exactly F_required simple cycles that are coplanar
- This avoids plane-clustering ambiguity for non-convex shapes

Algorithm:
1. Calculate F_required = E - V + 2 from wireframe
2. Enumerate all simple cycles in edge graph (BFS-based)
3. Filter cycles for planarity (coplanar vertices)
4. Search for valid subsets of exactly F_required coplanar cycles
5. Validate Euler formula and export mesh
"""

import numpy as np
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


def find_all_faces_by_planes(Lambda, Theta):
    """
    Find all faces using Euler-driven cycle enumeration.
    
    Args:
        Lambda: list of [x, y, z, ...] vertices
        Theta: list of (u, v) edges
    
    Returns:
        list of faces (each face is a list of vertex indices)
    """
    print("\n" + "=" * 70)
    print("FACE DETECTION: LARGEST-FACE-FIRST SEARCH")
    print("=" * 70)
    
    num_v = len(Lambda)
    num_e = len(Theta)
    F_required = calculate_face_count_required(num_v, num_e)
    
    print(f"\nStep 1: Calculate required face count")
    print(f"  V (vertices) = {num_v}")
    print(f"  E (edges) = {num_e}")
    print(f"  F_required = E - V + 2 = {num_e} - {num_v} + 2 = {F_required}")
    
    print(f"\nStep 2: Enumerate all simple cycles in edge graph...")
    cycles = find_simple_cycles_bfs(Theta, max_cycle_length=15)
    print(f"  Found {len(cycles)} total simple cycles")
    
    if not cycles:
        print("  ✗ No cycles found! Wireframe may be invalid.")
        return []
    
    print(f"\nStep 3: Filter for planarity and select F_required faces...")
    valid_faces = find_valid_face_subsets(cycles, Lambda, Theta, F_required, max_iterations=1000000)
    
    if not valid_faces:
        print(f"  ✗ Could not find {F_required} valid coplanar cycles")
        return []
    
    print(f"\nStep 4: Verify Euler formula with found faces...")
    euler_valid = validate_euler_formula(num_v, num_e, len(valid_faces))
    print(f"  V={num_v}, E={num_e}, F={len(valid_faces)}")
    print(f"  V - E + F = {num_v - num_e + len(valid_faces)} (valid: {euler_valid})")
    
    if not euler_valid:
        print(f"  ⚠ Euler formula does not validate! Found {len(valid_faces)} faces but F_required={F_required}")
    
    return list(valid_faces)


def point_distance_to_plane(point, normal, d):
    """Distance from point to plane (signed)."""
    return abs(np.dot(normal, point) - d)


def build_adjacency(Theta):
    """Build adjacency list from edges."""
    adj = defaultdict(list)
    for u, v in Theta:
        if v not in adj[u]:
            adj[u].append(v)
        if u not in adj[v]:
            adj[v].append(u)
    return adj


def find_simple_cycles_bfs(Theta, max_cycle_length=20):
    """
    Find simple cycles using BFS-based approach.
    Focuses on cycles that are actual face candidates.
    
    Args:
        Theta: list of (u, v) edges
        max_cycle_length: maximum vertices in a cycle
    
    Returns:
        list of cycles (each cycle is a list of vertex indices in order)
    """
    adj = build_adjacency(Theta)
    cycles = []
    found_normalized = set()
    
    # For each vertex, try to find cycles through it
    for start_v in sorted(adj.keys()):
        # BFS to find short paths back to start_v
        queue = [(start_v, [start_v], {start_v})]
        
        while queue:
            current, path, visited = queue.pop(0)
            
            if len(path) > max_cycle_length:
                continue
            
            for neighbor in adj[current]:
                if neighbor == start_v and len(path) >= 3:
                    # Found a cycle
                    cycle = path[:]
                    # Normalize for deduplication
                    min_idx = cycle.index(min(cycle))
                    normalized = tuple(cycle[min_idx:] + cycle[:min_idx])
                    
                    if normalized not in found_normalized:
                        cycles.append(list(normalized))
                        found_normalized.add(normalized)
                
                elif neighbor not in visited and len(path) < max_cycle_length:
                    new_visited = visited.copy()
                    new_visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], new_visited))
    
    return cycles


def is_cycle_coplanar(cycle, Lambda):
    """
    Check if a cycle's vertices are coplanar.
    
    Args:
        cycle: list of vertex indices
        Lambda: vertex coordinates
    
    Returns:
        (is_coplanar: bool, normal: np.array, d: float)
    """
    if len(cycle) < 3:
        return False, None, None
    
    # Get first 3 vertices to define plane
    p1 = np.array(Lambda[cycle[0]][:3])
    p2 = np.array(Lambda[cycle[1]][:3])
    p3 = np.array(Lambda[cycle[2]][:3])
    
    normal, d, valid = compute_plane_equation(p1, p2, p3)
    if not valid:
        return False, None, None
    
    # Check all other vertices
    for idx in cycle[3:]:
        point = np.array(Lambda[idx][:3])
        dist = point_distance_to_plane(point, normal, d)
        if dist > TOL:
            return False, None, None
    
    return True, normal, d


def cycle_edge_keys(cycle):
    """Return undirected edge keys for a cycle."""
    keys = set()
    for i in range(len(cycle)):
        u = cycle[i]
        v = cycle[(i + 1) % len(cycle)]
        keys.add((min(u, v), max(u, v)))
    return keys


def polygon_area_3d(cycle, Lambda):
    """Compute polygon area in 3D via fan triangulation from the first vertex."""
    if len(cycle) < 3:
        return 0.0

    p0 = np.array(Lambda[cycle[0]][:3], dtype=float)
    area = 0.0

    for i in range(1, len(cycle) - 1):
        p1 = np.array(Lambda[cycle[i]][:3], dtype=float)
        p2 = np.array(Lambda[cycle[i + 1]][:3], dtype=float)
        cross = np.cross(p1 - p0, p2 - p0)
        area += 0.5 * np.linalg.norm(cross)

    return float(area)


def calculate_face_count_required(num_vertices, num_edges):
    """
    Calculate required face count using Euler's formula.
    
    For closed polyhedron: V - E + F = 2
    Therefore: F = E - V + 2
    """
    F = num_edges - num_vertices + 2
    return F


def find_valid_face_subsets(cycles, Lambda, Theta, F_required, max_iterations=50000):
    """
    Find a valid subset of cycles that forms a closed manifold.
    
    Args:
        cycles: list of candidate cycles
        Lambda: vertices
        Theta: edges (as list of tuples)
        F_required: number of faces required
        max_iterations: limit search iterations
    
    Returns:
        list of valid faces (cycles) or None if not found
    """
    # Build unique edge set from wireframe
    edge_set = set()
    for u, v in Theta:
        edge_set.add((min(u, v), max(u, v)))

    # Filter cycles for planarity and deduplicate by boundary-edge signature
    candidate_by_edges = {}
    for cycle in cycles:
        is_planar, _, _ = is_cycle_coplanar(cycle, Lambda)
        if not is_planar:
            continue

        edges = frozenset(cycle_edge_keys(cycle))
        if not edges:
            continue

        area = polygon_area_3d(cycle, Lambda)
        if edges not in candidate_by_edges or area > candidate_by_edges[edges]["area"]:
            candidate_by_edges[edges] = {
                "cycle": cycle,
                "edges": set(edges),
                "area": area,
            }

    candidates = list(candidate_by_edges.values())
    print(f"  Found {len(candidates)} planar unique face candidates out of {len(cycles)} total cycles")

    if len(candidates) < F_required:
        print(f"  ⚠ Not enough planar candidates ({len(candidates)}) for F_required={F_required}")
        return None

    # Largest-face-first with backtracking and edge-incidence constraints.
    # Each wireframe edge can belong to at most 2 faces in a closed manifold boundary.
    ordered = sorted(candidates, key=lambda c: (-c["area"], len(c["cycle"])))

    def run_search(max_edge_incidence):
        node_counter = {"count": 0}

        def dfs(idx, selected_cycles, edge_incidence, covered_edges):
            node_counter["count"] += 1
            if node_counter["count"] > max_iterations:
                return None

            if len(selected_cycles) == F_required:
                return selected_cycles

            if idx >= len(ordered):
                return None

            # Prune: not enough candidates left to reach target face count.
            if len(selected_cycles) + (len(ordered) - idx) < F_required:
                return None

            cand = ordered[idx]
            cand_edges = cand["edges"]

            # Branch 1 (preferred): include current largest candidate if feasible.
            if all(edge_incidence[e] < max_edge_incidence for e in cand_edges):
                next_inc = edge_incidence.copy()
                for e in cand_edges:
                    next_inc[e] += 1
                include_result = dfs(
                    idx + 1,
                    selected_cycles + [cand["cycle"]],
                    next_inc,
                    covered_edges | cand_edges,
                )
                if include_result is not None:
                    return include_result

            # Branch 2: skip current candidate.
            return dfs(idx + 1, selected_cycles, edge_incidence, covered_edges)

        selected_local = dfs(0, [], defaultdict(int), set())
        return selected_local, node_counter["count"]

    selected = None
    explored = 0
    used_cap = None
    for cap in (2, 3, 4):
        selected_try, explored_try = run_search(cap)
        explored += explored_try
        if selected_try is not None:
            selected = selected_try
            used_cap = cap
            break

    if selected is None:
        print("  ⚠ Largest-face-first search could not find a feasible face set")
        return None

    covered = set()
    for cyc in selected:
        covered.update(cycle_edge_keys(cyc))
    cover_ratio = len(covered) / max(1, len(edge_set))

    print(f"  ✓ Largest-face-first selected {len(selected)} faces")
    print(f"  ✓ Edge coverage achieved: {cover_ratio:.1%}")
    print(f"  ✓ Edge-incidence cap used: {used_cap}")
    print(f"  ✓ Search nodes explored: {explored}")
    return selected



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
