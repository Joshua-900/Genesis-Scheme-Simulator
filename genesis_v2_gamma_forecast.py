"""Forecast whether gamma candidate attributes predict future identity."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step
from src.genesis_v2_gamma.probes import best_overlap


def boundary_permeability(state, mask: np.ndarray) -> float:
    rx, ry = np.asarray(to_cpu(state.rx)), np.asarray(to_cpu(state.ry))
    right = mask & ~np.roll(mask, -1, 1)
    down = mask & ~np.roll(mask, -1, 0)
    values = [rx[right], ry[down]]
    values = [value for value in values if value.size]
    return float(np.mean(np.concatenate(values))) if values else 0.0


def background_mask(mask: np.ndarray, occupied: np.ndarray) -> np.ndarray | None:
    """Translate a candidate shape into the least occupied available location."""
    height, width = mask.shape
    shifts = [(height // 2, width // 2), (height // 2, width // 3), (height // 3, width // 2), (height // 3, 2 * width // 3), (2 * height // 3, width // 3), (height // 4, width // 2), (height // 2, width // 4)]
    options = []
    for shift_y, shift_x in shifts:
        translated = np.roll(mask, (shift_y, shift_x), axis=(0, 1))
        options.append((float(np.logical_and(translated, occupied).sum() / translated.sum()), translated))
    overlap, selected = min(options, key=lambda option: option[0])
    return selected if overlap <= 0.10 else None


def run_one(args, seed: int, params: GammaParams) -> dict:
    state = GammaState(args.N, seed=seed)
    for _ in range(args.warmup_frames):
        step(state, params)
    records = []
    for checkpoint in range(args.checkpoints):
        domains = detect_relation_domains(state, args.cutoff, args.min_area)
        occupied = np.logical_or.reduce([domain.mask for domain in domains]) if domains else np.zeros((args.N, args.N), dtype=bool)
        future = state.clone()
        for _ in range(args.horizon_frames):
            step(future, params)
        future_domains = detect_relation_domains(future, args.cutoff, args.min_area)
        for rank, domain in enumerate(sorted(domains, key=lambda item: item.area, reverse=True)[:args.candidates_per_sample], start=1):
            background = background_mask(domain.mask, occupied)
            if background is None:
                continue
            candidate_overlap, _ = best_overlap(domain.mask, future_domains)
            background_overlap, _ = best_overlap(background, future_domains)
            records.append({
                "checkpoint": checkpoint,
                "rank": rank,
                "area_fraction": domain.area / (args.N * args.N),
                "coherence": domain.coherence,
                "boundary_contrast": domain.boundary_contrast,
                "boundary_permeability": boundary_permeability(state, domain.mask),
                "future_identity_overlap": candidate_overlap,
                "background_future_overlap": background_overlap,
                "identity_advantage": candidate_overlap - background_overlap,
            })
        for _ in range(args.sample_interval):
            step(state, params)
    return {"seed": seed, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test whether gamma candidate attributes forecast future identity better than background masks.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--warmup-frames", type=int, default=1_200)
    parser.add_argument("--checkpoints", type=int, default=5)
    parser.add_argument("--sample-interval", type=int, default=100)
    parser.add_argument("--horizon-frames", type=int, default=200)
    parser.add_argument("--candidates-per-sample", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_forecast.json"))
    args = parser.parse_args()
    if args.N < 8 or args.warmup_frames < 1 or args.checkpoints < 1 or args.sample_interval < 1 or args.horizon_frames < 1 or args.candidates_per_sample < 1 or args.seeds < 1 or not 0.0 <= args.cutoff <= 1.0 or args.min_area < 1:
        raise SystemExit("Invalid forecast arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    runs = [run_one(args, seed, params) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    records = [record for run in runs for record in run["records"]]
    aggregate = {"record_count": len(records), "median_candidate_overlap": statistics.median(record["future_identity_overlap"] for record in records) if records else None, "median_background_overlap": statistics.median(record["background_future_overlap"] for record in records) if records else None, "median_identity_advantage": statistics.median(record["identity_advantage"] for record in records) if records else None, "candidate_win_fraction": sum(record["identity_advantage"] > 0.0 for record in records) / len(records) if records else None}
    print(f"records={aggregate['record_count']}; candidate/background median overlap={aggregate['median_candidate_overlap']}/{aggregate['median_background_overlap']}; advantage={aggregate['median_identity_advantage']}; wins={aggregate['candidate_win_fraction']}")
    report = {"schema_version": 1, "claim_boundary": "This compares observer-defined candidate masks with equal-shape translated background masks. It tests predictive identity persistence, not autonomous causal closure or natural kinds.", "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params)}, "aggregate": aggregate, "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma forecast report to {args.output}")


if __name__ == "__main__":
    main()
