"""Render a completed audit's saved numbers; never reruns or tunes a model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def render(directory: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    protocol = json.loads((directory / "protocol.json").read_text(encoding="utf-8"))
    grids = protocol["config"]["grid_sizes"]
    v1_grids = [n for n in grids if f"N{n}/v1" in report["datasets"]]
    if not v1_grids:
        raise ValueError("This presentation needs a V1 dataset.")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    rows, gains, intervals, labels = [], [], [], []
    for n in v1_grids:
        forecast = report["datasets"][f"N{n}/v1"]["forecast"]
        for cohort, result in forecast["tracks"]["full_state_summaries"]["cohorts"].items():
            comparison = result["comparisons"]["planar_shells"]
            gain = 100 * comparison["relative_loss_reduction"]
            ci = [100 * value for value in comparison["paired_seed_bootstrap_95_interval"]]
            labels.append(f"{n}×{n}\n{cohort}")
            gains.append(gain)
            intervals.append(ci)
            rows.append(f"| {n}×{n} | {cohort} | {gain:+.2f}% | [{ci[0]:+.2f}%, {ci[1]:+.2f}%] | {comparison['seed_wins']}/{len(result['seeds'])} | {'Pass' if result['passes'] else 'Not passed'} |")
    positions = np.arange(len(labels))
    axes[0].bar(positions, gains, color=["#356f9c" if g >= 0 else "#b26048" for g in gains], width=.6)
    # Draw interval endpoints directly, including intervals that do not contain
    # the point estimate; matplotlib errorbar requires nonnegative offsets.
    for pos, (lo, hi) in zip(positions, intervals):
        axes[0].plot([pos, pos], [lo, hi], color="#252525", linewidth=1.2)
        axes[0].plot([pos - .08, pos + .08], [lo, lo], color="#252525", linewidth=1.2)
        axes[0].plot([pos - .08, pos + .08], [hi, hi], color="#252525", linewidth=1.2)
    axes[0].axhline(0, color="#777777", linewidth=.8)
    axes[0].axhline(100 * protocol["config"]["minimum_gain"], color="#777777", linestyle="--", linewidth=1, label="5% minimum gain (other gates also required)")
    axes[0].set_xticks(positions, labels)
    axes[0].set_ylabel("Held-out normalized loss reduction (%)")
    axes[0].set_title("V1 multiscale versus matched planar summaries")
    axes[0].legend(loc="lower left", fontsize=8)
    axes[0].set_xlabel("Positive values favor multiscale\nIntervals: paired seed bootstrap, 95%")
    n = max(v1_grids)
    organization = report["datasets"][f"N{n}/v1"]["organization"]
    for name, label, marker, color in (("original", "V1 snapshots", "o", "#356f9c"), ("spatial_permutation", "Spatial permutation", "s", "#b26048"), ("independent_angles", "Independent angle resampling", "^", "#6f6f6f")):
        scales = sorted(map(int, organization[name]))
        means = [organization[name][str(s)]["coherence"]["mean_across_seeds"] for s in scales]
        axes[1].plot(scales, means, marker=marker, color=color, label=label)
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(scales, [str(s) for s in scales])
    axes[1].set_xlabel("Block width (grid sites)")
    axes[1].set_ylabel("Mean block coherence |mean exp(iθ)|")
    axes[1].set_ylim(0, 1)
    axes[1].set_title(f"{n}×{n} organization across scale (descriptive)")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Classical organization audit — no bulk reconstruction", fontsize=13)
    fig.savefig(directory / "summary.png", dpi=170)
    plt.close(fig)
    lines = ["# Multiscale organization audit", "", report["claim_boundary"], "",
        f"Primary gate: **{'passed' if report['primary_gate_passes'] else 'not passed'}**. V1/V2 engine source hashes unchanged: **{report['engine_sources_unchanged']}**.", "",
        "## V1 primary comparison", "", "Positive reduction favors multiscale. Intervals are paired bootstraps of seed losses, not individual records.", "",
        "| Grid | Held-out cohort | Loss reduction vs planar | 95% interval | Seed wins | Combined cohort gate |",
        "| --- | --- | ---: | --- | ---: | --- |", *rows, "",
        "## Pipeline comparisons", "", "These comparisons are secondary. Losses are standardized within each dataset; raw normalized losses should not be compared across pipelines.", "",
        "| Dataset | Track | Test gain vs planar | Replication gain vs planar | Track gate |",
        "| --- | --- | ---: | ---: | --- |"]
    for name, result in report["datasets"].items():
        for track, values in result["forecast"]["tracks"].items():
            cohorts = values["cohorts"]
            test, replication = [100 * cohorts[c]["comparisons"]["planar_shells"]["relative_loss_reduction"] for c in ("test", "replication")]
            lines.append(f"| {name} | {track} | {test:+.2f}% | {replication:+.2f}% | {'Pass' if values['passes'] else 'Not passed'} |")
    lines += ["", "## Interpretation", "",
        "This is a test of fixed classical summary representations and a fixed ridge predictor. A failure is a limit of this protocol, not a refutation of all multiscale organization or Genesis formulations. Coherence differences from shuffled fields are expected from local alignment and do not establish holography. Even a predictive gain would not establish spatial depth.", "",
        "## Artifacts", "", "- [Protocol and source hashes](protocol.json)", "- [Complete metrics](report.json)", "- [Figure](summary.png)",
        "- Each `N<size>/<pipeline>/seed_<seed>.npz` contains input snapshots, feature arrays, event identifiers, and response targets.",
        "- Each `N<size>/<pipeline>/forecasts.npz` retains exact held-out predictions and event arrays.",
        "- Each `organization_records.json` retains descriptive block measurements and Fourier surrogate mismatch.", "",
        "## Limits recorded before collection", "", *["- " + item for item in protocol["design"]["limitations"]], ""]
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    render(args.directory)


if __name__ == "__main__":
    main()
