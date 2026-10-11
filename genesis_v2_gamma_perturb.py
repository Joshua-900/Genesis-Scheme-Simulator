"""Paired localized-perturbation probe for v2-gamma relation domains."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step


def angular_distance(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    return np.abs(np.angle(np.exp(1j * (first - second))))


def best_overlap(reference: np.ndarray, regions) -> tuple[float, int]:
    scores = []
    for region in regions:
        union = np.logical_or(reference, region.mask).sum()
        scores.append((float(np.logical_and(reference, region.mask).sum() / union) if union else 0.0, region.area))
    return max(scores, default=(0.0, 0))


def run_one(args, seed: int, params: GammaParams) -> dict:
    state = GammaState(args.N, seed=seed)
    for _ in range(args.warmup_frames):
        step(state, params)
    regions = detect_relation_domains(state, args.cutoff, args.min_area)
    if not regions:
        return {"seed": seed, "status": "no_candidate_at_intervention"}
    candidate = max(regions, key=lambda region: region.area)
    reference = candidate.mask
    yy, xx = np.indices(reference.shape)
    distances = np.sqrt((yy - candidate.centroid_y) ** 2 + (xx - candidate.centroid_x) ** 2)
    patch = reference & (distances <= args.patch_radius)
    if not patch.any():
        patch = reference

    control, perturbed = state.clone(), state.clone()
    perturbed.theta = (perturbed.theta + args.angle * patch) % (2.0 * np.pi)
    rows = []
    for frame in range(0, args.recovery_frames + 1):
        if frame % args.sample_interval == 0 or frame == args.recovery_frames:
            control_regions = detect_relation_domains(control, args.cutoff, args.min_area)
            perturbed_regions = detect_relation_domains(perturbed, args.cutoff, args.min_area)
            control_overlap, control_area = best_overlap(reference, control_regions)
            perturbed_overlap, perturbed_area = best_overlap(reference, perturbed_regions)
            delta = angular_distance(np.asarray(to_cpu(perturbed.theta)), np.asarray(to_cpu(control.theta)))
            rows.append({"frames_after_intervention": frame, "control_overlap": control_overlap, "perturbed_overlap": perturbed_overlap, "control_matched_area": control_area, "perturbed_matched_area": perturbed_area, "inside_difference": float(delta[reference].mean()), "outside_difference": float(delta[~reference].mean())})
        if frame < args.recovery_frames:
            step(control, params)
            step(perturbed, params)
    return {"seed": seed, "status": "measured", "candidate": {"area": candidate.area, "centroid": [candidate.centroid_y, candidate.centroid_x], "coherence": candidate.coherence, "boundary_contrast": candidate.boundary_contrast, "perturbed_cells": int(patch.sum())}, "series": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare gamma domain continuity after a localized actuality perturbation.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--warmup-frames", type=int, default=1_200)
    parser.add_argument("--recovery-frames", type=int, default=400)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=20)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--patch-radius", type=float, default=4.0)
    parser.add_argument("--angle", type=float, default=1.5707963267948966)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_perturbation.json"))
    args = parser.parse_args()
    if args.N < 2 or args.warmup_frames < 1 or args.recovery_frames < 1 or args.seeds < 1 or args.sample_interval < 1 or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1 or args.patch_radius <= 0.0:
        raise SystemExit("Invalid perturbation arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    runs = [run_one(args, seed, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    for run in runs:
        if run["status"] != "measured":
            print(f"seed={run['seed']}: no candidate at intervention")
            continue
        final = run["series"][-1]
        print(f"seed={run['seed']}: area={run['candidate']['area']}; overlap control/perturbed={final['control_overlap']:.3f}/{final['perturbed_overlap']:.3f}; inside/outside delta={final['inside_difference']:.3f}/{final['outside_difference']:.3f}")
    report = {"schema_version": 1, "claim_boundary": "This paired perturbation test measures continuity and disturbance propagation of an observer-defined gamma component. It does not establish autonomy or causal closure.", "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)}, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma perturbation report to {args.output}")


if __name__ == "__main__":
    main()
