"""Verify wireframe with vertex index mapping between reference and reconstructed."""

from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper
import numpy as np


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
        [0, 0,0], [6, 0, 0], [6, 4, 0], [0, 4, 0],
        [0, 0, 8], [6, 0, 8], [6, 4, 8], [0, 4, 8],
        [-3, 0, 8], [-3, 4, 8], [-3, 0, 5], [-3, 4, 5],
        [0, 0, 5], [0, 4, 5], [0, 0, 4], [0, 4, 4],
    ]
    
    Theta_ref = [
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7), (4, 0), (3, 2), (5, 1),
        (8, 9), (9, 7), (7, 4), (4, 8), (8, 10), (9, 11), (10, 12), (11, 13),
        (12, 4), (13, 7), (11, 9), (12, 14), (13, 15), (12, 13),
        (14, 15), (14, 0), (15, 3), (10, 11),
    ]
    
    # Reconstruct
    front_vertices, front_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 1))
    top_vertices, top_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 2))
    side_vertices, side_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(1, 2))
    
    Lambda, Theta, _ = build_pseudo_wireframe_paper(
        front_vertices, front_edges, top_vertices, top_edges,
        side_vertices, side_edges, split_intersections=False,
    )
    
    # Build vertex coordinate mapping: ref_idx -> rec_idx
    ref_to_rec = {}
    tol = 1e-6
    
    for ref_idx, ref_v in enumerate(Lambda_ref):
        for rec_idx, rec_v in enumerate(Lambda):
            if (abs(ref_v[0] - rec_v[0]) < tol and 
                abs(ref_v[1] - rec_v[1]) < tol and
                abs(ref_v[2] - rec_v[2]) < tol):
                ref_to_rec[ref_idx] = rec_idx
                break
    
    print("=" * 70)
    print("VERTEX MAPPING (Reference -> Reconstructed)")
    print("=" * 70)
    for ref_idx in sorted(ref_to_rec.keys()):
        rec_idx = ref_to_rec[ref_idx]
        print(f"  Ref {ref_idx}: {Lambda_ref[ref_idx][:3]} -> Rec {rec_idx}: {Lambda[rec_idx][:3]}")
    
    # Map reference edges to reconstructed indices
    mapped_ref_edges = set()
    unmappable = []
    
    for u, v in Theta_ref:
        if u in ref_to_rec and v in ref_to_rec:
            rec_u = ref_to_rec[u]
            rec_v = ref_to_rec[v]
            mapped_ref_edges.add((min(rec_u, rec_v), max(rec_u, rec_v)))
        else:
            unmappable.append((u, v))
    
    # Compare
    rec_edges = set((min(u, v), max(u, v)) for u, v in Theta)
    
    missing = mapped_ref_edges - rec_edges
    extra = rec_edges - mapped_ref_edges
    
    print(f"\n{'=' * 70}")
    print("EDGE COMPARISON (After Vertex Mapping)")
    print("=" * 70)
    print(f"Reference edges (mapped): {len(mapped_ref_edges)}")
    print(f"Reconstructed edges: {len(rec_edges)}")
    print(f"\nMissing edges: {len(missing)}")
    if missing:
        print("  Missing (in reconstructed indices):")
        for e in sorted(missing):
            print(f"    {e}")
    
    print(f"\nExtra edges: {len(extra)}")
    if extra:
        print("  Extra (in reconstructed indices):")
        for e in sorted(extra):
            print(f"    {e}")
    
    print(f"\n{'=' * 70}")
    if len(missing) == 0 and len(extra) == 0:
        print("✓✓✓ EDGES MATCH PERFECTLY (after vertex reordering)")
    else:
        print(f"⚠ WIREFRAME STILL HAS ISSUES: {len(missing)} missing, {len(extra)} extra")
    print("=" * 70)


if __name__ == "__main__":
    main()
