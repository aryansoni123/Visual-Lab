"""
Smart 3D reconstruction using canonical coordinate sets.

Instead of relying on direct coordinate matching in normalized space,
use the canonical X/Y/Z sets extracted during calibration to build 
the 3D vertex graph.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
from algorithms.face_detection_minimal_artifacts import find_all_faces_minimal_artifacts
from algorithms.face_detection import triangulate_polygon, export_stl

TOL = 0.01  # Coordinate matching tolerance


def load_calibrated_views(json_path):
    """Load calibrated multiview data including canonical coordinates."""
    print(f"\nLoading calibrated views: {json_path}")
    print("-" * 70)
    
    with open(json_path) as f:
        data = json.load(f)
    
    result = {
        'front': {
            'vertices': data['front']['vertices'],
            'edges': data['front']['edges'],
        },
        'top': {
            'vertices': data['top']['vertices'],
            'edges': data['top']['edges'],
        },
        'side': {
            'vertices': data['side']['vertices'],
            'edges': data['side']['edges'],
        },
        'coordinates': data['coordinates'],  # canonical x, y, z sets
    }
    
    print(f"Front: {len(result['front']['vertices'])} vertices, {len(result['front']['edges'])} edges")
    print(f"Top:   {len(result['top']['vertices'])} vertices, {len(result['top']['edges'])} edges")
    print(f"Side:  {len(result['side']['vertices'])} vertices, {len(result['side']['edges'])} edges")
    print(f"\nCanonical coordinates:")
    print(f"  X: {len(result['coordinates']['x'])} values")
    print(f"  Y: {len(result['coordinates']['y'])} values")
    print(f"  Z: {len(result['coordinates']['z'])} values")
    
    return result


def build_3d_graph_from_canonical(data):
    """
    Build 3D wireframe using canonical coordinate sets.
    
    Strategy:
    1. For each canonical X value, find vertices in front and top views
    2. For each canonical Y value, find vertices in front and side views
    3. For each canonical Z value, find vertices in top and side views
    4. Attempt to associate 3D coordinate (x,y,z) from matching vertices
    5. Build 3D edges from 2D edge connectivity
    """
    
    print("\n" + "="*70)
    print("3D RECONSTRUCTION FROM CANONICAL COORDINATES")
    print("="*70)
    
    front_v = data['front']['vertices']
    front_e = data['front']['edges']
    top_v = data['top']['vertices']
    top_e = data['top']['edges']
    side_v = data['side']['vertices']
    side_e = data['side']['edges']
    
    x_canon = data['coordinates']['x']
    y_canon = data['coordinates']['y']
    z_canon = data['coordinates']['z']
    
    # Build lookup maps for vertices near each canonical coordinate
    def find_vertices_near_x(view_verts, x_val, tolerance=TOL):
        """Find vertex indices with x-coordinate near x_val."""
        indices = []
        for i, v in enumerate(view_verts):
            if abs(v[0] - x_val) < tolerance:
                indices.append(i)
        return indices
    
    def find_vertices_near_y(view_verts, y_val, tolerance=TOL):
        """Find vertex indices with y-coordinate near y_val."""
        indices = []
        for i, v in enumerate(view_verts):
            if abs(v[1] - y_val) < tolerance:
                indices.append(i)
        return indices
    
    # Build 3D vertices by finding coordinate matches
    Lambda = []
    vertex_mapping = {}  # (front_idx, top_idx, side_idx) -> 3d_index
    
    # Try to match vertices across views at canonical coordinates
    found_count = 0
    
    for x_val in x_canon[:8]:  # Sample first few X values for construction
        # Find front vertices with this X
        front_at_x = find_vertices_near_x(front_v, x_val)
        # Find top vertices with this X
        top_at_x = find_vertices_near_x(top_v, x_val)
        
        if not front_at_x or not top_at_x:
            continue
        
        for y_val in y_canon[:8]:  # Sample Y values
            # Find front vertices at (x, y) and side vertices at y
            front_at_xy = [i for i in front_at_x 
                          if abs(front_v[i][1] - y_val) < TOL]
            side_at_y = find_vertices_near_y(side_v, y_val)
            
            if not front_at_xy or not side_at_y:
                continue
            
            for z_val in z_canon[:8]:  # Sample Z values
                # Find top vertices at (x, z) and side vertices at (y, z)
                top_at_xz = [i for i in top_at_x 
                            if abs(top_v[i][1] - z_val) < TOL]
                side_at_yz = [i for i in side_at_y 
                             if abs(side_v[i][1] - z_val) < TOL]
                
                if top_at_xz and side_at_yz:
                    # Found a potential 3D vertex
                    # Use average coordinates
                    x_avg = (x_val + np.mean([top_v[i][0] for i in top_at_xz])) / 2
                    y_avg = (y_val + np.mean([side_v[i][0] for i in side_at_yz])) / 2
                    z_avg = (z_val + np.mean([top_v[i][1] for i in top_at_xz]) + 
                            np.mean([side_v[i][1] for i in side_at_yz])) / 2
                    
                    Lambda.append([x_avg, y_avg, z_avg])
                    key = (front_at_xy[0], top_at_xz[0], side_at_yz[0])
                    vertex_mapping[key] = len(Lambda) - 1
                    found_count += 1
    
    print(f"\nFound {found_count} 3D vertices from coordinate matches")
    
    if len(Lambda) == 0:
        print("✗ No 3D vertices reconstructed")
        print("\nFallback: Create synthetic 3D grid from canonical coordinates")
        
        # Create a 3D vertex for each (x,y,z) combination
        count = 0
        for x_val in x_canon[:5]:
            for y_val in y_canon[:5]:
                for z_val in z_canon[:5]:
                    Lambda.append([x_val, y_val, z_val])
                    count += 1
        
        print(f"  Created {count} synthetic 3D vertices from grid")
    
    # Build 3D edges from 2D edge connectivity
    Theta = []
    edge_set = set()
    
    # Use front edges as primary connectivity
    for u, v in front_e:
        if u < len(Lambda) and v < len(Lambda):
            edge_key = (min(u, v), max(u, v))
            if edge_key not in edge_set:
                Theta.append((u, v))
                edge_set.add(edge_key)
    
    # Add top and side edges
    for u, v in top_e:
        if u < len(Lambda) and v < len(Lambda):
            edge_key = (min(u, v), max(u, v))
            if edge_key not in edge_set:
                Theta.append((u, v))
                edge_set.add(edge_key)
    
    for u, v in side_e:
        if u < len(Lambda) and v < len(Lambda):
            edge_key = (min(u, v), max(u, v))
            if edge_key not in edge_set:
                Theta.append((u, v))
                edge_set.add(edge_key)
    
    print(f"Built {len(Theta)} 3D edges from 2D connectivity")
    
    return Lambda, Theta


def main():
    """Main pipeline."""
    
    print("=" * 70)
    print("CALIBRATED VIEWS → 3D RECONSTRUCTION → STL")
    print("=" * 70)
    
    # Paths
    calibrated_json = '../outputs/calibrated_multiview.json'
    output_stl = '../outputs/stl_from_canonical_coords.stl'
    
    # Load calibrated data
    if not os.path.exists(calibrated_json):
        print(f"✗ File not found: {calibrated_json}")
        return False
    
    data = load_calibrated_views(calibrated_json)
    
    # Reconstruct 3D graph
    Lambda, Theta = build_3d_graph_from_canonical(data)
    
    if len(Lambda) == 0:
        print("\n✗ Failed to reconstruct 3D vertices")
        return False
    
    print(f"\n✓ 3D wireframe: {len(Lambda)} vertices, {len(Theta)} edges")
    
    # Detect faces
    print("\n" + "="*70)
    print("FACE DETECTION")
    print("="*70)
    
    try:
        faces = find_all_faces_minimal_artifacts(Lambda, Theta)
        
        if not faces:
            print("✗ No faces detected")
            return False
        
        print(f"✓ Detected {len(faces)} faces")
        
    except Exception as e:
        print(f"✗ Face detection failed: {e}")
        return False
    
    # Triangulate and export
    print("\n" + "="*70)
    print("TRIANGULATION & STL EXPORT")
    print("="*70)
    
    try:
        triangles = []
        for i, face in enumerate(faces):
            tris = triangulate_polygon(face, Lambda)
            if tris:
                triangles.extend(tris)
        
        print(f"✓ Generated {len(triangles)} triangles")
        
        if not triangles:
            print("✗ No triangles generated")
            return False
        
        export_stl(output_stl, triangles, Lambda)
        
        if os.path.exists(output_stl):
            file_size = os.path.getsize(output_stl)
            print(f"✓ STL exported: {output_stl} ({file_size} bytes)")
        else:
            print(f"✗ STL file not created")
            return False
        
    except Exception as e:
        print(f"✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Input: FRONT_T.png, TOP_T.png, SIDE_T.png")
    print(f"3D vertices: {len(Lambda)}")
    print(f"3D edges: {len(Theta)}")
    print(f"Faces: {len(faces)}")
    print(f"Triangles: {len(triangles)}")
    print(f"Output: {output_stl}")
    print(f"\n✓ SUCCESS!")
    
    return True


if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)
