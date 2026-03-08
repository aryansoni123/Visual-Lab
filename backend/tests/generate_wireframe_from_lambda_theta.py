"""Generate and visualize a 3D wireframe from explicit Lambda and Theta."""

from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


def main():
    Lambda = [
        # Bottom main block
        [0, 0, 0, 0, 0, 0],   # 0
        [6, 0, 0, 0, 0, 0],   # 1
        [6, 4, 0, 0, 0, 0],   # 2
        [0, 4, 0, 0, 0, 0],   # 3

        # Top main block
        [0, 0, 8, 0, 0, 0],   # 4
        [6, 0, 8, 0, 0, 0],   # 5
        [6, 4, 8, 0, 0, 0],   # 6
        [0, 4, 8, 0, 0, 0],   # 7

        # Left extension (top level)
        [-3, 0, 8, 0, 0, 0],  # 8
        [-3, 4, 8, 0, 0, 0],  # 9
        [-3, 0, 5, 0, 0, 0],  # 10
        [-3, 4, 5, 0, 0, 0],  # 11

        [0, 0, 5, 0, 0, 0],   # 12
        [0, 4, 5, 0, 0, 0],   # 13

        # Lower vertical drop
        [0, 0, 4, 0, 0, 0],   # 14
        [0, 4, 4, 0, 0, 0],   # 15
    ]

    Theta = [
        # Main block bottom rectangle
        (0, 1), (1, 2), (2, 3), (3, 0),

        # Main block top rectangle
        (4, 5), (5, 6), (6, 7), (7, 4),

        # Main block vertical edges
        (0, 4), (1, 5), (2, 6), (3, 7),

        # Main block front face (y=0): (0,1,5,4)
        (4, 0),

        # Main block back face (y=4): (3,2,6,7)
        (3, 2),

        # Main block right face (x=6): (1,2,6,5)
        (5, 1),

        # Left extension top face (z=8): (8,9,7,4)
        (8, 9), (9, 7), (7, 4), (4, 8),

        # Left extension vertical edges
        (8, 10), (9, 11), (10, 12), (11, 13),

        # Left extension inner step faces
        (12, 4), (13, 7),

        # Left extension back face (x=-3): (8,10,11,9)
        (11, 9),

        # Lower ledge horizontal edges
        (12, 14), (13, 15),

        # Lower ledge inner edge
        (12, 13),

        # Lower ledge bottom edge
        (14, 15),

        # Lower drop vertical edges
        (14, 0), (15, 3),

        # Left extension depth edge
        (10, 11),
    ]

    vertices = [row[:3] for row in Lambda]

    # Basic validation
    max_idx = len(vertices) - 1
    invalid_edges = [(u, v) for u, v in Theta if u < 0 or v < 0 or u > max_idx or v > max_idx]
    if invalid_edges:
        raise ValueError(f"Found invalid edges: {invalid_edges}")

    degree = Counter()
    for u, v in Theta:
        degree[u] += 1
        degree[v] += 1

    print(f"Vertices: {len(vertices)}")
    print(f"Edges: {len(Theta)}")
    print(f"Min degree: {min(degree.values())}, Max degree: {max(degree.values())}")

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Plot vertices and labels
    for i, (x, y, z) in enumerate(vertices):
        ax.scatter(x, y, z, c="royalblue", s=28)
        ax.text(x, y, z, str(i), fontsize=8)

    # Plot edges
    for u, v in Theta:
        x1, y1, z1 = vertices[u]
        x2, y2, z2 = vertices[v]
        ax.plot([x1, x2], [y1, y2], [z1, z2], c="gray", linewidth=1.5)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Wireframe from Given Lambda + Theta")

    # Keep aspect visually consistent
    xs = [p[0] for p in vertices]
    ys = [p[1] for p in vertices]
    zs = [p[2] for p in vertices]
    ax.set_box_aspect((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))

    out_path = Path(__file__).resolve().parents[1] / "outputs" / "wireframe_lambda_theta.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
