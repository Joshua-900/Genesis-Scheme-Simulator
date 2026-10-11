"""Inside-versus-outside perturbation control for v2-gamma candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step
from src.genesis_v2_gamma.probes import angular_distance, best_overlap, disk, outside_patch


def observe(reference: np.ndarray, patch: np.ndarray, control: GammaState, branch: GammaState, cutoff: float, min_area: int) -> dict:
    overlap, matched_area = best_overlap(reference, detect_relation_domains(branch, cutoff, min_area))
    delta = angular_distance(np.asarray(to_cpu(branch.theta)), np.asarray(to_cpu(control.theta)))
    elsewhere = ~(reference | patch)
    return {
        "candidate_overlap": overlap,
        "candidate_matched_area": matched_area,
        "difference_in_candidate": float(delta[reference].mean()),
        "difference_in_patch": float(delta[patch].mean()),
        "difference_elsewhere": float(delta[elsewhere].mean()) if elsewhere.any() else 0.0,
    }


def run_one(args, seed: int, params: GammaParams) -> dict:
    state = GammaState(args.N, seed=seed)
    for _ in range(args.warmup_frames):
        step(state, params)
    domains = detect_relation_domains(state, args.cutoff, args.min_area)
    if not domains:
        return {"seed": seed, "status": "no_candidate_at_intervention"}
    selected = max(domains, key=lambda domain: domain.area)
    reference = selected.mask
    center_y, center_x = np.argwhere(reference).mean(axis=0).round().astype(int)
    inside = disk(reference.shape, center_y, center_x, args.patch_radius) & reference
    if not inside.any():
        return {"seed": seed, "status": "no_inside_patch"}
    outside = outside_patch(reference, args.patch_radius, args.buffer)
    if outside is None:
        return {"seed": seed, "status": "no_outside_patch"}

    control, inside_branch, outside_branch = state.clone(), state.clone(), state.clone()
    inside_branch.theta = (inside_branch.theta + args.angle * inside) % (2.0 * np.pi)
    outside_branch.theta = (outside_branch.theta + args.angle * outside) % (2.0 * np.pi)
    series = []
    for frame in range(args.recovery_frames + 1):
        if frame % args.sample_interval == 0 or frame == args.recovery_frames:
            control_overlap, control_area = best_overlap(reference, detect_relation_domains(control, args.cutoff, args.min_area))
            series.append({"frames_after_intervention": frame, "control": {"candidate_overlap": control_overlap, "candidate_matched_area": control_area}, "inside": observe(reference, inside, control, inside_branch, args.cutoff, args.min_area), "outside": observe(reference, outside, control, outside_branch, args.cutoff, args.min_area)})
        if frame < args.recovery_frames:
            step(control, params)
            step(inside_branch, params)
            step(outside_branch, params)
    return {"seed": seed, "status": "measured", "candidate": {"area": selected.area, "coherence": selected.coherence, "boundary_contrast": selected.boundary_contrast, "inside_cells": int(inside.sum()), "outside_cells": int(outside.sum())}, "series": series}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test whether gamma candidate response differs for inside and outside perturbations.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--warmup-frames", type=int, default=1_200)
    parser.add_argument("--recovery-frames", type=int, default=400)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=20)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--patch-radius", type=float, default=4.0)
    parser.add_argument("--buffer", type=int, default=2)
    parser.add_argument("--angle", type=float, default=1.5707963267948966)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_location_control.json"))
    args = parser.parse_args()
    if args.N < 2 or args.warmup_frames < 1 or args.recovery_frames < 1 or args.seeds < 1 or args.sample_interval < 1 or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1 or args.patch_radius <= 0.0 or args.buffer < 0:
        raise SystemExit("Invalid location-control arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    runs = [run_one(args, seed, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    for run in runs:
        if run["status"] != "measured":
            print(f"seed={run['seed']}: {run['status']}")
            continue
        final = run["series"][-1]
        print(f"seed={run['seed']}: overlap C/I/O={final['control']['candidate_overlap']:.3f}/{final['inside']['candidate_overlap']:.3f}/{final['outside']['candidate_overlap']:.3f}; candidate delta I/O={final['inside']['difference_in_candidate']:.3f}/{final['outside']['difference_in_candidate']:.3f}")
    report = {"schema_version": 1, "claim_boundary": "This location control compares identical perturbations inside and outside an observer-defined gamma component. It tests a prerequisite for object-specific response; it does not establish autonomy or causal closure.", "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)}, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma location-control report to {args.output}")


if __name__ == "__main__":
    main()
