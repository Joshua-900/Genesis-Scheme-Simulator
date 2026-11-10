"""Standalone classical organization audit. Does not change V1 or V2 engines.

Example: .venv/Scripts/python.exe -B genesis_multiscale_audit.py --output results/multiscale_audit
The protocol is written before collection; existing output directories are refused.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import time

import numpy as np

from src.genesis_audit.analysis import (
    FULL_FEATURES, THETA_FEATURES, descriptors, evaluate_dataset, feature_vectors,
    observational_controls, response_targets, spectrum_mismatch, square_masks, winding,
)
from src.genesis_audit.v1_adapter import FIELDS, V1Adapter


ROOT = Path(__file__).resolve().parent
CLAIM_BOUNDARY = "Classical multiscale representation and held-out perturbation-response prediction only; no spatial bulk, quantum entanglement, physical energy, matter, or holographic duality is established."


@dataclass(frozen=True)
class AuditConfig:
    grid_sizes: tuple[int, ...] = (32, 64)
    modes: tuple[str, ...] = ("v1", "alignment_only", "geometry_ablation")
    sample_frames: tuple[int, ...] = (300, 450, 600)
    scales: tuple[int, ...] = (2, 4, 8, 16)
    train_seeds: tuple[int, ...] = (1, 2, 3, 4, 5, 6)
    test_seeds: tuple[int, ...] = (101, 102, 103, 104, 105, 106)
    replication_seeds: tuple[int, ...] = (201, 202, 203, 204, 205, 206)
    centers_per_snapshot: int = 4
    horizon: int = 80
    amplitude: float = .30
    pulse_width: float = 1.5
    dt: float = .05
    kappa: float = .10
    ridge: float = 10.
    minimum_gain: float = .05
    win_fraction: float = .70
    bootstrap_draws: int = 2000

    def validate(self) -> None:
        for name in ("grid_sizes", "sample_frames", "scales"):
            values = getattr(self, name)
            if not values or tuple(sorted(set(values))) != values or any(v < 1 for v in values):
                raise ValueError(f"{name} must be strictly increasing positive integers.")
        if min(self.grid_sizes) < 16 or max(self.scales) > min(self.grid_sizes) // 2:
            raise ValueError("Grid sizes must be >=16, with largest block <= half the smallest grid.")
        if self.scales[0] < 2:
            raise ValueError("Context blocks must be >=2; local input is the center site.")
        all_seeds = self.train_seeds + self.test_seeds + self.replication_seeds
        if len(set(all_seeds)) != len(all_seeds) or any(s < 0 for s in all_seeds):
            raise ValueError("All seeds must be nonnegative, unique and disjoint between cohorts.")
        if min(len(self.train_seeds), len(self.test_seeds), len(self.replication_seeds)) < 3:
            raise ValueError("At least three independent seeds per cohort are required.")
        if not self.modes or len(set(self.modes)) != len(self.modes) or any(m not in ("v1", "alignment_only", "geometry_ablation") for m in self.modes):
            raise ValueError("Modes must be unique supported pipeline names.")
        if min(self.horizon, self.centers_per_snapshot, self.bootstrap_draws) < 1 or self.centers_per_snapshot > min(self.grid_sizes) ** 2:
            raise ValueError("Positive horizon, valid unique center count, and bootstrap draws are required.")
        if not all(math.isfinite(v) for v in (self.amplitude, self.pulse_width, self.dt, self.kappa, self.ridge, self.minimum_gain, self.win_fraction)):
            raise ValueError("All continuous parameters must be finite.")
        if self.amplitude <= 0 or self.pulse_width <= 0 or self.dt <= 0 or self.ridge <= 0 or self.kappa < 0 or not 0 < self.minimum_gain < 1 or not 0 < self.win_fraction <= 1:
            raise ValueError("Invalid pulse, evolution, regression, or gate parameters.")


def engine_hashes() -> dict[str, str]:
    """All V1 and V2 Python sources, including prototypes; excludes caches."""
    paths = list((ROOT / "src/genesis_grid").rglob("*.py"))
    for directory in (ROOT / "src").glob("genesis_v2*"):
        paths.extend(directory.rglob("*.py"))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def write_json(path: Path, value: dict) -> None:
    # Atomic replace avoids leaving a half-written final report on interruption.
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def collect_seed(config: AuditConfig, n: int, mode: str, seed: int) -> tuple[dict[str, np.ndarray], list[dict]]:
    adapter = V1Adapter(mode, config.kappa, config.dt)
    state = adapter.create(n, seed)
    arrays: dict[str, list] = {"seed": [], "frame": [], "center": [], "targets": []}
    organization = []
    previous = 0
    for frame in config.sample_frames:
        adapter.advance(state, frame - previous)
        previous = frame
        snapshot = adapter.snapshot(state)
        for name in FIELDS:
            arrays.setdefault(f"snapshot_{name}", []).append(snapshot[name])
        reference = adapter.clone(state)
        adapter.advance(reference, config.horizon)
        future = adapter.snapshot(reference)
        rng = np.random.default_rng(np.random.SeedSequence([seed, frame, n, 281]))
        locations = rng.choice(n * n, config.centers_per_snapshot, replace=False)
        centers = [(int(location // n), int(location % n)) for location in locations]
        controls = {"original": snapshot, **observational_controls(snapshot, rng)}
        charges = {name: winding(values["theta"]) for name, values in controls.items()}
        for center in centers:
            features = feature_vectors(snapshot, center, config.scales, charges["original"])
            branch = adapter.clone(state)
            adapter.perturb(branch, center, config.amplitude, config.pulse_width)
            adapter.advance(branch, config.horizon)
            target = response_targets(future, adapter.snapshot(branch), center)
            arrays["seed"].append(seed)
            arrays["frame"].append(frame)
            arrays["center"].append(center)
            arrays["targets"].append(target)
            for track, representations in features.items():
                for name, value in representations.items():
                    arrays.setdefault(f"{track}__{name}", []).append(value)
            for control_name, values in controls.items():
                for scale, mask in zip(config.scales, square_masks(n, center, config.scales)):
                    d = descriptors(values, mask, charges[control_name])
                    organization.append({"seed": seed, "frame": frame, "center": list(center), "control": control_name,
                        "scale": scale, "coherence": d["coherence"], "abs_winding_density": d["abs_winding_density"]})
        organization.append({"seed": seed, "frame": frame, "control": "phase_surrogate_spectrum_error",
            "relative_spectral_mismatch_after_unit_projection": spectrum_mismatch(snapshot["theta"], controls["phase_surrogate"]["theta"])})
    return {name: np.asarray(values) for name, values in arrays.items()}, organization


def summarize_organization(records: list[dict]) -> dict:
    """Seed is the independent unit; center/frame measurements stay clustered."""
    summary = {}
    for control in ("original", "spatial_permutation", "independent_angles", "phase_surrogate"):
        by_scale = {}
        for scale in sorted({r["scale"] for r in records if "scale" in r}):
            selected = [r for r in records if r["control"] == control and r.get("scale") == scale]
            seed_values = [{key: float(np.mean([r[key] for r in selected if r["seed"] == seed])) for key in ("coherence", "abs_winding_density")} for seed in sorted({r["seed"] for r in selected})]
            by_scale[str(scale)] = {key: {"mean_across_seeds": float(np.mean([s[key] for s in seed_values])),
                "std_across_seeds": float(np.std([s[key] for s in seed_values]))} for key in ("coherence", "abs_winding_density")}
        summary[control] = by_scale
    summary["phase_surrogate_mean_spectral_mismatch"] = float(np.mean([r["relative_spectral_mismatch_after_unit_projection"] for r in records if r["control"] == "phase_surrogate_spectrum_error"]))
    return summary


def protocol(config: AuditConfig, before: dict[str, str]) -> dict:
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    own_paths = [ROOT / "genesis_multiscale_audit.py", *sorted((ROOT / "src/genesis_audit").glob("*.py"))]
    return {
        "schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(), "config": asdict(config),
        "claim_boundary": CLAIM_BOUNDARY, "git_head": revision,
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__, "backend": "numpy_cpu"},
        "engine_source_sha256_before": before,
        "audit_source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in own_paths},
        "pipelines": {mode: {"params": vars(V1Adapter(mode, config.kappa, config.dt).params),
            "rules": [r.__module__ + "." + r.__name__ for r in V1Adapter(mode, config.kappa, config.dt).rules]} for mode in config.modes},
        "design": {
            "primary": "full_state_summaries multiscale versus matched planar_shells, shuffled_context and training_mean, in V1",
            "secondary": "theta_only, local-only/zero-response baselines, snapshot controls and alternative pipelines",
            "targets": ["RMS_phasor_response_radius_0_to_2", "RMS_phasor_response_radius_2_to_4", "RMS_phasor_response_radius_4_to_8"],
            "feature_names": {"theta_only": THETA_FEATURES, "full_state_summaries": FULL_FEATURES},
            "comparison": "local center-site summary + equal-count nested square blocks or disjoint square shells, same outer footprint and same winding halo",
            "gate": "For every comparator, each unseen cohort needs >=minimum_gain loss reduction, positive paired-seed 95% bootstrap lower bound, and ceil(win_fraction * seed_count) wins. Both cohorts and all specified V1 grid sizes must pass.",
            "loss": "Mean squared prediction error standardized per response ring by training-target standard deviation, floored at 1e-6; average per independent seed",
            "limitations": ["Exploratory small cohorts and fixed linear ridge model; no optimized model selection.",
                "Independent angles and spatial permutation are observational controls, not simulated trajectories.",
                "Fourier phase surrogate is NOT pair-correlation matched after projection to unit angles; spectral mismatch is reported.",
                "Shuffled context permutes context within seed across times and centers while preserving local inputs.",
                "No mutual-information estimator is fitted; coherence and winding are descriptive statistics, not entropy or entanglement.",
                "Nested versus shell summaries are alternative representations of the same input footprint; gains can reflect feature geometry or ridge bias, not new dimensions.",
                "Gaussian pulse has small nonzero tails at every site; response radius is not a finite-speed or causality measurement.",
                "No bulk reconstruction, emergent locality, energy conservation or matter claim is tested."],
        },
    }


def run(config: AuditConfig, output: Path) -> dict:
    config.validate()
    if output.exists():
        raise ValueError(f"Refusing to overwrite an existing audit directory: {output}")
    before = engine_hashes()
    output.mkdir(parents=True)
    frozen = protocol(config, before)
    write_json(output / "protocol.json", frozen)
    write_json(output / "status.json", {"status": "collecting", "engine_sources_unchanged": True})
    started = time.perf_counter()
    results = {}
    try:
        for n in config.grid_sizes:
            for mode in config.modes:
                directory = output / f"N{n}" / mode
                directory.mkdir(parents=True)
                rows, organizations = [], []
                for seed in config.train_seeds + config.test_seeds + config.replication_seeds:
                    arrays, records = collect_seed(config, n, mode, seed)
                    np.savez_compressed(directory / f"seed_{seed}.npz", **arrays)
                    rows.append(arrays)
                    organizations.extend(records)
                    print(f"N={n} {mode} seed={seed}: {len(arrays['seed'])} matched perturbations", flush=True)
                # Snapshot arrays have a different leading axis from event arrays;
                # save snapshots per seed above and join only events for regression.
                joined = {key: np.concatenate([r[key] for r in rows]) for key in rows[0] if not key.startswith("snapshot_")}
                evaluation = evaluate_dataset(joined, config.train_seeds, {"test": config.test_seeds, "replication": config.replication_seeds},
                    config.ridge, config.minimum_gain, config.win_fraction, config.bootstrap_draws)
                np.savez_compressed(directory / "forecasts.npz", **joined)
                write_json(directory / "organization_records.json", {"records": organizations})
                result = {"forecast": evaluation, "organization": summarize_organization(organizations)}
                write_json(directory / "summary.json", result)
                results[f"N{n}/{mode}"] = result
                write_json(output / "status.json", {"status": "collecting", "completed_datasets": list(results), "elapsed_seconds": time.perf_counter() - started})
        after = engine_hashes()
        if before != after:
            raise RuntimeError("V1/V2 source integrity changed during the audit; results are not accepted.")
        v1 = [results[f"N{n}/v1"]["forecast"]["primary_gate_passes"] for n in config.grid_sizes if "v1" in config.modes]
        report = {"schema_version": 1, "claim_boundary": CLAIM_BOUNDARY, "protocol": "protocol.json", "elapsed_seconds": time.perf_counter() - started,
            "engine_sources_unchanged": True, "engine_source_sha256_after": after,
            "primary_gate_passes": bool(v1 and all(v1)), "datasets": results}
        write_json(output / "report.json", report)
        write_json(output / "status.json", {"status": "complete", "engine_sources_unchanged": True, "elapsed_seconds": report["elapsed_seconds"]})
        print(f"Completed: {output / 'report.json'}; primary gate passes={report['primary_gate_passes']}", flush=True)
        return report
    except BaseException as exc:
        write_json(output / "status.json", {"status": "failed", "error": str(exc), "engine_sources_unchanged": before == engine_hashes()})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/multiscale_audit"))
    parser.add_argument("--grid-sizes", type=int, nargs="+", default=[32, 64])
    parser.add_argument("--modes", nargs="+", choices=["v1", "alignment_only", "geometry_ablation"], default=["v1", "alignment_only", "geometry_ablation"])
    parser.add_argument("--sample-frames", type=int, nargs="+", default=[300, 450, 600])
    parser.add_argument("--scales", type=int, nargs="+", default=[2, 4, 8, 16])
    parser.add_argument("--seeds-per-cohort", type=int, default=6)
    parser.add_argument("--centers", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=80)
    args = parser.parse_args()
    if not 3 <= args.seeds_per_cohort <= 99:
        parser.error("--seeds-per-cohort must be between 3 and 99 for disjoint fixed seed ranges.")
    k = args.seeds_per_cohort
    config = AuditConfig(grid_sizes=tuple(args.grid_sizes), modes=tuple(args.modes), sample_frames=tuple(args.sample_frames), scales=tuple(args.scales),
        train_seeds=tuple(range(1, k + 1)), test_seeds=tuple(range(101, 101 + k)), replication_seeds=tuple(range(201, 201 + k)),
        centers_per_snapshot=args.centers, horizon=args.horizon)
    try:
        run(config, args.output)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
