import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from plot import read_obj

# (file, title, color) for each particle
PARTICLES = [
    ("siris-output.obj", "Danielle: near-spherical (σ = 0.01)", "lightblue"),
    ("complex.obj", "Nick: candidate complex shape (σ = 0.245)", "salmon"),
]

def compare_shapes(particles, save_path="shape_comparison.png"):
    """
    Plot particles side by side on identical axes so their sizes are comparable.
    """
    loaded = [(read_obj(f), title, color) for f, title, color in particles]

    # Shared axis limit so both shapes are drawn at the same scale
    lim = max(np.abs(v).max() for (v, _), _, _ in loaded)

    fig = plt.figure(figsize=(6 * len(loaded), 6))
    for i, ((vertices, faces), title, color) in enumerate(loaded):
        ax = fig.add_subplot(1, len(loaded), i + 1, projection='3d')

        poly = Poly3DCollection([vertices[face] for face in faces], edgecolor='k', linewidth=0.1)
        poly.set_facecolor(color)
        ax.add_collection3d(poly)

        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(-lim, lim)
        ax.set_box_aspect((1, 1, 1))
        ax.set_title(title)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    compare_shapes(PARTICLES)
