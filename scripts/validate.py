#!/usr/bin/env python3
"""Validate the pack: skills (Agent Skills spec + house budgets), subagents, manifests, hooks.

Usage: python3 scripts/validate.py [--strict]     (--strict turns warnings into errors)
Stdlib only, so it runs anywhere CI has Python 3.9+.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
BODY_MAX_BYTES = 7400  # Codex truncates inline skill injection at 8,000 B
BODY_MAX_LINES = 200
REF_MAX_LINES = 250
DESC_MAX_SOFT = 700
URL_RE = re.compile(r"https?://")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def split_frontmatter(text: str) -> tuple[dict, str] | None:
    """Minimal YAML-frontmatter reader: top-level `key: value`, folded `>-` blocks, and one
    level of nested keys (enough for this pack; avoids a PyYAML dependency)."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    raw, body = text[4:end], text[end + 5:]
    data: dict = {}
    key = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.split(" #", 1)[0].strip()
            data[key] = "" if v in (">-", ">", "|", "|-") else v.strip("'\"")
            if v == "":
                data[key] = {}
        elif key is not None:
            if isinstance(data[key], dict):
                k, _, v = line.strip().partition(":")
                data[key][k.strip()] = v.strip().strip("'\"")
            else:
                data[key] = (data[key] + " " + line.strip()).strip()
    return data, body


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def check_links(md: Path, text: str) -> None:
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
        if re.match(r"^[a-z]+:", target):
            continue
        if not (md.parent / target).exists():
            err(f"{rel(md)}: broken link → {target}")


def check_skill(d: Path) -> None:
    md = d / "SKILL.md"
    if not md.is_file():
        err(f"{rel(d)}: missing SKILL.md")
        return
    text = md.read_text()
    parsed = split_frontmatter(text)
    if not parsed:
        err(f"{rel(md)}: missing or malformed frontmatter")
        return
    fm, body = parsed
    for extra in set(fm) - SPEC_FIELDS:
        err(f"{rel(md)}: non-spec frontmatter field '{extra}' (breaks portability)")
    name = fm.get("name", "")
    if name != d.name:
        err(f"{rel(md)}: name '{name}' must equal directory '{d.name}'")
    if not NAME_RE.match(name) or len(name) > 64:
        err(f"{rel(md)}: name must be lowercase-hyphen and ≤ 64 chars")
    desc = fm.get("description", "")
    if not desc:
        err(f"{rel(md)}: description is required")
    elif len(desc) > 1024:
        err(f"{rel(md)}: description is {len(desc)} chars (max 1024)")
    elif len(desc) > DESC_MAX_SOFT:
        warn(f"{rel(md)}: description is {len(desc)} chars (aim ≤ {DESC_MAX_SOFT})")
    elif "use when" not in desc.lower():
        warn(f"{rel(md)}: description should say 'Use when …' to trigger reliably")
    size = len(body.encode())
    lines = body.count("\n")
    if size > BODY_MAX_BYTES or lines > BODY_MAX_LINES:
        warn(f"{rel(md)}: body is {size} B / {lines} lines (budget {BODY_MAX_BYTES} B / "
             f"{BODY_MAX_LINES} lines) — move depth to references/")
    if len(text.encode()) >= 8000:
        err(f"{rel(md)}: whole file is {len(text.encode())} B — Codex truncates inline skills "
            "at 8,000 B")
    check_links(md, body)
    for sub in d.iterdir():
        if sub.is_dir() and sub.name not in ("references", "assets", "scripts"):
            warn(f"{rel(sub)}: unexpected directory in skill")
    for f in d.rglob("*.md"):
        ftext = f.read_text()
        if re.search(r"^#+\s+Sources\s*$", ftext, re.M):
            err(f"{rel(f)}: has a Sources section — skills carry no citations")
        if URL_RE.search(ftext):
            err(f"{rel(f)}: contains a URL — skills carry no citations or links out")
    refs = d / "references"
    if refs.is_dir():
        for ref in refs.rglob("*"):
            if ref.is_dir():
                err(f"{rel(ref)}: references must be one level deep")
            elif ref.suffix == ".md":
                rtext = ref.read_text()
                if rtext.count("\n") > REF_MAX_LINES:
                    warn(f"{rel(ref)}: {rtext.count(chr(10))} lines (budget {REF_MAX_LINES})")
                check_links(ref, rtext)
                if ref.name not in body:
                    warn(f"{rel(ref)}: not referenced from SKILL.md")


def check_agent(md: Path, skill_names: set[str]) -> None:
    parsed = split_frontmatter(md.read_text())
    if not parsed:
        err(f"{rel(md)}: missing or malformed frontmatter")
        return
    fm, body = parsed
    if fm.get("name") != md.stem:
        err(f"{rel(md)}: name must equal filename stem '{md.stem}'")
    if not fm.get("description"):
        err(f"{rel(md)}: description is required")
    if md.stem in skill_names:
        err(f"{rel(md)}: subagent name collides with a skill")
    if "## Output contract" not in body:
        err(f"{rel(md)}: subagents must define an '## Output contract' section")
    for skill in agent_skills(fm):
        if skill not in skill_names:
            err(f"{rel(md)}: preloads unknown skill '{skill}'")


def agent_skills(fm: dict) -> list[str]:
    """The `skills:` a subagent preloads (comma-separated, bare names)."""
    return [s.strip() for s in str(fm.get("skills", "")).split(",") if s.strip()]


def check_json(path: Path) -> None:
    try:
        json.loads(path.read_text())
    except ValueError as e:
        err(f"{rel(path)}: invalid JSON ({e})")


def check_versions() -> None:
    manifests = [p for p in ROOT.glob(".*-plugin/plugin.json")] + \
                [p for p in [ROOT / "gemini-extension.json"] if p.exists()]
    versions = {}
    for m in manifests:
        try:
            versions[rel(m)] = json.loads(m.read_text()).get("version")
        except ValueError:
            pass
    if len(set(versions.values())) > 1:
        err(f"manifest versions differ: {versions} — run scripts/bump_version.py")


def main() -> int:
    strict = "--strict" in sys.argv
    skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    for d in skills:
        check_skill(d)
    names = {d.name for d in skills}
    for md in sorted((ROOT / "agents").glob("*.md")):
        check_agent(md, names)
    for path in list(ROOT.glob(".*-plugin/*.json")) + list(ROOT.glob("hooks/**/*.json")) + \
            [p for p in [ROOT / "gemini-extension.json"] if p.exists()]:
        check_json(path)
    check_versions()

    for w in warnings:
        print(f"warn  {w}")
    for e in errors:
        print(f"ERROR {e}")
    failed = bool(errors) or (strict and bool(warnings))
    print(f"\n{len(skills)} skills, {len(list((ROOT / 'agents').glob('*.md')))} agents — "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
