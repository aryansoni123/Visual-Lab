"""
High-precision calibration: Scale coordinates to preserve matching precision.

The issue: pseudo_wireframe_paper.py uses integer rounding with tolerance 1e-6.
This means coordinates are divided by 1e-6 before matching.

For matching to work:
- Two 2D coordinates that should be the same 3D projection must match after rounding
- If we scale coordinates to [0, 1e6], then dividing by 1e-6 gives [0, 1e12]
- This provides plenty of precision for matching

Strategy:
1. Extract pixel coordinates (no per-view normalization)
2. Scale to large range [0, 1e6] to match pseudo_wireframe precision
3. This preserves metric relationships between views
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from reconstruction.image_processing import image_to_2d_graph

def main():
    print("=" * 70)
    print("HIGH-PRECISION CALIBRATION FOR PSEUDO-WIREFRAME")
    print("=" * 70)
    
    front_path = Path("../data/FRONT_T.png")
    top_path = Path("../data/TOP_T.png")
    side_path = Path("../data/SIDE_T.png")
    
    print("\n[Step 1] Extract 2D graphs")
    print("=" * 70)
    
    front_verts, front_edges, _ = image_to_2d_graph(str(front_path))
    top_verts, top_edges, _ = image_to_2d_graph(str(top_path))
    side_verts, side_edges, _ = image_to_2d_graph(str(side_path))
    
    print(f"Extracted:")
    print(f"  Front: {len(front_verts)} verts")
    print(f"  Top:   {len(top_verts)} verts")
    print(f"  Side:  {len(side_verts)} verts")
    
    # Find global reference ranges
    print("\n[Step 2] Find global coordinate ranges")
    print("=" * 70)
    
    all_x = []
    all_y = []
    
    for v in front_verts:
        all_x.append(v[0])
        all_y.append(v[1])
    for v in top_verts:
        all_x.append(v[0])
        all_y.append(v[1])
    for v in side_verts:
        all_x.append(v[0])
        all_y.append(v[1])
    
    if all_x:
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        x_range = x_max - x_min if x_max > x_min else 1
        y_range = y_max - y_min if y_max > y_min else 1
        
        print(f"  Global X: [{x_min:.0f}, {x_max:.0f}] (range: {x_range:.0f})")
        print(f"  Global Y: [{y_min:.0f}, {y_max:.0f}] (range: {y_range:.0f})")
    
    # Scale to high precision range [0, 1e6]
    print("\n[Step 3] Scale to high-precision range [0, 1e6]")
    print("=" * 70)
    
    target_range = 1e6
    scale_factor = target_range / max(x_range, y_range)
    
    print(f"  Scale factor: {scale_factor:.2f}")
    print(f"  Target range: [0, {target_range:.0f}]")
    
    def scale_vertices(vertices, x_min, y_min, scale):
        return [((v[0] - x_min) * scale, (v[1] - y_min) * scale) for v in vertices]
    
    front_scaled = [((v[0] - x_min) * scale_factor, (v[1] - y_min) * scale_factor) for v in front_verts]
    top_scaled = [((v[0] - x_min) * scale_factor, (v[1] - y_min) * scale_factor) for v in top_verts]
    side_scaled = [((v[0] - x_min) * scale_factor, (v[1] - y_min) * scale_factor) for v in side_verts]
    
    print(f"\nScaled ranges:")
    if front_scaled:
        fx_min, fx_max = min(v[0] for v in front_scaled), max(v[0] for v in front_scaled)
        fy_min, fy_max = min(v[1] for v in front_scaled), max(v[1] for v in front_scaled)
        print(f"  Front: X [{fx_min:.0f}, {fx_max:.0f}], Y [{fy_min:.0f}, {fy_max:.0f}]")
    
    # Check coordinate overlap now
    print("\n[Step 4] Check coordinate matching potential")
    print("=" * 70)
    
    front_x = set(round(v[0]) for v in front_scaled)
    top_x = set(round(v[0]) for v in top_scaled)
    overlap_x = len(front_x & top_x)
    
    front_y = set(round(v[1]) for v in front_scaled)
    side_y = set(round(v[1]) for v in side_scaled)
    overlap_y = len(front_y & side_y)
    
    print(f"  Front X ∩ Top X (should share width): {overlap_x} matches out of {len(front_x)}")
    print(f"  Front Y ∩ Side Y (should share height): {overlap_y} matches out of {len(front_y)}")
    
    if overlap_x == 0 and overlap_y == 0:
        print("\n⚠ WARNING: No coordinate overlap even after scaling!")
        print("This suggests the views show different geometries or the line extraction")
        print("picked up different features. verify the_T images are truly orthographic")
        print("projections of the same object.")
    
    # Save calibration
    print("\n[Step 5] Save calibration")
    print("=" * 70)
    
    calib = {
        "strategy": "high_precision_scale",
        "scale_factor": float(scale_factor),
        "target_range": float(target_range),
        "description": f"Pixel coordinates scaled to [0, {target_range:.0f}] for pseudo-wireframe precision",
        "front": {
            "vertices": front_scaled,
            "edges": front_edges,
        },
        "top": {
            "vertices": top_scaled,
            "edges": top_edges,
        },
        "side": {
            "vertices": side_scaled,
            "edges": side_edges,
        }
    }
    
    output_file = Path("../outputs/calibrated_highprecision.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(calib, f, indent=2)
    
    print(f"✓ Saved: {output_file}")
    
    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
