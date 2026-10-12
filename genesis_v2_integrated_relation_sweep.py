"""Predeclared strength sweep for the V2 integrated relation-memory link."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from genesis_v2_integrated_relation_probe import run_condition


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep relation-memory tension without adding new dynamics.")
    parser.add_argument("--N", type=int, default=64)
    parser.add_argument("--frames", type=int, default=2_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--sample-interval", type=int, default=25)
    parser.add_argument("--min-pair-age", type=int, default=100)
    parser.add_argument("--max-pair-distance", type=float, default=64.0)
    parser.add_argument("--strengths", type=float, nargs="+", default=[0.0, 0.1, 0.2, 0.4, 0.8])
    parser.add_argument("--output", type=Path, default=Path("results/v2_integrated_relation_sweep.json"))
    args = parser.parse_args()
    if args.N < 4 or args.frames < 1 or args.seeds < 1 or args.sample_interval < 1:
        raise SystemExit("--N >= 4 and --frames, --seeds, --sample-interval must be positive.")
    if any(strength < 0.0 for strength in args.strengths):
        raise SystemExit("--strengths must be non-negative.")

    conditions = []
    for strength in args.strengths:
        name = "p_to_a_bridge" if strength == 0.0 else f"relation_memory_tension_{strength:g}"
        condition = run_condition(name, args, relation_memory_tension=strength)
        condition["relation_memory_tension"] = strength
        conditions.append(condition)

    output = {
        "schema_version": 1,
        "claim_boundary": "This is a predeclared parameter sweep of one causal link, not an object claim or a search for a preferred regime.",
        "experiment": {
            "name": "v2_integrated_relation_memory_tension_sweep",
            "question": "Does any specified relation-memory strength improve persistence without P/A collapse or global ordering?",
            "grid_size": args.N,
            "frames": args.frames,
            "seeds": args.seeds,
            "strengths": args.strengths,
        },
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
