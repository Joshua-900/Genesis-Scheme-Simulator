"""Headless baseline measurement harness for the experimental v2 engine.

This deliberately measures v2 before adding a visual layer or object detector.
It reports the independent P/A/R observables over time and their late-run
statistics across seeded, unperturbed runs.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from src.genesis_v2 import V2Params, V2State, step, summary


METRICS = ("actual_order", "potential_strength", "potential_actual_alignment", "relation_mean")


def tail_summary(series: list[dict], tail_fraction: float) -> dict[str, dict[str, float]]:
    start = max(0, int(len(series) * (1.0 - tail_fraction)))
    tail = series[start:] or series
    return {
        metric: {
            "mean": statistics.mean(point[metric] for point in tail),
            "std": statistics.pstdev(point[metric] for point in tail),
        }
        for metric in METRICS
    }


def run_one(N: int, frames: int, seed: int, log_interval: int, tail_fraction: float) -> dict:
    state = V2State(N, seed=seed)
    params = V2Params()
    series = []
    for frame in range(1, frames + 1):
        step(state, params)
        if frame % log_interval == 0 or frame == frames:
            series.append({"frame": frame, **summary(state)})
    return {"seed": seed, "series": series, "tail": tail_summary(series, tail_fraction)}


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
    parser = argparse.ArgumentParser(description="Measure the unperturbed Genesis v2 P/A/R baseline.")
    parser.add_argument("--N", type=int, default=64, help="Square-grid side length.")
    parser.add_argument("--frames", type=int, default=2_000, help="Frames per seed.")
    parser.add_argument("--seeds", type=int, default=5, help="Number of sequential deterministic seeds.")
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--log-interval", type=int, default=20)
    parser.add_argument("--tail-fraction", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=Path("results/v2_baseline.json"))
    args = parser.parse_args()
    if args.N < 2 or args.frames < 1 or args.seeds < 1 or args.log_interval < 1:
        raise SystemExit("N, frames, seeds, and log interval must be positive (N >= 2).")
    if not 0.0 < args.tail_fraction <= 1.0:
        raise SystemExit("--tail-fraction must be in (0, 1].")

    runs = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        run = run_one(args.N, args.frames, seed, args.log_interval, args.tail_fraction)
        runs.append(run)
        print(
            f"seed={seed}: order={run['tail']['actual_order']['mean']:.4f}; "
            f"P strength={run['tail']['potential_strength']['mean']:.4f}; "
            f"P/A alignment={run['tail']['potential_actual_alignment']['mean']:.4f}; "
            f"R={run['tail']['relation_mean']['mean']:.4f}"
        )

    report = {
        "schema_version": 1,
        "claim_boundary": "This characterizes the unperturbed v2 prototype. It does not establish object formation, v1 superiority, or metaphysical validity.",
        "config": {
            "N": args.N,
            "frames": args.frames,
            "seeds": list(range(args.seed_start, args.seed_start + args.seeds)),
            "log_interval": args.log_interval,
            "tail_fraction": args.tail_fraction,
            "params": vars(V2Params()),
        },
        "aggregate": aggregate(runs),
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2 baseline report to {args.output}")


if __name__ == "__main__":
    main()
