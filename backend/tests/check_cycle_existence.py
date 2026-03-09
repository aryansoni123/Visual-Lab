"""Check if the top face cycle exists in the enumeration."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import defaultdict


Lambda4 = [
    [0,0,0],[8,0,0],[8,4,0],[0,4,0],
    [0,0,6],[8,0,6],[8,4,6],[0,4,6],
    [2,0,6],[6,0,6],[6,4,6],[2,4,6],
    [2,0,9],[6,0,9],[6,4,9],[2,4,9],
    [3,0,9],[5,0,9],[5,4,9],[3,4,9],
    [3,0,12],[5,0,12],[5,4,12],[3,4,12]
]

Theta4 = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7),
    (8,9),(9,10),(10,11),(11,8),
    (12,13),(13,14),(14,15),(15,12),
    (8,12),(9,13),(10,14),(11,15),
    (16,17),(17,18),(18,19),(19,16),
    (20,21),(21,22),(22,23),(23,20),
    (16,20),(17,21),(18,22),(19,23)
]


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


print("Searching for cycles involving vertices 20, 21, 22, 23...")
print()

cycles = find_simple_cycles_bfs(Theta4, max_cycle_length=15)

top_face_vertices = {20, 21, 22, 23}
bottom_face_z9_vertices = {16, 17, 18, 19}

found_top = []
found_bottom_z9 = []

for cycle in cycles:
    cycle_set = set(cycle)
    if cycle_set == top_face_vertices:
        found_top.append(cycle)
    if cycle_set == bottom_face_z9_vertices:
        found_bottom_z9.append(cycle)

print(f"Total cycles found: {len(cycles)}")
print()
print(f"Cycles matching top face [20,21,22,23]:")
if found_top:
    for c in found_top:
        print(f"  {c}")
else:
    print("  ✗ NOT FOUND")

print()
print(f"Cycles matching bottom face at Z=9 [16,17,18,19]:")
if found_bottom_z9:
    for c in found_bottom_z9:
        print(f"  {c}")
else:
    print("  ✗ NOT FOUND")

# Check adjacency for these vertices
print()
print("Adjacency check:")
adj = build_adjacency(Theta4)
for v in [16, 17, 18, 19, 20, 21, 22, 23]:
    print(f"  Vertex {v}: neighbors = {sorted(adj[v])}")
