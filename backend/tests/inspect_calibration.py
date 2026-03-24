"""Inspect calibrated JSON output."""
import json

with open('../outputs/calibrated_multiview.json') as f:
    data = json.load(f)

print("="*70)
print("CALIBRATED MULTIVIEW JSON STRUCTURE")
print("="*70)

print("\nTop-level keys:", list(data.keys()))

print("\n" + "="*70)
print("FRONT VIEW")
print("="*70)
print(f"  Vertices: {len(data['front']['vertices'])}")
print(f"  Sample (first 3): {data['front']['vertices'][:3]}")
print(f"  Edges: {len(data['front']['edges'])}")
print(f"  Sample edges: {data['front']['edges'][:3]}")
print(f"  Metadata:")
print(f"    Resolution: {data['front']['metadata']['width']}x{data['front']['metadata']['height']}")
print(f"    Aspect ratio: {data['front']['metadata']['aspect_ratio']:.2f}")

print("\n" + "="*70)
print("TOP VIEW")
print("="*70)
print(f"  Vertices: {len(data['top']['vertices'])}")
print(f"  Edges: {len(data['top']['edges'])}")
print(f"  Resolution: {data['top']['metadata']['width']}x{data['top']['metadata']['height']}")

print("\n" + "="*70)
print("SIDE VIEW")
print("="*70)
print(f"  Vertices: {len(data['side']['vertices'])}")
print(f"  Edges: {len(data['side']['edges'])}")
print(f"  Resolution: {data['side']['metadata']['width']}x{data['side']['metadata']['height']}")

print("\n" + "="*70)
print("CANONICAL COORDINATE SETS (normalized [0,1])")
print("="*70)
print(f"  X coordinates ({len(data['coordinates']['x'])} values):")
print(f"    {data['coordinates']['x'][:8]} ...")
print(f"  Y coordinates ({len(data['coordinates']['y'])} values):")
print(f"    {data['coordinates']['y'][:8]} ...")
print(f"  Z coordinates ({len(data['coordinates']['z'])} values):")
print(f"    {data['coordinates']['z'][:8]} ...")

print("\n" + "="*70)
print("3D RECONSTRUCTION VALIDATION")
print("="*70)
print(f"  Successful 3D coordinate matches: {data['3d_matches']}")
if data['3d_matches'] > 0:
    print(f"  ✓ Views are properly calibrated and compatible")
else:
    print(f"  ⚠ Low match count - views may need further alignment")

print("\n" + "="*70)
print("USAGE")
print("="*70)
print("""
This JSON file contains:
1. Normalized 2D vertices and edges for each view
2. Image metadata (resolution, aspect ratio)
3. Canonical coordinates (X, Y, Z sets that appear across views)
4. Validation metrics (3D match count)

Next steps:
- Feed to pseudo-wireframe reconstruction using calibrated coordinates
- Use canonical X/Y/Z sets to match vertices across views
- Extract 3D vertices by finding (x,y,z) triplets across views
""")
