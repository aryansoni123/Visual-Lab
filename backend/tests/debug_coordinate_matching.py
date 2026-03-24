"""
Debug why coordinate matching fails across views.

The issue: vertices from different orthographic projections are in 
different 2D coordinate spaces. We need to understand what the actual
pixel values are.
"""

import json
from pathlib import Path

calib_file = Path("../outputs/calibrated_for_stl.json")

with open(calib_file) as f:
    calib = json.load(f)

front = calib['front']
top = calib['top']
side = calib['side']

print("=" * 70)
print("CALIBRATED COORDINATES (PIXEL SPACE WITH REFERENCE SCALING)")
print("=" * 70)

print("\nFRONT VIEW (26 vertices)")
print("-" * 70)
for i, v in enumerate(front['vertices'][:5]):
    print(f"  Vert {i}: ({v[0]:.2f}, {v[1]:.2f})")
print("  ...")

print("\nTOP VIEW (26 vertices)")
print("-" * 70)
for i, v in enumerate(top['vertices'][:5]):
    print(f"  Vert {i}: ({v[0]:.2f}, {v[1]:.2f})")
print("  ...")

print("\nSIDE VIEW (22 vertices)")
print("-" * 70)
for i, v in enumerate(side['vertices'][:5]):
    print(f"  Vert {i}: ({v[0]:.2f}, {v[1]:.2f})")
print("  ...")

# Check X coordinate ranges (should be similar for front and top)
front_x = [v[0] for v in front['vertices']]
top_x = [v[0] for v in top['vertices']]
side_y = [v[1] for v in side['vertices']]

print("\n" + "=" * 70)
print("CROSS-VIEW COORDINATE ANALYSIS")
print("=" * 70)

print(f"\nFront X (should be same as Top X):")
print(f"  Range: {min(front_x):.2f} to {max(front_x):.2f}")
print(f"  Count: {len(front_x)}")

print(f"\nTop X (should be same as Front X):")
print(f"  Range: {min(top_x):.2f} to {max(top_x):.2f}")
print(f"  Count: {len(top_x)}")

print(f"\nSide Y (should be same as Front Y):")
print(f"  Range: {min(side_y):.2f} to {max(side_y):.2f}")
print(f"  Count: {len(side_y)}")

# Check if coordinates actually overlap
front_x_set = set(round(x, 1) for x in front_x)
top_x_set = set(round(x, 1) for x in top_x)

overlap = front_x_set & top_x_set

print(f"\nX-coordinate overlap (Front ∩ Top at 0.1 tolerance):")
print(f"  Overlap: {len(overlap)} / {len(front_x_set)} Front, {len(top_x_set)} Top")
if overlap:
    print(f"  Overlapping values: {sorted(list(overlap))[:5]}")
