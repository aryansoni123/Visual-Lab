"""
Multi-View Calibration and Point Extraction.

Based on pseudo-wireframe reconstruction principle:
- Front view (X-Y plane) provides X and Y coordinates
- Top view (X-Z plane) provides X and Z coordinates  
- Side view (Y-Z plane) provides Y and Z coordinates

A 3D point (x,y,z) is reconstructed when:
  ∃ front point with (x,y), top point with (x,z), side point with (y,z)

Strategy for different resolutions/ratios:
1. Extract 2D graphs from each image
2. Detect image metadata (resolution, aspect ratio)
3. Normalize coordinates to common reference frame
4. Apply resolution-aware thresholds for line detection
5. Quantize to common grid for coordinate matching
6. Extract canonical coordinate sets (x_vals, y_vals, z_vals)
7. Attempt 3D reconstruction for validation
8. Output calibrated 2D graphs in JSON
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import json
import cv2
from reconstruction.image_processing import (
    image_to_2d_graph, 
    LineSegment,
    detect_lines_from_image,
    cluster_collinear_segments,
    classify_clusters,
    extract_vertices_from_segments,
    extract_edges_from_segments
)

TOL = 1e-6


def get_image_metadata(image_path):
    """Get resolution and metadata from image."""
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    height, width = img.shape[:2]
    aspect_ratio = width / height if height > 0 else 1.0
    diagonal = np.sqrt(width**2 + height**2)
    
    return {
        'path': image_path,
        'width': width,
        'height': height,
        'aspect_ratio': aspect_ratio,
        'diagonal': diagonal,
    }


def get_resolution_aware_thresholds(metadata, reference_diagonal=400):
    """
    Compute resolution-aware thresholds for line detection.
    Scale parameters based on image size to handle different resolutions.
    """
    scale = metadata['diagonal'] / reference_diagonal
    
    return {
        'min_line_length': max(5, int(20 * scale)),
        'max_line_gap': max(3, int(10 * scale)),
        'canny_low': int(50 * (scale ** 0.5)),
        'canny_high': int(150 * (scale ** 0.5)),
    }


def extract_and_normalize(image_path, view_name='view'):
    """
    Extract 2D graph and normalize to [0, 1]x[0, 1] range.
    Also return metadata for coordinate calibration.
    """
    print(f"\n{view_name} View Processing")
    print("-" * 70)
    
    # Get image metadata
    metadata = get_image_metadata(image_path)
    print(f"  Resolution: {metadata['width']}x{metadata['height']}")
    print(f"  Aspect ratio: {metadata['aspect_ratio']:.2f}")
    
    # Get resolution-aware thresholds
    thresholds = get_resolution_aware_thresholds(metadata)
    print(f"  Line detection thresholds (resolution-adapted):")
    print(f"    min_line_length: {thresholds['min_line_length']}")
    print(f"    max_line_gap: {thresholds['max_line_gap']}")
    
    # Extract vertices and edges
    vertices, edges, visibility = image_to_2d_graph(
        image_path,
        min_line_length=thresholds['min_line_length'],
        max_line_gap=thresholds['max_line_gap']
    )
    
    print(f"  Extracted: {len(vertices)} vertices, {len(edges)} edges")
    
    if not vertices:
        return None, None, metadata
    
    # Normalize coordinates to [0, 1]
    vertices_arr = np.array(vertices, dtype=float)
    min_coords = vertices_arr.min(axis=0)
    max_coords = vertices_arr.max(axis=0)
    ranges = max_coords - min_coords
    
    # Avoid division by zero
    ranges = np.maximum(ranges, TOL)
    
    normalized_verts = []
    for v in vertices_arr:
        norm_v = (v - min_coords) / ranges
        normalized_verts.append(tuple(norm_v))
    
    print(f"  Normalized to [0,1]x[0,1]")
    print(f"    X range (pixels): [{min_coords[0]:.1f}, {max_coords[0]:.1f}]")
    print(f"    Y range (pixels): [{min_coords[1]:.1f}, {max_coords[1]:.1f}]")
    
    return normalized_verts, edges, metadata


def extract_coordinate_sets(front_verts, top_verts, side_verts):
    """
    Extract unique X, Y, Z coordinate sets from three views.
    
    In normalized [0,1] space:
    - Front: (x, y) where x ∈ [0,1], y ∈ [0,1]
    - Top:   (x, z) where x ∈ [0,1], z ∈ [0,1]
    - Side:  (y, z) where y ∈ [0,1], z ∈ [0,1]
    """
    if not front_verts or not top_verts or not side_verts:
        return None
    
    coords = {}
    
    # Extract X coordinates (from front and top)
    x_vals = set()
    for x, y in front_verts:
        x_vals.add(round(x, 3))
    for x, z in top_verts:
        x_vals.add(round(x, 3))
    coords['x'] = sorted(x_vals)
    
    # Extract Y coordinates (from front and side)
    y_vals = set()
    for x, y in front_verts:
        y_vals.add(round(y, 3))
    for y, z in side_verts:
        y_vals.add(round(y, 3))
    coords['y'] = sorted(y_vals)
    
    # Extract Z coordinates (from top and side)
    z_vals = set()
    for x, z in top_verts:
        z_vals.add(round(z, 3))
    for y, z in side_verts:
        z_vals.add(round(z, 3))
    coords['z'] = sorted(z_vals)
    
    return coords


def attempt_3d_reconstruction(front_verts, front_edges, top_verts, top_edges, side_verts, side_edges):
    """
    Attempt to reconstruct 3D points by matching coordinates across views.
    Returns count of successfully matched 3D vertices.
    """
    # Build lookup maps
    front_map = {}
    for x, y in front_verts:
        key = (round(x, 3), round(y, 3))
        front_map[key] = (x, y)
    
    top_map = {}
    for x, z in top_verts:
        key = (round(x, 3), round(z, 3))
        top_map[key] = (x, z)
    
    side_map = {}
    for y, z in side_verts:
        key = (round(y, 3), round(z, 3))
        side_map[key] = (y, z)
    
    # Try to find 3D points
    matches_3d = 0
    
    for (x_front, y_front), (x_front_check, y_front_check) in front_map.items():
        # Find matching X in top
        for (x_top, z_top), (x_top_check, z_top_check) in top_map.items():
            if abs(x_front - x_top) > 0.01:
                continue  # X doesn't match
            
            # Find matching Y in side
            for (y_side, z_side), (y_side_check, z_side_check) in side_map.items():
                if abs(y_front - y_side) > 0.01:
                    continue  # Y doesn't match
                
                # Check Z consistency
                if abs(z_top - z_side) < 0.01:
                    # Valid 3D point found
                    matches_3d += 1
    
    return matches_3d


def multi_view_calibrate(front_img, top_img, side_img, output_json=None):
    """
    Main calibration pipeline for different-resolution orthographic views.
    
    Args:
        front_img: Path to front view image
        top_img: Path to top view image
        side_img: Path to side view image
        output_json: Path to save calibrated data (optional)
    
    Returns:
        {
            'front': {'vertices': [...], 'edges': [...], 'metadata': {...}},
            'top': {...},
            'side': {...},
            'coordinates': {'x': [...], 'y': [...], 'z': [...]},
            '3d_matches': count,
        }
    """
    
    print("=" * 70)
    print("MULTI-VIEW CALIBRATION PIPELINE")
    print("=" * 70)
    
    # Step 1: Extract and normalize
    print("\n[Step 1] Extract 2D graphs from images")
    print("=" * 70)
    
    front_verts, front_edges, front_metadata = extract_and_normalize(
        front_img, 'FRONT'
    )
    top_verts, top_edges, top_metadata = extract_and_normalize(
        top_img, 'TOP'
    )
    side_verts, side_edges, side_metadata = extract_and_normalize(
        side_img, 'SIDE'
    )
    
    if not front_verts or not top_verts or not side_verts:
        raise RuntimeError("One or more views failed to extract vertices")
    
    # Step 2: Extract coordinate sets
    print("\n[Step 2] Extract canonical coordinate sets")
    print("=" * 70)
    
    coords = extract_coordinate_sets(front_verts, top_verts, side_verts)
    
    print(f"\nCanonical coordinates (normalized [0,1]):")
    print(f"  X values ({len(coords['x'])}): {coords['x'][:5]}... (sample)")
    print(f"  Y values ({len(coords['y'])}): {coords['y'][:5]}... (sample)")
    print(f"  Z values ({len(coords['z'])}): {coords['z'][:5]}... (sample)")
    
    # Step 3: Attempt 3D reconstruction
    print("\n[Step 3] Validate calibration via 3D reconstruction attempt")
    print("=" * 70)
    
    matches_3d = attempt_3d_reconstruction(
        front_verts, front_edges,
        top_verts, top_edges,
        side_verts, side_edges
    )
    
    print(f"  3D coordinate matches found: {matches_3d}")
    if matches_3d > 0:
        print(f"  ✓ Calibration valid (coordinates align across views)")
    else:
        print(f"  ⚠ Warning: No 3D matches found")
        print(f"    Views may have different scales or systematic offsets")
    
    # Prepare output
    result = {
        'front': {
            'vertices': front_verts,
            'edges': front_edges,
            'metadata': front_metadata,
        },
        'top': {
            'vertices': top_verts,
            'edges': top_edges,
            'metadata': top_metadata,
        },
        'side': {
            'vertices': side_verts,
            'edges': side_edges,
            'metadata': side_metadata,
        },
        'coordinates': coords,
        '3d_matches': matches_3d,
    }
    
    # Step 4: Save to JSON
    print("\n[Step 4] Save calibrated data")
    print("=" * 70)
    
    if output_json:
        # Custom encoder for numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                return super().default(obj)
        
        with open(output_json, 'w') as f:
            json.dump(result, f, indent=2, cls=NumpyEncoder)
        
        print(f"  ✓ Saved: {output_json}")
    
    return result


if __name__ == "__main__":
    # Test on _T images with different resolutions
    front_img = '../data/FRONT_T.png'
    top_img = '../data/TOP_T.png'
    side_img = '../data/SIDE_T.png'
    output_json = '../outputs/calibrated_multiview.json'
    
    print(f"\nInitializing Multi-View Calibration")
    print(f"  Front: {front_img}")
    print(f"  Top:   {top_img}")
    print(f"  Side:  {side_img}")
    
    try:
        result = multi_view_calibrate(front_img, top_img, side_img, output_json)
        
        print("\n" + "=" * 70)
        print("CALIBRATION COMPLETE")
        print("=" * 70)
        print(f"\nResults:")
        print(f"  Front: {len(result['front']['vertices'])} vertices, "
              f"{len(result['front']['edges'])} edges")
        print(f"  Top:   {len(result['top']['vertices'])} vertices, "
              f"{len(result['top']['edges'])} edges")
        print(f"  Side:  {len(result['side']['vertices'])} vertices, "
              f"{len(result['side']['edges'])} edges")
        print(f"  Coordinate sets: X({len(result['coordinates']['x'])}), "
              f"Y({len(result['coordinates']['y'])}), Z({len(result['coordinates']['z'])})")
        print(f"  3D matches: {result['3d_matches']}")
        
        if result['3d_matches'] > 0:
            print(f"\n✓ SUCCESS: Views are properly calibrated!")
        else:
            print(f"\n⚠ WARNING: Check coordinate alignment in generated JSON")
        
    except Exception as e:
        print(f"\n✗ Calibration failed: {e}")
        import traceback
        traceback.print_exc()
