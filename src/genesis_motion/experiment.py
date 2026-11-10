"""Matched V1 vortex encounters and held-out motion forecasts; opt-in only.

Run: python -B -m src.genesis_motion.experiment --output results/vortex_motion_new
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import platform

import numpy as np

from genesis_multiscale_audit import ROOT, engine_hashes, write_json
from src.genesis_audit.verify import verify
from src.genesis_audit.v1_adapter import V1Adapter
from .evaluation import evaluate
from .observations import ANGULAR, ANGULAR_EXTRA, KINEMATIC, STRUCTURAL, PeriodicTracker, choose_pair, delta, erase_structure, features


BRANCHES = ("untouched", "selected_structure", "background_structure")


@dataclass(frozen=True)
class Config:
    n: int = 64
    burn: int = 800
    tracker_warmup: int = 100
    follow: int = 400
    interval: int = 5
    horizon: int = 100
    minimum_age: int = 50
    minimum_pair_distance: float = 3.
    maximum_pair_distance: float = 16.
    radius: float = 5.
    tracker_distance: float = 2.5
    tracker_margin: float = .25
    train: tuple[int, ...] = tuple(range(1001, 1009))
    test: tuple[int, ...] = tuple(range(2001, 2009))
    replication: tuple[int, ...] = tuple(range(3001, 3009))
    ridge: float = 10.
    minimum_gain: float = .05
    bootstrap: int = 2000

    def validate(self):
        if self.n < 32 or not 0 < self.tracker_warmup <= self.burn or not 0 < self.horizon < self.follow:
            raise ValueError("Need N>=32, burn >= tracker warmup >0, and 0<horizon<follow.")
        if self.interval < 1 or any(v % self.interval for v in (self.burn, self.tracker_warmup, self.follow, self.horizon)):
            raise ValueError("Burn, tracker warmup, follow and horizon must be multiples of interval.")
        seeds = self.train + self.test + self.replication
        if len(set(seeds)) != len(seeds) or min(map(len, (self.train, self.test, self.replication))) < 3 or min(seeds) < 0:
            raise ValueError("Cohorts need >=3 unique, disjoint nonnegative seeds each.")
        if not 0 < self.radius < self.n / 4 or not 0 < self.minimum_pair_distance < self.maximum_pair_distance < self.n / 2:
            raise ValueError("Invalid neighborhood radius or pair-distance limits.")
        if self.minimum_age < 0 or self.minimum_age > self.tracker_warmup or self.ridge <= 0 or self.bootstrap < 1:
            raise ValueError("Invalid age, regression, or bootstrap setting.")


def trace_branch(adapter, state, tracker, selected, config, record_visual):
    trajectories, absolute, vectors, visual_theta, visual_c = [], [], [], [], []
    previous = None
    unwrapped = np.full((2, 2), np.nan)
    for elapsed in range(0, config.follow + 1, config.interval):
        if elapsed:
            adapter.advance(state, config.interval)
            tracker.update(state.theta, config.burn + elapsed)
        snapshot = adapter.snapshot(state)
        positions = np.full((2, 2), np.nan)
        current = []
        for slot, identity in enumerate(selected):
            track = tracker.tracks.get(identity)
            if track is None:
                current.append(None)
                continue
            positions[slot] = [track.x, track.y]
            partner = tracker.tracks.get(selected[1 - slot])
            current.append(features(snapshot, track, partner, config.burn + elapsed, config.radius))
            if previous is None:
                unwrapped[slot] = positions[slot]
            elif np.isfinite(previous[slot]).all():
                unwrapped[slot] += delta(positions[slot], previous[slot], config.n)
        trajectories.append(positions.copy())
        absolute.append(unwrapped.copy())
        vectors.append(current)
        previous = positions
        if record_visual:
            visual_theta.append(snapshot["theta"].astype(np.float32))
            visual_c.append(snapshot["C"].astype(np.float32))
    positions = np.asarray(trajectories)
    absolute = np.asarray(absolute)
    rows = []
    offset = config.horizon // config.interval
    for start in range(len(positions) - offset):
        for slot in range(2):
            if vectors[start][slot] is None:
                continue
            survives = bool(np.isfinite(positions[start + offset, slot]).all())
            motion = absolute[start + offset, slot] - absolute[start, slot] if survives else np.full(2, np.nan)
            rows.append({"elapsed": start * config.interval, "slot": slot, "survived": survives, "motion": motion, **vectors[start][slot]})
    pair_observed = np.isfinite(positions).all(axis=(1, 2))
    return {"positions": positions, "unwrapped": absolute, "pair_observed": pair_observed, "records": rows,
        "theta": np.asarray(visual_theta), "C": np.asarray(visual_c)}


def collect(seed: int, config: Config, visual: bool):
    adapter = V1Adapter()
    state = adapter.create(config.n, seed)
    tracker = PeriodicTracker(config.n, config.tracker_distance, config.tracker_margin)
    adapter.advance(state, config.burn - config.tracker_warmup)
    tracker.update(state.theta, config.burn - config.tracker_warmup)
    for index in range(config.tracker_warmup // config.interval):
        adapter.advance(state, config.interval)
        frame = config.burn - config.tracker_warmup + (index + 1) * config.interval
        tracker.update(state.theta, frame)
    snapshot = adapter.snapshot(state)
    pair = choose_pair(tracker.tracks, snapshot, config.burn, config.minimum_age, config.minimum_pair_distance, config.maximum_pair_distance)
    if pair is None:
        return None
    plus, minus = [tracker.tracks[i] for i in pair]
    plus_position = np.asarray([plus.x, plus.y])
    midpoint = (plus_position + delta(np.asarray([minus.x, minus.y]), plus_position, config.n) / 2) % config.n
    background = (midpoint + config.n / 2) % config.n
    branches = {}
    for name, center in zip(BRANCHES, (None, midpoint, background)):
        branch = adapter.clone(state)
        if center is not None:
            erase_structure(branch, center, config.radius)
        if not np.array_equal(branch.theta, state.theta):
            raise RuntimeError("Matched branches do not have identical initial theta.")
        branches[name] = trace_branch(adapter, branch, copy.deepcopy(tracker), pair, config, visual)
    return {"seed": seed, "pair_ids": list(pair), "midpoint": midpoint.tolist(), "background": background.tolist(), "snapshot": snapshot, "branches": branches}


def run(config: Config, output: Path) -> dict:
    config.validate()
    if output.exists():
        raise ValueError("Refusing to overwrite an existing experiment directory.")
    inherited = verify(ROOT / "results/v1_baseline_audit_2026-10-31/manifest.json")
    if not inherited["fingerprints_match"] or not inherited["environment_matches"]:
        raise ValueError("Closed baseline differs; review its explicit delta before using this preset.")
    before = engine_hashes()
    output.mkdir(parents=True)
    adapter = V1Adapter()
    sources = list((ROOT / "src/genesis_motion").glob("*.py")) + [ROOT / "tests/test_vortex_motion.py"]
    protocol = {"experiment_id": output.name, "parent_audit_id": inherited["audit_id"], "parent_manifest_sha256": inherited["manifest_sha256"],
        "created_utc": datetime.now(timezone.utc).isoformat(), "config": asdict(config), "parameters": vars(adapter.params),
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "engine_source_sha256_before": before, "new_source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "question": "Does present structural state steer tracked vortex trajectories and improve compact forecasts on fresh seeds?",
        "selection": "At fixed burn-in choose an opposite-charge pair, both old enough, within distance bounds; maximize current radius-5 midpoint compression, then age. No future selection. Populated field, not isolated two-body initial data.",
        "branches": "Same initial theta and tracker in all arms. Smooth compact cosine-taper reset of tau/ux/uy/C at selected midpoint or equal-shaped periodic antipode; untouched control. Not equal state-removal magnitude.",
        "tracker": "Separate periodic mutual-nearest same-charge matcher, distance and ambiguity gates, no gap bridging. Loss is strict observed continuation, not proven annihilation.",
        "features": {"common_kinematic": KINEMATIC, "local_angular": ANGULAR, "extra_angular_for_matched_capacity": ANGULAR_EXTRA, "structural": STRUCTURAL},
        "models": "Structural uses 8 kinematic +8 angular +8 structural features. Matched field uses 8 kinematic +16 angular. Shuffled structure has identical width, shuffled within seed/branch separately in each cohort. Branch labels, absolute positions and elapsed frame are excluded from inputs.",
        "primary_gate": "Motion MSE on strict horizon survivors: >=5% reduction vs matched field, shuffled structure and zero-displacement persistence; positive paired-seed 95% bootstrap lower limit and >=ceil(.7*cohort seeds) wins. Both unseen cohorts must pass with >=5 surviving records per seed and >=10% nonzero (>0.1 cell) displacements.",
        "secondary_gate": "Same comparisons for strict continuation Brier score, requiring both outcome classes in each cohort. Motion conditional on survivors; no equivalence to autonomous dynamics.",
        "causal_endpoint": "At the fixed forecast horizon, pair position RMS difference from untouched, compared selected vs background reset, on seeds where both identities are observed in all arms. Report coverage and paired difference interval. Also report observed pair continuation counts. This conditional contrast does not generalize to identities lost after intervention.",
        "visual_selection": "First eligible training seed in ascending order; chosen without inspecting future trajectories or forecast performance.",
        "limits": ["Fresh seed cohorts, one selected pair per seed, one grid size and one regime; not a universal interaction law.",
            "Conservative periodic identities can terminate on matching ambiguity or missed observations; tracker loss is not automatically physical destruction.",
            "Structural reset is a counterfactual state intervention, not proof that two naturally occurring histories realize the compared states.",
            "Joint structural reset does not identify separate effects of tension, geometry, compression or history.",
            "State-removal magnitude differs between selected and background neighborhoods; control matches shape and position policy, not energy or amount.",
            "Per-seed clustering controls repeated observations, but small cohorts and fixed ridge models limit generalization.",
            "An incremental forecast gain would support state-dependent object modeling, not autonomous closure, novel physics, physical time, matter or holography."]}
    write_json(output / "protocol.json", protocol)
    write_json(output / "status.json", {"status": "collecting"})
    arrays = {k: [] for k in ("seed", "branch", "elapsed", "slot", "survived", "motion", "kinematic", "local_field", "field_matched", "structural")}
    summaries, skipped, visual_seed = [], [], None
    try:
        for seed in config.train + config.test + config.replication:
            visual = visual_seed is None and seed in config.train
            result = collect(seed, config, visual)
            if result is None:
                skipped.append(seed)
                print(f"seed={seed}: no eligible pair", flush=True)
                continue
            if visual:
                visual_seed = seed
            raw = {f"initial_{k}": v for k, v in result["snapshot"].items()}
            summary = {k: result[k] for k in ("seed", "pair_ids", "midpoint", "background")}
            summary["branches"] = {}
            for b, name in enumerate(BRANCHES):
                branch = result["branches"][name]
                raw[f"{name}_positions"] = branch["positions"]
                raw[f"{name}_unwrapped"] = branch["unwrapped"]
                raw[f"{name}_pair_observed"] = branch["pair_observed"]
                summary["branches"][name] = {"pair_observed_samples_after_start": int(branch["pair_observed"][1:].sum()),
                    "pair_observed_at_end": bool(branch["pair_observed"][-1]), "forecast_records": len(branch["records"])}
                for row in branch["records"]:
                    for key in arrays:
                        arrays[key].append(seed if key == "seed" else b if key == "branch" else row[key])
                if visual:
                    raw[f"{name}_theta"] = branch["theta"]
                    raw[f"{name}_C"] = branch["C"]
            horizon_index = config.horizon // config.interval
            position_at_horizon = [result["branches"][name]["positions"][horizon_index] for name in BRANCHES]
            joint = all(np.isfinite(p).all() for p in position_at_horizon)
            summary["joint_observed_at_horizon"] = bool(joint)
            if joint:
                differences = [float(np.sqrt(np.mean(np.sum(delta(p, position_at_horizon[0], config.n) ** 2, axis=1)))) for p in position_at_horizon[1:]]
                summary["horizon_position_divergence"] = dict(zip(BRANCHES[1:], differences))
            np.savez_compressed(output / f"seed_{seed}.npz", **raw)
            summaries.append(summary)
            print(f"seed={seed}: records={[summary['branches'][b]['forecast_records'] for b in BRANCHES]}; joint horizon={joint}", flush=True)
        joined = {k: np.asarray(v) for k, v in arrays.items()}
        if not summaries:
            raise RuntimeError("No eligible pairs; no claims can be evaluated.")
        forecasting = evaluate(joined, config.train, {"test": config.test, "replication": config.replication}, config.ridge, config.minimum_gain, config.bootstrap)
        np.savez_compressed(output / "forecasts.npz", **joined)
        joint = [s for s in summaries if s["joint_observed_at_horizon"]]
        differences = np.asarray([s["horizon_position_divergence"]["selected_structure"] - s["horizon_position_divergence"]["background_structure"] for s in joint])
        if len(differences):
            rng = np.random.default_rng(143)
            resampled = differences[rng.integers(0, len(differences), (config.bootstrap, len(differences)))].mean(axis=1)
            interval = np.quantile(resampled, [.025, .975]).tolist()
        else:
            interval = None
        causal = {"joint_observed_seed_count": len(joint), "eligible_seed_count": len(summaries), "seed_ids": [s["seed"] for s in joint],
            "mean_selected_minus_background_position_divergence": float(differences.mean()) if len(differences) else None,
            "paired_seed_bootstrap_95_interval": interval,
            "positive_conditional_motion_contrast": bool(len(joint) >= 6 and interval is not None and interval[0] > 0),
            "coverage_limit": "Conditional on strict observation of both identities in all arms at the horizon; report lost identities separately."}
        after = engine_hashes()
        if before != after:
            raise RuntimeError("Preserved engine sources changed; result not accepted.")
        report = {"experiment_id": output.name, "source_and_baseline_unchanged": True, "engine_source_sha256_after": after,
            "visual_seed": visual_seed, "skipped_seeds": skipped, "selection_coverage": len(summaries), "forecast_records": len(joined["seed"]),
            "seeds": summaries, "conditional_motion_contrast": causal, "forecast": forecasting,
            "claim_boundary": "Specific-regime observed vortex trajectories and compact forecasts under joint structural-state interventions; not a universal interaction law, autonomous matter, emergent time or holography."}
        write_json(output / "report.json", report)
        write_json(output / "status.json", {"status": "complete", "engines_unchanged": True})
        print(f"Completed: {output}; motion gate={forecasting['gate_passes']}", flush=True)
        return report
    except BaseException as exc:
        write_json(output / "status.json", {"status": "failed", "error": str(exc)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds-per-cohort", type=int, default=8)
    args = parser.parse_args()
    k = args.seeds_per_cohort
    if not 3 <= k <= 100:
        parser.error("Use between 3 and 100 seeds per cohort.")
    run(Config(train=tuple(range(1001, 1001 + k)), test=tuple(range(2001, 2001 + k)), replication=tuple(range(3001, 3001 + k))), args.output)


if __name__ == "__main__":
    main()
