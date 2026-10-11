"""Paired non-relabeling intervention for the rule-based v2-beta engine."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu, xp
from src.genesis_v2_beta import BetaParams, BetaState, step


def circular_distance(a, b) -> float:
    return float(np.mean(np.abs(np.arctan2(np.sin(a - b), np.cos(a - b)))))


def potential_distance(a: BetaState, b: BetaState) -> float:
    components = [
        np.asarray(to_cpu(a.px)) - np.asarray(to_cpu(b.px)),
        np.asarray(to_cpu(a.py)) - np.asarray(to_cpu(b.py)),
        np.asarray(to_cpu(a.availability)) - np.asarray(to_cpu(b.availability)),
    ]
    return float(np.mean(np.sqrt(sum(component * component for component in components))))


def mask_for(N: int, fraction: float) -> np.ndarray:
    radius = max(1, int(N * fraction))
    y, x = np.ogrid[:N, :N]
    return (x - N // 2) ** 2 + (y - N // 2) ** 2 <= radius * radius


def rotate_potential(state: BetaState, mask: np.ndarray, angle: float) -> None:
    px, py = np.asarray(to_cpu(state.px)).copy(), np.asarray(to_cpu(state.py)).copy()
    rotated = np.arctan2(py, px) + angle
    px[mask], py[mask] = np.cos(rotated[mask]), np.sin(rotated[mask])
    state.px, state.py = xp.asarray(px), xp.asarray(py)


def rotate_actuality(state: BetaState, mask: np.ndarray, angle: float) -> None:
    theta = np.asarray(to_cpu(state.theta)).copy()
    theta[mask] = (theta[mask] + angle) % (2.0 * np.pi)
    state.theta = xp.asarray(theta)


def advance(control: BetaState, treated: BetaState, steps: int, measure) -> float:
    params = BetaParams()
    for _ in range(steps):
        step(control, params)
        step(treated, params)
    return measure(control, treated)


def run_one(N: int, steps: int, seed: int, fraction: float, angle: float) -> dict:
    base, mask = BetaState(N, seed=seed), mask_for(N, fraction)
    p_control, p_treated = base.clone(), base.clone()
    rotate_potential(p_treated, mask, angle)
    p_invariant = circular_distance(np.asarray(to_cpu(p_control.theta)), np.asarray(to_cpu(p_treated.theta)))
    p_to_a = advance(p_control, p_treated, steps, lambda a, b: circular_distance(np.asarray(to_cpu(a.theta)), np.asarray(to_cpu(b.theta))))

    a_control, a_treated = base.clone(), base.clone()
    rotate_actuality(a_treated, mask, angle)
    a_invariant = potential_distance(a_control, a_treated)
    a_to_p = advance(a_control, a_treated, steps, potential_distance)
    return {"seed": seed, "initial_actuality_distance_after_p_only": p_invariant, "initial_potential_distance_after_a_only": a_invariant, "potentiality_to_actuality": p_to_a, "actuality_to_potentiality": a_to_p}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v2-beta paired interventions across seeds.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--region-fraction", type=float, default=0.12)
    parser.add_argument("--angle", type=float, default=np.pi / 2)
    parser.add_argument("--output", type=Path, default=Path("results/v2_beta_intervention.json"))
    args = parser.parse_args()
    runs = [run_one(args.N, args.steps, seed, args.region_fraction, args.angle) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    p_to_a = [run["potentiality_to_actuality"] for run in runs]
    a_to_p = [run["actuality_to_potentiality"] for run in runs]
    report = {
        "schema_version": 1,
        "claim_boundary": "This tests distinct coupled beta state roles, not object formation or metaphysical validity.",
        "config": vars(args) | {"output": str(args.output)},
        "runs": runs,
        "summary": {
            "potentiality_to_actuality": {"min": min(p_to_a), "median": statistics.median(p_to_a), "max": max(p_to_a)},
            "actuality_to_potentiality": {"min": min(a_to_p), "median": statistics.median(a_to_p), "max": max(a_to_p)},
            "all_initial_invariants_zero": all(run["initial_actuality_distance_after_p_only"] == 0.0 and run["initial_potential_distance_after_a_only"] == 0.0 for run in runs),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"P -> A final divergence (min/median): {min(p_to_a):.6f}/{statistics.median(p_to_a):.6f}")
    print(f"A -> P final divergence (min/median): {min(a_to_p):.6f}/{statistics.median(a_to_p):.6f}")
    print(f"Wrote v2-beta intervention report to {args.output}")


if __name__ == "__main__":
    main()
