"""Initial regime map for the v2-epsilon resource-renewal hypothesis."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_epsilon import EpsilonParams, EpsilonState, step, summary


def run_one(N: int, frames: int, seed: int, params: EpsilonParams, cutoff: float, min_area: int) -> dict:
    state = EpsilonState(N, seed=seed)
    for _ in range(frames):
        step(state, params)
    domains = detect_relation_domains(state, cutoff, min_area)
    areas = [domain.area for domain in domains]
    return {
        **summary(state),
        "domain_count": len(domains),
        "largest_domain_fraction": max((area / (N * N) for area in areas), default=0.0),
        "median_domain_area": statistics.median(areas) if areas else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Map v2-epsilon resource-renewal regimes.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--depletions", type=float, nargs="+", default=[0.01, 0.03, 0.08])
    parser.add_argument("--replenishments", type=float, nargs="+", default=[0.015, 0.035, 0.070])
    parser.add_argument("--transport", type=float, default=0.22)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("results/v2_epsilon_regime_map.json"))
    args = parser.parse_args()
    if args.N < 8 or args.frames < 1 or args.seeds < 1 or args.transport < 0.0 or any(value < 0.0 for value in args.depletions + args.replenishments) or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1:
        raise SystemExit("Invalid epsilon sweep arguments.")
    conditions = []
    for replenish in args.replenishments:
        for depletion in args.depletions:
            params = EpsilonParams(
                potential_to_actual=0.05,
                relation_difference_gain=0.55,
                availability_transport=args.transport,
                availability_replenish=replenish,
                coherence_depletion=depletion,
            )
            runs = [run_one(args.N, args.frames, seed, params, args.cutoff, args.min_area) for seed in range(args.seed_start, args.seed_start + args.seeds)]
            aggregate = {key: statistics.mean(run[key] for run in runs) for key in runs[0]}
            conditions.append({"replenish": replenish, "coherence_depletion": depletion, "params": vars(params), "aggregate": aggregate, "runs": runs})
            print(f"replenish={replenish:.3f}; depletion={depletion:.3f}: P/A={aggregate['potential_actual_alignment']:.3f}; resource={aggregate['potential_strength']:.3f}; largest={aggregate['largest_domain_fraction']:.3f}; domains={aggregate['domain_count']:.2f}")
    report = {
        "schema_version": 1,
        "claim_boundary": "This maps a slow-resource renewal hypothesis. It does not establish cycles, stable objects, or metaphysical claims.",
        "config": {key: value for key, value in vars(args).items() if key != "output"},
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-epsilon regime report to {args.output}")


if __name__ == "__main__":
    main()
