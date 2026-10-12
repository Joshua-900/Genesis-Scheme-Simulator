"""Render an annotated theta-field explanation for the v2 coarsening result."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import Region, detect_relation_domains
from src.genesis_v2_zeta import ZetaParams, ZetaState, step


def capture(state: ZetaState, frame: int, cutoff: float, min_area: int) -> dict:
    domains = detect_relation_domains(state, cutoff, min_area)
    areas = [domain.area for domain in domains]
    return {
        "frame": frame,
        "theta": np.asarray(to_cpu(state.theta)),
        "permeability": 0.5 * (np.asarray(to_cpu(state.rx)) + np.asarray(to_cpu(state.ry))),
        "domains": domains,
        "largest_fraction": max((area / (state.N * state.N) for area in areas), default=0.0),
    }


def add_theta_field(axis, snapshot: dict, arrow_stride: int) -> None:
    theta = snapshot["theta"]
    axis.imshow(theta, cmap="twilight", vmin=0.0, vmax=2.0 * np.pi, interpolation="nearest")
    y, x = np.mgrid[0:theta.shape[0]:arrow_stride, 0:theta.shape[1]:arrow_stride]
    angles = theta[::arrow_stride, ::arrow_stride]
    axis.quiver(x, y, np.cos(angles), np.sin(angles), color="white", pivot="mid", scale=18, width=0.0035, headwidth=3.4, alpha=0.78)
    for domain in snapshot["domains"]:
        axis.contour(domain.mask, levels=[0.5], colors="#111111", linewidths=0.9, linestyles="--", alpha=0.85)
    count = len(snapshot["domains"])
    label = "domain" if count == 1 else "domains"
    axis.set_title(f"frame {snapshot['frame']:,}: {count} candidate {label}; largest {snapshot['largest_fraction']:.1%}")
    axis.set_xticks([]); axis.set_yticks([])


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an annotated theta-field explanation.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--early-frame", type=int, default=2_000)
    parser.add_argument("--late-frame", type=int, default=8_000)
    parser.add_argument("--sample-interval", type=int, default=200)
    parser.add_argument("--arrow-stride", type=int, default=4)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("findings/figures/2026-10-11_theta_field_explainer.png"))
    args = parser.parse_args()
    if args.N < 8 or args.early_frame < 1 or args.late_frame <= args.early_frame or args.sample_interval < 1 or args.arrow_stride < 1:
        raise SystemExit("Invalid figure arguments.")

    params = ZetaParams(potential_to_actual=0.05, relation_difference_gain=0.55, refractory_production=0.020, refractory_alignment_gain=0.90)
    state = ZetaState(args.N, seed=args.seed)
    snapshots = {}
    timeline = []
    for frame in range(args.late_frame + 1):
        if frame in (args.early_frame, args.late_frame):
            snapshots[frame] = capture(state, frame, args.cutoff, args.min_area)
        if frame % args.sample_interval == 0 or frame == args.late_frame:
            measured = capture(state, frame, args.cutoff, args.min_area)
            timeline.append((frame, len(measured["domains"]), measured["largest_fraction"]))
        if frame < args.late_frame:
            step(state, params)

    figure, axes = plt.subplots(2, 2, figsize=(13, 10), constrained_layout=True)
    figure.suptitle(
        "Reading the Genesis v2 theta field\n"
        "Hue + arrows: realized orientation | dashed outlines: measured relation domains",
        fontsize=16,
    )
    add_theta_field(axes[0, 0], snapshots[args.early_frame], args.arrow_stride)
    add_theta_field(axes[0, 1], snapshots[args.late_frame], args.arrow_stride)
    axes[0, 0].set_ylabel("Intermediate structure", fontsize=12)
    axes[0, 1].set_ylabel("Late-time outcome", fontsize=12)

    permeability = snapshots[args.early_frame]["permeability"]
    image = axes[1, 0].imshow(permeability, cmap="viridis", vmin=0.0, vmax=1.0, interpolation="nearest")
    axes[1, 0].set_title("Why the dashed outlines appear\nlow permeability marks relational separation")
    axes[1, 0].set_xticks([]); axes[1, 0].set_yticks([])
    colorbar = figure.colorbar(image, ax=axes[1, 0], shrink=0.82)
    colorbar.set_label("relation permeability")

    frames, counts, fractions = map(np.asarray, zip(*timeline))
    axis = axes[1, 1]
    axis.plot(frames, counts, color="#197278", linewidth=2.5, label="candidate-domain count")
    right = axis.twinx()
    right.plot(frames, fractions, color="#c44536", linewidth=2.5, label="largest-domain share")
    axis.set_title("The test: do boundaries remain plural and bounded?")
    axis.set_xlabel("frame")
    axis.set_ylabel("candidate domains", color="#197278")
    right.set_ylabel("largest share of field", color="#c44536")
    right.set_ylim(0.0, 1.0)
    axis.grid(alpha=0.25)
    lines = axis.lines + right.lines
    axis.legend(lines, [line.get_label() for line in lines], loc="center right")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180, facecolor="white")
    print(f"Wrote theta-field explainer to {args.output}")


if __name__ == "__main__":
    main()
