"""
Test STL generation with light-scale calibration.
"""

import json
import struct
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper
from algorithms.face_detection_minimal_artifacts import find_all_faces_minimal_artifacts

def export_stl_binary(filename, vertices, triangles):
    """Export triangle mesh to binary STL format."""
    with open(filename, 'wb') as f:
        # Header
        f.write(b'\0' * 80)
        f.write(struct.pack('<I', len(triangles)))
        
        for tri in triangles:
            v0 = np.array(vertices[tri[0]], dtype=np.float32)
            v1 = np.array(vertices[tri[1]], dtype=np.float32)
            v2 = np.array(vertices[tri[2]], dtype=np.float32)
            
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            if norm > 1e-6:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1], dtype=np.float32)
            
            f.write(struct.pack('<fff', *normal))
            f.write(struct.pack('<fff', *v0))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<H', 0))

def main():
    calib_file = Path("../outputs/calibrated_light_scale.json")
    
    if not calib_file.exists():
        print(f"ERROR: {calib_file} not found")
        return
    
    print("=" * 70)
    print("TESTING STL GENERATION: LIGHT SCALE CALIBRATION")
    print("=" * 70)
    
    with open(calib_file) as f:
        calib = json.load(f)
    
    front = calib['front']
    top = calib['top']
    side = calib['side']
    
    print(f"\nLoaded calibration: {calib.get('strategy', 'unknown')}")
    print(f"  Front: {len(front['vertices'])} verts, {len(front['edges'])} edges")
    print(f"  Top:   {len(top['vertices'])} verts, {len(top['edges'])} edges")
    print(f"  Side:  {len(side['vertices'])} verts, {len(side['edges'])} edges")
    
    # Run reconstruction
    print("\n" + "=" * 70)
    print("[Step 1] 3D Reconstruction")
    print("=" * 70 )
    
    vertices_3d, edges_3d, metadata = build_pseudo_wireframe_paper(
        front['vertices'], front['edges'],
        top['vertices'], top['edges'],
        side['vertices'], side['edges']
    )
    
    print(f"\n✓ Reconstructed:")
    print(f"  Vertices: {len(vertices_3d)}")
    print(f"  Edges: {len(edges_3d)}")
    
    if len(vertices_3d) == 0:
        print("\nERROR: No 3D vertices found!")
        print("\nDEBUGGING: Check coordinate overlap...")
        
        # Debug coordinate matching
        front_x = set(round(v[0], 2) for v in front['vertices'])
        top_x = set(round(v[0], 2) for v in top['vertices'])
        overlap_x = len(front_x & top_x)
        
        front_y = set(round(v[1], 2) for v in front['vertices'])
        side_y = set(round(v[1], 2) for v in side['vertices'])
        overlap_y = len(front_y & side_y)
        
        print(f"  Front X ∩ Top X: {overlap_x} matches")
        print(f"  Front Y ∩ Side Y: {overlap_y} matches")
        return
    
    # Detect faces
    print("\n" + "=" * 70)
    print("[Step 2] Face Detection")
    print("=" * 70)
    
    triangles = find_all_faces_minimal_artifacts(
        vertices_3d, edges_3d,
        max_iterations=1000000
    )
    
    print(f"\n✓ Detected triangles: {len(triangles)}")
    
    if len(triangles) == 0:
        print("ERROR: No triangles detected!")
        return
    
    # Export STL
    print("\n" + "=" * 70)
    print("[Step 3] Export STL")
    print("=" * 70)
    
    stl_file = Path("../outputs/mesh_from_lightscale.stl")
    stl_file.parent.mkdir(parents=True, exist_ok=True)
    
    export_stl_binary(str(stl_file), vertices_3d, triangles)
    
    print(f"\n✓ STL exported: {stl_file}")
    print(f"  Vertices: {len(vertices_3d)}")
    print(f"  Triangles: {len(triangles)}")
    print(f"  File size: {stl_file.stat().st_size} bytes")
    
    print("\n" + "=" * 70)
    print("SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
