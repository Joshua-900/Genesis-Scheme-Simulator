"""Headless baseline measurement for the rule-based Genesis v2-beta engine."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from src.genesis_v2_beta import BetaParams, BetaState, step, summary


METRICS = ("actual_order", "potential_strength", "potential_actual_alignment", "relation_mean", "availability_std")


def run_one(N: int, frames: int, seed: int, log_interval: int, tail_fraction: float) -> dict:
    state, params = BetaState(N, seed=seed), BetaParams()
    series = []
    for frame in range(1, frames + 1):
        step(state, params)
        if frame % log_interval == 0 or frame == frames:
            series.append({"frame": frame, **summary(state)})
    tail = series[max(0, int(len(series) * (1.0 - tail_fraction))):] or series
    return {
        "seed": seed,
        "series": series,
        "tail": {metric: {"mean": statistics.mean(row[metric] for row in tail), "std": statistics.pstdev(row[metric] for row in tail)} for metric in METRICS},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the unperturbed rule-based Genesis v2-beta baseline.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--log-interval", type=int, default=20)
    parser.add_argument("--tail-fraction", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=Path("results/v2_beta_baseline.json"))
    args = parser.parse_args()
    if args.N < 2 or args.frames < 1 or args.seeds < 1 or args.log_interval < 1 or not 0.0 < args.tail_fraction <= 1.0:
        raise SystemExit("Invalid baseline arguments.")
    runs = [run_one(args.N, args.frames, seed, args.log_interval, args.tail_fraction) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    aggregate = {
        metric: {
            "tail_mean_across_seeds": statistics.mean(run["tail"][metric]["mean"] for run in runs),
            "tail_mean_std_across_seeds": statistics.pstdev(run["tail"][metric]["mean"] for run in runs),
            "tail_temporal_std_mean": statistics.mean(run["tail"][metric]["std"] for run in runs),
        }
        for metric in METRICS
    }
    for run in runs:
        print(f"seed={run['seed']}: alignment={run['tail']['potential_actual_alignment']['mean']:.4f}; availability={run['tail']['potential_strength']['mean']:.4f}; relation={run['tail']['relation_mean']['mean']:.4f}")
    report = {"schema_version": 1, "claim_boundary": "This characterizes the beta prototype; it does not establish object formation or metaphysical validity.", "config": {"N": args.N, "frames": args.frames, "seeds": list(range(args.seed_start, args.seed_start + args.seeds)), "params": vars(BetaParams())}, "aggregate": aggregate, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-beta baseline report to {args.output}")


if __name__ == "__main__":
    main()
