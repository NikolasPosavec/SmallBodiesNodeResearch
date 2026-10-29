"""
Extract S11 and -S12/S11 from each sweep run and plot one comparison per sweep.

For every finished run this writes <run>/s11_pol.txt (angle, S11, -S12/S11).
The N-particle results are averages over the first N shapes of n_particles_20,
weighted by geometric cross-section, written to n_particles_<N>/s11_pol.txt.
Runs that have not finished yet are skipped.

Usage (from the repo root):
    python3 sweeps/extract_and_plot.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

SWEEP_DIR = Path(__file__).resolve().parent
PLOT_DIR = SWEEP_DIR / "plots"

N_PARTICLES = [5, 10, 20]

# sweep -> (baseline legend label, [(run folder, legend label)] for the
# variants). The baseline is power law 4, l_min 2, l_max 10, N = 1, and is
# drawn on every plot as the same gray reference line.
SWEEPS = {
    "power_law": ("ν = 4 (baseline)",
                  [("power_law_2", "ν = 2"), ("power_law_6", "ν = 6")]),
    "l_min": ("l_min = 2 (baseline)",
              [("l_min_1", "l_min = 1"), ("l_min_3", "l_min = 3")]),
    "l_max": ("l_max = 10 (baseline)",
              [("l_max_5", "l_max = 5"), ("l_max_30", "l_max = 30")]),
    "n_particles": ("N = 1 (baseline)",
                    [(f"n_particles_{n}", f"N = {n}") for n in N_PARTICLES]),
}

# Categorical slots 1-3 (validated), one dash style each as a second cue
STYLES = [("#2a78d6", "-"), ("#eb6834", "--"), ("#1baf7a", "-.")]
BASELINE_STYLE = ("#8a8a85", ":")


# ============================================================
# HELPERS
# ============================================================

def read_outputS(run_dir):
    """Angle (deg), S11, S12 from a sirismp outputS.out."""

    data = np.loadtxt(run_dir / "outputS.out")
    return data[:, 0], data[:, 1], data[:, 2]


def read_area(run_dir):
    """Geometric cross-section (Real_Area) from details.out."""

    for line in (run_dir / "details.out").read_text().splitlines():
        if line.startswith("Real_Area:"):
            return float(line.split()[1].rstrip(","))
    raise ValueError(f"No Real_Area in {run_dir / 'details.out'}")


def write_table(run_dir, angle, s11, s12):

    run_dir.mkdir(exist_ok=True)
    table = np.column_stack([angle, s11, -s12 / s11])
    np.savetxt(run_dir / "s11_pol.txt", table, fmt="%.6g",
               header="angle_deg  S11  -S12/S11")


def ensemble_average(n):
    """
    Average the first n shapes of n_particles_20. Each sirismp output is
    normalized per hit ray, and hits scale with cross-section, so each shape
    is weighted by its area. Polarization comes from the averaged S12 and S11.
    """

    shape_dirs = [SWEEP_DIR / "n_particles_20" / f"shape_{i:02d}"
                  for i in range(1, n + 1)]
    if not all((d / "details.out").exists() for d in shape_dirs):
        return None

    weights = np.array([read_area(d) for d in shape_dirs])
    outputs = [read_outputS(d) for d in shape_dirs]
    s11 = sum(w * o[1] for w, o in zip(weights, outputs)) / weights.sum()
    s12 = sum(w * o[2] for w, o in zip(weights, outputs)) / weights.sum()
    return outputs[0][0], s11, s12


def load_table(name):

    path = SWEEP_DIR / name / "s11_pol.txt"
    return np.loadtxt(path) if path.exists() else None


def plot_sweep(sweep, baseline_label, runs):

    fig, (ax_s11, ax_pol) = plt.subplots(1, 2, figsize=(11, 4.2))

    lines = [(("baseline", baseline_label), BASELINE_STYLE)]
    lines += list(zip(runs, STYLES))

    plotted = 0
    for (name, label), (color, dash) in lines:
        table = load_table(name)
        if table is None:
            continue
        ax_s11.plot(table[:, 0], table[:, 1], color=color, linestyle=dash,
                    linewidth=1.5, label=label)
        ax_pol.plot(table[:, 0], table[:, 2], color=color, linestyle=dash,
                    linewidth=1.5, label=label)
        plotted += 1

    if plotted == 0:
        plt.close(fig)
        return False

    ax_s11.set_yscale("log")
    ax_s11.set_ylabel("S11 (intensity)")
    ax_pol.set_ylabel("−S12/S11 (degree of linear polarization)")
    ax_pol.axhline(0, color="#c3c2b7", linewidth=0.8, zorder=0)

    for ax in (ax_s11, ax_pol):
        ax.set_xlabel("Scattering angle (deg)")
        ax.set_xlim(0, 180)
        ax.set_xticks(range(0, 181, 30))
        ax.grid(color="#e6e5e0", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    ax_pol.legend(frameon=False, fontsize=9)
    fig.suptitle(f"Effect of {sweep.replace('_', ' ')} "
                 f"(fayalite, size parameter 20)")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / f"{sweep}.png", dpi=150)
    plt.close(fig)
    return True


# ============================================================
# MAIN
# ============================================================

def main():

    PLOT_DIR.mkdir(exist_ok=True)

    # 1. Two-column tables for every finished single-shape run
    for run_dir in sorted(SWEEP_DIR.iterdir()):
        if (run_dir / "outputS.out").exists():
            write_table(run_dir, *read_outputS(run_dir))
            print(f"table: {run_dir.name}")

    # 2. Ensemble averages over the first N shapes
    for n in N_PARTICLES:
        averaged = ensemble_average(n)
        if averaged is None:
            print(f"skip:  n_particles_{n} (shapes not finished)")
            continue
        write_table(SWEEP_DIR / f"n_particles_{n}", *averaged)
        print(f"table: n_particles_{n} (area-weighted average of {n} shapes)")

    # 3. One comparison figure per sweep
    for sweep, (baseline_label, runs) in SWEEPS.items():
        if plot_sweep(sweep, baseline_label, runs):
            print(f"plot:  plots/{sweep}.png")


if __name__ == "__main__":
    main()
