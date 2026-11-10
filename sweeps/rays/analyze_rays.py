"""
Ray-count convergence analysis for the runs made by run_rays.py.

Measures Monte Carlo noise in -S12/S11 and S11 at 100k/200k/400k/900k rays
(3 independent ray seeds each), fits noise vs ray count, tests wider angle bins
(2 and 5 deg) at 100k and 200k, and writes:

    sweeps/rays/results.md            table + fit numbers
    sweeps/rays/results.json          the same numbers, machine-readable
    sweeps/plots/rays_noise.png       Plot 1: noise vs ray count (log-log)
    sweeps/plots/rays_pol_100k_900k.png   Plot 2: -S12/S11 at 100k vs 900k

Usage (from anywhere):
    python3 sweeps/rays/analyze_rays.py

NOISE DEFINITION
For one setting, take the 3 runs (different ray seeds), and in each angle bin
compute the sample variance across the runs (ddof=1). Noise = sqrt(mean of
that variance over the bins). This is exactly the pairwise definition
"RMS(run_a - run_b) / sqrt(2)" pooled over all 3 pairs, because for n values
sum over pairs (x_i - x_j)^2 = n (n - 1) s^2. It is the expected per-bin
error of a SINGLE run. S11 uses the same thing on (std / mean), i.e. relative.

ANGLE RANGE
Bins centered on 10..169 deg (160 one-degree bins). 160 = 80 x 2 = 32 x 5, so
1, 2 and 5 deg bins cover exactly the same range, 9.5 to 169.5 deg.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# SETTINGS
# ============================================================

RAYS_DIR = Path(__file__).resolve().parent
PLOT_DIR = RAYS_DIR.parent / "plots"

COUNTS = [100_000, 200_000, 400_000, 900_000]
SEEDS = [1, 2, 3]
REFERENCE_COUNT = 900_000

FIRST_BIN, LAST_BIN = 10, 169          # bin centers in degrees (inclusive)
WIDE_BINS = [2, 5]                     # degrees
WIDE_BIN_COUNTS = [100_000, 200_000]   # ray counts to rebin

PREVIOUS_100K_NOISE = 0.015            # Nick's earlier estimate (Oct 29 sweep)

# Same colors and styling as sweeps/extract_and_plot.py
BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"
GRAY = "#8a8a85"
GRID = "#e6e5e0"


# ============================================================
# LOADING
# ============================================================

def label(count):

    return f"{count // 1000}k"


def run_dir(count, seed):

    return RAYS_DIR / f"{label(count)}_seed{seed}"


def load_run(count, seed):
    """Angle, S11 and S12 (181 one-degree bins, row i = bin centered on i deg)."""

    data = np.loadtxt(run_dir(count, seed) / "outputS.out")
    return data[:, 0], data[:, 1], data[:, 2]


def load_count(count):
    """S11 and S12 as (n_seeds, 181) arrays."""

    runs = [load_run(count, s) for s in SEEDS]
    s11 = np.array([r[1] for r in runs])
    s12 = np.array([r[2] for r in runs])
    return runs[0][0], s11, s12


def runtimes_minutes(count):

    return [json.loads((run_dir(count, s) / "params.json").read_text())["runtime_seconds"] / 60
            for s in SEEDS]


# ============================================================
# ANALYSIS
# ============================================================

def in_range(a):
    """Keep the bins centered on FIRST_BIN..LAST_BIN (last axis)."""

    return a[..., FIRST_BIN:LAST_BIN + 1]


def rebin(angle, s11, s12, width):
    """
    Combine `width` neighbouring 1-deg bins into one wider bin.

    sirismp divides each bin's summed intensity by its solid-angle factor
    (cos(lower edge) - cos(upper edge)), see Detector::normalize_output. So the
    raw sums are recovered by multiplying back by that factor, and the wide bin
    is the weighted mean of S11 (and of S12) with those weights. The ratio
    -S12/S11 is formed afterwards from the combined S11 and S12.
    """

    theta = np.radians(in_range(angle))
    half = np.radians(0.5)
    w = np.cos(theta - half) - np.cos(theta + half)          # (160,)

    def combine(s):
        s = in_range(s)                                       # (n_seeds, 160)
        shape = s.shape[:-1] + (-1, width)
        return (s * w).reshape(shape).sum(-1) / w.reshape(-1, width).sum(-1)

    centers = in_range(angle).reshape(-1, width).mean(-1)
    return centers, combine(s11), combine(s12)


def pol(s11, s12):

    return -s12 / s11


def noise(values):
    """Single-run noise: sqrt(mean over bins of the across-seed variance)."""

    return float(np.sqrt(np.mean(np.var(values, axis=0, ddof=1))))


def relative_noise(values):

    rel_var = np.var(values, axis=0, ddof=1) / np.mean(values, axis=0) ** 2
    return float(np.sqrt(np.mean(rel_var)))


def loglog_slope(counts, values):

    slope, intercept = np.polyfit(np.log10(counts), np.log10(values), 1)
    return float(slope), float(intercept)


# ============================================================
# PLOTS
# ============================================================

def style_axes(ax):

    ax.grid(color=GRID, linewidth=0.6, which="major")
    ax.spines[["top", "right"]].set_visible(False)


def plot_noise(results):

    fig, ax = plt.subplots(figsize=(6.4, 4.6))

    counts = np.array(COUNTS)
    one_deg = np.array([results["1deg"][label(c)]["pol_noise"] for c in COUNTS])

    # 1/sqrt(N) reference anchored at the 100k point
    n_ref = np.geomspace(80_000, 1_100_000, 50)
    ax.plot(n_ref, one_deg[0] * np.sqrt(COUNTS[0] / n_ref), color=GRAY,
            linestyle="--", linewidth=1.2, label="1/√N (from 100k point)")

    ax.plot(counts, one_deg, color=BLUE, marker="o", markersize=8,
            linewidth=2, label="1° bins")
    for width, color in zip(WIDE_BINS, [ORANGE, GREEN]):
        wide = [results[f"{width}deg"][label(c)]["pol_noise"] for c in WIDE_BIN_COUNTS]
        ax.plot(WIDE_BIN_COUNTS, wide, color=color, marker="s", markersize=8,
                linewidth=2, label=f"{width}° bins")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(COUNTS)
    ax.set_xticklabels([label(c) for c in COUNTS])
    ax.minorticks_off()
    yticks = [0.002, 0.003, 0.005, 0.01, 0.02]
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{y:g}" for y in yticks])
    ax.set_xlabel("Rays per run")
    ax.set_ylabel("Noise in −S12/S11 per bin (single run)")
    style_axes(ax)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title(f"Polarization noise vs ray count "
                 f"(fit slope {results['fit']['pol_slope']:.2f}, ideal −0.50)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "rays_noise.png", dpi=150)
    plt.close(fig)


def plot_pol_curves():

    fig, ax = plt.subplots(figsize=(8, 4.4))

    for count, color, width in [(100_000, BLUE, 1.0), (900_000, ORANGE, 1.6)]:
        angle, s11, s12 = load_run(count, 1)
        ax.plot(angle, pol(s11, s12), color=color, linewidth=width,
                label=f"{label(count)} rays (seed 1)")

    ax.axhline(0, color="#c3c2b7", linewidth=0.8, zorder=0)
    ax.axvspan(0, FIRST_BIN - 0.5, color="#f2f1ed", zorder=-1)
    ax.axvspan(LAST_BIN + 0.5, 180, color="#f2f1ed", zorder=-1)
    ax.set_xlim(0, 180)
    ax.set_xticks(range(0, 181, 30))
    ax.set_xlabel("Scattering angle (deg)")
    ax.set_ylabel("−S12/S11 (degree of linear polarization)")
    style_axes(ax)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("−S12/S11 at 100k vs 900k rays, 1° bins "
                 "(shaded: outside the 10–169° noise range)", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "rays_pol_100k_900k.png", dpi=150)
    plt.close(fig)


# ============================================================
# MAIN
# ============================================================

def main():

    PLOT_DIR.mkdir(exist_ok=True)
    results = {"1deg": {}}
    data = {c: load_count(c) for c in COUNTS}

    # 1. Noise per ray count, 1 deg bins
    for c in COUNTS:
        angle, s11, s12 = data[c]
        times = runtimes_minutes(c)
        results["1deg"][label(c)] = {
            "pol_noise": noise(in_range(pol(s11, s12))),
            "s11_rel_noise": relative_noise(in_range(s11)),
            "runtime_min_mean": float(np.mean(times)),
            "runtime_min_range": [float(min(times)), float(max(times))],
        }

    # 2. Cross-check: 3-run mean at each count vs the 900k 3-run mean.
    #    Expected RMS^2 = sigma_N^2/3 + sigma_900^2/3, so the implied
    #    single-run noise is sqrt(3 RMS^2 - sigma_900^2).
    ref_pol = in_range(pol(*data[REFERENCE_COUNT][1:])).mean(0)
    ref_s11 = in_range(data[REFERENCE_COUNT][1]).mean(0)
    sigma_ref = results["1deg"][label(REFERENCE_COUNT)]
    for c in COUNTS:
        if c == REFERENCE_COUNT:
            continue
        r = results["1deg"][label(c)]
        mean_pol = in_range(pol(*data[c][1:])).mean(0)
        mean_s11 = in_range(data[c][1]).mean(0)
        rms_pol = float(np.sqrt(np.mean((mean_pol - ref_pol) ** 2)))
        rms_s11 = float(np.sqrt(np.mean(((mean_s11 - ref_s11) / ref_s11) ** 2)))
        r["xcheck_pol_rms_mean_vs_900k"] = rms_pol
        r["xcheck_pol_implied_single_run"] = float(
            np.sqrt(max(3 * rms_pol**2 - sigma_ref["pol_noise"] ** 2, 0)))
        r["xcheck_s11_rel_rms_mean_vs_900k"] = rms_s11
        r["xcheck_s11_implied_single_run"] = float(
            np.sqrt(max(3 * rms_s11**2 - sigma_ref["s11_rel_noise"] ** 2, 0)))

    # 3. Fit noise vs N on log-log axes
    pol_n = [results["1deg"][label(c)]["pol_noise"] for c in COUNTS]
    s11_n = [results["1deg"][label(c)]["s11_rel_noise"] for c in COUNTS]
    pol_slope, pol_int = loglog_slope(COUNTS, pol_n)
    s11_slope, s11_int = loglog_slope(COUNTS, s11_n)
    results["fit"] = {
        "pol_slope": pol_slope,
        "pol_noise_at_1M_from_fit": float(10 ** (pol_int + pol_slope * 6)),
        "s11_slope": s11_slope,
        "expected_slope": -0.5,
    }

    # 4. Wider bins at 100k and 200k
    for width in WIDE_BINS:
        key = f"{width}deg"
        results[key] = {}
        for c in WIDE_BIN_COUNTS:
            _, s11w, s12w = rebin(*data[c], width)
            r = {"pol_noise": noise(pol(s11w, s12w)),
                 "s11_rel_noise": relative_noise(s11w),
                 "runtime_min_mean": results["1deg"][label(c)]["runtime_min_mean"]}
            r["pol_noise_ratio_vs_1deg"] = r["pol_noise"] / results["1deg"][label(c)]["pol_noise"]
            results[key][label(c)] = r

    # 5. Outputs
    (RAYS_DIR / "results.json").write_text(json.dumps(results, indent=2))
    write_markdown(results)
    plot_noise(results)
    plot_pol_curves()
    print((RAYS_DIR / "results.md").read_text())
    print("plots: sweeps/plots/rays_noise.png, sweeps/plots/rays_pol_100k_900k.png")


def write_markdown(results):

    lines = [
        "# Ray-count convergence results",
        "",
        "Baseline particle (σ 0.3, ν 4, l 2–10, GS seed 1), fayalite n = 1.85 + 0.00077i, "
        "size parameter 20. 3 runs per ray count with different ray seeds. "
        f"Noise = expected per-bin error of a single run over {FIRST_BIN}–{LAST_BIN}° "
        "(pooled across-seed variance), unsmoothed. Runtime = mean wall time per run "
        "with 4 runs in parallel on the M4 MacBook Air (solo: 8.4 min per 100k rays).",
        "",
        "| Setting | −S12/S11 noise | S11 relative noise | Runtime per run |",
        "|---|---|---|---|",
    ]
    rows = [(f"{label(c)} rays, 1° bins", results["1deg"][label(c)]) for c in COUNTS]
    rows += [(f"{label(c)} rays, {w}° bins", results[f"{w}deg"][label(c)])
             for c in WIDE_BIN_COUNTS for w in WIDE_BINS]
    for name, r in rows:
        lines.append(f"| {name} | {r['pol_noise']:.4f} | {100 * r['s11_rel_noise']:.1f}% "
                     f"| {r['runtime_min_mean']:.0f} min |")

    fit = results["fit"]
    lines += [
        "",
        f"Log-log fit, 1° bins: −S12/S11 noise slope {fit['pol_slope']:.3f}, "
        f"S11 relative noise slope {fit['s11_slope']:.3f} (ideal −0.5). "
        f"Earlier 100k estimate: {PREVIOUS_100K_NOISE}.",
        "",
        "Cross-check (mean of 3 runs vs mean of the 3 900k runs; "
        "implied single-run noise = √(3·RMS² − σ_900k²)):",
        "",
        "| Rays | −S12/S11 RMS vs 900k | implied single-run | S11 rel. RMS vs 900k | implied single-run |",
        "|---|---|---|---|---|",
    ]
    for c in COUNTS:
        if c == REFERENCE_COUNT:
            continue
        r = results["1deg"][label(c)]
        lines.append(f"| {label(c)} | {r['xcheck_pol_rms_mean_vs_900k']:.4f} "
                     f"| {r['xcheck_pol_implied_single_run']:.4f} "
                     f"| {100 * r['xcheck_s11_rel_rms_mean_vs_900k']:.1f}% "
                     f"| {100 * r['xcheck_s11_implied_single_run']:.1f}% |")
    lines += ["", "Wider bins, noise relative to 1° bins at the same ray count "
              "(ideal 1/√width: 2° → 0.71, 5° → 0.45):", ""]
    for w in WIDE_BINS:
        for c in WIDE_BIN_COUNTS:
            lines.append(f"- {label(c)}, {w}°: ×{results[f'{w}deg'][label(c)]['pol_noise_ratio_vs_1deg']:.2f}")
    (RAYS_DIR / "results.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
