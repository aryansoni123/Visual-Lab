"""
End-to-End Pipeline: Image → 3D Pseudo-Wireframe → Faces → STL

Orchestrates:
1. Image processing (image_processing.py)
2. Pseudo-wireframe reconstruction (pseudo_wireframe.py)
3. Face detection (face_detection.py)
4. STL export
"""

import sys
import numpy as np
from reconstruction.image_processing import process_three_views
from reconstruction.pseudo_wireframe import build_pseudo_wireframe
from algorithms.face_detection import find_all_faces_by_planes, triangulate_polygon, export_stl

TOL = 1e-6


def normalize_2d_coordinates(vertices_dict):
    """
    Normalize 2D vertex coordinates across all views.
    
    Ensures consistent scaling and origin.
    
    Args:
        vertices_dict: {view: [list of (x, y) tuples]}
    
    Returns:
        normalized vertices_dict
    """
    normalized = {}
    
    for view in ['front', 'top', 'side']:
        vertices = vertices_dict.get(view, [])
        
        if not vertices:
            normalized[view] = []
            continue
        
        vertices = np.array(vertices)
        
        # Translate to origin
        min_coords = vertices.min(axis=0)
        vertices = vertices - min_coords
        
        # Normalize to [0, 1] range
        max_coords = vertices.max(axis=0)
        if max_coords[0] > TOL and max_coords[1] > TOL:
            vertices = vertices / max_coords
        
        normalized[view] = vertices.tolist()
    
    return normalized


def reconstruct_from_images(front_image, top_image, side_image, output_stl=None):
    """
    Complete 3D reconstruction pipeline from three 2D orthographic images.
    
    Args:
        front_image: Path to front view image
        top_image: Path to top view image
        side_image: Path to side view image
        output_stl: Path to output STL file (optional)
    
    Returns:
        {
            'Lambda': list of 3D vertices,
            'Theta': list of 3D edges,
            'faces': list of faces (each is list of vertex indices),
            'triangles': list of triangles,
            'status': completion status message
        }
    """
    
    print("=" * 70)
    print("3D RECONSTRUCTION PIPELINE")
    print("=" * 70)
    
    # ========== STAGE 1: IMAGE PROCESSING ==========
    print("\nStage 1: Image Processing")
    print("-" * 70)
    
    try:
        views_data = process_three_views(front_image, top_image, side_image)
    except Exception as e:
        return {
            'Lambda': [],
            'Theta': [],
            'faces': [],
            'triangles': [],
            'status': f'Image processing failed: {e}'
        }
    
    # Extract vertices and edges per view
    front_vertices, front_edges, front_visibility = views_data['front']
    top_vertices, top_edges, top_visibility = views_data['top']
    side_vertices, side_edges, side_visibility = views_data['side']
    
    print(f"\nFront: {len(front_vertices)} vertices, {len(front_edges)} edges")
    print(f"  Visible: {sum(front_visibility)}, Hidden: {len(front_visibility) - sum(front_visibility)}")
    print(f"Top:   {len(top_vertices)} vertices, {len(top_edges)} edges")
    print(f"  Visible: {sum(top_visibility)}, Hidden: {len(top_visibility) - sum(top_visibility)}")
    print(f"Side:  {len(side_vertices)} vertices, {len(side_edges)} edges")
    print(f"  Visible: {sum(side_visibility)}, Hidden: {len(side_visibility) - sum(side_visibility)}")
    
    # ========== STAGE 2: PSEUDO-WIREFRAME RECONSTRUCTION ==========
    print("\nStage 2: Pseudo-Wireframe Reconstruction (Furferi Algorithm)")
    print("-" * 70)
    
    try:
        # Prepare projections for pseudo_wireframe
        front_proj = {
            'vertices': front_vertices,
            'edges': front_edges,
            'visibility': front_visibility
        }
        top_proj = {
            'vertices': top_vertices,
            'edges': top_edges,
            'visibility': top_visibility
        }
        side_proj = {
            'vertices': side_vertices,
            'edges': side_edges,
            'visibility': side_visibility
        }
        
        # Call pseudo-wireframe builder
        Lambda, Theta = build_pseudo_wireframe(
            front_proj['vertices'], front_proj['edges'],
            top_proj['vertices'], top_proj['edges'],
            side_proj['vertices'], side_proj['edges']
        )
        
    except Exception as e:
        return {
            'Lambda': [],
            'Theta': [],
            'faces': [],
            'triangles': [],
            'status': f'Pseudo-wireframe reconstruction failed: {e}'
        }
    
    print(f"\n✓ Lambda (3D vertices): {len(Lambda)}")
    print(f"✓ Theta (3D edges): {len(Theta)}")
    
    # ========== STAGE 3: FACE DETECTION ==========
    print("\nStage 3: Face Detection (Plane Clustering)")
    print("-" * 70)
    
    try:
        faces = find_all_faces_by_planes(Lambda, Theta)
    except Exception as e:
        return {
            'Lambda': Lambda,
            'Theta': Theta,
            'faces': [],
            'triangles': [],
            'status': f'Face detection failed: {e}'
        }
    
    print(f"\n✓ Faces detected: {len(faces)}")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {len(face)}-gon {face}")
    
    # ========== STAGE 4: TRIANGULATION & VALIDATION ==========
    print("\nStage 4: Triangulation & Euler Validation")
    print("-" * 70)
    
    try:
        triangles = []
        for face in faces:
            triangles.extend(triangulate_polygon(face, Lambda))
        
        num_v = len(Lambda)
        num_e = len(Theta)
        num_f = len(faces)
        
        euler = num_v - num_e + num_f
        euler_valid = (euler == 2)
        
        print(f"\n✓ Triangles: {len(triangles)}")
        print(f"✓ Euler check: V={num_v}, E={num_e}, F={num_f}")
        print(f"  V - E + F = {euler} (valid: {euler_valid})")
        
        if not euler_valid:
            print(f"  ⚠ WARNING: Euler formula invalid!")
        
    except Exception as e:
        return {
            'Lambda': Lambda,
            'Theta': Theta,
            'faces': faces,
            'triangles': [],
            'status': f'Triangulation failed: {e}'
        }
    
    # ========== STAGE 5: STL EXPORT ==========
    print("\nStage 5: STL Export")
    print("-" * 70)
    
    if output_stl:
        try:
            export_stl(output_stl, triangles, Lambda)
            print(f"\n✓ STL exported: {output_stl}")
        except Exception as e:
            print(f"✗ STL export failed: {e}")
    
    # ========== COMPLETION ==========
    status = "✓ RECONSTRUCTION COMPLETE" if euler_valid else "⚠ RECONSTRUCTION COMPLETE (Euler invalid)"
    
    return {
        'Lambda': Lambda,
        'Theta': Theta,
        'faces': faces,
        'triangles': triangles,
        'status': status
    }


if __name__ == "__main__":
    
    # Test with synthetic cube images (placeholder paths)
    # In real usage, replace with actual image paths
    
    print("Pipeline module loaded.")
    print("\nUsage:")
    print("  result = reconstruct_from_images(front.jpg, top.jpg, side.jpg, output.stl)")
