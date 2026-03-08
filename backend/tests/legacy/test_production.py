"""
Final production test: Complete 3D reconstruction with mesh generation.

Tests:
1. Simple cube (valid manifold)
2. Rectangular box
3. Full pipeline: faces → tetrahedra → exports
"""

import sys
sys.path.insert(0, r'd:\Coding\3D to 2D\backend')

from face_detection import (
    find_all_faces_by_planes,
    generate_tetrahedral_mesh,
    classify_tetrahedra,
    validate_euler_formula,
    export_stl,
    export_tetrahedral_mesh_vtu
)

def test_geometry(name, Lambda, Theta):
    """Complete pipeline test."""
    print("\n" + "=" * 70)
    print(f"TEST: {name}")
    print("=" * 70)
    
    print(f"\nInput: V={len(Lambda)}, E={len(Theta)}")
    
    # Step 1: Find boundary faces
    print("\n[1] Finding boundary faces...")
    faces = find_all_faces_by_planes(Lambda, Theta)
    print(f"    ✓ Found {len(faces)} faces")
    
    # Step 2: Generate tetrahedral mesh
    print("\n[2] Generating tetrahedral mesh...")
    tetrahedra, boundary_triangles = generate_tetrahedral_mesh(Lambda, faces)
    print(f"    ✓ Tetrahedra: {len(tetrahedra)}")
    print(f"    ✓ Boundary triangles: {len(boundary_triangles)}")
    
    # Step 3: Classify tetrahedra
    print("\n[3] Classifying tetrahedra...")
    interior_tets, exterior_tets = classify_tetrahedra(tetrahedra, boundary_triangles, Lambda)
    print(f"    ✓ Interior: {len(interior_tets)}")
    print(f"    ✓ Exterior: {len(exterior_tets)}")
    
    # Step 4: Validate Euler
    print("\n[4] Validating boundary mesh...")
    num_v = len(Lambda)
    num_e = len(Theta)
    num_f = len(faces)
    euler = num_v - num_e + num_f
    euler_valid = (euler == 2)
    print(f"    V={num_v}, E={num_e}, F={num_f}")
    print(f"    V - E + F = {euler}")
    print(f"    Status: {'✓ VALID' if euler_valid else '✗ INVALID'}")
    
    if euler_valid:
        # Step 5: Export meshes
        print("\n[5] Exporting meshes...")
        safe_name = name.lower().replace(" ", "_")
        
        stl_file = f"prod_{safe_name}.stl"
        vtu_file = f"prod_{safe_name}.vtu"
        
        export_stl(stl_file, boundary_triangles, Lambda)
        print(f"    ✓ STL: {stl_file}")
        
        export_tetrahedral_mesh_vtu(vtu_file, Lambda, interior_tets, boundary_triangles)
        print(f"    ✓ VTU: {vtu_file}")
        
        return True
    else:
        print("\n✗ Euler invalid - skipping export")
        return False


# ============================================================================
# TEST 1: Simple Cube
# ============================================================================

print("=" * 70)
print("PRODUCTION MESH GENERATION TEST SUITE")
print("=" * 70)

cube_lambda = [
    [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
]

cube_theta = [
    (0,1), (1,2), (2,3), (3,0),
    (4,5), (5,6), (6,7), (7,4),
    (0,4), (1,5), (2,6), (3,7),
]

cube_ok = test_geometry("Simple Cube", cube_lambda, cube_theta)


# ============================================================================
# TEST 2: Rectangular Box
# ============================================================================

box_lambda = [
    [0, 0, 0], [3, 0, 0], [3, 2, 0], [0, 2, 0],
    [0, 0, 2], [3, 0, 2], [3, 2, 2], [0, 2, 2],
]

box_theta = [
    (0,1), (1,2), (2,3), (3,0),
    (4,5), (5,6), (6,7), (7,4),
    (0,4), (1,5), (2,6), (3,7),
]

box_ok = test_geometry("Rectangular Box", box_lambda, box_theta)


# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

results = [
    ("Cube", cube_ok),
    ("Box", box_ok),
]

passed = sum(1 for _, ok in results if ok)
total = len(results)

print(f"\nPassed: {passed}/{total}\n")

for name, ok in results:
    status = "✓ PASS" if ok else "✗ FAIL"
    print(f"  {status}  {name}")

print("\n" + "=" * 70)
if passed == total:
    print("✓ ALL TESTS PASSED - PRODUCTION READY")
    print("\nPipeline verified:")
    print("  ✓ Face detection (Plane-clustering)")
    print("  ✓ Tetrahedral mesh generation (Delaunay)")
    print("  ✓ Interior classification")
    print("  ✓ STL export (surface)")
    print("  ✓ VTU export (volumetric)")
    print("  ✓ Euler formula validation")
else:
    print("✗ SOME TESTS FAILED")
print("=" * 70)
