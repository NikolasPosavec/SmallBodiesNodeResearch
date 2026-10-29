"""
One-parameter-at-a-time sweep of Gaussian-sphere shape parameters.

For each variant: write a GS input, generate the shape(s) with GS, run sirismp
on each shape, and log every parameter to params.json in the run folder.

Usage (from the repo root):
    python3 sweeps/run_sweep.py               # run everything not yet done
    python3 sweeps/run_sweep.py baseline      # run only the named runs
    python3 sweeps/run_sweep.py --list        # show run names and status
"""

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

REPO = Path(__file__).resolve().parent.parent
SWEEP_DIR = REPO / "sweeps"

GS_EXE = REPO / "GS" / "GS"
SIRISMP_EXE = REPO / "multi-particle" / "sirismp"

# Diffuse-scatterer phase matrix: Danielle's original 81-row input,
# recovered from git (the committed example/outputS.out was overwritten)
DIFFUSE_PMATRIX = SWEEP_DIR / "diffuse_pmatrix.in"
DIFFUSE_PMATRIX_GIT = "c5439cea:multi-particle/example/outputS.out"

# Baseline shape (tests/GS-input.in); every run changes one of these
BASELINE_GS = {
    "n_shapes": 1,
    "seed": 1,
    "sigma": 0.3,
    "power_law": 4,
    "l_min": 2,
    "l_max": 10,
    "rows_per_octant": 30,
}

# sirismp settings from Danielle's *_20 batch runs, material = fayalite
# (example/input.in). Material line order is: n k diffuse MFP ALBEDO pmatrix
# use_distribution dist_file (see multi-particle/smaterial.hpp), so this is
# MFP = 1.0, albedo = 0.946. The distribution file does not exist (and "~" is
# not expanded), which is kept on purpose to match her runs.
NRAYS = 100000
SIRISMP_SEED = 12345
MESH_SCALE = 20
REF_REAL = 1.85
REF_IMAG = 0.00077
MATERIAL_TAIL = "1 1.0 0.946029056271191 diffuse_pmatrix.in 1 ~/dists/cdfconstant04dist.txt"


# ============================================================
# RUNS
# ============================================================

# name -> changes from BASELINE_GS. The baseline is shared by the power-law,
# l_min and l_max sweeps. N = 5/10/20 are averages over the first N shapes of
# n_particles_20 (same seed, so the first 5 shapes are what N = 5 would give).
RUNS = {
    "baseline": {},
    "power_law_2": {"power_law": 2},
    "power_law_6": {"power_law": 6},
    "l_min_1": {"l_min": 1},
    "l_min_3": {"l_min": 3},
    "l_max_5": {"l_max": 5},
    "l_max_30": {"l_max": 30},
    "n_particles_20": {"n_shapes": 20},
}


# ============================================================
# HELPERS
# ============================================================

def write_gs_input(workdir, gs):

    text = f"""
INPUT FILE for Gaussian spheres (siris4-framework)

{gs['n_shapes']}               ! Number of Gaussian spheres.
{gs['seed']}               ! Seed for the random number generator. Non-positive number for random seed.
{gs['sigma']}             ! Relative standard deviation of radial distance.
{gs['power_law']}               ! Power law index for correlation. Increase for irregular shape.
{gs['l_min']}               ! Minimum degree in correlation series. Increase for rough shape.
{gs['l_max']}              ! Maximum degree in correlation series. Increase for rough shape.
{gs['rows_per_octant']}              ! Discretization: number of triangle rows per octant.
! Next line, prefix for output files.
shape
0               ! Output in Matlab format. 0 for no, 1 for yes.
0               ! Output for IDL format.
0               ! Output in VTK format
1               ! Output in OFF format
1               ! Output in OBJ format
"""

    (workdir / "GS-input.in").write_text(text)


def write_sirismp_input(workdir, mesh_name):

    text = f"""nrays {NRAYS}
max_scattering 200
killswitch_start 70
nbins 180
I_cutoff_limit 0.0000001
seed {SIRISMP_SEED}
wavelen 6.283185307179586
mesh_scale {MESH_SCALE}
mesh {mesh_name}
force_interaction 1
beam_radius -1
material1 {REF_REAL} {REF_IMAG} {MATERIAL_TAIL}
output_file outputS.out
pmatrix_out pmatrix.out
details_out details.out
"""

    (workdir / "input.in").write_text(text)
    return text


def run_sirismp(workdir, mesh_path):

    workdir.mkdir(exist_ok=True)
    shutil.copy(mesh_path, workdir / "mesh.off")
    shutil.copy(DIFFUSE_PMATRIX, workdir / DIFFUSE_PMATRIX.name)
    input_text = write_sirismp_input(workdir, "mesh.off")

    start = time.time()
    with open(workdir / "sirismp.log", "w") as log:
        subprocess.run([str(SIRISMP_EXE), "input.in"], cwd=workdir,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    return input_text, time.time() - start


def git_commit():

    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            cwd=REPO, capture_output=True, text=True)
    return result.stdout.strip()


def is_done(name):

    return (SWEEP_DIR / name / "params.json").exists()


# ============================================================
# MAIN
# ============================================================

def run_one(name):

    gs = {**BASELINE_GS, **RUNS[name]}
    run_dir = SWEEP_DIR / name
    run_dir.mkdir(exist_ok=True)

    # 1. Shapes
    write_gs_input(run_dir, gs)
    subprocess.run([str(GS_EXE), "GS-input.in"], cwd=run_dir, check=True,
                   stdout=subprocess.DEVNULL)

    # GS names the file "shape.off" for one shape, "shape1.off".. for several
    if gs["n_shapes"] == 1:
        meshes = {run_dir: run_dir / "shape.off"}
    else:
        meshes = {run_dir / f"shape_{i:02d}": run_dir / f"shape{i}.off"
                  for i in range(1, gs["n_shapes"] + 1)}

    # 2. Scattering, one sirismp run per shape
    timings = {}
    input_text = write_sirismp_input(run_dir, "mesh.off")
    for workdir, mesh in meshes.items():
        if (workdir / "details.out").exists() and workdir != run_dir:
            print(f"  {workdir.name}: already done, skipping")
            continue
        print(f"  sirismp on {mesh.name} ...", flush=True)
        input_text, seconds = run_sirismp(workdir, mesh)
        timings[workdir.name] = round(seconds, 1)
        print(f"    done in {seconds / 60:.1f} min")

    # 3. Log (written last, so its presence means the run finished)
    params = {
        "run": name,
        "changed": RUNS[name],
        "gs": gs,
        "sirismp_input": input_text,
        "sirismp_seconds": timings,
        "git_commit": git_commit(),
        "finished": datetime.now().isoformat(timespec="seconds"),
    }
    (run_dir / "params.json").write_text(json.dumps(params, indent=2))


def main():

    args = sys.argv[1:]

    if "--list" in args:
        for name in RUNS:
            print(f"{name:16s} {'done' if is_done(name) else '-'}")
        return

    names = args or [n for n in RUNS if not is_done(n)]
    unknown = [n for n in names if n not in RUNS]
    if unknown:
        sys.exit(f"Unknown run(s): {unknown}. Use --list.")

    if not DIFFUSE_PMATRIX.exists():
        text = subprocess.run(["git", "show", DIFFUSE_PMATRIX_GIT], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout
        DIFFUSE_PMATRIX.write_text(text)

    for name in names:
        print(f"\n=== {name} ===")
        run_one(name)

    print("\nDone.")


if __name__ == "__main__":
    main()
