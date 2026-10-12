"""Render the second layperson visual: vortex, region, and object are distinct."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, FancyArrowPatch


BG = "#10151c"
INK = "#f1ede3"
MUTED = "#aab5c0"
GRID = "#283542"
BOUNDARY = "#e7c46a"
RELATION = "#55c7b5"
WARNING = "#ca6276"


def draw_dashes(axis, theta: np.ndarray, length: float = 0.31, color: str = INK, alpha: float = 1.0) -> None:
    rows, columns = theta.shape
    y, x = np.mgrid[0:rows, 0:columns]
    dx, dy = length * np.cos(theta), length * np.sin(theta)
    segments = np.stack((np.stack((x - dx, y - dy), axis=-1), np.stack((x + dx, y + dy), axis=-1)), axis=2).reshape(-1, 2, 2)
    axis.add_collection(LineCollection(segments, colors=color, linewidths=2.0, alpha=alpha, capstyle="round"))


def clean(axis, width=10, height=10) -> None:
    axis.set_facecolor(BG)
    axis.set_xlim(-0.8, width - 0.2); axis.set_ylim(height - 0.2, -0.8)
    axis.set_aspect("equal"); axis.set_xticks([]); axis.set_yticks([])
    for spine in axis.spines.values(): spine.set_visible(False)


def panel_title(axis, number: str, title: str, subtitle: str) -> None:
    axis.text(0.0, 1.12, number, transform=axis.transAxes, color=BOUNDARY, fontsize=11, fontweight="bold")
    axis.text(0.0, 1.03, title, transform=axis.transAxes, color=INK, fontsize=16, fontweight="bold")
    axis.text(0.0, 0.92, subtitle, transform=axis.transAxes, color=MUTED, fontsize=10, linespacing=1.3)


def main() -> None:
    output = Path("findings/figures/2026-10-11_structure_ladder.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 3, figsize=(16, 7), facecolor=BG)
    figure.subplots_adjust(left=0.055, right=0.975, bottom=0.16, top=0.72, wspace=0.20)
    figure.text(0.055, 0.935, "A pattern is not yet an object", color=INK, fontsize=23, fontweight="bold")
    figure.text(0.055, 0.885, "The same dash field can exhibit geometry, relation, and individuation. These must not be conflated.", color=MUTED, fontsize=12)
    rng = np.random.default_rng(8)

    # Vortex: a winding pattern in theta alone.
    vortex = axes[0]; clean(vortex)
    y, x = np.mgrid[0:10, 0:10]
    theta = np.arctan2(y - 4.5, x - 4.5) + np.pi / 2
    draw_dashes(vortex, theta)
    vortex.add_patch(Circle((4.5, 4.5), 0.28, color=BOUNDARY, alpha=0.95))
    vortex.add_patch(FancyArrowPatch((1.4, 4.5), (2.4, 2.2), connectionstyle="arc3,rad=-0.42", arrowstyle="-|>", mutation_scale=14, color=BOUNDARY, linewidth=1.6))
    vortex.text(4.5, 8.8, "dashes turn\naround a center", color=INK, fontsize=10, ha="center", fontweight="bold")
    panel_title(vortex, "01", "A vortex", "A geometric winding in theta.\nIt does not imply a boundary or persistence.")

    # Region: connected inside, weakened relational edge around it.
    region = axes[1]; clean(region)
    region_theta = rng.uniform(0.0, 2.0 * np.pi, size=(10, 10))
    inside = (x - 4.5) ** 2 + (y - 4.5) ** 2 < 11.0
    region_theta[inside] = 0.1 + 0.18 * np.sin(y[inside])
    draw_dashes(region, region_theta)
    region.contour(inside, levels=[0.5], colors=BOUNDARY, linestyles="--", linewidths=2.2)
    for row in range(3, 7):
        region.plot([2.9, 6.1], [row, row], color=RELATION, linewidth=1.1, alpha=0.65)
    region.text(4.5, 4.4, "stronger\ninternal relation", color=RELATION, fontsize=10, ha="center", va="center", fontweight="bold")
    panel_title(region, "02", "A candidate region", "A patch defined by relations: connected inside,\nweakened across its perimeter.")

    # Object: the same bounded identity must survive time and disturbance.
    obj = axes[2]; clean(obj, 13, 10)
    centers = ((2.2, 5.0), (6.2, 4.9), (10.2, 5.1))
    labels = ("time 1", "after change", "later")
    for index, ((center_x, center_y), caption) in enumerate(zip(centers, labels)):
        obj.add_patch(Circle((center_x, center_y), 1.45, fill=False, edgecolor=BOUNDARY, linewidth=2.0, linestyle="--"))
        for angle in np.linspace(0.0, 2.0 * np.pi, 8, endpoint=False):
            px, py = center_x + 0.72 * np.cos(angle), center_y + 0.72 * np.sin(angle)
            obj.plot([px - 0.24 * np.cos(angle), px + 0.24 * np.cos(angle)], [py - 0.24 * np.sin(angle), py + 0.24 * np.sin(angle)], color=INK, linewidth=2.0, solid_capstyle="round")
        obj.text(center_x, 7.35, caption, color=MUTED, fontsize=9.5, ha="center")
        if index < 2:
            obj.add_patch(FancyArrowPatch((center_x + 1.55, center_y), (centers[index + 1][0] - 1.55, centers[index + 1][1]), arrowstyle="-|>", mutation_scale=13, color=RELATION, linewidth=1.8))
    obj.text(6.2, 1.05, "same bounded organization\nthrough change", color=RELATION, fontsize=10.5, ha="center", fontweight="bold")
    obj.text(6.2, 8.7, "must remain finite, organized,\nand recoverable", color=INK, fontsize=10, ha="center")
    panel_title(obj, "03", "A higher-level object", "A candidate region that keeps its identity\nthrough time and disturbance.")

    figure.text(0.055, 0.055, "Genesis v2 has shown temporary relation-bounded candidate regions. It has not yet shown the third panel: stable bounded individuation.", color=INK, fontsize=11)
    figure.savefig(output, dpi=180, facecolor=BG)
    print(f"Wrote structure ladder to {output}")


if __name__ == "__main__":
    main()
