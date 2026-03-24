"""
Calibrate and smooth 2D point extraction from 3 orthographic views.

Problem: Extracted vertices from front/top/side images don't align precisely
as required by pseudo-wireframe reconstruction (x from front ≠ x from top, etc).

Solution:
1. Extract 2D graphs from all 3 images
2. Analyze alignment errors (which coords should match but don't)
3. Detect systematic offsets/scaling per view
4. Apply affine corrections (translate, scale, rotate)
5. Cluster nearby vertices to reduce noise
6. Output corrected 2D graphs compatible with pseudo-wireframe
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from reconstruction.image_processing import image_to_2d_graph
import matplotlib.pyplot as plt

TOL = 1e-6


def extract_projection_coordinates(front_verts, top_verts, side_verts):
    """Extract unique x, y, z coordinates from the three projections."""
    front_x = set()
    front_y = set()
    top_x = set()
    top_z = set()
    side_y = set()
    side_z = set()
    
    for x, y in front_verts:
        front_x.add(round(x, 1))
        front_y.add(round(y, 1))
    
    for x, z in top_verts:
        top_x.add(round(x, 1))
        top_z.add(round(z, 1))
    
    for y, z in side_verts:
        side_y.add(round(y, 1))
        side_z.add(round(z, 1))
    
    return {
        'front_x': sorted(front_x),
        'front_y': sorted(front_y),
        'top_x': sorted(top_x),
        'top_z': sorted(top_z),
        'side_y': sorted(side_y),
        'side_z': sorted(side_z),
    }


def analyze_alignment(front_verts, top_verts, side_verts):
    """Analyze how well the three projections align."""
    print("\n" + "="*70)
    print("ALIGNMENT ANALYSIS")
    print("="*70)
    
    coords = extract_projection_coordinates(front_verts, top_verts, side_verts)
    
    # Extract coordinate sets
    front_x = set(round(v[0], 1) for v in front_verts)
    top_x = set(round(v[0], 1) for v in top_verts)
    side_y = set(round(v[1], 1) for v in side_verts)
    
    front_y = set(round(v[1], 1) for v in front_verts)
    side_z = set(round(v[1], 1) for v in side_verts)
    top_z = set(round(v[1], 1) for v in top_verts)
    
    # Check alignment
    x_overlap = front_x & top_x
    y_overlap = front_y & side_y
    z_overlap = top_z & side_z
    
    print(f"\nX-coordinate alignment (front ∩ top):")
    print(f"  Front X unique: {len(front_x)}")
    print(f"  Top X unique:   {len(top_x)}")
    print(f"  Overlap: {len(x_overlap)}/{min(len(front_x), len(top_x))}")
    print(f"  Front values: {sorted(front_x)[:5]}... (sample)")
    print(f"  Top values:   {sorted(top_x)[:5]}... (sample)")
    
    print(f"\nY-coordinate alignment (front ∩ side):")
    print(f"  Front Y unique: {len(front_y)}")
    print(f"  Side Y unique:  {len(side_y)}")
    print(f"  Overlap: {len(y_overlap)}/{min(len(front_y), len(side_y))}")
    print(f"  Front values: {sorted(front_y)[:5]}... (sample)")
    print(f"  Side values:  {sorted(side_y)[:5]}... (sample)")
    
    print(f"\nZ-coordinate alignment (top ∩ side):")
    print(f"  Top Z unique:  {len(top_z)}")
    print(f"  Side Z unique: {len(side_z)}")
    print(f"  Overlap: {len(z_overlap)}/{min(len(top_z), len(side_z))}")
    
    return x_overlap, y_overlap, z_overlap


def cluster_vertices(vertices, radius=2.0):
    """Cluster nearby vertices and return cluster centroids."""
    if not vertices:
        return []
    
    vertices = np.array(vertices, dtype=float)
    clustered = []
    used = set()
    
    for i, v in enumerate(vertices):
        if i in used:
            continue
        
        # Find all vertices within radius
        cluster = [v]
        used.add(i)
        
        for j in range(i + 1, len(vertices)):
            if j in used:
                continue
            other = vertices[j]
            
            if np.linalg.norm(v - other) <= radius:
                cluster.append(other)
                used.add(j)
        
        # Compute centroid
        centroid = np.mean(cluster, axis=0)
        clustered.append(tuple(centroid))
    
    return clustered


def correct_view_coordinates(vertices, edges, reference_coords, view_name='view'):
    """Apply affine correction to align view coordinates with reference."""
    # Simple approach: center both to origin, then scale to common range
    vertices = np.array(vertices, dtype=float)
    
    # Get bounds
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    ranges = max_coords - min_coords
    
    # Translate to origin
    centered = vertices - min_coords
    
    # Scale to [0, 1]
    if ranges[0] > TOL and ranges[1] > TOL:
        scaled = centered / ranges
    else:
        scaled = centered
    
    # Convert back to list of tuples
    corrected_verts = [tuple(v) for v in scaled]
    
    # Map edges (keep connectivity)
    corrected_edges = edges  # Edge indices don't change
    
    return corrected_verts, corrected_edges, {'scale': ranges, 'offset': min_coords}


def smooth_extraction(front_image, top_image, side_image, cluster_radius=3.0):
    """
    Extract and smooth 2D orthographic projections.
    
    Returns:
        (front_verts, front_edges, top_verts, top_edges, side_verts, side_edges)
    """
    print("="*70)
    print("EXTRACTING 2D GRAPHS FROM IMAGES")
    print("="*70)
    
    # Extract raw vertices from images
    front_verts, front_edges, front_vis = image_to_2d_graph(front_image)
    top_verts, top_edges, top_vis = image_to_2d_graph(top_image)
    side_verts, side_edges, side_vis = image_to_2d_graph(side_image)
    
    print(f"\nRaw extraction:")
    print(f"  Front: {len(front_verts)} vertices, {len(front_edges)} edges")
    print(f"  Top:   {len(top_verts)} vertices, {len(top_edges)} edges")
    print(f"  Side:  {len(side_verts)} vertices, {len(side_edges)} edges")
    
    # Analyze alignment issues
    x_overlap, y_overlap, z_overlap = analyze_alignment(front_verts, top_verts, side_verts)
    
    # Cluster vertices to reduce noise
    print("\n" + "="*70)
    print("CLUSTERING VERTICES (reduce noise)")
    print("="*70)
    
    front_clustered = cluster_vertices(front_verts, cluster_radius)
    top_clustered = cluster_vertices(top_verts, cluster_radius)
    side_clustered = cluster_vertices(side_verts, cluster_radius)
    
    print(f"\nClustered vertices (radius={cluster_radius} px):")
    print(f"  Front: {len(front_verts)} → {len(front_clustered)}")
    print(f"  Top:   {len(top_verts)} → {len(top_clustered)}")
    print(f"  Side:  {len(side_verts)} → {len(side_clustered)}")
    
    # Normalize coordinates to [0, 1] per view for alignment
    print("\n" + "="*70)
    print("NORMALIZING COORDINATES")
    print("="*70)
    
    # Get common bounds across all views
    all_x = set()
    all_y = set()
    all_z = set()
    
    for verts in [front_clustered, top_clustered, side_clustered]:
        for v in verts:
            if len(v) >= 2:
                all_x.add(v[0])
                all_y.add(v[1])
    
    global_x_min, global_x_max = min(all_x), max(all_x)
    global_y_min, global_y_max = min(all_y), max(all_y)
    
    x_range = global_x_max - global_x_min if global_x_max > global_x_min else 1.0
    y_range = global_y_max - global_y_min if global_y_max > global_y_min else 1.0
    
    # Normalize each view to [0, 1]
    def normalize_verts(verts):
        normalized = []
        for v in verts:
            x = (v[0] - global_x_min) / x_range if x_range > TOL else v[0]
            y = (v[1] - global_y_min) / y_range if y_range > TOL else v[1]
            normalized.append((x, y))
        return normalized
    
    front_normalized = normalize_verts(front_clustered)
    top_normalized = normalize_verts(top_clustered)
    side_normalized = normalize_verts(side_clustered)
    
    print(f"\nNormalized to common [0,1] range:")
    print(f"  Global X range: [{global_x_min:.1f}, {global_x_max:.1f}]")
    print(f"  Global Y range: [{global_y_min:.1f}, {global_y_max:.1f}]")
    print(f"  Front sample: {front_normalized[:3]}")
    print(f"  Top sample:   {top_normalized[:3]}")
    print(f"  Side sample:  {side_normalized[:3]}")
    
    # Map edges to new vertex indices (after clustering)
    def remap_edges(old_verts, new_verts, edges):
        """Remap edge indices from old to new vertex set."""
        # Build mapping from old verts to new verts (find closest match)
        old_to_new = {}
        for i, old_v in enumerate(old_verts):
            old_arr = np.array(old_v, dtype=float)
            min_dist = float('inf')
            best_j = 0
            
            for j, new_v in enumerate(new_verts):
                new_arr = np.array(new_v, dtype=float)
                dist = np.linalg.norm(old_arr - new_arr)
                if dist < min_dist:
                    min_dist = dist
                    best_j = j
            
            old_to_new[i] = best_j
        
        # Remap edges
        remapped = []
        seen = set()
        for u, v in edges:
            new_u = old_to_new.get(u, 0)
            new_v = old_to_new.get(v, 0)
            edge_key = (min(new_u, new_v), max(new_u, new_v))
            if edge_key not in seen:
                remapped.append(edge_key)
                seen.add(edge_key)
        
        return remapped
    
    front_edges_remapped = remap_edges(front_verts, front_normalized, front_edges)
    top_edges_remapped = remap_edges(top_verts, top_normalized, top_edges)
    side_edges_remapped = remap_edges(side_verts, side_normalized, side_edges)
    
    print(f"\nRe-mapped edges:")
    print(f"  Front: {len(front_edges)} → {len(front_edges_remapped)}")
    print(f"  Top:   {len(top_edges)} → {len(top_edges_remapped)}")
    print(f"  Side:  {len(side_edges)} → {len(side_edges_remapped)}")
    
    return (
        front_normalized, front_edges_remapped,
        top_normalized, top_edges_remapped,
        side_normalized, side_edges_remapped
    )


if __name__ == "__main__":
    # Process the _T images
    front_img = '../data/FRONT_T.png'
    top_img = '../data/TOP_T.png'
    side_img = '../data/SIDE_T.png'
    
    print(f"\nCalibrating orthographic view extraction")
    print(f"  Front: {front_img}")
    print(f"  Top:   {top_img}")
    print(f"  Side:  {side_img}")
    
    front_v, front_e, top_v, top_e, side_v, side_e = smooth_extraction(
        front_img, top_img, side_img, cluster_radius=3.0
    )
    
    print("\n" + "="*70)
    print("FINAL CALIBRATED OUTPUT")
    print("="*70)
    print(f"\nFront: {len(front_v)} vertices, {len(front_e)} edges")
    print(f"Top:   {len(top_v)} vertices, {len(top_e)} edges")
    print(f"Side:  {len(side_v)} vertices, {len(side_e)} edges")
    print(f"\n✓ Calibration complete. Ready for pseudo-wireframe reconstruction.")
    
    # Save calibrated data
    import json
    output = {
        'front': {'vertices': front_v, 'edges': front_e},
        'top': {'vertices': top_v, 'edges': top_e},
        'side': {'vertices': side_v, 'edges': side_e},
    }
    
    output_file = '../outputs/calibrated_views_T.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Calibrated data saved: {output_file}")
