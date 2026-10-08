"""Tests for hooks/ae_hook.py. Run: python3 -m unittest discover -s tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "ae_hook.py"
sys.path.insert(0, str(HOOK.parent))
import ae_hook  # noqa: E402


def run(event, payload, harness="claude", env=None):
    proc = subprocess.run(
        [sys.executable, str(HOOK), event, "--harness", harness],
        input=json.dumps(payload), capture_output=True, text=True, timeout=10,
        env={**os.environ, **(env or {})},
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout) if proc.stdout.strip() else None


class SessionStart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_silent_for_non_llm_project(self):
        (self.root / "package.json").write_text('{"dependencies": {"react": "18"}}')
        self.assertIsNone(run("session-start", {"cwd": str(self.root)}))

    def test_profiles_llm_project_and_reports_gaps(self):
        (self.root / "pyproject.toml").write_text(
            '[project]\ndependencies = ["anthropic>=0.40", "langchain-openai"]\n')
        out = run("session-start", {"cwd": str(self.root)})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("anthropic", ctx)
        self.assertIn("langchain", ctx)
        self.assertIn("no tracing", ctx)
        self.assertIn("no evals", ctx)
        self.assertNotIn("skill first", ctx)  # a profile, not an order to load the skill

    def test_detects_js_deps_tracing_and_artifacts(self):
        (self.root / "package.json").write_text(json.dumps({
            "dependencies": {"@anthropic-ai/sdk": "1", "langfuse": "3"}}))
        (self.root / "evals").mkdir()
        (self.root / "agent-engineering").mkdir()
        (self.root / "agent-engineering" / "design.md").write_text("x")
        ctx = run("session-start", {"cwd": str(self.root)})["hookSpecificOutput"][
            "additionalContext"]
        self.assertIn("Tracing: langfuse", ctx)
        self.assertIn("Evals: evals", ctx)
        self.assertIn("design.md", ctx)
        self.assertNotIn("Gaps", ctx)

    def test_falls_back_to_imports_without_a_manifest(self):
        (self.root / "agent.py").write_text("import os\nfrom anthropic import Anthropic\n")
        (self.root / "ui.ts").write_text('import { generateText } from "@ai-sdk/openai";\n')
        ctx = run("session-start", {"cwd": str(self.root)})["hookSpecificOutput"][
            "additionalContext"]
        self.assertIn("anthropic", ctx)
        self.assertIn("@ai-sdk/openai", ctx)

    def test_import_fallback_stays_silent_for_non_llm_code(self):
        (self.root / "app.py").write_text("import requests\nfrom flask import Flask\n")
        self.assertIsNone(run("session-start", {"cwd": str(self.root)}))


class SecretGuard(unittest.TestCase):
    def payload(self, path, content):
        return {"session_id": str(uuid.uuid4()),
                "tool_input": {"file_path": path, "content": content}}

    def test_denies_real_looking_key(self):
        out = run("pre-write", self.payload("app.py", 'k = "sk-ant-api03-' + "a1B2" * 8 + '"'))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allows_placeholder_and_dotenv(self):
        self.assertIsNone(run("pre-write", self.payload("app.py", 'k = "sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"')))
        self.assertIsNone(run("pre-write", self.payload(".env", "AWS=AKIAABCDEFGHIJKLMNOP")))

    def test_blocks_dotenv_example(self):
        out = run("pre-write", self.payload(".env.example", "AWS=AKIAABCDEFGHIJKLMNOP"))
        self.assertIsNotNone(out)

    def test_can_be_disabled(self):
        out = run("pre-write", self.payload("a.py", "AKIAABCDEFGHIJKLMNOP"),
                  env={"AE_SECRET_GUARD": "off"})
        self.assertIsNone(out)


class EvalGate(unittest.TestCase):
    def setUp(self):
        self.sid = f"test-{uuid.uuid4()}"
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        ae_hook.state_path(self.sid).unlink(missing_ok=True)
        self.tmp.cleanup()

    def write(self, path, text):
        return run("post-write", {"session_id": self.sid, "cwd": str(self.root),
                                  "tool_input": {"file_path": path, "new_string": text}})

    def edit_on_disk(self, name, content, new_string):
        """Simulate an Edit whose result is already on disk (PostToolUse runs after the write)."""
        (self.root / name).write_text(content)
        return self.write(str(self.root / name), new_string)

    def test_wording_only_prompt_edit_triggers(self):
        out = self.edit_on_disk("agent.py", 'SYSTEM_PROMPT = (\n    "You are a friendly agent."\n)\n',
                                '"You are a friendly agent."')
        self.assertIn("changes agent behaviour", out["hookSpecificOutput"]["additionalContext"])

    def test_wording_only_edit_in_relative_path_triggers(self):
        (self.root / "src").mkdir()
        (self.root / "src" / "bot.py").write_text('client.messages.create(\n    system="Be brief.",\n)\n')
        self.assertIsNotNone(self.write("src/bot.py", '"Be brief."'))

    def test_edit_far_from_any_prompt_does_not_trigger(self):
        body = 'SYSTEM_PROMPT = "x"\n' + "\n".join(f"v{i} = {i}" for i in range(100)) + "\n"
        self.assertIsNone(self.edit_on_disk("agent.py", body, "v99 = 99"))

    def test_tool_docstring_wording_edit_triggers(self):
        out = self.edit_on_disk("tools.py", '@tool\ndef lookup(order_id: str):\n    """Find an order by ID."""\n',
                                '"""Find an order by ID."""')
        self.assertIsNotNone(out)

    def test_unrelated_edit_near_agent_construction_does_not_trigger(self):
        body = 'agent = Agent(model=m)\nlog = get_logger("app")\n'
        self.assertIsNone(self.edit_on_disk("main.py", body, 'log = get_logger("app")'))

    def test_common_prompt_spellings_trigger(self):
        for text in ('SYSTEM = "You are a support agent."', 'system="Be brief."',
                     "generateText({ system: prompt })", '{"system": "Be brief."}'):
            with self.subTest(text=text):
                self.assertTrue(ae_hook.is_behaviour_change("agent.py", text))
        for text in ('FILESYSTEM = "/tmp"', "if system == 'linux':", 'os.system("ls")'):
            with self.subTest(text=text):
                self.assertFalse(ae_hook.is_behaviour_change("agent.py", text))

    def test_remind_once_then_gate_once(self):
        first = self.write("src/prompts/system.md", "You are a support agent.")
        self.assertIn("eval", first["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.write("src/agent.py", "SYSTEM_PROMPT = '...'"))
        stop = run("stop", {"session_id": self.sid})
        self.assertEqual(stop["decision"], "block")
        self.assertIsNone(run("stop", {"session_id": self.sid}))

    def test_eval_run_clears_gate(self):
        self.write("src/agent.py", "tools = [search, lookup]")
        run("post-bash", {"session_id": self.sid, "tool_input": {"command": "pytest tests/evals"}})
        self.assertIsNone(run("stop", {"session_id": self.sid}))

    def test_ordinary_edits_do_not_trigger(self):
        self.assertIsNone(self.write("src/utils.py", "def add(a, b): return a + b"))
        self.assertIsNone(self.write("README.md", "system_prompt is documented here"))
        self.assertIsNone(run("stop", {"session_id": self.sid}))

    def test_respects_stop_hook_active(self):
        self.write("prompts/x.md", "hi")
        self.assertIsNone(run("stop", {"session_id": self.sid, "stop_hook_active": True}))


class Robustness(unittest.TestCase):
    def test_garbage_input_fails_open(self):
        proc = subprocess.run([sys.executable, str(HOOK), "stop"], input="not json",
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_unknown_event_is_noop(self):
        self.assertIsNone(run("nope", {}))

    def test_shell_eval_builtin_is_not_an_eval(self):
        self.assertFalse(ae_hook.is_eval_command('eval "$(ssh-agent -s)"'))
        self.assertTrue(ae_hook.is_eval_command("npm run eval"))

    def test_eval_commands(self):
        for cmd in ("pytest tests/evals", "uv run python run_evals.py", "promptfoo eval",
                    "deepeval test run test_agent.py", "cd evals && python run.py",
                    "OPENAI_API_KEY=x python -m evals.harness", "make evaluate"):
            with self.subTest(cmd=cmd):
                self.assertTrue(ae_hook.is_eval_command(cmd))

    def test_looking_at_evals_is_not_running_them(self):
        for cmd in ("python retrieval.py", "cat evals/README.md", "ls evals", "grep -rn eval .",
                    "git add evals/", "pytest tests/test_retrieval.py", "cd evals && ls",
                    "python medieval.py"):
            with self.subTest(cmd=cmd):
                self.assertFalse(ae_hook.is_eval_command(cmd))


if __name__ == "__main__":
    unittest.main()
