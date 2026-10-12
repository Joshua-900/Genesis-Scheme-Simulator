"""Causal ablation of V1 geometry/compression for tracked pair candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_grid import GenesisParams, GenesisState, diagnostics, rules_locking, step
from src.genesis_grid import rules_alignment, rules_compression, rules_curvature
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker


RULES = (rules_alignment.alignment_rule, rules_compression.compression_rule, rules_curvature.curvature_rule)


def make_params(kappa: float) -> GenesisParams:
    params = GenesisParams()
    params.alpha = 0.30
    params.gamma = 0.01
    params.kappa = kappa
    params.curv = 0.04
    params.phase = 0.0
    params.dipole = 0.0
    params.triads = 0.0
    params.lock_strength = 0.96
    params.phase_lock_gain = 0.0
    params.tri_lock_gain = 0.0
    params.shell_geom_gain = 0.08
    return params


def run_kappa(kappa: float, args: argparse.Namespace) -> dict:
    runs = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        np.random.seed(seed)
        state = GenesisState(args.N, dt=0.05)
        params = make_params(kappa)
        defects = DefectTracker()
        pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
        compression_average = np.zeros((args.N, args.N), dtype=np.float64)
        pair_max_ages: dict[int, int] = {}
        pair_compression: dict[int, list[float]] = {}

        for frame in range(1, args.frames + 1):
            step(state, params, RULES, post=rules_locking.locking_postprocess)
            if frame % args.sample_interval:
                continue

            plus, minus, _ = diagnostics.detect_vortices(state)
            detections = [(col, row, 1) for row, col in plus] + [(col, row, -1) for row, col in minus]
            compression = np.asarray(to_cpu(state.C), dtype=np.float64)
            compression_average = 0.95 * compression_average + 0.05 * compression
            tracks = defects.update(frame, detections, C=compression, C_avg=compression_average)
            for pair in pairs.update(frame=frame, defect_tracks=tracks, C=compression, C_avg=compression_average):
                pair_max_ages[pair.id] = max(pair_max_ages.get(pair.id, 0), pair.age)
                pair_compression.setdefault(pair.id, []).append(pair.mean_C_avg_along_line)

        persistent = [age for age in pair_max_ages.values() if age >= args.min_pair_age]
        pair_c = [float(np.mean(values)) for values in pair_compression.values() if values]
        result = {
            "seed": seed,
            "mean_tension": float(np.mean(to_cpu(state.tau))),
            "mean_compression": float(np.mean(to_cpu(state.C))),
            "pair_candidates_observed": len(pair_max_ages),
            "persistent_pair_candidates": len(persistent),
            "median_pair_max_age": float(np.median(list(pair_max_ages.values()))) if pair_max_ages else 0.0,
            "mean_pair_compression": float(np.mean(pair_c)) if pair_c else 0.0,
        }
        runs.append(result)
        print(f"kappa={kappa:g} seed={seed}: C={result['mean_compression']:.6f}, persistent={result['persistent_pair_candidates']}")

    keys = ("mean_tension", "mean_compression", "pair_candidates_observed", "persistent_pair_candidates", "median_pair_max_age", "mean_pair_compression")
    return {
        "kappa": kappa,
        "runs": runs,
        "median_final": {key: float(np.median([run[key] for run in runs])) for key in keys},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ablate V1 geometry coupling while tracking pair candidates.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--min-pair-age", type=int, default=100)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--kappas", type=float, nargs="+", default=[0.0, 0.025, 0.05, 0.1])
    parser.add_argument("--output", type=Path, default=Path("results/v1_compression_ablation.json"))
    args = parser.parse_args()
    if args.N < 4 or args.frames < 1 or args.seeds < 1 or args.sample_interval < 1:
        raise SystemExit("--N >= 4 and --frames, --seeds, --sample-interval must be positive.")
    if any(kappa < 0.0 for kappa in args.kappas):
        raise SystemExit("--kappas must be non-negative.")

    conditions = [run_kappa(kappa, args) for kappa in args.kappas]
    output = {
        "schema_version": 1,
        "claim_boundary": "This tests the causal role of the specified V1 geometry/compression path in tracked pair candidates; it does not establish objects.",
        "experiment": {
            "name": "v1_geometry_compression_ablation",
            "question": "Does V1 geometry coupling causally change pair-candidate persistence?",
            "grid_size": args.N,
            "frames": args.frames,
            "seeds": args.seeds,
            "kappas": args.kappas,
        },
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
