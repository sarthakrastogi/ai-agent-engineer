#!/usr/bin/env python3
"""Set the pack version everywhere it appears.

  python3 scripts/bump_version.py 0.2.0

Updates every plugin/marketplace manifest and `metadata.version` in every SKILL.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.\-]+)?$")


def set_json(path: Path, version: str) -> None:
    data = json.loads(path.read_text())
    if "version" in data:
        data["version"] = version
    if isinstance(data.get("metadata"), dict) and "version" in data["metadata"]:
        data["metadata"]["version"] = version
    for plugin in data.get("plugins", []):
        if "version" in plugin:
            plugin["version"] = version
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    if len(sys.argv) != 2 or not SEMVER.match(sys.argv[1]):
        print(__doc__)
        return 2
    version = sys.argv[1]
    for path in sorted(ROOT.glob(".*-plugin/*.json")):
        set_json(path, version)
        print(f"updated {path.relative_to(ROOT)}")
    for md in sorted(ROOT.glob("skills/*/SKILL.md")):
        text = md.read_text()
        new = re.sub(r"(?m)^(\s+version:\s*).*$", rf"\g<1>{version}", text, count=1)
        if new != text:
            md.write_text(new)
            print(f"updated {md.relative_to(ROOT)}")
    print(f"\nversion → {version}. Add a CHANGELOG.md entry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
