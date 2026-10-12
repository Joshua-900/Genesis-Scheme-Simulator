"""Test whether remembered relational incompatibility changes V1 candidates.

This is the second causal link in the V1-derived V2 bridge.  It compares the
first P-to-A bridge condition with the same condition plus edge relation memory
feeding structural tension.  The existing vortex-pair tracker is read-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis_v2_integrated_probe import configure_potential_influence, configure_v1_substrate
from src.genesis_grid import diagnostics
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker
from src.genesis_v2_integrated import IntegratedParams, IntegratedState, step


def configure_relation_memory(params: IntegratedParams, tension: float = 0.20) -> None:
    """Add one causal link: remembered edge incompatibility feeds tension."""
    params.relation_memory_rate = 0.30
    params.relation_memory_decay = 0.05
    params.relation_memory_tension = tension


def run_condition(name: str, args: argparse.Namespace, relation_memory_tension: float = 0.0) -> dict:
    runs: list[dict] = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        state = IntegratedState(args.N, seed=seed)
        params = IntegratedParams()
        configure_v1_substrate(params)
        configure_potential_influence(params)
        if relation_memory_tension:
            configure_relation_memory(params, relation_memory_tension)

        defects = DefectTracker()
        pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
        compression_average = np.zeros((args.N, args.N), dtype=np.float64)
        pair_max_ages: dict[int, int] = {}
        pair_compression: dict[int, list[float]] = {}

        for frame in range(1, args.frames + 1):
            step(state, params)
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
        mean_pair_compression = [float(np.mean(values)) for values in pair_compression.values() if values]
        theta = np.asarray(to_cpu(state.theta))
        p_angle = np.arctan2(np.asarray(to_cpu(state.py)), np.asarray(to_cpu(state.px)))
        result = {
            "seed": seed,
            "potential_actual_alignment": float(np.mean(np.cos(theta - p_angle))),
            "actual_order": float(np.hypot(np.mean(np.cos(theta)), np.mean(np.sin(theta)))),
            "mean_tension": float(np.mean(to_cpu(state.tau))),
            "mean_compression": float(np.mean(to_cpu(state.C))),
            "mean_relation_memory": float(0.5 * (np.mean(to_cpu(state.rx)) + np.mean(to_cpu(state.ry)))),
            "pair_candidates_observed": len(pair_max_ages),
            "persistent_pair_candidates": len(persistent),
            "median_pair_max_age": float(np.median(list(pair_max_ages.values()))) if pair_max_ages else 0.0,
            "mean_pair_compression": float(np.mean(mean_pair_compression)) if mean_pair_compression else 0.0,
        }
        runs.append(result)
        print(
            f"{name} seed={seed}: R={result['mean_relation_memory']:.3f}, "
            f"tau={result['mean_tension']:.3f}, persistent={result['persistent_pair_candidates']}"
        )

    keys = (
        "potential_actual_alignment", "actual_order", "mean_tension", "mean_compression", "mean_relation_memory",
        "pair_candidates_observed", "persistent_pair_candidates", "median_pair_max_age", "mean_pair_compression",
    )
    median = {key: float(np.median([run[key] for run in runs])) for key in keys}
    return {"condition": name, "parameters": vars(params), "runs": runs, "median_final": median}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the P-to-A bridge with and without relation-memory tension.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--min-pair-age", type=int, default=100)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--relation-memory-tension", type=float, default=0.20)
    parser.add_argument("--output", type=Path, default=Path("results/v2_integrated_relation_probe.json"))
    args = parser.parse_args()
    if args.N < 4 or args.frames < 1 or args.seeds < 1 or args.sample_interval < 1:
        raise SystemExit("--N >= 4 and --frames, --seeds, --sample-interval must be positive.")

    baseline = run_condition("p_to_a_bridge", args)
    memory = run_condition("p_to_a_plus_relation_memory", args, relation_memory_tension=args.relation_memory_tension)
    output = {
        "schema_version": 1,
        "claim_boundary": "This measures a single structural-memory intervention and tracked pair candidates, not higher-order objects.",
        "experiment": {
            "name": "v2_integrated_relation_memory_probe",
            "question": "Does remembered edge incompatibility alter candidate persistence or compression context without P/A collapse?",
            "grid_size": args.N,
            "frames": args.frames,
            "seeds": args.seeds,
            "sampling": {"interval": args.sample_interval, "persistent_pair_age": args.min_pair_age},
        },
        "conditions": [baseline, memory],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
