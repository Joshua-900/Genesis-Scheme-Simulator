"""Screen compression-gated renewal before applying the object-level gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis_v1_compression_ablation import make_params
from src.genesis_grid import GenesisState, diagnostics, rules_alignment, rules_compression
from src.genesis_grid import rules_boundary_renewal, rules_curvature, rules_locking, step
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker


RULES = (
    rules_alignment.alignment_rule,
    rules_compression.compression_rule,
    rules_boundary_renewal.boundary_renewal_rule,
    rules_curvature.curvature_rule,
)


def run(seed: int, renewal: float, args) -> dict:
    np.random.seed(seed)
    state = GenesisState(args.N, dt=0.05)
    params = make_params(args.kappa)
    params.boundary_renewal = renewal
    defects, pairs = DefectTracker(), PairLineTracker(max_pair_distance=args.max_pair_distance)
    average = np.zeros((args.N, args.N), dtype=float)
    ages = {}
    for frame in range(1, args.frames + 1):
        step(state, params, RULES, post=rules_locking.locking_postprocess)
        if frame % args.sample_interval:
            continue
        plus, minus, _ = diagnostics.detect_vortices(state)
        detections = [(col, row, 1) for row, col in plus] + [(col, row, -1) for row, col in minus]
        compression = np.asarray(to_cpu(state.C))
        average = 0.95 * average + 0.05 * compression
        tracks = defects.update(frame, detections, C=compression, C_avg=average)
        for pair in pairs.update(frame=frame, defect_tracks=tracks, C=compression, C_avg=average):
            ages[pair.id] = max(ages.get(pair.id, 0), pair.age)
    values = list(ages.values())
    return {"seed": seed, "persistent_pairs": sum(age >= args.min_pair_age for age in values), "long_lived_pairs": sum(age >= args.long_pair_age for age in values), "median_pair_age": float(np.median(values)) if values else 0.0, "mean_compression": float(np.mean(to_cpu(state.C))), "mean_tension": float(np.mean(to_cpu(state.tau)))}


def main() -> None:
    parser = argparse.ArgumentParser(description="V1 boundary-renewal screen.")
    parser.add_argument("--strengths", type=float, nargs="+", default=(0.0, 0.10, 0.30, 0.60, 1.00))
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--kappa", type=float, default=0.10)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--min-pair-age", type=int, default=100)
    parser.add_argument("--long-pair-age", type=int, default=500)
    parser.add_argument("--output", type=Path, default=Path("results/v1_boundary_renewal_screen.json"))
    args = parser.parse_args()
    conditions = []
    for strength in args.strengths:
        runs = [run(seed, strength, args) for seed in range(args.seed_start, args.seed_start + args.seeds)]
        median = {key: float(np.median([item[key] for item in runs])) for key in runs[0] if key != "seed"}
        conditions.append({"boundary_renewal": strength, "runs": runs, "median": median})
        print(f"renewal={strength:g}: {json.dumps(median)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema_version": 1, "claim_boundary": "Regime screen only; no object claim.", "conditions": conditions}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
