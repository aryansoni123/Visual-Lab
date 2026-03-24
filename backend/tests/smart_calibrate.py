"""
Smarter calibration: detect scale/rotation patterns rather than force alignment.

Key insight: don't try to normalize coordinates away; instead detect the 
systematic scale and rotation differences between views, then attempt to 
correct them using cross-view geometry constraints.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from reconstruction.image_processing import image_to_2d_graph
from scipy.spatial.distance import cdist

TOL = 1e-6


def analyze_edge_structure(vertices, edges):
    """Analyze edge lengths and angles in a projection."""
    if not vertices or not edges:
        return None
    
    vertices_arr = np.array(vertices, dtype=float)
    edge_lengths = []
    
    for u, v in edges:
        if u < len(vertices_arr) and v < len(vertices_arr):
            p1 = vertices_arr[u]
            p2 = vertices_arr[v]
            length = np.linalg.norm(p2 - p1)
            edge_lengths.append(length)
    
    if not edge_lengths:
        return None
    
    return {
        'min': np.min(edge_lengths),
        'max': np.max(edge_lengths),
        'mean': np.mean(edge_lengths),
        'median': np.median(edge_lengths),
        'count': len(edge_lengths),
    }


def estimate_scale_factor(ref_structure, target_structure):
    """Estimate scale factor between two edge structures."""
    if ref_structure is None or target_structure is None:
        return 1.0
    
    # Use median edge length ratio
    ref_median = ref_structure['median']
    target_median = target_structure['median']
    
    if target_median > TOL:
        return ref_median / target_median
    return 1.0


def correct_view_scale(vertices, edges, scale_factor):
    """Apply uniform scale correction to vertices."""
    if abs(scale_factor - 1.0) < TOL:
        return list(vertices)
    
    vertices_arr = np.array(vertices, dtype=float)
    centroid = np.mean(vertices_arr, axis=0)
    
    corrected = []
    for v in vertices_arr:
        # Scale relative to centroid
        offset = v - centroid
        scaled_offset = offset * scale_factor
        corrected_v = centroid + scaled_offset
        corrected.append(tuple(corrected_v))
    
    return corrected


def quantize_coordinates(vertices, grid_size=1.0):
    """
    Snap vertices to a quantization grid to reduce noise.
    This lets coordinates align better across views.
    """
    quantized = []
    for v in vertices:
        if len(v) >= 2:
            x = round(v[0] / grid_size) * grid_size
            y = round(v[1] / grid_size) * grid_size
            additional = v[2:] if len(v) > 2 else ()
            quantized.append((x, y) + additional)
        else:
            quantized.append(v)
    
    return quantized


def deduplicate_vertices(vertices, edges, tol=1.0):
    """Merge vertices that are very close together."""
    if not vertices:
        return vertices, edges
    
    vertices_arr = np.array(vertices, dtype=float)
    n = len(vertices_arr)
    
    # Find groups of nearby vertices
    mapping = {}  # old index -> new index
    kept_indices = []
    
    for i in range(n):
        if i in mapping:
            continue  # Already mapped to another vertex
        
        kept_indices.append(i)
        
        # Find all vertices close to this one
        for j in range(i + 1, n):
            if j in mapping:
                continue
            
            dist = np.linalg.norm(vertices_arr[i] - vertices_arr[j])
            if dist <= tol:
                mapping[j] = len(kept_indices) - 1  # Map to current kept vertex
        
        mapping[i] = len(kept_indices) - 1
    
    # Create deduplicated vertex list
    dedup_verts = [vertices[i] for i in kept_indices]
    
    # Remap edges
    dedup_edges = set()
    for u, v in edges:
        new_u = mapping.get(u, 0)
        new_v = mapping.get(v, 0)
        if new_u != new_v:
            edge_key = (min(new_u, new_v), max(new_u, new_v))
            dedup_edges.add(edge_key)
    
    return dedup_verts, list(dedup_edges)


def smart_calibrate_views(front_img, top_img, side_img):
    """
    Smart calibration preserving graph structure.
    
    Strategy:
    1. Extract 2D graphs
    2. Analyze edge structure per view
    3. Estimate scale factors based on edge distributions
    4. Apply quantization to snap coordinates to visible grid
    5. Deduplicate vertices that are too close
    """
    
    print("="*70)
    print("SMART CALIBRATION (Structure-Preserving)")
    print("="*70)
    
    # Step 1: Extract
    print("\nStep 1: Extract 2D graphs from images")
    print("-"*70)
    
    front_verts, front_edges, front_vis = image_to_2d_graph(front_img)
    top_verts, top_edges, top_vis = image_to_2d_graph(top_img)
    side_verts, side_edges, side_vis = image_to_2d_graph(side_img)
    
    print(f"Front: {len(front_verts)} vertices, {len(front_edges)} edges")
    print(f"Top:   {len(top_verts)} vertices, {len(top_edges)} edges")
    print(f"Side:  {len(side_verts)} vertices, {len(side_edges)} edges")
    
    # Step 2: Analyze edge structures
    print("\nStep 2: Analyze edge structure")
    print("-"*70)
    
    front_struct = analyze_edge_structure(front_verts, front_edges)
    top_struct = analyze_edge_structure(top_verts, top_edges)
    side_struct = analyze_edge_structure(side_verts, side_edges)
    
    print(f"Front edges - mean length: {front_struct['mean']:.1f} px")
    print(f"Top edges   - mean length: {top_struct['mean']:.1f} px")
    print(f"Side edges  - mean length: {side_struct['mean']:.1f} px")
    
    # Step 3: Estimate scale factors (use front as reference)
    print("\nStep 3: Estimate scale factors")
    print("-"*70)
    
    scale_top = estimate_scale_factor(front_struct, top_struct)
    scale_side = estimate_scale_factor(front_struct, side_struct)
    
    print(f"Scale top  (relative to front): {scale_top:.3f}")
    print(f"Scale side (relative to front): {scale_side:.3f}")
    
    # Apply scaling
    print("\nStep 4: Apply scaling corrections")
    print("-"*70)
    
    front_scaled = front_verts  # Reference
    top_scaled = correct_view_scale(top_verts, top_edges, scale_top)
    side_scaled = correct_view_scale(side_verts, side_edges, scale_side)
    
    print(f"Front: {len(front_verts)} → {len(front_scaled)} vertices")
    print(f"Top:   {len(top_verts)} → {len(top_scaled)} vertices")
    print(f"Side:  {len(side_verts)} → {len(side_scaled)} vertices")
    
    # Step 5: Quantize coordinates
    print("\nStep 5: Quantize to grid (snap to nearest units)")
    print("-"*70)
    
    # Use grid size that matches smallest detected feature
    grid_size = min(front_struct['median'], top_struct['median'], 
                     side_struct['median']) / 2
    grid_size = max(grid_size, 1.0)  # At least 1 pixel
    
    print(f"Grid size: {grid_size:.1f} px")
    
    front_quantized = quantize_coordinates(front_scaled, grid_size)
    top_quantized = quantize_coordinates(top_scaled, grid_size)
    side_quantized = quantize_coordinates(side_scaled, grid_size)
    
    print(f"Quantized (no change in vertex count)")
    
    # Step 6: Deduplicate close vertices
    print("\nStep 6: Deduplicate nearby vertices")
    print("-"*70)
    
    dedup_tol = grid_size * 1.5
    
    front_dedup, front_edges_dedup = deduplicate_vertices(
        front_quantized, front_edges, dedup_tol
    )
    top_dedup, top_edges_dedup = deduplicate_vertices(
        top_quantized, top_edges, dedup_tol
    )
    side_dedup, side_edges_dedup = deduplicate_vertices(
        side_quantized, side_edges, dedup_tol
    )
    
    print(f"Front: {len(front_quantized)} → {len(front_dedup)} vertices, "
          f"{len(front_edges)} → {len(front_edges_dedup)} edges")
    print(f"Top:   {len(top_quantized)} → {len(top_dedup)} vertices, "
          f"{len(top_edges)} → {len(top_edges_dedup)} edges")
    print(f"Side:  {len(side_quantized)} → {len(side_dedup)} vertices, "
          f"{len(side_edges)} → {len(side_edges_dedup)} edges")
    
    return (
        front_dedup, front_edges_dedup,
        top_dedup, top_edges_dedup,
        side_dedup, side_edges_dedup
    )


if __name__ == "__main__":
    front_img = '../data/FRONT_T.png'
    top_img = '../data/TOP_T.png'
    side_img = '../data/SIDE_T.png'
    
    print(f"\nSmart Calibration of Orthographic Views")
    print(f"  Front: {front_img}")
    print(f"  Top:   {top_img}")
    print(f"  Side:  {side_img}")
    
    try:
        f_v, f_e, t_v, t_e, s_v, s_e = smart_calibrate_views(
            front_img, top_img, side_img
        )
        
        print("\n" + "="*70)
        print("CALIBRATION COMPLETE")
        print("="*70)
        print(f"\nFront: {len(f_v)} vertices, {len(f_e)} edges")
        print(f"Top:   {len(t_v)} vertices, {len(t_e)} edges")
        print(f"Side:  {len(s_v)} vertices, {len(s_e)} edges")
        
        print("\n✓ Calibrated views ready for pseudo-wireframe reconstruction")
        
    except Exception as e:
        print(f"\n✗ Calibration failed: {e}")
        import traceback
        traceback.print_exc()
