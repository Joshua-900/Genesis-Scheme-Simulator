"""Render saved vortex encounters and evaluation; does not simulate or train."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from .experiment import BRANCHES
from .observations import delta


def render(directory: Path, make_movie: bool = True):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    protocol = json.loads((directory / "protocol.json").read_text(encoding="utf-8"))
    config = protocol["config"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), layout="constrained")
    cohorts = [(name, c['motion']) for name, c in report['forecast']['cohorts'].items() if c['motion']['status'] == 'evaluated']
    if cohorts:
        styles = (("persistence", "No movement", "#777777"), ("kinematic", "Kinematic", "#4c8a68"),
            ("field_matched", "Matched field", "#b46b45"), ("structural", "Structural", "#80639d"), ("shuffled_structure", "Shuffled structure", "#387ba0"))
        positions = np.arange(len(cohorts))
        for index, (model, label, color) in enumerate(styles):
            axes[0].bar(positions + (index - 2) * .145, [task['mean_loss'][model] for _, task in cohorts], width=.135, color=color, label=label)
        axes[0].set_xticks(positions, [name for name, _ in cohorts])
        axes[0].legend(fontsize=8, ncol=2)
    else:
        axes[0].text(.5, .5, "Insufficient motion coverage", ha="center", transform=axes[0].transAxes)
    axes[0].set_ylabel("Motion MSE (grid sites²; lower is better)")
    axes[0].set_title("All motion baselines (strict survivors)")
    axes[0].set_xlabel("Independent held-out cohorts; full gate not passed" if not report['forecast']['gate_passes'] else "Independent held-out cohorts; full gate passed")
    counts = [[s["branches"][b]["pair_observed_samples_after_start"] for s in report["seeds"]] for b in BRANCHES]
    axes[1].boxplot(counts, tick_labels=["Untouched", "Selected reset", "Background reset"], showfliers=True)
    axes[1].set_ylabel("Strict pair-observed samples")
    axes[1].set_title("Observed continuation after structural reset")
    axes[1].tick_params(axis="x", rotation=12)
    fig.suptitle("V1 vortex motion — fixed discrete updates", fontsize=13)
    fig.savefig(directory / "summary.png", dpi=165)
    plt.close(fig)

    seed = report["visual_seed"]
    if seed is not None:
        data = np.load(directory / f"seed_{seed}.npz")
        selected = next(s for s in report["seeds"] if s["seed"] == seed)
        n = config["n"]
        center = np.rint(selected["midpoint"]).astype(int)
        half = 12
        x = (np.arange(-half, half + 1) + center[0]) % n
        y = (np.arange(-half, half + 1) + center[1]) % n
        times = np.arange(data["untouched_positions"].shape[0]) * config["interval"]
        fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.3), layout="constrained")
        axes = np.asarray(axes)
        titles = ("Untouched", "Selected structural reset", "Distant structural reset")
        extent = [-half - .5, half + .5, -half - .5, half + .5]

        def draw(index):
            for axis, name, title in zip(axes, BRANCHES, titles):
                axis.clear()
                theta = data[f"{name}_theta"][index][np.ix_(y, x)]
                compression = data[f"{name}_C"][index][np.ix_(y, x)]
                axis.imshow(theta, origin="lower", extent=extent, cmap="twilight", vmin=0, vmax=2 * np.pi)
                yy, xx = np.mgrid[-half:half + 1, -half:half + 1]
                axis.quiver(xx[::3, ::3], yy[::3, ::3], np.cos(theta)[::3, ::3], np.sin(theta)[::3, ::3], color="#202020", pivot="mid", scale=20, width=.004)
                for level in (.1, .5):
                    if compression.min() < level < compression.max():
                        axis.contour(xx, yy, compression, levels=[level], colors=["white"], linewidths=.65)
                positions = delta(data[f"{name}_positions"][:index + 1], center, n)
                for slot, marker in ((0, "+"), (1, "x")):
                    trail = positions[:, slot]
                    axis.plot(trail[:, 0], trail[:, 1], color="#111111", linewidth=1.3)
                    if np.isfinite(trail[-1]).all():
                        axis.scatter(*trail[-1], marker=marker, s=95, color="#111111", linewidths=2)
                if name == "selected_structure":
                    from matplotlib.patches import Circle
                    relative = delta(np.asarray(selected["midpoint"]), center, n)
                    axis.add_patch(Circle(relative, config["radius"], fill=False, edgecolor="#111111", linestyle="--", linewidth=1))
                axis.set(xlim=extent[:2], ylim=extent[2:], xlabel="x offset (grid sites)", ylabel="y offset (grid sites)", title=title, aspect="equal")
            fig.suptitle(f"Seed {seed} · update +{times[index]} · θ color, arrows; white contours C=0.1/0.5", fontsize=11)
            fig.supxlabel("Same initial θ in all arms · + / ×: selected opposite winding identities · missing marker: track no longer observed", fontsize=9)
            return []

        draw(0)
        fig.savefig(directory / "encounter_start.png", dpi=150)
        draw(min(config["horizon"] // config["interval"], len(times) - 1))
        fig.savefig(directory / "encounter_horizon.png", dpi=150)
        if make_movie:
            animation = FuncAnimation(fig, draw, frames=len(times), interval=100, blit=False)
            animation.save(directory / "encounter.gif", writer=PillowWriter(fps=10), dpi=95)
        plt.close(fig)
        data.close()

    lines = ["# V1 vortex motion and structural-state encounter", "", report["claim_boundary"], "",
        f"Eligible seeds: **{report['selection_coverage']}**. Forecast records: **{report['forecast_records']}**. V1/V2 sources unchanged: **{report['source_and_baseline_unchanged']}**.", "",
        f"Motion gate: **{'passed' if report['forecast']['gate_passes'] else 'not passed'}**. Strict-continuation secondary gate: **{'passed' if report['forecast']['continuation_gate_passes'] else 'not passed'}**.", "",
        "The structural model must beat every declared comparator. A large gain against a poor field model alone is insufficient; inspect the no-movement and shuffled-structure references too.", "",
        "| Cohort | Target | Comparator | Loss reduction | 95% seed interval | Seed wins | Comparator gate |", "| --- | --- | --- | ---: | --- | ---: | --- |"]
    for name, c in report["forecast"]["cohorts"].items():
        for target, task in c.items():
            if task["status"] != "evaluated":
                lines.append(f"| {name} | {target} | — | Insufficient coverage | — | — | Not passed |")
                continue
            for reference, comparison in task['comparisons'].items():
                gain = comparison["relative_gain"]
                interval = comparison["interval"]
                formatted_gain = f"{100 * gain:+.2f}%" if gain is not None else "Undefined"
                formatted_interval = f"[{100 * interval[0]:+.2f}%, {100 * interval[1]:+.2f}%]" if interval else "—"
                lines.append(f"| {name} | {target} | {reference} | {formatted_gain} | {formatted_interval} | {comparison['wins']}/{len(task['seeds'])} | {'Passed' if comparison['passes'] else 'Not passed'} |")
    contrast = report["conditional_motion_contrast"]
    lines += ["", "## Conditional motion contrast", "", json.dumps(contrast, indent=2), "", "## Visual replay", "",
        f"Representative seed: {seed}, selected before inspecting future results. Spatial crop around the selected pair; the background intervention is outside this crop.", "",
        "![Encounter at forecast horizon](encounter_horizon.png)", "", "[Animated encounter](encounter.gif)", "", "![Forecast and continuation summary](summary.png)", "",
        "## Artifacts", "", "- [Frozen protocol](protocol.json)", "- [All metrics](report.json)", "- `forecasts.npz`: event inputs, targets and exact held-out predictions.",
        "- `seed_<seed>.npz`: initial full state, target trajectories, and representative fields for the visual seed.", "", "## Limits", "", *["- " + text for text in protocol["limits"]], ""]
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    presentation = {'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'report_sha256': hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        'purpose': 'Presentation includes all gate comparators; no data, fit, protocol, metric or threshold changed.'}
    (directory/'presentation.json').write_text(json.dumps(presentation, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--no-movie", action="store_true")
    args = parser.parse_args()
    render(args.directory, not args.no_movie)


if __name__ == "__main__":
    main()
