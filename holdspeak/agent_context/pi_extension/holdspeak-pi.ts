// HoldSpeak's pi extension: the tool gate and the rider hooks for one pi launch.
//
// pi has no hook file. Every pi launch HoldSpeak makes passes this file with
// `-e` and writes `holdspeak.json` in the launch's own PI_CODING_AGENT_DIR
// (`holdspeak/agent_context/hooks.py`, `pi_hook_template`). That document names
// two commands, each an argv list run with no shell:
//
// - gate  (`holdspeak gate hook --agent pi`): PreToolUse on `tool_call`. A deny
//   blocks the call with its reason. Any failure blocks the call too (fail
//   closed): no document, a command that does not start, a non-zero exit, a
//   timeout, output that is not the deny shape.
// - rider (`holdspeak agent-hook ingest --agent pi`): SessionStart, UserPromptSubmit,
//   PostToolUse (the heartbeat), Stop (with `last_assistant_message`), SessionEnd.
//
// Each payload has the Claude Code shape the commands already read. pi's tools
// `bash`, `edit` and `write` go to the gate as `Bash`, `Edit` and `Write`; an MCP
// tool keeps its own name. pi's read-only tools (`read`, `grep`, `find`, `ls`) are
// not sent. Children stay in pi's process group, so a launch Stop that kills the
// group also kills a hook that waits on a hold (pi spike #1020).
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";

type Hook = { argv: string[]; events: string[]; timeout_seconds: number };
type HookDocument = {
  holdspeak_pi_schema: number;
  tools: Record<string, string>;
  read_tools: string[];
  rider?: Hook;
  gate?: Hook;
};
type Ran = { code: number | null; stdout: string };

const SCHEMA = 1;
const DOCUMENT = "holdspeak.json";
// Codex clamps its SessionEnd hooks to 3 s; pi waits as long for its own.
const SHUTDOWN_SECONDS = 3;

function readDocument(): HookDocument | null {
  const dir = process.env.PI_CODING_AGENT_DIR;
  if (!dir) return null;
  try {
    const doc = JSON.parse(readFileSync(join(dir, DOCUMENT), "utf8")) as HookDocument;
    if (!doc || doc.holdspeak_pi_schema !== SCHEMA) return null;
    return doc;
  } catch {
    return null;
  }
}

function run(argv: string[], payload: object, timeoutSeconds: number): Promise<Ran> {
  return new Promise((resolve, reject) => {
    if (!Array.isArray(argv) || argv.length === 0) {
      reject(new Error("no command"));
      return;
    }
    const child = spawn(argv[0], argv.slice(1), { stdio: ["pipe", "pipe", "ignore"] });
    let stdout = "";
    let done = false;
    const timer = setTimeout(() => {
      if (done) return;
      done = true;
      child.kill("SIGKILL");
      reject(new Error(`timed out after ${timeoutSeconds} s`));
    }, Math.max(1, timeoutSeconds) * 1000);
    child.stdout.on("data", (chunk) => (stdout += chunk));
    child.on("error", (error) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      resolve({ code, stdout });
    });
    child.stdin.on("error", () => {});
    child.stdin.end(JSON.stringify(payload));
  });
}

// A gate proposal id is a URL path segment: pi's nested call ids hold `/`.
function callId(id: string): string {
  return String(id || "").replace(/[^A-Za-z0-9._:-]/g, "-");
}

// The Claude Code input shape the gate rules read (`file_path` for a write).
function toolInput(toolName: string, input: Record<string, unknown>): Record<string, unknown> {
  if (toolName === "bash") return { command: input?.command };
  if (toolName === "edit") return { file_path: input?.path, edits: input?.edits };
  if (toolName === "write") return { file_path: input?.path, content: input?.content };
  return input ?? {};
}

// The model's last words of the turn. A local model can leak its thinking tags.
function lastAssistantText(messages: any[]): string {
  const last = [...(messages ?? [])].reverse().find((m) => m?.role === "assistant");
  const text = (last?.content ?? [])
    .filter((c: any) => c?.type === "text")
    .map((c: any) => String(c.text ?? ""))
    .join("\n");
  return text.replace(/<think>[\s\S]*?<\/think>/g, "").replace(/<\/?think>/g, "").trim();
}

// pi's session reasons in Claude Code's words (`coder_gate.SESSION_END_KEEPS_CREDENTIAL`).
function startSource(reason: string): string {
  return reason === "startup" ? "startup" : reason === "new" ? "clear" : "resume";
}
function endReason(reason: string): string {
  return reason === "quit" ? "prompt_input_exit" : reason === "new" ? "clear" : "resume";
}

export default function holdspeakPi(pi: any) {
  const doc = readDocument();
  let queue: Promise<unknown> = Promise.resolve();

  function session(ctx: any) {
    return {
      session_id: String(ctx?.sessionManager?.getSessionId?.() ?? "") || "unknown-session",
      transcript_path: ctx?.sessionManager?.getSessionFile?.() ?? null,
      cwd: ctx?.cwd ?? process.cwd(),
    };
  }

  // One rider event at a time, in order; pi never waits for the rider.
  function rider(event: string, ctx: any, fields: object): Promise<unknown> {
    const hook = doc?.rider;
    if (!hook || !hook.events.includes(event)) return queue;
    const payload = { hook_event_name: event, ...session(ctx), ...fields };
    queue = queue.then(() => run(hook.argv, payload, hook.timeout_seconds)).catch(() => undefined);
    return queue;
  }

  // A gate event that is not PreToolUse: telemetry and the session credential.
  function gateNote(event: string, ctx: any, fields: object, timeoutSeconds?: number): Promise<unknown> {
    const hook = doc?.gate;
    if (!hook || !hook.events.includes(event)) return Promise.resolve();
    const payload = { hook_event_name: event, ...session(ctx), ...fields };
    return run(hook.argv, payload, timeoutSeconds ?? hook.timeout_seconds).catch(() => undefined);
  }

  pi.on("session_start", async (event: any, ctx: any) => {
    const fields = { source: startSource(String(event?.reason ?? "startup")) };
    void gateNote("SessionStart", ctx, fields);
    void rider("SessionStart", ctx, fields);
    return undefined;
  });

  pi.on("before_agent_start", async (event: any, ctx: any) => {
    void rider("UserPromptSubmit", ctx, { prompt: String(event?.prompt ?? "") });
    return undefined;
  });

  pi.on("tool_call", async (event: any, ctx: any) => {
    const name = String(event?.toolName ?? "");
    if (doc && doc.read_tools.includes(name)) return undefined;
    const hook = doc?.gate;
    if (!hook) {
      return { block: true, reason: "HoldSpeak gate not configured for this launch; the call was not run" };
    }
    const payload = {
      hook_event_name: "PreToolUse",
      tool_name: doc!.tools[name] ?? name,
      tool_input: toolInput(name, event?.input ?? {}),
      tool_use_id: callId(event?.toolCallId),
      ...session(ctx),
    };
    let ran: Ran;
    try {
      ran = await run(hook.argv, payload, hook.timeout_seconds);
    } catch (error: any) {
      return { block: true, reason: `HoldSpeak gate failed (${error?.message ?? "error"}); the call was not run` };
    }
    if (ran.code !== 0) {
      return { block: true, reason: `HoldSpeak gate failed (exit ${ran.code}); the call was not run` };
    }
    const text = ran.stdout.trim();
    if (!text) return undefined; // no opinion: the call runs
    try {
      const out = JSON.parse(text)?.hookSpecificOutput;
      const reason = String(out?.permissionDecisionReason ?? "").trim();
      if (out?.permissionDecision === "deny" && reason) return { block: true, reason };
    } catch {
      // not the deny shape: fail closed below
    }
    return { block: true, reason: "HoldSpeak gate answered in an unknown form; the call was not run" };
  });

  pi.on("tool_result", async (event: any, ctx: any) => {
    const name = String(event?.toolName ?? "");
    const mapped = doc?.tools[name] ?? name;
    const fields = {
      tool_name: mapped,
      tool_input: toolInput(name, event?.input ?? {}),
      tool_use_id: callId(event?.toolCallId),
    };
    if (!event?.isError && !(doc?.read_tools ?? []).includes(name)) void gateNote("PostToolUse", ctx, fields, 15);
    void rider("PostToolUse", ctx, fields);
    return undefined;
  });

  pi.on("agent_end", async (event: any, ctx: any) => {
    const last = [...(event?.messages ?? [])].reverse().find((m: any) => m?.role === "assistant");
    void rider("Stop", ctx, {
      stop_reason: last?.stopReason ?? null,
      last_assistant_message: lastAssistantText(event?.messages ?? []),
    });
    return undefined;
  });

  pi.on("session_shutdown", async (event: any, ctx: any) => {
    const fields = { reason: endReason(String(event?.reason ?? "quit")) };
    const ended = Promise.all([gateNote("SessionEnd", ctx, fields, SHUTDOWN_SECONDS), rider("SessionEnd", ctx, fields)]);
    const cap = new Promise((resolve) => setTimeout(resolve, SHUTDOWN_SECONDS * 1000));
    await Promise.race([ended, cap]);
    return undefined;
  });
}
