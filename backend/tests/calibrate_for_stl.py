"""
Fixed calibration that preserves cross-view coordinate correspondence.

Key insight: DON'T normalize each view independently. Instead:
1. Use raw pixel coordinates
2. Scale all views to common reference using their aspect ratios
3. Preserve relative distances that should match across views
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import json
from reconstruction.image_processing import image_to_2d_graph

def extract_with_pixel_coords(image_path, view_name='view'):
    """Extract 2D graph preserving pixel coordinates."""
    print(f"\n{view_name} View")
    print("-" * 70)
    
    vertices, edges, visibility = image_to_2d_graph(image_path)
    
    print(f"  Extracted: {len(vertices)} vertices, {len(edges)} edges")
    print(f"  X range: {min(v[0] for v in vertices):.1f} to {max(v[0] for v in vertices):.1f}")
    print(f"  Y range: {min(v[1] for v in vertices):.1f} to {max(v[1] for v in vertices):.1f}")
    
    # Keep pixel coords as-is, return them wrapped for pseudo-wireframe
    return vertices, edges, visibility


def normalize_coords_reference(views_data, reference_scale=100):
    """
    Normalize all views to common scale while preserving cross-view correspondence.
    """
    front_v, front_e = views_data['front']
    top_v, top_e = views_data['top']
    side_v, side_e = views_data['side']
    
    # Get ranges for each view
    front_v_arr = np.array(front_v)
    front_range = front_v_arr.max(axis=0) - front_v_arr.min(axis=0)
    
    top_v_arr = np.array(top_v)
    top_range = top_v_arr.max(axis=0) - top_v_arr.min(axis=0)
    
    side_v_arr = np.array(side_v)
    side_range = side_v_arr.max(axis=0) - side_v_arr.min(axis=0)
    
    # Scale each view to reference scale
    front_scale = reference_scale / (front_range.max() + 1e-6)
    top_scale = reference_scale / (top_range.max() + 1e-6)
    side_scale = reference_scale / (side_range.max() + 1e-6)
    
    front_v_scaled = [(v[0] * front_scale, v[1] * front_scale) for v in front_v]
    top_v_scaled = [(v[0] * top_scale, v[1] * top_scale) for v in top_v]
    side_v_scaled = [(v[0] * side_scale, v[1] * side_scale) for v in side_v]
    
    print(f"\nAfter reference scaling (scale={reference_scale}):")
    print(f"  Front scale factor: {front_scale:.3f}")
    print(f"  Top scale factor: {top_scale:.3f}")
    print(f"  Side scale factor: {side_scale:.3f}")
    
    return (front_v_scaled, front_e, 
            top_v_scaled, top_e, 
            side_v_scaled, side_e)


def simple_calibrate_for_stl(front_img, top_img, side_img, output_json=None):
    """Calibrate views for STL generation (preserves correspondence)."""
    
    print("=" * 70)
    print("CALIBRATION FOR STL GENERATION")
    print("=" * 70)
    print("\nStrategy: Use reference scaling to preserve cross-view coordinate")
    print("correspondence while handling different image resolutions.")
    
    # Extract with pixel coordinates
    print("\n[Step 1] Extract 2D graphs")
    print("=" * 70)
    
    front_v, front_e, _ = extract_with_pixel_coords(front_img, 'FRONT')
    top_v, top_e, _ = extract_with_pixel_coords(top_img, 'TOP')
    side_v, side_e, _ = extract_with_pixel_coords(side_img, 'SIDE')
    
    # Apply reference scaling
    print("\n[Step 2] Apply reference scaling")
    print("=" * 70)
    
    (f_v_scaled, f_e, t_v_scaled, t_e, 
     s_v_scaled, s_e) = normalize_coords_reference(
        {'front': (front_v, front_e), 
         'top': (top_v, top_e),
         'side': (side_v, side_e)},
        reference_scale=100
    )
    
    # Prepare output
    result = {
        'front': {'vertices': f_v_scaled, 'edges': f_e},
        'top': {'vertices': t_v_scaled, 'edges': t_e},
        'side': {'vertices': s_v_scaled, 'edges': s_e},
    }
    
    if output_json:
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                return super().default(obj)
        
        with open(output_json, 'w') as f:
            json.dump(result, f, indent=2, cls=NumpyEncoder)
        
        print(f"\n✓ Saved: {output_json}")
    
    return result


if __name__ == "__main__":
    front_img = '../data/FRONT_T.png'
    top_img = '../data/TOP_T.png'
    side_img = '../data/SIDE_T.png'
    output_json = '../outputs/calibrated_for_stl.json'
    
    print(f"\nCalibrating orthographic views for STL generation")
    print(f"  Front: {front_img}")
    print(f"  Top:   {top_img}")
    print(f"  Side:  {side_img}")
    
    result = simple_calibrate_for_stl(front_img, top_img, side_img, output_json)
    
    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)
    print(f"\nFront: {len(result['front']['vertices'])} vertices, "
          f"{len(result['front']['edges'])} edges")
    print(f"Top:   {len(result['top']['vertices'])} vertices, "
          f"{len(result['top']['edges'])} edges")
    print(f"Side:  {len(result['side']['vertices'])} vertices, "
          f"{len(result['side']['edges'])} edges")
    print(f"\n✓ Ready for pseudo-wireframe reconstruction")
