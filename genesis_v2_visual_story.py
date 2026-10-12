"""Render a field-first visual story of the current Genesis v2 research arc."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, FancyArrowPatch

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta.objects import detect_relation_domains
from src.genesis_v2_zeta import ZetaParams, ZetaState, step


BG, INK, MUTED, GOLD, TEAL, ORANGE, PINK, WARNING = "#10151c", "#f1ede3", "#aab5c0", "#e7c46a", "#55c7b5", "#e38c39", "#dd6e9f", "#ca6276"


def run_to(frames: int, N: int, seed: int) -> ZetaState:
    state = ZetaState(N, seed=seed)
    params = ZetaParams(potential_to_actual=0.05, relation_difference_gain=0.55, refractory_production=0.020, refractory_alignment_gain=0.90)
    for _ in range(frames): step(state, params)
    return state


def field(axis, state: ZetaState, cutoff: float = 0.75, min_area: int = 24) -> None:
    theta = np.asarray(to_cpu(state.theta))
    axis.imshow(theta, cmap="twilight", vmin=0, vmax=2 * np.pi, interpolation="nearest")
    yy, xx = np.mgrid[2:theta.shape[0]:6, 2:theta.shape[1]:6]
    angle = theta[2::6, 2::6]
    axis.quiver(xx, yy, np.cos(angle), np.sin(angle), color=INK, pivot="mid", scale=16, width=0.005, headwidth=3.1, alpha=0.88)
    for domain in detect_relation_domains(state, cutoff, min_area):
        axis.contour(domain.mask, levels=[0.5], colors=GOLD, linestyles="--", linewidths=1.5)
    axis.set_xticks([]); axis.set_yticks([])
    for spine in axis.spines.values(): spine.set_edgecolor("#384653")


def clean(axis) -> None:
    axis.set_facecolor(BG); axis.set_xticks([]); axis.set_yticks([])
    for spine in axis.spines.values(): spine.set_visible(False)


def mini_object(axis, stage: int) -> None:
    clean(axis)
    axis.set_xlim(0, 10); axis.set_ylim(0, 10); axis.set_aspect("equal")
    center = (5.0 + (0.4 if stage == 1 else 0.0), 5.0)
    radius = 2.5
    axis.add_patch(Circle(center, radius, fill=False, edgecolor=GOLD, linewidth=2.1, linestyle="--"))
    angles = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    for angle in angles:
        x, y = center[0] + 1.35 * np.cos(angle), center[1] + 1.35 * np.sin(angle)
        axis.plot([x - .32 * np.cos(angle), x + .32 * np.cos(angle)], [y - .32 * np.sin(angle), y + .32 * np.sin(angle)], color=INK, linewidth=2.1, solid_capstyle="round")
    if stage == 1:
        axis.add_patch(FancyArrowPatch((0.8, 5), (2.6, 5), arrowstyle="-|>", mutation_scale=15, color=PINK, linewidth=2.0))
    if stage == 2:
        axis.add_patch(Circle(center, 1.4, fill=True, color=TEAL, alpha=.14))


def main() -> None:
    output = Path("findings/figures/2026-10-11_v2_visual_story.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    zero, early, late = (run_to(frame, 64, 1) for frame in (0, 2_000, 8_000))
    figure = plt.figure(figsize=(16, 10), facecolor=BG)
    grid = figure.add_gridspec(2, 7, left=.055, right=.97, top=.82, bottom=.11, wspace=.28, hspace=.43, width_ratios=(1, .16, 1, .16, 1, .86, .86))
    figure.text(.055, .93, "Genesis v2: from a dash field to the search for an individual", color=INK, fontsize=23, fontweight="bold")
    figure.text(.055, .885, "White dashes are local orientation. Gold dashed contours are measured relation boundaries.", color=MUTED, fontsize=11.5)

    # The observed story.
    current_axes = [figure.add_subplot(grid[0, column]) for column in (0, 2, 4)]
    for axis, state in zip(current_axes, (zero, early, late)): field(axis, state)
    captions = (("1. Field", "local orientations"), ("2. Regions appear", "plural dashed boundaries"), ("3. Current outcome", "boundaries merge"))
    for axis, (title, subtitle) in zip(current_axes, captions):
        axis.text(.5, -0.12, title, transform=axis.transAxes, color=INK, fontsize=12.5, ha="center", fontweight="bold")
        axis.text(.5, -0.22, subtitle, transform=axis.transAxes, color=MUTED, fontsize=9.5, ha="center")
    for column in (1, 3):
        arrow_axis = figure.add_subplot(grid[0, column]); clean(arrow_axis)
        arrow_axis.add_patch(FancyArrowPatch((.05, .5), (.95, .5), transform=arrow_axis.transAxes, arrowstyle="simple", mutation_scale=23, color=GOLD, alpha=.85))

    lever = figure.add_subplot(grid[0, 5:]); clean(lever)
    lever.set_xlim(0, 1); lever.set_ylim(0, 1)
    lever.text(.05, .88, "WHAT WE TRIED", color=INK, fontsize=12.5, fontweight="bold")
    for y, color, name, phrase in ((.66, ORANGE, "DELTA", "broad-scale brake"), (.46, PINK, "EPSILON", "resource renewal"), (.26, TEAL, "ZETA", "refractory brake")):
        lever.plot([.06, .20], [y, y], color=color, linewidth=5, solid_capstyle="round")
        lever.text(.27, y+.02, name, color=INK, fontsize=11, fontweight="bold", va="center")
        lever.text(.27, y-.10, phrase, color=MUTED, fontsize=9.5, va="center")
    lever.text(.05, .06, "Each prolonged plurality.\nNone stopped merger.", color=INK, fontsize=10.5, linespacing=1.35)

    # The target story: no claim this is yet achieved.
    question = figure.add_subplot(grid[1, 0:5]); clean(question)
    question.text(.0, 1.04, "THE OBJECT TEST", transform=question.transAxes, color=INK, fontsize=13, fontweight="bold")
    question.text(.0, .94, "A higher-level object is not merely a pattern. Its boundary stays finite and organized through change.", transform=question.transAxes, color=MUTED, fontsize=10.5)
    question.set_xlim(0, 1); question.set_ylim(0, 1)
    mini_positions = (.13, .47, .81)
    labels = (("formed", "a bounded region"), ("disturbed", "change without dissolution"), ("still itself", "organized later"))
    for index, (x, (title, subtitle)) in enumerate(zip(mini_positions, labels)):
        inset = question.inset_axes((x - .105, .13, .21, .65))
        mini_object(inset, index)
        question.text(x, .04, title, transform=question.transAxes, color=INK, fontsize=11, ha="center", fontweight="bold")
        question.text(x, -.055, subtitle, transform=question.transAxes, color=MUTED, fontsize=9, ha="center")
        if index < 2:
            question.add_patch(FancyArrowPatch((x+.115, .45), (mini_positions[index+1]-.115, .45), transform=question.transAxes, arrowstyle="-|>", mutation_scale=15, color=TEAL, linewidth=1.8))

    verdict = figure.add_subplot(grid[1, 5:]); clean(verdict)
    verdict.text(.05, .86, "WHERE WE ARE", color=INK, fontsize=13, fontweight="bold")
    verdict.text(.05, .64, "We have reached\n‘regions appear.’", color=INK, fontsize=15, fontweight="bold", linespacing=1.25)
    verdict.text(.05, .38, "We have not reached\n‘regions remain themselves.’", color=WARNING, fontsize=13, fontweight="bold", linespacing=1.3)
    verdict.text(.05, .12, "That gap is the research problem.", color=MUTED, fontsize=10)

    figure.savefig(output, dpi=180, facecolor=BG)
    print(f"Wrote visual story to {output}")


if __name__ == "__main__": main()
