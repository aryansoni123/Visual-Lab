"""
Inspect actual normalized coordinates and match precision.
"""

import json
from pathlib import Path

calib_file = Path("../outputs/calibrated_normalized.json")

with open(calib_file) as f:
    calib = json.load(f)

front = calib['front']['vertices']
top = calib['top']['vertices']
side = calib['side']['vertices']

print("NORMALIZED COORDINATES [0, 100]")
print("=" * 70)

print("\nFRONT X coordinates:")
front_x = sorted(set(round(v[0], 2) for v in front))
print(f"  {len(front_x)} unique X values: {front_x[:10]}")

print("\nTOP X coordinates:")
top_x = sorted(set(round(v[0], 2) for v in top))
print(f"  {len(top_x)} unique X values: {top_x[:10]}")

print("\nMatching X between Front and Top (tolerance 0.5):")
matches = 0
for fx in front_x:
    for tx in top_x:
        if abs(fx - tx) < 0.5:
            matches += 1
            break

print(f"  Matches: {matches} out of {len(front_x)} Front coords")

# Check Front Y and evaluate
print("\nFRONT Y coordinates:")
front_y = sorted(set(round(v[1], 2) for v in front))
print(f"  {len(front_y)} unique Y values: {front_y[:10]}")

print("\nSIDE Y coordinates:")
side_y = sorted(set(round(v[1], 2) for v in side))
print(f"  {len(side_y)} unique Y values: {side_y[:10]}")

print("\nMatching Y between Front and Side (tolerance 0.5):")
matches = 0
for fy in front_y:
    for sy in side_y:
        if abs(fy - sy) < 0.5:
            matches += 1
            break

print(f"  Matches: {matches} out of {len(front_y)} Front coords")

# The real issue: pseudo_wireframe_paper.py looks for EXACT coordinate matches
# Let's check with the actual tolerance used in that code

print("\n" + "=" * 70)
print("CHECKING ACTUAL TOLERANCE IN PSEUDO_WIREFRAME")
print("=" * 70)

# From pseudo_wireframe_paper.py, TOL = 1e-6
TOL = 1e-6

# But it uses _round_key_2d which rounds to nearest integer with scale=1e6
scale = 1.0 / max(TOL, 1e-12)
print(f"\nRounding scale: {scale}")
print(f"Effective precision: 1e-6 (6 decimal places)")

# With our coordinates in [0, 100], this means:
# Threshold: 100 * 1e-6 = 0.0001

print(f"With coordinates in [0, 100]:")
print(f"  Coordinates must match to 6+ decimal places")
print(f"  Our normalized coords have ~2 decimal places")
print(f"  MISMATCH: Our precision ({len(str(front[0][0]).split('.')[1])} decimals) < Required (6 decimals)")

print("\nSolution needed: Either")
print("  1. Scale coordinates to larger values (e.g., [0, 1000000])")
print("  2. Or modify pseudo_wireframe_paper.py to use higher tolerance")
print("  3. Or implement explicit coordinate mapping between views")
