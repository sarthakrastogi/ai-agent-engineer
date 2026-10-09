#!/usr/bin/env python3
"""Summarise graded A/B runs into results/summary[-judge].{json,md}.

  python3 evals/ab/report_ab.py [--grader audit|judge]

`audit` (default) uses audit.json: a blinded agent that reads the files and grades
strictly. `judge` uses grade.json from grade_ab.py, which agreed with the audit on 85% of
items and was lenient in the plugin arms' favour (see docs/README.md).
"""
from __future__ import annotations

import json
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ab import RESULTS, TASKS  # noqa: E402

# Arm = run directory name without its run number: without-2 → without, with-v0.2-1 → with-v0.2.
ARMS = ("without", "with-v0.2", "with")
LABEL = {"without": "No plugin", "with-v0.2": "v0.2.0", "with": "v0.3.0"}


GRADER = "audit"


def load() -> list[dict]:
    runs = []
    for d in sorted(RESULTS.glob("*/*")):
        src = d / ("audit.json" if GRADER == "audit" else "grade.json")
        if (d / "run.json").exists() and src.exists():
            run = json.loads((d / "run.json").read_text())
            run["grade"] = json.loads(src.read_text())
            run["arm"] = d.name.rsplit("-", 1)[0]
            orig = {p.relative_to(TASKS / run["task"] / "fixture")
                    for p in (TASKS / run["task"] / "fixture").rglob("*") if p.is_file()}
            new = [p.relative_to(d / "project") for p in (d / "project").rglob("*")
                   if p.is_file() and p.relative_to(d / "project") not in orig]
            run["new_md_files"] = sum(p.suffix == ".md" for p in new)
            run["record_dir"] = (d / "project" / "agent-engineering").is_dir()
            runs.append(run)
    return runs


def frac(run: dict) -> float:
    return run["grade"]["score"] / run["grade"]["max"]


def bootstrap_diff(runs: list[dict], arm: str, iters: int = 10000,
                   seed: int = 1) -> tuple[float, float]:
    """95% CI for mean(arm) − mean(without) rubric fraction over tasks that have both,
    resampling runs within each task."""
    rng = random.Random(seed)
    cells = defaultdict(list)
    for r in runs:
        cells[(r["task"], r["arm"])].append(frac(r))
    tasks = sorted({t for t, _ in cells})
    diffs = []
    for _ in range(iters):
        d = [st.mean(rng.choices(cells[(t, arm)], k=len(cells[(t, arm)]))) -
             st.mean(rng.choices(cells[(t, "without")], k=len(cells[(t, "without")])))
             for t in tasks if cells[(t, arm)] and cells[(t, "without")]]
        diffs.append(st.mean(d))
    diffs.sort()
    return diffs[int(0.025 * iters)], diffs[int(0.975 * iters)]


def mean(xs) -> float:
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else float("nan")


def summarise(runs: list[dict]) -> dict:
    out = {"tasks": {}, "overall": {}}
    for task in sorted({r["task"] for r in runs}):
        t = {"arms": {}, "items": {}}
        rubric = json.loads((TASKS / task / "rubric.json").read_text())
        for arm in ARMS:
            rs = [r for r in runs if r["task"] == task and r["arm"] == arm]
            if not rs:
                continue
            t["arms"][arm] = {
                "n": len(rs), "score_pct": 100 * mean(frac(r) for r in rs),
                "scores": [f"{r['grade']['score']}/{r['grade']['max']}" for r in rs],
                "tests_passed": sum(r.get("tests_clean", r["tests_passed"]) for r in rs),
                "cost_usd": mean(r["cost_usd"] for r in rs),
                "elapsed_s": mean(r["elapsed_s"] for r in rs),
                "turns": mean(r["turns"] for r in rs),
                "lines_added": mean(r["lines_added"] for r in rs),
                "new_md_files": mean(r["new_md_files"] for r in rs),
                "record_dir": sum(r["record_dir"] for r in rs),
                "skills": sorted({s.split(":")[-1] for r in rs for s in r["skills_loaded"]}),
            }
        for item in rubric:
            t["items"][item["id"]] = {
                arm: sum(next(i["pass"] for i in r["grade"]["items"] if i["id"] == item["id"])
                         for r in runs if r["task"] == task and r["arm"] == arm)
                for arm in t["arms"]}
        out["tasks"][task] = t
    for arm in ARMS:
        rs = [r for r in runs if r["arm"] == arm]
        if not rs:
            continue
        out["overall"][arm] = {
            "n": len(rs), "score_pct": 100 * mean(frac(r) for r in rs),
            "tests_passed": sum(r.get("tests_clean", r["tests_passed"]) for r in rs),
            "cost_usd": mean(r["cost_usd"] for r in rs), "elapsed_s": mean(r["elapsed_s"] for r in rs),
            "turns": mean(r["turns"] for r in rs), "new_md_files": mean(r["new_md_files"] for r in rs)}
    out["comparisons"] = {}
    for arm in ARMS[1:]:
        tasks = sorted({r["task"] for r in runs if r["arm"] == arm} &
                       {r["task"] for r in runs if r["arm"] == "without"})
        if not tasks:
            continue
        both = [r for r in runs if r["task"] in tasks]
        def pct(a):
            return 100 * mean(frac(r) for r in both if r["arm"] == a)
        lo, hi = bootstrap_diff(both, arm)
        out["comparisons"][arm] = {"tasks": tasks, "arm_pct": pct(arm), "without_pct": pct("without"),
                                   "diff_pct_points": pct(arm) - pct("without"),
                                   "diff_ci95": [100 * lo, 100 * hi]}
    return out


def markdown(s: dict) -> str:
    lines = [f"# A/B summary (grader: {GRADER})", ""]
    for arm, c in s["comparisons"].items():
        lines.append(f"- **{LABEL[arm]} vs no plugin** on {len(c['tasks'])} tasks: "
                     f"{c['arm_pct']:.0f}% vs {c['without_pct']:.0f}% "
                     f"({c['diff_pct_points']:+.0f} points, 95% CI {c['diff_ci95'][0]:+.0f} to "
                     f"{c['diff_ci95'][1]:+.0f})")
    arms = [a for a in ARMS if a in s["overall"]]
    head = " | ".join(LABEL[a] for a in arms)
    lines += ["", f"| Task | {head} | Tests pass | Cost $ | Time s | New .md files |",
              "|---|" + "---|" * (len(arms) + 4)]
    for task, t in s["tasks"].items():
        a = [x for x in arms if x in t["arms"]]
        cell = lambda k, f: " · ".join(f(t["arms"][x][k]) if x in t["arms"] else "–" for x in arms)
        lines.append(f"| {task} | " + " | ".join(
            f"{t['arms'][x]['score_pct']:.0f}% ({', '.join(t['arms'][x]['scores'])})"
            if x in t["arms"] else "–" for x in arms) + " | " +
            " · ".join(f"{t['arms'][x]['tests_passed']}/{t['arms'][x]['n']}" if x in t["arms"]
                       else "–" for x in arms) + " | " +
            cell("cost_usd", lambda v: f"{v:.2f}") + " | " + cell("elapsed_s", lambda v: f"{v:.0f}")
            + " | " + cell("new_md_files", lambda v: f"{v:.1f}") + " |")
    lines += ["", f"Multi-value cells are in arm order: {', '.join(LABEL[a] for a in arms)}."]
    for task, t in s["tasks"].items():
        a = [x for x in arms if x in t["arms"]]
        lines += ["", f"## {task}", ""]
        for x in a:
            if x != "without":
                lines.append(f"Skills loaded ({LABEL[x]}): {', '.join(t['arms'][x]['skills']) or 'none'}  ")
        lines += ["", "| Rubric item | " + " | ".join(LABEL[x] for x in a) + " |",
                  "|---|" + "---|" * len(a)]
        for item, c in t["items"].items():
            lines.append(f"| {item} | " + " | ".join(f"{c[x]}/{t['arms'][x]['n']}" for x in a) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    global GRADER
    if "--grader" in sys.argv:
        GRADER = sys.argv[sys.argv.index("--grader") + 1]
    runs = load()
    if not runs:
        print("no graded runs; run run_ab.py then grade_ab.py")
        return 1
    s = summarise(runs)
    suffix = "" if GRADER == "audit" else f"-{GRADER}"
    (RESULTS / f"summary{suffix}.json").write_text(json.dumps(s, indent=2))
    (RESULTS / f"summary{suffix}.md").write_text(markdown(s))
    print(markdown(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
