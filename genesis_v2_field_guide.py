"""Render an explanatory, data-grounded visual guide to Genesis v2 levers."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

from src.genesis_grid.backend import to_cpu, xp
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_delta import DeltaParams, DeltaState, step as delta_step
from src.genesis_v2_epsilon import EpsilonParams, EpsilonState, step as epsilon_step
from src.genesis_v2_zeta import ZetaParams, ZetaState, step as zeta_step


def advance(state, params, step, frames: int):
    for _ in range(frames):
        step(state, params)
    return state


def fields(state, cutoff: float, min_area: int) -> dict:
    domains = detect_relation_domains(state, cutoff, min_area)
    return {
        "theta": np.asarray(to_cpu(state.theta)),
        "availability": np.asarray(to_cpu(state.availability)),
        "permeability": 0.5 * (np.asarray(to_cpu(state.rx)) + np.asarray(to_cpu(state.ry))),
        "domains": domains,
    }


def draw_theta(axis, field: dict, title: str, arrows: bool = True) -> None:
    theta = field["theta"]
    axis.imshow(theta, cmap="twilight", vmin=0.0, vmax=2.0 * np.pi, interpolation="nearest")
    if arrows:
        y, x = np.mgrid[2:theta.shape[0]:5, 2:theta.shape[1]:5]
        angles = theta[2::5, 2::5]
        axis.quiver(x, y, np.cos(angles), np.sin(angles), color="white", pivot="mid", scale=16, width=0.004, headwidth=3.5, alpha=0.75)
    for domain in field["domains"]:
        axis.contour(domain.mask, levels=[0.5], colors="#161616", linestyles="--", linewidths=1.1)
    axis.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=10)
    axis.set_xticks([]); axis.set_yticks([])


def add_note(axis, title: str, body: str, color: str) -> None:
    axis.set_facecolor("#f6f4ef")
    axis.spines[:].set_visible(False)
    axis.set_xticks([]); axis.set_yticks([])
    axis.plot([0.04, 0.18], [0.86, 0.86], color=color, linewidth=6, solid_capstyle="round", transform=axis.transAxes)
    axis.text(0.04, 0.73, title, transform=axis.transAxes, fontsize=14, fontweight="bold", color="#202020", va="top")
    axis.text(0.04, 0.59, "\n".join(textwrap.wrap(body, width=34)), transform=axis.transAxes, fontsize=10.2, color="#3d3d3d", va="top", linespacing=1.45)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the Genesis v2 visual field guide.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--cutoff", type=float, default=0.75)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--output", type=Path, default=Path("findings/figures/2026-10-11_v2_field_guide.png"))
    args = parser.parse_args()

    delta = advance(DeltaState(args.N, seed=args.seed), DeltaParams(potential_to_actual=0.05, relation_difference_gain=0.55, long_range_passes=4, long_range_counter_gain=0.03), delta_step, args.frames)
    epsilon = advance(EpsilonState(args.N, seed=args.seed), EpsilonParams(potential_to_actual=0.05, relation_difference_gain=0.55, availability_replenish=0.035, coherence_depletion=0.03), epsilon_step, args.frames)
    zeta = advance(ZetaState(args.N, seed=args.seed), ZetaParams(potential_to_actual=0.05, relation_difference_gain=0.55, refractory_production=0.020, refractory_alignment_gain=0.90), zeta_step, args.frames)
    later = advance(ZetaState(args.N, seed=args.seed), ZetaParams(potential_to_actual=0.05, relation_difference_gain=0.55, refractory_production=0.020, refractory_alignment_gain=0.90), zeta_step, 8_000)
    delta_field, epsilon_field, zeta_field, late_field = (fields(state, args.cutoff, args.min_area) for state in (delta, epsilon, zeta, later))

    figure = plt.figure(figsize=(16, 12), facecolor="#f6f4ef")
    grid = figure.add_gridspec(
        3, 4,
        height_ratios=(0.18, 1.0, 0.88),
        width_ratios=(1.05, 1.05, 1.05, 0.93),
        left=0.055, right=0.975, top=0.94, bottom=0.065,
        wspace=0.32, hspace=0.48,
    )
    heading = figure.add_subplot(grid[0, :])
    heading.axis("off")
    heading.text(0.0, 0.70, "Genesis v2: how we are trying to make a field become an individual", fontsize=21, fontweight="bold", color="#1e1e1e")
    heading.text(0.0, 0.15, "Every panel uses the same seed at frame 2,000. Hue and arrows show realized orientation; dashed lines are measured relation boundaries, not assumed walls.", fontsize=10.5, color="#505050")

    main_axis = figure.add_subplot(grid[1, :2])
    draw_theta(main_axis, zeta_field, "Theta + dashes: plural candidates at frame 2,000")
    main_axis.annotate("A candidate region is a measured pocket of relative internal connection", xy=(36, 35), xytext=(5, 57), fontsize=9.5, color="#161616", arrowprops={"arrowstyle": "->", "color": "#161616", "lw": 1.1}, bbox={"boxstyle": "round,pad=0.3", "fc": "#f6f4ef", "ec": "#161616", "alpha": 0.90})

    delta_axis = figure.add_subplot(grid[1, 2])
    draw_theta(delta_axis, delta_field, "Delta: broad-scale brake", arrows=False)
    delta_axis.add_patch(FancyArrowPatch((7, 50), (54, 16), connectionstyle="arc3,rad=-0.35", arrowstyle="simple", mutation_scale=20, color="#d08138", alpha=0.72))

    epsilon_axis = figure.add_subplot(grid[1, 3])
    epsilon_axis.imshow(epsilon_field["availability"], cmap="magma", vmin=0.0, vmax=0.5, interpolation="nearest")
    epsilon_axis.set_title("Epsilon: resource renewal", loc="left", fontsize=13, fontweight="bold", pad=10)
    epsilon_axis.set_xticks([]); epsilon_axis.set_yticks([])

    zeta_axis = figure.add_subplot(grid[2, 2])
    image = zeta_axis.imshow(np.asarray(to_cpu(zeta.refractory)), cmap="cividis", vmin=0.0, vmax=0.65, interpolation="nearest")
    zeta_axis.set_title("Zeta: refractory brake", loc="left", fontsize=13, fontweight="bold", pad=10)
    zeta_axis.set_xticks([]); zeta_axis.set_yticks([])
    figure.colorbar(image, ax=zeta_axis, shrink=0.68, label="refractory pressure")

    result_axis = figure.add_subplot(grid[2, 3])
    draw_theta(result_axis, late_field, "Zeta at 8,000: one region", arrows=True)

    add_note(figure.add_subplot(grid[2, 0]), "What would count as success", "The dashes would remain plural, mobile, and bounded through time. A region could transform or recover without merging into the entire field. We have not shown that yet.", "#197278")
    add_note(figure.add_subplot(grid[2, 1]), "What we have learned", "Delta, epsilon, and zeta each change the tempo of merger. None has changed the deeper tendency of this model family to relax toward one large coherent region.", "#c44536")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180, facecolor=figure.get_facecolor())
    print(f"Wrote v2 field guide to {args.output}")


if __name__ == "__main__":
    main()
