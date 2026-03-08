import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Lambda: 3D Vertex Coordinates
Lambda = [
    [0, 0, 0], [6, 0, 0], [6, 4, 0], [0, 4, 0],       # 0-3
    [0, 0, 8], [6, 0, 8], [6, 4, 8], [0, 4, 8],       # 4-7
    [-3, 0, 8], [-3, 4, 8], [-3, 0, 5], [-3, 4, 5],   # 8-11
    [0, 0, 5], [0, 4, 5], [0, 0, 4], [0, 4, 4]        # 12-15
]

# Theta: Edge Connectivity (pairs of indices)
Theta = [
    (0,1),(1,2),(2,3),(3,0), (4,5),(5,6),(6,7),(7,4), # Blocks
    (0,4),(1,5),(2,6),(3,7), (4,0), (3,2), (5,1),     # Verticals
    (8,9),(9,7),(7,4),(4,8), (8,10),(9,11),           # Extension
    (10,12),(11,13), (12,4),(13,7), (11,9),           # Steps
    (12,14),(13,15), (12,13), (14,15),                # Ledge
    (14,0),(15,3), (10,11)                            # Base connections
]

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot vertices
for i, (x, y, z) in enumerate(Lambda):
    ax.scatter(x, y, z, color='blue')
    ax.text(x, y, z, f'{i}', size=10, zorder=1)

# Plot edges
for edge in Theta:
    v1, v2 = Lambda[edge[0]], Lambda[edge[1]]
    ax.plot([v1[0], v2[0]], [v1[1], v2[1]], [v1[2], v2[2]], color='gray')

ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.set_zlabel('Z axis')
ax.set_title('3D Pseudo-Wireframe Reconstruction')
plt.show()