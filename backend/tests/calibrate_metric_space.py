"""
Orthographic multi-view calibration with unified metric space.

Key insight: For true orthographic projection, coordinates must have
consistent metric meaning across views:
- FRONT X = TOP X (width)
- FRONT Y = SIDE Y (height)  
- TOP Y = SIDE X (depth)

Instead of normalizing each view independently, we'll:
1. Keep pixel coordinates as-is (they're already in a metric space)
2. Find the scale factor from one reference view
3. Apply uniform scaling to all views
4. Use a modest tolerance for coordinate matching

This preserves metric relationships needed for reconstruction.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from reconstruction.image_processing import image_to_2d_graph

def main():
    print("=" * 70)
    print("ORTHOGRAPHIC CALIBRATION: UNIFIED METRIC SPACE")
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
    print(f"  Front: {len(front_verts)} verts, {len(front_edges)} edges")
    print(f"  Top:   {len(top_verts)} verts, {len(top_edges)} edges")
    print(f"  Side:  {len(side_verts)} verts, {len(side_edges)} edges")
    
    print(f"\nPixel ranges (raw):")
    if front_verts:
        fx_min, fx_max = min(v[0] for v in front_verts), max(v[0] for v in front_verts)
        fy_min, fy_max = min(v[1] for v in front_verts), max(v[1] for v in front_verts)
        print(f"  Front: X [{fx_min:.0f}, {fx_max:.0f}], Y [{fy_min:.0f}, {fy_max:.0f}]")
    
    if top_verts:
        tx_min, tx_max = min(v[0] for v in top_verts), max(v[0] for v in top_verts)
        ty_min, ty_max = min(v[1] for v in top_verts), max(v[1] for v in top_verts)
        print(f"  Top:   X [{tx_min:.0f}, {tx_max:.0f}], Y [{ty_min:.0f}, {ty_max:.0f}]")
    
    if side_verts:
        sx_min, sx_max = min(v[0] for v in side_verts), max(v[0] for v in side_verts)
        sy_min, sy_max = min(v[1] for v in side_verts), max(v[1] for v in side_verts)
        print(f"  Side:  X [{sx_min:.0f}, {sx_max:.0f}], Y [{sy_min:.0f}, {sy_max:.0f}]")
    
    # Key insight: Front X should ~ Top X if they're orthographic projections
    # Front Y should ~ Side Y
    # TOP Y should ~ Side X
    print(f"\nExpected metric relationships:")
    print(f"  Front X range should ≈ Top X range (both are width)")
    print(f"  Front Y range should ≈ Side Y range (both are height)")
    print(f"  Top Y range should ≈ Side X range (both are depth)")
    
    # The solution: Instead of per-view normalization, scale to maximize
    # overlap of the metric spaces. We'll use a simple reference-based approach:
    # - For each view dimension, scale by max_coord * 2 to give safe range
    
    reference_scale = 100  # Use [0, 200] space for each view as reference
    
    print(f"\n[Step 2] Apply uniform reference scaling ({reference_scale}x)")
    print("=" * 70)
    
    # Strategy: scale each view by its own maximum to fill [0, reference_scale*2]
    # This keeps relative geometry but allows cross-view matching
    
    def scale_vertices(vertices, ref_scale=reference_scale):
        if not vertices:
            return []
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        max_coord = max(max(xs), max(ys))
        scale_factor = (ref_scale * 2) / max_coord if max_coord > 0 else 1
        return [(v[0] * scale_factor, v[1] * scale_factor) for v in vertices]
    
    front_scaled = scale_vertices(front_verts, reference_scale)
    top_scaled = scale_vertices(top_verts, reference_scale)
    side_scaled = scale_vertices(side_verts, reference_scale)
    
    print(f"Scaled to reference {{[0, {reference_scale*2}]}}:")
    print(f"  Front: {len(front_scaled)} verts")
    print(f"  Top:   {len(top_scaled)} verts")
    print(f"  Side:  {len(side_scaled)} verts")
    
    # Alternative: Simple pixel scaling without normalization
    # This might preserve more of the metric properties
    print(f"\n[Step 3] Strategy: Direct pixel coordinates with light scaling")
    print("=" * 70)
    
    # Use raw pixel coords but scale by 0.5 to make them fit nicely
    light_scale = 0.5
    front_light = [(v[0] * light_scale, v[1] * light_scale) for v in front_verts]
    top_light = [(v[0] * light_scale, v[1] * light_scale) for v in top_verts]
    side_light = [(v[0] * light_scale, v[1] * light_scale) for v in side_verts]
    
    print(f"Light scaled (pixel coords × {light_scale}):")
    print(f"  Front X: {min(v[0] for v in front_light):.1f} to {max(v[0] for v in front_light):.1f}")
    print(f"  Top X:   {min(v[0] for v in top_light):.1f} to {max(v[0] for v in top_light):.1f}")
    
    # Save both strategies for testing
    print(f"\n[Step 4] Save calibrations")
    print("=" * 70)
    
    calib_uniform = {
        "strategy": "uniform_reference_scale",
        "scale": reference_scale,
        "description": f"Each view scaled to [0, {reference_scale*2}] range",
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
    
    calib_light = {
        "strategy": "light_pixel_scale",
        "scale": light_scale,
        "description": "Pixel coordinates scaled by 0.5 (preserves metric properties)",
        "front": {
            "vertices": front_light,
            "edges": front_edges,
        },
        "top": {
            "vertices": top_light,
            "edges": top_edges,
        },
        "side": {
            "vertices": side_light,
            "edges": side_edges,
        }
    }
    
    output_prefix = Path("../outputs")
    output_prefix.mkdir(parents=True, exist_ok=True)
    
    with open(output_prefix / "calibrated_uniform.json", 'w') as f:
        json.dump(calib_uniform, f, indent=2)
    print(f"✓ Saved: calibrated_uniform.json")
    
    with open(output_prefix / "calibrated_light_scale.json", 'w') as f:
        json.dump(calib_light, f, indent=2)
    print(f"✓ Saved: calibrated_light_scale.json")
    
    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)
    print(f"\nNext: Test both calibrations with pseudo-wireframe reconstruction")

if __name__ == "__main__":
    main()
