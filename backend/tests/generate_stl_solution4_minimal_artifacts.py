"""Solution 4: Minimize triangulation artifacts by preferring smaller, simpler faces."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import defaultdict
import numpy as np
from itertools import combinations

from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper

TOL = 1e-6


def build_projection_graph(lambda_rows, theta_edges, axes):
    """Project 3D wireframe onto a 2D plane and deduplicate points/edges."""
    points2d = [tuple(float(lambda_rows[i][a]) for a in axes) for i in range(len(lambda_rows))]
    index_by_point = {}
    vertices2d = []
    map3d_to2d = {}
    for i, p in enumerate(points2d):
        if p not in index_by_point:
            index_by_point[p] = len(vertices2d)
            vertices2d.append(p)
        map3d_to2d[i] = index_by_point[p]
    edges2d = set()
    for u, v in theta_edges:
        pu = map3d_to2d[u]
        pv = map3d_to2d[v]
        if pu != pv:
            a, b = (pu, pv) if pu < pv else (pv, pu)
            edges2d.add((a, b))
    return vertices2d, sorted(edges2d)


def compute_plane_equation(p1, p2, p3):
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    normal = np.cross(v1, v2)
    if np.linalg.norm(normal) < TOL:
        return None, None, False
    normal = normal / np.linalg.norm(normal)
    d = np.dot(normal, p1)
    return normal, d, True


def is_cycle_coplanar(cycle, Lambda):
    if len(cycle) < 3:
        return False, None, None
    p1 = np.array(Lambda[cycle[0]][:3])
    p2 = np.array(Lambda[cycle[1]][:3])
    p3 = np.array(Lambda[cycle[2]][:3])
    normal, d, valid = compute_plane_equation(p1, p2, p3)
    if not valid:
        return False, None, None
    for idx in cycle[3:]:
        point = np.array(Lambda[idx][:3])
        dist = abs(np.dot(normal, point) - d)
        if dist > TOL:
            return False, None, None
    return True, normal, d


def cycle_edge_keys(cycle):
    keys = set()
    for i in range(len(cycle)):
        u = cycle[i]
        v = cycle[(i + 1) % len(cycle)]
        keys.add((min(u, v), max(u, v)))
    return keys


def polygon_area_3d(cycle, Lambda):
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


def build_adjacency(Theta):
    adj = defaultdict(list)
    for u, v in Theta:
        if v not in adj[u]:
            adj[u].append(v)
        if u not in adj[v]:
            adj[v].append(u)
    return adj


def find_simple_cycles_bfs(Theta, max_cycle_length=20):
    adj = build_adjacency(Theta)
    cycles = []
    found_normalized = set()
    for start_v in sorted(adj.keys()):
        queue = [(start_v, [start_v], {start_v})]
        while queue:
            current, path, visited = queue.pop(0)
            if len(path) > max_cycle_length:
                continue
            for neighbor in adj[current]:
                if neighbor == start_v and len(path) >= 3:
                    cycle = path[:]
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


def find_faces_minimal_artifacts(Lambda, Theta, max_iterations=1000000):
    """Prefer smaller faces to minimize triangulation artifacts."""
    num_v = len(Lambda)
    num_e = len(Theta)
    F_required = num_e - num_v + 2
    
    print(f"\n[Solution 4: Minimize Triangulation Artifacts]")
    print(f"V={num_v}, E={num_e}, F_required={F_required}")
    
    cycles = find_simple_cycles_bfs(Theta, max_cycle_length=15)
    print(f"Total cycles found: {len(cycles)}")
    
    # Filter for planarity
    candidate_by_edges = {}
    for cycle in cycles:
        is_planar, _, _ = is_cycle_coplanar(cycle, Lambda)
        if not is_planar:
            continue
        edges = frozenset(cycle_edge_keys(cycle))
        if not edges:
            continue
        area = polygon_area_3d(cycle, Lambda)
        # Prefer smaller faces with same edge set
        if edges not in candidate_by_edges or len(cycle) < len(candidate_by_edges[edges]["cycle"]):
            candidate_by_edges[edges] = {"cycle": cycle, "edges": set(edges), "area": area}
    
    candidates = list(candidate_by_edges.values())
    print(f"Planar unique candidates: {len(candidates)}")
    
    if len(candidates) < F_required:
        print(f"⚠ Not enough candidates for F_required={F_required}")
        return None
    
    # Sort by: smallest face first (fewer vertices = fewer triangulation artifacts)
    ordered = sorted(candidates, key=lambda c: (len(c["cycle"]), -c["area"]))
    
    node_counter = {"count": 0}
    
    def dfs(idx, selected_cycles, edge_incidence, covered_edges):
        node_counter["count"] += 1
        if node_counter["count"] > max_iterations:
            return None
        if len(selected_cycles) == F_required:
            return selected_cycles
        if idx >= len(ordered):
            return None
        if len(selected_cycles) + (len(ordered) - idx) < F_required:
            return None
        
        cand = ordered[idx]
        cand_edges = cand["edges"]
        
        # Try with increasing caps
        max_cap = 4
        if all(edge_incidence[e] < max_cap for e in cand_edges):
            next_inc = edge_incidence.copy()
            for e in cand_edges:
                next_inc[e] += 1
            include_result = dfs(idx + 1, selected_cycles + [cand["cycle"]], next_inc, covered_edges | cand_edges)
            if include_result is not None:
                return include_result
        
        return dfs(idx + 1, selected_cycles, edge_incidence, covered_edges)
    
    selected = dfs(0, [], defaultdict(int), set())
    
    if selected is None:
        print(f"✗ Could not find {F_required} faces")
        return None
    
    # Calculate artifact metric: total triangulation edges
    total_triangulation_edges = sum(max(0, len(face) - 3) for face in selected)
    
    print(f"✓ Found {len(selected)} faces")
    print(f"✓ Face sizes: {sorted([len(f) for f in selected])}")
    print(f"✓ Estimated triangulation edges: {total_triangulation_edges}")
    print(f"✓ Search nodes explored: {node_counter['count']}")
    return selected


def triangulate_polygon(face, Lambda):
    if len(face) < 3:
        return []
    triangles = []
    for i in range(1, len(face) - 1):
        triangles.append((face[0], face[i], face[i + 1]))
    return triangles


def compute_face_normal(triangle, Lambda):
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


def export_stl(filename, triangles, Lambda):
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


def main():
    Lambda_ref = [
        [0, 0, 0, 0, 0, 0], [6, 0, 0, 0, 0, 0], [6, 4, 0, 0, 0, 0], [0, 4, 0, 0, 0, 0],
        [0, 0, 8, 0, 0, 0], [6, 0, 8, 0, 0, 0], [6, 4, 8, 0, 0, 0], [0, 4, 8, 0, 0, 0],
        [-3, 0, 8, 0, 0, 0], [-3, 4, 8, 0, 0, 0], [-3, 0, 5, 0, 0, 0], [-3, 4, 5, 0, 0, 0],
        [0, 0, 5, 0, 0, 0], [0, 4, 5, 0, 0, 0], [0, 0, 4, 0, 0, 0], [0, 4, 4, 0, 0, 0],
    ]
    Theta_ref = [
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7), (4, 0), (3, 2), (5, 1),
        (8, 9), (9, 7), (7, 4), (4, 8), (8, 10), (9, 11), (10, 12), (11, 13),
        (12, 4), (13, 7), (11, 9), (12, 14), (13, 15), (12, 13),
        (14, 15), (14, 0), (15, 3), (10, 11),
    ]
    
    front_vertices, front_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 1))
    top_vertices, top_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 2))
    side_vertices, side_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(1, 2))
    
    Lambda, Theta, _ = build_pseudo_wireframe_paper(
        front_vertices, front_edges, top_vertices, top_edges,
        side_vertices, side_edges, split_intersections=False,
    )
    
    faces = find_faces_minimal_artifacts(Lambda, Theta)
    
    if faces is None:
        print("Failed to find valid face set")
        return
    
    triangles = []
    for face in faces:
        triangles.extend(triangulate_polygon(face, Lambda))
    triangles = ensure_outward_normals(triangles, Lambda)
    
    out_path = Path(__file__).resolve().parents[1] / "outputs" / "solution4_minimal_artifacts.stl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(str(out_path), triangles, Lambda)
    
    print(f"\nLambda: {len(Lambda)}")
    print(f"Theta: {len(Theta)}")
    print(f"Faces: {len(faces)}")
    print(f"Triangles: {len(triangles)}")
    print(f"STL: {out_path}")


if __name__ == "__main__":
    main()
