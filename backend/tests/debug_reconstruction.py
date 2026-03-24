"""
Debug: Understand why 3D reconstruction fails on calibrated views.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper

# Load calibrated data
with open('../outputs/calibrated_multiview.json') as f:
    data = json.load(f)

front_v = data['front']['vertices']
front_e = data['front']['edges']
top_v = data['top']['vertices']
top_e = data['top']['edges']
side_v = data['side']['vertices']
side_e = data['side']['edges']

print("="*70)
print("DEBUG: 3D RECONSTRUCTION DIAGNOSTICS")
print("="*70)

# Check data types
print("\nData types:")
print(f"  Front vertices type: {type(front_v[0])} - {front_v[0]}")
print(f"  Front edges type: {type(front_e[0])} - {front_e[0]}")

# Check coordinate ranges
print("\nCoordinate ranges (normalized [0,1]):")
print(f"  Front X: {min(v[0] for v in front_v):.3f} to {max(v[0] for v in front_v):.3f}")
print(f"  Front Y: {min(v[1] for v in front_v):.3f} to {max(v[1] for v in front_v):.3f}")
print(f"  Top X:   {min(v[0] for v in top_v):.3f} to {max(v[0] for v in top_v):.3f}")
print(f"  Top Z:   {min(v[1] for v in top_v):.3f} to {max(v[1] for v in top_v):.3f}")
print(f"  Side Y:  {min(v[0] for v in side_v):.3f} to {max(v[0] for v in side_v):.3f}")
print(f"  Side Z:  {min(v[1] for v in side_v):.3f} to {max(v[1] for v in side_v):.3f}")

# Check how many unique X, Y, Z coordinates
front_x = set(round(v[0], 2) for v in front_v)
front_y = set(round(v[1], 2) for v in front_v)
top_x = set(round(v[0], 2) for v in top_v)
top_z = set(round(v[1], 2) for v in top_v)
side_y = set(round(v[0], 2) for v in side_v)
side_z = set(round(v[1], 2) for v in side_v)

print(f"\nUnique coordinates (quantized to 0.01):")
print(f"  Front X: {len(front_x)}, Y: {len(front_y)}")
print(f"  Top X:   {len(top_x)}, Z: {len(top_z)}")
print(f"  Side Y:  {len(side_y)}, Z: {len(side_z)}")

# Check coordinate overlap
x_overlap = front_x & top_x
y_overlap = front_y & side_y
z_overlap = top_z & side_z

print(f"\nCoordinate overlap (at tolerance 0.01):")
print(f"  X (front ∩ top): {len(x_overlap)}/{min(len(front_x), len(top_x))}")
print(f"  Y (front ∩ side): {len(y_overlap)}/{min(len(front_y), len(side_y))}")
print(f"  Z (top ∩ side): {len(z_overlap)}/{min(len(top_z), len(side_z))}")

# Try reconstruction with debug output
print("\n" + "="*70)
print("Attempting 3D reconstruction...")
print("="*70)

try:
    # Convert lists to tuples if needed
    front_v_tuples = [tuple(v) for v in front_v]
    top_v_tuples = [tuple(v) for v in top_v]
    side_v_tuples = [tuple(v) for v in side_v]
    
    Lambda, Theta, metadata = build_pseudo_wireframe_paper(
        front_v_tuples, front_e,
        top_v_tuples, top_e,
        side_v_tuples, side_e,
        split_intersections=True,
    )
    
    print(f"\nResult:")
    print(f"  Lambda: {len(Lambda)} vertices")
    print(f"  Theta: {len(Theta)} edges")
    
    if len(Lambda) > 0:
        print(f"\n  Sample 3D vertices:")
        for i, v in enumerate(Lambda[:5]):
            print(f"    {i}: {v}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

# Recommendation
print("\n" + "="*70)
print("ANALYSIS")
print("="*70)

if len(x_overlap) == 0 or len(y_overlap) == 0 or len(z_overlap) == 0:
    print("""
✗ COORDINATE MISMATCH: Views don't share sufficient coordinate values

The normalized coordinates have almost no overlap across views.
This is because:
1. Each image has different drawing positions (different bounding boxes)
2. Normalization to [0,1] per-view makes coordinates incompatible

Solution: Instead of per-view normalization, we need:
- Global coordinate system across all three views
- OR intelligent coordinate alignment/snapping
- OR use the canonical coordinate sets from calibration data
""")
else:
    print(f"""
Partial match found. Building new alignment strategy...
""")
