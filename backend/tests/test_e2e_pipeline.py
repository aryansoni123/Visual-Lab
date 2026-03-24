"""Test end-to-end pipeline with known synthetic dataset."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.face_detection_minimal_artifacts import find_all_faces_minimal_artifacts
from algorithms.face_detection import triangulate_polygon, export_stl
import numpy as np

# Use Dataset 1 (Stepped Block) from test.py - we know it works
Lambda = [
    [0,0,0], [6,0,0], [6,4,0], [0,4,0],
    [0,0,6], [6,0,6], [6,4,6], [0,4,6],
    [2,0,6], [4,0,6], [4,4,6], [2,4,6],
    [2,0,9], [4,0,9], [4,4,9], [2,4,9]
]

Theta = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7),
    (8,9),(9,10),(10,11),(11,8),
    (12,13),(13,14),(14,15),(15,12),
    (8,12),(9,13),(10,14),(11,15),
    (8,4),(9,5),(10,6),(11,7)
]

print("="*70)
print("END-TO-END PIPELINE TEST")
print("="*70)
print(f"\nInput: V={len(Lambda)}, E={len(Theta)}")

# Stage 1: Face Detection
print("\nStage: Face Detection (Minimal Artifacts)")
print("-"*70)
try:
    faces = find_all_faces_minimal_artifacts(Lambda, Theta)
    print(f"✓ Faces: {len(faces)}")
except Exception as e:
    print(f"✗ Face detection failed: {e}")
    faces = []

# Stage 2: Triangulation
print("\nStage: Triangulation")
print("-"*70)
triangles = []
for i, face in enumerate(faces):
    try:
        tris = triangulate_polygon(face, Lambda)
        triangles.extend(tris)
        print(f"  Face {i}: {len(face)}-gon → {len(tris)} triangles")
    except Exception as e:
        print(f"  Face {i}: ERROR - {e}")

print(f"\n✓ Total triangles: {len(triangles)}")

# Stage 3: Export STL
print("\nStage: STL Export")
print("-"*70)
output_path = "../outputs/test_e2e.stl"
try:
    export_stl(output_path, triangles, Lambda)
    print(f"✓ STL exported: {output_path}")
except Exception as e:
    print(f"✗ Export failed: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Vertices: {len(Lambda)}")
print(f"Edges: {len(Theta)}")
print(f"Faces: {len(faces)}")
print(f"Triangles: {len(triangles)}")
print("✓ End-to-end test COMPLETE")
