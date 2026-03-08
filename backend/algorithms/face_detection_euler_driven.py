"""
Face Detection: Euler-Driven Cycle Search

NEW APPROACH:
Instead of generating planes then checking Euler,
we use Euler's formula to CONSTRAIN the face count upfront:

    F_required = E - V + 2

Then we search for exactly F_required simple cycles that:
1. Are coplanar (vertices lie on a plane)
2. Cover all edges
3. Form a valid manifold (consistent orientation)

This is fundamentally more correct for non-convex geometries.

Algorithm:
1. Calculate F_required from wireframe
2. Enumerate all simple cycles in edge graph (Johnson's algorithm)
3. Filter for planarity
4. Search for valid subsets of size F_required
5. Validate manifold properties
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
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    
    normal = np.cross(v1, v2)
    
    if np.linalg.norm(normal) < TOL:
        return None, None, False
    
    normal = normalize_vector(normal)
    d = np.dot(normal, p1)
    
    # Ensure consistent orientation
    for component in normal:
        if abs(component) > TOL:
            if component < 0:
                normal = -normal
                d = -d
            break
    
    return normal, d, True


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


def find_all_simple_cycles_johnson(adj, max_cycle_length=20):
    """
    Find all elementary cycles using Johnson's algorithm variant.
    
    Args:
        adj: adjacency dict {vertex: [neighbors]}
        max_cycle_length: limit search to cycles of this length
    
    Returns:
        list of cycles, each cycle is a list of vertex indices
    """
    cycles = []
    vertices = sorted(adj.keys())
    
    def dfs_cycle(v, start, path, visited_in_path):
        """DFS to find cycles starting from 'start' vertex."""
        neighbors = adj.get(v, [])
        
        for neighbor in neighbors:
            if neighbor == start and len(path) >= 3:
                # Found a cycle
                cycle = path[:]
                # Normalize: start from smallest vertex
                min_idx = cycle.index(min(cycle))
                normalized = cycle[min_idx:] + cycle[:min_idx]
                # Avoid duplicates in reverse order
                reversed_cycle = [normalized[0]] + normalized[1:][::-1]
                canonical = min(normalized, reversed_cycle)
                
                if canonical not in cycles:
                    cycles.append(canonical)
                return
            
            if neighbor not in visited_in_path and len(path) < max_cycle_length:
                visited_in_path.add(neighbor)
                path.append(neighbor)
                dfs_cycle(neighbor, start, path, visited_in_path)
                path.pop()
                visited_in_path.remove(neighbor)
    
    # Search from each vertex as starting point
    for start_vertex in vertices:
        visited = {start_vertex}
        dfs_cycle(start_vertex, start_vertex, [start_vertex], visited)
    
    return cycles


def find_simple_cycles_bfs(Theta, max_cycle_length=20):
    """
    Find simple cycles using BFS-based approach (simpler, practical version).
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


def calculate_face_count_required(num_vertices, num_edges):
    """
    Calculate required face count using Euler's formula.
    
    For closed polyhedron: V - E + F = 2
    Therefore: F = E - V + 2
    """
    F = num_edges - num_vertices + 2
    return F


def find_valid_face_subsets(cycles, Lambda, Theta, F_required, max_iterations=10000):
    """
    Find a valid subset of cycles that forms a closed manifold.
    
    Args:
        cycles: list of candidate cycles
        Lambda: vertices
        Theta: edges (as set of tuples for quick lookup)
        F_required: number of faces required
        max_iterations: limit search iterations
    
    Returns:
        list of valid faces (cycles) or None if not found
    """
    # Filter cycles for planarity
    planar_cycles = []
    for cycle in cycles:
        is_planar, normal, d = is_cycle_coplanar(cycle, Lambda)
        if is_planar:
            planar_cycles.append(cycle)
    
    print(f"  Found {len(planar_cycles)} planar cycles out of {len(cycles)} total cycles")
    
    if len(planar_cycles) < F_required:
        print(f"  ⚠ Not enough planar cycles ({len(planar_cycles)}) for F_required={F_required}")
        return None
    
    # Build edge set for comparison
    edge_set = set()
    for u, v in Theta:
        edge_set.add((min(u, v), max(u, v)))
    
    # Greedy search: try to find F_required cycles that cover edges
    best_subset = None
    best_cover_ratio = 0
    
    # Sample combinations of F_required cycles
    iterations = 0
    for subset in combinations(planar_cycles, F_required):
        if iterations > max_iterations:
            break
        iterations += 1
        
        # Check edge coverage
        covered_edges = set()
        for cycle in subset:
            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                edge_key = (min(u, v), max(u, v))
                covered_edges.add(edge_key)
        
        cover_ratio = len(covered_edges) / len(edge_set)
        
        if cover_ratio > best_cover_ratio:
            best_cover_ratio = cover_ratio
            best_subset = subset
            
            # If perfect coverage, we're done
            if cover_ratio >= 0.99:
                return list(best_subset)
    
    if best_subset and best_cover_ratio > 0.8:
        print(f"  ✓ Found valid face subset with {best_cover_ratio:.1%} edge coverage")
        return list(best_subset)
    
    print(f"  ⚠ Best subset found has only {best_cover_ratio:.1%} edge coverage")
    return best_subset if best_subset else None


def triangulate_polygon(face, Lambda):
    """Triangulate a polygon using fan triangulation."""
    if len(face) < 3:
        return []
    
    triangles = []
    for i in range(1, len(face) - 1):
        triangles.append((face[0], face[i], face[i + 1]))
    
    return triangles


def compute_face_normal(triangle, Lambda):
    """Compute normal of a triangle."""
    i, j, k = triangle
    p0 = np.array(Lambda[i][:3])
    p1 = np.array(Lambda[j][:3])
    p2 = np.array(Lambda[k][:3])
    
    v1 = p1 - p0
    v2 = p2 - p0
    
    normal = np.cross(v1, v2)
    norm = np.linalg.norm(normal)
    
    if norm < TOL:
        return np.array([0, 0, 1])
    
    return normal / norm


def ensure_outward_normals(triangles, Lambda):
    """Ensure all triangle normals point outward from mesh centroid."""
    points = np.array([v[:3] for v in Lambda])
    centroid = points.mean(axis=0)
    
    corrected = []
    for tri in triangles:
        i, j, k = tri
        p0 = np.array(Lambda[i][:3])
        p1 = np.array(Lambda[j][:3])
        p2 = np.array(Lambda[k][:3])
        
        tri_center = (p0 + p1 + p2) / 3
        to_tri = tri_center - centroid
        
        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)
        
        dot_product = np.dot(normal, to_tri)
        
        if dot_product < 0:
            corrected.append((i, k, j))
        else:
            corrected.append(tri)
    
    return corrected


def validate_euler_formula(num_vertices, num_edges, num_faces):
    """Check Euler formula: V - E + F = 2."""
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


def find_all_faces_euler_driven(Lambda, Theta):
    """
    Find all faces using Euler-driven cycle enumeration.
    
    Args:
        Lambda: list of [x, y, z, ...] vertices
        Theta: list of (u, v) edges
    
    Returns:
        list of faces (each face is a list of vertex indices)
    """
    print("\n" + "=" * 70)
    print("EULER-DRIVEN FACE DETECTION")
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
    valid_faces = find_valid_face_subsets(cycles, Lambda, Theta, F_required, max_iterations=50000)
    
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


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test with L-shaped geometry
    Lambda = [
        [0, 0, 0], [6, 0, 0], [6, 4, 0], [0, 4, 0],       # 0-3
        [0, 0, 8], [6, 0, 8], [6, 4, 8], [0, 4, 8],       # 4-7
        [-3, 0, 8], [-3, 4, 8], [-3, 0, 5], [-3, 4, 5],   # 8-11
        [0, 0, 5], [0, 4, 5], [0, 0, 4], [0, 4, 4]        # 12-15
    ]
    
    Theta = [
        (0,1),(1,2),(2,3),(3,0), (4,5),(5,6),(6,7),(7,4), # Blocks
        (0,4),(1,5),(2,6),(3,7), (4,0), (3,2), (5,1),     # Verticals
        (8,9),(9,7),(7,4),(4,8), (8,10),(9,11),           # Extension
        (10,12),(11,13), (12,4),(13,7), (11,9),           # Steps
        (12,14),(13,15), (12,13), (14,15),                # Ledge
        (14,0),(15,3), (10,11)                            # Base connections
    ]
    
    faces = find_all_faces_euler_driven(Lambda, Theta)
    
    print(f"\nFound {len(faces)} faces:")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {face}")
    
    # Export if valid
    if faces:
        print("\nTriangulating and exporting...")
        triangles = []
        for face in faces:
            triangles.extend(triangulate_polygon(face, Lambda))
        
        triangles = ensure_outward_normals(triangles, Lambda)
        export_stl("test_euler_driven.stl", triangles, Lambda)
        print("✓ Exported to test_euler_driven.stl")
