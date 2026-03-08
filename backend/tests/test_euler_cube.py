"""
Test Euler-driven face detection on a simple cube.
Expected: 8 vertices, 12 edges, 6 faces (passes Euler test)
"""

from algorithms.face_detection_euler_driven import find_all_faces_euler_driven, triangulate_polygon, ensure_outward_normals, export_stl

# Simple unit cube
Lambda = [
    [0, 0, 0],  # 0
    [1, 0, 0],  # 1
    [1, 1, 0],  # 2
    [0, 1, 0],  # 3
    [0, 0, 1],  # 4
    [1, 0, 1],  # 5
    [1, 1, 1],  # 6
    [0, 1, 1],  # 7
]

Theta = [
    # Bottom face (z=0)
    (0, 1), (1, 2), (2, 3), (3, 0),
    # Top face (z=1)
    (4, 5), (5, 6), (6, 7), (7, 4),
    # Vertical edges
    (0, 4), (1, 5), (2, 6), (3, 7),
]

print("=" * 70)
print("TEST: Simple Unit Cube")
print("=" * 70)
print(f"\nExpected: V=8, E=12, F=6 (Euler: 8-12+6=2)")

faces = find_all_faces_euler_driven(Lambda, Theta)

print(f"\nResult: {len(faces)} faces found")

if len(faces) == 6:
    print("✓ PASS: Correct number of faces!")
    
    # Triangulate and export
    triangles = []
    for face in faces:
        triangles.extend(triangulate_polygon(face, Lambda))
    
    triangles = ensure_outward_normals(triangles, Lambda)
    export_stl("test_cube_euler_driven.stl", triangles, Lambda)
    print("✓ Exported to test_cube_euler_driven.stl")
else:
    print(f"✗ FAIL: Expected 6 faces, got {len(faces)}")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {face}")
