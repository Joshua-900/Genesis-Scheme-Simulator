"""State-independent classical descriptors and seed-grouped forecast evaluation.

No height, distance, quantum entropy, or new physical dimension is inferred.
All spatial masks refer to the supplied periodic square grid.
"""

from __future__ import annotations

import math

import numpy as np


THETA_FEATURES = ("cos_mean", "sin_mean", "coherence", "winding_density", "abs_winding_density")
FULL_FEATURES = THETA_FEATURES + ("tension_mean", "tension_std", "compression_mean", "compression_std", "ux_mean", "uy_mean", "displacement_rms")
MODELS = ("local", "planar_shells", "multiscale", "shuffled_context")


def winding(theta: np.ndarray) -> np.ndarray:
    """Integer oriented plaquette winding, including periodic boundary plaquettes."""
    right = np.roll(theta, -1, axis=1)
    down = np.roll(theta, -1, axis=0)
    diagonal = np.roll(down, -1, axis=1)
    wrap = lambda a: (a + np.pi) % (2 * np.pi) - np.pi
    return np.rint((wrap(right - theta) + wrap(diagonal - right) + wrap(down - diagonal) + wrap(theta - down)) / (2 * np.pi)).astype(int)


def offsets(n: int, center: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = np.indices((n, n))
    return (rows - center[0] + n // 2) % n - n // 2, (cols - center[1] + n // 2) % n - n // 2


def square_masks(n: int, center: tuple[int, int], scales: tuple[int, ...]) -> list[np.ndarray]:
    dr, dc = offsets(n, center)
    return [(dr >= -(s // 2)) & (dr < s - s // 2) & (dc >= -(s // 2)) & (dc < s - s // 2) for s in scales]


def descriptors(snapshot: dict[str, np.ndarray], mask: np.ndarray, charge: np.ndarray) -> dict[str, float]:
    theta = snapshot["theta"][mask]
    if not theta.size:
        raise ValueError("Descriptor mask must contain at least one site.")
    c, s = np.cos(theta).mean(), np.sin(theta).mean()
    tau, compression = snapshot["tau"][mask], snapshot["C"][mask]
    ux, uy = snapshot["ux"][mask], snapshot["uy"][mask]
    return dict(zip(FULL_FEATURES, (
        float(c), float(s), float(np.hypot(c, s)), float(charge[mask].mean()), float(np.abs(charge[mask]).mean()),
        float(tau.mean()), float(tau.std()), float(compression.mean()), float(compression.std()),
        float(ux.mean()), float(uy.mean()), float(np.sqrt(np.mean(ux * ux + uy * uy))),
    )))


def feature_vectors(snapshot: dict[str, np.ndarray], center: tuple[int, int], scales: tuple[int, ...], charge: np.ndarray | None = None) -> dict[str, dict[str, np.ndarray]]:
    """Same footprint and feature count for nested blocks and disjoint shells.

    Both representations use the same underlying sites. Winding on boundary
    plaquettes can reference the one-site halo, identically for both models.
    Frame/time is deliberately absent: every record is a current-state summary.
    """
    if charge is None:
        charge = winding(snapshot["theta"])
    masks = square_masks(len(snapshot["theta"]), center, scales)
    local = descriptors(snapshot, square_masks(len(snapshot["theta"]), center, (1,))[0], charge)
    nested = [descriptors(snapshot, m, charge) for m in masks]
    shells, previous = [], np.zeros_like(masks[0])
    for mask in masks:
        shells.append(descriptors(snapshot, mask & ~previous, charge))
        previous = mask
    result = {}
    for track, names in (("theta_only", THETA_FEATURES), ("full_state_summaries", FULL_FEATURES)):
        common = [local[k] for k in names]
        result[track] = {
            "local": np.asarray(common),
            "multiscale": np.asarray(common + [d[k] for d in nested for k in names]),
            "planar_shells": np.asarray(common + [d[k] for d in shells for k in names]),
        }
    return result


def observational_controls(snapshot: dict[str, np.ndarray], rng: np.random.Generator) -> dict[str, dict[str, np.ndarray]]:
    """Controls for snapshot organization, not extra physical trajectories.

    The Fourier surrogate preserves complex-phasor spectral amplitudes BEFORE
    projecting back to unit-modulus angles. Projection breaks exact preservation;
    its resulting spectral mismatch is reported, never called pair-matched.
    """
    shape = snapshot["theta"].shape
    permutation = rng.permutation(shape[0] * shape[1])
    shuffled = {k: v.ravel()[permutation].reshape(shape).copy() for k, v in snapshot.items()}
    independent = {k: v.copy() for k, v in snapshot.items()}
    independent["theta"] = rng.choice(snapshot["theta"].ravel(), size=shape, replace=True)
    phasor = np.exp(1j * snapshot["theta"])
    spectrum = np.fft.fft2(phasor)
    surrogate = {k: v.copy() for k, v in snapshot.items()}
    surrogate["theta"] = np.angle(np.fft.ifft2(np.abs(spectrum) * np.exp(1j * rng.uniform(-np.pi, np.pi, shape)))) % (2 * np.pi)
    return {"spatial_permutation": shuffled, "independent_angles": independent, "phase_surrogate": surrogate}


def spectrum_mismatch(theta: np.ndarray, other: np.ndarray) -> float:
    a, b = np.abs(np.fft.fft2(np.exp(1j * theta))), np.abs(np.fft.fft2(np.exp(1j * other)))
    return float(np.linalg.norm(a - b) / max(np.linalg.norm(a), 1e-12))


def response_targets(reference: dict[str, np.ndarray], perturbed: dict[str, np.ndarray], center: tuple[int, int]) -> np.ndarray:
    """RMS phasor response in three fixed rings; no angle wrap discontinuity."""
    dr, dc = offsets(len(reference["theta"]), center)
    distance2 = dr * dr + dc * dc
    response2 = 2.0 - 2.0 * np.cos(perturbed["theta"] - reference["theta"])
    return np.asarray([np.sqrt(np.maximum(response2[(distance2 >= lo * lo) & (distance2 < hi * hi)].mean(), 0.0)) for lo, hi in ((0, 2), (2, 4), (4, 8))])


def shuffled_context(x: np.ndarray, seeds: np.ndarray, common_count: int, rng: np.random.Generator) -> np.ndarray:
    """Keep local input intact, permute context within each seed and cohort.

    This destroys context/event matching across sampled times and centers while
    preserving its marginal values and the seed boundary. It is an observational
    negative control, not a simulated time-shuffled universe.
    """
    out = x.copy()
    for seed in np.unique(seeds):
        indices = np.flatnonzero(seeds == seed)
        out[indices, common_count:] = x[rng.permutation(indices), common_count:]
    return out


def ridge_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, penalty: float) -> np.ndarray:
    """Standardize on training inputs only; multioutput ridge with an intercept."""
    mean, std = x_train.mean(axis=0), x_train.std(axis=0)
    std = np.where(std < 1e-10, 1.0, std)
    a = np.column_stack((np.ones(len(x_train)), (x_train - mean) / std))
    b = np.column_stack((np.ones(len(x_test)), (x_test - mean) / std))
    regularizer = np.eye(a.shape[1]) * penalty
    regularizer[0, 0] = 0
    beta = np.linalg.solve(a.T @ a + regularizer, a.T @ y_train)
    return b @ beta


def paired_gain_interval(baseline: np.ndarray, candidate: np.ndarray, rng: np.random.Generator, draws: int = 2000) -> list[float]:
    """Paired seed bootstrap; inputs are one loss per independent held-out seed."""
    indices = rng.integers(0, len(baseline), size=(draws, len(baseline)))
    b, c = baseline[indices].mean(axis=1), candidate[indices].mean(axis=1)
    gains = (b - c) / np.maximum(b, 1e-15)
    return np.quantile(gains, [.025, .975]).tolist()


def evaluate_dataset(arrays: dict[str, np.ndarray], train_seeds: tuple[int, ...], cohorts: dict[str, tuple[int, ...]], ridge: float, minimum_gain: float, win_fraction: float, bootstrap_draws: int) -> dict:
    """Fixed training seeds; two unseen cohorts. No tuning on held-out targets."""
    seeds, y = arrays["seed"], arrays["targets"]
    train = np.isin(seeds, train_seeds)
    # Equal weighting of response components using training target variability.
    scale = np.maximum(y[train].std(axis=0), 1e-6)
    report = {"training_target_scale": scale.tolist(), "tracks": {}}
    for track, names in (("theta_only", THETA_FEATURES), ("full_state_summaries", FULL_FEATURES)):
        cohort_reports = {}
        for cohort_name, held_seeds in cohorts.items():
            test = np.isin(seeds, held_seeds)
            x = {model: arrays[f"{track}__{model}"] for model in MODELS if model != "shuffled_context"}
            # Each split is shuffled separately; no values cross train/test.
            context_train = shuffled_context(x["multiscale"][train], seeds[train], len(names), np.random.default_rng(531))
            context_test = shuffled_context(x["multiscale"][test], seeds[test], len(names), np.random.default_rng(947))
            predictions = {}
            for model in MODELS:
                a, b = (context_train, context_test) if model == "shuffled_context" else (x[model][train], x[model][test])
                predictions[model] = ridge_predict(a, y[train], b, ridge)
            predictions["training_mean"] = np.broadcast_to(y[train].mean(axis=0), y[test].shape)
            predictions["zero_response"] = np.zeros_like(y[test])
            # Save exact held-out predictions as part of the raw audit artifact.
            for model, values in predictions.items():
                arrays[f"prediction__{track}__{cohort_name}__{model}"] = values
            loss = {model: np.mean(((value - y[test]) / scale) ** 2, axis=1) for model, value in predictions.items()}
            per_seed = {model: np.asarray([values[seeds[test] == seed].mean() for seed in held_seeds]) for model, values in loss.items()}
            comparisons = {}
            for baseline in ("planar_shells", "shuffled_context", "training_mean"):
                b, c = per_seed[baseline], per_seed["multiscale"]
                gain = float((b.mean() - c.mean()) / max(b.mean(), 1e-15))
                ci = paired_gain_interval(b, c, np.random.default_rng(813), bootstrap_draws)
                wins = int(np.sum(c < b))
                comparisons[baseline] = {"relative_loss_reduction": gain, "paired_seed_bootstrap_95_interval": ci, "seed_wins": wins,
                    "passes": bool(gain >= minimum_gain and ci[0] > 0 and wins >= math.ceil(win_fraction * len(held_seeds)))}
            cohort_reports[cohort_name] = {
                "seeds": list(held_seeds), "records": int(test.sum()),
                "normalized_mse": {model: float(values.mean()) for model, values in per_seed.items()},
                "per_seed_normalized_mse": {model: values.tolist() for model, values in per_seed.items()},
                "physical_phasor_rmse_by_ring": {model: np.sqrt(np.mean((values - y[test]) ** 2, axis=0)).tolist() for model, values in predictions.items()},
                "comparisons": comparisons,
                "passes": all(c["passes"] for c in comparisons.values()),
            }
        report["tracks"][track] = {"cohorts": cohort_reports, "passes": all(c["passes"] for c in cohort_reports.values())}
    report["primary_gate_passes"] = report["tracks"]["full_state_summaries"]["passes"]
    return report
