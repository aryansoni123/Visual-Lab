# =========================================================
# FULL PSEUDO-WIREFRAME PIPELINE (STRICT CM/PM VERSION)
# Includes:
# 1. Segmentation
# 2. Strict CM Matrix
# 3. Strict PM Matrix
# 4. Collinearity Matrix C = CM ⊙ PM
# 5. Lambda generation
# 6. Correct Theta generation
# =========================================================

import numpy as np
from itertools import combinations

TOL = 1e-6

# =========================================================
# ================== GEOMETRIC UTILITIES ==================
# =========================================================

def point_on_segment(p, a, b):
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > TOL:
        return False
    dot = (p[0] - a[0]) * (p[0] - b[0]) + (p[1] - a[1]) * (p[1] - b[1])
    return dot <= TOL


def segment_intersection(a1, a2, b1, b2):
    def det(a, b):
        return a[0]*b[1] - a[1]*b[0]

    xdiff = (a1[0] - a2[0], b1[0] - b2[0])
    ydiff = (a1[1] - a2[1], b1[1] - b2[1])

    div = det(xdiff, ydiff)
    if abs(div) < TOL:
        return None

    d = (det(a1, a2), det(b1, b2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    p = (x, y)

    if point_on_segment(p, a1, a2) and point_on_segment(p, b1, b2):
        return p

    return None


# =========================================================
# ===================== SEGMENTATION ======================
# =========================================================

def segment_projection(vertices, edges):
    vertices = list(vertices)
    edge_points = [(vertices[e[0]], vertices[e[1]]) for e in edges]

    split_points = {i: [edge_points[i][0], edge_points[i][1]]
                    for i in range(len(edge_points))}

    for i in range(len(edge_points)):
        for j in range(i + 1, len(edge_points)):
            p = segment_intersection(edge_points[i][0], edge_points[i][1],
                                     edge_points[j][0], edge_points[j][1])
            if p:
                split_points[i].append(p)
                split_points[j].append(p)

    def add_vertex(p):
        for idx, v in enumerate(vertices):
            if np.linalg.norm(np.array(v) - np.array(p)) < TOL:
                return idx
        vertices.append(p)
        return len(vertices) - 1

    new_edges = []

    for i, pts in split_points.items():
        pts = list(set(pts))
        a = np.array(edge_points[i][0])
        pts.sort(key=lambda p: np.linalg.norm(np.array(p) - a))

        for k in range(len(pts) - 1):
            v1 = add_vertex(pts[k])
            v2 = add_vertex(pts[k + 1])
            if v1 != v2:
                new_edges.append((v1, v2))

    return vertices, new_edges


# =========================================================
# ===================== CM / PM STRICT ====================
# =========================================================

def edge_direction(vertices, edge):
    p1 = np.array(vertices[edge[0]])
    p2 = np.array(vertices[edge[1]])
    return p2 - p1


def is_parallel(v1, v2):
    cross = v1[0]*v2[1] - v1[1]*v2[0]
    return abs(cross) < TOL


def build_CM(edges):
    n = len(edges)
    CM = np.zeros((n, n), dtype=int)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if len(set(edges[i]) & set(edges[j])) > 0:
                CM[i, j] = 1
    return CM


def build_PM(vertices, edges):
    n = len(edges)
    PM = np.zeros((n, n), dtype=int)

    directions = [edge_direction(vertices, e) for e in edges]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if is_parallel(directions[i], directions[j]):
                PM[i, j] = 1
    return PM


def build_collinearity_matrix(CM, PM):
    return CM * PM


def edge_exists(edge_set, a, b):
    """Check if an edge exists in either direction."""
    return (a, b) in edge_set or (b, a) in edge_set


def augment_collinear_edges(vertices, edges):
    """
    Given 2D vertices and edges, detect and add missing collinear links.
    
    Per the paper (Sec. 3, p.3): collinearity is detected as the logical 
    product of concatenation (CM) and parallelism (PM). When two edges share
    a vertex AND are parallel, the connecting edge between their other 
    endpoints MUST be added to ensure topological consistency.
    
    Returns: (vertices, augmented_edges)
    """
    if not edges:
        return vertices, edges
    
    # Compute matrices for current edge set
    CM = build_CM(edges)
    PM = build_PM(vertices, edges)
    C = build_collinearity_matrix(CM, PM)
    
    # Track new edges to add
    new_edges_set = set(tuple(sorted(e)) for e in edges)
    n = len(edges)
    
    for i in range(n):
        for j in range(i + 1, n):
            # If C[i,j] = 1, edges i and j are concatenated AND parallel
            if C[i, j]:
                ei = edges[i]
                ej = edges[j]
                common = set(ei) & set(ej)
                
                # They should share exactly one vertex (concatenated)
                if len(common) == 1:
                    shared = common.pop()
                    # Find the two non-shared endpoints
                    other_i = ei[0] if ei[1] == shared else ei[1]
                    other_j = ej[0] if ej[1] == shared else ej[1]
                    
                    # Add edge between the non-shared endpoints
                    if other_i != other_j:
                        new_edge = tuple(sorted([other_i, other_j]))
                        new_edges_set.add(new_edge)
    
    # Convert back to original edge format (unsorted)
    augmented_edges = []
    for e_tuple in new_edges_set:
        # Preserve direction if it existed, else use sorted order
        if (e_tuple[0], e_tuple[1]) in edges or (e_tuple[1], e_tuple[0]) in edges:
            # Preserve original direction
            if (e_tuple[0], e_tuple[1]) in edges:
                augmented_edges.append((e_tuple[0], e_tuple[1]))
            else:
                augmented_edges.append((e_tuple[1], e_tuple[0]))
        else:
            # New edge, use forward order
            augmented_edges.append((e_tuple[0], e_tuple[1]))
    
    return vertices, augmented_edges


# =========================================================
# ===================== LAMBDA ============================
# =========================================================

def generate_lambda(front, top, side):
    Vf, _ = front
    Vt, _ = top
    Vs, _ = side

    Lambda = []

    top_x_map = {}
    for i, (x, z) in enumerate(Vt):
        top_x_map.setdefault(x, []).append((i, z))

    side_y_map = {}
    for i, (y, z) in enumerate(Vs):
        side_y_map.setdefault(y, []).append((i, z))

    for i_f, (x_f, y_f) in enumerate(Vf):

        if x_f not in top_x_map or y_f not in side_y_map:
            continue

        for i_t, z_t in top_x_map[x_f]:
            for i_s, z_s in side_y_map[y_f]:
                if abs(z_t - z_s) < TOL:
                    Lambda.append([
                        x_f,
                        y_f,
                        z_t,
                        i_f,
                        i_t,
                        i_s
                    ])

    return Lambda


# =========================================================
# ===================== THETA =============================
# =========================================================

def generate_theta(Lambda, front, top, side):
    Vf, Ef = front
    Vt, Et = top
    Vs, Es = side

    Ef_set = set(Ef)
    Et_set = set(Et)
    Es_set = set(Es)

    Theta = []

    for i, j in combinations(range(len(Lambda)), 2):

        x1, y1, z1, f1, t1, s1 = Lambda[i]
        x2, y2, z2, f2, t2, s2 = Lambda[j]

        valid = True

        if f1 != f2 and not edge_exists(Ef_set, f1, f2):
            valid = False

        if t1 != t2 and not edge_exists(Et_set, t1, t2):
            valid = False

        if s1 != s2 and not edge_exists(Es_set, s1, s2):
            valid = False

        if valid:
            Theta.append((i, j))

    return Theta


# =========================================================
# ===================== FULL PIPELINE =====================
# =========================================================

def build_pseudo_wireframe(front_vertices, front_edges,
                           top_vertices, top_edges,
                           side_vertices, side_edges):

    # --- Segmentation + Collinearity Augmentation ---
    Vf, Ef = segment_projection(front_vertices, front_edges)
    Vf, Ef = augment_collinear_edges(Vf, Ef)
    
    Vt, Et = segment_projection(top_vertices, top_edges)
    Vt, Et = augment_collinear_edges(Vt, Et)
    
    Vs, Es = segment_projection(side_vertices, side_edges)
    Vs, Es = augment_collinear_edges(Vs, Es)

    # --- Strict CM / PM ---
    CM_f = build_CM(Ef)
    PM_f = build_PM(Vf, Ef)
    C_f = build_collinearity_matrix(CM_f, PM_f)

    CM_t = build_CM(Et)
    PM_t = build_PM(Vt, Et)
    C_t = build_collinearity_matrix(CM_t, PM_t)

    CM_s = build_CM(Es)
    PM_s = build_PM(Vs, Es)
    C_s = build_collinearity_matrix(CM_s, PM_s)

    front = (Vf, Ef)
    top = (Vt, Et)
    side = (Vs, Es)

    Lambda = generate_lambda(front, top, side)
    Theta = generate_theta(Lambda, front, top, side)

    return Lambda, Theta, (C_f, C_t, C_s)


# =========================================================
# ===================== TESTS =========================
# =========================================================

print("=" * 70)
print("TEST 1: Segmentation with crossing edges")
print("=" * 70)
seg_vertices = [(0,0),(2,0),(1,-1),(1,1)]
seg_edges = [(0,1),(2,3)]
print("Input vertices:", seg_vertices)
print("Input edges:", seg_edges)
seg_v, seg_e = segment_projection(seg_vertices, seg_edges)
print("After segmentation:")
print("  Vertices:", seg_v)
print("  Edges:", seg_e)
print("  Expected: intersection at (1,0) splits both edges")
print()

print("=" * 70)
print("TEST 2: Collinearity - two edges sharing vertex and parallel")
print("=" * 70)
col_vertices = [(0,0),(1,0),(2,0)]
col_edges = [(0,1),(1,2)]
print("Input vertices:", col_vertices)
print("Input edges:", col_edges)

CM = build_CM(col_edges)
PM = build_PM(col_vertices, col_edges)
C = build_collinearity_matrix(CM, PM)
print("CM (concatenation):\n", CM)
print("PM (parallelism):\n", PM)
print("C = CM * PM (collinearity):\n", C)
print("  Expected: C[0,1]=1 (edges share vertex 1 AND are parallel)")

col_vertices_aug, col_edges_aug = augment_collinear_edges(col_vertices, col_edges)
print("After augmentation:")
print("  Vertices:", col_vertices_aug)
print("  Edges:", col_edges_aug)
print("  Expected: edge (0,2) added to complete the chain")
print()

print("=" * 70)
print("TEST 3: Complex collinearity - three collinear edges")
print("=" * 70)
col3_vertices = [(0,0),(1,0),(2,0),(3,0)]
col3_edges = [(0,1),(1,2),(2,3)]
print("Input vertices:", col3_vertices)
print("Input edges:", col3_edges)

CM3 = build_CM(col3_edges)
C3 = build_collinearity_matrix(CM3, build_PM(col3_vertices, col3_edges))
print("Collinearity matrix C:\n", C3)

col3_vertices_aug, col3_edges_aug = augment_collinear_edges(col3_vertices, col3_edges)
print("After augmentation:")
print("  Edges:", col3_edges_aug)
print("  Expected: edges (0,2) and (0,3) and (1,3) added")
print()

print("=" * 70)
print("TEST 4: Cube reconstruction (full pipeline)")
print("=" * 70)

front_vertices = [(0,0),(4,0),(4,3),(0,3)]
front_edges = [(0,1),(1,2),(2,3),(3,0)]

top_vertices = [(0,0),(4,0),(4,2),(0,2)]
top_edges = [(0,1),(1,2),(2,3),(3,0)]

side_vertices = [(0,0),(3,0),(3,2),(0,2)]
side_edges = [(0,1),(1,2),(2,3),(3,0)]

Lambda, Theta, C_matrices = build_pseudo_wireframe(
    front_vertices, front_edges,
    top_vertices, top_edges,
    side_vertices, side_edges
)

print("Lambda (3D Vertices):")
for i, row in enumerate(Lambda):
    print("  %d: (x=%.1f, y=%.1f, z=%.1f) from front[%d], top[%d], side[%d]" % 
          (i, row[0], row[1], row[2], row[3], row[4], row[5]))

print("\nTotal Vertices:", len(Lambda), " (expected: 8 for cube)")

print("\nTheta (3D Edges):")
for e in Theta:
    print("  %d---%d" % e)

print("\nTotal Edges:", len(Theta), " (expected: 12 for cube)")
print()