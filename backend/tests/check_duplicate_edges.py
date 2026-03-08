"""Check for duplicate edges in the reference Theta."""

Theta_ref = [
    (0, 1), (1, 2), (2, 3), (3, 0),         # Bottom rectangle
    (4, 5), (5, 6), (6, 7), (7, 4),         # Top main rectangle
    (0, 4), (1, 5), (2, 6), (3, 7),         # Vertical main block
    (4, 0), (3, 2), (5, 1),                 # Additional main faces
    (8, 9), (9, 7), (7, 4), (4, 8),         # Left extension top
    (8, 10), (9, 11), (10, 12), (11, 13),   # Left extension verticals
    (12, 4), (13, 7),                       # Left extension inner
    (11, 9),                                # Left extension back
    (12, 14), (13, 15),                     # Lower ledge
    (12, 13),                               # Lower ledge inner
    (14, 15),                               # Lower ledge bottom
    (14, 0), (15, 3),                       # Lower drop verticals
    (10, 11),                               # Left extension depth
]

print(f"Total edges in list: {len(Theta_ref)}")

# Normalize edges (undirected)
normalized = set()
duplicates = []

for i, (u, v) in enumerate(Theta_ref):
    edge_key = (min(u, v), max(u, v))
    if edge_key in normalized:
        duplicates.append((i, edge_key, "duplicate of earlier entry"))
    normalized.add(edge_key)

print(f"Unique edges: {len(normalized)}")
print(f"Duplicates found: {len(duplicates)}")

if duplicates:
    print("\nDuplicate edges:")
    for idx, edge, msg in duplicates:
        print(f"  Index {idx}: {Theta_ref[idx]} -> normalized {edge} ({msg})")

# Check which edges appear in the list
edge_count = {}
for u, v in Theta_ref:
    key = (min(u, v), max(u, v))
    edge_count[key] = edge_count.get(key, 0) + 1

multi_count = [(e, c) for e, c in edge_count.items() if c > 1]
if multi_count:
    print(f"\nEdges appearing multiple times:")
    for edge, count in sorted(multi_count):
        print(f"  {edge}: appears {count} times")
