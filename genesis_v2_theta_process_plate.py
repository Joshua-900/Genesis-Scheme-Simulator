"""Render a field-first explanatory plate using the actual theta data and boundaries."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_zeta import ZetaParams, ZetaState, step


def evolve(frames: int, seed: int, size: int) -> ZetaState:
    state = ZetaState(size, seed=seed)
    params = ZetaParams(
        potential_to_actual=0.05,
        relation_difference_gain=0.55,
        refractory_production=0.020,
        refractory_alignment_gain=0.90,
    )
    for _ in range(frames):
        step(state, params)
    return state


def plot_field(axis, state: ZetaState, cutoff: float, min_area: int, arrows: bool) -> list:
    theta = np.asarray(to_cpu(state.theta))
    domains = detect_relation_domains(state, cutoff, min_area)
    axis.imshow(theta, cmap="twilight", vmin=0.0, vmax=2.0 * np.pi, interpolation="nearest")
    if arrows:
        yy, xx = np.mgrid[2:theta.shape[0]:5, 2:theta.shape[1]:5]
        angle = theta[2::5, 2::5]
        axis.quiver(xx, yy, np.cos(angle), np.sin(angle), color="#f7f1dc", pivot="mid", scale=16, width=0.004, headwidth=3.3, alpha=0.84)
    for domain in domains:
        axis.contour(domain.mask, levels=[0.5], colors="#f4d06f", linewidths=1.35, linestyles="--", alpha=0.98)
    axis.set_xticks([]); axis.set_yticks([])
    return domains


def label(axis, xy, text, color, target, side="left") -> None:
    x, y = xy
    alignment = "left" if side == "left" else "right"
    axis.text(x, y, text, transform=axis.transAxes, color="#f6f3eb", fontsize=11.5, fontweight="bold", ha=alignment, va="center", linespacing=1.25)
    axis.annotate("", xy=target, xycoords="data", xytext=(x, y), textcoords=axis.transAxes, arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.7, "connectionstyle": "arc3,rad=0.14"})


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an artistic process plate over actual theta data.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("findings/figures/2026-10-11_theta_process_plate.png"))
    args = parser.parse_args()
    early, late = evolve(2_000, args.seed, args.N), evolve(8_000, args.seed, args.N)

    figure = plt.figure(figsize=(16, 9), facecolor="#11151c")
    main_axis = figure.add_axes((0.17, 0.14, 0.54, 0.68), facecolor="#11151c")
    plot_field(main_axis, early, args.cutoff, args.min_area, arrows=True)
    main_axis.set_title("Actual theta field at frame 2,000", color="#f6f3eb", fontsize=18, loc="left", pad=15, fontweight="bold")
    main_axis.text(0.0, 1.01, "real orientation; dashed contours are measured relation boundaries", transform=main_axis.transAxes, color="#b9c1cc", fontsize=10.5, va="bottom")

    # These are diagrammatic callouts for named hypotheses, deliberately outside the measurement surface.
    label(main_axis, (-0.28, 0.79), "ACTUALITY  theta\nHue + strokes show\nlocal realized direction", "#f4d06f", (20, 17), "left")
    label(main_axis, (1.27, 0.70), "RELATION\nDashed perimeter =\nweakened connection", "#f4d06f", (49, 28), "right")
    label(main_axis, (-0.27, 0.35), "DELTA\nA broad-scale brake\nagainst total absorption", "#e38c39", (25, 42), "left")
    label(main_axis, (1.28, 0.37), "EPSILON\nPotential availability:\na renewable resource", "#dd6e9f", (44, 44), "right")
    label(main_axis, (0.50, -0.10), "ZETA  A refractory response: coherence eventually resists more coherence", "#61c4c4", (32, 55), "left")

    main_axis.add_patch(FancyArrowPatch((5, 58), (57, 5), connectionstyle="arc3,rad=-0.42", arrowstyle="simple", mutation_scale=16, color="#e38c39", alpha=0.58))

    outcome_axis = figure.add_axes((0.79, 0.23, 0.15, 0.27), facecolor="#11151c")
    plot_field(outcome_axis, late, args.cutoff, args.min_area, arrows=False)
    outcome_axis.set_title("frame 8,000", color="#f6f3eb", fontsize=11, pad=8)
    figure.text(0.79, 0.17, "The test: do dashes\nstay plural and bounded?\n\nCurrent answer: no.\nThey merge into one region.", color="#d7dde5", fontsize=10.5, linespacing=1.35)

    figure.text(0.055, 0.93, "GENESIS v2 / A FIELD TRYING TO BECOME AN INDIVIDUAL", color="#f6f3eb", fontsize=19, fontweight="bold")
    figure.text(0.055, 0.89, "A field-first process illustration grounded in the actual zeta theta state, seed 1.", color="#b9c1cc", fontsize=10.5)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180, facecolor=figure.get_facecolor())
    print(f"Wrote theta process plate to {args.output}")


if __name__ == "__main__":
    main()
