#!/usr/bin/env python3
"""agent-engineer hook runner — one script for every harness.

Usage:  ae_hook.py <event> --harness <claude|codex|cursor|gemini|opencode>

Events:
  session-start   inject a short LLM-project profile + pointer to the agent-engineer skill
  pre-write       deny file writes that contain likely API keys
  post-write      remember behaviour-changing edits (prompts, tools, agent config); remind once
  post-bash       remember when an eval command ran
  stop            if behaviour changed and no eval ran, ask the agent (once) to run evals

Contract: stdlib only, no network, never writes to the user's repo, fails open (any internal
error → exit 0 with no output), and finishes well under the harness timeout.

Env switches: AE_HOOKS=off (all), AE_SECRET_GUARD=off, AE_EVAL_GATE=off, AE_DIR (artifact dir).
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

ARTIFACT_DIR = os.environ.get("AE_DIR", "agent-engineering")
MAX_FILE_BYTES = 256_000
STATE_TTL_S = 7 * 24 * 3600

# --------------------------------------------------------------------------- detection

LLM_LIBS = {
    # python
    "anthropic", "openai", "langchain", "langgraph", "llama-index", "llama_index", "crewai",
    "autogen", "ag2", "pydantic-ai", "pydantic_ai", "dspy", "dspy-ai", "haystack-ai",
    "semantic-kernel", "smolagents", "strands-agents", "google-genai", "google-adk",
    "litellm", "instructor", "mistralai", "cohere", "claude-agent-sdk", "openai-agents",
    "bedrock-agentcore", "mcp", "fastmcp",
    # js / ts
    "@anthropic-ai/sdk", "@anthropic-ai/claude-agent-sdk", "@langchain/core",
    "@langchain/langgraph", "llamaindex", "@mastra/core", "@openai/agents", "@google/genai",
    "@modelcontextprotocol/sdk", "@ai-sdk/openai", "@ai-sdk/anthropic",
}
TRACING_LIBS = {
    "opentelemetry-sdk", "opentelemetry-api", "@opentelemetry/sdk-node", "@opentelemetry/api",
    "openinference", "langfuse", "langsmith", "arize-phoenix", "braintrust",
    "mlflow", "weave", "opik", "traceloop-sdk", "openllmetry", "logfire", "agentops",
    "helicone", "ddtrace", "@arizeai/openinference-core", "@traceloop/node-server-sdk",
}
EVAL_LIBS = {
    "promptfoo", "deepeval", "ragas", "inspect-ai", "inspect_ai", "braintrust",
    "openevals", "agentevals", "trulens", "giskard", "autoevals",
}
DEP_FILES = (
    "pyproject.toml", "requirements.txt", "requirements-dev.txt", "requirements.in",
    "setup.py", "setup.cfg", "Pipfile", "uv.lock", "poetry.lock", "package.json",
)
EVAL_PATHS = ("evals", "eval", "tests/evals", "tests/eval", "promptfooconfig.yaml",
              "promptfooconfig.yml")

SECRET_PATTERNS = [
    ("Anthropic API key", r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    ("OpenAI API key", r"sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{32,}"),
    ("AWS access key ID", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("GitHub token", r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})"),
    ("Slack token", r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    ("Google API key", r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ("Hugging Face token", r"\bhf_[A-Za-z0-9]{30,}\b"),
    ("Groq API key", r"\bgsk_[A-Za-z0-9]{40,}\b"),
    ("Stripe live key", r"\b[rs]k_live_[0-9A-Za-z]{24,}\b"),
    ("Private key", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
]
PLACEHOLDER = re.compile(r"(x{6,}|your[_\-]?|example|placeholder|dummy|redacted|\.\.\.|<[^>]+>)",
                         re.I)

BEHAVIOUR_PATH = re.compile(r"(^|/)(prompts?|instructions|system[_\-]?prompts?)(/|\.|_|-)|"
                            r"\.(prompt|prompty|j2|jinja2?)$", re.I)
BEHAVIOUR_CONTENT = re.compile(
    r"system_prompt|SYSTEM_PROMPT|systemPrompt|[\"']role[\"']\s*:\s*[\"']system[\"']|"
    r"role\s*=\s*[\"']system[\"']|\binstructions\s*=|@tool\b|@function_tool\b|"
    r"\btools\s*=\s*\[|\binput_schema\b|\bfunction_declarations\b|\bFunctionTool\b|"
    r"\bAgent\(|\bcreate_react_agent\b|\bStateGraph\(|\bmodel\s*=\s*[\"'][^\"']*"
    r"(claude|gpt|gemini|llama|mistral|sonnet|opus|haiku)",
)
SKIP_DIRS = ("node_modules/", ".git/", ".venv/", "venv/", "dist/", "build/", "__pycache__/",
             ".claude/", ".agents/", ".codex/", ".cursor/", ".gemini/", ".opencode/")
PATCH_FILE = re.compile(r"^\*\*\* (?:Add|Update) File: (.+)$", re.M)
SHELL_EVAL_BUILTIN = re.compile(r"(^|[;&|(]\s*)eval\s")
EVAL_COMMAND = re.compile(
    r"\b(promptfoo|deepeval|ragas|inspect\s+eval|braintrust\s+eval|evaluate)\b|"
    r"[\w/.\-]*evals?[\w/.\-]*", re.I)


def read_text(p: Path) -> str:
    try:
        if p.is_file() and p.stat().st_size <= MAX_FILE_BYTES:
            return p.read_text(errors="ignore")
    except OSError:
        pass
    return ""


def dep_names(root: Path) -> set[str]:
    """Lower-cased dependency names found in common manifest files (top level + one down)."""
    found: set[str] = set()
    dirs = [root]
    try:
        dirs += [d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")
                 and d.name not in ("node_modules", "venv", "dist", "build")][:40]
    except OSError:
        pass
    for d in dirs:
        for name in DEP_FILES:
            text = read_text(d / name)
            if not text:
                continue
            if name == "package.json":
                try:
                    pkg = json.loads(text)
                    for key in ("dependencies", "devDependencies", "peerDependencies"):
                        found.update(k.lower() for k in (pkg.get(key) or {}))
                except ValueError:
                    pass
            else:
                found.update(m.lower() for m in re.findall(r"[A-Za-z0-9_.\-@/]+", text))
    return found


def matches(deps: set[str], libs: set[str]) -> list[str]:
    hits = set()
    for dep in deps:
        base = re.split(r"[\[<>=~!;]", dep, maxsplit=1)[0]
        hits.update(lib for lib in libs if base == lib or base.startswith(lib + "-"))
    return sorted(hits)


def profile(root: Path) -> dict:
    deps = dep_names(root)
    art = root / ARTIFACT_DIR
    return {
        "llm": matches(deps, LLM_LIBS),
        "tracing": matches(deps, TRACING_LIBS),
        "eval_libs": matches(deps, EVAL_LIBS),
        "eval_paths": [p for p in EVAL_PATHS if (root / p).exists()],
        "artifacts": sorted(p.name for p in art.iterdir()) if art.is_dir() else None,
    }


def find_secret(text: str) -> str | None:
    for label, pattern in SECRET_PATTERNS:
        for m in re.finditer(pattern, text):
            window = text[max(0, m.start() - 20): m.end() + 5]
            if not PLACEHOLDER.search(m.group(0)) and "EXAMPLE" not in window:
                return label
    return None


def is_behaviour_change(path: str, text: str) -> bool:
    norm = path.replace("\\", "/")
    if any(s in norm for s in SKIP_DIRS) or f"{ARTIFACT_DIR}/" in norm:
        return False
    if BEHAVIOUR_PATH.search(norm):
        return True
    if norm.endswith((".md", ".txt", ".rst", ".lock", ".json")) and "prompt" not in norm.lower():
        return False
    return bool(BEHAVIOUR_CONTENT.search(text))


def is_eval_command(cmd: str) -> bool:
    cleaned = SHELL_EVAL_BUILTIN.sub(" ", cmd)
    return bool(EVAL_COMMAND.search(cleaned))


# --------------------------------------------------------------------------- state

def state_path(session: str) -> Path:
    d = Path(tempfile.gettempdir()) / "agent-engineer"
    d.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_\-]", "_", session)[:120] or "default"
    return d / f"{safe}.json"


def load_state(session: str) -> dict:
    p = state_path(session)
    try:
        if time.time() - p.stat().st_mtime < STATE_TTL_S:
            return json.loads(p.read_text())
    except (OSError, ValueError):
        pass
    return {"changes": [], "evals": 0, "reminded": False, "gated": False}


def save_state(session: str, state: dict) -> None:
    try:
        state_path(session).write_text(json.dumps(state))
    except OSError:
        pass


# --------------------------------------------------------------------------- payloads

def strings_in(obj, keys=("content", "new_string", "newString", "new_str", "text", "patch",
                          "input", "contents", "file_text")) -> str:
    """Collect text being written, across harness tool-input shapes."""
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and k in keys:
                out.append(v)
            elif isinstance(v, (dict, list)):
                out.append(strings_in(v, keys))
    elif isinstance(obj, list):
        out.extend(strings_in(v, keys) for v in obj)
    return "\n".join(s for s in out if s)


def first(d: dict, *keys, default=""):
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return default


class Event:
    def __init__(self, payload: dict):
        self.raw = payload
        self.session = str(first(payload, "session_id", "sessionId", "conversation_id",
                                 "thread_id", default=f"ppid-{os.getppid()}"))
        self.cwd = Path(first(payload, "cwd", "workspace_root", default=os.getcwd()))
        roots = payload.get("workspace_roots")
        if isinstance(roots, list) and roots:
            self.cwd = Path(roots[0])
        self.tool_input = first(payload, "tool_input", "toolInput", "args", "input",
                                default={}) or {}
        if isinstance(self.tool_input, str):
            try:
                self.tool_input = json.loads(self.tool_input)
            except ValueError:
                self.tool_input = {"input": self.tool_input}
        ti = self.tool_input if isinstance(self.tool_input, dict) else {}
        self.file_path = str(first(ti, "file_path", "filePath", "path", "absolute_path",
                                   default=first(payload, "file_path", default="")))
        self.command = str(first(ti, "command", "cmd", default=first(payload, "command",
                                                                    default="")))
        if isinstance(ti.get("command"), list):
            self.command = " ".join(map(str, ti["command"]))
        self.write_text = strings_in(self.tool_input) or strings_in(payload.get("edits", []))
        if "*** Begin Patch" in self.command:  # Codex apply_patch passes the patch as a command
            self.write_text = f"{self.write_text}\n{self.command}"
        self.file_paths = [self.file_path] if self.file_path else []
        self.file_paths += [m.strip() for m in PATCH_FILE.findall(self.write_text)
                            if m.strip() not in self.file_paths]
        self.stop_active = bool(payload.get("stop_hook_active") or payload.get("loop_count"))


# --------------------------------------------------------------------------- outputs

def emit(harness: str, event: str, *, context: str = "", deny: str = "",
         block: str = "") -> None:
    """Print the harness-specific output. Exactly one of context/deny/block is set."""
    out: dict | None = None
    if harness in ("claude", "codex"):
        name = {"session-start": "SessionStart", "pre-write": "PreToolUse",
                "post-write": "PostToolUse", "post-bash": "PostToolUse"}.get(event)
        if deny:
            out = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                          "permissionDecision": "deny",
                                          "permissionDecisionReason": deny}}
        elif block:
            out = {"decision": "block", "reason": block}
        elif context and name:
            out = {"hookSpecificOutput": {"hookEventName": name, "additionalContext": context}}
    elif harness == "gemini":
        name = {"session-start": "SessionStart", "post-write": "AfterTool",
                "post-bash": "AfterTool"}.get(event)
        if deny:
            out = {"decision": "deny", "reason": deny}
        elif block:  # AfterAgent: "deny" makes Gemini retry with the reason as a new prompt
            out = {"decision": "deny", "reason": block}
        elif context and name:
            out = {"hookSpecificOutput": {"hookEventName": name, "additionalContext": context}}
    elif harness == "cursor":
        if deny:
            out = {"permission": "deny", "user_message": deny, "agent_message": deny}
        elif block:
            out = {"followup_message": block}
        elif context:
            out = {"additional_context": context}
    else:  # opencode plugin and anything else: plain JSON the caller interprets
        out = {"context": context or None, "deny": deny or None, "block": block or None}
    if out:
        sys.stdout.write(json.dumps(out))


# --------------------------------------------------------------------------- handlers

def on_session_start(ev: Event) -> dict:
    p = profile(ev.cwd)
    if not p["llm"] and p["artifacts"] is None:
        return {}
    lines = ["[agent-engineer] This project builds on LLMs. For any work on the agent's "
             "behaviour, design, prompts, tools, retrieval, evals, tracing or deployment, use "
             "the `agent-engineer` skill first — it routes to the specialised agent-* skills."]
    if p["llm"]:
        lines.append(f"- LLM libraries: {', '.join(p['llm'][:8])}")
    lines.append(f"- Tracing: {', '.join(p['tracing']) if p['tracing'] else 'none detected'}")
    evals = p["eval_libs"] + p["eval_paths"]
    lines.append(f"- Evals: {', '.join(evals) if evals else 'none detected'}")
    if p["artifacts"] is not None:
        lines.append(f"- {ARTIFACT_DIR}/: {', '.join(p['artifacts']) or 'empty'} "
                     "— read these before changing the agent.")
    gaps = []
    if not p["tracing"]:
        gaps.append("no tracing (see agent-observability)")
    if not evals:
        gaps.append("no evals (see agent-evals)")
    if gaps:
        lines.append(f"- Gaps: {'; '.join(gaps)}. Mention these before claiming any "
                     "behaviour change is an improvement.")
    return {"context": "\n".join(lines)}


def on_pre_write(ev: Event) -> dict:
    if os.environ.get("AE_SECRET_GUARD") == "off" or not ev.write_text:
        return {}
    target = ev.file_paths[0] if ev.file_paths else ""
    base = os.path.basename(target)
    if base.startswith(".env") and not re.search(r"example|sample|template", base, re.I):
        return {}
    label = find_secret(ev.write_text)
    if not label:
        return {}
    return {"deny": f"[agent-engineer secret-guard] This write to {target or 'a file'} contains "
                    f"what looks like a secret ({label}). Read it from an environment variable "
                    "or secret manager instead, and put real values only in a git-ignored "
                    ".env. If this is a real key, it is already in this session's transcript: "
                    "tell the user to revoke and reissue it. Set AE_SECRET_GUARD=off to bypass "
                    "if this is a false positive."}


def on_post_write(ev: Event) -> dict:
    changed = [p for p in ev.file_paths if is_behaviour_change(p, ev.write_text)]
    if not changed:
        return {}
    st = load_state(ev.session)
    st["changes"] += [p for p in changed if p not in st["changes"]]
    msg = {}
    if not st["reminded"]:
        st["reminded"] = True
        msg = {"context": f"[agent-engineer] {changed[0]} changes agent behaviour (prompt, "
                          "tools or agent config). Before calling this an improvement: run "
                          "the eval suite before/after and add an entry to "
                          f"{ARTIFACT_DIR}/experiment-log.md (see agent-accuracy)."}
    save_state(ev.session, st)
    return msg


def on_post_bash(ev: Event) -> dict:
    if ev.command and is_eval_command(ev.command):
        st = load_state(ev.session)
        st["evals"] += 1
        save_state(ev.session, st)
    return {}


def on_stop(ev: Event) -> dict:
    if os.environ.get("AE_EVAL_GATE") == "off" or ev.stop_active:
        return {}
    st = load_state(ev.session)
    if not st["changes"] or st["evals"] or st["gated"]:
        return {}
    st["gated"] = True
    save_state(ev.session, st)
    files = ", ".join(st["changes"][:5])
    return {"block": f"[agent-engineer eval-gate] Behaviour-changing files were edited this "
                     f"session ({files}) but no eval command ran. Run the eval suite and report "
                     "the before/after result, or tell the user explicitly that the change is "
                     "unevaluated and why. (This check fires once per session; disable with "
                     "AE_EVAL_GATE=off.)"}


HANDLERS = {"session-start": on_session_start, "pre-write": on_pre_write,
            "post-write": on_post_write, "post-bash": on_post_bash, "stop": on_stop}


def main(argv: list[str]) -> int:
    if os.environ.get("AE_HOOKS") == "off" or not argv or argv[0] not in HANDLERS:
        return 0
    event = argv[0]
    harness = argv[argv.index("--harness") + 1] if "--harness" in argv else "claude"
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        payload = {}
    try:
        result = HANDLERS[event](Event(payload if isinstance(payload, dict) else {}))
        if result:
            emit(harness, event, **result)
    except Exception:  # fail open: a broken hook must never break the user's session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
