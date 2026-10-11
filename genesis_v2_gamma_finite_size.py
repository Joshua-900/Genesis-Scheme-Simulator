"""Finite-size robustness sweep for v2-gamma bounded-response candidates."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step
from src.genesis_v2_gamma.probes import angular_distance, best_overlap, disk, outside_patch


def observe(reference, patch, control, branch, cutoff, min_area):
    overlap, matched_area = best_overlap(reference, detect_relation_domains(branch, cutoff, min_area))
    delta = angular_distance(np.asarray(to_cpu(branch.theta)), np.asarray(to_cpu(control.theta)))
    elsewhere = ~(reference | patch)
    return {"candidate_overlap": overlap, "candidate_matched_area": matched_area, "difference_in_candidate": float(delta[reference].mean()), "difference_in_patch": float(delta[patch].mean()), "difference_elsewhere": float(delta[elsewhere].mean()) if elsewhere.any() else 0.0}


def run_one(N, cutoff, seed, args, params):
    state = GammaState(N, seed=seed)
    for _ in range(args.warmup_frames):
        step(state, params)
    domains = detect_relation_domains(state, cutoff, args.min_area)
    if not domains:
        return {"status": "no_candidate"}
    selected = max(domains, key=lambda domain: domain.area)
    reference = selected.mask
    center_y, center_x = np.argwhere(reference).mean(axis=0).round().astype(int)
    inside = disk(reference.shape, center_y, center_x, args.patch_radius) & reference
    outside = outside_patch(reference, args.patch_radius, args.buffer)
    if not inside.any() or outside is None:
        return {"status": "no_matched_patches"}
    control, inside_branch, outside_branch = state.clone(), state.clone(), state.clone()
    inside_branch.theta = (inside_branch.theta + args.angle * inside) % (2.0 * np.pi)
    outside_branch.theta = (outside_branch.theta + args.angle * outside) % (2.0 * np.pi)
    for _ in range(args.recovery_frames):
        step(control, params); step(inside_branch, params); step(outside_branch, params)
    control_overlap, _ = best_overlap(reference, detect_relation_domains(control, cutoff, args.min_area))
    inside_measure = observe(reference, inside, control, inside_branch, cutoff, args.min_area)
    outside_measure = observe(reference, outside, control, outside_branch, cutoff, args.min_area)
    return {"status": "measured", "candidate_area_fraction": selected.area / (N * N), "candidate_coherence": selected.coherence, "candidate_boundary_contrast": selected.boundary_contrast, "control_overlap": control_overlap, "inside": inside_measure, "outside": outside_measure}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep v2-gamma candidate response across lattice sizes and observer cutoffs.")
    parser.add_argument("--sizes", type=int, nargs="+", default=[32, 64, 96])
    parser.add_argument("--cutoffs", type=float, nargs="+", default=[0.70, 0.75, 0.80])
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--warmup-frames", type=int, default=1_200)
    parser.add_argument("--recovery-frames", type=int, default=400)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--patch-radius", type=float, default=4.0)
    parser.add_argument("--buffer", type=int, default=2)
    parser.add_argument("--angle", type=float, default=1.5707963267948966)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_finite_size.json"))
    args = parser.parse_args()
    if any(size < 8 for size in args.sizes) or args.seeds < 1 or any(not 0.0 <= cutoff <= 1.0 for cutoff in args.cutoffs):
        raise SystemExit("Invalid finite-size arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    conditions = {}
    for N in args.sizes:
        for cutoff in args.cutoffs:
            runs = [run_one(N, cutoff, seed, args, params) | {"seed": seed} for seed in range(args.seed_start, args.seed_start + args.seeds)]
            measured = [run for run in runs if run["status"] == "measured"]
            key = f"N{N}_cutoff{cutoff:.2f}"
            conditions[key] = {"N": N, "cutoff": cutoff, "runs": runs, "aggregate": {"measured_runs": len(measured), "median_area_fraction": statistics.median(run["candidate_area_fraction"] for run in measured) if measured else None, "median_control_overlap": statistics.median(run["control_overlap"] for run in measured) if measured else None, "median_inside_candidate_difference": statistics.median(run["inside"]["difference_in_candidate"] for run in measured) if measured else None, "median_outside_candidate_difference": statistics.median(run["outside"]["difference_in_candidate"] for run in measured) if measured else None}}
            aggregate = conditions[key]["aggregate"]
            print(f"{key}: measured={aggregate['measured_runs']}; area={aggregate['median_area_fraction']}; C/I/O delta={aggregate['median_control_overlap']}/{aggregate['median_inside_candidate_difference']}/{aggregate['median_outside_candidate_difference']}")
    report = {"schema_version": 1, "claim_boundary": "This finite-size sweep asks whether gamma's observer-defined bounded response survives modest lattice-size and cutoff changes. It does not test continuum resolution or establish autonomous objects.", "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)}, "conditions": conditions}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma finite-size report to {args.output}")


if __name__ == "__main__":
    main()
