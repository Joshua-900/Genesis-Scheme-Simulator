"""Verify a closed audit's fingerprint without rerunning its experiments."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform


ROOT = Path(__file__).resolve().parents[2]


def verify(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changes = []
    for group in ("source_sha256", "evidence_sha256"):
        for name, expected in manifest[group].items():
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT):
                raise ValueError(f"Manifest path escapes repository: {name}")
            if not path.is_file():
                changes.append({"group": group, "path": name, "status": "missing"})
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                changes.append({"group": group, "path": name, "status": "changed"})
    paths = list((ROOT / "src/genesis_grid").rglob("*.py"))
    for directory in (ROOT / "src").glob("genesis_v2*"):
        paths.extend(directory.rglob("*.py"))
    for path in paths:
        name = path.relative_to(ROOT).as_posix()
        if name not in manifest["source_sha256"]:
            changes.append({"group": "source_sha256", "path": name, "status": "new_engine_source"})
    current = {"python": platform.python_version(), "numpy": version("numpy"), "scipy": version("scipy")}
    environment = {k: {"audited": manifest["environment"][k], "current": v} for k, v in current.items() if manifest["environment"][k] != v}
    return {"audit_id": manifest["audit_id"], "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "fingerprints_match": not changes, "environment_matches": not environment, "changes": changes, "environment_differences": environment,
        "meaning": "Unchanged reviewed inputs inherit only this audit's stated coverage. New evidence of a defect can reopen a specific claim; a fingerprint is not a proof of scientific completeness."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    result = verify(args.manifest)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["fingerprints_match"] and result["environment_matches"] else 1)


if __name__ == "__main__":
    main()
