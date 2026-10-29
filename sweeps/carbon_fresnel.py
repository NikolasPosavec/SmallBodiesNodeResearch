"""
Why the amorphous carbon (size 200) -S12/S11 curve is smooth.

Carbon absorbs almost all light that enters the particle, so the scattered
light is a single reflection from the surface. For one reflection, the
scattering angle fixes the incidence angle, i = (180 - theta) / 2, so the
polarization at each angle is the Fresnel value for that incidence angle.
This script overlays that prediction on the sirismp results.

Usage (from the repo root, with the .venv active for matplotlib):
    python3 sweeps/carbon_fresnel.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "multi-particle" / "example"

M = 2.14 + 0.805j  # amorphous carbon at red wavelengths
Q_SCA_DANIELLE = 0.2283  # from her details.out

RUNS = [
    (EXAMPLE / "batch_runs" / "amorphous_carbon_200" / "outputS.out",
     "Danielle (100,000 rays)", "#2a78d6", "-"),
    (EXAMPLE / "my_runs" / "amorphous_carbon_200" / "outputS.out",
     "Nick (20,000 rays)", "#eb6834", "--"),
]
FRESNEL_STYLE = ("#1a1a19", ":")

SAVE_PATH = REPO / "sweeps" / "plots" / "carbon_fresnel.png"


# ============================================================
# HELPERS
# ============================================================

def fresnel(incidence):
    """Reflectances Rs, Rp at the given incidence angles (radians)."""

    cos_i = np.cos(incidence)
    cos_t = np.sqrt(1 - (np.sin(incidence) / M) ** 2)
    rs = (cos_i - M * cos_t) / (cos_i + M * cos_t)
    rp = (M * cos_i - cos_t) / (M * cos_i + cos_t)
    return abs(rs) ** 2, abs(rp) ** 2


def single_reflection_pol(theta_deg):
    """-S12/S11 for light reflected once, at scattering angle theta."""

    rs, rp = fresnel(np.radians((180 - theta_deg) / 2))
    return (rs - rp) / (rs + rp)


def sphere_reflectance():
    """Fraction of light a sphere reflects, averaged over the beam."""

    i = np.linspace(0, np.pi / 2, 20001)
    rs, rp = fresnel(i)
    return np.trapezoid((rs + rp) / 2 * 2 * np.cos(i) * np.sin(i), i)


# ============================================================
# MAIN
# ============================================================

def main():

    theta = np.linspace(0.5, 179.5, 359)
    prediction = single_reflection_pol(theta)

    fig, (ax_pol, ax_diff) = plt.subplots(
        2, 1, figsize=(7.5, 6), sharex=True,
        gridspec_kw={"height_ratios": [3, 1.3]})

    for path, label, color, dash in RUNS:
        data = np.loadtxt(path)
        keep = data[:, 1] > 0  # skip empty bins
        angle = data[keep, 0]
        pol = -data[keep, 2] / data[keep, 1]
        diff = pol - single_reflection_pol(angle)
        inner = (angle > 2) & (angle < 178)
        print(f"{label:24s} max |sim - Fresnel| (2-178°): "
              f"{np.abs(diff[inner]).max():.4f}")

        ax_pol.plot(angle, pol, color=color, linestyle=dash, linewidth=1.5,
                    label=label)
        ax_diff.plot(angle[inner], diff[inner], color=color, linestyle=dash,
                     linewidth=1.2)

    color, dash = FRESNEL_STYLE
    ax_pol.plot(theta, prediction, color=color, linestyle=dash, linewidth=2,
                label="Fresnel, single reflection")

    peak = np.argmax(prediction)
    print(f"Fresnel peak: {prediction[peak]:.4f} at {theta[peak]:.0f}°")
    print(f"Sphere-averaged reflectance: {sphere_reflectance():.4f} "
          f"(Danielle's Q_sca: {Q_SCA_DANIELLE})")

    ax_pol.set_ylabel("−S12/S11")
    ax_pol.legend(frameon=False, fontsize=9)
    ax_diff.axhline(0, color="#c3c2b7", linewidth=0.8, zorder=0)
    ax_diff.set_ylabel("Simulation − Fresnel")
    ax_diff.set_ylim(-0.02, 0.02)
    ax_diff.set_xlabel("Scattering angle (deg)")

    for ax in (ax_pol, ax_diff):
        ax.set_xlim(0, 180)
        ax.set_xticks(range(0, 181, 30))
        ax.grid(color="#e6e5e0", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Amorphous carbon, size 200: polarization from one reflection")
    fig.tight_layout()
    fig.savefig(SAVE_PATH, dpi=150)
    print(f"plot: {SAVE_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
