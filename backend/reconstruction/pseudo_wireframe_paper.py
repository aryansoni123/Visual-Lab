"""
Pseudo-wireframe reconstruction aligned to the paper-style constraint flow.

Design goals:
- Keep reconstruction deterministic and conservative.
- Avoid over-generation of 3D edges (ghost edges).
- Separate preprocessing from reconstruction core.

Pipeline (vector-input case):
1. Split 2D segments at intersections (optional but recommended).
2. Build consistent 2D vertex/edge graphs per view.
3. Generate Lambda by coordinate consistency across views.
4. Generate Theta using strict multi-view edge-consistency constraints.

Notes:
- This implementation intentionally does NOT perform collinearity-based edge augmentation,
  since that can inflate Theta for some geometries.
"""

from itertools import combinations
from typing import Dict, List, Sequence, Tuple

TOL = 1e-6

Point2D = Tuple[float, float]
Edge2D = Tuple[int, int]
Point3D = Tuple[float, float, float]
LambdaRow = List[float]


def _round_key_2d(p: Point2D, tol: float = TOL) -> Tuple[int, int]:
    scale = 1.0 / max(tol, 1e-12)
    return (int(round(p[0] * scale)), int(round(p[1] * scale)))


def _edge_key(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def _point_on_segment(p: Point2D, a: Point2D, b: Point2D, tol: float = TOL) -> bool:
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > tol:
        return False
    dot = (p[0] - a[0]) * (p[0] - b[0]) + (p[1] - a[1]) * (p[1] - b[1])
    return dot <= tol


def _segment_intersection(a1: Point2D, a2: Point2D, b1: Point2D, b2: Point2D, tol: float = TOL):
    def det(u: Point2D, v: Point2D) -> float:
        return u[0] * v[1] - u[1] * v[0]

    xdiff = (a1[0] - a2[0], b1[0] - b2[0])
    ydiff = (a1[1] - a2[1], b1[1] - b2[1])

    div = det(xdiff, ydiff)
    if abs(div) < tol:
        return None

    d = (det(a1, a2), det(b1, b2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    p = (x, y)

    if _point_on_segment(p, a1, a2, tol) and _point_on_segment(p, b1, b2, tol):
        return p
    return None


def split_projection_segments(vertices: Sequence[Point2D], edges: Sequence[Edge2D], tol: float = TOL):
    """Split segments at all intersections and return a cleaned 2D graph."""
    vertices = list(vertices)
    edge_points = [(vertices[u], vertices[v]) for u, v in edges]

    split_points: Dict[int, List[Point2D]] = {
        i: [edge_points[i][0], edge_points[i][1]] for i in range(len(edge_points))
    }

    for i in range(len(edge_points)):
        for j in range(i + 1, len(edge_points)):
            p = _segment_intersection(
                edge_points[i][0], edge_points[i][1], edge_points[j][0], edge_points[j][1], tol
            )
            if p is not None:
                split_points[i].append(p)
                split_points[j].append(p)

    index_by_key: Dict[Tuple[int, int], int] = {}
    out_vertices: List[Point2D] = []

    def add_vertex(p: Point2D) -> int:
        key = _round_key_2d(p, tol)
        if key in index_by_key:
            return index_by_key[key]
        idx = len(out_vertices)
        out_vertices.append((float(p[0]), float(p[1])))
        index_by_key[key] = idx
        return idx

    out_edges_set = set()
    for pts in split_points.values():
        unique_pts = {}
        for p in pts:
            unique_pts[_round_key_2d(p, tol)] = p
        pts = list(unique_pts.values())

        p0 = pts[0]
        pts.sort(key=lambda p: (p[0] - p0[0]) ** 2 + (p[1] - p0[1]) ** 2)

        for i in range(len(pts) - 1):
            u = add_vertex(pts[i])
            v = add_vertex(pts[i + 1])
            if u != v:
                out_edges_set.add(_edge_key(u, v))

    return out_vertices, sorted(out_edges_set)


def _build_lambda(front_vertices, top_vertices, side_vertices, tol: float = TOL):
    """
    Build Lambda from coordinate consistency:
    - x from front/top
    - y from front/side
    - z from top/side
    """
    top_x_map: Dict[Tuple[int], List[Tuple[int, float]]] = {}
    for i, (x, z) in enumerate(top_vertices):
        kx = int(round(x / max(tol, 1e-12)))
        top_x_map.setdefault((kx,), []).append((i, z))

    side_y_map: Dict[Tuple[int], List[Tuple[int, float]]] = {}
    for i, (y, z) in enumerate(side_vertices):
        ky = int(round(y / max(tol, 1e-12)))
        side_y_map.setdefault((ky,), []).append((i, z))

    lambda_rows: List[LambdaRow] = []
    seen = set()

    for i_f, (x_f, y_f) in enumerate(front_vertices):
        kx = (int(round(x_f / max(tol, 1e-12))),)
        ky = (int(round(y_f / max(tol, 1e-12))),)

        if kx not in top_x_map or ky not in side_y_map:
            continue

        for i_t, z_t in top_x_map[kx]:
            for i_s, z_s in side_y_map[ky]:
                if abs(z_t - z_s) <= tol:
                    key = (
                        int(round(x_f / max(tol, 1e-12))),
                        int(round(y_f / max(tol, 1e-12))),
                        int(round(z_t / max(tol, 1e-12))),
                        i_f,
                        i_t,
                        i_s,
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    lambda_rows.append([float(x_f), float(y_f), float(z_t), i_f, i_t, i_s])

    return lambda_rows


def _supports_projected_edge(edge_set: set, a: int, b: int) -> bool:
    return _edge_key(a, b) in edge_set


def _build_theta(lambda_rows: Sequence[LambdaRow], front_edges, top_edges, side_edges):
    """
    Build Theta conservatively.

    A 3D edge (i, j) is accepted only if:
    - Every view where the two vertices project to distinct 2D vertices supports that edge.
    - At least two views provide distinct-vertex evidence.

    This prevents weak single-view edge hallucinations.
    """
    ef = {_edge_key(u, v) for u, v in front_edges}
    et = {_edge_key(u, v) for u, v in top_edges}
    es = {_edge_key(u, v) for u, v in side_edges}

    theta = []
    for i, j in combinations(range(len(lambda_rows)), 2):
        _, _, _, f1, t1, s1 = lambda_rows[i]
        _, _, _, f2, t2, s2 = lambda_rows[j]

        constraints = 0

        if f1 != f2:
            constraints += 1
            if not _supports_projected_edge(ef, int(f1), int(f2)):
                continue

        if t1 != t2:
            constraints += 1
            if not _supports_projected_edge(et, int(t1), int(t2)):
                continue

        if s1 != s2:
            constraints += 1
            if not _supports_projected_edge(es, int(s1), int(s2)):
                continue

        if constraints >= 2:
            theta.append((i, j))

    return theta


def build_pseudo_wireframe_paper(
    front_vertices: Sequence[Point2D],
    front_edges: Sequence[Edge2D],
    top_vertices: Sequence[Point2D],
    top_edges: Sequence[Edge2D],
    side_vertices: Sequence[Point2D],
    side_edges: Sequence[Edge2D],
    split_intersections: bool = True,
    tol: float = TOL,
):
    """
    Research-paper-aligned pseudo-wireframe reconstruction.

    Returns:
    - Lambda: list of [x, y, z, front_idx, top_idx, side_idx]
    - Theta: list of (u, v) over Lambda indices
    - metadata: dict with preprocessed 2D graphs
    """
    if split_intersections:
        vf, ef = split_projection_segments(front_vertices, front_edges, tol=tol)
        vt, et = split_projection_segments(top_vertices, top_edges, tol=tol)
        vs, es = split_projection_segments(side_vertices, side_edges, tol=tol)
    else:
        vf, ef = list(front_vertices), sorted({_edge_key(u, v) for u, v in front_edges})
        vt, et = list(top_vertices), sorted({_edge_key(u, v) for u, v in top_edges})
        vs, es = list(side_vertices), sorted({_edge_key(u, v) for u, v in side_edges})

    lambda_rows = _build_lambda(vf, vt, vs, tol=tol)
    theta = _build_theta(lambda_rows, ef, et, es)

    metadata = {
        "front": {"vertices": vf, "edges": ef},
        "top": {"vertices": vt, "edges": et},
        "side": {"vertices": vs, "edges": es},
    }
    return lambda_rows, theta, metadata
