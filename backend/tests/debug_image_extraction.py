"""Debug extracted 2D graphs from images."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reconstruction.image_processing import image_to_2d_graph

# Process each view
for view_name, image_path in [
    ('FRONT', 'data/FRONT_T.png'),
    ('TOP', 'data/TOP_T.png'),
    ('SIDE', 'data/SIDE_T.png')
]:
    try:
        vertices, edges, visibility = image_to_2d_graph(image_path)
        print(f"\n{view_name}:")
        print(f"  Vertices ({len(vertices)}): {vertices[:8]}")
        print(f"  Edges ({len(edges)}): {edges[:8]}")
        print(f"  Visible edges: {sum(visibility)}/{len(visibility)}")
    except Exception as e:
        print(f"\n{view_name}: ERROR - {e}")
