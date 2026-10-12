"""Render an evidence figure explaining the v2 coarsening result."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_zeta import ZetaParams, ZetaState, step


def capture(state: ZetaState, frame: int, cutoff: float, min_area: int) -> dict:
    domains = detect_relation_domains(state, cutoff, min_area)
    areas = [domain.area for domain in domains]
    return {
        "frame": frame,
        "theta": np.asarray(to_cpu(state.theta)),
        "permeability": 0.5 * (np.asarray(to_cpu(state.rx)) + np.asarray(to_cpu(state.ry))),
        "domain_count": len(domains),
        "largest_fraction": max((area / (state.N * state.N) for area in areas), default=0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the zeta coarsening evidence figure.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--early-frame", type=int, default=2_000)
    parser.add_argument("--late-frame", type=int, default=8_000)
    parser.add_argument("--sample-interval", type=int, default=200)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("findings/figures/2026-10-11_v2_coarsening_explainer.png"))
    args = parser.parse_args()
    if args.N < 8 or args.early_frame < 1 or args.late_frame <= args.early_frame or args.sample_interval < 1:
        raise SystemExit("Invalid figure arguments.")

    params = ZetaParams(potential_to_actual=0.05, relation_difference_gain=0.55, refractory_production=0.020, refractory_alignment_gain=0.90)
    state = ZetaState(args.N, seed=args.seed)
    snapshots = {}
    timeline = []
    for frame in range(args.late_frame + 1):
        if frame in (args.early_frame, args.late_frame):
            snapshots[frame] = capture(state, frame, args.cutoff, args.min_area)
        if frame % args.sample_interval == 0 or frame == args.late_frame:
            observed = capture(state, frame, args.cutoff, args.min_area)
            timeline.append(observed)
        if frame < args.late_frame:
            step(state, params)

    early, late = snapshots[args.early_frame], snapshots[args.late_frame]
    figure, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    figure.suptitle("Genesis v2: rich fields are not yet stable higher-order objects", fontsize=16)

    theta_maps = []
    for axis, snapshot, heading in zip(axes[0, :2], (early, late), ("Intermediate structure", "Late-time outcome")):
        image = axis.imshow(snapshot["theta"], cmap="twilight", vmin=0.0, vmax=2.0 * np.pi, interpolation="nearest")
        theta_maps.append(image)
        axis.set_title(f"Actuality $\\theta$: {heading}\nframe {snapshot['frame']:,}")
        axis.set_xticks([]); axis.set_yticks([])
    colorbar = figure.colorbar(theta_maps[-1], ax=axes[0, :2], shrink=0.8, ticks=(0, np.pi, 2.0 * np.pi))
    colorbar.set_ticklabels(("0", "$\\pi$", "$2\\pi$"))
    colorbar.set_label("realized local orientation")

    axes[0, 2].plot([row["frame"] for row in timeline], [row["domain_count"] for row in timeline], color="#197278", linewidth=2.5, label="candidate domains")
    axes[0, 2].set_title("Candidate-domain count")
    axes[0, 2].set_xlabel("frame")
    axes[0, 2].set_ylabel("count")
    axes[0, 2].grid(alpha=0.25)

    permeability_maps = []
    for axis, snapshot in zip(axes[1, :2], (early, late)):
        image = axis.imshow(snapshot["permeability"], cmap="viridis", vmin=0.0, vmax=1.0, interpolation="nearest")
        permeability_maps.append(image)
        count_label = "domain" if snapshot["domain_count"] == 1 else "domains"
        axis.set_title(f"Relation permeability\n{snapshot['domain_count']} {count_label}; largest {snapshot['largest_fraction']:.1%}")
        axis.set_xticks([]); axis.set_yticks([])
    colorbar = figure.colorbar(permeability_maps[-1], ax=axes[1, :2], shrink=0.8)
    colorbar.set_label("high = cells remain structurally connected")

    axes[1, 2].plot([row["frame"] for row in timeline], [row["largest_fraction"] for row in timeline], color="#c44536", linewidth=2.5, label="largest candidate")
    axes[1, 2].axhline(0.5, color="#555555", linestyle="--", linewidth=1)
    axes[1, 2].set_title("Largest candidate's field share")
    axes[1, 2].set_xlabel("frame")
    axes[1, 2].set_ylabel("fraction of lattice")
    axes[1, 2].set_ylim(0.0, 1.0)
    axes[1, 2].grid(alpha=0.25)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180, facecolor="white")
    print(f"Wrote explanatory figure to {args.output}")


if __name__ == "__main__":
    main()
