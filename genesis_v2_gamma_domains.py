"""Track relation-bounded region candidates in the Genesis v2-gamma hypothesis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.genesis_v2_beta.objects import RegionTracker, detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step


def run_one(N: int, frames: int, seed: int, sample_interval: int, cutoffs: list[float], min_area: int, min_samples: int, params: GammaParams) -> dict:
    state = GammaState(N, seed=seed)
    trackers = {cutoff: RegionTracker() for cutoff in cutoffs}
    samples = {cutoff: [] for cutoff in cutoffs}
    for frame in range(1, frames + 1):
        step(state, params)
        if frame % sample_interval != 0 and frame != frames:
            continue
        for cutoff, tracker in trackers.items():
            regions = detect_relation_domains(state, cutoff, min_area)
            tracker.update(frame, regions)
            samples[cutoff].append({"frame": frame, "region_count": len(regions), "areas": sorted((region.area for region in regions), reverse=True)})
    conditions = {}
    for cutoff, tracker in trackers.items():
        tracks = tracker.reports(min_samples)
        persistent = [track for track in tracks if track["status"] == "persistent_candidate"]
        conditions[str(cutoff)] = {"samples": samples[cutoff], "tracks": tracks, "persistent_count": len(persistent), "largest_persistent_area": max((track["max_area"] for track in persistent), default=0)}
    return {"seed": seed, "conditions": conditions}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep and track gamma relation-bounded region candidates.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=100)
    parser.add_argument("--cutoffs", type=float, nargs="+", default=[0.55, 0.60, 0.65, 0.70, 0.75])
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--min-samples", type=int, default=5)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_domains.json"))
    args = parser.parse_args()
    if args.N < 2 or args.frames < 1 or args.seeds < 1 or args.sample_interval < 1 or args.min_area < 1 or args.min_samples < 1 or any(not 0.0 <= cutoff <= 1.0 for cutoff in args.cutoffs):
        raise SystemExit("Invalid domain-census arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    runs = [run_one(args.N, args.frames, seed, args.sample_interval, args.cutoffs, args.min_area, args.min_samples, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    aggregate = {}
    for cutoff in args.cutoffs:
        key = str(cutoff)
        counts = [run["conditions"][key]["persistent_count"] for run in runs]
        largest = [run["conditions"][key]["largest_persistent_area"] / (args.N * args.N) for run in runs]
        aggregate[key] = {"persistent_count_by_seed": counts, "largest_persistent_area_fraction_by_seed": largest}
        print(f"cutoff={cutoff:.2f}: persistent={counts}; largest-area-fraction={[round(value, 3) for value in largest]}")
    report = {"schema_version": 1, "claim_boundary": "This is a cutoff-sensitivity and identity-tracking probe for gamma's relation-boundary mechanism. Persistent components are not yet higher-order objects; autonomy and perturbation resistance remain untested.", "config": {"N": args.N, "frames": args.frames, "seeds": list(range(args.seed_start, args.seed_start + args.seeds)), "sample_interval": args.sample_interval, "cutoffs": args.cutoffs, "min_area": args.min_area, "min_samples": args.min_samples, "params": vars(params)}, "aggregate": aggregate, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma domain report to {args.output}")


if __name__ == "__main__":
    main()
