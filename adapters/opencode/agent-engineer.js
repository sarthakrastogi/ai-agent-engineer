// agent-engineer plugin for OpenCode (experimental).
//
// OpenCode has no shell-hook contract, so this plugin calls the same hooks/ae_hook.py the
// other harnesses use and maps its generic JSON ({context, deny, block}) onto OpenCode's
// in-process hooks:
//   session-start → experimental.chat.system.transform (append profile to the system prompt)
//   pre-write     → tool.execute.before (throw to deny)
//   post-write    → tool.execute.after  (append reminder to the tool result)
//   post-bash     → tool.execute.after
//   stop          → event "session.idle" (send the eval-gate prompt once)
// Every call fails open: if Python or the hook breaks, the session carries on.

import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const HOOK = join(ROOT, "hooks", "ae_hook.py");
const PYTHON = process.env.AE_PYTHON || "python3";
const WRITE_TOOLS = new Set(["write", "edit", "patch", "apply_patch", "multiedit"]);

function runHook(event, payload) {
  try {
    const r = spawnSync(PYTHON, [HOOK, event, "--harness", "opencode"], {
      input: JSON.stringify(payload),
      encoding: "utf8",
      timeout: 5000,
    });
    return r.status === 0 && r.stdout ? JSON.parse(r.stdout) : {};
  } catch {
    return {};
  }
}

export const AgentEngineer = async ({ client, directory }) => {
  const profiles = new Map(); // sessionID -> session-start context (or null)
  const argsByCall = new Map(); // callID -> tool args, for tool.execute.after

  return {
    "experimental.chat.system.transform": async (input, output) => {
      const sid = input?.sessionID ?? "default";
      if (!profiles.has(sid)) {
        profiles.set(sid, runHook("session-start", { session_id: sid, cwd: directory }).context ?? null);
      }
      const ctx = profiles.get(sid);
      if (ctx && Array.isArray(output?.system)) output.system.push(ctx);
    },

    "tool.execute.before": async (input, output) => {
      if (!WRITE_TOOLS.has(input.tool) && input.tool !== "bash") return;
      argsByCall.set(input.callID, output.args);
      if (!WRITE_TOOLS.has(input.tool)) return;
      const r = runHook("pre-write", { session_id: input.sessionID, cwd: directory, tool_input: output.args });
      if (r.deny) throw new Error(r.deny);
    },

    "tool.execute.after": async (input, output) => {
      const args = argsByCall.get(input.callID);
      argsByCall.delete(input.callID);
      const event = input.tool === "bash" ? "post-bash" : WRITE_TOOLS.has(input.tool) ? "post-write" : null;
      if (!event || !args) return;
      const r = runHook(event, { session_id: input.sessionID, cwd: directory, tool_input: args });
      if (r.context && typeof output?.output === "string") output.output += `\n\n${r.context}`;
    },

    event: async ({ event }) => {
      if (event?.type !== "session.idle") return;
      const sid = event.properties?.sessionID;
      if (!sid) return;
      const r = runHook("stop", { session_id: sid, cwd: directory });
      if (!r.block) return;
      try {
        await client.session.prompt({ path: { id: sid }, body: { parts: [{ type: "text", text: r.block }] } });
      } catch {
        // fail open
      }
    },
  };
};
