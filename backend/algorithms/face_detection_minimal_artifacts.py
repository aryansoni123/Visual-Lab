"""
Face Detection: Minimal Artifacts Strategy

Prefers smaller, simpler faces to minimize triangulation artifacts.
Generates cleaner meshes by finding all-quad faces when possible.
"""

from collections import defaultdict
import numpy as np

TOL = 1e-6


def build_adjacency(Theta):
    """Build adjacency list from edge list."""
    adj = defaultdict(list)
    for u, v in Theta:
        if v not in adj[u]:
            adj[u].append(v)
        if u not in adj[v]:
            adj[v].append(u)
    return adj


def find_simple_cycles_bfs(Theta, max_cycle_length=20):
    """Find all simple cycles using BFS."""
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
                    # Found a cycle
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


def compute_plane_equation(p1, p2, p3):
    """Compute plane equation from 3 points."""
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    normal = np.cross(v1, v2)
    if np.linalg.norm(normal) < TOL:
        return None, None, False
    normal = normal / np.linalg.norm(normal)
    d = np.dot(normal, p1)
    return normal, d, True


def is_cycle_coplanar(cycle, Lambda):
    """Check if a cycle forms a planar face."""
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
    """Get normalized edge keys from a cycle."""
    keys = set()
    for i in range(len(cycle)):
        u = cycle[i]
        v = cycle[(i + 1) % len(cycle)]
        keys.add((min(u, v), max(u, v)))
    return keys


def polygon_area_3d(cycle, Lambda):
    """Calculate 3D polygon area."""
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


def count_connected_components(Theta, num_v):
    """Count connected components of the edge graph."""
    adj = defaultdict(set)
    for u, v in Theta:
        adj[u].add(v)
        adj[v].add(u)

    visited = set()
    components = 0
    for start in range(num_v):
        if start not in visited:
            components += 1
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                stack.extend(adj[node] - visited)
    return components


def find_all_faces_minimal_artifacts(Lambda, Theta, max_iterations=1000000):
    """
    Find faces that minimize triangulation artifacts.

    Strategy: Prefer smaller faces (quads over larger polygons) to reduce
    the number of diagonal edges needed for triangulation.
    Uses the generalised Euler formula F = E - V + 2*c where c is the
    number of connected components, so disconnected sub-solids are handled
    correctly.

    Args:
        Lambda: List of 3D vertices
        Theta: List of 3D edges
        max_iterations: Maximum search nodes to explore

    Returns:
        List of faces (each face is a list of vertex indices)
    """
    num_v = len(Lambda)
    num_e = len(Theta)
    num_components = count_connected_components(Theta, num_v)
    F_required = num_e - num_v + 2 * num_components  # Generalised Euler formula
    
    print(f"\n{'=' * 70}")
    print(f"FACE DETECTION: MINIMAL ARTIFACTS STRATEGY")
    print(f"{'=' * 70}")
    print(f"\nStep 1: Calculate required face count")
    print(f"  V (vertices) = {num_v}")
    print(f"  E (edges) = {num_e}")
    print(f"  Connected components (c) = {num_components}")
    print(f"  F_required = E - V + 2*c = {num_e} - {num_v} + {2*num_components} = {F_required}")
    
    # Step 2: Enumerate all simple cycles
    print(f"\nStep 2: Enumerate all simple cycles in edge graph...")
    cycles = find_simple_cycles_bfs(Theta, max_cycle_length=15)
    print(f"  Found {len(cycles)} total simple cycles")
    
    # Step 3: Filter for planarity and deduplicate by edge set
    print(f"\nStep 3: Filter for planarity and prefer smaller faces...")
    candidate_by_edges = {}
    
    for cycle in cycles:
        is_planar, _, _ = is_cycle_coplanar(cycle, Lambda)
        if not is_planar:
            continue
        
        edges = frozenset(cycle_edge_keys(cycle))
        if not edges:
            continue
        
        area = polygon_area_3d(cycle, Lambda)
        
        # Prefer smaller faces with same edge set (fewer vertices = fewer triangulation diagonals)
        if edges not in candidate_by_edges or len(cycle) < len(candidate_by_edges[edges]["cycle"]):
            candidate_by_edges[edges] = {
                "cycle": cycle,
                "edges": set(edges),
                "area": area
            }
    
    candidates = list(candidate_by_edges.values())
    print(f"  Found {len(candidates)} planar unique face candidates out of {len(cycles)} total cycles")
    
    if len(candidates) < F_required:
        print(f"  ⚠ Not enough candidates for F_required={F_required}")
        return None
    
    # Helper: Check if face is horizontal (all vertices at same Z-level)
    def is_horizontal(cycle):
        z_vals = [Lambda[v][2] for v in cycle]
        return len(set(z_vals)) == 1
    
    # Step 4: Sort by: size (smallest first), horizontal before vertical, then area
    # This prioritizes top/bottom faces of boxes over side faces
    ordered = sorted(candidates, key=lambda c: (len(c["cycle"]), not is_horizontal(c["cycle"]), -c["area"]))
    
    node_counter = {"count": 0}
    
    def dfs(idx, selected_cycles, edge_incidence, covered_edges):
        """DFS backtracking search with edge-incidence constraints."""
        node_counter["count"] += 1
        if node_counter["count"] > max_iterations:
            return None
        
        # Success: found F_required faces
        if len(selected_cycles) == F_required:
            return selected_cycles
        
        # Exhausted candidates
        if idx >= len(ordered):
            return None
        
        # Pruning: not enough candidates left
        if len(selected_cycles) + (len(ordered) - idx) < F_required:
            return None
        
        cand = ordered[idx]
        cand_edges = cand["edges"]
        
        # Try including this candidate (with cap relaxation up to 4)
        max_cap = 4
        if all(edge_incidence[e] < max_cap for e in cand_edges):
            next_inc = edge_incidence.copy()
            for e in cand_edges:
                next_inc[e] += 1
            
            include_result = dfs(
                idx + 1,
                selected_cycles + [cand["cycle"]],
                next_inc,
                covered_edges | cand_edges
            )
            if include_result is not None:
                return include_result
        
        # Try excluding this candidate
        return dfs(idx + 1, selected_cycles, edge_incidence, covered_edges)
    
    # Step 5: Search for face combination
    print(f"\nStep 4: Backtracking search for minimal-artifact face set...")
    selected = dfs(0, [], defaultdict(int), set())
    
    if selected is None:
        print(f"  ✗ Could not find {F_required} faces")
        return None
    
    # Calculate metrics
    face_sizes = sorted([len(f) for f in selected])
    total_triangulation_edges = sum(max(0, len(face) - 3) for face in selected)
    edge_coverage = len(set().union(*[cycle_edge_keys(f) for f in selected])) / num_e * 100
    
    print(f"  ✓ Minimal-artifact selected {len(selected)} faces")
    print(f"  ✓ Face sizes: {face_sizes}")
    print(f"  ✓ Triangulation edges needed: {total_triangulation_edges}")
    print(f"  ✓ Edge coverage achieved: {edge_coverage:.1f}%")
    print(f"  ✓ Search nodes explored: {node_counter['count']}")
    
    # Step 6: Verify Euler formula
    print(f"\nStep 5: Verify Euler formula with found faces...")
    F_found = len(selected)
    euler = num_v - num_e + F_found
    euler_valid = (euler == 2 * num_components)
    print(f"  V={num_v}, E={num_e}, F={F_found}, c={num_components}")
    print(f"  V - E + F = {euler} (valid: {euler_valid}, expected {2 * num_components})")
    
    return selected
