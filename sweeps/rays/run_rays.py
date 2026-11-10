"""
Ray-count convergence sweep: run sirismp on the sweep-baseline particle at
several ray counts, several independent ray seeds per count.

Everything except `nrays` and `seed` is copied from sweeps/baseline/ (same
mesh, same input.in, same diffuse_pmatrix.in), so the only thing that changes
between runs is the Monte Carlo ray sample.

Each run gets its own folder sweeps/rays/<count>_seed<k>/ with its input files,
sirismp output, sirismp.log and params.json. params.json is written last, so
its presence means the run finished; rerunning the script skips those runs.

Usage (from anywhere):
    python3 sweeps/rays/run_rays.py              # run everything not yet done
    python3 sweeps/rays/run_rays.py 900k_seed1   # run only the named runs
    python3 sweeps/rays/run_rays.py --list       # show runs, seeds and status
    python3 sweeps/rays/run_rays.py --jobs 2     # change the number of parallel jobs

To survive closing the terminal (and stop the Mac idle-sleeping), launch with:
    nohup caffeinate -i python3 sweeps/rays/run_rays.py > sweeps/rays/run_rays.log 2>&1 &
"""

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

RAYS_DIR = Path(__file__).resolve().parent
REPO = RAYS_DIR.parent.parent
BASELINE_DIR = REPO / "sweeps" / "baseline"
SIRISMP_EXE = REPO / "multi-particle" / "sirismp"

# Files copied unchanged from the baseline run
COPY_FILES = ["mesh.off", "diffuse_pmatrix.in", "GS-input.in"]

# sirismp is single-threaded; the M4 Air has 4 performance cores
DEFAULT_JOBS = 4

# (folder name, nrays, ray seed). Every run has its own seed: sirismp draws
# random numbers in order from one stream, so reusing a seed at a different
# ray count would repeat the same first rays and correlate the two runs.
# 100k_seed1 uses 12345, the baseline seed, so it reproduces sweeps/baseline.
# Listed longest-first: the pool starts jobs in this order.
RUNS = [
    ("900k_seed1", 900_000, 12354),
    ("900k_seed2", 900_000, 12355),
    ("900k_seed3", 900_000, 12356),
    ("400k_seed1", 400_000, 12351),
    ("400k_seed2", 400_000, 12352),
    ("400k_seed3", 400_000, 12353),
    ("200k_seed1", 200_000, 12348),
    ("200k_seed2", 200_000, 12349),
    ("200k_seed3", 200_000, 12350),
    ("100k_seed1", 100_000, 12345),
    ("100k_seed2", 100_000, 12346),
    ("100k_seed3", 100_000, 12347),
]


# ============================================================
# HELPERS
# ============================================================

print_lock = threading.Lock()
running_lock = threading.Lock()
running = set()


def log(msg):

    with print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def sha256(path):

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_input(nrays, seed):
    """Baseline input.in with only the nrays and seed lines replaced."""

    lines = (BASELINE_DIR / "input.in").read_text().splitlines()
    replaced = {"nrays": 0, "seed": 0}
    for i, line in enumerate(lines):
        key = line.split()[0] if line.split() else ""
        if key == "nrays":
            lines[i] = f"nrays {nrays}"
            replaced["nrays"] += 1
        elif key == "seed":
            lines[i] = f"seed {seed}"
            replaced["seed"] += 1
    if replaced != {"nrays": 1, "seed": 1}:
        raise RuntimeError(f"baseline input.in has unexpected nrays/seed lines: {replaced}")
    return "\n".join(lines) + "\n"


def on_ac_power():

    out = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True).stdout
    return "AC Power" in out


def git_commit():

    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            cwd=REPO, capture_output=True, text=True)
    return result.stdout.strip()


def is_done(name):

    return (RAYS_DIR / name / "params.json").exists()


# ============================================================
# ONE RUN
# ============================================================

def run_one(name, nrays, seed, n_jobs):

    run_dir = RAYS_DIR / name
    run_dir.mkdir(exist_ok=True)

    for f in COPY_FILES:
        shutil.copy(BASELINE_DIR / f, run_dir / f)
    input_text = make_input(nrays, seed)
    (run_dir / "input.in").write_text(input_text)

    with running_lock:
        running.add(name)
        running_at_start = sorted(running)
    ac_at_start = on_ac_power()
    started = datetime.now()
    log(f"START  {name}  (nrays={nrays}, seed={seed}; running: {', '.join(running_at_start)})")

    t0 = time.perf_counter()
    with open(run_dir / "sirismp.log", "w") as out:
        proc = subprocess.run([str(SIRISMP_EXE), "input.in"], cwd=run_dir,
                              stdout=out, stderr=subprocess.STDOUT)
    seconds = time.perf_counter() - t0
    finished = datetime.now()

    with running_lock:
        running.discard(name)

    if proc.returncode != 0 or not (run_dir / "details.out").exists():
        log(f"FAILED {name}  exit code {proc.returncode} after {seconds / 60:.1f} min "
            f"(see {run_dir / 'sirismp.log'})")
        return

    # Written last: its presence marks the run as finished
    params = {
        "run": name,
        "nrays": nrays,
        "ray_seed": seed,
        "runtime_seconds": round(seconds, 1),
        "seconds_per_100k_rays": round(seconds / (nrays / 100_000), 1),
        "started": started.isoformat(timespec="seconds"),
        "finished": finished.isoformat(timespec="seconds"),
        "parallel_jobs_setting": n_jobs,
        "runs_in_progress_at_start": running_at_start,
        "on_ac_power_at_start": ac_at_start,
        "on_ac_power_at_end": on_ac_power(),
        "fixed_setup": {
            "copied_from": str(BASELINE_DIR.relative_to(REPO)),
            "gs": "sigma 0.3, power law 4, l_min 2, l_max 10, GS seed 1 (see GS-input.in)",
            "material": "fayalite n = 1.85 + 0.00077i, mesh_scale 20, wavelen 2*pi (size parameter 20)",
            "mesh_sha256": sha256(run_dir / "mesh.off"),
        },
        "sirismp_input": input_text,
        "sirismp_sha256": sha256(SIRISMP_EXE),
        "machine": f"{platform.node()} {platform.machine()} macOS {platform.mac_ver()[0]}",
        "git_commit": git_commit(),
    }
    (run_dir / "params.json").write_text(json.dumps(params, indent=2))
    log(f"DONE   {name}  {seconds / 60:.1f} min  ({params['seconds_per_100k_rays']} s per 100k rays)")


# ============================================================
# MAIN
# ============================================================

def main():

    args = sys.argv[1:]

    n_jobs = DEFAULT_JOBS
    if "--jobs" in args:
        i = args.index("--jobs")
        n_jobs = int(args[i + 1])
        del args[i:i + 2]

    if "--list" in args:
        for name, nrays, seed in RUNS:
            print(f"{name:12s} nrays={nrays:>7d} seed={seed}  {'done' if is_done(name) else '-'}")
        return

    by_name = {r[0]: r for r in RUNS}
    unknown = [a for a in args if a not in by_name]
    if unknown:
        sys.exit(f"Unknown run(s): {unknown}. Use --list.")
    todo = [by_name[a] for a in args] if args else [r for r in RUNS if not is_done(r[0])]

    log(f"{len(todo)} run(s) to do, {n_jobs} at a time: {', '.join(r[0] for r in todo)}")
    if not on_ac_power():
        log("WARNING: running on battery")

    with ThreadPoolExecutor(max_workers=n_jobs) as pool:
        futures = [pool.submit(run_one, name, nrays, seed, n_jobs) for name, nrays, seed in todo]
        for f in futures:
            f.result()   # re-raise any Python error (sirismp failures are only logged)

    log("All done.")


if __name__ == "__main__":
    main()
