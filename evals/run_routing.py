#!/usr/bin/env python3
"""Routing eval: does each prompt load the expected agent-* skill? (Claude Code only for now.)

  python3 evals/run_routing.py --harness claude [--case ID] [--model MODEL] [--jobs N]

Set CLAUDE_BIN if `claude` isn't on PATH.

Runs `claude -p` headless with this checkout as a plugin dir, in a fresh copy of
evals/fixture/ (a small LangGraph support agent), reads the stream-json events, and records
which skills the model invoked on its first turns. Running inside the pack itself would
test the wrong thing: the model sees AGENTS.md and reads the skill files directly.
"""
from __future__ import annotations

import argparse
import json
import shutil
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "evals" / "fixture"


def skills_loaded(prompt: str, model: str | None, edits: dict[str, str]) -> set[str]:
    cmd = [os.environ.get("CLAUDE_BIN", "claude"), "-p", prompt, "--plugin-dir", str(ROOT), "--output-format", "stream-json",
           "--verbose", "--max-turns", "3", "--permission-mode", "plan"]
    if model:
        cmd += ["--model", model]
    with tempfile.TemporaryDirectory(prefix="ae-routing-") as tmp:
        project = Path(tmp) / "support-agent"
        shutil.copytree(FIXTURE, project)
        git = ["git", "-c", "user.name=routing-eval", "-c", "user.email=eval@example.invalid"]
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "fixture"]):
            subprocess.run(git + args, cwd=project, check=False, capture_output=True)
        for rel, text in edits.items():  # uncommitted changes the prompt can refer to
            (project / rel).write_text(text)
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=project,
                             stdin=subprocess.DEVNULL).stdout
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
    ap.add_argument("--jobs", type=int, default=4, help="sessions to run in parallel")
    args = ap.parse_args()
    cases = [json.loads(l) for l in (ROOT / "evals/routing.jsonl").read_text().splitlines() if l]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    with ThreadPoolExecutor(max(1, args.jobs)) as pool:
        results = list(pool.map(lambda c: skills_loaded(c["prompt"], args.model,
                                                       c.get("edits", {})), cases))
    passed = 0
    for c, got in zip(cases, results):
        ok = (not got) if not c["expect"] else bool(got & set(c["expect"]))
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'} {c['id']}: expected {c['expect'] or 'none'}, "
              f"got {sorted(got) or 'none'}")
    positives = [got for c, got in zip(cases, results) if c["expect"]]
    extra = sum(len(got) for got in positives) / max(1, len(positives))
    print(f"\n{passed}/{len(cases)} passed; {extra:.1f} agent-* skills loaded per positive case "
          "(breadth: lower is cheaper, as long as cases pass)")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
