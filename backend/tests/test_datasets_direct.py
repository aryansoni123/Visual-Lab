"""Test all 4 datasets DIRECTLY (skip pseudo-wireframe reconstruction)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from algorithms.face_detection_minimal_artifacts import find_all_faces_minimal_artifacts
from algorithms.face_detection import triangulate_polygon, ensure_outward_normals, export_stl


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


def visualize_wireframe(Lambda, Theta, title, output_path):
    """Generate 3D wireframe visualization PNG."""
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot vertices
    vertices = np.array(Lambda)
    ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], 
               c='blue', marker='o', s=50, alpha=0.8, label='Vertices')
    
    # Plot edges
    for i, j in Theta:
        p1 = Lambda[i]
        p2 = Lambda[j]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], 
                'orange', linewidth=2, alpha=0.7)
    
    # Labels
    ax.set_xlabel('X', fontsize=12)
    ax.set_ylabel('Y', fontsize=12)
    ax.set_zlabel('Z', fontsize=12)
    ax.set_title(f'{title}\nV={len(Lambda)}, E={len(Theta)}', 
                 fontsize=14, fontweight='bold')
    ax.legend()
    
    # Set equal aspect ratio
    max_range = max(
        vertices[:, 0].max() - vertices[:, 0].min(),
        vertices[:, 1].max() - vertices[:, 1].min(),
        vertices[:, 2].max() - vertices[:, 2].min()
    )
    mid_x = (vertices[:, 0].max() + vertices[:, 0].min()) * 0.5
    mid_y = (vertices[:, 1].max() + vertices[:, 1].min()) * 0.5
    mid_z = (vertices[:, 2].max() + vertices[:, 2].min()) * 0.5
    ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
    ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
    ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ PNG: {output_path.name}")


def generate_stl_direct(Lambda, Theta, dataset_name, output_path):
    """Generate STL file directly from Lambda/Theta (skip reconstruction)."""
    print(f"\n{'=' * 70}")
    print(f"{dataset_name}")
    print(f"{'=' * 70}")
    print(f"Input: V={len(Lambda)}, E={len(Theta)}")
    
    # Face detection
    faces = find_all_faces_minimal_artifacts(Lambda, Theta)
    
    if faces is None:
        print(f"  ✗ Face detection failed!")
        return False
    
    print(f"\n  ✓ Faces detected: {len(faces)}")
    
    # Triangulation
    triangles = []
    for face in faces:
        triangles.extend(triangulate_polygon(face, Lambda))
    triangles = ensure_outward_normals(triangles, Lambda)
    
    print(f"  ✓ Triangles: {len(triangles)}")
    
    # Export STL
    export_stl(output_path, triangles, Lambda)
    print(f"  ✓ STL: {output_path.name}")
    
    # Euler validation (generalised: V - E + F = 2*c)
    from algorithms.face_detection_minimal_artifacts import count_connected_components
    V, E, F = len(Lambda), len(Theta), len(faces)
    c = count_connected_components(Theta, V)
    euler = V - E + F
    euler_valid = (euler == 2 * c)
    print(f"\n  Euler: V={V}, E={E}, F={F}, c={c} → V-E+F={euler} (expected {2*c}) {'✓' if euler_valid else '✗'}")
    
    return True


def test_all_datasets():
    """Test all 4 datasets."""
    datasets = [
        ("Dataset 1: Stepped Block", Lambda1, Theta1),
        ("Dataset 2: L-Shaped Solid", Lambda2, Theta2),
        ("Dataset 3: Frame With Hole", Lambda3, Theta3),
        ("Dataset 4: Double-Step Mechanical", Lambda4, Theta4),
    ]
    
    output_dir = Path(__file__).parent.parent / "outputs" / "test_datasets"
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n{'#' * 70}")
    print(f"TESTING ALL DATASETS (DIRECT LAMBDA/THETA)")
    print(f"{'#' * 70}")
    print(f"Output: {output_dir}\n")
    
    results = []
    
    for i, (name, Lambda, Theta) in enumerate(datasets, 1):
        print(f"\n{'*' * 70}")
        print(f"Dataset {i}: {name.split(': ')[1]}")
        print(f"{'*' * 70}")
        
        # Generate wireframe PNG
        png_path = output_dir / f"dataset{i}_wireframe.png"
        visualize_wireframe(Lambda, Theta, name, png_path)
        
        # Generate STL
        stl_path = output_dir / f"dataset{i}_mesh.stl"
        try:
            success = generate_stl_direct(Lambda, Theta, name, stl_path)
            results.append((i, name, success))
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            results.append((i, name, False))
    
    # Summary
    print(f"\n\n{'#' * 70}")
    print(f"SUMMARY")
    print(f"{'#' * 70}")
    for i, name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  Dataset {i}: {status}")
    
    success_count = sum(1 for _, _, s in results if s)
    print(f"\nTotal: {success_count}/{len(results)} successful")
    print(f"\nOutput directory: {output_dir}")


if __name__ == "__main__":
    test_all_datasets()
