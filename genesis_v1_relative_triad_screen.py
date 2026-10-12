"""Screen V1's existing rotationally invariant relative-triad pathway."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_grid import GenesisState, diagnostics, rules_alignment, rules_compression
from src.genesis_grid import rules_curvature, rules_locking, rules_triads_relative, step
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker
from genesis_v1_compression_ablation import make_params


RULES = (
    rules_alignment.alignment_rule,
    rules_compression.compression_rule,
    rules_triads_relative.triad_relative_rule,
    rules_curvature.curvature_rule,
)


def run(seed: int, triads: float, lock_gain: float, args) -> dict:
    np.random.seed(seed)
    state = GenesisState(args.N, dt=0.05)
    params = make_params(args.kappa)
    params.triads = triads
    params.tri_lock_gain = lock_gain
    defects = DefectTracker()
    pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
    compression_average = np.zeros((args.N, args.N), dtype=float)
    max_ages = {}
    for frame in range(1, args.frames + 1):
        step(state, params, RULES, post=rules_locking.locking_postprocess)
        if frame % args.sample_interval:
            continue
        plus, minus, _ = diagnostics.detect_vortices(state)
        detections = [(col, row, 1) for row, col in plus] + [(col, row, -1) for row, col in minus]
        compression = np.asarray(to_cpu(state.C))
        compression_average = 0.95 * compression_average + 0.05 * compression
        tracks = defects.update(frame, detections, C=compression, C_avg=compression_average)
        for pair in pairs.update(
            frame=frame,
            defect_tracks=tracks,
            C=compression,
            C_avg=compression_average,
        ):
            max_ages[pair.id] = max(max_ages.get(pair.id, 0), pair.age)
    ages = list(max_ages.values())
    return {
        "seed": seed,
        "mean_tension": float(np.mean(to_cpu(state.tau))),
        "mean_compression": float(np.mean(to_cpu(state.C))),
        "global_order": float(np.hypot(np.mean(np.cos(to_cpu(state.theta))), np.mean(np.sin(to_cpu(state.theta))))),
        "pair_count": len(ages),
        "persistent_pairs": sum(age >= args.min_pair_age for age in ages),
        "long_lived_pairs": sum(age >= args.long_pair_age for age in ages),
        "median_pair_age": float(np.median(ages)) if ages else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen relative-triad V1 regimes before object testing.")
    parser.add_argument("--triads", type=float, nargs="+", default=(0.0, 0.05, 0.10, 0.20))
    parser.add_argument("--lock-gains", type=float, nargs="+", default=(0.0, 1.0))
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--kappa", type=float, default=0.10)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--min-pair-age", type=int, default=100)
    parser.add_argument("--long-pair-age", type=int, default=500)
    parser.add_argument("--output", type=Path, default=Path("results/v1_relative_triad_screen.json"))
    args = parser.parse_args()
    conditions = []
    for triads in args.triads:
        for lock_gain in args.lock_gains:
            if triads == 0.0 and lock_gain != 0.0:
                continue
            runs = [run(seed, triads, lock_gain, args) for seed in range(args.seed_start, args.seed_start + args.seeds)]
            keys = tuple(key for key in runs[0] if key != "seed")
            median = {key: float(np.median([item[key] for item in runs])) for key in keys}
            conditions.append({"triads": triads, "tri_lock_gain": lock_gain, "runs": runs, "median": median})
            print(f"triads={triads:g}, tri_lock={lock_gain:g}: {json.dumps(median)}")
    report = {"schema_version": 1, "claim_boundary": "Regime screen only; candidate counts do not establish higher-order objects.", "conditions": conditions}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
