"""Paired audit of whether the existing P-to-A link changes high-compression dynamics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis_v2_integrated_local_structure_probe import make_params
from src.genesis_grid import diagnostics
from src.genesis_grid.backend import to_cpu
from src.genesis_v2_integrated import IntegratedState, step


def observe(state):
    theta = np.asarray(to_cpu(state.theta))
    px = np.asarray(to_cpu(state.px))
    py = np.asarray(to_cpu(state.py))
    plus, minus, _ = diagnostics.detect_vortices(state)

    return {
        "pa_alignment": float(np.mean(np.cos(theta - np.arctan2(py, px)))),
        "actual_order": float(
            np.hypot(np.mean(np.cos(theta)), np.mean(np.sin(theta)))
        ),
        "mean_tension": float(np.mean(to_cpu(state.tau))),
        "mean_compression": float(np.mean(to_cpu(state.C))),
        "vortex_count": len(plus) + len(minus),
    }


def run(seed, potential, args):
    state = IntegratedState(args.N, seed=seed)
    params = make_params(potential)
    for _ in range(args.frames): step(state,params)
    return observe(state)


def main():
    parser = argparse.ArgumentParser(description="Paired high-compression P-to-A audit.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2000)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v2_integrated_high_compression_audit.json"),
    )
    args = parser.parse_args()

    runs = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        runs.append(
            {
                "seed": seed,
                "parity": run(seed, False, args),
                "potential": run(seed, True, args),
            }
        )

    keys = list(runs[0]["parity"])
    medians = {
        key: {
            condition: float(np.median([run[condition][key] for run in runs]))
            for condition in ("parity", "potential")
        }
        for key in keys
    }
    data = {
        "schema_version": 1,
        "claim_boundary": "Field-level audit only; no object claim.",
        "experiment": {
            "name": "v2_integrated_high_compression_pa_audit",
            "N": args.N,
            "frames": args.frames,
            "seeds": args.seeds,
        },
        "runs": runs,
        "medians": medians,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(medians, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
