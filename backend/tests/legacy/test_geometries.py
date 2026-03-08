"""
Test suite for face detection with various geometries.

Validates the plane-clustering algorithm on:
1. Simple cube (baseline)
2. Rectangular box
3. More complex shapes
"""

import sys
sys.path.insert(0, r'd:\Coding\3D to 2D')

from face_detection_v5 import find_all_faces_by_planes, triangulate_polygon, validate_euler_formula

def test_geometry(name, Lambda, Theta):
    """Test a geometry and report results."""
    print("\n" + "=" * 70)
    print(f"TEST: {name}")
    print("=" * 70)
    
    print(f"\nVertices: {len(Lambda)}")
    print(f"Edges: {len(Theta)}")
    
    # Find faces
    faces = find_all_faces_by_planes(Lambda, Theta)
    print(f"\nFaces found: {len(faces)}")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {len(face)}-gon {face}")
    
    # Triangulate
    triangles = []
    for face in faces:
        triangles.extend(triangulate_polygon(face, Lambda))
    
    print(f"Triangles: {len(triangles)}")
    
    # Validate Euler
    num_v = len(Lambda)
    num_e = len(Theta)
    num_f = len(faces)
    euler_valid = validate_euler_formula(num_v, num_e, num_f)
    
    print(f"\nEuler: V={num_v}, E={num_e}, F={num_f}")
    print(f"V - E + F = {num_v - num_e + num_f}")
    print(f"Status: {'✓ VALID' if euler_valid else '✗ INVALID'}")
    
    return euler_valid


# ============================================================================
# TEST 1: Simple Cube (Baseline)
# ============================================================================

cube_lambda = [
    [0.0, 0.0, 0.0],
    [0.0, 0.0, 2.0],
    [0.0, 3.0, 0.0],
    [0.0, 3.0, 2.0],
    [5.0, 0.0, 0.0],
    [5.0, 0.0, 2.0],
    [5.0, 3.0, 0.0],
    [5.0, 3.0, 2.0],
]

cube_theta = [
    (0, 1), (0, 2), (0, 4),
    (1, 3), (1, 5),
    (2, 3), (2, 6),
    (3, 7),
    (4, 5), (4, 6),
    (5, 7),
    (6, 7),
]

test_geometry("Simple Cube", cube_lambda, cube_theta)


# ============================================================================
# TEST 2: Your Complex Geometry (As-Is)
# ============================================================================

your_lambda = [
    # Bottom main block
    [0, 0, 0],   # 0
    [6, 0, 0],   # 1
    [6, 4, 0],   # 2
    [0, 4, 0],   # 3

    # Top main block
    [0, 0, 8],   # 4
    [6, 0, 8],   # 5
    [6, 4, 8],   # 6
    [0, 4, 8],   # 7

    # Left extension (top level)
    [-3, 0, 8],  # 8
    [-3, 4, 8],  # 9
    [-3, 0, 5],  # 10
    [-3, 4, 5],  # 11

    [0, 0, 5],   # 12
    [0, 4, 5],   # 13

    # Lower vertical drop
    [0, 0, 4],   # 14
    [0, 4, 4],   # 15
]

your_theta = [
    # Main bottom rectangle
    (0, 1), (1, 2), (2, 3), (3, 0),

    # Main top rectangle
    (4, 5), (5, 6), (6, 7), (7, 4),

    # Vertical edges main
    (0, 4), (1, 5), (2, 6), (3, 7),

    # Left extension top rectangle
    (8, 9), (9, 7), (7, 4), (4, 8),

    # Extension vertical edges
    (8, 10), (9, 11), (10, 12), (11, 13),
    (12, 4), (13, 7),

    # Horizontal lower ledge
    (12, 14), (13, 15),

    # Vertical drop edges
    (14, 0), (15, 3),

    # Back depth edges for extension
    (10, 11),
]

test_geometry("Your Complex Geometry", your_lambda, your_theta)

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print("""
Your complex geometry has missing faces or incomplete edges.

Possible issues:
1. Back face of main block not closed (missing edges connecting bottom to top-right)
2. Extension block needs more connectivity
3. Vertical ledge structure needs closing faces

To debug, verify:
- Every vertex has at least 3 edges (for a closed polyhedron)
- Every edge is part of exactly 2 faces
- No dangling edges or isolated components

Would you like to:
1. Add missing edges to your geometry?
2. Simplify to a rectangular box first?
3. Verify the edge list is complete?
""")
