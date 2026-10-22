"""Update the skill's benchmarks from a freshly downloaded copy.

rox-pace.com publishes the same data it uses at /data/skill-benchmarks.json after
each weekly data refresh. This script checks a downloaded copy, writes it into
skills/hyrox-pacing/references/benchmarks.json when it differs, and bumps the
patch version in SKILL.md and .claude-plugin/marketplace.json so plugin users
get the update.

Usage: python3 scripts/update_benchmarks.py DOWNLOADED.json [--root DIR]
Writes changed=true|false (and version=…) to $GITHUB_OUTPUT when set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

BENCHMARKS = Path("skills/hyrox-pacing/references/benchmarks.json")
SKILL = Path("skills/hyrox-pacing/SKILL.md")
MARKETPLACE = Path(".claude-plugin/marketplace.json")
STATION_COUNT = 16


def validate(data: object) -> None:
    if not isinstance(data, dict):
        raise ValueError("not a JSON object")
    if not isinstance(data.get("generatedAt"), str):
        raise ValueError("generatedAt is missing")
    if not isinstance(data.get("stations"), list) or len(data["stations"]) != STATION_COUNT:
        raise ValueError(f"expected {STATION_COUNT} stations")
    divisions = data.get("divisions")
    if not isinstance(divisions, dict) or "men" not in divisions:
        raise ValueError("divisions are missing")


def bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def write_output(**values: str) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            for key, value in values.items():
                fh.write(f"{key}={value}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("downloaded", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    payload = args.downloaded.read_text(encoding="utf-8")
    try:
        validate(json.loads(payload))
    except ValueError as exc:  # json.JSONDecodeError is a ValueError
        print(f"Rejected the downloaded benchmarks: {exc}", file=sys.stderr)
        return 1

    benchmarks = args.root / BENCHMARKS
    if benchmarks.read_text(encoding="utf-8") == payload:
        print("Benchmarks unchanged.")
        write_output(changed="false")
        return 0

    skill_path = args.root / SKILL
    skill = skill_path.read_text(encoding="utf-8")
    match = re.search(r"^version: (\d+\.\d+\.\d+)$", skill, re.MULTILINE)
    if not match:
        print(f"No version line in {SKILL}", file=sys.stderr)
        return 1
    version = bump_patch(match.group(1))

    marketplace_path = args.root / MARKETPLACE
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    marketplace["plugins"][0]["version"] = version

    benchmarks.write_text(payload, encoding="utf-8")
    skill_path.write_text(skill[: match.start(1)] + version + skill[match.end(1) :], encoding="utf-8")
    marketplace_path.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")
    print(f"Updated benchmarks; version {version}.")
    write_output(changed="true", version=version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
