"""Matched local structural perturbation test for a tracked V1 pair candidate."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from genesis_v1_compression_ablation import RULES, make_params
from src.genesis_grid import GenesisState, diagnostics, rules_locking, step
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLine, PairLineTracker


def update_trackers(state, frame: int, defects: DefectTracker, pairs: PairLineTracker, compression_average: np.ndarray):
    plus, minus, _ = diagnostics.detect_vortices(state)
    detections = [(col, row, 1) for row, col in plus] + [(col, row, -1) for row, col in minus]
    compression = np.asarray(to_cpu(state.C), dtype=np.float64)
    compression_average = 0.95 * compression_average + 0.05 * compression
    tracks = defects.update(frame, detections, C=compression, C_avg=compression_average)
    active = pairs.update(frame=frame, defect_tracks=tracks, C=compression, C_avg=compression_average)
    return active, compression_average


def select_candidate(active_pairs: list[PairLine]) -> PairLine | None:
    if not active_pairs:
        return None
    return max(active_pairs, key=lambda pair: (pair.mean_C_avg_along_line, pair.age))


def disk_mask(N: int, x: float, y: float, radius: float) -> np.ndarray:
    rows, cols = np.indices((N, N))
    dx = np.minimum(np.abs(cols - x), N - np.abs(cols - x))
    dy = np.minimum(np.abs(rows - y), N - np.abs(rows - y))
    return dx * dx + dy * dy <= radius * radius


def choose_background(N: int, candidate: PairLine, radius: float, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    protected = ((candidate.midpoint_x, candidate.midpoint_y), (candidate.plus_x, candidate.plus_y), (candidate.minus_x, candidate.minus_y))
    minimum = max(2.0 * radius, 8.0)
    for _ in range(2_000):
        x, y = float(rng.integers(N)), float(rng.integers(N))
        if all(np.hypot(x - px, y - py) >= minimum for px, py in protected):
            return x, y
    raise RuntimeError("Could not find a background location separated from the selected candidate.")


def weaken_structure(state: GenesisState, mask: np.ndarray, strength: float) -> None:
    """Remove a declared fraction of stored structural state inside one mask."""
    retained = 1.0 - strength
    state.tau = state.tau * (1.0 - strength * mask)
    state.ux = state.ux * (1.0 - strength * mask)
    state.uy = state.uy * (1.0 - strength * mask)
    state.C = state.C * retained * mask + state.C * (~mask)


def follow_branch(state, defects, pairs, compression_average, candidate_key, start_frame: int, args: argparse.Namespace) -> dict:
    seen = 0
    last_seen = start_frame
    for frame in range(start_frame + 1, start_frame + args.follow_frames + 1):
        step(state, make_params(args.kappa), RULES, post=rules_locking.locking_postprocess)
        if frame % args.sample_interval:
            continue
        active, compression_average = update_trackers(state, frame, defects, pairs, compression_average)
        if any((pair.plus_id, pair.minus_id) == candidate_key for pair in active):
            seen += 1
            last_seen = frame
    return {"continuation_samples": seen, "last_seen_frame": last_seen, "survived_to_end": last_seen == start_frame + args.follow_frames}


def run_seed(seed: int, args: argparse.Namespace) -> dict:
    np.random.seed(seed)
    state = GenesisState(args.N, dt=0.05)
    params = make_params(args.kappa)
    defects = DefectTracker()
    pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
    compression_average = np.zeros((args.N, args.N), dtype=np.float64)
    active: list[PairLine] = []

    for frame in range(1, args.burn_in_frames + 1):
        step(state, params, RULES, post=rules_locking.locking_postprocess)
        if frame % args.sample_interval == 0:
            active, compression_average = update_trackers(state, frame, defects, pairs, compression_average)

    candidate = select_candidate(active)
    if candidate is None:
        return {"seed": seed, "status": "no_candidate"}

    candidate_key = (candidate.plus_id, candidate.minus_id)
    background_x, background_y = choose_background(args.N, candidate, args.radius, seed)
    target_mask = disk_mask(args.N, candidate.midpoint_x, candidate.midpoint_y, args.radius)
    background_mask = disk_mask(args.N, background_x, background_y, args.radius)

    branches = {}
    for name, mask in (("untouched", None), ("candidate_neighborhood", target_mask), ("background", background_mask)):
        branch_state = copy.deepcopy(state)
        branch_defects = copy.deepcopy(defects)
        branch_pairs = copy.deepcopy(pairs)
        branch_average = compression_average.copy()
        if mask is not None:
            weaken_structure(branch_state, mask, args.weaken_strength)
        branches[name] = follow_branch(branch_state, branch_defects, branch_pairs, branch_average, candidate_key, args.burn_in_frames, args)

    return {
        "seed": seed,
        "status": "tested",
        "candidate": {
            "pair_key": candidate_key,
            "age": candidate.age,
            "midpoint": [candidate.midpoint_x, candidate.midpoint_y],
            "mean_line_compression": candidate.mean_C_avg_along_line,
        },
        "background_center": [background_x, background_y],
        "branches": branches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Matched candidate-neighborhood versus background structural perturbation.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--burn-in-frames", type=int, default=1_000)
    parser.add_argument("--follow-frames", type=int, default=1_000)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--kappa", type=float, default=0.1)
    parser.add_argument("--radius", type=float, default=5.0)
    parser.add_argument("--weaken-strength", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("results/v1_local_structure_perturbation.json"))
    args = parser.parse_args()
    if args.N < 4 or args.burn_in_frames < 1 or args.follow_frames < 1 or args.seeds < 1:
        raise SystemExit("Grid size, frame counts, and seeds must be positive.")

    runs = [run_seed(seed, args) for seed in range(args.seed_start, args.seed_start + args.seeds)]
    tested = [run for run in runs if run["status"] == "tested"]
    summary = {}
    for branch in ("untouched", "candidate_neighborhood", "background"):
        survival = [run["branches"][branch]["survived_to_end"] for run in tested]
        samples = [run["branches"][branch]["continuation_samples"] for run in tested]
        summary[branch] = {
            "tested": len(tested),
            "survived_to_end": int(sum(survival)),
            "median_continuation_samples": float(np.median(samples)) if samples else 0.0,
        }
    parameters = vars(args).copy()
    parameters["output"] = str(args.output)
    output = {
        "schema_version": 1,
        "claim_boundary": "This tests strict continuation of a tracked pair after a localized structural perturbation; it does not establish higher-order objects.",
        "experiment": {"name": "v1_matched_local_structure_perturbation", "parameters": parameters},
        "runs": runs,
        "summary": summary,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
