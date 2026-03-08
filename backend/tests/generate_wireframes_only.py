"""Generate wireframe STL files (edges as tubes) for all test datasets."""

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


# ===============================
# Test Dataset 2: L-Shaped Solid
# ===============================
Lambda2 = [
    [0,0,0],[6,0,0],[6,2,0],[2,2,0],[2,6,0],[0,6,0],
    [0,0,6],[6,0,6],[6,2,6],[2,2,6],[2,6,6],[0,6,6]
]

Theta2 = [
    (0,1),(1,2),(2,3),(3,4),(4,5),(5,0),
    (6,7),(7,8),(8,9),(9,10),(10,11),(11,6),
    (0,6),(1,7),(2,8),(3,9),(4,10),(5,11)
]


# ===============================
# Test Dataset 3: Frame With Hole
# ===============================
Lambda3 = [
    [0,0,0],[8,0,0],[8,8,0],[0,8,0],
    [0,0,6],[8,0,6],[8,8,6],[0,8,6],
    [3,3,0],[5,3,0],[5,5,0],[3,5,0],
    [3,3,6],[5,3,6],[5,5,6],[3,5,6]
]

Theta3 = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7),
    (8,9),(9,10),(10,11),(11,8),
    (12,13),(13,14),(14,15),(15,12),
    (8,12),(9,13),(10,14),(11,15)
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


def create_tube_triangles(p1, p2, radius=0.05, segments=8):
    """Create a cylindrical tube between two points."""
    p1 = np.array(p1[:3], dtype=float)
    p2 = np.array(p2[:3], dtype=float)
    
    # Direction vector
    direction = p2 - p1
    length = np.linalg.norm(direction)
    if length < 1e-6:
        return []
    
    direction = direction / length
    
    # Find perpendicular vectors
    if abs(direction[2]) < 0.9:
        perp1 = np.cross(direction, np.array([0, 0, 1]))
    else:
        perp1 = np.cross(direction, np.array([1, 0, 0]))
    
    perp1 = perp1 / np.linalg.norm(perp1)
    perp2 = np.cross(direction, perp1)
    
    # Generate circle vertices at both ends
    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    
    vertices_start = []
    vertices_end = []
    
    for angle in angles:
        offset = radius * (np.cos(angle) * perp1 + np.sin(angle) * perp2)
        vertices_start.append(p1 + offset)
        vertices_end.append(p2 + offset)
    
    # Generate triangles
    triangles = []
    
    # Side faces
    for i in range(segments):
        next_i = (i + 1) % segments
        
        # Triangle 1
        triangles.append((
            vertices_start[i],
            vertices_end[i],
            vertices_start[next_i]
        ))
        
        # Triangle 2
        triangles.append((
            vertices_start[next_i],
            vertices_end[i],
            vertices_end[next_i]
        ))
    
    # Cap faces (optional, makes it closed)
    center_start = p1
    center_end = p2
    
    for i in range(segments):
        next_i = (i + 1) % segments
        
        # Start cap
        triangles.append((
            center_start,
            vertices_start[next_i],
            vertices_start[i]
        ))
        
        # End cap
        triangles.append((
            center_end,
            vertices_end[i],
            vertices_end[next_i]
        ))
    
    return triangles


def export_wireframe_stl(Lambda, Theta, output_path, tube_radius=0.05):
    """Export wireframe as STL with edges as tubes."""
    all_triangles = []
    
    # Generate tube for each edge
    for i, j in Theta:
        p1 = Lambda[i]
        p2 = Lambda[j]
        triangles = create_tube_triangles(p1, p2, radius=tube_radius)
        all_triangles.extend(triangles)
    
    # Write STL
    with open(output_path, 'w') as f:
        f.write("solid wireframe\n")
        
        for tri in all_triangles:
            p0, p1, p2 = tri
            
            # Calculate normal
            v1 = np.array(p1) - np.array(p0)
            v2 = np.array(p2) - np.array(p0)
            normal = np.cross(v1, v2)
            norm = np.linalg.norm(normal)
            if norm > 1e-6:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1])
            
            f.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
            f.write(f"    outer loop\n")
            f.write(f"      vertex {p0[0]:.6f} {p0[1]:.6f} {p0[2]:.6f}\n")
            f.write(f"      vertex {p1[0]:.6f} {p1[1]:.6f} {p1[2]:.6f}\n")
            f.write(f"      vertex {p2[0]:.6f} {p2[1]:.6f} {p2[2]:.6f}\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        
        f.write("endsolid wireframe\n")
    
    print(f"  ✓ Wireframe STL: {output_path.name} ({len(all_triangles)} triangles)")


def generate_all_wireframes():
    """Generate wireframe STL files for all datasets."""
    datasets = [
        ("Dataset 1: Stepped Block", Lambda1, Theta1),
        ("Dataset 2: L-Shaped Solid", Lambda2, Theta2),
        ("Dataset 3: Frame With Hole", Lambda3, Theta3),
        ("Dataset 4: Double-Step Mechanical", Lambda4, Theta4),
    ]
    
    output_dir = Path(__file__).parent.parent / "outputs" / "test_datasets"
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n{'#' * 70}")
    print(f"GENERATING WIREFRAME STL FILES")
    print(f"{'#' * 70}\n")
    
    for i, (name, Lambda, Theta) in enumerate(datasets, 1):
        print(f"Dataset {i}: {name.split(': ')[1]}")
        print(f"  V={len(Lambda)}, E={len(Theta)}")
        
        output_path = output_dir / f"dataset{i}_wireframe.stl"
        export_wireframe_stl(Lambda, Theta, output_path)
        print()
    
    print(f"{'#' * 70}")
    print(f"WIREFRAME FILES GENERATED")
    print(f"{'#' * 70}")
    print(f"\nOutput directory: {output_dir}")
    print(f"\nGenerated files:")
    print(f"  - dataset1_wireframe.stl")
    print(f"  - dataset2_wireframe.stl")
    print(f"  - dataset3_wireframe.stl")
    print(f"  - dataset4_wireframe.stl")
    print(f"\nOpen these in your STL viewer to inspect the wireframe geometry.")


if __name__ == "__main__":
    generate_all_wireframes()
