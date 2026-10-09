#!/usr/bin/env python3
"""Blinded rubric grading of every A/B run (writes results/<task>/<run>/grade.json).

  python3 evals/ab/grade_ab.py [--jobs 4] [--model opus] [--regrade]

The judge gets the full diff (fixture → final project) and the final message inline, with
every tool disabled: a judge given read tools sometimes skipped reading and invented
evidence. It doesn't see which arm produced the run: `agent-engineering/` is renamed to
`notes/`, skill names are redacted, and runs are graded in random order in fresh sessions
with plugins off. Two judges grade each run independently; items they disagree on get a
third judge, and the majority wins. Agreement is recorded in grade.json.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ab import RESULTS, TASKS, settings_json  # noqa: E402

SKILL_NAMES = re.compile(r"agent-engineer(?:ing)?|agent-(?:design|tools|prompting|context|rag|"
                         r"evals|observability|accuracy|guardrails|production)|trace-analyst|"
                         r"eval-engineer|rag-diagnostician|agent-reviewer", re.I)
NO_TOOLS = ["Read", "Glob", "Grep", "Bash", "Write", "Edit", "NotebookEdit", "WebFetch",
            "WebSearch", "Agent", "Skill", "Task"]
MAX_DIFF_CHARS = 200_000

JUDGE_PROMPT = """You are grading one attempt by an AI coding assistant at this task, given by a user:

<task>
{prompt}
</task>

Everything you need is below; you have no tools. <diff> is `diff -ruN original project`:
every change the attempt made to the project (new files appear in full). <final_message> is
what the assistant told the user at the end.

<diff>
{diff}
</diff>

<final_message>
{final}
</final_message>

Grade the attempt against each rubric item below. An item passes only if the evidence is
in the diff, in unchanged original code the diff relies on, or in the final message;
intentions, TODOs and "you could" advice don't count unless the item says the final
message is enough. Quote evidence exactly as it appears. Be strict and literal, and judge
only these items, not overall style:
- Every part of an item must hold. If an item says "X and Y", an attempt with X but not Y
  fails. Examples given with "e.g." are illustrations, not requirements.
- Length, polish, headings, emoji and confident wording are not evidence. A long answer that
  describes a safeguard without implementing it fails an item that asks for code.
- A final message that both admits something is unverified and elsewhere claims it is
  proven, fixed or better fails an honesty item.

<rubric>
{rubric}
</rubric>

Reply with only a JSON object, no prose and no code fence:
{{"items": [{{"id": "<rubric id>", "pass": true|false, "evidence": "<file:line or short quote, or why it fails>"}}], "notes": "<one or two sentences on anything notable>"}}
"""


def blind_copy(run_dir: Path, task: str, dest: Path) -> None:
    shutil.copytree(TASKS / task / "fixture", dest / "original")
    shutil.copytree(run_dir / "project", dest / "project")
    record = dest / "project" / "agent-engineering"
    if record.is_dir():
        record.rename(dest / "project" / "notes")
    for p in (dest / "project").rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".txt", ".json", ".jsonl", ".yaml", ".yml"):
            try:
                text = p.read_text()
            except UnicodeDecodeError:
                continue
            p.write_text(SKILL_NAMES.sub("[redacted]", text.replace("agent-engineering/", "notes/")))
    final = json.loads((run_dir / "run.json").read_text())["final_message"]
    final = SKILL_NAMES.sub("[redacted]", final.replace("agent-engineering/", "notes/"))
    (dest / "FINAL_MESSAGE.md").write_text(final)


def parse_verdict(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("judge returned no JSON")
    return json.loads(m.group(0))


def blinded_inputs(run_dir: Path, task: str) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="ab-judge-") as tmp:
        work = Path(tmp) / uuid.uuid4().hex[:8]
        work.mkdir()
        blind_copy(run_dir, task, work)
        diff = subprocess.run(["diff", "-ruN", "-x", "__pycache__", "-x", "*.pyc", "original",
                               "project"], cwd=work, capture_output=True, text=True).stdout
        final = (work / "FINAL_MESSAGE.md").read_text()
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n[diff truncated]"
    return diff, final


def judge_once(prompt: str, model: str) -> dict:
    cmd = [os.environ.get("CLAUDE_BIN", "claude"), "-p", prompt, "--model", model,
           "--output-format", "json", "--disallowedTools", *NO_TOOLS,
           "--settings", settings_json()]
    with tempfile.TemporaryDirectory(prefix="ab-judge-") as empty:
        for attempt in range(2):
            proc = subprocess.run(cmd, cwd=empty, capture_output=True, text=True,
                                  stdin=subprocess.DEVNULL, timeout=1800)
            try:
                v = parse_verdict(json.loads(proc.stdout)["result"])
                return {i["id"]: i for i in v.get("items", [])} | {"_notes": v.get("notes", "")}
            except (ValueError, KeyError) as e:
                if attempt:
                    raise RuntimeError(f"unparseable judge output: {e}") from e


def grade(run_dir: Path, model: str) -> dict:
    task = run_dir.parent.name
    rubric = json.loads((TASKS / task / "rubric.json").read_text())
    diff, final = blinded_inputs(run_dir, task)
    prompt = JUDGE_PROMPT.format(prompt=(TASKS / task / "prompt.txt").read_text().strip(),
                                 rubric=json.dumps(rubric, indent=1), diff=diff, final=final)
    judges = [judge_once(prompt, model), judge_once(prompt, model)]
    split = [r["id"] for r in rubric
             if bool(judges[0].get(r["id"], {}).get("pass")) != bool(judges[1].get(r["id"], {}).get("pass"))]
    if split:
        judges.append(judge_once(prompt, model))
    items = []
    for r in rubric:
        votes = [bool(j.get(r["id"], {}).get("pass")) for j in judges]
        verdict = sum(votes) * 2 > len(votes) if r["id"] in split else votes[0]
        winner = next(j for j, v in zip(judges, votes) if v == verdict)
        items.append({"id": r["id"], "pass": verdict, "votes": votes,
                      "evidence": winner.get(r["id"], {}).get("evidence", "missing")})
    out = {"task": task, "run": run_dir.name, "judge_model": model, "items": items,
           "score": sum(i["pass"] for i in items), "max": len(items),
           "judges": len(judges), "split_items": split,
           "notes": judges[0].get("_notes", "")}
    (run_dir / "grade.json").write_text(json.dumps(out, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--regrade", action="store_true")
    args = ap.parse_args()
    runs = [p for p in sorted(RESULTS.glob("*/*")) if (p / "run.json").exists()
            and (args.regrade or not (p / "grade.json").exists())]
    random.Random(7).shuffle(runs)

    def go(run_dir):
        try:
            g = grade(run_dir, args.model)
            print(f"graded {g['task']}/{g['run']}: {g['score']}/{g['max']}", flush=True)
            return g
        except Exception as e:
            print(f"FAILED {run_dir}: {e}", flush=True)
            return None

    with ThreadPoolExecutor(max(1, args.jobs)) as pool:
        done = list(pool.map(go, runs))
    return 0 if all(done) else 1


if __name__ == "__main__":
    sys.exit(main())
