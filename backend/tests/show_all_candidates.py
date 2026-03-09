"""Show all 18 planar face candidates for Dataset 4."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from algorithms.face_detection_minimal_artifacts import (
    find_simple_cycles_bfs,
    is_cycle_coplanar,
    cycle_edge_keys,
    polygon_area_3d
)


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


print(f"\n{'=' * 70}")
print(f"ALL PLANAR FACE CANDIDATES FOR DATASET 4")
print(f"{'=' * 70}\n")

cycles = find_simple_cycles_bfs(Theta4, max_cycle_length=15)

candidate_by_edges = {}
for cycle in cycles:
    is_planar, _, _ = is_cycle_coplanar(cycle, Lambda4)
    if not is_planar:
        continue
    
    edges = frozenset(cycle_edge_keys(cycle))
    if not edges:
        continue
    
    area = polygon_area_3d(cycle, Lambda4)
    
    if edges not in candidate_by_edges or len(cycle) < len(candidate_by_edges[edges]["cycle"]):
        candidate_by_edges[edges] = {"cycle": cycle, "edges": set(edges), "area": area}

candidates = list(candidate_by_edges.values())
ordered = sorted(candidates, key=lambda c: (len(c["cycle"]), -c["area"]))

print(f"Total planar candidates: {len(ordered)}\n")

for i, cand in enumerate(ordered, 1):
    cycle = cand["cycle"]
    z_vals = [Lambda4[v][2] for v in cycle]
    z_level = z_vals[0] if len(set(z_vals)) == 1 else "mixed"
    
    # Check if this is top or bottom face
    label = ""
    if set(cycle) == {20, 21, 22, 23}:
        label = "← TOP FACE (Z=12)"
    elif set(cycle) == {16, 17, 18, 19}:
        label = "← BOTTOM FACE (Z=9)"
    
    print(f"{i:2d}. Size={len(cycle)}, Z={z_level:5}, Cycle={cycle} {label}")

print(f"\n{'=' * 70}\n")
print("The algorithm sorts by smallest size first, then tries combinations.")
print("It finds a valid set of 14 faces, but not necessarily the 'best' set.")
