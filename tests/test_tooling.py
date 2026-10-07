"""Tests for install.py, build_adapters.py and per-harness hook output shapes."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "scripts" / "install.py"
HOOK = ROOT / "hooks" / "ae_hook.py"
sys.path.insert(0, str(HOOK.parent))
import ae_hook  # noqa: E402


def sh(*args, cwd=None, payload=None):
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, capture_output=True,
                          text=True, input=json.dumps(payload) if payload is not None else None,
                          timeout=30)


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, harness, *extra):
        r = sh(INSTALL, "--harness", harness, "--project-dir", self.proj, *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_every_harness_installs_idempotently_and_uninstalls_cleanly(self):
        for harness in ("claude", "codex", "cursor", "opencode", "gemini"):
            with self.subTest(harness=harness):
                self.install(harness)
                self.assertIn("nothing to do", self.install(harness))
                self.install(harness, "--uninstall")
                leftovers = [p for p in self.proj.rglob("*") if p.is_symlink()]
                self.assertEqual(leftovers, [])

    def test_user_hooks_are_preserved(self):
        cfg = self.proj / ".claude" / "settings.json"
        cfg.parent.mkdir(parents=True)
        mine = {"permissions": {"allow": ["Bash(ls)"]},
                "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo mine"}]}]}}
        cfg.write_text(json.dumps(mine))
        self.install("claude")
        data = json.loads(cfg.read_text())
        self.assertEqual(data["permissions"], mine["permissions"])
        self.assertEqual(len(data["hooks"]["Stop"]), 2)
        self.assertIn(str(ROOT), json.dumps(data["hooks"]))
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", json.dumps(data["hooks"]))
        self.install("claude", "--uninstall")
        self.assertEqual(json.loads(cfg.read_text()), mine)

    def test_gemini_hooks_use_ms_timeouts_and_absolute_paths(self):
        self.install("gemini")
        hooks = json.loads((self.proj / ".gemini" / "settings.json").read_text())["hooks"]
        h = hooks["BeforeTool"][0]["hooks"][0]
        self.assertGreaterEqual(h["timeout"], 1000)
        self.assertIn(str(ROOT), h["command"])

    def test_refuses_to_install_into_pack_checkout(self):
        r = sh(INSTALL, "--harness", "codex", "--project-dir", ROOT)
        self.assertNotEqual(r.returncode, 0)


class Adapters(unittest.TestCase):
    def test_generated_adapters_are_in_sync(self):
        r = sh(ROOT / "scripts" / "build_adapters.py", "--check")
        self.assertEqual(r.returncode, 0, r.stdout)


class HarnessShapes(unittest.TestCase):
    SECRET = 'k = "sk-ant-api03-' + "a1B2" * 8 + '"'

    def setUp(self):
        self.sids = []

    def tearDown(self):
        for sid in self.sids:
            ae_hook.state_path(sid).unlink(missing_ok=True)

    def sid(self):
        self.sids.append(f"t-{uuid.uuid4()}")
        return self.sids[-1]

    def hook(self, event, harness, payload):
        r = sh(HOOK, event, "--harness", harness, payload=payload)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout else None

    def test_deny_shapes(self):
        p = {"tool_input": {"file_path": "a.py", "content": self.SECRET}}
        self.assertEqual(self.hook("pre-write", "codex", p)["hookSpecificOutput"]
                         ["permissionDecision"], "deny")
        self.assertEqual(self.hook("pre-write", "cursor", p)["permission"], "deny")
        self.assertEqual(self.hook("pre-write", "gemini", p)["decision"], "deny")
        self.assertTrue(self.hook("pre-write", "opencode", p)["deny"])

    def test_codex_apply_patch_paths_and_gate(self):
        sid = self.sid()
        patch = ("*** Begin Patch\n*** Update File: src/prompts/system.txt\n@@\n-old\n+new\n"
                 "*** End Patch\n")
        out = self.hook("post-write", "codex",
                        {"session_id": sid, "tool_name": "apply_patch",
                         "tool_input": {"command": ["apply_patch", patch]}})
        self.assertIn("src/prompts/system.txt",
                      out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.hook("stop", "codex", {"session_id": sid})["decision"], "block")

    def test_cursor_and_gemini_stop_shapes(self):
        for harness, key in (("cursor", "followup_message"), ("gemini", "reason")):
            sid = self.sid()
            self.hook("post-write", harness, {"conversation_id": sid, "session_id": sid,
                                              "tool_input": {"file_path": "prompts/a.md",
                                                             "content": "x"}})
            out = self.hook("stop", harness, {"conversation_id": sid, "session_id": sid})
            self.assertIn(key, out)

    def test_cursor_session_start_uses_workspace_roots(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "requirements.txt").write_text("openai==1.50\n")
            out = self.hook("session-start", "cursor", {"workspace_roots": [d], "cwd": "/"})
            self.assertIn("openai", out["additional_context"])


if __name__ == "__main__":
    unittest.main()
