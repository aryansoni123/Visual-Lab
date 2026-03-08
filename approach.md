# 3D Reconstruction Project Approach

## Definitions
- `Lambda`: Candidate 3D vertices list, each vertex represented as `[x, y, z, front_idx, top_idx, side_idx]`.
- `Theta`: 3D edge list as index pairs `(u, v)` over `Lambda`.
- `Face`: Closed coplanar boundary cycle over `Theta`.
- `Boundary triangles`: Triangulated surface faces used for STL export.
- `Tetrahedra`: Interior volumetric elements from Delaunay tetrahedralization.
- `Euler check`: For closed genus-0 polyhedron, `V - E + F = 2`.

## PS (Problem Statement)
Build a robust pipeline that reconstructs a watertight 3D mesh from orthographic-view-derived wireframes and exports valid STL/VTU outputs. The key challenge is ambiguous face reconstruction from `Lambda/Theta`, especially for non-trivial cuboidal/stepped geometries.

## Constraints
- Domain focus: Mechanical parts made of cuboidal/orthogonal surfaces.
- Output quality:
  - Faces must be topologically consistent.
  - STL normals must point outward (no disappearing faces in viewers).
  - Mesh should support both boundary-only and filled volume outputs.
- Practical constraints:
  - Numeric tolerance handling (`TOL = 1e-6`).
  - Prefer deterministic/repeatable selection over ad hoc randomness.

## Different Approaches Tried and Results

### 1. Legacy face walkers / minimal-cycle variants (v2-v4)
- Idea: Traverse half-edges / shortest cycles to recover faces.
- Outcome: Unstable on complex graphs; produced duplicate/incorrect cycles and Euler failures on harder geometries.
- Verdict: Not reliable as production core.

### 2. Plane-clustering (v5)
- Idea: Generate plane hypotheses from vertex triples, cluster coplanar vertices, extract induced boundary cycles.
- Outcome:
  - Strong improvement over legacy versions.
  - Worked on simple cube/box tests.
  - Still vulnerable to ambiguity on complex stepped/non-convex layouts.
- Verdict: Good baseline, but not fully robust for all target cases.

### 3. Euler-driven cycle selection
- Idea: Compute required face count first (`F_required = E - V + 2`), enumerate cycles, then select coplanar subset to meet topology.
- Outcome:
  - Conceptually stronger than post-hoc Euler validation.
  - Worked on cube and L-shaped validation runs.
  - Search-space complexity and candidate conflicts remained challenging.
- Verdict: Important conceptual pivot and useful fallback/reference implementation.

### 4. Largest-face-first (current active direction)
- Idea: Prioritize larger planar candidates first, then enforce constraints while selecting required face count.
- Implemented as:
  - Planar candidate deduplication by boundary-edge signature.
  - 3D polygon area scoring.
  - Include-first branch-and-bound/backtracking.
  - Adaptive edge-incidence cap fallback (`2 -> 3 -> 4`) when strict manifold cap cannot satisfy target.
- Latest result on provided L-shape test:
  - `F_required = 19`, selected `19` faces.
  - `Edge coverage = 100%`.
  - Euler check passed (`V - E + F = 2`).
  - STL/VTU export succeeded.
- Caveat:
  - Needed incidence cap `4` on that dataset; this signals practical success but not strict manifold purity at candidate-selection stage.
- Verdict: Current best working implementation for progress continuation.

## Normal Orientation Fix (Critical)
- Problem seen: Some mesh faces disappeared in STL viewers due to inconsistent winding.
- Fix implemented: `ensure_outward_normals()`
  - Compute mesh centroid.
  - For each triangle, compare normal direction with vector from centroid to triangle center.
  - Flip vertex winding if inward.
- Result: Stable outward-facing normals in generated STL.

## Volumetric Mesh Addition
- Added Delaunay tetrahedral meshing to fill interior volume.
- Exports:
  - `STL`: boundary triangles.
  - `VTU`: tetrahedral cells + boundary triangles.
- Result: Surface + volumetric outputs available for downstream visualization/analysis.

## Project Structure Refactor (Completed)
- `backend/pipeline.py` retained as main entrypoint at backend root.
- Categorized modules:
  - `backend/reconstruction/` for image + pseudo-wireframe stages.
  - `backend/algorithms/` for face/mesh logic.
  - `backend/tests/` for current tests and `backend/tests/legacy/` for older scripts.
  - `backend/outputs/` for generated STL/VTU artifacts.
  - `backend/config/requirements.txt` for dependencies.
- Imports in `pipeline.py` and active tests updated accordingly.

## Current Progress Snapshot
- Face detection core now runs with largest-face-first constrained search.
- L-shape regression test passes end-to-end with current selector.
- Backend structure reorganized into category folders.
- Syntax checks pass for key backend modules.

## Known Risks / Next Hardening Steps
1. Add explicit strict mode (`edge-incidence=2 only`) vs adaptive mode.
2. Add deterministic tie-breakers for candidate conflicts.
3. Add manifold-quality metrics beyond Euler (edge-face incidence histograms, self-overlap checks).
4. Build targeted regression suite for cuboidal edge cases (steps, notches, deep concavities).
5. Optionally gate STL export when strict manifold criteria fail.
