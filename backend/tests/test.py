# I propose when the concentri faces overlap we add 1, eg for 4 faces concentric and overlapping we add 3 to the face count hence keeping the euler formula valid. what do you say? and why is dataset 1 while 4 fails?
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# ===============================
# DATASETS
# ===============================

# Dataset 1
Lambda1 = [
[0,0,0], [6,0,0], [6,4,0], [0,4,0],
[0,0,6], [6,0,6], [6,4,6], [0,4,6],
[2,0,6], [4,0,6], [4,4,6], [2,4,6],
[2,0,9], [4,0,9], [4,4,9], [2,4,9]
]

Theta1 = [
(0,1),(1,2),(2,3),(3,0),
(4,5),(5,6),(6,7),(7,4),
(0,4),(1,5),(2,6),(3,7),
(8,9),(9,10),(10,11),(11,8),
(12,13),(13,14),(14,15),(15,12),
(8,12),(9,13),(10,14),(11,15),
(8,4),(9,5),(10,6),(11,7)
]


# Dataset 2
Lambda2 = [
[0,0,0],[6,0,0],[6,2,0],[2,2,0],[2,6,0],[0,6,0],
[0,0,6],[6,0,6],[6,2,6],[2,2,6],[2,6,6],[0,6,6]
]

Theta2 = [
(0,1),(1,2),(2,3),(3,4),(4,5),(5,0),
(6,7),(7,8),(8,9),(9,10),(10,11),(11,6),
(0,6),(1,7),(2,8),(3,9),(4,10),(5,11)
]


# Dataset 3
Lambda3 = [
[0,0,0],[8,0,0],[8,8,0],[0,8,0],
[0,0,6],[8,0,6],[8,8,6],[0,8,6],
[3,3,0],[5,3,0],[5,5,0],[3,5,0],
[3,3,6],[5,3,6],[5,5,6],[3,5,6]
]

Theta3 = [
(0,1),(1,2),(2,3),(3,0),
(4,5),(5,6),(6,7),(7,4),
(0,4),(1,5),(2,6),(3,7),
(8,9),(9,10),(10,11),(11,8),
(12,13),(13,14),(14,15),(15,12),
(8,12),(9,13),(10,14),(11,15)
]


# Dataset 4
Lambda4 = [
[0,0,0],[8,0,0],[8,4,0],[0,4,0],
[0,0,6],[8,0,6],[8,4,6],[0,4,6],
[2,0,6],[6,0,6],[6,4,6],[2,4,6],
[2,0,9],[6,0,9],[6,4,9],[2,4,9],
[3,0,9],[5,0,9],[5,4,9],[3,4,9],
[3,0,12],[5,0,12],[5,4,12],[3,4,12]
]

Theta4 = [
(0,1),(1,2),(2,3),(3,0),
(4,5),(5,6),(6,7),(7,4),
(0,4),(1,5),(2,6),(3,7),
(8,9),(9,10),(10,11),(11,8),
(12,13),(13,14),(14,15),(15,12),
(8,12),(9,13),(10,14),(11,15),
(16,17),(17,18),(18,19),(19,16),
(20,21),(21,22),(22,23),(23,20),
(16,20),(17,21),(18,22),(19,23)
]


datasets = [
("Dataset 1: Stepped Block", Lambda1, Theta1),
("Dataset 2: L-Shape", Lambda2, Theta2),
("Dataset 3: Frame Hole", Lambda3, Theta3),
("Dataset 4: Double Step", Lambda4, Theta4)
]


# ===============================
# VISUALIZATION FUNCTION
# ===============================

def visualize(lambda_pts, theta_edges, title):

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    xs = [p[0] for p in lambda_pts]
    ys = [p[1] for p in lambda_pts]
    zs = [p[2] for p in lambda_pts]

    ax.scatter(xs, ys, zs, color='red', s=40)

    for i, p in enumerate(lambda_pts):
        ax.text(p[0], p[1], p[2], str(i))

    for e in theta_edges:
        p1 = lambda_pts[e[0]]
        p2 = lambda_pts[e[1]]

        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            [p1[2], p2[2]],
            color='black'
        )

    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    plt.show()


# ===============================
# RUN VISUALIZATION
# ===============================

for name, L, T in datasets:
    visualize(L, T, name)