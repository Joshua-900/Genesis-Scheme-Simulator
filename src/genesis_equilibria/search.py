"""Bounded fixed-point search and active-state numerical stability study.

python -B -m src.genesis_equilibria.search --output results/v1_equilibria_new
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from genesis_multiscale_audit import ROOT, engine_hashes, write_json
from src.genesis_audit.verify import verify
from src.genesis_audit.v1_adapter import V1Adapter
from .equations import active_from_reduced, active_jacobian, alignment, normalized_difference, quantities, reduced_fields, reduced_jacobian, reduced_residual


@dataclass(frozen=True)
class Config:
    grids: tuple[int, ...] = (4, 6, 8)
    evaluations: int = 160
    raw_torque_tolerance: float = 1e-8
    state_tolerance: float = 1e-8
    witness_rms_alignment: float = 1e-3
    smooth_margin: float = 1e-4
    eigen_margin: float = 1e-4
    eigen_agreement: float = 5e-4
    perturbation_updates: int = 1000
    perturbation_amplitudes: tuple[float, ...] = (1e-4, 1e-3)
    perturbation_seeds: tuple[int, ...] = (17, 29, 43)
    interesting_stability_limit_per_grid: int = 2


def seed_fields(n: int, params):
    rows, cols = np.indices((n, n))
    entries = [
        ("uniform_control", np.zeros((n, n)), False),
        ("checkerboard_control", np.pi * ((rows + cols) % 2), False),
        ("twist_reference", 2 * np.pi * cols / n, False),
        ("weak_wave", .3 * np.cos(2 * np.pi * cols / n), False),
        ("smooth_forced_guess", .8 * np.sin(2 * np.pi * cols / n) + .8 * np.cos(2 * np.pi * rows / n), True),
        ("periodic_vortex_guess", np.arctan2(np.sin(2 * np.pi * (rows + .25) / n), np.sin(2 * np.pi * (cols + .25) / n)), True),
    ]
    for seed in (11, 23, 37):
        entries.append((f"random_{seed}", np.random.default_rng(seed).uniform(-np.pi, np.pi, (n, n)), True))
    for name, theta, quasi_static in entries:
        tau = params.gamma / params.decay_tau * np.abs(alignment(theta))
        ux = params.kappa / params.geom_decay * tau * np.cos(theta) if quasi_static else np.zeros_like(theta)
        uy = params.kappa / params.geom_decay * tau * np.sin(theta) if quasi_static else np.zeros_like(theta)
        yield name, np.stack((theta, ux, uy)).ravel()


def source_state(active, n, params):
    adapter = V1Adapter()
    adapter.params = params
    state = adapter.create(n, 0)
    for key, field in zip(("theta", "tau", "ux", "uy"), active.reshape(4, n, n)):
        setattr(state, key, field.copy())
    fields = active.reshape(4, n, n)
    state.C = quantities(*fields, params)["C"].copy()
    return adapter, state


def accepted_state(x, n, params, config):
    theta, tau, ux, uy = reduced_fields(x, n, params)
    d = quantities(theta, tau, ux, uy, params)
    active = active_from_reduced(x, n, params)
    adapter, state = source_state(active, n, params)
    original_c = state.C.copy()
    adapter.advance(state, 1)
    angular = (state.theta - theta + np.pi) % (2 * np.pi) - np.pi
    residuals = {"theta": float(np.max(np.abs(angular))), "tau": float(np.max(np.abs(state.tau - tau))),
        "ux": float(np.max(np.abs(state.ux - ux))), "uy": float(np.max(np.abs(state.uy - uy))), "C": float(np.max(np.abs(state.C - original_c)))}
    raw = float(np.max(np.abs(d["T"])))
    passed = raw <= config.raw_torque_tolerance and max(residuals.values()) <= config.state_tolerance
    rms = float(np.sqrt(np.mean(d["a"] ** 2)))
    return {"accepted": bool(passed), "raw_torque_max": raw, "source_one_update_residuals": residuals,
        "rms_alignment_torque": rms, "interesting_nonzero_alignment": bool(passed and rms >= config.witness_rms_alignment),
        "coherence": float(np.abs(np.exp(1j * theta).mean())), "mean_tension": float(tau.mean()), "mean_compression": float(d["C"].mean()),
        "minimum_abs_alignment": float(np.abs(d["a"]).min()), "minimum_laplacian_norm": float(d["Lnorm"].min()),
        "stationary_global_torque_budget_residual": float(abs(d["R"].sum() + .1 * tau.sum())),
        "minimum_mobility": float(d["q"].min())}


def perturbation_check(active, n, params, config):
    samples = []
    for amplitude in config.perturbation_amplitudes:
        for seed in config.perturbation_seeds:
            adapter, state = source_state(active, n, params)
            untouched = adapter.clone(state)
            rng = np.random.default_rng(seed)
            scale = np.repeat([1., 2., 4.8, 4.8], n * n)
            direction = rng.normal(size=len(active))
            direction /= np.sqrt(np.mean(direction ** 2))
            perturbed = active + amplitude * scale * direction
            perturbed.reshape(4, n, n)[1] = np.maximum(perturbed.reshape(4, n, n)[1], 0)
            _, changed = source_state(perturbed, n, params)
            initial = normalized_difference(perturbed, active, n)
            records = []
            previous = 0
            for updates in (1, 10, 50, 100, 344, config.perturbation_updates):
                adapter.advance(state, updates - previous)
                adapter.advance(changed, updates - previous)
                previous = updates
                current = np.stack((state.theta, state.tau, state.ux, state.uy)).ravel()
                moved = np.stack((changed.theta, changed.tau, changed.ux, changed.uy)).ravel()
                records.append({"updates": updates, "base_drift_from_root": normalized_difference(current, active, n),
                    "perturbed_distance_from_root": normalized_difference(moved, active, n),
                    "difference_from_unperturbed": normalized_difference(moved, current, n)})
            final = records[-1]
            samples.append({"amplitude": amplitude, "seed": seed, "actual_initial_distance": initial,
                "final_difference_ratio": final["difference_from_unperturbed"] / initial,
                "base_drift_ratio": final["base_drift_from_root"] / initial, "samples": records})
    return {"trials": samples, "all_tested_directions_contract": all(r["final_difference_ratio"] < .1 and r["base_drift_ratio"] < .1 for r in samples),
        "meaning": "Finite tested perturbations in active variables; not a global or rigorous stability proof. Nonnegative tension is enforced at perturbation initialization."}


def stability(active, n, params, config):
    fields = active.reshape(4, n, n)
    d = quantities(*fields, params)
    smooth = bool(np.min(np.abs(d["a"])) > config.smooth_margin and (params.curv == 0 or d["Lnorm"].min() > config.smooth_margin))
    radii = []
    for step in (1e-6, 1e-7):
        values = np.linalg.eigvals(active_jacobian(active, n, params, step))
        radii.append({"finite_difference_step": step, "spectral_radius": float(np.max(np.abs(values))),
            "eigenvalues_outside_unit_margin": int(np.sum(np.abs(values) > 1 + config.eigen_margin))})
    agreement = abs(radii[0]["spectral_radius"] - radii[1]["spectral_radius"]) <= config.eigen_agreement
    spectral_stable = smooth and agreement and max(r["spectral_radius"] for r in radii) < 1 - config.eigen_margin
    spectral_unstable = smooth and agreement and min(r["spectral_radius"] for r in radii) > 1 + config.eigen_margin
    trajectory = perturbation_check(active, n, params, config)
    return {"smooth_margin_satisfied": smooth, "finite_difference_spectra": radii, "spectral_radius_agrees": agreement,
        "classification": "numerically_linearly_stable" if spectral_stable else "numerically_linearly_unstable" if spectral_unstable else "unresolved_or_nonsmooth",
        "perturbations": trajectory, "passes_local_numerical_stability_gate": bool(spectral_stable and trajectory["all_tested_directions_contract"]),
        "scope": "Active theta/tau/ux/uy state. Stored C is overwritten and adds zero eigenvalues. Disabled memory/inhibitor arrays pass through and add trivial neutral directions if included."}


def run(config: Config, output: Path):
    if output.exists():
        raise ValueError("Refusing to overwrite an equilibrium study.")
    if config.perturbation_updates < 344 or config.evaluations < 1 or any(n < 4 for n in config.grids):
        raise ValueError("Invalid bounded-search configuration.")
    inherited = verify(ROOT / "results/v1_baseline_audit_2026-10-31/manifest.json")
    if not inherited["fingerprints_match"] or not inherited["environment_matches"]:
        raise ValueError("Parent baseline changed; review the delta first.")
    before = engine_hashes()
    output.mkdir(parents=True)
    source_paths = list((ROOT / "src/genesis_equilibria").glob("*.py")) + [ROOT / "tests/test_equilibria.py"]
    write_json(output / "protocol.json", {"study_id": output.name, "created_utc": datetime.now(timezone.utc).isoformat(), "parent_audit_id": inherited["audit_id"],
        "parent_manifest_sha256": inherited["manifest_sha256"], "config": asdict(config), "parameters": vars(V1Adapter().params),
        "engine_source_sha256_before": before, "analysis_source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        "hypothesis": "The unchanged V1 preset may admit a stable full active-state nonuniform equilibrium with rms net alignment torque >=1e-3, supported by curvature feedback.",
        "root_problem": "Unknown theta/ux/uy; tau is eliminated exactly at equilibrium. Residual uses raw torque and displacement recurrence divided by displacement decay, not slowed angular increments.",
        "search": "Grids4,6,8; same nine named deterministic starts for beta=.04 and beta=0, bounded TRF least_squares, fixed 160 evaluation budget per start, no retuning on outcomes. Angles bounded +/-10pi, u components +/-4.8.",
        "acceptance": "Raw torque infinity norm and independent source one-update residual for theta,tau,ux,uy,C <=1e-8. Solver success alone does not imply acceptance.",
        "stability_selection": "Uniform/checkerboard controls plus at most two unique interesting roots per grid/mode, in ascending raw residual then start index. No result-based stability selection.",
        "stability": "Full active-state central FD at1e-6/1e-7; smoothness and eigenvalue/agreement margins in config. Also six fixed physical perturbations for1000 updates, with separate unperturbed base drift. Interesting full-curvature roots also receive locking-off stability checks without rerooting. Finite tests do not constitute rigorous proof.",
        "larger_grid": "Each selected interesting full-curvature root is tiled to a2N periodic grid, checked against source and tested for added perturbation modes. Exact tiling preserves local equations, not stability or a localized object interpretation.",
        "milestone_gate": "At least one accepted nonzero-alignment full-curvature root must pass the numerical local stability gate at both N and2N. Curvature-off controls must not contradict the inherited no-curvature static-balance theorem.",
        "limits": ["A bounded multistart search cannot prove no other equilibria exist.", "Small periodic cells or repeated tiled patterns are not localized autonomous matter.",
            "Root acceptance is finite numerical tolerance, not an exact existence proof.", "Nonsmooth abs source and zero-Laplacian epsilon can invalidate ordinary Jacobian certification; mark unresolved.",
            "Only active-state stability is analyzed; disabled pass-through arrays have neutral directions.", "Static equilibria do not exhaust moving, rotating or periodic persistent structures.",
            "No engine, old audit or historical result is overwritten."]})
    write_json(output / "status.json", {"status": "searching"})
    results, states, assessments = [], {}, []
    try:
        for n in config.grids:
            for mode, beta in (("full", .04), ("curvature_off", 0.)):
                params = V1Adapter().params
                params.curv = beta
                for index, (name, initial) in enumerate(seed_fields(n, params)):
                    bound = np.r_[np.full(n*n, 10*np.pi), np.full(2*n*n, 4.8)]
                    if np.max(np.abs(reduced_residual(initial, n, params))) <= 1e-10:
                        x, evaluations, cost, solver_success = initial, 0, 0., True
                    else:
                        fit = least_squares(reduced_residual, initial, jac=reduced_jacobian, args=(n, params),
                            bounds=(-bound, bound), x_scale="jac", max_nfev=config.evaluations, ftol=1e-11, xtol=1e-11, gtol=1e-11)
                        x, evaluations, cost, solver_success = fit.x, fit.nfev, float(fit.cost), bool(fit.success)
                    record = {"id": f"N{n}_{mode}_{name}", "grid": n, "mode": mode, "start": name, "start_index": index,
                        "solver_success": solver_success, "function_evaluations": evaluations, "least_squares_cost": cost,
                        **accepted_state(x, n, params, config)}
                    if mode == "curvature_off" and record["interesting_nonzero_alignment"]:
                        raise RuntimeError("Curvature-off nonzero-alignment root contradicts inherited theorem; investigate numerical implementation.")
                    states[record["id"]] = active_from_reduced(x, n, params)
                    results.append(record)
                    print(f"{record['id']}: accepted={record['accepted']} raw={record['raw_torque_max']:.2g} rms_a={record['rms_alignment_torque']:.3g} nfev={evaluations}", flush=True)
                subset = [r for r in results if r["grid"] == n and r["mode"] == mode and r["accepted"]]
                selected = [r for r in subset if r["start"] in ("uniform_control", "checkerboard_control")]
                interesting = sorted([r for r in subset if r["interesting_nonzero_alignment"]], key=lambda r: (r["raw_torque_max"], r["start_index"]))
                unique = []
                for r in interesting:
                    if not any(normalized_difference(states[r["id"]], states[z["id"]], n) < 1e-4 for z in unique):
                        unique.append(r)
                selected += unique[:config.interesting_stability_limit_per_grid]
                for record in selected:
                    active = states[record["id"]]
                    assessment = {"candidate_id": record["id"], "grid": n, "mode": mode, **stability(active, n, params, config)}
                    if mode == "full" and record["interesting_nonzero_alignment"]:
                        unlocked_params = copy.copy(params)
                        unlocked_params.lock_strength = 0.
                        assessment["locking_off_stability"] = stability(active, n, unlocked_params, config)
                        tiled = np.tile(active.reshape(4, n, n), (1, 2, 2)).ravel()
                        tiled_reduced = tiled.reshape(4, 2*n, 2*n)[[0,2,3]].ravel()
                        acceptance = accepted_state(tiled_reduced, 2*n, params, config)
                        assessment["tiled"] = {"grid": 2*n, "acceptance": acceptance,
                            "stability": stability(tiled, 2*n, params, config) if acceptance["accepted"] else None}
                    assessments.append(assessment)
                    print(f"stability {record['id']}: {assessment['classification']}; contraction={assessment['perturbations']['all_tested_directions_contract']}", flush=True)
                np.savez_compressed(output / "candidate_states.npz", **states)
                write_json(output / "progress.json", {"roots": results, "stability": assessments})
        passed = any(a["passes_local_numerical_stability_gate"] and a.get("tiled", {}).get("stability", {}).get("passes_local_numerical_stability_gate", False) for a in assessments if a.get("tiled", {}).get("stability") is not None)
        after = engine_hashes()
        if before != after:
            raise RuntimeError("Preserved engine sources changed.")
        report = {"study_id": output.name, "baseline_and_engines_unchanged": True, "engine_source_sha256_after": after, "roots": results,
            "stability": assessments, "milestone_gate_passed": bool(passed),
            "accepted_roots": sum(r["accepted"] for r in results), "interesting_roots": sum(r["interesting_nonzero_alignment"] for r in results),
            "claim_boundary": "Bounded numerical equilibrium search and active-state local checks for one preserved discrete preset; no exhaustive nonexistence, autonomy, matter, physical time or holography claim."}
        write_json(output / "report.json", report)
        write_json(output / "status.json", {"status": "complete", "milestone_gate_passed": bool(passed)})
        print(f"Completed {output}; milestone gate={passed}", flush=True)
        return report
    except BaseException as exc:
        write_json(output / "status.json", {"status": "failed", "error": str(exc)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(Config(), args.output)


if __name__ == "__main__":
    main()
