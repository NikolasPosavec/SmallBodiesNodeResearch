import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import os

def read_obj(file_path):
    vertices = []
    faces = []

    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue

            values = line.split()
            if not values:
                continue

            if values[0] == 'v':
                vertices.append([float(values[1]), float(values[2]), float(values[3])])

            elif values[0] == 'f':
                face = []
                for v in values[1:]:
                    vertex_index = int(v.split('/')[0]) - 1
                    face.append(vertex_index)
                faces.append(face)

    return np.array(vertices), faces

def plot_multiple_objs(file_paths, offsets=None):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    colors = ['lightblue', 'salmon', 'lightgreen', 'orange', 'violet', 'cyan', 'gold']
    if offsets is None:
        offsets = [(0, 0, 0)] * len(file_paths)

    for idx, file_path in enumerate(file_paths):
        vertices, faces = read_obj(file_path)
        offset = offsets[idx] if idx < len(offsets) else (0, 0, 0)
        vertices = vertices + np.array(offset)

        mesh = []
        for face in faces:
            verts = [vertices[i] for i in face]
            mesh.append(verts)

        poly = Poly3DCollection(mesh, alpha=0.5, edgecolor='k', linewidth=0.5)
        color = colors[idx % len(colors)]
        poly.set_facecolor(color)
        ax.add_collection3d(poly)

    # Combine all vertices to set limits correctly
    all_vertices = []
    for i, file_path in enumerate(file_paths):
        v, _ = read_obj(file_path)
        v = v + np.array(offsets[i])
        all_vertices.append(v)
    all_vertices = np.vstack(all_vertices)

    if len(all_vertices) > 0:
        x = all_vertices[:, 0]
        y = all_vertices[:, 1]
        z = all_vertices[:, 2]

        max_range = np.array([x.max()-x.min(), y.max()-y.min(), z.max()-z.min()]).max() / 2.0
        mid_x = (x.max()+x.min()) / 2.0
        mid_y = (y.max()+y.min()) / 2.0
        mid_z = (z.max()+z.min()) / 2.0
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title("Multiple 3D OBJ Models")

    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        obj_files = sys.argv[1:]
    else:
        obj_files = ["model1.obj", "model2.obj", "model3.obj"]  # Replace with your OBJ file names

    # Optional: Offset each model in X direction to separate them visually
    offsets = [(i * 3, 0, 0) for i in range(len(obj_files))]

    plot_multiple_objs(obj_files, offsets=offsets)
