"""Predeclared P-to-A coupling-strength dose response on the V1-derived bridge."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from genesis_v1_local_structure_perturbation import choose_background, disk_mask, select_candidate, weaken_structure
from genesis_v2_integrated_high_compression_audit import observe
from genesis_v2_integrated_local_structure_probe import follow, make_params, update
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker
from src.genesis_v2_integrated import IntegratedState, step


def params_for_gain(gain: float):
    """Keep the high-compression V1 substrate fixed while varying only P-to-A."""
    params = make_params(False)
    params.potential_transport = 0.03
    params.potential_source_restore = 0.10
    params.potential_to_actual = gain
    return params


def run_field_seed(seed: int, gain: float, args) -> dict:
    state = IntegratedState(args.N, seed=seed)
    params = params_for_gain(gain)
    for _ in range(args.field_frames):
        step(state, params)
    return observe(state)


def run_local_seed(seed: int, gain: float, args) -> dict:
    state = IntegratedState(args.N, dt=0.05, seed=seed)
    params = params_for_gain(gain)
    defects = DefectTracker()
    pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
    compression_average = np.zeros((args.N, args.N), dtype=np.float64)
    active = []

    for frame in range(1, args.burn_in_frames + 1):
        step(state, params)
        if frame % args.sample_interval == 0:
            active, compression_average = update(state, frame, defects, pairs, compression_average)

    candidate = select_candidate(active)
    if candidate is None:
        return {"seed": seed, "status": "no_candidate"}

    key = (candidate.plus_id, candidate.minus_id)
    background_x, background_y = choose_background(args.N, candidate, args.radius, seed)
    masks = {
        "untouched": None,
        "candidate_neighborhood": disk_mask(args.N, candidate.midpoint_x, candidate.midpoint_y, args.radius),
        "background": disk_mask(args.N, background_x, background_y, args.radius),
    }
    branches = {}
    for name, mask in masks.items():
        branch_state = copy.deepcopy(state)
        if mask is not None:
            weaken_structure(branch_state, mask, args.weaken_strength)
        branches[name] = follow(
            branch_state,
            params,
            copy.deepcopy(defects),
            copy.deepcopy(pairs),
            compression_average.copy(),
            key,
            args.burn_in_frames,
            args,
        )
    return {"seed": seed, "status": "tested", "branches": branches}


def field_summary(runs: list[dict]) -> dict:
    metrics = runs[0]["observation"] if runs else {}
    return {
        metric: float(np.median([run["observation"][metric] for run in runs]))
        for metric in metrics
    }


def local_summary(runs: list[dict]) -> dict:
    tested = [run for run in runs if run["status"] == "tested"]
    summary = {}
    for branch in ("untouched", "candidate_neighborhood", "background"):
        samples = [run["branches"][branch]["continuation_samples"] for run in tested]
        summary[branch] = {
            "tested": len(tested),
            "survived_to_end": int(sum(run["branches"][branch]["survived_to_end"] for run in tested)),
            "median_continuation_samples": float(np.median(samples)) if samples else 0.0,
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="P-to-A coupling-strength dose response.")
    parser.add_argument("--mode", choices=("field", "local", "both"), default="both")
    parser.add_argument("--gains", type=float, nargs="+", default=(0.0, 0.025, 0.05, 0.10, 0.20))
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--field-frames", type=int, default=2_000)
    parser.add_argument("--burn-in-frames", type=int, default=1_000)
    parser.add_argument("--follow-frames", type=int, default=1_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--radius", type=float, default=5.0)
    parser.add_argument("--weaken-strength", type=float, default=1.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v2_integrated_coupling_dose_response.json"),
    )
    args = parser.parse_args()
    if any(gain < 0.0 for gain in args.gains):
        parser.error("--gains must be non-negative")

    conditions = []
    seeds = range(args.seed_start, args.seed_start + args.seeds)
    for gain in args.gains:
        condition = {"potential_to_actual": gain}
        if args.mode in ("field", "both"):
            field_runs = [{"seed": seed, "observation": run_field_seed(seed, gain, args)} for seed in seeds]
            condition["field_runs"] = field_runs
            condition["field_summary"] = field_summary(field_runs)
        if args.mode in ("local", "both"):
            local_runs = [run_local_seed(seed, gain, args) for seed in seeds]
            condition["local_runs"] = local_runs
            condition["local_summary"] = local_summary(local_runs)
        conditions.append(condition)

    output = {
        "schema_version": 1,
        "claim_boundary": "This tests dose response of one P-to-A link; it does not establish higher-order objects.",
        "experiment": {
            "name": "v2_integrated_coupling_dose_response",
            "parameters": {**vars(args), "output": str(args.output)},
        },
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    for condition in conditions:
        print(f"P-to-A={condition['potential_to_actual']}")
        if "field_summary" in condition:
            print(json.dumps(condition["field_summary"], indent=2))
        if "local_summary" in condition:
            print(json.dumps(condition["local_summary"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
