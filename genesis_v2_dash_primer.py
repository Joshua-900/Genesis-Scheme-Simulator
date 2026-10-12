"""Render the first layperson visual: dash, relation, and candidate region."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle


INK = "#f1ede3"
BG = "#10151c"
GRID = "#283542"
STRONG = "#55c7b5"
WEAK = "#ca6276"
BOUNDARY = "#e7c46a"
MUTED = "#aab5c0"


def draw_dashes(axis, theta: np.ndarray, length: float = 0.33, color: str = INK, alpha: float = 1.0) -> None:
    rows, columns = theta.shape
    y, x = np.mgrid[0:rows, 0:columns]
    dx, dy = length * np.cos(theta), length * np.sin(theta)
    segments = np.stack((np.stack((x - dx, y - dy), axis=-1), np.stack((x + dx, y + dy), axis=-1)), axis=2).reshape(-1, 2, 2)
    axis.add_collection(LineCollection(segments, colors=color, linewidths=2.0, alpha=alpha, capstyle="round"))


def clean(axis, width: int, height: int) -> None:
    axis.set_facecolor(BG)
    axis.set_xlim(-0.8, width - 0.2)
    axis.set_ylim(height - 0.2, -0.8)
    axis.set_aspect("equal")
    axis.set_xticks([]); axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_visible(False)


def heading(axis, number: str, title: str, subtitle: str) -> None:
    axis.text(0.0, 1.11, number, transform=axis.transAxes, color=BOUNDARY, fontsize=11, fontweight="bold")
    axis.text(0.0, 1.02, title, transform=axis.transAxes, color=INK, fontsize=16, fontweight="bold")
    axis.text(0.0, 0.91, subtitle, transform=axis.transAxes, color=MUTED, fontsize=10, linespacing=1.3)


def main() -> None:
    output = Path("findings/figures/2026-10-11_dash_primer.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 3, figsize=(16, 6.8), facecolor=BG)
    figure.subplots_adjust(left=0.055, right=0.975, bottom=0.16, top=0.74, wspace=0.20)
    figure.text(0.055, 0.935, "Genesis v2, starting at the smallest unit", color=INK, fontsize=23, fontweight="bold")
    figure.text(0.055, 0.885, "A dash is an oriented local state. Regions arise from the relations between neighboring dashes.", color=MUTED, fontsize=12)

    # 1. One dash at each location is an orientation, not a moving object.
    rng = np.random.default_rng(4)
    theta = rng.uniform(0.0, 2.0 * np.pi, size=(8, 8))
    clean(axes[0], 8, 8)
    for line in range(9):
        axes[0].axhline(line - 0.5, color=GRID, linewidth=0.7)
        axes[0].axvline(line - 0.5, color=GRID, linewidth=0.7)
    draw_dashes(axes[0], theta)
    axes[0].add_patch(Circle((3.0, 3.0), 0.55, fill=False, edgecolor=BOUNDARY, linewidth=1.8))
    axes[0].annotate("one local\norientation", xy=(3.0, 3.0), xytext=(5.1, 1.0), color=INK, fontsize=10, arrowprops={"arrowstyle": "-", "color": BOUNDARY, "lw": 1.5})
    heading(axes[0], "01", "What a dash means", "Each location carries a direction: theta.\nIt is not a particle moving through space.")

    # 2. Relation is strong for compatible neighbors and weak for conflict.
    clean(axes[1], 8, 8)
    pair_theta = np.full((8, 8), np.pi / 4)
    pair_theta[:, 4:] = -np.pi / 4
    pair_theta[2:5, 2:4] = np.pi / 4 + 0.1
    draw_dashes(axes[1], pair_theta)
    axes[1].plot([1.2, 2.8], [2.0, 2.0], color=STRONG, linewidth=4.5, solid_capstyle="round")
    axes[1].text(0.2, 1.2, "similar directions\nstrong relation", color=STRONG, fontsize=10, fontweight="bold")
    axes[1].plot([3.2, 4.8], [5.3, 5.3], color=WEAK, linewidth=2.0, linestyle=(0, (2, 2)))
    axes[1].text(4.0, 6.5, "conflicting directions\nweak relation", color=WEAK, fontsize=10, fontweight="bold", ha="center")
    heading(axes[1], "02", "What the field is doing", "Neighboring orientations affect their relation.\nCompatibility connects; conflict weakens connection.")

    # 3. Strongly connected dashes are an observer-defined candidate region.
    clean(axes[2], 8, 8)
    y, x = np.mgrid[0:8, 0:8]
    inside = (x - 3.5) ** 2 + (y - 3.5) ** 2 < 7.0
    region_theta = rng.uniform(0.0, 2.0 * np.pi, size=(8, 8))
    region_theta[inside] = 0.2 + 0.16 * np.sin(y[inside])
    draw_dashes(axes[2], region_theta, alpha=0.92)
    axes[2].contour(inside, levels=[0.5], colors=BOUNDARY, linestyles="--", linewidths=2.2)
    axes[2].text(3.5, 3.4, "internally\nconnected", color=INK, fontsize=10, ha="center", va="center", fontweight="bold")
    axes[2].annotate("measured relation boundary", xy=(5.6, 2.0), xytext=(4.3, 0.4), color=BOUNDARY, fontsize=10, arrowprops={"arrowstyle": "-", "color": BOUNDARY, "lw": 1.5})
    heading(axes[2], "03", "How a candidate region appears", "The detector follows strong relations until they weaken.\nThe dashed perimeter is found, not inserted.")

    figure.text(0.055, 0.055, "A higher-level object would be a candidate region that remains bounded, organized, and recoverable through time. Current v2 regions are candidates; they usually merge instead.", color=INK, fontsize=11)
    figure.savefig(output, dpi=180, facecolor=BG)
    print(f"Wrote dash primer to {output}")


if __name__ == "__main__":
    main()
