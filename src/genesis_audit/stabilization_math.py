"""Algebra checks for the unchanged V1 structural preset, not a new engine.

Evaluates closed-form bounds and checks one update of archived starting states.
Does not run a simulation cohort, fit a predictor, or tune model parameters.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path

import numpy as np

from genesis_multiscale_audit import ROOT, write_json
from src.genesis_audit.verify import verify
from src.genesis_audit.v1_adapter import V1Adapter


def scalar_results() -> dict:
    p = V1Adapter().params
    denominator = p.sigma_c2 + 1e-8
    tau_bound = 4 * p.gamma / p.decay_tau
    component_bound = (p.kappa * tau_bound + p.shell_geom_gain / 2) / p.geom_decay
    torque_bound = 4 * p.alpha + .1 * tau_bound + p.curv * (8 * math.sqrt(2) * component_bound + 1e-8)
    h = .05
    targets = {}
    for slowdown in (2, 5, 10, 20):
        q = 1 / slowdown
        required_c = (1 - q) / p.lock_strength
        threshold = math.sqrt(-denominator * math.log(required_c))
        targets[str(slowdown)] = {"required_C": required_c, "maximum_abs_detF": threshold}
    half_tau = math.log(.5) / math.log(1 - p.decay_tau)
    half_u = math.log(.5) / math.log(1 - p.geom_decay)
    review_window = math.ceil(10 * max(half_tau, half_u))
    return {
        "q_minimum": 1 - p.lock_strength, "maximum_same_torque_slowdown": 1 / (1 - p.lock_strength),
        "compression_denominator": denominator, "strong_slowdown_thresholds": targets,
        "tau_bound_zero_initialization": tau_bound, "u_component_bound_zero_initialization": component_bound,
        "maximum_torque_bound": torque_bound, "maximum_single_angle_increment_bound": h * torque_bound,
        "bound_excludes_2pi_fixedpoint_alias": h * torque_bound < 2 * math.pi,
        "source_free_tau_half_life_updates": half_tau, "unforced_u_half_life_updates": half_u,
        "ten_half_life_review_window_updates": review_window,
        "direct_initial_tau_fraction_after_window": (1 - p.decay_tau) ** review_window,
        "direct_initial_u_fraction_after_window": (1 - p.geom_decay) ** review_window,
        "no_curvature_stationary_torque_positive_a_coefficient": p.alpha + .1 * p.gamma / p.decay_tau,
        "no_curvature_stationary_torque_negative_a_coefficient": p.alpha - .1 * p.gamma / p.decay_tau,
        "zero_laplacian_epsilon_turn_bound_per_update": h * p.curv * 1e-8,
        "frozen_mobility_alignment_mode_at_mu8_unlocked": 1 - h * p.alpha * 8,
        "frozen_mobility_alignment_mode_at_mu8_max_locked": 1 - h * (1 - p.lock_strength) * p.alpha * 8,
        "detF_examples": [{"J": j, "C": math.exp(-j * j / denominator), "q": 1 - p.lock_strength * math.exp(-j * j / denominator)} for j in (1., .5, .25, .1, 0.)],
        "limits": ["Slowdown is a fixed-torque one-update ratio, not a global lifetime bound.",
            "Memory half-lives concern homogeneous carryover only. New alignment and shell sources may continually regenerate state.",
            "The Fourier mode factors hold for the isolated linear alignment part with mobility frozen, not the coupled spectrum.",
            "Bounds and no-alias conclusion concern this preset and nonnegative tension; other parameters need separate bounds."]}


def snapshot_check(path: Path) -> dict:
    adapter = V1Adapter()
    with np.load(path) as raw:
        values = {key: raw[f"initial_{key}"].copy() for key in ("theta", "tau", "ux", "uy", "C")}
    theta, tau, ux, uy = [values[k] for k in ("theta", "tau", "ux", "uy")]
    p = adapter.params
    a = sum(np.sin(np.roll(theta, shift, axis) - theta) for axis in (0, 1) for shift in (-1, 1))
    next_tau = (1 - p.decay_tau) * tau + p.gamma * np.abs(a)
    provisional_x = (1 - p.geom_decay) * ux + p.kappa * next_tau * np.cos(theta)
    provisional_y = (1 - p.geom_decay) * uy + p.kappa * next_tau * np.sin(theta)
    derivative = lambda v, axis: .5 * (np.roll(v, -1, axis) - np.roll(v, 1, axis))
    j = (1 + derivative(provisional_x, 1)) * (1 + derivative(provisional_y, 0)) - derivative(provisional_x, 0) * derivative(provisional_y, 1)
    c = np.exp(-j * j / (p.sigma_c2 + 1e-8))
    final_x = provisional_x + p.shell_geom_gain * derivative(c, 1)
    final_y = provisional_y + p.shell_geom_gain * derivative(c, 0)
    laplace = lambda v: sum(np.roll(v, shift, axis) for axis in (0, 1) for shift in (-1, 1)) - 4 * v
    lx, ly = laplace(final_x), laplace(final_y)
    curvature = p.curv * (np.hypot(lx, ly) + 1e-8) * np.sin(np.arctan2(ly, lx) - theta)
    total = p.alpha * a + .1 * next_tau + curvature
    q = 1 - p.lock_strength * c
    state = adapter.create(len(theta), 0)
    for key, value in values.items():
        setattr(state, key, value.copy())
    unlocked = adapter.clone(state)
    adapter.advance(state, 1)
    unlock_adapter = V1Adapter()
    unlock_adapter.params.lock_strength = 0
    unlock_adapter.advance(unlocked, 1)
    expected = {"theta": (theta + .05 * q * total) % (2 * np.pi), "tau": next_tau, "ux": final_x, "uy": final_y, "C": c}
    residuals = {key: float(np.max(np.abs(getattr(state, key) - value))) for key, value in expected.items()}
    wrap = lambda v: (v + np.pi) % (2 * np.pi) - np.pi
    mobility_error = float(np.max(np.abs(wrap(state.theta - theta) - q * wrap(unlocked.theta - theta))))
    if max(residuals.values()) > 1e-12 or mobility_error > 1e-12:
        raise AssertionError(f"Derived map mismatch: {path.name}")
    return {"archive": path.relative_to(ROOT).as_posix(), "map_max_absolute_residuals": residuals,
        "locked_unlocked_same_torque_relation_max_error": mobility_error}


def render(output: Path, scalars: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    j = np.linspace(-1, 1, 501)
    c = np.exp(-j * j / scalars["compression_denominator"])
    q = 1 - .96 * c
    ticks = np.arange(0, 401)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), layout="constrained")
    axes[0].plot(j, q, color="#356f9c", label="q = 1 − 0.96 C")
    threshold = scalars["strong_slowdown_thresholds"]["10"]["maximum_abs_detF"]
    axes[0].axvspan(-threshold, threshold, color="#356f9c", alpha=.13, label="At least 10× same-torque slowing")
    axes[0].axhline(.04, color="#777777", linestyle="--", linewidth=1)
    axes[0].set(xlabel="Pre-shell deformation determinant J", ylabel="Angular mobility q", title="Strong braking needs near-singular geometry", ylim=(0, 1.05))
    axes[0].legend(fontsize=8)
    axes[1].semilogy(ticks, .98 ** ticks, color="#356f9c", label="Direct initial tension contribution")
    axes[1].semilogy(ticks, .95 ** ticks, color="#b36d44", label="Direct initial displacement contribution")
    axes[1].axvline(scalars["ten_half_life_review_window_updates"], color="#777777", linestyle="--", linewidth=1)
    axes[1].set(xlabel="Model updates", ylabel="Fraction of initial homogeneous contribution", title="Carryover decays; ongoing sources may renew it")
    axes[1].legend(fontsize=8)
    fig.suptitle("V1 stabilization: equations, not new simulation results", fontsize=13)
    fig.savefig(output / "mechanism.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    if output.exists():
        raise ValueError("Use a new directory; derivation records are not overwritten.")
    inherited = verify(ROOT / "results/v1_baseline_audit_2026-10-31/manifest.json")
    if not inherited["fingerprints_match"] or not inherited["environment_matches"]:
        raise ValueError("Parent baseline changed; review the explicit delta.")
    archives = sorted((ROOT / "results/vortex_motion_2026-10-31").glob("seed_*.npz"))
    if len(archives) != 24:
        raise ValueError("Expected the existing 24 archived starting states.")
    output.mkdir(parents=True)
    write_json(output / "manifest.json", {"record_id": output.name, "kind": "source_based_mathematical_derivation_with_one_update_consistency_checks",
        "parent_audit_id": inherited["audit_id"], "parent_manifest_sha256": inherited["manifest_sha256"], "created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "archive_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in archives},
        "scope": "Existing preset equations; 24 archived states, one locked and one unlocked update each. No new trajectory campaign, statistical gate or fitted model."})
    scalars = scalar_results()
    checks = [snapshot_check(p) for p in archives]
    if not verify(ROOT / "results/v1_baseline_audit_2026-10-31/manifest.json")["fingerprints_match"]:
        raise RuntimeError("Preserved baseline changed during analysis.")
    write_json(output / "checks.json", {"scalar_derivations": scalars, "archived_state_one_update_checks": checks, "baseline_unchanged": True})
    render(output, scalars)
    print(f"Verified staged equations on {len(checks)} archived states. Maximum angle bound={scalars['maximum_single_angle_increment_bound']:.6f}; 10x braking |J|<={scalars['strong_slowdown_thresholds']['10']['maximum_abs_detF']:.6f}; carryover window={scalars['ten_half_life_review_window_updates']} updates.")


if __name__ == "__main__":
    main()
