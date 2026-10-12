"""Causal perimeter-boundary intervention for v2-gamma candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step
from src.genesis_v2_gamma.interventions import apply_boundary, perimeter_boundary_mean
from src.genesis_v2_gamma.probes import angular_distance, best_overlap, translated_background_mask


def observe(reference: np.ndarray, control: GammaState, branch: GammaState, cutoff: float, min_area: int) -> dict:
    overlap, area = best_overlap(reference, detect_relation_domains(branch, cutoff, min_area))
    delta = angular_distance(np.asarray(to_cpu(branch.theta)), np.asarray(to_cpu(control.theta)))
    return {"candidate_overlap": overlap, "matched_area": area, "candidate_state_difference": float(delta[reference].mean()), "candidate_perimeter_boundary": perimeter_boundary_mean(branch, reference)}


def run_one(args, seed: int, params: GammaParams) -> dict:
    state = GammaState(args.N, seed=seed)
    for _ in range(args.warmup_frames):
        step(state, params)
    domains = detect_relation_domains(state, args.cutoff, args.min_area)
    if not domains:
        return {"seed": seed, "status": "no_candidate"}
    selected = max(domains, key=lambda domain: domain.area)
    reference = selected.mask
    occupied = np.logical_or.reduce([domain.mask for domain in domains])
    background = translated_background_mask(reference, occupied, max_overlap=0.25)
    if background is None:
        return {"seed": seed, "status": "no_background_mask"}
    control = state.clone()
    branches = {"candidate_weaken": state.clone(), "background_weaken": state.clone(), "candidate_strengthen": state.clone(), "background_strengthen": state.clone()}
    apply_boundary(branches["candidate_weaken"], reference, params, "weaken", args.strength)
    apply_boundary(branches["background_weaken"], background, params, "weaken", args.strength)
    apply_boundary(branches["candidate_strengthen"], reference, params, "strengthen", args.strength)
    apply_boundary(branches["background_strengthen"], background, params, "strengthen", args.strength)
    series = []
    for frame in range(args.recovery_frames + 1):
        if frame % args.sample_interval == 0 or frame == args.recovery_frames:
            control_overlap, control_area = best_overlap(reference, detect_relation_domains(control, args.cutoff, args.min_area))
            series.append({"frames_after_intervention": frame, "control": {"candidate_overlap": control_overlap, "matched_area": control_area, "candidate_perimeter_boundary": perimeter_boundary_mean(control, reference)}, **{name: observe(reference, control, branch, args.cutoff, args.min_area) for name, branch in branches.items()}})
        if frame < args.recovery_frames:
            step(control, params)
            for branch in branches.values():
                step(branch, params)
    return {"seed": seed, "status": "measured", "candidate": {"area": selected.area, "coherence": selected.coherence, "boundary_contrast": selected.boundary_contrast, "initial_perimeter_boundary": perimeter_boundary_mean(state, reference), "background_cells": int(background.sum())}, "series": series}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test whether v2-gamma candidate perimeter boundaries causally affect identity.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--warmup-frames", type=int, default=1_200)
    parser.add_argument("--recovery-frames", type=int, default=400)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=20)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--strength", type=float, default=0.85)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_boundary_causality.json"))
    args = parser.parse_args()
    if args.N < 8 or args.warmup_frames < 1 or args.recovery_frames < 1 or args.seeds < 1 or args.sample_interval < 1 or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1 or not 0.0 <= args.strength <= 1.0:
        raise SystemExit("Invalid causality arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    runs = [run_one(args, seed, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    for run in runs:
        if run["status"] != "measured":
            print(f"seed={run['seed']}: {run['status']}")
            continue
        final = run["series"][-1]
        print(f"seed={run['seed']}: overlap control/weaken-bg/weaken-candidate/strengthen-candidate={final['control']['candidate_overlap']:.3f}/{final['background_weaken']['candidate_overlap']:.3f}/{final['candidate_weaken']['candidate_overlap']:.3f}/{final['candidate_strengthen']['candidate_overlap']:.3f}")
    report = {"schema_version": 1, "claim_boundary": "This directly intervenes on the stored gamma boundary state at a selected candidate or matched background mask. It tests causal contribution to model identity, not autonomy or metaphysical validity.", "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)}, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma boundary-causality report to {args.output}")


if __name__ == "__main__":
    main()
