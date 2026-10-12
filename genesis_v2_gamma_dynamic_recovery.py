"""Motion-aware causal recovery tracking for v2-gamma candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_v2_beta.objects import Region, detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step
from src.genesis_v2_gamma.interventions import apply_boundary, perimeter_boundary_mean
from src.genesis_v2_gamma.probes import translated_background_mask


def iou(first: np.ndarray, second: np.ndarray) -> float:
    union = np.logical_or(first, second).sum()
    return float(np.logical_and(first, second).sum() / union) if union else 0.0


class DynamicTrack:
    """Follow one candidate by overlap with its immediately prior state."""

    def __init__(self, initial: Region, frame: int, max_missed: int):
        self.mask = initial.mask
        self.max_missed = max_missed
        self.missed = 0
        self.ended = False
        self.history = []
        self.observe(frame, initial, 1.0)

    def observe(self, frame: int, region: Region, overlap: float) -> None:
        self.mask = region.mask
        self.missed = 0
        self.history.append({"frame": frame, "area": region.area, "centroid": [region.centroid_y, region.centroid_x], "coherence": region.coherence, "boundary_contrast": region.boundary_contrast, "overlap_with_previous": overlap})

    def update(self, frame: int, regions: list[Region], min_iou: float) -> None:
        if self.ended:
            return
        matches = [(iou(self.mask, region.mask), region) for region in regions]
        overlap, region = max(matches, key=lambda item: item[0], default=(0.0, None))
        if region is not None and overlap >= min_iou:
            self.observe(frame, region, overlap)
            return
        self.missed += 1
        if self.missed > self.max_missed:
            self.ended = True

    def report(self) -> dict:
        return {"status": "ended" if self.ended else "active", "samples": len(self.history), "last_seen_frame": self.history[-1]["frame"], "max_area": max(row["area"] for row in self.history), "final_area": self.history[-1]["area"], "history": self.history}


def run_one(args, seed: int, params: GammaParams) -> dict:
    state = GammaState(args.N, seed=seed)
    for _ in range(args.warmup_frames):
        step(state, params)
    domains = detect_relation_domains(state, args.cutoff, args.min_area)
    if not domains:
        return {"seed": seed, "status": "no_candidate"}
    selected = max(domains, key=lambda domain: domain.area)
    occupied = np.logical_or.reduce([domain.mask for domain in domains])
    background = translated_background_mask(selected.mask, occupied, max_overlap=args.max_background_overlap)
    if background is None:
        return {"seed": seed, "status": "no_background_mask"}
    control, candidate_weaken, background_weaken = state.clone(), state.clone(), state.clone()
    apply_boundary(candidate_weaken, selected.mask, params, "weaken", args.strength)
    apply_boundary(background_weaken, background, params, "weaken", args.strength)
    branches = {"control": control, "candidate_weaken": candidate_weaken, "background_weaken": background_weaken}
    tracks = {name: DynamicTrack(selected, 0, args.max_missed) for name in branches}
    boundary_series = {name: [] for name in branches}
    for frame in range(args.recovery_frames + 1):
        if frame % args.sample_interval == 0 or frame == args.recovery_frames:
            for name, branch in branches.items():
                regions = detect_relation_domains(branch, args.cutoff, args.min_area)
                if frame > 0:
                    tracks[name].update(frame, regions, args.min_iou)
                boundary_series[name].append({"frame": frame, "reference_perimeter_boundary": perimeter_boundary_mean(branch, selected.mask)})
        if frame < args.recovery_frames:
            for branch in branches.values():
                step(branch, params)
    return {"seed": seed, "status": "measured", "candidate": {"area": selected.area, "initial_perimeter_boundary": perimeter_boundary_mean(state, selected.mask)}, "tracks": {name: track.report() for name, track in tracks.items()}, "boundary_series": boundary_series}


def main() -> None:
    parser = argparse.ArgumentParser(description="Track gamma candidate continuity after matched boundary weakening.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--warmup-frames", type=int, default=1_200)
    parser.add_argument("--recovery-frames", type=int, default=1_000)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--min-iou", type=float, default=0.15)
    parser.add_argument("--max-missed", type=int, default=2)
    parser.add_argument("--strength", type=float, default=0.85)
    parser.add_argument("--max-background-overlap", type=float, default=0.25)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_dynamic_recovery.json"))
    args = parser.parse_args()
    if args.N < 8 or args.warmup_frames < 1 or args.recovery_frames < 1 or args.seeds < 1 or args.sample_interval < 1 or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1 or not 0.0 <= args.min_iou <= 1.0 or args.max_missed < 0 or not 0.0 <= args.strength <= 1.0 or not 0.0 <= args.max_background_overlap <= 1.0:
        raise SystemExit("Invalid dynamic-recovery arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    runs = [run_one(args, seed, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    for run in runs:
        if run["status"] != "measured":
            print(f"seed={run['seed']}: {run['status']}"); continue
        print(f"seed={run['seed']}: " + "; ".join(f"{name}={track['status']}@{track['last_seen_frame']} ({track['samples']} samples)" for name, track in run["tracks"].items()))
    report = {"schema_version": 1, "claim_boundary": "This uses incremental overlap to track a candidate through movement or transformation after boundary weakening. It measures model continuity, not autonomous identity or metaphysical validity.", "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)}, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma dynamic-recovery report to {args.output}")


if __name__ == "__main__":
    main()
