"""Test whether v2-zeta sustains finite domains and local refractory renewal."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_zeta import ZetaParams, ZetaState, step, summary


def observe(state: ZetaState, cutoff: float, min_area: int) -> dict:
    domains = detect_relation_domains(state, cutoff, min_area)
    areas = [domain.area for domain in domains]
    total_area = state.N * state.N
    return {
        **summary(state),
        "refractory_mean": float(state.refractory.mean()),
        "refractory_std": float(state.refractory.std()),
        "domain_count": len(domains),
        "largest_domain_fraction": max((area / total_area for area in areas), default=0.0),
        "median_domain_area": statistics.median(areas) if areas else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure v2-zeta finite-scale stationarity.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=8_000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=200)
    parser.add_argument("--production", type=float, default=0.020)
    parser.add_argument("--alignment-gain", type=float, default=0.90)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("results/v2_zeta_stationarity.json"))
    args = parser.parse_args()
    if args.N < 8 or args.frames < 1 or args.sample_interval < 1 or args.production < 0.0 or args.alignment_gain < 0.0 or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1:
        raise SystemExit("Invalid zeta stationarity arguments.")
    params = ZetaParams(
        potential_to_actual=0.05,
        relation_difference_gain=0.55,
        refractory_production=args.production,
        refractory_alignment_gain=args.alignment_gain,
    )
    state = ZetaState(args.N, seed=args.seed)
    samples = []
    for frame in range(args.frames + 1):
        if frame % args.sample_interval == 0 or frame == args.frames:
            row = {"frame": frame, **observe(state, args.cutoff, args.min_area)}
            samples.append(row)
            print(f"frame={frame}: domains={row['domain_count']}; largest={row['largest_domain_fraction']:.3f}; refractory={row['refractory_mean']:.3f}")
        if frame < args.frames:
            step(state, params)
    report = {
        "schema_version": 1,
        "claim_boundary": "This measures finite-scale stationarity and aggregate refractory dynamics in one zeta trajectory. It does not establish object identity, generality, or a novel mechanism.",
        "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)},
        "samples": samples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-zeta stationarity report to {args.output}")


if __name__ == "__main__":
    main()
