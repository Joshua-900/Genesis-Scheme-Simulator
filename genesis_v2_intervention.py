"""Paired intervention test for the v2 P/A/R prototype.

It starts matched states, perturbs only P in one pair and only A in another,
then measures whether the untouched component develops differently. This is
the first non-relabeling test, not a claim of metaphysical validation.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu, xp
from src.genesis_v2 import V2Params, V2State, step, summary


def circular_distance(a, b) -> float:
    return float(np.mean(np.abs(np.arctan2(np.sin(a - b), np.cos(a - b)))))


def field_distance(a, b) -> float:
    return float(np.mean(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)))


def region_mask(N: int, fraction: float) -> np.ndarray:
    radius = max(1, int(N * fraction))
    y, x = np.ogrid[:N, :N]
    return (x - N // 2) ** 2 + (y - N // 2) ** 2 <= radius * radius


def perturb_potential(state: V2State, mask: np.ndarray, angle: float) -> None:
    px, py = to_cpu(state.px), to_cpu(state.py)
    magnitude = np.sqrt(px * px + py * py)
    original = np.arctan2(py, px)
    rotated = original + angle
    px[mask] = magnitude[mask] * np.cos(rotated[mask])
    py[mask] = magnitude[mask] * np.sin(rotated[mask])
    state.px, state.py = xp.asarray(px), xp.asarray(py)


def perturb_actuality(state: V2State, mask: np.ndarray, angle: float) -> None:
    theta = to_cpu(state.theta)
    theta[mask] = (theta[mask] + angle) % (2.0 * np.pi)
    state.theta = xp.asarray(theta)


def run_pair(control: V2State, treated: V2State, params: V2Params, steps: int, measure: str) -> dict:
    series = []
    for frame in range(1, steps + 1):
        step(control, params)
        step(treated, params)
        if frame % max(1, steps // 20) == 0 or frame == steps:
            if measure == "actuality":
                distance = circular_distance(to_cpu(control.theta), to_cpu(treated.theta))
            else:
                distance = field_distance(
                    (to_cpu(control.px), to_cpu(control.py)),
                    (to_cpu(treated.px), to_cpu(treated.py)),
                )
            series.append({"frame": frame, "distance": distance})
    return {"final_distance": series[-1]["distance"], "series": series, "control": summary(control), "treated": summary(treated)}


def run_intervention(N: int, steps: int, seed: int, region_fraction: float, angle: float) -> dict:
    """Run both directions of the non-relabeling test from one matched seed."""
    base = V2State(N, seed=seed)
    mask = region_mask(N, region_fraction)
    params = V2Params()

    p_control, p_treated = base.clone(), base.clone()
    perturb_potential(p_treated, mask, angle)
    p_initial_actuality_distance = circular_distance(to_cpu(p_control.theta), to_cpu(p_treated.theta))
    potential_to_actual = run_pair(p_control, p_treated, params, steps, "actuality")

    a_control, a_treated = base.clone(), base.clone()
    perturb_actuality(a_treated, mask, angle)
    a_initial_potential_distance = field_distance(
        (to_cpu(a_control.px), to_cpu(a_control.py)),
        (to_cpu(a_treated.px), to_cpu(a_treated.py)),
    )
    actuality_to_potential = run_pair(a_control, a_treated, params, steps, "potentiality")

    return {
        "seed": seed,
        "pre_intervention_invariants": {
            "actuality_distance_after_potential_only_change": p_initial_actuality_distance,
            "potentiality_distance_after_actuality_only_change": a_initial_potential_distance,
        },
        "potentiality_to_actuality": potential_to_actual,
        "actuality_to_potentiality": actuality_to_potential,
    }


def parse_fractions(raw: str) -> list[float]:
    try:
        values = [float(value.strip()) for value in raw.split(",") if value.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--region-fractions must contain comma-separated numbers.") from exc
    if not values or any(value <= 0.0 or value >= 0.5 for value in values):
        raise argparse.ArgumentTypeError("Each region fraction must be greater than 0 and less than 0.5.")
    return values


def summarize(runs: list[dict]) -> dict:
    p_to_a = [run["potentiality_to_actuality"]["final_distance"] for run in runs]
    a_to_p = [run["actuality_to_potentiality"]["final_distance"] for run in runs]
    return {
        "runs": len(runs),
        "potentiality_to_actuality": {"min": min(p_to_a), "median": statistics.median(p_to_a), "max": max(p_to_a)},
        "actuality_to_potentiality": {"min": min(a_to_p), "median": statistics.median(a_to_p), "max": max(a_to_p)},
        "all_pre_intervention_invariants_zero": all(
            run["pre_intervention_invariants"]["actuality_distance_after_potential_only_change"] == 0.0
            and run["pre_intervention_invariants"]["potentiality_distance_after_actuality_only_change"] == 0.0
            for run in runs
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the v2 P/A/R paired intervention test.")
    parser.add_argument("--N", type=int, default=100)
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--region-fractions", default="0.12", help="Comma-separated fractions of grid width for the intervention radius.")
    parser.add_argument("--angle", type=float, default=np.pi / 2)
    parser.add_argument("--output", type=Path, default=Path("results/v2_paired_intervention.json"))
    args = parser.parse_args()
    fractions = parse_fractions(args.region_fractions)
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive.")

    conditions = []
    seeds = range(args.seed_start, args.seed_start + args.seeds)
    for fraction in fractions:
        runs = [run_intervention(args.N, args.steps, seed, fraction, args.angle) for seed in seeds]
        conditions.append({
            "region_fraction": fraction,
            "runs": runs,
            "summary": summarize(runs),
        })
        summary_row = conditions[-1]["summary"]
        print(
            f"region={fraction:g}: P -> A median {summary_row['potentiality_to_actuality']['median']:.6f}; "
            f"A -> P median {summary_row['actuality_to_potentiality']['median']:.6f}"
        )

    report = {
        "schema_version": 1,
        "claim_boundary": "A nonzero divergence is evidence that this prototype implements distinct coupled P/A/R state components. It is not evidence for a metaphysical claim.",
        "config": {"N": args.N, "steps": args.steps, "seeds": list(seeds), "region_fractions": fractions, "angle": args.angle},
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote paired intervention report to {args.output}")


if __name__ == "__main__":
    main()
