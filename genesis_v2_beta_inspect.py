"""Visual inspection of the distinction-preserving v2-beta regime."""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np

from src.genesis_grid.backend import to_cpu
from src.genesis_v2_beta import BetaParams, BetaState, step, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a v2-beta field without claiming objects.")
    parser.add_argument("--N", type=int, default=128)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--potential-to-actual", type=float, default=0.05)
    parser.add_argument("--relation-difference-gain", type=float, default=0.55)
    args = parser.parse_args()

    state = BetaState(args.N, seed=args.seed)
    params = BetaParams(potential_to_actual=args.potential_to_actual, relation_difference_gain=args.relation_difference_gain)
    history = []
    history_interval = max(1, args.frames // 100)
    for frame in range(1, args.frames + 1):
        step(state, params)
        if frame % history_interval == 0 or frame == args.frames:
            history.append({"frame": frame, **summary(state)})

    theta = np.asarray(to_cpu(state.theta))
    p_angle = np.arctan2(np.asarray(to_cpu(state.py)), np.asarray(to_cpu(state.px)))
    availability = np.asarray(to_cpu(state.availability))
    difference = np.abs(np.arctan2(np.sin(theta - p_angle), np.cos(theta - p_angle)))

    figure, axes = plt.subplots(2, 3, figsize=(14, 9), constrained_layout=True)
    panels = ((theta, "Actuality A (orientation)", "twilight", 0, 2 * np.pi), (p_angle % (2 * np.pi), "Potentiality P (latent direction)", "twilight", 0, 2 * np.pi), (availability, "Potential availability", "viridis", 0, 1), (difference, "P/A angular difference", "magma", 0, np.pi))
    for axis, (field, title, cmap, low, high) in zip(axes.flat[:4], panels):
        image = axis.imshow(field, cmap=cmap, vmin=low, vmax=high, interpolation="nearest")
        axis.set_title(title)
        axis.set_xticks([])
        axis.set_yticks([])
        figure.colorbar(image, ax=axis, shrink=0.82)
    frames = [row["frame"] for row in history]
    dynamics = axes.flat[4]
    dynamics.plot(frames, [row["potential_actual_alignment"] for row in history], label="P/A alignment")
    dynamics.plot(frames, [row["availability_std"] for row in history], label="availability variation")
    dynamics.set_title("Distinction Over Time")
    dynamics.set_xlabel("frame")
    dynamics.set_ylim(0, 1)
    dynamics.legend(fontsize=8)
    structure = axes.flat[5]
    structure.plot(frames, [row["actual_order"] for row in history], label="global order")
    structure.plot(frames, [row["relation_mean"] for row in history], label="relation strength")
    structure.set_title("Global State Over Time")
    structure.set_xlabel("frame")
    structure.set_ylim(0, 1)
    structure.legend(fontsize=8)
    figure.suptitle(f"Genesis v2-beta inspector | seed={args.seed}, frames={args.frames}, P->A={args.potential_to_actual}, relation={args.relation_difference_gain}")
    plt.show()


if __name__ == "__main__":
    main()
