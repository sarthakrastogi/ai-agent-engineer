#!/usr/bin/env python3
"""Behavioural A/B eval: the same task, with and without the agent-engineer plugin.

  python3 evals/ab/run_ab.py [--tasks a,b] [--runs 3] [--jobs 4] [--model opus]
  python3 evals/ab/grade_ab.py            # blinded rubric grading of every run
  python3 evals/ab/report_ab.py           # summary.md / summary.json

Each run copies tasks/<task>/fixture/ into a fresh git repo, sends tasks/<task>/prompt.txt to
`claude -p`, then saves the transcript, the final project and its pytest result under
results/<task>/<arm>-<n>/. Both arms disable every installed plugin through --settings; the
"with" arm adds this checkout via --plugin-dir. Set CLAUDE_BIN if `claude` isn't on PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASKS = HERE / "tasks"
RESULTS = HERE / "results"
PLUGIN = "agent-engineer"

# Local commands only: no package installs, no network.
ALLOWED_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash(python3:*)", "Bash(python:*)",
                 "Bash(pytest:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(find:*)",
                 "Bash(head:*)", "Bash(wc:*)", "Bash(mkdir:*)", "Bash(git diff:*)",
                 "Bash(git status:*)", "Bash(git log:*)", "Bash(git show:*)"]
# Deny rules win over allow rules: `python3 *` would otherwise allow `python3 -m pip install`.
DENIED_TOOLS = ["Bash(python3 -m pip:*)", "Bash(python -m pip:*)", "Bash(pip:*)", "Bash(pip3:*)",
                "Bash(python3 -m venv:*)", "Bash(uv:*)"]
GIT = ["git", "-c", "user.name=ab-eval", "-c", "user.email=ab-eval@example.invalid"]


def installed_plugins() -> list[str]:
    path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        return list(json.loads(path.read_text()).get("plugins", {}))
    except (OSError, ValueError):
        return []


def settings_json() -> str:
    """Disable every installed plugin in both arms, so only --plugin-dir differs."""
    disabled = {p: False for p in installed_plugins()}
    for p in ("agent-engineer@agent-engineer", "viola@viola"):
        disabled.setdefault(p, False)
    return json.dumps({"enabledPlugins": disabled})


def run_one(task: str, arm: str, n: int, model: str, budget: float) -> dict:
    out_dir = RESULTS / task / f"{arm}-{n}"
    if (out_dir / "run.json").exists():
        return json.loads((out_dir / "run.json").read_text())
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    prompt = (TASKS / task / "prompt.txt").read_text().strip()
    with tempfile.TemporaryDirectory(prefix="ab-") as tmp:
        project = Path(tmp) / task  # same path shape in both arms
        shutil.copytree(TASKS / task / "fixture", project)
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "fixture"]):
            subprocess.run(GIT + args, cwd=project, check=True, capture_output=True)
        cmd = [os.environ.get("CLAUDE_BIN", "claude"), "-p", prompt, "--model", model,
               "--output-format", "stream-json", "--verbose",
               "--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED_TOOLS,
               "--disallowedTools", *DENIED_TOOLS,
               "--max-budget-usd", str(budget), "--settings", settings_json()]
        if arm == "with":
            cmd += ["--plugin-dir", str(ROOT)]
        start = time.time()
        proc = subprocess.run(cmd, cwd=project, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=3600)
        elapsed = time.time() - start
        (out_dir / "transcript.jsonl").write_text(proc.stdout)
        if proc.stderr.strip():
            (out_dir / "stderr.txt").write_text(proc.stderr)

        plugins, result, tools, skills = [], {}, 0, []
        for line in proc.stdout.splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                plugins = [p.get("name") for p in ev.get("plugins", [])]
            elif ev.get("type") == "assistant":
                for b in ev.get("message", {}).get("content", []):
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tools += 1
                        if b.get("name") == "Skill":
                            skills.append(str(b.get("input", {}).get("skill", "")))
            elif ev.get("type") == "result":
                result = ev
        loaded = PLUGIN in plugins
        if loaded != (arm == "with"):
            raise RuntimeError(f"{task} {arm}-{n}: plugin loaded={loaded}; arm is contaminated")

        diff = subprocess.run(["git", "diff", "--stat", "HEAD"], cwd=project, capture_output=True,
                              text=True).stdout
        subprocess.run(GIT + ["add", "-A"], cwd=project, capture_output=True)
        numstat = subprocess.run(["git", "diff", "--cached", "--numstat", "HEAD"], cwd=project,
                                 capture_output=True, text=True).stdout
        added = sum(int(r.split()[0]) for r in numstat.splitlines() if r.split()[0].isdigit())
        tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                               cwd=project, capture_output=True, text=True, timeout=300)
        tail = tests.stdout.strip().splitlines()[-1:] or [""]
        shutil.copytree(project, out_dir / "project", ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache"))
        (out_dir / "diff.txt").write_text(diff)

    version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
    run = {"task": task, "arm": arm, "n": n, "model": model, "plugins": plugins,
           "plugin_version": version if arm == "with" else None,
           "skills_loaded": skills, "tool_calls": tools, "elapsed_s": round(elapsed),
           "turns": result.get("num_turns"), "cost_usd": result.get("total_cost_usd"),
           "is_error": result.get("is_error", True), "stop": result.get("subtype"),
           "final_message": result.get("result", ""), "lines_added": added,
           "files_changed": len(numstat.splitlines()),
           "tests_passed": tests.returncode == 0, "tests_summary": tail[0]}
    (out_dir / "run.json").write_text(json.dumps(run, indent=2))
    return run


def retest(run_dir: Path) -> None:
    """Re-run a saved project's tests so every run is measured in the same environment."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("ANTHROPIC_")}
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                          cwd=run_dir / "project", capture_output=True, text=True, timeout=300,
                          env=env)
    run = json.loads((run_dir / "run.json").read_text())
    run["tests_clean"] = proc.returncode == 0
    run["tests_clean_summary"] = (proc.stdout.strip().splitlines()[-1:] or [""])[0]
    (run_dir / "run.json").write_text(json.dumps(run, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", help="comma-separated task names (default: all)")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--budget", type=float, default=3.0, help="max USD per run")
    ap.add_argument("--arms", default="with,without")
    ap.add_argument("--retest", action="store_true",
                    help="only re-run saved projects' tests in this environment")
    args = ap.parse_args()
    if args.retest:
        for d in sorted(RESULTS.glob("*/*")):
            if (d / "run.json").exists():
                retest(d)
        return 0
    tasks = args.tasks.split(",") if args.tasks else sorted(p.name for p in TASKS.iterdir())
    jobs = [(t, arm, n) for n in range(1, args.runs + 1) for t in tasks
            for arm in args.arms.split(",")]

    def go(job):
        try:
            r = run_one(*job, args.model, args.budget)
            print(f"done {job}: {r['elapsed_s']}s ${r['cost_usd']} tests_passed={r['tests_passed']}",
                  flush=True)
            return r
        except Exception as e:  # keep the other runs going
            print(f"FAILED {job}: {e}", flush=True)
            return None

    with ThreadPoolExecutor(max(1, args.jobs)) as pool:
        results = list(pool.map(go, jobs))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
