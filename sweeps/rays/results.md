# Ray-count convergence results

Baseline particle (σ 0.3, ν 4, l 2–10, GS seed 1), fayalite n = 1.85 + 0.00077i, size parameter 20. 3 runs per ray count with different ray seeds. Noise = expected per-bin error of a single run over 10–169° (pooled across-seed variance), unsmoothed. Runtime = mean wall time per run with 4 runs in parallel on the M4 MacBook Air (solo: 8.4 min per 100k rays).

| Setting | −S12/S11 noise | S11 relative noise | Runtime per run |
|---|---|---|---|
| 100k rays, 1° bins | 0.0153 | 7.4% | 12 min |
| 200k rays, 1° bins | 0.0117 | 4.7% | 25 min |
| 400k rays, 1° bins | 0.0075 | 3.4% | 46 min |
| 900k rays, 1° bins | 0.0047 | 2.3% | 100 min |
| 100k rays, 2° bins | 0.0104 | 5.1% | 12 min |
| 100k rays, 5° bins | 0.0069 | 3.5% | 12 min |
| 200k rays, 2° bins | 0.0082 | 3.1% | 25 min |
| 200k rays, 5° bins | 0.0050 | 2.1% | 25 min |

Log-log fit, 1° bins: −S12/S11 noise slope -0.544, S11 relative noise slope -0.527 (ideal −0.5). Earlier 100k estimate: 0.015.

Cross-check (mean of 3 runs vs mean of the 3 900k runs; implied single-run noise = √(3·RMS² − σ_900k²)):

| Rays | −S12/S11 RMS vs 900k | implied single-run | S11 rel. RMS vs 900k | implied single-run |
|---|---|---|---|---|
| 100k | 0.0101 | 0.0168 | 3.9% | 6.3% |
| 200k | 0.0068 | 0.0107 | 3.3% | 5.2% |
| 400k | 0.0048 | 0.0068 | 2.0% | 2.7% |

Wider bins, noise relative to 1° bins at the same ray count (ideal 1/√width: 2° → 0.71, 5° → 0.45):

- 100k, 2°: ×0.68
- 200k, 2°: ×0.70
- 100k, 5°: ×0.45
- 200k, 5°: ×0.43
