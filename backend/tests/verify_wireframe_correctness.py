"""Verify that the reconstructed wireframe matches the reference geometry."""

from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper


def build_projection_graph(lambda_rows, theta_edges, axes):
    """Project 3D wireframe onto a 2D plane and deduplicate points/edges."""
    points2d = [tuple(float(lambda_rows[i][a]) for a in axes) for i in range(len(lambda_rows))]
    index_by_point = {}
    vertices2d = []
    map3d_to2d = {}
    for i, p in enumerate(points2d):
        if p not in index_by_point:
            index_by_point[p] = len(vertices2d)
            vertices2d.append(p)
        map3d_to2d[i] = index_by_point[p]
    edges2d = set()
    for u, v in theta_edges:
        pu = map3d_to2d[u]
        pv = map3d_to2d[v]
        if pu != pv:
            a, b = (pu, pv) if pu < pv else (pv, pu)
            edges2d.add((a, b))
    return vertices2d, sorted(edges2d)


def main():
    # Reference geometry
    Lambda_ref = [
        [0, 0, 0, 0, 0, 0], [6, 0, 0, 0, 0, 0], [6, 4, 0, 0, 0, 0], [0, 4, 0, 0, 0, 0],
        [0, 0, 8, 0, 0, 0], [6, 0, 8, 0, 0, 0], [6, 4, 8, 0, 0, 0], [0, 4, 8, 0, 0, 0],
        [-3, 0, 8, 0, 0, 0], [-3, 4, 8, 0, 0, 0], [-3, 0, 5, 0, 0, 0], [-3, 4, 5, 0, 0, 0],
        [0, 0, 5, 0, 0, 0], [0, 4, 5, 0, 0, 0], [0, 0, 4, 0, 0, 0], [0, 4, 4, 0, 0, 0],
    ]
    
    Theta_ref = [
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7), (4, 0), (3, 2), (5, 1),
        (8, 9), (9, 7), (7, 4), (4, 8), (8, 10), (9, 11), (10, 12), (11, 13),
        (12, 4), (13, 7), (11, 9), (12, 14), (13, 15), (12, 13),
        (14, 15), (14, 0), (15, 3), (10, 11),
    ]
    
    print("=" * 70)
    print("WIREFRAME CORRECTNESS VERIFICATION")
    print("=" * 70)
    
    # Generate projections
    front_vertices, front_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 1))
    top_vertices, top_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 2))
    side_vertices, side_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(1, 2))
    
    # Reconstruct
    Lambda, Theta, _ = build_pseudo_wireframe_paper(
        front_vertices, front_edges, top_vertices, top_edges,
        side_vertices, side_edges, split_intersections=False,
    )
    
    print(f"\n1. REFERENCE GEOMETRY:")
    print(f"   Lambda_ref: {len(Lambda_ref)} vertices")
    print(f"   Theta_ref:  {len(Theta_ref)} edges")
    
    print(f"\n2. RECONSTRUCTED WIREFRAME:")
    print(f"   Lambda: {len(Lambda)} vertices")
    print(f"   Theta:  {len(Theta)} edges")
    
    # Compare Lambda (vertices)
    print(f"\n3. VERTEX COMPARISON:")
    print(f"   Reference vertices (first 3 coords only):")
    for i, v in enumerate(Lambda_ref):
        print(f"     {i}: {v[:3]}")
    
    print(f"\n   Reconstructed vertices:")
    for i, v in enumerate(Lambda):
        print(f"     {i}: {v[:3]}")
    
    vertex_match = len(Lambda) == len(Lambda_ref)
    print(f"\n   Vertex count matches: {vertex_match}")
    
    # Compare Theta (edges)
    print(f"\n4. EDGE COMPARISON:")
    print(f"   Reference edges (Theta_ref):")
    theta_ref_sorted = sorted(Theta_ref)
    for i, e in enumerate(theta_ref_sorted):
        print(f"     {i}: {e}")
    
    print(f"\n   Reconstructed edges (Theta):")
    theta_sorted = sorted(Theta)
    for i, e in enumerate(theta_sorted):
        print(f"     {i}: {e}")
    
    # Find differences
    ref_set = set((min(u, v), max(u, v)) for u, v in Theta_ref)
    rec_set = set((min(u, v), max(u, v)) for u, v in Theta)
    
    missing = ref_set - rec_set
    extra = rec_set - ref_set
    
    print(f"\n5. EDGE DIFFERENCES:")
    print(f"   Edges in reference but MISSING in reconstruction: {len(missing)}")
    if missing:
        for e in sorted(missing):
            print(f"     MISSING: {e}")
    
    print(f"\n   EXTRA edges in reconstruction (not in reference): {len(extra)}")
    if extra:
        for e in sorted(extra):
            print(f"     EXTRA: {e}")
    
    edge_match = len(missing) == 0 and len(extra) == 0
    print(f"\n   Edges match exactly: {edge_match}")
    
    # Verdict
    print(f"\n{'=' * 70}")
    if vertex_match and edge_match:
        print("✓✓✓ WIREFRAME IS CORRECT - Perfect match!")
    elif vertex_match:
        print(f"⚠ WIREFRAME HAS EDGE ISSUES - {len(missing)} missing, {len(extra)} extra")
    else:
        print("✗ WIREFRAME IS INCORRECT - Vertex count mismatch")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
