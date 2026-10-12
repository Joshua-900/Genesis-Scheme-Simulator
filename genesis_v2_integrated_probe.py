"""Headless first probe for the V1-derived P/A/R bridge.

The probe does not search for objects.  It compares the V1-parity baseline to
one narrowly defined intervention: independent potentiality influences
actuality while the inherited V1 structural loop remains unchanged.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.genesis_grid import diagnostics
from src.genesis_grid.backend import to_cpu
from src.genesis_v2_integrated import IntegratedParams, IntegratedState, step


def configure_v1_substrate(params: IntegratedParams) -> None:
    """Use the same conservative substrate as the existing object census."""
    params.alpha = 0.30
    params.gamma = 0.01
    params.kappa = 0.05
    params.curv = 0.04
    params.phase = 0.0
    params.dipole = 0.0
    params.triads = 0.0
    params.lock_strength = 0.96
    params.phase_lock_gain = 0.0
    params.tri_lock_gain = 0.0
    params.shell_geom_gain = 0.08


def configure_potential_influence(params: IntegratedParams) -> None:
    """The first bridge intervention: P remains independent but affects A."""
    params.potential_transport = 0.03
    params.potential_source_restore = 0.10
    params.potential_to_actual = 0.10


def observe(state: IntegratedState, frame: int) -> dict[str, float | int]:
    theta = np.asarray(to_cpu(state.theta))
    px, py = np.asarray(to_cpu(state.px)), np.asarray(to_cpu(state.py))
    plus, minus, _ = diagnostics.detect_vortices(state)
    p_angle = np.arctan2(py, px)
    return {
        "frame": frame,
        "potential_actual_alignment": float(np.mean(np.cos(theta - p_angle))),
        "mean_tension": float(np.mean(to_cpu(state.tau))),
        "mean_compression": float(np.mean(to_cpu(state.C))),
        "mean_relation_memory": float(0.5 * (np.mean(to_cpu(state.rx)) + np.mean(to_cpu(state.ry)))),
        "vortex_count": len(plus) + len(minus),
    }


def run_condition(name: str, args: argparse.Namespace, coupled: bool) -> dict:
    runs: list[dict] = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        state = IntegratedState(args.N, seed=seed)
        params = IntegratedParams()
        configure_v1_substrate(params)
        if coupled:
            configure_potential_influence(params)

        samples = []
        for frame in range(1, args.frames + 1):
            step(state, params)
            if frame % args.sample_interval == 0:
                samples.append(observe(state, frame))
        runs.append({"seed": seed, "samples": samples, "final": samples[-1]})
        final = samples[-1]
        print(
            f"{name} seed={seed}: P/A={final['potential_actual_alignment']:.3f}, "
            f"C={final['mean_compression']:.3f}, vortices={final['vortex_count']}"
        )

    final_keys = ("potential_actual_alignment", "mean_tension", "mean_compression", "vortex_count")
    median = {key: float(np.median([run["final"][key] for run in runs])) for key in final_keys}
    return {"condition": name, "parameters": vars(params), "runs": runs, "median_final": median}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare V1 parity against the first P-to-A bridge intervention.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("results/v2_integrated_potential_probe.json"))
    args = parser.parse_args()
    if args.N < 4 or args.frames < 1 or args.seeds < 1 or args.sample_interval < 1:
        raise SystemExit("--N >= 4 and --frames, --seeds, --sample-interval must be positive.")

    baseline = run_condition("v1_parity", args, coupled=False)
    coupled = run_condition("independent_potential_influences_actuality", args, coupled=True)
    output = {
        "schema_version": 1,
        "claim_boundary": "This measures causal field distinction and inherited structural change, not higher-order objects.",
        "experiment": {
            "name": "v2_integrated_first_potential_bridge_probe",
            "question": "Can P remain distinct from A while changing V1-derived structural dynamics?",
            "grid_size": args.N,
            "frames": args.frames,
            "seeds": args.seeds,
        },
        "conditions": [baseline, coupled],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
