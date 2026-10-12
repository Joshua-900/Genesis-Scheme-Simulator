"""Matched potential-only perturbation of a selected V2 bridge candidate."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from genesis_v1_local_structure_perturbation import choose_background, disk_mask, select_candidate
from genesis_v2_integrated_local_structure_probe import make_params, update, follow
from src.genesis_grid.backend import to_cpu, xp
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker
from src.genesis_v2_integrated import IntegratedState, step


def rotate_potential(state: IntegratedState, mask: np.ndarray, angle: float) -> None:
    """Rotate P locally without changing A, tension, geometry, or compression."""
    cos_angle, sin_angle = np.cos(angle), np.sin(angle)
    px, py = state.px.copy(), state.py.copy()
    rotated_x = cos_angle * px - sin_angle * py
    rotated_y = sin_angle * px + cos_angle * py
    state.px = xp.where(mask, rotated_x, px)
    state.py = xp.where(mask, rotated_y, py)


def run_seed(seed: int, args) -> dict:
    state = IntegratedState(args.N, dt=0.05, seed=seed)
    params = make_params(True)
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
        "candidate_potential": disk_mask(args.N, candidate.midpoint_x, candidate.midpoint_y, args.radius),
        "background_potential": disk_mask(args.N, background_x, background_y, args.radius),
    }
    branches = {}
    for name, mask in masks.items():
        branch_state = copy.deepcopy(state)
        if mask is not None:
            rotate_potential(branch_state, mask, args.rotation)
        branches[name] = follow(branch_state, params, copy.deepcopy(defects), copy.deepcopy(pairs), compression_average.copy(), key, args.burn_in_frames, args)

    theta = np.asarray(to_cpu(state.theta))
    p_angle = np.arctan2(np.asarray(to_cpu(state.py)), np.asarray(to_cpu(state.px)))
    return {
        "seed": seed,
        "status": "tested",
        "potential_actual_alignment": float(np.mean(np.cos(theta - p_angle))),
        "candidate_line_compression": candidate.mean_C_avg_along_line,
        "branches": branches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Matched potential-only candidate-neighborhood versus background perturbation.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--burn-in-frames", type=int, default=1_000)
    parser.add_argument("--follow-frames", type=int, default=1_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--radius", type=float, default=5.0)
    parser.add_argument("--rotation", type=float, default=float(np.pi / 2.0))
    parser.add_argument("--output", type=Path, default=Path("results/v2_integrated_potential_perturbation.json"))
    args = parser.parse_args()
    runs = [run_seed(seed, args) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    tested = [run for run in runs if run["status"] == "tested"]
    summary = {}
    for branch in ("untouched", "candidate_potential", "background_potential"):
        values = [run["branches"][branch]["continuation_samples"] for run in tested]
        summary[branch] = {
            "tested": len(tested),
            "survived_to_end": int(sum(run["branches"][branch]["survived_to_end"] for run in tested)),
            "median_continuation_samples": float(np.median(values)) if values else 0.0,
        }
    output = {
        "schema_version": 1,
        "claim_boundary": "This tests causal sensitivity to a local P-direction perturbation, not higher-order objects.",
        "experiment": {"name": "v2_integrated_potential_only_perturbation", "parameters": {**vars(args), "output": str(args.output)}},
        "runs": runs,
        "summary": summary,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
