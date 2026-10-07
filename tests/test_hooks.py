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

    def tearDown(self):
        ae_hook.state_path(self.sid).unlink(missing_ok=True)

    def write(self, path, text):
        return run("post-write", {"session_id": self.sid,
                                  "tool_input": {"file_path": path, "new_string": text}})

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


if __name__ == "__main__":
    unittest.main()
