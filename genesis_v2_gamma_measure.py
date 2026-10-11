"""Headless baseline measurement for the boundary-forming Genesis v2-gamma hypothesis."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_gamma import GammaParams, GammaState, step, summary


METRICS = ("actual_order", "potential_strength", "potential_actual_alignment", "relation_mean", "availability_std", "boundary_mean", "boundary_std")


def observe(state: GammaState) -> dict[str, float]:
    report = summary(state)
    boundary = np.concatenate((np.asarray(to_cpu(state.boundary_x)).ravel(), np.asarray(to_cpu(state.boundary_y)).ravel()))
    report["boundary_mean"] = float(np.mean(boundary))
    report["boundary_std"] = float(np.std(boundary))
    return report


def run_one(N: int, frames: int, seed: int, log_interval: int, tail_fraction: float, params: GammaParams) -> dict:
    state = GammaState(N, seed=seed)
    series = []
    for frame in range(1, frames + 1):
        step(state, params)
        if frame % log_interval == 0 or frame == frames:
            series.append({"frame": frame, **observe(state)})
    tail = series[max(0, int(len(series) * (1.0 - tail_fraction))):] or series
    return {"seed": seed, "series": series, "tail": {metric: {"mean": statistics.mean(row[metric] for row in tail), "std": statistics.pstdev(row[metric] for row in tail)} for metric in METRICS}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the unperturbed v2-gamma boundary hypothesis.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--log-interval", type=int, default=20)
    parser.add_argument("--tail-fraction", type=float, default=0.25)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_baseline.json"))
    args = parser.parse_args()
    if args.N < 2 or args.frames < 1 or args.seeds < 1 or args.log_interval < 1 or not 0.0 < args.tail_fraction <= 1.0:
        raise SystemExit("Invalid baseline arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    runs = [run_one(args.N, args.frames, seed, args.log_interval, args.tail_fraction, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    aggregate = {metric: {"tail_mean_across_seeds": statistics.mean(run["tail"][metric]["mean"] for run in runs), "tail_mean_std_across_seeds": statistics.pstdev(run["tail"][metric]["mean"] for run in runs)} for metric in METRICS}
    for run in runs:
        print(f"seed={run['seed']}: P/A={run['tail']['potential_actual_alignment']['mean']:.4f}; boundary={run['tail']['boundary_mean']['mean']:.4f} +/- {run['tail']['boundary_std']['mean']:.4f}")
    report = {"schema_version": 1, "claim_boundary": "This measures the gamma boundary mechanism. It does not establish bounded objects, autonomy, or metaphysical validity.", "config": {"N": args.N, "frames": args.frames, "seeds": list(range(args.seed_start, args.seed_start + args.seeds)), "params": vars(params)}, "aggregate": aggregate, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma baseline report to {args.output}")


if __name__ == "__main__":
    main()
