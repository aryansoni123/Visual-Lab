"""Quick regression for paper-aligned pseudo-wireframe reconstruction."""

from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper


def main():
    # Unit cube orthographic projections
    front_vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]
    front_edges = [(0, 1), (1, 2), (2, 3), (3, 0)]

    top_vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]
    top_edges = [(0, 1), (1, 2), (2, 3), (3, 0)]

    side_vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]
    side_edges = [(0, 1), (1, 2), (2, 3), (3, 0)]

    Lambda, Theta, _ = build_pseudo_wireframe_paper(
        front_vertices,
        front_edges,
        top_vertices,
        top_edges,
        side_vertices,
        side_edges,
        split_intersections=False,
    )

    print(f"Lambda: {len(Lambda)}")
    print(f"Theta: {len(Theta)}")

    # Expected for cube projections
    assert len(Lambda) == 8, f"Expected 8 Lambda vertices, got {len(Lambda)}"
    assert len(Theta) == 12, f"Expected 12 Theta edges, got {len(Theta)}"

    print("PASS: pseudo-wireframe paper reconstruction")


if __name__ == "__main__":
    main()
