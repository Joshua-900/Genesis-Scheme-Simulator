"""Held-out object-level forecast gate for tracked V1 vortex-antivortex pairs.

The test asks whether a pair's coarse relational state predicts strict
constituent-ID survival at a future horizon better than generic local field
statistics around the same pair midpoint.  It observes the simulation only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from genesis_v1_compression_ablation import RULES, make_params
from genesis_v1_local_structure_perturbation import disk_mask
from src.genesis_grid import GenesisState, diagnostics, rules_locking, step
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker, sample_line_stats


FIELD_FEATURES = (
    "pair_age",
    "local_orientation_coherence",
    "local_tension_mean",
    "local_tension_std",
    "local_compression_mean",
    "local_compression_std",
)
RELATIONAL_FEATURES = (
    "pair_age",
    "pair_length",
    "closing_speed",
    "line_unity",
    "line_compression",
    "relational_activity",
)


def local_field_features(state: GenesisState, pair, radius: float) -> dict[str, float]:
    """Generic raw-field summary in a disk around a pair's midpoint."""
    theta = np.asarray(to_cpu(state.theta))
    tau = np.asarray(to_cpu(state.tau))
    compression = np.asarray(to_cpu(state.C))
    mask = disk_mask(theta.shape[0], pair.midpoint_x, pair.midpoint_y, radius)
    theta_values = theta[mask]
    return {
        "local_orientation_coherence": float(
            np.hypot(np.mean(np.cos(theta_values)), np.mean(np.sin(theta_values)))
        ),
        "local_tension_mean": float(np.mean(tau[mask])),
        "local_tension_std": float(np.std(tau[mask])),
        "local_compression_mean": float(np.mean(compression[mask])),
        "local_compression_std": float(np.std(compression[mask])),
    }


def pair_record(seed: int, frame: int, pair, state: GenesisState, unity: np.ndarray, radius: float) -> dict:
    line_unity, _ = sample_line_stats(
        unity, pair.plus_x, pair.plus_y, pair.minus_x, pair.minus_y
    )
    return {
        "seed": seed,
        "frame": frame,
        "pair_key": [pair.plus_id, pair.minus_id],
        "pair_age": float(pair.age),
        "pair_length": float(pair.length),
        "closing_speed": float(pair.closing_speed),
        "line_unity": float(line_unity),
        "line_compression": float(pair.mean_C_avg_along_line),
        "relational_activity": float(pair.pair_tau),
        **local_field_features(state, pair, radius),
    }


def select_pairs(active, maximum: int):
    """Sample both young and old active pairs without using future information."""
    ordered = sorted(active, key=lambda pair: (pair.age, pair.id))
    if len(ordered) <= maximum:
        return ordered
    lower_count = maximum // 2
    return ordered[:lower_count] + ordered[-(maximum - lower_count) :]


def collect_seed(seed: int, args) -> list[dict]:
    np.random.seed(seed)
    state = GenesisState(args.N, dt=0.05)
    params = make_params(args.kappa)
    defects = DefectTracker()
    pairs = PairLineTracker(max_pair_distance=args.max_pair_distance)
    compression_average = np.zeros((args.N, args.N), dtype=np.float64)
    pending: dict[int, list[dict]] = {}
    records: list[dict] = []

    for frame in range(1, args.frames + 1):
        step(state, params, RULES, post=rules_locking.locking_postprocess)
        if frame % args.sample_interval:
            continue

        plus, minus, _ = diagnostics.detect_vortices(state)
        detections = [(col, row, 1) for row, col in plus] + [(col, row, -1) for row, col in minus]
        compression = np.asarray(to_cpu(state.C), dtype=np.float64)
        compression_average = 0.95 * compression_average + 0.05 * compression
        tracks = defects.update(frame, detections, C=compression, C_avg=compression_average)
        active = pairs.update(frame=frame, defect_tracks=tracks, C=compression, C_avg=compression_average)
        active_keys = {(pair.plus_id, pair.minus_id) for pair in active}

        for record in pending.pop(frame, []):
            record["future_survival"] = int(tuple(record["pair_key"]) in active_keys)
            records.append(record)

        if args.warmup_frames <= frame <= args.frames - args.horizon_frames:
            unity = diagnostics.compute_unity(state)
            snapshots = [
                pair_record(seed, frame, pair, state, unity, args.local_radius)
                for pair in select_pairs(active, args.max_pairs_per_sample)
            ]
            pending.setdefault(frame + args.horizon_frames, []).extend(snapshots)

    return records


def matrix(records: list[dict], names: tuple[str, ...]) -> np.ndarray:
    return np.asarray([[record[name] for name in names] for record in records], dtype=float)


def ridge_predict(train: list[dict], test: list[dict], names: tuple[str, ...], ridge: float) -> np.ndarray:
    x_train, x_test = matrix(train, names), matrix(test, names)
    mean, scale = x_train.mean(axis=0), x_train.std(axis=0)
    scale[scale < 1e-12] = 1.0
    x_train = np.column_stack((np.ones(len(x_train)), (x_train - mean) / scale))
    x_test = np.column_stack((np.ones(len(x_test)), (x_test - mean) / scale))
    y_train = np.asarray([record["future_survival"] for record in train], dtype=float)
    penalty = np.eye(x_train.shape[1]) * ridge
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(x_train.T @ x_train + penalty, x_train.T @ y_train)
    return np.clip(x_test @ coefficients, 0.0, 1.0)


def auc(actual: np.ndarray, prediction: np.ndarray) -> float | None:
    positives = int(np.sum(actual == 1))
    negatives = int(np.sum(actual == 0))
    if not positives or not negatives:
        return None
    ranks = rankdata(prediction)
    return float((np.sum(ranks[actual == 1]) - positives * (positives + 1) / 2.0) / (positives * negatives))


def score(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float | None]:
    return {
        "brier": float(np.mean((actual - prediction) ** 2)),
        "auc": auc(actual, prediction),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Held-out V1 pair object-level forecast gate.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=3_000)
    parser.add_argument("--warmup-frames", type=int, default=500)
    parser.add_argument("--horizon-frames", type=int, default=200)
    parser.add_argument("--sample-interval", type=int, default=100)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--max-pairs-per-sample", type=int, default=24)
    parser.add_argument("--local-radius", type=float, default=5.0)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--kappa", type=float, default=0.10)
    parser.add_argument("--ridge", type=float, default=0.20)
    parser.add_argument("--output", type=Path, default=Path("results/v1_pair_object_gate.json"))
    args = parser.parse_args()
    if args.horizon_frames % args.sample_interval:
        parser.error("--horizon-frames must be divisible by --sample-interval")
    if args.frames <= args.warmup_frames + args.horizon_frames or args.seeds < 3:
        parser.error("Need at least three seeds and frames beyond warmup plus horizon.")

    records = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        seed_records = collect_seed(seed, args)
        records.extend(seed_records)
        print(f"seed={seed}: {len(seed_records)} forecast records")

    folds = []
    pooled_actual, pooled_field, pooled_relational = [], [], []
    for held_seed in range(args.seed_start, args.seed_start + args.seeds):
        train = [record for record in records if record["seed"] != held_seed]
        test = [record for record in records if record["seed"] == held_seed]
        actual = np.asarray([record["future_survival"] for record in test], dtype=float)
        field_prediction = ridge_predict(train, test, FIELD_FEATURES, args.ridge)
        relational_prediction = ridge_predict(train, test, RELATIONAL_FEATURES, args.ridge)
        field_score = score(actual, field_prediction)
        relational_score = score(actual, relational_prediction)
        folds.append({
            "held_seed": held_seed,
            "records": len(test),
            "survival_fraction": float(np.mean(actual)),
            "field_baseline": field_score,
            "relational_model": relational_score,
            "brier_reduction_fraction": float(
                (field_score["brier"] - relational_score["brier"]) / field_score["brier"]
            ) if field_score["brier"] else 0.0,
        })
        pooled_actual.extend(actual)
        pooled_field.extend(field_prediction)
        pooled_relational.extend(relational_prediction)

    actual = np.asarray(pooled_actual)
    field_score = score(actual, np.asarray(pooled_field))
    relational_score = score(actual, np.asarray(pooled_relational))
    reduction = (field_score["brier"] - relational_score["brier"]) / field_score["brier"]
    wins = sum(fold["relational_model"]["brier"] < fold["field_baseline"]["brier"] for fold in folds)
    gate = {
        "required_brier_reduction_fraction": 0.05,
        "required_held_seed_wins": 7,
        "pooled_brier_reduction_fraction": float(reduction),
        "held_seed_wins": wins,
        "passed": bool(reduction >= 0.05 and wins >= 7),
    }
    report = {
        "schema_version": 1,
        "claim_boundary": (
            "Passing supports a reproducible relational object type in this V1 regime. "
            "It does not establish full autonomy, causal closure, natural kinds, or metaphysical claims."
        ),
        "experiment": {"name": "v1_pair_object_level_forecast_gate", "parameters": {**vars(args), "output": str(args.output)}},
        "feature_sets": {"generic_local_field": FIELD_FEATURES, "relational_object_state": RELATIONAL_FEATURES},
        "records": records,
        "folds": folds,
        "summary": {"records": len(records), "field_baseline": field_score, "relational_model": relational_score, "gate": gate},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
