"""Solution 2: Robust polygon triangulation using ear clipping instead of simple fan."""

from collections import defaultdict
from pathlib import Path
import numpy as np

from reconstruction.pseudo_wireframe_paper import build_pseudo_wireframe_paper
from algorithms.face_detection import find_all_faces_by_planes

TOL = 1e-6


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


def compute_plane_equation(p1, p2, p3):
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    normal = np.cross(v1, v2)
    if np.linalg.norm(normal) < TOL:
        return None, None, False
    normal = normal / np.linalg.norm(normal)
    d = np.dot(normal, p1)
    return normal, d, True


def project_polygon_to_2d(face, Lambda):
    """Project 3D polygon onto its best-fit plane for robust 2D triangulation."""
    if len(face) < 3:
        return None, None, None
    
    # Get plane normal
    p1 = np.array(Lambda[face[0]][:3])
    p2 = np.array(Lambda[face[1]][:3])
    p3 = np.array(Lambda[face[2]][:3])
    normal, d, valid = compute_plane_equation(p1, p2, p3)
    
    if not valid:
        return None, None, None
    
    # Choose basis vectors for 2D projection
    # u: arbitrary perpendicular to normal
    if abs(normal[0]) < abs(normal[1]):
        u = np.array([1, 0, 0])
    else:
        u = np.array([0, 1, 0])
    
    u = u - np.dot(u, normal) * normal
    u = u / np.linalg.norm(u)
    v = np.cross(normal, u)
    
    # Project all points to 2D
    points_2d = []
    for idx in face:
        p = np.array(Lambda[idx][:3])
        x = np.dot(p, u)
        y = np.dot(p, v)
        points_2d.append((x, y))
    
    return points_2d, normal, d


def is_ear(polygon, i, n):
    """Check if vertex i is an ear (can be clipped)."""
    prev_i = (i - 1) % n
    next_i = (i + 1) % n
    
    p_prev = polygon[prev_i]
    p_curr = polygon[i]
    p_next = polygon[next_i]
    
    # Check if triangle is oriented correctly (CCW)
    cross = (p_curr[0] - p_prev[0]) * (p_next[1] - p_prev[1]) - \
            (p_curr[1] - p_prev[1]) * (p_next[0] - p_prev[0])
    
    if cross <= 0:  # Reflex or degenerate
        return False
    
    # Check if any other vertex is inside this triangle
    for j in range(n):
        if j in (prev_i, i, next_i):
            continue
        p = polygon[j]
        if point_in_triangle_2d(p, p_prev, p_curr, p_next):
            return False
    
    return True


def point_in_triangle_2d(p, a, b, c):
    """Check if point p is inside triangle abc in 2D."""
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    
    d1 = sign(p, a, b)
    d2 = sign(p, b, c)
    d3 = sign(p, c, a)
    
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    
    return not (has_neg and has_pos)


def triangulate_polygon_ear_clipping(face, Lambda):
    """Triangulate polygon using ear clipping algorithm."""
    if len(face) < 3:
        return []
    if len(face) == 3:
        return [tuple(face)]
    
    # Project to 2D
    points_2d, normal, d = project_polygon_to_2d(face, Lambda)
    if points_2d is None:
        # Fallback to fan triangulation
        triangles = []
        for i in range(1, len(face) - 1):
            triangles.append((face[0], face[i], face[i + 1]))
        return triangles
    
    # Ear clipping
    triangles = []
    remaining = list(range(len(face)))
    polygon_2d = points_2d[:]
    
    max_iterations = len(face) * 2
    iteration = 0
    
    while len(remaining) > 3 and iteration < max_iterations:
        iteration += 1
        n = len(remaining)
        ear_found = False
        
        for i in range(n):
            if is_ear(polygon_2d, i, n):
                # Clip this ear
                prev_i = (i - 1) % n
                next_i = (i + 1) % n
                
                tri = (face[remaining[prev_i]], face[remaining[i]], face[remaining[next_i]])
                triangles.append(tri)
                
                # Remove ear vertex
                remaining.pop(i)
                polygon_2d.pop(i)
                ear_found = True
                break
        
        if not ear_found:
            # Fallback: just triangulate remaining polygon with fan
            for i in range(1, len(remaining) - 1):
                triangles.append((face[remaining[0]], face[remaining[i]], face[remaining[i + 1]]))
            break
    
    # Add final triangle
    if len(remaining) == 3:
        triangles.append((face[remaining[0]], face[remaining[1]], face[remaining[2]]))
    
    return triangles


def compute_face_normal(triangle, Lambda):
    i, j, k = triangle
    p0 = np.array(Lambda[i][:3])
    p1 = np.array(Lambda[j][:3])
    p2 = np.array(Lambda[k][:3])
    v1 = p1 - p0
    v2 = p2 - p0
    normal = np.cross(v1, v2)
    norm = np.linalg.norm(normal)
    if norm < TOL:
        return np.array([0, 0, 1])
    return normal / norm


def ensure_outward_normals(triangles, Lambda):
    points = np.array([v[:3] for v in Lambda])
    centroid = points.mean(axis=0)
    corrected = []
    for tri in triangles:
        i, j, k = tri
        p0 = np.array(Lambda[i][:3])
        p1 = np.array(Lambda[j][:3])
        p2 = np.array(Lambda[k][:3])
        tri_center = (p0 + p1 + p2) / 3
        to_tri = tri_center - centroid
        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)
        dot_product = np.dot(normal, to_tri)
        if dot_product < 0:
            corrected.append((i, k, j))
        else:
            corrected.append(tri)
    return corrected


def export_stl(filename, triangles, Lambda):
    with open(filename, 'w') as f:
        f.write(f"solid object\n")
        for triangle in triangles:
            normal = compute_face_normal(triangle, Lambda)
            f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
            f.write(f"    outer loop\n")
            for vertex_idx in triangle:
                x, y, z = Lambda[vertex_idx][:3]
                f.write(f"      vertex {x} {y} {z}\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        f.write(f"endsolid object\n")


def main():
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
    
    print("\n[Solution 2: Robust Ear-Clipping Triangulation]")
    
    front_vertices, front_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 1))
    top_vertices, top_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(0, 2))
    side_vertices, side_edges = build_projection_graph(Lambda_ref, Theta_ref, axes=(1, 2))
    
    Lambda, Theta, _ = build_pseudo_wireframe_paper(
        front_vertices, front_edges, top_vertices, top_edges,
        side_vertices, side_edges, split_intersections=False,
    )
    
    faces = find_all_faces_by_planes(Lambda, Theta)
    
    triangles = []
    for face in faces:
        triangles.extend(triangulate_polygon_ear_clipping(face, Lambda))
    triangles = ensure_outward_normals(triangles, Lambda)
    
    out_path = Path(__file__).resolve().parents[1] / "outputs" / "solution2_robust_triangulation.stl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(str(out_path), triangles, Lambda)
    
    print(f"\nLambda: {len(Lambda)}")
    print(f"Theta: {len(Theta)}")
    print(f"Faces: {len(faces)}")
    print(f"Triangles: {len(triangles)}")
    print(f"STL: {out_path}")


if __name__ == "__main__":
    main()
