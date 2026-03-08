"""
Test largest-face-first face detection on the provided L-shaped geometry.
"""

from algorithms.face_detection import find_all_faces_by_planes, triangulate_polygon, ensure_outward_normals, export_stl, validate_euler_formula, generate_tetrahedral_mesh

Lambda = [
    # Bottom main block
    [0, 0, 0, 0, 0, 0],      # 0
    [6, 0, 0, 0, 0, 0],      # 1
    [6, 4, 0, 0, 0, 0],      # 2
    [0, 4, 0, 0, 0, 0],      # 3
    
    # Top main block
    [0, 0, 8, 0, 0, 0],      # 4
    [6, 0, 8, 0, 0, 0],      # 5
    [6, 4, 8, 0, 0, 0],      # 6
    [0, 4, 8, 0, 0, 0],      # 7
    
    # Left extension (top level)
    [-3, 0, 8, 0, 0, 0],     # 8
    [-3, 4, 8, 0, 0, 0],     # 9
    [-3, 0, 5, 0, 0, 0],     # 10
    [-3, 4, 5, 0, 0, 0],     # 11
    
    [0, 0, 5, 0, 0, 0],      # 12
    [0, 4, 5, 0, 0, 0],      # 13
    
    # Lower vertical drop
    [0, 0, 4, 0, 0, 0],      # 14
    [0, 4, 4, 0, 0, 0],      # 15
]

Theta = [
    # Main block bottom rectangle
    (0,1),(1,2),(2,3),(3,0),
    
    # Main block top rectangle
    (4,5),(5,6),(6,7),(7,4),
    
    # Main block vertical edges
    (0,4),(1,5),(2,6),(3,7),
    
    # Main block front face (y=0): (0,1,5,4)
    (4,0),
    
    # Main block back face (y=4): (3,2,6,7)
    (3,2),
    
    # Main block right face (x=6): (1,2,6,5)
    (5,1),
    
    # Left extension top face (z=8): (8,9,7,4)
    (8,9),(9,7),(7,4),(4,8),
    
    # Left extension vertical edges
    (8,10),(9,11),(10,12),(11,13),
    
    # Left extension inner step faces
    (12,4),(13,7),
    
    # Left extension back face (x=-3): (8,10,11,9)
    (11,9),
    
    # Lower ledge horizontal edges
    (12,14),(13,15),
    
    # Lower ledge inner edge
    (12,13),
    
    # Lower ledge bottom edge
    (14,15),
    
    # Lower drop vertical edges
    (14,0),(15,3),
    
    # Left extension depth edge
    (10,11),
]

print("=" * 80)
print("TESTING LARGEST-FACE-FIRST DETECTION ON L-SHAPED GEOMETRY")
print("=" * 80)

# Find faces
faces = find_all_faces_by_planes(Lambda, Theta)

print(f"\n✓ Found {len(faces)} faces")

# Print face details
print("\nDetailed face information:")
for i, face in enumerate(faces):
    print(f"  Face {i}: {len(face)}-gon vertices={face}")

# Triangulate
print("\nTriangulating...")
triangles = []
for face in faces:
    triangles.extend(triangulate_polygon(face, Lambda))

print(f"  Generated {len(triangles)} triangles from {len(faces)} faces")

# Fix normals
print("Correcting normal orientation...")
triangles = ensure_outward_normals(triangles, Lambda)

# Export STL
print("Exporting to STL...")
export_stl("test_lshape_final.stl", triangles, Lambda)

print("\n✓ Exported to test_lshape_final.stl")
print(f"  Total triangles: {len(triangles)}")

# Generate tetrahedral mesh
print("\nGenerating tetrahedral mesh...")
tetrahedra, boundary_triangles = generate_tetrahedral_mesh(Lambda, faces)

print(f"  Tetrahedra: {len(tetrahedra)}")
print(f"  Boundary triangles: {len(boundary_triangles)}")

# Final validation
print("\nFinal validation:")
num_v = len(Lambda)
num_e = len(Theta)
num_f = len(faces)
euler_valid = validate_euler_formula(num_v, num_e, num_f)
print(f"  V={num_v}, E={num_e}, F={num_f}")
print(f"  V - E + F = {num_v - num_e + num_f}")
print(f"  Euler valid: {euler_valid}")

if euler_valid:
    print("\n✓✓✓ SUCCESS: Full pipeline passed! ✓✓✓")
else:
    print("\n✗ EULER VALIDATION FAILED")
