"""Debug Dataset 4: Check which faces were detected and which edges are missing."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from algorithms.face_detection_minimal_artifacts import find_all_faces_minimal_artifacts


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


def get_face_edges(face):
    """Get edge keys from a face."""
    edges = set()
    for i in range(len(face)):
        u = face[i]
        v = face[(i + 1) % len(face)]
        edges.add((min(u, v), max(u, v)))
    return edges


def main():
    print(f"\n{'=' * 70}")
    print(f"DATASET 4 FACE DETECTION DEBUG")
    print(f"{'=' * 70}\n")
    
    print(f"Input: V={len(Lambda4)}, E={len(Theta4)}")
    
    # Detect faces
    faces = find_all_faces_minimal_artifacts(Lambda4, Theta4)
    
    if faces is None:
        print("Face detection failed!")
        return
    
    print(f"\n{'=' * 70}")
    print(f"DETECTED FACES:")
    print(f"{'=' * 70}\n")
    
    all_covered_edges = set()
    
    for i, face in enumerate(faces, 1):
        face_edges = get_face_edges(face)
        all_covered_edges.update(face_edges)
        
        # Get Z-level of face
        z_vals = [Lambda4[v][2] for v in face]
        z_level = z_vals[0] if len(set(z_vals)) == 1 else "mixed"
        
        print(f"Face {i:2d}: {face}")
        print(f"  Size: {len(face)} vertices")
        print(f"  Z-level: {z_level}")
        print(f"  Edges: {sorted(face_edges)}")
        
        # Show vertex coordinates
        coords = [f"({Lambda4[v][0]:.0f},{Lambda4[v][1]:.0f},{Lambda4[v][2]:.0f})" for v in face]
        print(f"  Coords: {', '.join(coords)}")
        print()
    
    # Check edge coverage
    print(f"\n{'=' * 70}")
    print(f"EDGE COVERAGE ANALYSIS:")
    print(f"{'=' * 70}\n")
    
    theta_normalized = set()
    for u, v in Theta4:
        theta_normalized.add((min(u, v), max(u, v)))
    
    covered = all_covered_edges & theta_normalized
    missing = theta_normalized - all_covered_edges
    
    print(f"Total edges in Theta: {len(theta_normalized)}")
    print(f"Edges covered by faces: {len(covered)}")
    print(f"Missing edges: {len(missing)}")
    print(f"Coverage: {len(covered)/len(theta_normalized)*100:.1f}%")
    
    if missing:
        print(f"\nMISSING EDGES:")
        for edge in sorted(missing):
            u, v = edge
            v1 = Lambda4[u]
            v2 = Lambda4[v]
            print(f"  {u:2d}→{v:2d}: ({v1[0]:.0f},{v1[1]:.0f},{v1[2]:.0f}) → ({v2[0]:.0f},{v2[1]:.0f},{v2[2]:.0f})")
    
    # Check specifically for top face
    print(f"\n{'=' * 70}")
    print(f"TOP FACE CHECK (Z=12):")
    print(f"{'=' * 70}\n")
    
    top_face_edges = {(20,21), (21,22), (22,23), (20,23)}
    top_face_normalized = set()
    for u, v in top_face_edges:
        top_face_normalized.add((min(u, v), max(u, v)))
    
    print(f"Expected top face edges: {sorted(top_face_normalized)}")
    print(f"Top face vertices: 20, 21, 22, 23")
    print(f"Coordinates:")
    for v in [20, 21, 22, 23]:
        print(f"  Vertex {v}: {Lambda4[v]}")
    
    found_in_faces = False
    for i, face in enumerate(faces, 1):
        if set(face) == {20, 21, 22, 23}:
            print(f"\n✓ Top face FOUND in Face {i}")
            found_in_faces = True
            break
    
    if not found_in_faces:
        print(f"\n✗ Top face NOT FOUND in detected faces")
        
        # Check if edges are in missing list
        top_missing = top_face_normalized & missing
        if top_missing:
            print(f"  Top face edges are MISSING from coverage: {sorted(top_missing)}")
        else:
            print(f"  Top face edges are covered but face was not detected")


if __name__ == "__main__":
    main()
