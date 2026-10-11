"""Held-out attribute-prediction test for v2-gamma candidate persistence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_gamma import GammaParams, GammaState, step
from src.genesis_v2_gamma.probes import best_overlap


BASE_FEATURES = ("area_fraction", "lattice_size", "cutoff")
FULL_FEATURES = BASE_FEATURES + ("coherence", "boundary_contrast", "boundary_permeability")


def boundary_permeability(state, mask: np.ndarray) -> float:
    rx, ry = np.asarray(to_cpu(state.rx)), np.asarray(to_cpu(state.ry))
    right = mask & ~np.roll(mask, -1, 1)
    down = mask & ~np.roll(mask, -1, 0)
    values = [value for value in (rx[right], ry[down]) if value.size]
    return float(np.mean(np.concatenate(values))) if values else 0.0


def collect_seed(N: int, cutoff: float, seed: int, args, params) -> list[dict]:
    state = GammaState(N, seed=seed)
    for _ in range(args.warmup_frames):
        step(state, params)
    records = []
    for checkpoint in range(args.checkpoints):
        domains = detect_relation_domains(state, cutoff, args.min_area)
        future = state.clone()
        for _ in range(args.horizon_frames):
            step(future, params)
        future_domains = detect_relation_domains(future, cutoff, args.min_area)
        for rank, domain in enumerate(sorted(domains, key=lambda item: item.area, reverse=True)[:args.candidates_per_sample], start=1):
            overlap, _ = best_overlap(domain.mask, future_domains)
            records.append({"seed": seed, "N": N, "cutoff": cutoff, "checkpoint": checkpoint, "rank": rank, "area_fraction": domain.area / (N * N), "lattice_size": float(N), "coherence": domain.coherence, "boundary_contrast": domain.boundary_contrast, "boundary_permeability": boundary_permeability(state, domain.mask), "future_identity_overlap": overlap})
        for _ in range(args.sample_interval):
            step(state, params)
    return records


def matrix(records: list[dict], names: tuple[str, ...]) -> np.ndarray:
    return np.asarray([[record[name] for name in names] for record in records], dtype=float)


def fit_predict(train: list[dict], test: list[dict], names: tuple[str, ...], ridge: float) -> np.ndarray:
    x_train, x_test = matrix(train, names), matrix(test, names)
    mean, scale = x_train.mean(axis=0), x_train.std(axis=0)
    scale[scale < 1e-12] = 1.0
    x_train = (x_train - mean) / scale
    x_test = (x_test - mean) / scale
    x_train = np.column_stack((np.ones(len(x_train)), x_train))
    x_test = np.column_stack((np.ones(len(x_test)), x_test))
    y_train = np.asarray([record["future_identity_overlap"] for record in train])
    penalty = np.eye(x_train.shape[1]) * ridge
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(x_train.T @ x_train + penalty, x_train.T @ y_train)
    return x_test @ coefficients


def score(actual: np.ndarray, predicted: np.ndarray, reference_mean: float) -> dict[str, float]:
    errors = actual - predicted
    return {"mae": float(np.mean(np.abs(errors))), "rmse": float(np.sqrt(np.mean(errors * errors))), "r2_against_train_mean": float(1.0 - np.sum(errors * errors) / np.sum((actual - reference_mean) ** 2)) if np.sum((actual - reference_mean) ** 2) > 1e-12 else 0.0}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate whether gamma region attributes predict held-out persistence.")
    parser.add_argument("--sizes", type=int, nargs="+", default=[64, 96])
    parser.add_argument("--cutoffs", type=float, nargs="+", default=[0.70, 0.75, 0.80])
    parser.add_argument("--seeds", type=int, default=6)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--warmup-frames", type=int, default=1_200)
    parser.add_argument("--checkpoints", type=int, default=4)
    parser.add_argument("--sample-interval", type=int, default=100)
    parser.add_argument("--horizon-frames", type=int, default=200)
    parser.add_argument("--candidates-per-sample", type=int, default=2)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--ridge", type=float, default=0.20)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    parser.add_argument("--boundary-rate", type=float, default=0.18)
    parser.add_argument("--boundary-decay", type=float, default=0.04)
    parser.add_argument("--output", type=Path, default=Path("results/v2_gamma_attribute_model.json"))
    args = parser.parse_args()
    if any(size < 8 for size in args.sizes) or args.seeds < 3 or args.checkpoints < 1 or args.sample_interval < 1 or args.horizon_frames < 1 or args.candidates_per_sample < 1 or args.min_area < 1 or args.ridge < 0.0:
        raise SystemExit("Invalid attribute-model arguments.")
    params = GammaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain, boundary_rate=args.boundary_rate, boundary_decay=args.boundary_decay)
    records = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        for N in args.sizes:
            for cutoff in args.cutoffs:
                condition_records = collect_seed(N, cutoff, seed, args, params)
                records.extend(condition_records)
                print(f"seed={seed}; N={N}; cutoff={cutoff:.2f}; records={len(condition_records)}")
    folds = []
    all_actual, all_baseline, all_full = [], [], []
    for held_seed in range(args.seed_start, args.seed_start + args.seeds):
        train = [record for record in records if record["seed"] != held_seed]
        test = [record for record in records if record["seed"] == held_seed]
        if not train or not test:
            continue
        actual = np.asarray([record["future_identity_overlap"] for record in test])
        baseline = fit_predict(train, test, BASE_FEATURES, args.ridge)
        full = fit_predict(train, test, FULL_FEATURES, args.ridge)
        train_mean = float(np.mean([record["future_identity_overlap"] for record in train]))
        folds.append({"held_seed": held_seed, "records": len(test), "baseline": score(actual, baseline, train_mean), "full": score(actual, full, train_mean)})
        all_actual.extend(actual); all_baseline.extend(baseline); all_full.extend(full)
    actual = np.asarray(all_actual)
    summary = {"record_count": len(records), "folds": len(folds), "baseline": score(actual, np.asarray(all_baseline), float(actual.mean())) if len(actual) else None, "full": score(actual, np.asarray(all_full), float(actual.mean())) if len(actual) else None}
    print(f"records={summary['record_count']}; baseline RMSE={summary['baseline']['rmse'] if summary['baseline'] else None}; full RMSE={summary['full']['rmse'] if summary['full'] else None}")
    report = {"schema_version": 1, "claim_boundary": "This grouped held-out test asks whether declared region attributes improve persistence forecasts beyond lattice size, cutoff, and area. It does not establish autonomous objects or causal closure.", "config": {key: value for key, value in vars(args).items() if key != "output"} | {"params": vars(params), "baseline_features": BASE_FEATURES, "full_features": FULL_FEATURES}, "summary": summary, "folds": folds, "records": records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote v2-gamma attribute-model report to {args.output}")


if __name__ == "__main__":
    main()
