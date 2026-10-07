#!/usr/bin/env python3
"""Generate per-harness subagent files from the canonical agents/*.md.

  python3 scripts/build_adapters.py           write adapters/<harness>/agents/*
  python3 scripts/build_adapters.py --check   exit 1 if generated files are stale (CI)

Claude Code reads agents/*.md directly. Everything else is generated:
  codex     adapters/codex/agents/<name>.toml     (developer_instructions, sandbox_mode)
  cursor    adapters/cursor/agents/<name>.md      (readonly, model: inherit)
  opencode  adapters/opencode/agents/<name>.md    (mode: subagent, permission map)
  gemini    adapters/gemini/agents/<name>.md      (snake_case tool list)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import split_frontmatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HEADER = "Generated from agents/{name}.md by scripts/build_adapters.py — do not edit."
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
GEMINI_TOOLS = {
    "Read": ["read_file", "read_many_files"], "Grep": ["grep_search"],
    "Glob": ["glob", "list_directory"], "Bash": ["run_shell_command"],
    "Write": ["write_file"], "Edit": ["replace"], "WebFetch": ["web_fetch"],
    "WebSearch": ["google_web_search"],
}


def load_agents() -> list[dict]:
    agents = []
    for md in sorted((ROOT / "agents").glob("*.md")):
        fm, body = split_frontmatter(md.read_text())
        tools = [t.strip() for t in fm.get("tools", "").split(",") if t.strip()]
        agents.append({"name": fm["name"], "description": fm["description"],
                       "tools": tools, "body": body.strip() + "\n"})
    return agents


def yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def codex(a: dict) -> str:
    if "'''" in a["body"]:
        raise ValueError(f"{a['name']}: body contains ''' which breaks TOML literal strings")
    sandbox = "workspace-write" if WRITE_TOOLS & set(a["tools"]) else "read-only"
    return (f"# {HEADER.format(**a)}\n"
            f"name = {yaml_str(a['name'])}\n"
            f"description = {yaml_str(a['description'])}\n"
            f"sandbox_mode = \"{sandbox}\"\n"
            f"developer_instructions = '''\n{a['body']}'''\n")


def cursor(a: dict) -> str:
    readonly = "false" if WRITE_TOOLS & set(a["tools"]) else "true"
    return (f"---\nname: {a['name']}\ndescription: {yaml_str(a['description'])}\n"
            f"model: inherit\nreadonly: {readonly}\n---\n\n"
            f"<!-- {HEADER.format(**a)} -->\n\n{a['body']}")


def opencode(a: dict) -> str:
    tools = set(a["tools"])
    perm = {
        "edit": "allow" if WRITE_TOOLS & tools else "deny",
        "bash": "allow" if "Bash" in tools else "deny",
        "webfetch": "allow" if "WebFetch" in tools else "deny",
    }
    perm_yaml = "".join(f"  {k}: {v}\n" for k, v in perm.items())
    return (f"---\ndescription: {yaml_str(a['description'])}\nmode: subagent\n"
            f"permission:\n{perm_yaml}---\n\n<!-- {HEADER.format(**a)} -->\n\n{a['body']}")


def gemini(a: dict) -> str:
    tools = [g for t in a["tools"] for g in GEMINI_TOOLS.get(t, [])]
    tools_yaml = "".join(f"  - {t}\n" for t in dict.fromkeys(tools))
    return (f"---\nname: {a['name']}\ndescription: {yaml_str(a['description'])}\n"
            f"tools:\n{tools_yaml}---\n\n<!-- {HEADER.format(**a)} -->\n\n{a['body']}")


TARGETS = {"codex": (codex, ".toml"), "cursor": (cursor, ".md"),
           "opencode": (opencode, ".md"), "gemini": (gemini, ".md")}


def expected() -> dict[Path, str]:
    files = {}
    for a in load_agents():
        for harness, (fn, ext) in TARGETS.items():
            files[ROOT / "adapters" / harness / "agents" / f"{a['name']}{ext}"] = fn(a)
    return files


def main() -> int:
    check = "--check" in sys.argv
    want = expected()
    existing = {p for h in TARGETS for p in (ROOT / "adapters" / h / "agents").glob("*")}
    stale = [p for p, text in want.items() if not p.exists() or p.read_text() != text]
    orphans = sorted(existing - set(want))
    if check:
        for p in stale + orphans:
            print(f"stale: {p.relative_to(ROOT)}")
        if stale or orphans:
            print("run: python3 scripts/build_adapters.py")
            return 1
        print(f"adapters up to date ({len(want)} files)")
        return 0
    for p, text in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    for p in orphans:
        p.unlink()
    print(f"wrote {len(want)} files, removed {len(orphans)} orphans")
    return 0


if __name__ == "__main__":
    sys.exit(main())
