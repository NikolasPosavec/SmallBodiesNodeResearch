"""
Why is the original SIRIS4 example's -S12/S11 curve smooth?

Starts from the original example (git c5439cea: perfect sphere, n = 1.5 + 0i,
no diffuse inclusions, 10 000 rays, 80 bins) and changes one thing per test.
Prints a noise measure for each test and plots each against the original.

Usage (from the repo root, with the .venv active for matplotlib):
    python3 sweeps/smooth_tests.py
"""

import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

REPO = Path(__file__).resolve().parent.parent
TEST_DIR = REPO / "sweeps" / "smooth_tests"
SIRISMP_EXE = REPO / "multi-particle" / "sirismp"

SPHERE = REPO / "multi-particle" / "example" / "sphere.off"
DANIELLE_SHAPE = REPO / "multi-particle" / "example" / "siris-output.off"
BASELINE_SHAPE = REPO / "sweeps" / "baseline" / "shape.off"

ORIGINAL_OUTPUT_GIT = "c5439cea:multi-particle/example/outputS.out"

# The original example input, minus the unused diffuse-scatterer fields
ORIGINAL = {
    "nrays": 10000,
    "nbins": 80,
    "mesh_scale": 2000,
    "mesh": SPHERE,
    "material": "1.5 0.0 0",
}

# name -> (what changed, changes from ORIGINAL)
TESTS = {
    "T0_original": ("none (rerun)", {}),
    "T1_nbins_180": ("180 bins", {"nbins": 180}),
    "T2_gaussian_0.3": ("shape: σ = 0.3 baseline", {"mesh": BASELINE_SHAPE}),
    "T3_danielle_0.01": ("shape: σ = 0.01, l 10–30", {"mesh": DANIELLE_SHAPE}),
    "T4_fayalite_x20": ("fayalite, size 20",
                        {"material": "1.85 0.00077 0", "mesh_scale": 20}),
    "T5_gaussian_100k": ("σ = 0.3, 100k rays",
                         {"mesh": BASELINE_SHAPE, "nrays": 100000}),
}


# ============================================================
# HELPERS
# ============================================================

def write_input(workdir, s):

    text = f"""nrays {s['nrays']}
max_scattering 200
killswitch_start 70
nbins {s['nbins']}
I_cutoff_limit 0.0000001
seed 12345
wavelen 6.283185307179586
mesh_scale {s['mesh_scale']}
mesh mesh.off
force_interaction 1
beam_radius -1
material1 {s['material']}
output_file outputS.out
pmatrix_out pmatrix.out
details_out details.out
"""

    (workdir / "input.in").write_text(text)


def run_test(name, changes):

    workdir = TEST_DIR / name
    if (workdir / "details.out").exists():
        print(f"{name}: already done, skipping")
        return

    settings = {**ORIGINAL, **changes}
    workdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(settings["mesh"], workdir / "mesh.off")
    write_input(workdir, settings)

    print(f"{name}: running ...", flush=True)
    with open(workdir / "sirismp.log", "w") as log:
        subprocess.run([str(SIRISMP_EXE), "input.in"], cwd=workdir,
                       stdout=log, stderr=subprocess.STDOUT, check=True)


def polarization(data):
    """Angle and -S12/S11, without the half-width end bins at 0 and 180."""

    angle, pol = data[1:-1, 0], -data[1:-1, 2] / data[1:-1, 1]
    return angle, pol


def noise(angle, pol):
    """
    Bin-to-bin scatter: std of the second difference, scaled to one bin
    (a smooth curve has a near-zero second difference). Uses 10-170 deg.
    """

    keep = (angle >= 10) & (angle <= 170)
    return np.std(np.diff(pol[keep], 2)) / np.sqrt(6)


def original_output():

    text = subprocess.run(["git", "show", ORIGINAL_OUTPUT_GIT], cwd=REPO,
                          capture_output=True, text=True, check=True).stdout
    return np.loadtxt(text.splitlines())


# ============================================================
# MAIN
# ============================================================

def main():

    for name, (_, changes) in TESTS.items():
        run_test(name, changes)

    ref_angle, ref_pol = polarization(original_output())

    print(f"\n{'test':20s} {'changed':26s} {'noise':>7s}  max -S12/S11 (140-170°)")
    print(f"{'2019 original':20s} {'(committed output)':26s} "
          f"{noise(ref_angle, ref_pol):7.4f}")

    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True, sharey=True)
    for ax, (name, (changed, _)) in zip(axes.flat, TESTS.items()):
        angle, pol = polarization(np.loadtxt(TEST_DIR / name / "outputS.out"))
        rainbow = (angle > 140) & (angle < 170)
        peak = np.argmax(np.where(rainbow, pol, -np.inf))
        print(f"{name:20s} {changed:26s} {noise(angle, pol):7.4f}  "
              f"{pol[peak]:.3f} at {angle[peak]:.0f}°")

        ax.plot(ref_angle, ref_pol, color="#8a8a85", linestyle=":",
                linewidth=1.5, label="2019 original")
        ax.plot(angle, pol, color="#2a78d6", linewidth=1.5, label=name)
        ax.axhline(0, color="#c3c2b7", linewidth=0.8, zorder=0)
        ax.set_title(f"{name}\n{changed}", fontsize=10)
        ax.set_xlim(0, 180)
        ax.set_xticks(range(0, 181, 30))
        ax.grid(color="#e6e5e0", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    for ax in axes[1]:
        ax.set_xlabel("Scattering angle (deg)")
    for ax in axes[:, 0]:
        ax.set_ylabel("−S12/S11")
    axes[0, 0].legend(["2019 original", "this test"], frameon=False, fontsize=9)

    fig.suptitle("What makes the original example's polarization smooth?")
    fig.tight_layout()
    fig.savefig(TEST_DIR / "smooth_tests.png", dpi=150)
    print(f"\nplot: {TEST_DIR.relative_to(REPO)}/smooth_tests.png")


if __name__ == "__main__":
    main()
