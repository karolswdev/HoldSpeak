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
// tool keeps its own name. pi's read-only tools (`read`, `grep`, `find`, `ls`)
// pass with no hook when the path they name resolves (symlinks too) inside the
// launch's worktree; a path outside it goes to the gate as `Read` with
// `file_path`, where the outside-the-worktree hold applies (PR #1022 r1). Children stay in pi's process group, so a launch Stop that kills the
// group also kills a hook that waits on a hold (pi spike #1020).
import { spawn } from "node:child_process";
import { existsSync, readFileSync, realpathSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

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

// The real path of `path` (symlinks resolved); a path that does not exist yet
// resolves through its nearest existing folder.
function realPath(path: string): string {
  try {
    return realpathSync(path);
  } catch {
    const parent = dirname(path);
    return parent === path ? path : join(realPath(parent), basename(path));
  }
}

// A path the way pi's own tools resolve it (`expandPath` / `resolveToCwd` in
// pi's core/tools/path-utils.js): its odd spaces made plain, a leading `@`
// dropped, `~` expanded, a `file://` URL read. Astra's post-merge check
// (2026-11-01): `@/outside/file` was checked as a folder named `@` in the
// worktree while pi read the outside file.
const PI_ODD_SPACES = /[\u00A0\u2000-\u200A\u202F\u205F\u3000]/g;
function piPath(raw: string): string {
  let path = String(raw ?? "").replace(PI_ODD_SPACES, " ");
  if (path.startsWith("@")) path = path.slice(1);
  if (path === "~") return homedir();
  if (path.startsWith("~/")) return join(homedir(), path.slice(2));
  if (/^file:\/\//.test(path)) {
    try {
      return fileURLToPath(path);
    } catch {
      return path;
    }
  }
  return path;
}

// The other names pi's read tool tries when a path does not exist (its
// `resolveReadPath`): each one is checked as well.
function piVariants(path: string): string[] {
  const amPm = path.replace(/ (AM|PM)\./gi, "\u202F$1.");
  const nfd = path.normalize("NFD");
  const curly = path.replace(/'/g, "\u2019");
  return [path, amPm, nfd, curly, nfd.replace(/'/g, "\u2019")].filter((p, i, all) => all.indexOf(p) === i);
}

// The absolute path a read tool names (its `path`; none: the working folder).
function readTarget(input: Record<string, unknown>, cwd: string): string {
  const raw = typeof input?.path === "string" && input.path.trim() ? (input.path as string) : ".";
  return resolve(cwd, piPath(raw));
}

// Inside when the path and every name pi may read in its place resolve inside.
function readInside(target: string, cwd: string): boolean {
  const root = realPath(cwd);
  return piVariants(target).every((p) => (p === target || existsSync(p) ? inside(realPath(p), root) : true));
}

function inside(path: string, root: string): boolean {
  return path === root || path.startsWith(root.endsWith(sep) ? root : root + sep);
}

// A gate proposal id is a URL path segment: pi's nested call ids hold `/`.
function callId(id: string): string {
  return String(id || "").replace(/[^A-Za-z0-9._:-]/g, "-");
}

// The Claude Code input shape the gate rules read (`file_path` for a write).
function toolInput(toolName: string, input: Record<string, unknown>): Record<string, unknown> {
  if (toolName === "bash") return { command: input?.command };
  // The gate reads the path pi will write (a leading `@`, `~`, a file URL).
  const path = typeof input?.path === "string" ? piPath(input.path as string) : input?.path;
  if (toolName === "edit") return { file_path: path, edits: input?.edits };
  if (toolName === "write") return { file_path: path, content: input?.content };
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
  // The read calls that went to the gate (outside the worktree): their
  // completion is reported as the same `Read` call.
  const outsideReads = new Set<string>();

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
    const readTools = doc?.read_tools ?? ["read", "grep", "find", "ls"];
    let toolName = doc?.tools[name] ?? name;
    let input = toolInput(name, event?.input ?? {});
    if (readTools.includes(name)) {
      const cwd = ctx?.cwd ?? process.cwd();
      const target = readTarget(event?.input ?? {}, cwd);
      if (readInside(target, cwd)) return undefined; // inside the worktree
      toolName = "Read";
      input = { file_path: target };
      outsideReads.add(callId(event?.toolCallId));
    }
    const hook = doc?.gate;
    if (!hook) {
      return { block: true, reason: "HoldSpeak gate not configured for this launch; the call was not run" };
    }
    const payload = {
      hook_event_name: "PreToolUse",
      tool_name: toolName,
      tool_input: input,
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
    const id = callId(event?.toolCallId);
    const fields = {
      tool_name: mapped,
      tool_input: toolInput(name, event?.input ?? {}),
      tool_use_id: id,
    };
    const outside = outsideReads.delete(id);
    const gated = outside || !(doc?.read_tools ?? []).includes(name);
    const gateFields = outside ? { ...fields, tool_name: "Read", tool_input: { file_path: readTarget(event?.input ?? {}, ctx?.cwd ?? process.cwd()) } } : fields;
    if (!event?.isError && gated) void gateNote("PostToolUse", ctx, gateFields, 15);
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
