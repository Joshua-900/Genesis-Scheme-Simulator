"""Fixed-seed object-motion and continuation forecasts with independent cohorts."""

from __future__ import annotations

import math
import numpy as np

from src.genesis_audit.analysis import paired_gain_interval, ridge_predict


MODELS = ("kinematic", "local_field", "field_matched", "structural", "shuffled_structure")


def shuffle_structure(x: np.ndarray, seeds: np.ndarray, branches: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    out = x.copy()
    for seed in np.unique(seeds):
        for branch in np.unique(branches):
            index = np.flatnonzero((seeds == seed) & (branches == branch))
            out[index, -8:] = x[rng.permutation(index), -8:]
    return out


def evaluate(arrays: dict[str, np.ndarray], training: tuple[int, ...], cohorts: dict[str, tuple[int, ...]], ridge: float = 10., minimum_gain: float = .05, bootstrap: int = 2000) -> dict:
    seeds, branch = arrays["seed"], arrays["branch"]
    training_mask = np.isin(seeds, training)
    report = {"cohorts": {}, "gate_passes": False}
    for name, held in cohorts.items():
        test_mask = np.isin(seeds, held)
        common = {}
        for task in ("motion", "continuation"):
            valid = arrays["survived"].astype(bool) if task == "motion" else np.ones(len(seeds), dtype=bool)
            train = training_mask & valid
            test = test_mask & valid
            covered = [s for s in held if np.sum(test & (seeds == s)) >= 5]
            if np.sum(train) < 10 or len(covered) < len(held):
                common[task] = {"status": "insufficient_coverage", "covered_seeds": covered, "records_train": int(train.sum()), "records_test": int(test.sum()), "passes": False}
                continue
            y = arrays["motion"] if task == "motion" else arrays["survived"][:, None].astype(float)
            predictions = {}
            for model in MODELS:
                if model == "shuffled_structure":
                    a = shuffle_structure(arrays["structural"][train], seeds[train], branch[train], np.random.default_rng(571))
                    b = shuffle_structure(arrays["structural"][test], seeds[test], branch[test], np.random.default_rng(863))
                else:
                    a, b = arrays[model][train], arrays[model][test]
                pred = ridge_predict(a, y[train], b, ridge)
                if task == "continuation":
                    pred = np.clip(pred, 0, 1)
                predictions[model] = pred
            predictions["persistence"] = np.zeros_like(y[test]) if task == "motion" else np.ones_like(y[test])
            predictions["training_mean"] = np.broadcast_to(y[train].mean(axis=0), y[test].shape)
            per_seed = {}
            for model, pred in predictions.items():
                arrays[f"prediction__{name}__{task}__{model}"] = pred
                loss = np.mean((pred - y[test]) ** 2, axis=1)
                per_seed[model] = np.asarray([loss[seeds[test] == s].mean() for s in held])
            comparisons = {}
            for reference in ("field_matched", "shuffled_structure", "persistence"):
                b, c = per_seed[reference], per_seed["structural"]
                if b.mean() <= 1e-12:
                    comparisons[reference] = {"relative_gain": None, "interval": None, "wins": int(np.sum(c < b)), "passes": False, "reason": "reference_loss_is_zero"}
                    continue
                gain = float((b.mean() - c.mean()) / b.mean())
                interval = paired_gain_interval(b, c, np.random.default_rng(189), bootstrap)
                wins = int(np.sum(c < b))
                comparisons[reference] = {"relative_gain": gain, "interval": interval, "wins": wins,
                    "passes": bool(gain >= minimum_gain and interval[0] > 0 and wins >= math.ceil(.7 * len(held)))}
            moving = int(np.sum(np.linalg.norm(y[test], axis=1) > .1)) if task == "motion" else None
            informative = (moving >= .1 * test.sum()) if task == "motion" else (0 < arrays["survived"][test].mean() < 1)
            common[task] = {"status": "evaluated", "records_train": int(train.sum()), "records_test": int(test.sum()), "seeds": list(held),
                "loss_unit": "squared grid sites, mean over x/y" if task == "motion" else "Brier error for strict observed continuation",
                "mean_loss": {m: float(v.mean()) for m, v in per_seed.items()}, "per_seed_loss": {m: v.tolist() for m, v in per_seed.items()},
                "comparisons": comparisons, "informative_variation": bool(informative), "moving_records": moving,
                "continuation_fraction": float(arrays["survived"][test].mean()),
                "passes": bool(informative and all(c["passes"] for c in comparisons.values()))}
        report["cohorts"][name] = common
    report["gate_passes"] = all(c.get("motion", {}).get("passes", False) for c in report["cohorts"].values())
    report["continuation_gate_passes"] = all(c.get("continuation", {}).get("passes", False) for c in report["cohorts"].values())
    return report
