// Spike: bridge pi's tool_call event to `holdspeak gate hook` (Claude-shaped PreToolUse payload).
import { spawn } from "node:child_process";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const HOOK = (process.env.HOLDSPEAK_GATE_HOOK_CMD ?? "").split(" ").filter(Boolean);

function runHook(payload: object): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(HOOK[0], HOOK.slice(1), { stdio: ["pipe", "pipe", "inherit"] });
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    child.on("error", reject);
    child.on("close", () => resolve(out));
    child.stdin.end(JSON.stringify(payload));
  });
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return undefined;
    const started = Date.now();
    const out = await runHook({
      hook_event_name: "PreToolUse",
      tool_name: "Bash",
      tool_input: { command: (event.input as any).command },
      tool_use_id: event.toolCallId,
      session_id: "pi-spike-session",
      cwd: ctx.cwd,
    });
    const secs = ((Date.now() - started) / 1000).toFixed(1);
    if (!out.trim()) { console.error(`[gate] allow after ${secs}s`); return undefined; }
    const reason = JSON.parse(out)?.hookSpecificOutput?.permissionDecisionReason ?? "held by HoldSpeak";
    console.error(`[gate] BLOCK after ${secs}s: ${reason}`);
    return { block: true, reason };
  });
}
