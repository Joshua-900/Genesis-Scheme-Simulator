"""Freeze a cumulative V1 baseline audit: evidence replay and equation probes.

No simulation experiment is repeated and no V1/V2 engine is edited. Existing
forecast records are re-evaluated using their original prediction functions.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
import scipy
from scipy.stats import wilcoxon

from genesis_multiscale_audit import ROOT, engine_hashes, write_json
from genesis_v1_pair_object_gate import FIELD_FEATURES, RELATIONAL_FEATURES, ridge_predict
from src.genesis_audit.v1_adapter import V1Adapter
from src.genesis_grid import rules_alignment, rules_compression


EVIDENCE = (
    "results/v1_local_structure_perturbation_30seed.json",
    "results/v1_local_structure_perturbation_30seed_batch1.json",
    "results/v1_local_structure_perturbation_30seed_batch2.json",
    "results/v1_local_structure_perturbation_30seed_batch3.json",
    "results/v1_vortex_census.json",
    "results/v1_vortex_robustness.json",
    "results/v1_pair_object_gate.json",
    "results/v1_pair_object_gate_replication.json",
    "results/multiscale_audit_2026-10-31/protocol.json",
    "results/multiscale_audit_2026-10-31/report.json",
)
PRODUCERS = (
    "genesis_v1_compression_ablation.py", "genesis_v1_local_structure_perturbation.py",
    "genesis_v1_vortex_census.py", "genesis_v1_vortex_robustness.py", "genesis_v1_pair_object_gate.py",
    "genesis_multiscale_audit.py", "src/genesis_audit/analysis.py", "src/genesis_audit/v1_adapter.py",
    "src/genesis_audit/v1_baseline.py", "tests/test_multiscale_audit.py", "tests/test_v2_integrated.py",
    "requirements.txt",
)


def file_hashes(paths: tuple[str, ...]) -> dict[str, str]:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def structural_evidence() -> dict:
    d = load(EVIDENCE[0])
    runs = [r for r in d["runs"] if r["status"] == "tested"]
    assert sorted(r["seed"] for r in runs) == list(range(1, 31))
    batched = [r for name in EVIDENCE[1:4] for r in load(name)["runs"]]
    assert sorted(batched, key=lambda r: r["seed"]) == sorted(d["runs"], key=lambda r: r["seed"])
    values = {b: np.asarray([r["branches"][b]["continuation_samples"] for r in runs]) for b in ("untouched", "candidate_neighborhood", "background")}
    medians = {b: float(np.median(x)) for b, x in values.items()}
    for b, median in medians.items():
        assert median == d["summary"][b]["median_continuation_samples"]
    x, y = values["candidate_neighborhood"], values["background"]
    settings = {"zero_method": "wilcox", "correction": False, "method": "approx"}
    two = wilcoxon(x, y, alternative="two-sided", **settings)
    one = wilcoxon(x, y, alternative="less", **settings)
    minimum_distance = min(np.linalg.norm(np.minimum(np.abs(np.asarray(r["candidate"]["midpoint"]) - r["background_center"]), 64 - np.abs(np.asarray(r["candidate"]["midpoint"]) - r["background_center"]))) for r in runs)
    return {"tested_seeds": len(runs), "batch_merge_exact": True, "medians": medians,
        "end_survival": {b: sum(r["branches"][b]["survived_to_end"] for r in runs) for b in values},
        "target_lower_equal_higher": [int(np.sum(x < y)), int(np.sum(x == y)), int(np.sum(x > y))],
        "background_matches_untouched": bool(np.array_equal(y, values["untouched"])),
        "wilcoxon": {"settings": settings, "two_sided_p": float(two.pvalue), "one_sided_less_p": float(one.pvalue)},
        "minimum_periodic_midpoint_background_distance": float(minimum_distance),
        "interpretation": "Local joint structural-state intervention changes strict tracked-pair continuation in the selected high-compression regime. Does not isolate which state component or establish a history-dependent interaction law.",
        "reporting_discrepancy": "Historical prose says medians 22/5/22; archived raw and summary agree on 21/4.5/21. Its p=0.000106 matches a one-sided less test; sidedness was unspecified."}


def vortex_evidence() -> dict:
    census, robustness = load(EVIDENCE[4]), load(EVIDENCE[5])
    vortices = census["vortices"]
    persistent = [v for v in vortices if v["max_age"] >= census["experiment"]["min_age"]]
    assert len(vortices) == census["summary"]["observed"]
    assert len(persistent) == census["summary"]["persistent"]
    assert float(np.median([v["max_age"] for v in persistent])) == census["summary"]["median_persistent_age"]
    tested = [r for r in robustness["runs"] if r["status"] == "tested"]
    medians = {b: float(np.median([r["branches"][b]["continuation_samples"] for r in tested])) for b in ("untouched", "core", "background")}
    assert all(medians[b] == robustness["summary"][b]["median"] for b in medians)
    x = [r["branches"]["core"]["continuation_samples"] for r in tested]
    y = [r["branches"]["untouched"]["continuation_samples"] for r in tested]
    p = wilcoxon(x, y, alternative="two-sided", zero_method="wilcox", correction=False, method="approx")
    return {"observed": len(vortices), "persistent": len(persistent), "median_persistent_age": float(np.median([v["max_age"] for v in persistent])),
        "all_final_net_winding_zero": all(r["final_net_winding"] == 0 for r in census["runs"]),
        "robustness_seeds": len(tested), "robustness_medians": medians, "core_vs_untouched_two_sided_p": float(p.pvalue),
        "interpretation": "Persistent topological object class and survival under the tested smooth core perturbation; nonsignificant difference is not a formal equivalence proof or autonomy claim."}


def forecast_evidence() -> dict:
    cohorts, pooled = [], []
    for name in EVIDENCE[6:8]:
        d = load(name)
        records = d["records"]
        field_errors, relational_errors, wins = [], [], 0
        for seed in sorted({r["seed"] for r in records}):
            train = [r for r in records if r["seed"] != seed]
            test = [r for r in records if r["seed"] == seed]
            y = np.asarray([r["future_survival"] for r in test])
            penalty = d["experiment"]["parameters"]["ridge"]
            a = (ridge_predict(train, test, FIELD_FEATURES, penalty) - y) ** 2
            b = (ridge_predict(train, test, RELATIONAL_FEATURES, penalty) - y) ** 2
            field_errors.extend(a.tolist())
            relational_errors.extend(b.tolist())
            wins += int(b.mean() < a.mean())
        field, relational = float(np.mean(field_errors)), float(np.mean(relational_errors))
        np.testing.assert_allclose(field, d["summary"]["field_baseline"]["brier"], rtol=1e-11)
        np.testing.assert_allclose(relational, d["summary"]["relational_model"]["brier"], rtol=1e-11)
        assert wins == d["summary"]["gate"]["held_seed_wins"]
        gain = (field - relational) / field
        assert bool(gain >= .05 and wins >= 7) == d["summary"]["gate"]["passed"]
        cohorts.append({"file": name, "records": len(records), "field_brier": field, "relational_brier": relational, "relative_reduction": gain, "held_seed_wins": wins, "gate_passed": d["summary"]["gate"]["passed"]})
        pooled.append((field_errors, relational_errors))
    a, b = [np.mean([e for cohort in pooled for e in cohort[i]]) for i in (0, 1)]
    return {"cohorts": cohorts, "combined_descriptive_reduction": float((a - b) / a),
        "interpretation": "Replicated relational predictive information, below the original object-level gate. No independent object dynamics or general interaction law established."}


def equation_probes() -> dict:
    adapter = V1Adapter()
    state = adapter.create(8, 3)
    state.theta[:] = 0
    state.theta[4, 3] = state.theta[3, 4] = np.pi / 2
    state.theta[4, 5] = state.theta[5, 4] = -np.pi / 2
    extra = {}
    rules_alignment.alignment_rule(state, adapter.params, extra)
    net = float(extra["grad_align"][4, 4])
    disagreement = sum(1 - np.cos(state.theta[r, c] - state.theta[4, 4]) for r, c in ((4, 3), (3, 4), (4, 5), (5, 4)))
    assert abs(net) < 1e-12 and disagreement > 3.99

    state.tau[:] = 1
    torque = rules_compression.compression_rule(state, adapter.params, {"grad_align": np.zeros((8, 8))})["torque"]
    assert np.all(torque > 0)
    fast, slow = adapter.create(8, 7), adapter.create(8, 7)
    slow.dt = fast.dt / 2
    initial = fast.theta.copy()
    adapter.advance(fast, 1)
    adapter.advance(slow, 1)
    structural_equal = all(np.array_equal(getattr(fast, name), getattr(slow, name)) for name in ("tau", "ux", "uy", "C"))
    wrap = lambda a: (a + np.pi) % (2 * np.pi) - np.pi
    theta_error = float(np.max(np.abs(wrap(fast.theta - initial) - 2 * wrap(slow.theta - initial))))
    assert structural_equal and theta_error < 1e-12
    sigma = adapter.params.sigma_c2
    return {
        "net_torque_cancellation": {"tension_source_at_center": net, "positive_disagreement_diagnostic": float(disagreement), "conclusion": "grad_align is magnitude of net alignment torque, not total disagreement or energy."},
        "fixed_sign_drive": {"minimum_tension_torque": float(torque.min()), "conclusion": "Compression rule adds +0.1*tau angular drive; for nonnegative tau a turning sign is supplied, not spontaneously selected."},
        "dt_convention": {"one_update_structural_state_identical_at_half_dt": structural_equal, "theta_double_increment_max_error": theta_error, "conclusion": "Structural recurrences are per-update while theta uses dt. Physical-time convergence requires an explicit convention; naive dt halving is not such a test."},
        "compression_semantics": {"C_at_detF_zero": 1., "C_at_detF_one": float(np.exp(-1 / (sigma + 1e-8))), "C_at_detF_minus_one": float(np.exp(-1 / (sigma + 1e-8))), "conclusion": "C emphasizes near-zero determinant and is sign-insensitive, not a general pressure or physical energy density."},
    }


def run(output: Path, parent: str | None = None) -> dict:
    if output.exists():
        raise ValueError("Refusing to overwrite a closed audit record; choose a new output directory.")
    sources = {**engine_hashes(), **file_hashes(PRODUCERS)}
    evidence = file_hashes(EVIDENCE)
    output.mkdir(parents=True)
    manifest = {"audit_id": output.name, "parent_audit_id": parent, "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Current named three-rule V1 preset, archived object/structural evidence and mathematical update semantics. V2 preserved and regression-checked, not a full V2 scientific audit.",
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "source_sha256": sources, "evidence_sha256": evidence,
        "historical_provenance_limit": "Legacy archives lack producer-source hashes. This audit replays archived evidence and freezes today's source snapshot; it cannot retroactively certify that every legacy run used these exact bytes.",
        "coverage_limits": ["No new vortex interaction experiment.", "No continuum or physical-time convergence result.", "No full audit of all optional V1 rules or V2 mechanisms.", "No proof of global continuous rotational symmetry, energy conservation, holography or fundamental physics."]}
    write_json(output / "manifest.json", manifest)
    write_json(output / "status.json", {"status": "running"})
    try:
        results = {"structural_evidence": structural_evidence(), "vortex_evidence": vortex_evidence(), "forecast_evidence": forecast_evidence(), "equation_probes": equation_probes()}
        completed = subprocess.run([__import__('sys').executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, capture_output=True, text=True)
        (output / "test_log.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError("Regression test suite failed; see test_log.txt.")
        assert sources == {**engine_hashes(), **file_hashes(PRODUCERS)}
        assert evidence == file_hashes(EVIDENCE)
        results["regression_tests_passed"] = True
        results["frozen_source_and_evidence_unchanged"] = True
        write_json(output / "report.json", results)
        write_json(output / "status.json", {"status": "closed", "source_and_evidence_unchanged": True})
        print(json.dumps(results, indent=2))
        return results
    except BaseException as exc:
        write_json(output / "status.json", {"status": "failed", "error": str(exc)})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parent-audit-id")
    args = parser.parse_args()
    run(args.output, args.parent_audit_id)


if __name__ == "__main__":
    main()
