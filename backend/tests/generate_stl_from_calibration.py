"""
Generate STL mesh from calibrated views using reference scaling approach.

Process:
1. Load calibrated_for_stl.json (pixel-space coordinates with reference scaling)
2. Run pseudo-wireframe reconstruction
3. Detect faces and triangulate
4. Export STL file

Reference scaling approach preserves cross-view coordinate correspondence
by using uniform scaling factors, unlike per-view normalization.
"""

import json
import sys
import struct
from pathlib import Path
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper
from algorithms.face_detection_minimal_artifacts import (
    find_all_faces_minimal_artifacts
)

def export_stl_binary(filename, vertices, triangles):
    """Export triangle mesh to binary STL format."""
    with open(filename, 'wb') as f:
        # Header
        f.write(b'\0' * 80)
        
        # Number of triangles
        f.write(struct.pack('<I', len(triangles)))
        
        # Write triangles
        for tri in triangles:
            v0 = np.array(vertices[tri[0]], dtype=np.float32)
            v1 = np.array(vertices[tri[1]], dtype=np.float32)
            v2 = np.array(vertices[tri[2]], dtype=np.float32)
            
            # Normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            if norm > 1e-6:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1], dtype=np.float32)
            
            # Write normal
            f.write(struct.pack('<fff', *normal))
            
            # Write vertices
            f.write(struct.pack('<fff', *v0))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            
            # Attribute byte count
            f.write(struct.pack('<H', 0))

def main():
    # Try normalized calibration first, fall back to reference scaling
    calib_file = Path("../outputs/calibrated_normalized.json")
    
    if not calib_file.exists():
        calib_file = Path("../outputs/calibrated_for_stl.json")
    
    if not calib_file.exists():
        print(f"ERROR: {calib_file} not found")
        print("Run calibrate_for_stl.py first")
        return
    
    print("=" * 70)
    print("GENERATING STL FROM CALIBRATED VIEWS")
    print("=" * 70)
    
    # Load calibration
    with open(calib_file) as f:
        calib = json.load(f)
    
    front = calib['front']
    top = calib['top']
    side = calib['side']
    
    print(f"\nLoaded calibration:")
    print(f"  Front: {len(front['vertices'])} verts, {len(front['edges'])} edges")
    print(f"  Top:   {len(top['vertices'])} verts, {len(top['edges'])} edges")
    print(f"  Side:  {len(side['vertices'])} verts, {len(side['edges'])} edges")
    
    # Build pseudo-wireframe
    print("\n" + "=" * 70)
    print("[Step 1] Reconstruct 3D mesh from orthographic views")
    print("=" * 70)
    
    vertices_3d, edges_3d, metadata = build_pseudo_wireframe_paper(
        front['vertices'], front['edges'],
        top['vertices'], top['edges'],
        side['vertices'], side['edges']
    )
    
    print(f"\n✓ 3D Reconstruction:")
    print(f"  Vertices: {len(vertices_3d)}")
    print(f"  Edges: {len(edges_3d)}")
    
    if len(vertices_3d) == 0:
        print("\nERROR: No 3D vertices reconstructed!")
        print("Coordinate system may still be misaligned.")
        return
    
    # Detect faces
    print("\n" + "=" * 70)
    print("[Step 2] Detect faces using minimal artifacts algorithm")
    print("=" * 70)
    
    triangles = find_all_faces_minimal_artifacts(
        vertices_3d, edges_3d,
        max_iterations=1000000
    )
    
    if len(triangles) == 0:
        print("\nERROR: No triangles detected!")
        return
    
    print(f"\n✓ Face Detection:")
    print(f"  Triangles: {len(triangles)}")
    
    # Export STL
    print("\n" + "=" * 70)
    print("[Step 3] Export STL mesh")
    print("=" * 70)
    
    stl_file = Path("../outputs/mesh_from_calibration.stl")
    stl_file.parent.mkdir(parents=True, exist_ok=True)
    
    export_stl_binary(str(stl_file), vertices_3d, triangles)
    
    print(f"\n✓ STL exported: {stl_file}")
    print(f"  Vertices: {len(vertices_3d)}")
    print(f"  Triangles: {len(triangles)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
