"""Does distinct P/A dynamics change V1's validated local structural effect?"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from genesis_v1_local_structure_perturbation import choose_background, disk_mask, select_candidate, update_trackers, weaken_structure
from src.genesis_grid import diagnostics
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker
from src.genesis_v2_integrated import IntegratedParams, IntegratedState, step


def make_params(potential_bridge: bool) -> IntegratedParams:
    params = IntegratedParams()
    params.alpha = 0.30
    params.gamma = 0.01
    params.kappa = 0.10
    params.curv = 0.04
    params.phase = 0.0
    params.dipole = 0.0
    params.triads = 0.0
    params.lock_strength = 0.96
    params.phase_lock_gain = 0.0
    params.tri_lock_gain = 0.0
    params.shell_geom_gain = 0.08
    if potential_bridge:
        params.potential_transport = 0.03
        params.potential_source_restore = 0.10
        params.potential_to_actual = 0.10
    return params


def update(state, frame, defects, pairs, compression_average):
    plus, minus, _ = diagnostics.detect_vortices(state)
    detections = [(col, row, 1) for row, col in plus] + [(col, row, -1) for row, col in minus]
    compression = np.asarray(to_cpu(state.C), dtype=np.float64)
    compression_average = 0.95 * compression_average + 0.05 * compression
    tracks = defects.update(frame, detections, C=compression, C_avg=compression_average)
    active = pairs.update(frame=frame, defect_tracks=tracks, C=compression, C_avg=compression_average)
    return active, compression_average


def follow(state, params, defects, pairs, compression_average, candidate_key, start_frame, args):
    seen, last_seen = 0, start_frame
    for frame in range(start_frame + 1, start_frame + args.follow_frames + 1):
        step(state, params)
        if frame % args.sample_interval:
            continue
        active, compression_average = update(state, frame, defects, pairs, compression_average)
        if any((pair.plus_id, pair.minus_id) == candidate_key for pair in active):
            seen += 1
            last_seen = frame
    return {"continuation_samples": seen, "survived_to_end": last_seen == start_frame + args.follow_frames}


def run_seed(seed: int, potential_bridge: bool, args) -> dict:
    state = IntegratedState(args.N, dt=0.05, seed=seed)
    params = make_params(potential_bridge)
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


def run_condition(name: str, potential_bridge: bool, args) -> dict:
    runs = [run_seed(seed, potential_bridge, args) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    tested = [run for run in runs if run["status"] == "tested"]
    summary = {}
    for branch in ("untouched", "candidate_neighborhood", "background"):
        values = [run["branches"][branch]["continuation_samples"] for run in tested]
        summary[branch] = {
            "tested": len(tested),
            "survived_to_end": int(sum(run["branches"][branch]["survived_to_end"] for run in tested)),
            "median_continuation_samples": float(np.median(values)) if values else 0.0,
        }
    return {"condition": name, "runs": runs, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare V1-parity and P-to-A bridge local structural continuation.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--burn-in-frames", type=int, default=1_000)
    parser.add_argument("--follow-frames", type=int, default=1_000)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--radius", type=float, default=5.0)
    parser.add_argument("--weaken-strength", type=float, default=1.0)
    parser.add_argument("--condition", choices=("both", "parity", "potential"), default="both")
    parser.add_argument("--output", type=Path, default=Path("results/v2_integrated_local_structure_probe.json"))
    args = parser.parse_args()
    conditions = []
    if args.condition in ("both", "parity"):
        conditions.append(run_condition("v1_parity", False, args))
    if args.condition in ("both", "potential"):
        conditions.append(run_condition("independent_potential_influences_actuality", True, args))
    output = {
        "schema_version": 1,
        "claim_boundary": "This compares a validated local structural continuation measurement across P/A conditions; it does not establish higher-order objects.",
        "experiment": {"name": "v2_integrated_local_structure_probe", "parameters": {**vars(args), "output": str(args.output)}},
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    for condition in output["conditions"]:
        print(condition["condition"], json.dumps(condition["summary"]))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
