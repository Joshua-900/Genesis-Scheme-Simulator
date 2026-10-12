"""Test whether a local potential perturbation propagates beyond its source mask.

This is a field-level causal experiment.  It compares a locally rotated P field
with an untouched copy of the exact same state, then measures differences well
outside the perturbed disk.  Candidate and background sites use equal masks.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from genesis_v1_local_structure_perturbation import choose_background, disk_mask, select_candidate
from genesis_v2_integrated_local_structure_probe import make_params, update
from genesis_v2_integrated_potential_perturbation import rotate_potential
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker
from src.genesis_v2_integrated import IntegratedState, step


def angular_distance(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Return the absolute shortest angular difference between two fields."""
    return np.abs(np.angle(np.exp(1j * (left - right))))


def outside_response(perturbed: IntegratedState, control: IntegratedState, outside: np.ndarray) -> dict:
    p_perturbed = np.arctan2(to_cpu(perturbed.py), to_cpu(perturbed.px))
    p_control = np.arctan2(to_cpu(control.py), to_cpu(control.px))
    a_perturbed = np.asarray(to_cpu(perturbed.theta))
    a_control = np.asarray(to_cpu(control.theta))
    return {
        "mean_p_angle_difference": float(np.mean(angular_distance(p_perturbed, p_control)[outside])),
        "mean_a_angle_difference": float(np.mean(angular_distance(a_perturbed, a_control)[outside])),
        "mean_tension_difference": float(np.mean(np.abs(to_cpu(perturbed.tau) - to_cpu(control.tau))[outside])),
        "mean_compression_difference": float(np.mean(np.abs(to_cpu(perturbed.C) - to_cpu(control.C))[outside])),
    }


def follow_response(
    state: IntegratedState,
    params,
    mask: np.ndarray,
    outside: np.ndarray,
    args,
) -> dict:
    control = copy.deepcopy(state)
    perturbed = copy.deepcopy(state)
    rotate_potential(perturbed, mask, args.rotation)
    samples = {}

    for frame in range(1, args.follow_frames + 1):
        step(control, params)
        step(perturbed, params)
        if frame in args.sample_frames:
            samples[str(frame)] = outside_response(perturbed, control, outside)
    return samples


def run_seed(seed: int, args) -> dict:
    state = IntegratedState(args.N, dt=0.05, seed=seed)
    params = make_params(True)
    defects = DefectTracker()
    pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
    compression_average = np.zeros((args.N, args.N), dtype=np.float64)
    active = []

    for frame in range(1, args.burn_in_frames + 1):
        step(state, params)
        if frame % args.tracker_sample_interval == 0:
            active, compression_average = update(state, frame, defects, pairs, compression_average)

    candidate = select_candidate(active)
    if candidate is None:
        return {"seed": seed, "status": "no_candidate"}

    background_x, background_y = choose_background(args.N, candidate, args.radius, seed)
    locations = {
        "candidate": (candidate.midpoint_x, candidate.midpoint_y),
        "background": (background_x, background_y),
    }
    responses = {}
    for name, (x, y) in locations.items():
        perturbation_mask = disk_mask(args.N, x, y, args.radius)
        # This exclusion makes every recorded cell at least one source-radius
        # away from the intervention, rather than merely just outside its edge.
        outside = ~disk_mask(args.N, x, y, args.radius * args.exclusion_radius_multiple)
        responses[name] = follow_response(state, params, perturbation_mask, outside, args)

    return {"seed": seed, "status": "tested", "responses": responses}


def main() -> None:
    parser = argparse.ArgumentParser(description="Matched potential perturbation propagation test.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--burn-in-frames", type=int, default=1_000)
    parser.add_argument("--follow-frames", type=int, default=250)
    parser.add_argument("--sample-frames", type=int, nargs="+", default=(25, 100, 250))
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--tracker-sample-interval", type=int, default=25)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--radius", type=float, default=5.0)
    parser.add_argument("--exclusion-radius-multiple", type=float, default=2.0)
    parser.add_argument("--rotation", type=float, default=float(np.pi / 2.0))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v2_integrated_potential_propagation.json"),
    )
    args = parser.parse_args()
    if max(args.sample_frames) > args.follow_frames:
        parser.error("--sample-frames cannot exceed --follow-frames")

    runs = [run_seed(seed, args) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    tested = [run for run in runs if run["status"] == "tested"]
    summary = {}
    for frame in args.sample_frames:
        frame_key = str(frame)
        summary[frame_key] = {}
        for location in ("candidate", "background"):
            metrics = tested[0]["responses"][location][frame_key] if tested else {}
            summary[frame_key][location] = {
                metric: float(np.median([run["responses"][location][frame_key][metric] for run in tested]))
                for metric in metrics
            }

    output = {
        "schema_version": 1,
        "claim_boundary": "This tests field-level propagation from P; it does not establish higher-order objects.",
        "experiment": {
            "name": "v2_integrated_potential_propagation",
            "parameters": {**vars(args), "output": str(args.output)},
        },
        "runs": runs,
        "summary": summary,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
