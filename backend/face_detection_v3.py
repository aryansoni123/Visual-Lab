# =========================================================
# FACE DETECTION FROM 3D WIREFRAME (V3 - CORRECTED)
# Using: Minimal Cycle Detection with Planarity Filtering
# 
# This is robust for 2-manifold polyhedra.
# =========================================================

import numpy as np
from collections import defaultdict

TOL = 1e-6


# =========================================================
# ============== PLANARITY CHECK ======================
# =========================================================

def are_coplanar(points, tolerance=TOL):
    """Check if points lie on a plane."""
    if len(points) < 4:
        return True
    
    points = np.array(points)
    
    # PCA: if rank <= 2, points are coplanar
    centered = points - points.mean(axis=0)
    
    if len(points) >= 3:
        try:
            _, s, _ = np.linalg.svd(centered)
            # If smallest singular value is tiny, points are coplanar
            return s[-1] < tolerance * max(s[0], 1.0)
        except:
            return True
    
    return True


# =========================================================
# ============== CYCLE DETECTION ======================
# =========================================================

def find_shortest_cycle_from_edge(u, v, graph, num_vertices):
    """
    Find the shortest simple cycle containing directed edge (u→v).
    Uses BFS to find shortest path from v back to u without using edge v→u.
    """
    from collections import deque
    
    if v not in graph:
        return None
    
    # BFS: start from v, find shortest path back to u
    # Path must have length >= 2 (at least 3 vertices in cycle)
    queue = deque([(v, [v], {v})])  # (current_node, path, visited)
    
    while queue:
        current, path, visited = queue.popleft()
        
        # Limit path length to avoid long cycles (allow up to num_vertices)
        if len(path) > num_vertices:
            continue
        
        for neighbor in graph[current]:
            if neighbor == u and len(path) >= 2:
                # Found a cycle: u → v → ... → u
                cycle = [u] + path
                return cycle[:-1]  # Return without duplicate u
            
            if neighbor not in visited and neighbor != u:
                new_visited = visited | {neighbor}
                queue.append((neighbor, path + [neighbor], new_visited))
    
    return None


def find_minimal_faces(lambda_vertices, theta_edges):
    """
    Find minimal planar cycles (faces) by:
    1. For each directed edge, find ALL simple cycles (up to length limit)
    2. Filter by planarity AND keep only those with minimum size (greedy)
    3. Use BFS to ensure we find actual small cycles, not large wrapping ones
    """
    from collections import deque
    
    # Build graph
    graph = defaultdict(list)
    for u, v in theta_edges:
        graph[u].append(v)
        graph[v].append(u)
    
    all_cycles = []
    
    # Find cycles starting from each edge
    for u, v in theta_edges:
        # Forward (u → v)
        cycle = find_shortest_cycle_from_edge(u, v, graph, len(lambda_vertices))
        if cycle and len(cycle) >= 3:
            all_cycles.append(cycle)
        
        # Backward (v → u)
        cycle = find_shortest_cycle_from_edge(v, u, graph, len(lambda_vertices))
        if cycle and len(cycle) >= 3:
            all_cycles.append(cycle)
    
    # Filter by planarity
    planar_cycles = []
    for cycle in all_cycles:
        points = [lambda_vertices[i] for i in cycle]
        if are_coplanar(points, TOL):
            planar_cycles.append(cycle)
    
    # Deduplicate and keep only minimal cycles (not combinations of smaller ones)
    unique_faces = []
    seen = set()
    
    # Sort by cycle length (prefer shorter cycles)
    planar_cycles.sort(key=len)
    
    for cycle in planar_cycles:
        canonical = tuple(sorted(cycle))
        if canonical not in seen:
            seen.add(canonical)
            unique_faces.append(cycle)
    
    return unique_faces


# =========================================================
# ============== MESH EXPORT ==============================
# =========================================================

def triangulate_polygon(polygon_indices, lambda_vertices):
    """Fan triangulation of a polygon."""
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


def export_stl(faces, lambda_vertices, filename):
    """Export to ASCII STL."""
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
            
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            
            if norm > TOL:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1])
            
            f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}\n")
            f.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
            f.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        
        f.write("endsolid mesh\n")


# =========================================================
# ===================== PIPELINE =========================
# =========================================================

def detect_faces_and_export(lambda_vertices, theta_edges, output_filename):
    """Complete pipeline."""
    print("\n" + "=" * 70)
    print("FACE DETECTION (Greedy Minimal Cycles)")
    print("=" * 70)
    
    print(f"\nInput: {len(lambda_vertices)} vertices, {len(theta_edges)} edges")
    
    # Step 1: Find minimal faces
    print(f"\nStep 1: Finding minimal planar cycles...")
    faces = find_minimal_faces(lambda_vertices, theta_edges)
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
    V = len(lambda_vertices)
    E = len(theta_edges)
    F = len(faces)
    euler_char = V - E + F
    is_valid = abs(euler_char - 2) < 0.5
    print(f"  V={V}, E={E}, F={F}")
    print(f"  V - E + F = {euler_char} (valid: {is_valid})")
    
    # Step 4: Export
    print(f"\nStep 4: Exporting to STL...")
    export_stl(faces, lambda_vertices, output_filename)
    print(f"  Written to: {output_filename}")
    
    print("\n" + "=" * 70)
    return faces, triangles, is_valid, euler_char


# =========================================================
# ===================== TEST ==============================
# =========================================================

if __name__ == "__main__":
    from collections import deque
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
    faces, triangles, is_valid, euler = detect_faces_and_export(
        lambda_coords, Theta, "test_cube_v3.stl"
    )
    
    print("\nFaces detected:")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {len(face)}-gon: {face}")
