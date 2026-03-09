"""Analyze and diagnose geometry issues in test datasets."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np


# ===============================
# Test Dataset 1: Stepped Block
# ===============================
Lambda1 = [
    [0,0,0], [6,0,0], [6,4,0], [0,4,0],
    [0,0,6], [6,0,6], [6,4,6], [0,4,6],
    [2,0,6], [4,0,6], [4,4,6], [2,4,6],
    [2,0,9], [4,0,9], [4,4,9], [2,4,9]
]

Theta1 = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7),
    (8,9),(9,10),(10,11),(11,8),
    (12,13),(13,14),(14,15),(15,12),
    (8,12),(9,13),(10,14),(11,15),
    (8,4),(9,5),(10,6),(11,7)
]


# =======================================
# Test Dataset 4: Double-Step Mechanical
# =======================================
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


def analyze_dataset(name, Lambda, Theta):
    """Analyze geometry structure of a dataset."""
    print(f"\n{'=' * 70}")
    print(f"{name}")
    print(f"{'=' * 70}\n")
    
    vertices = np.array(Lambda)
    
    # Group vertices by Z-level
    z_levels = {}
    for i, v in enumerate(Lambda):
        z = v[2]
        if z not in z_levels:
            z_levels[z] = []
        z_levels[z].append((i, v))
    
    print(f"VERTICES BY Z-LEVEL:")
    print(f"-" * 70)
    for z in sorted(z_levels.keys()):
        print(f"\nZ = {z}:")
        for idx, v in z_levels[z]:
            print(f"  Vertex {idx:2d}: ({v[0]:5.1f}, {v[1]:5.1f}, {v[2]:5.1f})")
    
    # Analyze bounding boxes per level
    print(f"\n\nBOUNDING BOXES PER Z-LEVEL:")
    print(f"-" * 70)
    for z in sorted(z_levels.keys()):
        level_verts = np.array([v for _, v in z_levels[z]])
        x_min, x_max = level_verts[:, 0].min(), level_verts[:, 0].max()
        y_min, y_max = level_verts[:, 1].min(), level_verts[:, 1].max()
        print(f"Z = {z:5.1f}: X=[{x_min:5.1f}, {x_max:5.1f}], Y=[{y_min:5.1f}, {y_max:5.1f}]  "
              f"(Width={x_max-x_min:.1f}, Depth={y_max-y_min:.1f})")
    
    # Overall bounding box
    print(f"\n\nOVERALL BOUNDING BOX:")
    print(f"-" * 70)
    x_min, x_max = vertices[:, 0].min(), vertices[:, 0].max()
    y_min, y_max = vertices[:, 1].min(), vertices[:, 1].max()
    z_min, z_max = vertices[:, 2].min(), vertices[:, 2].max()
    print(f"X: [{x_min:.1f}, {x_max:.1f}]  (Width: {x_max-x_min:.1f})")
    print(f"Y: [{y_min:.1f}, {y_max:.1f}]  (Depth: {y_max-y_min:.1f})")
    print(f"Z: [{z_min:.1f}, {z_max:.1f}]  (Height: {z_max-z_min:.1f})")
    
    # Analyze edge connections
    print(f"\n\nEDGE CONNECTIVITY:")
    print(f"-" * 70)
    
    # Vertical edges (same X, Y, different Z)
    # Horizontal edges (different X or Y, same Z)
    vertical = []
    horizontal = []
    
    for i, j in Theta:
        v1 = np.array(Lambda[i])
        v2 = np.array(Lambda[j])
        
        if v1[2] != v2[2]:
            vertical.append((i, j))
        else:
            horizontal.append((i, j))
    
    print(f"Vertical edges (connecting Z-levels): {len(vertical)}")
    for i, j in vertical:
        v1 = Lambda[i]
        v2 = Lambda[j]
        print(f"  {i:2d}→{j:2d}: ({v1[0]:.1f},{v1[1]:.1f},{v1[2]:.1f}) → ({v2[0]:.1f},{v2[1]:.1f},{v2[2]:.1f})")
    
    print(f"\nHorizontal edges (within Z-level): {len(horizontal)}")
    by_z = {}
    for i, j in horizontal:
        z = Lambda[i][2]
        if z not in by_z:
            by_z[z] = []
        by_z[z].append((i, j))
    
    for z in sorted(by_z.keys()):
        print(f"\n  At Z={z}:")
        for i, j in by_z[z]:
            v1 = Lambda[i]
            v2 = Lambda[j]
            print(f"    {i:2d}→{j:2d}: ({v1[0]:.1f},{v1[1]:.1f}) → ({v2[0]:.1f},{v2[1]:.1f})")


def main():
    """Analyze datasets 1 and 4."""
    print(f"\n{'#' * 70}")
    print(f"GEOMETRY DIAGNOSTIC ANALYSIS")
    print(f"{'#' * 70}")
    
    analyze_dataset("Dataset 1: Stepped Block", Lambda1, Theta1)
    analyze_dataset("Dataset 4: Double-Step Mechanical", Lambda4, Theta4)
    
    print(f"\n\n{'#' * 70}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'#' * 70}\n")


if __name__ == "__main__":
    main()
