"""Detector-sensitivity sweep for v1 vortex-antivortex pair candidates.

This holds the v1 dynamics and random seeds fixed while changing only the
observation schedule and maximum pairing radius.  It measures distributional
robustness; it does not yet establish one-to-one object identity across
detector configurations.

Example:
    python genesis_object_sensitivity.py --seeds 5 --frames 10000
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Callable, TypeVar

from genesis_object_census import run_one


T = TypeVar("T", int, float)


def comma_values(raw: str, convert: Callable[[str], T]) -> list[T]:
    values = [convert(value.strip()) for value in raw.split(",") if value.strip()]
    if not values:
        raise argparse.ArgumentTypeError("Provide at least one comma-separated value.")
    return values


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Measure v1 pair-census sensitivity to detector settings.")
    p.add_argument("--N", type=int, default=100)
    p.add_argument("--frames", type=int, default=10_000)
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--sample-intervals", default="10,25,50", help="Comma-separated frame intervals.")
    p.add_argument("--pair-distances", default="32,64,96", help="Comma-separated maximum pair distances.")
    p.add_argument("--min-age", type=int, default=100)
    p.add_argument("--min-observations-floor", type=int, default=1, help="Minimum samples even when elapsed-time persistence is already satisfied.")
    p.add_argument("--alpha", type=float, default=0.3)
    p.add_argument("--gamma", type=float, default=0.01)
    p.add_argument("--kappa", type=float, default=0.05)
    p.add_argument("--curv", type=float, default=0.04)
    p.add_argument("--lock", type=float, default=0.96)
    p.add_argument("--output", type=Path, default=Path("results/pair_census_sensitivity.json"))
    return p


def summarize(objects: list[dict]) -> dict:
    persistent = [item for item in objects if item["recognition"]["status"] == "persistent_candidate"]
    ages = [item["persistence"]["max_age_frames"] for item in persistent]
    return {
        "observed_candidates": len(objects),
        "persistent_candidates": len(persistent),
        "persistent_fraction": len(persistent) / len(objects) if objects else 0.0,
        "persistent_age_median": statistics.median(ages) if ages else 0.0,
        "persistent_age_mean": statistics.mean(ages) if ages else 0.0,
        "persistent_age_1000_or_more": sum(age >= 1_000 for age in ages),
        "persistent_age_5000_or_more": sum(age >= 5_000 for age in ages),
    }


def main() -> None:
    args = parser().parse_args()
    intervals = comma_values(args.sample_intervals, int)
    distances = comma_values(args.pair_distances, float)
    if min(intervals) < 1 or args.seeds < 1:
        raise SystemExit("Sample intervals and --seeds must be positive.")

    conditions: list[dict] = []
    total = len(intervals) * len(distances)
    condition_number = 0
    for interval in intervals:
        for distance in distances:
            condition_number += 1
            args.sample_interval = interval
            args.max_pair_distance = distance
            # Keep the persistence meaning constant across sampling schedules.
            # A pair born on an observation needs the initial sample plus enough
            # intervals to demonstrate the requested elapsed lifetime.
            args.min_observations = max(
                args.min_observations_floor,
                math.ceil(args.min_age / interval) + 1,
            )
            objects: list[dict] = []
            runs: list[dict] = []
            for run, seed in enumerate(range(args.seed_start, args.seed_start + args.seeds), start=1):
                run_objects, run_summary = run_one(args, run, seed)
                objects.extend(run_objects)
                runs.append(run_summary)
            summary = summarize(objects)
            conditions.append({
                "detector": {
                    "sample_interval": interval,
                    "max_pair_distance": distance,
                    "min_observations": args.min_observations,
                },
                "runs": runs,
                "summary": summary,
                "objects": objects,
            })
            print(
                f"condition {condition_number}/{total}: interval={interval}, radius={distance:g}; "
                f"{summary['persistent_candidates']} persistent / {summary['observed_candidates']} observed"
            )

    output = {
        "schema_version": 1,
        "claim_boundary": (
            "This compares detector settings while holding v1 dynamics and seeds fixed. "
            "It reports distributional sensitivity, not one-to-one object identity or autonomy."
        ),
        "experiment": {
            "name": "v1_pair_detector_sensitivity",
            "grid_size": args.N,
            "frames_per_run": args.frames,
            "seeds": list(range(args.seed_start, args.seed_start + args.seeds)),
            "recognition_threshold": {
                "min_age_frames": args.min_age,
                "min_observations_floor": args.min_observations_floor,
                "note": "Each condition raises its observation count as needed to preserve the same elapsed-time threshold.",
            },
            "parameters": {key: getattr(args, key) for key in ("alpha", "gamma", "kappa", "curv", "lock")},
        },
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {len(conditions)} detector conditions to {args.output}")


if __name__ == "__main__":
    main()
