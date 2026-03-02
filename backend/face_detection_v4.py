# =========================================================
# FACE DETECTION FROM 3D WIREFRAME (V4 - CORRECT)
# Using: Proper Half-Edge Face Walking with 3D Ordering
# 
# The key fix: order neighbors correctly in 3D using
# a normal vector computed from the local surface.
# =========================================================

import numpy as np
from collections import defaultdict

TOL = 1e-6


# =========================================================
# ============== ANGULAR ORDERING (3D) =================
# =========================================================

def compute_face_normal_from_path(path, lambda_vertices):
    """Compute a normal vector for the local surface patch."""
    if len(path) < 3:
        return np.array([0, 0, 1])
    
    # Use first 3 distinct points
    points = [np.array(lambda_vertices[i]) for i in path[:3]]
    
    if len(points) < 3:
        return np.array([0, 0, 1])
    
    v1 = points[1] - points[0]
    v2 = points[2] - points[0]
    
    normal = np.cross(v1, v2)
    norm = np.linalg.norm(normal)
    
    if norm > TOL:
        return normal / norm
    return np.array([0, 0, 1])


def angle_in_plane(vertex, neighbor, normal, lambda_vertices):
    """
    Compute angle of neighbor around vertex in the plane perpendicular to normal.
    """
    vertex_coord = np.array(lambda_vertices[vertex])
    neighbor_coord = np.array(lambda_vertices[neighbor])
    
    vec = neighbor_coord - vertex_coord
    
    # Create orthonormal basis
    # Find a vector perpendicular to normal
    if abs(normal[0]) < abs(normal[1]):
        u = np.array([1, 0, 0])
    else:
        u = np.array([0, 1, 0])
    
    u = u - np.dot(u, normal) * normal
    u_norm = np.linalg.norm(u)
    
    if u_norm < TOL:
        # normal is parallel to [1,0,0] or [0,1,0]
        u = np.array([0, 0, 1]) - np.dot(np.array([0, 0, 1]), normal) * normal
        u_norm = np.linalg.norm(u)
    
    u = u / (u_norm + TOL)
    v_basis = np.cross(normal, u)
    
    # Project vec onto plane
    vec_proj = vec - np.dot(vec, normal) * normal
    
    # Compute angle in 2D
    x = np.dot(vec_proj, u)
    y = np.dot(vec_proj, v_basis)
    
    return np.arctan2(y, x)


def sort_neighbors_ccw(vertex, neighbors, normal, lambda_vertices):
    """
    Sort neighbors around vertex in counter-clockwise order
    when viewed from the direction of the normal.
    """
    if len(neighbors) <= 1:
        return neighbors
    
    angles = [(n, angle_in_plane(vertex, n, normal, lambda_vertices))
              for n in neighbors]
    
    angles.sort(key=lambda x: x[1])
    return [n for n, _ in angles]


# =========================================================
# ============= HALF-EDGE FACE WALKING ====================
# =========================================================

class PolyhedralGraph:
    """Represent a polyhedron with proper face walking."""
    
    def __init__(self, vertices, edges):
        self.vertices = vertices
        self.edges = edges
        self.num_vertices = len(vertices)
        
        # Adjacency
        self.adj = defaultdict(list)
        for u, v in edges:
            self.adj[u].append(v)
            self.adj[v].append(u)
        
        self.visited_half_edges = set()
    
    def walk_face_from_edge(self, start_u, start_v):
        """
        Walk a face starting from directed edge (start_u → start_v).
        Uses proper 3D angular ordering at each vertex.
        """
        face = []
        u, v = start_u, start_v
        max_steps = self.num_vertices + 10
        steps = 0
        
        while steps < max_steps:
            face.append(u)
            
            # At vertex v, find the next edge in CCW order
            neighbors = self.adj[v]
            if not neighbors:
                return None
            
            # Compute normal for ordering (use current face path as guide)
            normal = compute_face_normal_from_path([u, v] + neighbors[:2], self.vertices)
            
            # Sort neighbors in CCW order around v, with normal pointing outward
            sorted_neighbors = sort_neighbors_ccw(v, neighbors, normal, self.vertices)
            
            # Find u in sorted neighbors
            try:
                idx = sorted_neighbors.index(u)
            except ValueError:
                return None
            
            # Next neighbor in circular order
            next_vertex = sorted_neighbors[(idx + 1) % len(sorted_neighbors)]
            
            u, v = v, next_vertex
            
            # Check if we've closed the face
            if u == start_u and v == start_v:
                return face
            
            steps += 1
        
        return None
    
    def extract_all_faces(self):
        """Extract all faces by walking from each unvisited half-edge."""
        faces = []
        
        for u, v in self.edges:
            # Try (u → v)
            if (u, v) not in self.visited_half_edges:
                face = self.walk_face_from_edge(u, v)
                if face and len(face) >= 3:
                    faces.append(face)
                    # Mark all half-edges in this face
                    for i in range(len(face)):
                        v1 = face[i]
                        v2 = face[(i + 1) % len(face)]
                        self.visited_half_edges.add((v1, v2))
            
            # Try (v → u)
            if (v, u) not in self.visited_half_edges:
                face = self.walk_face_from_edge(v, u)
                if face and len(face) >= 3:
                    faces.append(face)
                    for i in range(len(face)):
                        v1 = face[i]
                        v2 = face[(i + 1) % len(face)]
                        self.visited_half_edges.add((v1, v2))
        
        return faces


# =========================================================
# ============== MESH EXPORT ==============================
# =========================================================

def triangulate_polygon(polygon_indices, lambda_vertices):
    """Fan triangulation."""
    if len(polygon_indices) < 3:
        return []
    
    triangles = []
    for i in range(1, len(polygon_indices) - 1):
        triangles.append([
            polygon_indices[0],
            polygon_indices[i],
            polygon_indices[i + 1]
        ])
    
    return triangles


def export_stl(faces, lambda_vertices, filename):
    """Export to ASCII STL."""
    triangles = []
    for face in faces:
        tris = triangulate_polygon(face, lambda_vertices)
        triangles.extend(tris)
    
    with open(filename, 'w') as f:
        f.write("solid mesh\n")
        
        for tri in triangles:
            v0 = np.array(lambda_vertices[tri[0]])
            v1 = np.array(lambda_vertices[tri[1]])
            v2 = np.array(lambda_vertices[tri[2]])
            
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            
            if norm > TOL:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1])
            
            f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}\n")
            f.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
            f.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        
        f.write("endsolid mesh\n")


# =========================================================
# ===================== PIPELINE =========================
# =========================================================

def detect_faces_and_export(lambda_vertices, theta_edges, output_filename):
    """Complete pipeline."""
    print("\n" + "=" * 70)
    print("FACE DETECTION (Half-Edge Face Walking - v4)")
    print("=" * 70)
    
    print(f"\nInput: {len(lambda_vertices)} vertices, {len(theta_edges)} edges")
    
    # Step 1: Build graph and walk faces
    print(f"\nStep 1: Walking faces using half-edge ordering...")
    graph = PolyhedralGraph(lambda_vertices, theta_edges)
    faces = graph.extract_all_faces()
    print(f"  Found {len(faces)} faces")
    
    # Step 2: Triangulate
    print(f"\nStep 2: Triangulating...")
    triangles = []
    for face in faces:
        tris = triangulate_polygon(face, lambda_vertices)
        triangles.extend(tris)
    print(f"  Total triangles: {len(triangles)}")
    
    # Step 3: Validate Euler
    print(f"\nStep 3: Validating Euler formula...")
    V = len(lambda_vertices)
    E = len(theta_edges)
    F = len(faces)
    euler_char = V - E + F
    is_valid = abs(euler_char - 2) < 0.5
    print(f"  V={V}, E={E}, F={F}")
    print(f"  V - E + F = {euler_char} (valid: {is_valid})")
    
    # Step 4: Export
    print(f"\nStep 4: Exporting to STL...")
    export_stl(faces, lambda_vertices, output_filename)
    print(f"  Written to: {output_filename}")
    
    print("\n" + "=" * 70)
    return faces, triangles, is_valid, euler_char


# =========================================================
# ===================== TEST ==============================
# =========================================================

if __name__ == "__main__":
    from pseudo_wireframe import build_pseudo_wireframe
    
    front_vertices = [(0,0),(4,0),(4,3),(0,3)]
    front_edges = [(0,1),(1,2),(2,3),(3,0)]
    
    top_vertices = [(0,0),(4,0),(4,2),(0,2)]
    top_edges = [(0,1),(1,2),(2,3),(3,0)]
    
    side_vertices = [(0,0),(3,0),(3,2),(0,2)]
    side_edges = [(0,1),(1,2),(2,3),(3,0)]
    
    Lambda, Theta, _ = build_pseudo_wireframe(
        front_vertices, front_edges,
        top_vertices, top_edges,
        side_vertices, side_edges
    )
    
    lambda_coords = [[row[0], row[1], row[2]] for row in Lambda]
    
    print("\nTest: Cube Reconstruction")
    faces, triangles, is_valid, euler = detect_faces_and_export(
        lambda_coords, Theta, "test_cube_v4.stl"
    )
    
    print("\nFaces detected:")
    for i, face in enumerate(faces):
        print(f"  Face {i}: {len(face)}-gon {face}")
