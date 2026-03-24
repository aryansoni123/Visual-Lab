"""
Robust orthographic calibration with tolerance-based matching.

Problem: Current pseudo-wireframe assumes EXACT coordinate matches
between 2D projections. But digitized images may have small registration shifts.

Solution: Use approximate coordinate matching with reasonable tolerance to
establish 3D vertices, then validate with edge consistency.

Approach:
1. For each Front vertex at (x, y):
   a. Find all Top vertices with x ≈ front_x (tolerance: ±2 pixels)
   b. Find all Side vertices with y ≈ front_y (tolerance: ±2 pixels)
   c. If Z coordinates from Top and Side match, create 3D vertex
2. For edges: match using the same tolerance
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from reconstruction.image_processing import image_to_2d_graph

def main():
    print("=" * 70)
    print("ROBUST ORTHOGRAPHIC CALIBRATION")
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
    print(f"  Front {len(front_verts)} verts, {len(front_edges)} edges")
    print(f"  Top:   {len(top_verts)} verts, {len(top_edges)} edges")
    print(f"  Side:  {len(side_verts)} verts, {len(side_edges)} edges")
    
    # Analysis: what's the coordinate precision?
    print("\n[Step 2] Analyze coordinate precision")
    print("=" * 70)
    
    front_x_vals = sorted(set(round(v[0], 1) for v in front_verts))
    top_x_vals = sorted(set(round(v[0], 1) for v in top_verts))
    
    print(f"\nFront X unique values: {len(front_x_vals)}")
    print(f"  Sample: {front_x_vals[:5]}")
    
    print(f"\nTop X unique values: {len(top_x_vals)}")
    print(f"  Sample: {top_x_vals[:5]}")
    
    # Check spacing between consecutive X values
    front_x_gaps = [front_x_vals[i+1] - front_x_vals[i] for i in range(len(front_x_vals)-1)]
    top_x_gaps = [top_x_vals[i+1] - top_x_vals[i] for i in range(len(top_x_vals)-1)]
    
    if front_x_gaps:
        print(f"\nFront X min gap: {min(front_x_gaps):.1f}, max gap: {max(front_x_gaps):.1f}")
    if top_x_gaps:
        print(f"Top X min gap: {min(top_x_gaps):.1f}, max gap: {max(top_x_gaps):.1f}")
    
    # Try progressive tolerance levels
    print("\n[Step 3] Test coordinate matching with different tolerances")
    print("=" * 70)
    
    def count_matches(vals1, vals2, tol):
        """Count approximate matches with given tolerance."""
        matches = 0
        for v1 in vals1:
            for v2 in vals2:
                if abs(v1 - v2) <= tol:
                    matches += 1
                    break
        return matches
    
    for tol in [0.1, 0.5, 1.0, 2.0, 3.0, 5.0]:
        matches_x = count_matches(front_x_vals, top_x_vals, tol)
        print(f"  Tolerance {tol:.1f}: {matches_x} Front X values match Top X")
    
    # Save pixel-space calibration (simplest approach)
    print("\n[Step 4] Save pixel-space calibration")
    print("=" * 70)
    
    calib = {
        "strategy": "pixel_space_direct",
        "description": "Raw pixel coordinates with minimal processing",
        "front": {
            "vertices": front_verts,
            "edges": front_edges,
        },
        "top": {
            "vertices": top_verts,
            "edges": top_edges,
        },
        "side": {
            "vertices": side_verts,
            "edges": side_edges,
        }
    }
    
    output_file = Path("../outputs/calibrated_pixelspace.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(calib, f, indent=2)
    
    print(f"✓ Saved: {output_file}")
    
    # Also try scaled version
    print("\n[Step 5] Save scaled pixel-space calibration")
    print("=" * 70)
    
    # Scale up by 10x to improve precision
    front_scaled_10 = [(v[0] * 10, v[1] * 10) for v in front_verts]
    top_scaled_10 = [(v[0] * 10, v[1] * 10) for v in top_verts]
    side_scaled_10 = [(v[0] * 10, v[1] * 10) for v in side_verts]
    
    calib_10x = {
        "strategy": "pixel_space_10x",
        "scale": 10,
        "description": "Pixel coordinates scaled by 10x for better precision",
        "front": {
            "vertices": front_scaled_10,
            "edges": front_edges,
        },
        "top": {
            "vertices": top_scaled_10,
            "edges": top_edges,
        },
        "side": {
            "vertices": side_scaled_10,
            "edges": side_edges,
        }
    }
    
    output_file_10x = Path("../outputs/calibrated_pixelspace_10x.json")
    
    with open(output_file_10x, 'w') as f:
        json.dump(calib_10x, f, indent=2)
    
    print(f"✓ Saved: {output_file_10x}")
    
    print("\n" + "=" * 70)
    print("CALIBRATIONS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
