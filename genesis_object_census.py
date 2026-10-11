"""Headless census of conservative vortex-antivortex object candidates.

This program observes the existing v1 simulation.  It never contributes to
the rule pipeline or modifies a simulation state.  A recognized candidate is
only a persistent tracked relation, not evidence of autonomy or metaphysics.

Example:
    python genesis_object_census.py --seeds 8 --frames 5000 --output results/pair_census.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from genesis_measure import RULES, make_params
from src.genesis_grid import GenesisState, diagnostics, rules_locking, step
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker, sample_line_stats


@dataclass
class PairLifecycle:
    """Aggregate, read-only observations of one tracked pair candidate."""

    run: int
    pair_id: int
    plus_id: int
    minus_id: int
    birth_frame: int
    last_seen_frame: int
    observations: int = 0
    max_age: int = 0
    min_length: float = float("inf")
    max_length: float = 0.0
    mean_length_total: float = 0.0
    mean_line_unity_total: float = 0.0
    mean_compression_total: float = 0.0
    max_relational_activity: float = 0.0
    events: list[str] = field(default_factory=list)
    samples: list[dict[str, float | int]] = field(default_factory=list)

    def observe(self, frame: int, pair: Any, line_unity: float) -> None:
        self.last_seen_frame = int(pair.last_seen_frame)
        self.observations += 1
        self.max_age = max(self.max_age, int(pair.age))
        self.min_length = min(self.min_length, float(pair.length))
        self.max_length = max(self.max_length, float(pair.length))
        self.mean_length_total += float(pair.length)
        self.mean_line_unity_total += float(line_unity)
        self.mean_compression_total += float(pair.mean_C_avg_along_line)
        self.max_relational_activity = max(self.max_relational_activity, float(pair.pair_tau))
        self.samples.append({
            "frame": frame,
            "midpoint_x": float(pair.midpoint_x),
            "midpoint_y": float(pair.midpoint_y),
            "orientation": float(pair.orientation),
            "length": float(pair.length),
            "closing_speed": float(pair.closing_speed),
            "line_unity": float(line_unity),
            "mean_compression": float(pair.mean_C_avg_along_line),
            "relational_activity": float(pair.pair_tau),
        })

    def report(self, min_age: int, min_observations: int) -> dict[str, Any]:
        mean = lambda total: total / self.observations if self.observations else 0.0
        return {
            "run": self.run,
            "object_type": "vortex_antivortex_pair_candidate",
            "pair_id": self.pair_id,
            "constituents": {"plus_defect_id": self.plus_id, "minus_defect_id": self.minus_id},
            "birth_frame": self.birth_frame,
            "last_seen_frame": self.last_seen_frame,
            "persistence": {"max_age_frames": self.max_age, "observations": self.observations},
            "extent": {"min_length": self.min_length if self.observations else None, "max_length": self.max_length},
            "internal_state": {
                "mean_length": mean(self.mean_length_total),
                "mean_line_unity": mean(self.mean_line_unity_total),
                "mean_compression": mean(self.mean_compression_total),
                "max_relational_activity": self.max_relational_activity,
            },
            "events": self.events,
            "observations": self.samples,
            "recognition": {
                "status": "persistent_candidate" if self.max_age >= min_age and self.observations >= min_observations else "transient_candidate",
                "min_age_frames": min_age,
                "min_observations": min_observations,
            },
        }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Headless census of vortex-antivortex pair candidates.")
    p.add_argument("--N", type=int, default=100, help="Square-grid side length.")
    p.add_argument("--frames", type=int, default=10_000, help="Simulation frames per seed.")
    p.add_argument("--seeds", type=int, default=5, help="Number of deterministic seeds to run.")
    p.add_argument("--seed-start", type=int, default=1, help="First seed; subsequent runs increment by one.")
    p.add_argument("--sample-interval", type=int, default=25, help="Frames between object observations.")
    p.add_argument("--min-age", type=int, default=100, help="Frames required for persistent-candidate recognition.")
    p.add_argument("--min-observations", type=int, default=4, help="Observations required for persistent-candidate recognition.")
    p.add_argument("--max-pair-distance", type=float, default=64.0, help="Maximum opposite-charge pairing distance.")
    p.add_argument("--alpha", type=float, default=0.3)
    p.add_argument("--gamma", type=float, default=0.01)
    p.add_argument("--kappa", type=float, default=0.05)
    p.add_argument("--curv", type=float, default=0.04)
    p.add_argument("--lock", type=float, default=0.96)
    p.add_argument("--output", type=Path, default=Path("results/pair_census.json"))
    return p


def run_one(args: argparse.Namespace, run: int, seed: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    np.random.seed(seed)
    state = GenesisState(args.N, dt=0.05)
    params = make_params(alpha=args.alpha, gamma=args.gamma, kappa=args.kappa, curv=args.curv, lock=args.lock)
    defects = DefectTracker()
    pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
    lifecycles: dict[int, PairLifecycle] = {}
    compression_average = np.zeros((args.N, args.N), dtype=np.float64)
    average_decay = 0.95

    for frame in range(1, args.frames + 1):
        step(state, params, RULES, post=rules_locking.locking_postprocess)
        if frame % args.sample_interval:
            continue

        plus, minus, _ = diagnostics.detect_vortices(state)
        # Diagnostics return (row, col); trackers consistently use (x=col, y=row).
        detections = [(col, row, 1) for row, col in plus] + [(col, row, -1) for row, col in minus]
        C = np.asarray(to_cpu(state.C), dtype=np.float64)
        compression_average = average_decay * compression_average + (1.0 - average_decay) * C
        tracks = defects.update(frame, detections, C=C, C_avg=compression_average)
        active_pairs = pairs.update(frame=frame, defect_tracks=tracks, C=C, C_avg=compression_average)
        unity = diagnostics.compute_unity(state)

        for pair in active_pairs:
            record = lifecycles.setdefault(
                pair.id,
                PairLifecycle(run, pair.id, pair.plus_id, pair.minus_id, pair.birth_frame, pair.last_seen_frame),
            )
            line_unity, _ = sample_line_stats(unity, pair.plus_x, pair.plus_y, pair.minus_x, pair.minus_y)
            record.observe(frame, pair, line_unity)

    for event in pairs.events:
        pair_id = event.get("pair_id")
        if pair_id in lifecycles:
            lifecycles[pair_id].events.append(str(event["type"]))

    reports = [item.report(args.min_age, args.min_observations) for item in lifecycles.values()]
    persistent = sum(item["recognition"]["status"] == "persistent_candidate" for item in reports)
    summary = {
        "run": run,
        "seed": seed,
        "observed_candidates": len(reports),
        "persistent_candidates": persistent,
        "final_defect_summary": defects.summary(),
        "final_pair_summary": pairs.summary(),
    }
    return reports, summary


def main() -> None:
    args = parser().parse_args()
    if args.sample_interval < 1 or args.seeds < 1:
        raise SystemExit("--sample-interval and --seeds must both be positive.")

    all_objects: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    for run, seed in enumerate(range(args.seed_start, args.seed_start + args.seeds), start=1):
        objects, summary = run_one(args, run, seed)
        all_objects.extend(objects)
        runs.append(summary)
        print(f"run {run}/{args.seeds}, seed={seed}: {summary['persistent_candidates']} persistent / {summary['observed_candidates']} observed")

    output = {
        "schema_version": 1,
        "claim_boundary": "Persistent candidate status is a measurement threshold, not evidence of autonomy, natural kinds, or metaphysical claims.",
        "experiment": {
            "name": "v1_vortex_antivortex_pair_census",
            "grid_size": args.N,
            "frames_per_run": args.frames,
            "sample_interval": args.sample_interval,
            "recognition_threshold": {"min_age_frames": args.min_age, "min_observations": args.min_observations},
            "parameters": {key: getattr(args, key) for key in ("alpha", "gamma", "kappa", "curv", "lock", "max_pair_distance")},
        },
        "runs": runs,
        "objects": all_objects,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_objects)} candidate records to {args.output}")


if __name__ == "__main__":
    main()
