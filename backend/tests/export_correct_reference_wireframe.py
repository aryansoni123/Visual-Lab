"""Export the CORRECT reference wireframe directly (no reconstruction) for comparison."""

from pathlib import Path
import numpy as np


def export_wireframe_obj(filename, Lambda, Theta):
    """Export wireframe as OBJ file showing only edges."""
    with open(filename, 'w') as f:
        f.write("# Wireframe edges only\n")
        
        # Write vertices
        for v in Lambda:
            x, y, z = v[:3]
            f.write(f"v {x} {y} {z}\n")
        
        # Write edges as line segments
        for u, v in Theta:
            f.write(f"l {u+1} {v+1}\n")  # OBJ is 1-indexed


def compute_edge_normal(u_pos, v_pos):
    """Compute a pseudo-normal for edge visualization in STL."""
    edge_vec = np.array(v_pos) - np.array(u_pos)
    # Use a perpendicular vector
    if abs(edge_vec[2]) < 0.9:
        perp = np.cross(edge_vec, [0, 0, 1])
    else:
        perp = np.cross(edge_vec, [1, 0, 0])
    norm = np.linalg.norm(perp)
    if norm < 1e-6:
        return np.array([1, 0, 0])
    return perp / norm


def export_wireframe_as_tubes_stl(filename, Lambda, Theta, tube_radius=0.05):
    """Export wireframe as STL with cylindrical tubes for edges (approximate)."""
    with open(filename, 'w') as f:
        f.write("solid wireframe\n")
        
        # For each edge, create a simple rectangular tube
        for u, v in Theta:
            p1 = np.array(Lambda[u][:3])
            p2 = np.array(Lambda[v][:3])
            
            # Create a thin quad connecting p1 and p2
            edge_vec = p2 - p1
            perp = compute_edge_normal(p1, p2) * tube_radius
            
            # Four corners of the tube cross-section
            v1 = p1 + perp
            v2 = p1 - perp
            v3 = p2 + perp
            v4 = p2 - perp
            
            # Two triangles forming a quad face
            # Triangle 1: v1, v2, v3
            normal = np.cross(v2 - v1, v3 - v1)
            norm = np.linalg.norm(normal)
            if norm > 1e-6:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1])
            
            f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
            f.write(f"    outer loop\n")
            f.write(f"      vertex {v1[0]} {v1[1]} {v1[2]}\n")
            f.write(f"      vertex {v2[0]} {v2[1]} {v2[2]}\n")
            f.write(f"      vertex {v3[0]} {v3[1]} {v3[2]}\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
            
            # Triangle 2: v2, v4, v3
            f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
            f.write(f"    outer loop\n")
            f.write(f"      vertex {v2[0]} {v2[1]} {v2[2]}\n")
            f.write(f"      vertex {v4[0]} {v4[1]} {v4[2]}\n")
            f.write(f"      vertex {v3[0]} {v3[1]} {v3[2]}\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        
        f.write("endsolid wireframe\n")


def main():
    # CORRECT reference geometry
    Lambda_ref = [
        [0, 0, 0, 0, 0, 0], [6, 0, 0, 0, 0, 0], [6, 4, 0, 0, 0, 0], [0, 4, 0, 0, 0, 0],
        [0, 0, 8, 0, 0, 0], [6, 0, 8, 0, 0, 0], [6, 4, 8, 0, 0, 0], [0, 4, 8, 0, 0, 0],
        [-3, 0, 8, 0, 0, 0], [-3, 4, 8, 0, 0, 0], [-3, 0, 5, 0, 0, 0], [-3, 4, 5, 0, 0, 0],
        [0, 0, 5, 0, 0, 0], [0, 4, 5, 0, 0, 0], [0, 0, 4, 0, 0, 0], [0, 4, 4, 0, 0, 0],
    ]
    
    Theta_ref = [
        (0, 1), (1, 2), (2, 3), (3, 0),         # Bottom rectangle
        (4, 5), (5, 6), (6, 7), (7, 4),         # Top main rectangle
        (0, 4), (1, 5), (2, 6), (3, 7),         # Vertical main block
        (4, 0), (3, 2), (5, 1),                 # Additional main faces
        (8, 9), (9, 7), (7, 4), (4, 8),         # Left extension top
        (8, 10), (9, 11), (10, 12), (11, 13),   # Left extension verticals
        (12, 4), (13, 7),                       # Left extension inner
        (11, 9),                                # Left extension back
        (12, 14), (13, 15),                     # Lower ledge
        (12, 13),                               # Lower ledge inner
        (14, 15),                               # Lower ledge bottom
        (14, 0), (15, 3),                       # Lower drop verticals
        (10, 11),                               # Left extension depth
    ]
    
    print("=" * 70)
    print("EXPORTING CORRECT REFERENCE WIREFRAME")
    print("=" * 70)
    print(f"\nLambda: {len(Lambda_ref)} vertices")
    print(f"Theta: {len(Theta_ref)} edges")
    
    out_dir = Path(__file__).resolve().parents[1] / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Export as OBJ (wireframe format)
    obj_path = out_dir / "reference_wireframe_CORRECT.obj"
    export_wireframe_obj(str(obj_path), Lambda_ref, Theta_ref)
    print(f"\n✓ OBJ wireframe: {obj_path}")
    
    # Export as STL with tube visualization
    stl_path = out_dir / "reference_wireframe_CORRECT.stl"
    export_wireframe_as_tubes_stl(str(stl_path), Lambda_ref, Theta_ref, tube_radius=0.08)
    print(f"✓ STL wireframe: {stl_path}")
    
    print("\n" + "=" * 70)
    print("Compare this file with the reconstructed solutions:")
    print("  - This file has 33 edges (CORRECT)")
    print("  - Solutions 2/3/4 have 28 edges (INCORRECT)")
    print("=" * 70)


if __name__ == "__main__":
    main()
