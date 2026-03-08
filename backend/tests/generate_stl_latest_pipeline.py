"""Generate STL using latest pseudo-wireframe + largest-face-first face detection."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import defaultdict
from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper
from algorithms.face_detection import (
    find_all_faces_by_planes,
    triangulate_polygon,
    ensure_outward_normals,
    export_stl,
)


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
    # Reference geometry (user-provided wireframe)
    Lambda_ref = [
        [0, 0, 0, 0, 0, 0], [6, 0, 0, 0, 0, 0], [6, 4, 0, 0, 0, 0], [0, 4, 0, 0, 0, 0],
        [0, 0, 8, 0, 0, 0], [6, 0, 8, 0, 0, 0], [6, 4, 8, 0, 0, 0], [0, 4, 8, 0, 0, 0],
        [-3, 0, 8, 0, 0, 0], [-3, 4, 8, 0, 0, 0], [-3, 0, 5, 0, 0, 0], [-3, 4, 5, 0, 0, 0],
        [0, 0, 5, 0, 0, 0], [0, 4, 5, 0, 0, 0], [0, 0, 4, 0, 0, 0], [0, 4, 4, 0, 0, 0],
    ]

    Theta_ref = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
        (4, 0), (3, 2), (5, 1),
        (8, 9), (9, 7), (7, 4), (4, 8),
        (8, 10), (9, 11), (10, 12), (11, 13),
        (12, 4), (13, 7),
        (11, 9),
        (12, 14), (13, 15),
        (12, 13),
        (14, 15),
        (14, 0), (15, 3),
        (10, 11),
    ]

    # Generate 2D orthographic graphs from the reference geometry.
    front_vertices, front_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 1))
    top_vertices, top_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 2))
    side_vertices, side_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(1, 2))

    Lambda, Theta, _ = build_pseudo_wireframe_paper(
        front_vertices,
        front_edges,
        top_vertices,
        top_edges,
        side_vertices,
        side_edges,
        split_intersections=False,
    )

    faces = find_all_faces_by_planes(Lambda, Theta)

    triangles = []
    for face in faces:
        triangles.extend(triangulate_polygon(face, Lambda))
    triangles = ensure_outward_normals(triangles, Lambda)

    out_path = Path(__file__).resolve().parents[1] / "outputs" / "latest_pseudo_largest_face_first.stl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(str(out_path), triangles, Lambda)

    print(f"Lambda: {len(Lambda)}")
    print(f"Theta: {len(Theta)}")
    print(f"Faces: {len(faces)}")
    print(f"Triangles: {len(triangles)}")
    print(f"STL: {out_path}")


if __name__ == "__main__":
    main()
