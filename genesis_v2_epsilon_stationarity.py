"""Test whether v2-epsilon sustains a finite domain scale over time."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_epsilon import EpsilonParams, EpsilonState, step, summary


def observe(state: EpsilonState, cutoff: float, min_area: int) -> dict:
    domains = detect_relation_domains(state, cutoff, min_area)
    areas = [domain.area for domain in domains]
    total_area = state.N * state.N
    return {
        **summary(state),
        "domain_count": len(domains),
        "largest_domain_fraction": max((area / total_area for area in areas), default=0.0),
        "median_domain_area": statistics.median(areas) if areas else 0.0,
        "occupied_fraction": sum(areas) / total_area,
    }


def run_one(args, seed: int, params: EpsilonParams) -> dict:
    state = EpsilonState(args.N, seed=seed)
    samples = []
    for frame in range(args.frames + 1):
        if frame % args.sample_interval == 0 or frame == args.frames:
            samples.append({"frame": frame, **observe(state, args.cutoff, args.min_area)})
        if frame < args.frames:
            step(state, params)
    return {"seed": seed, "samples": samples}


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure v2-epsilon domain-scale stationarity.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=8_000)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=200)
    parser.add_argument("--coherence-depletion", type=float, default=0.03)
    parser.add_argument("--availability-replenish", type=float, default=0.035)
    parser.add_argument("--availability-transport", type=float, default=0.22)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("results/v2_epsilon_stationarity.json"))
    args = parser.parse_args()
    if args.N < 8 or args.frames < 1 or args.seeds < 1 or args.sample_interval < 1 or any(value < 0.0 for value in (args.coherence_depletion, args.availability_replenish, args.availability_transport)) or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1:
        raise SystemExit("Invalid epsilon stationarity arguments.")
    params = EpsilonParams(
        potential_to_actual=0.05,
        relation_difference_gain=0.55,
        availability_transport=args.availability_transport,
        availability_replenish=args.availability_replenish,
        coherence_depletion=args.coherence_depletion,
    )
    runs = [run_one(args, seed, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    for run in runs:
        final = run["samples"][-1]
        print(f"seed={run['seed']}: domains={final['domain_count']}; median_area={final['median_domain_area']:.1f}; largest={final['largest_domain_fraction']:.3f}")
    report = {
        "schema_version": 1,
        "claim_boundary": "This measures whether observer-defined relation domains maintain a finite aggregate scale. It does not establish object identity, causal autonomy, or a continuum-scale law.",
        "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)},
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-epsilon stationarity report to {args.output}")


if __name__ == "__main__":
    main()
