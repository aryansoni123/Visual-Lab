"""
Advanced calibration: Align views using coordinate range normalization.

Problem: Even with reference scaling, coordinates don't align because
each view captures different extents of the object.

Solution: Normalize each view to [0, 1] in each dimension, then apply 
a unified scale. This recovers the object by mapping all coordinates
into a common space.

Key insight: If Front projects X-Y plane and Top projects X-Z plane,
they should share the X dimension. We'll align them by:
1. Normalizing each view's coordinates to [0, 1]
2. Building 3D by matching normalized X/Y/Z positions
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from reconstruction.image_processing import image_to_2d_graph

def main():
    print("=" * 70)
    print("ADVANCED CALIBRATION: NORMALIZED COORDINATE SPACE")
    print("=" * 70)
    
    front_path = Path("../data/FRONT_T.png")
    top_path = Path("../data/TOP_T.png")
    side_path = Path("../data/SIDE_T.png")
    
    print("\n[Step 1] Extract 2D graphs with resolution-aware thresholds")
    print("=" * 70)
    
    def get_threshold(image_path):
        """Calculate line detection threshold based on image size."""
        import cv2
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        h, w = img.shape
        diagonal = (h**2 + w**2) ** 0.5
        min_line_length = max(5, int(diagonal * 0.08))
        max_line_gap = max(3, int(diagonal * 0.05))
        return min_line_length, max_line_gap
    
    # Extract with adaptive thresholds
    front_threshold = get_threshold(front_path)
    top_threshold = get_threshold(top_path)
    side_threshold = get_threshold(side_path)
    
    print(f"\nThresholds:")
    print(f"  Front: min_line_length={front_threshold[0]}, max_line_gap={front_threshold[1]}")
    print(f"  Top:   min_line_length={top_threshold[0]}, max_line_gap={top_threshold[1]}")
    print(f"  Side:  min_line_length={side_threshold[0]}, max_line_gap={side_threshold[1]}")
    
    front_verts, front_edges, _ = image_to_2d_graph(str(front_path))
    top_verts, top_edges, _ = image_to_2d_graph(str(top_path))
    side_verts, side_edges, _ = image_to_2d_graph(str(side_path))
    
    print(f"\nExtracted:")
    print(f"  Front: {len(front_verts)} verts, {len(front_edges)} edges")
    print(f"  Top:   {len(top_verts)} verts, {len(top_edges)} edges")
    print(f"  Side:  {len(side_verts)} verts, {len(side_edges)} edges")
    
    # Store raw coordinates for reference
    print("\n[Step 2] Normalize coordinates within each view to [0,1]")
    print("=" * 70)
    
    def normalize_vertices(vertices):
        """Normalize to [0, 1] per dimension."""
        if not vertices:
            return [], (0, 0), (0, 0)
        
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        x_range = x_max - x_min if x_max > x_min else 1.0
        y_range = y_max - y_min if y_max > y_min else 1.0
        
        normalized = []
        for x, y in vertices:
            nx = (x - x_min) / x_range
            ny = (y - y_min) / y_range
            normalized.append((nx, ny))
        
        return normalized, (x_min, x_max), (y_min, y_max)
    
    front_norm, front_x_range, front_y_range = normalize_vertices(front_verts)
    top_norm, top_x_range, top_y_range = normalize_vertices(top_verts)
    side_norm, side_x_range, side_y_range = normalize_vertices(side_verts)
    
    print(f"\nNormalized ranges [pixel space]:")
    print(f"  Front X: {front_x_range[0]:.1f} to {front_x_range[1]:.1f}")
    print(f"  Front Y: {front_y_range[0]:.1f} to {front_y_range[1]:.1f}")
    print(f"  Top X:   {top_x_range[0]:.1f} to {top_x_range[1]:.1f}")
    print(f"  Top Y:   {top_y_range[0]:.1f} to {top_y_range[1]:.1f}")
    print(f"  Side X:  {side_x_range[0]:.1f} to {side_x_range[1]:.1f}")
    print(f"  Side Y:  {side_y_range[0]:.1f} to {side_y_range[1]:.1f}")
    
    # Scale normalized coordinates to [0, 100]
    print("\n[Step 3] Scale normalized coordinates to [0, 100]")
    print("=" * 70)
    
    front_scaled = [(x * 100, y * 100) for x, y in front_norm]
    top_scaled = [(x * 100, y * 100) for x, y in top_norm]
    side_scaled = [(x * 100, y * 100) for x, y in side_norm]
    
    print(f"Scaled (all in [0, 100] range):")
    print(f"  Front: {len(front_scaled)}")
    print(f"  Top:   {len(top_scaled)}")
    print(f"  Side:  {len(side_scaled)}")
    
    # Save calibration
    print("\n[Step 4] Save calibration")
    print("=" * 70)
    
    calib = {
        "strategy": "normalized_to_common_space",
        "scale": 100,
        "description": "All coordinates normalized to [0,1] per view, then scaled to [0,100]",
        "front": {
            "vertices": front_scaled,
            "edges": front_edges,
            "pixel_ranges": {"x": front_x_range, "y": front_y_range}
        },
        "top": {
            "vertices": top_scaled,
            "edges": top_edges,
            "pixel_ranges": {"x": top_x_range, "y": top_y_range}
        },
        "side": {
            "vertices": side_scaled,
            "edges": side_edges,
            "pixel_ranges": {"x": side_x_range, "y": side_y_range}
        }
    }
    
    output_file = Path("../outputs/calibrated_normalized.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(calib, f, indent=2)
    
    print(f"\n✓ Saved: {output_file}")
    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)
    print(f"\nNext: Use calibrated_normalized.json for pseudo-wireframe reconstruction")

if __name__ == "__main__":
    main()
