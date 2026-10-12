"""Initial regime sweep for the v2-delta scale-selection hypothesis."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_delta import DeltaParams, DeltaState, step, summary


def run_one(N, frames, seed, params, cutoff, min_area):
    state = DeltaState(N, seed=seed)
    for _ in range(frames):
        step(state, params)
    domains = detect_relation_domains(state, cutoff, min_area)
    return {**summary(state), "domain_count": len(domains), "largest_domain_fraction": max((domain.area / (N * N) for domain in domains), default=0.0), "median_domain_area": statistics.median([domain.area for domain in domains]) if domains else 0.0}


def main() -> None:
    parser = argparse.ArgumentParser(description="Map initial v2-delta scale-selection regimes.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--gains", type=float, nargs="+", default=[0.03, 0.08, 0.16])
    parser.add_argument("--passes", type=int, nargs="+", default=[4, 8, 12])
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("results/v2_delta_regime_map.json"))
    args = parser.parse_args()
    if args.N < 8 or args.frames < 1 or args.seeds < 1 or any(gain < 0.0 for gain in args.gains) or any(passes < 1 for passes in args.passes) or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1:
        raise SystemExit("Invalid delta sweep arguments.")
    conditions = []
    for passes in args.passes:
        for gain in args.gains:
            params = DeltaParams(potential_to_actual=0.05, relation_difference_gain=0.55, long_range_passes=passes, long_range_counter_gain=gain)
            runs = [run_one(args.N, args.frames, seed, params, args.cutoff, args.min_area) for seed in range(args.seed_start, args.seed_start + args.seeds)]
            aggregate = {key: statistics.mean(run[key] for run in runs) for key in runs[0]}
            condition = {"passes": passes, "counter_gain": gain, "params": vars(params), "aggregate": aggregate, "runs": runs}
            conditions.append(condition)
            print(f"passes={passes}; gain={gain:.3f}: P/A={aggregate['potential_actual_alignment']:.3f}; largest={aggregate['largest_domain_fraction']:.3f}; domains={aggregate['domain_count']:.2f}")
    report = {
        "schema_version": 1,
        "claim_boundary": "This maps a new scale-selection hypothesis. It does not establish bounded objects; it only determines whether delta avoids immediate P/A collapse, one-domain coarsening, or noise fragmentation.",
        "config": {key: value for key, value in vars(args).items() if key != "output"},
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-delta regime report to {args.output}")


if __name__ == "__main__":
    main()
