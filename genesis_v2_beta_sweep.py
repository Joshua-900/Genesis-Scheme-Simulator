"""Small parameter-regime map for the rule-based Genesis v2-beta engine.

The sweep does not label patterns as objects. It separates three questions:
does a condition retain P/A distinction, retain spatial variation, and settle
into a stable late-time regime?
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta import BetaParams, BetaState, step, summary


METRICS = ("actual_order", "potential_strength", "potential_actual_alignment", "relation_mean", "availability_std", "neighbor_coherence")


def float_values(raw: str) -> list[float]:
    try:
        values = [float(value.strip()) for value in raw.split(",") if value.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected comma-separated numbers.") from exc
    if not values:
        raise argparse.ArgumentTypeError("Provide at least one value.")
    return values


def neighbor_coherence(state: BetaState) -> float:
    theta = np.asarray(to_cpu(state.theta))
    horizontal = np.cos(np.roll(theta, -1, axis=1) - theta)
    vertical = np.cos(np.roll(theta, -1, axis=0) - theta)
    return float(0.5 * (horizontal.mean() + vertical.mean()))


def run_one(N: int, frames: int, seed: int, log_interval: int, tail_fraction: float, params: BetaParams) -> dict:
    state = BetaState(N, seed=seed)
    series = []
    for frame in range(1, frames + 1):
        step(state, params)
        if frame % log_interval == 0 or frame == frames:
            series.append({"frame": frame, **summary(state), "neighbor_coherence": neighbor_coherence(state)})
    tail = series[max(0, int(len(series) * (1.0 - tail_fraction))):] or series
    return {
        "seed": seed,
        "tail": {metric: {"mean": statistics.mean(row[metric] for row in tail), "std": statistics.pstdev(row[metric] for row in tail)} for metric in METRICS},
    }


def aggregate(runs: list[dict]) -> dict[str, dict[str, float]]:
    return {
        metric: {
            "tail_mean_across_seeds": statistics.mean(run["tail"][metric]["mean"] for run in runs),
            "tail_mean_std_across_seeds": statistics.pstdev(run["tail"][metric]["mean"] for run in runs),
            "tail_temporal_std_mean": statistics.mean(run["tail"][metric]["std"] for run in runs),
        }
        for metric in METRICS
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Map beta regimes without assuming objects or emergence.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--log-interval", type=int, default=20)
    parser.add_argument("--tail-fraction", type=float, default=0.25)
    parser.add_argument("--potential-to-actual", default="0.05,0.20,0.45")
    parser.add_argument("--relation-difference-gain", default="0.20,0.55,0.90")
    parser.add_argument("--output", type=Path, default=Path("results/v2_beta_regime_map.json"))
    args = parser.parse_args()
    p_to_a_values = float_values(args.potential_to_actual)
    relation_values = float_values(args.relation_difference_gain)
    if args.N < 2 or args.frames < 1 or args.seeds < 1 or args.log_interval < 1 or not 0.0 < args.tail_fraction <= 1.0:
        raise SystemExit("Invalid sweep arguments.")

    conditions = []
    for p_to_a in p_to_a_values:
        for relation_gain in relation_values:
            params = BetaParams(potential_to_actual=p_to_a, relation_difference_gain=relation_gain)
            runs = [run_one(args.N, args.frames, seed, args.log_interval, args.tail_fraction, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
            totals = aggregate(runs)
            conditions.append({"params": asdict(params), "runs": runs, "aggregate": totals})
            print(
                f"P->A={p_to_a:.2f}, relation={relation_gain:.2f}: "
                f"alignment={totals['potential_actual_alignment']['tail_mean_across_seeds']:.3f}; "
                f"neighbor coherence={totals['neighbor_coherence']['tail_mean_across_seeds']:.3f}; "
                f"availability std={totals['availability_std']['tail_mean_across_seeds']:.3f}"
            )

    report = {
        "schema_version": 1,
        "claim_boundary": "This is a parameter characterization of beta. It does not identify objects or validate a metaphysical claim.",
        "config": {"N": args.N, "frames": args.frames, "seeds": list(range(args.seed_start, args.seed_start + args.seeds)), "log_interval": args.log_interval, "tail_fraction": args.tail_fraction, "potential_to_actual": p_to_a_values, "relation_difference_gain": relation_values},
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote beta regime map to {args.output}")


if __name__ == "__main__":
    main()
