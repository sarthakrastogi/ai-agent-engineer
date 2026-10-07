#!/usr/bin/env python3
"""Routing eval: does each prompt load the expected agent-* skill? (Claude Code only for now.)

  python3 evals/run_routing.py --harness claude [--case ID] [--model MODEL]

Runs `claude -p` headless with this checkout as a plugin dir, reads the stream-json events,
and records which skills the model invoked on its first turns.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def skills_loaded(prompt: str, model: str | None) -> set[str]:
    cmd = ["claude", "-p", prompt, "--plugin-dir", str(ROOT), "--output-format", "stream-json",
           "--verbose", "--max-turns", "3", "--permission-mode", "plan"]
    if model:
        cmd += ["--model", model]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=300).stdout
    loaded = set()
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        for block in (ev.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and \
                    block.get("name") == "Skill":
                name = str((block.get("input") or {}).get("skill", ""))
                loaded.add(name.split(":")[-1])
    return {s for s in loaded if s.startswith("agent-")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="claude", choices=["claude"])
    ap.add_argument("--case")
    ap.add_argument("--model")
    args = ap.parse_args()
    cases = [json.loads(l) for l in (ROOT / "evals/routing.jsonl").read_text().splitlines() if l]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    passed = 0
    for c in cases:
        got = skills_loaded(c["prompt"], args.model)
        ok = (not got) if not c["expect"] else bool(got & set(c["expect"]))
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'} {c['id']}: expected {c['expect'] or 'none'}, "
              f"got {sorted(got) or 'none'}")
    print(f"\n{passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
