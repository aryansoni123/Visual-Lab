"""
End-to-End: Calibrated 2D Views → 3D Mesh → STL Export

Pipeline:
1. Load calibrated multiview.json (from multiview_calibrate.py)
2. Pass normalized 2D graphs to pseudo-wireframe reconstruction
3. Detect faces using minimal-artifacts algorithm
4. Triangulate faces
5. Export as STL mesh
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper
from algorithms.face_detection_minimal_artifacts import find_all_faces_minimal_artifacts
from algorithms.face_detection import triangulate_polygon, export_stl

TOL = 1e-6


def load_calibrated_views(json_path):
    """Load calibrated multiview data from JSON."""
    print(f"\nLoading calibrated views: {json_path}")
    print("-" * 70)
    
    with open(json_path) as f:
        data = json.load(f)
    
    front_verts = data['front']['vertices']
    front_edges = data['front']['edges']
    top_verts = data['top']['vertices']
    top_edges = data['top']['edges']
    side_verts = data['side']['vertices']
    side_edges = data['side']['edges']
    
    print(f"Front: {len(front_verts)} vertices, {len(front_edges)} edges")
    print(f"Top:   {len(top_verts)} vertices, {len(top_edges)} edges")
    print(f"Side:  {len(side_verts)} vertices, {len(side_edges)} edges")
    
    return front_verts, front_edges, top_verts, top_edges, side_verts, side_edges


def reconstruct_3d_wireframe(front_verts, front_edges, top_verts, top_edges, side_verts, side_edges):
    """
    Reconstruct 3D wireframe from calibrated 2D views.
    """
    print("\n" + "="*70)
    print("STAGE 1: 3D WIREFRAME RECONSTRUCTION")
    print("="*70)
    
    # Call pseudo-wireframe builder
    # Note: These are normalized 2D coordinates, so we pass them directly
    try:
        Lambda, Theta, metadata = build_pseudo_wireframe_paper(
            front_verts, front_edges,
            top_verts, top_edges,
            side_verts, side_edges,
            split_intersections=True,
        )
        
        print(f"\n✓ Lambda (3D vertices): {len(Lambda)}")
        print(f"✓ Theta (3D edges): {len(Theta)}")
        
        if len(Lambda) == 0:
            raise RuntimeError("No 3D vertices reconstructed")
        
        return Lambda, Theta
        
    except Exception as e:
        print(f"✗ Reconstruction failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def detect_faces(Lambda, Theta):
    """
    Detect faces from 3D wireframe.
    """
    print("\n" + "="*70)
    print("STAGE 2: FACE DETECTION (MINIMAL ARTIFACTS)")
    print("="*70)
    
    try:
        faces = find_all_faces_minimal_artifacts(Lambda, Theta)
        
        if faces is None:
            print("✗ Face detection returned None")
            return None
        
        print(f"\n✓ Faces detected: {len(faces) if faces else 0}")
        
        if faces:
            for i, face in enumerate(faces[:5]):
                print(f"  Face {i}: {len(face)}-gon {face}")
            if len(faces) > 5:
                print(f"  ... and {len(faces) - 5} more faces")
        
        return faces
        
    except Exception as e:
        print(f"✗ Face detection failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def triangulate_and_export(Lambda, faces, output_stl):
    """
    Triangulate faces and export as STL.
    """
    print("\n" + "="*70)
    print("STAGE 3: TRIANGULATION & STL EXPORT")
    print("="*70)
    
    if not faces:
        print("✗ No faces to triangulate")
        return False
    
    try:
        triangles = []
        
        for i, face in enumerate(faces):
            try:
                tris = triangulate_polygon(face, Lambda)
                if tris:
                    triangles.extend(tris)
                    if i < 5:
                        print(f"  Face {i}: {len(face)}-gon → {len(tris)} triangles")
            except Exception as e:
                if i < 5:
                    print(f"  Face {i}: ERROR - {e}")
        
        print(f"\n✓ Total triangles: {len(triangles)}")
        
        if not triangles:
            print("✗ No triangles generated")
            return False
        
        # Export STL
        print(f"\nExporting STL: {output_stl}")
        export_stl(output_stl, triangles, Lambda)
        
        # Verify file exists
        if os.path.exists(output_stl):
            file_size = os.path.getsize(output_stl)
            print(f"✓ STL file created: {file_size} bytes")
            return True
        else:
            print(f"✗ STL file not created")
            return False
        
    except Exception as e:
        print(f"✗ Triangulation/Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Main pipeline: calibrated views → 3D mesh → STL
    """
    
    print("=" * 70)
    print("MULTI-VIEW CALIBRATION → 3D MESH → STL")
    print("=" * 70)
    
    # Paths
    calibrated_json = '../outputs/calibrated_multiview.json'
    output_stl = '../outputs/mesh_from_calibrated_views.stl'
    
    # Step 1: Load calibrated data
    if not os.path.exists(calibrated_json):
        print(f"✗ Calibrated JSON not found: {calibrated_json}")
        print(f"  Run multiview_calibrate.py first")
        return False
    
    front_v, front_e, top_v, top_e, side_v, side_e = load_calibrated_views(
        calibrated_json
    )
    
    # Step 2: Reconstruct 3D wireframe
    Lambda, Theta = reconstruct_3d_wireframe(
        front_v, front_e, top_v, top_e, side_v, side_e
    )
    
    if Lambda is None or len(Lambda) == 0:
        print("\n✗ 3D reconstruction failed")
        return False
    
    # Step 3: Detect faces
    faces = detect_faces(Lambda, Theta)
    
    if not faces:
        print("\n✗ Face detection failed")
        return False
    
    # Step 4: Triangulate and export
    success = triangulate_and_export(Lambda, faces, output_stl)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Input views: FRONT_T.png, TOP_T.png, SIDE_T.png")
    print(f"Calibration: {calibrated_json}")
    print(f"3D vertices: {len(Lambda)}")
    print(f"3D edges: {len(Theta)}")
    print(f"Faces: {len(faces) if faces else 0}")
    print(f"Output STL: {output_stl}")
    
    if success:
        print("\n✓ SUCCESS: 3D mesh generated!")
        return True
    else:
        print("\n✗ FAILED: STL generation incomplete")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
