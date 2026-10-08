/** PHILO-14 C2 — the agent's lane: the wire of `GET /api/agent/launches/{id}/lane`
 * (`holdspeak/services/launch_lane.py`) and the pure maps from it to the faces
 * (the station track, the timeline, the PR card, the files).
 *
 * Every collection on the wire may be `{not_read: reason}`: it stays a
 * `NotRead` here and the face says so in one line; a failed read is never
 * an empty list. */
import { wireClock, wireDate } from "../surface/format";
import { windowName } from "../windowName";
import type { ObjectTone, Station, TimelineEntry } from "../surface";

export type NotRead = { not_read: string };

export function isNotRead(value: unknown): value is NotRead {
  return Boolean(value && typeof value === "object" && typeof (value as NotRead).not_read === "string");
}

export interface LaneLaunch {
  launch_id: string;
  state?: string | null;
  agent: "claude" | "codex" | string;
  origin_ref?: { kind?: string; id?: string } | null;
  branch?: string | null;
  worktree_path?: string | null;
  launched_at?: string | null;
  /** PHILO-15 B42: `sent` once the brief reached the agent; `pending` while
   * the launch waits for it (a start screen, a slow start). */
  instruction_state?: string | null;
  /** When the delivery receipt said the brief reached the agent. */
  brief_sent_at?: string | null;
  /** PHILO-15 B46: a Re-brief sent mid-turn, typed at the turn end (the first of the queue). */
  queued_rebrief?: LaneQueuedRebrief | null;
  /** The queued Re-briefs, oldest first (a small FIFO). */
  queued_rebriefs?: LaneQueuedRebrief[] | null;
  /** One terminal receipt per Re-brief press (Astra r2 on #996). */
  rebriefs?: LaneRebriefReceipt[] | null;
  control_mode?: string | null;
  brief_text?: string | null;
  session_key?: string | null;
  tmux_session?: string | null;
  /** The owner stopped the agent (kill route): when, and the audit row. */
  stopped?: { by?: string; at?: string; audit_id?: number | null; scope?: string } | null;
}

export interface LaneQueuedRebrief {
  id?: string | null;
  text?: string | null;
  at?: string | null;
  approved_at?: string | null;
}

/** A Re-brief's receipt: what became of the owner's press (`sent`,
 * `superseded`, `expired`), when he pressed, and the delivery's command id. */
export interface LaneRebriefReceipt {
  id?: string | null;
  state: "sent" | "superseded" | "expired" | string;
  text_head?: string | null;
  approved_at?: string | null;
  approved_by?: { kind?: string; identity?: string } | null;
  /** The press's own id (its approval). */
  press_id?: string | null;
  /** The delivery's `process.input` command id (derived from the press). */
  command_id?: string | null;
  receipt_id?: string | null;
  at?: string | null;
  how?: string | null;
  detail?: string | null;
}

export interface LaneCheck {
  name?: string;
  state?: string;
  url?: string;
}

export interface LanePR {
  number: number | null;
  /** PHILO-15 B50: the PR's own title (GitHub's). */
  title?: string | null;
  url?: string | null;
  state?: string | null;
  review_decision?: string | null;
  ci?: string | null;
  checks?: LaneCheck[];
}

export interface LaneFollowThrough {
  pr: LanePR | null;
  pr_state?: string | null;
  merged?: Record<string, unknown> | null;
  close?: unknown;
  cleanup?: unknown;
  done?: boolean;
}

export interface LaneDraft {
  verdict?: string;
  reason?: string;
  text?: string;
}

export interface LaneWait {
  question?: string | null;
  kind: "TO ANSWER" | "TO APPROVE" | "DECIDING" | string;
  started?: string | number | null;
  /** The hub's id of this wait: an answer names it (the steer route refuses
   * an answer to a wait that is not the current one). */
  wait_id?: string | null;
  draft?: LaneDraft | null;
  /** PHILO-15 B48: how the turn ended: a real question (`asks`), no
   * question (`idle`), or no question with the PR open (`done`). PHILO-15 15:
   * a turn end the responder read as not the owner's comes as kind `DONE` /
   * `IDLE` (no Needs you row). */
  turn_end?: "asks" | "idle" | "done" | string | null;
}

/** PHILO-15 15: the turn end the lane says instead of a wait (kind `DONE`,
 * `IDLE`: the responder hid it from Needs you), or null. */
export function turnEndWord(wait: LaneWait | null | undefined): "DONE" | "IDLE" | null {
  const kind = String(wait?.kind ?? "").toUpperCase();
  return kind === "DONE" || kind === "IDLE" ? kind : null;
}

/** How the lane may act on its session now (the route's `control`). */
export interface LaneControl {
  mode: string;
  armed: boolean;
  /** The steer policy lets the owner type without a grant (YOLO, registered pane). */
  direct: boolean;
  expires_in_seconds?: number | null;
  pane?: boolean;
  /** The registered pane (`%N`) the steer names (PHILO-15 B46). */
  pane_id?: string | null;
}

export interface LaneAnswer {
  id: number;
  ts?: string | number | null;
  outcome?: string | null;
  text_head?: string | null;
}

export interface LaneEvent {
  id: number;
  ts: string;
  event: string;
  tool?: string | null;
  head?: string | null;
  text?: string | null;
  detail?: Record<string, unknown>;
}

export interface LaneGated {
  id: string;
  tool?: string | null;
  args_head?: string | null;
  /** PHILO-14 A5 (`db.gate.command_view`): the shown command, whether the
   * hub holds it whole, and how many of its characters are missing. */
  args_shown?: string | null;
  args_cut?: boolean | null;
  args_hidden?: number | null;
  state: string;
  created_at?: number | string | null;
  decided_by?: string | null;
  decided_at?: number | string | null;
  /** PHILO-15 15: why the call waits (`OUTSIDE THE WORKTREE · /tmp/x`). */
  hold_reason?: string | null;
  /** PHILO-15 15 (B45): the Control mode did not pass it at once. A call the
   * mode passed is a run, not a hold (absent: an older hub; read as held). */
  was_held?: boolean | null;
}

export interface LaneCommit {
  sha: string;
  at?: number | null;
  subject?: string;
}

export interface LaneFile {
  status?: string;
  path: string;
  from?: string;
}

export interface LaneWorktree {
  base?: string | null;
  branch?: string | null;
  commits: LaneCommit[];
  files: LaneFile[];
  uncommitted?: { staged?: number; modified?: number; untracked?: number } | NotRead;
}

export interface LaneWire {
  launch: LaneLaunch;
  session?: unknown;
  follow_through: LaneFollowThrough;
  wait: LaneWait | null | NotRead;
  events: LaneEvent[] | NotRead;
  events_next_after: number | null;
  gated: LaneGated[] | NotRead;
  answers?: LaneAnswer[] | NotRead;
  attempt_events?: unknown[] | NotRead;
  worktree: LaneWorktree | NotRead;
  usage?: unknown;
  control?: LaneControl | NotRead;
}

/** Each collection of the lane that could not be read, as `[PART, reason]`
 * (one honest line each on the face; never dropped). */
export function unreadParts(lane: LaneWire): Array<[string, string]> {
  const parts: Array<[string, unknown]> = [
    ["SESSION", lane.session],
    ["ANSWERS", lane.answers],
    ["ATTEMPT", lane.attempt_events],
    ["USAGE", lane.usage],
    ["CONTROL", lane.control],
  ];
  return parts.filter(([, v]) => isNotRead(v)).map(([k, v]) => [k, (v as NotRead).not_read]);
}

/* ── words ───────────────────────────────────────────────────────── */

const AGENT_NAME: Record<string, string> = { claude: "Claude Code", codex: "Codex" };

/** The agent's name as the face says it (`Claude Code`, `Codex`). */
export function agentName(agent: string | null | undefined): string {
  const key = String(agent ?? "").toLowerCase();
  return AGENT_NAME[key] ?? (key ? key.charAt(0).toUpperCase() + key.slice(1) : "Agent");
}

/** The time a wait has run, `6 min` (`1 min` under two minutes; `2 h` past two hours). */
export function waitAge(started: unknown, now: number = Date.now()): string {
  const date = wireDate(started);
  if (!date) return "";
  const minutes = Math.max(0, Math.floor((now - date.getTime()) / 60_000));
  if (minutes < 2) return "1 min";
  if (minutes < 120) return `${minutes} min`;
  return `${Math.floor(minutes / 60)} h`;
}

/** The PR's review as words: `NONE YET`, `APPROVED`, `CHANGES ASKED`. */
export function reviewWord(decision: string | null | undefined): string {
  switch (String(decision ?? "").toUpperCase()) {
    case "APPROVED":
      return "APPROVED";
    case "CHANGES_REQUESTED":
      return "CHANGES ASKED";
    case "REVIEW_REQUIRED":
      return "ASKED";
    default:
      return "NONE YET";
  }
}

const PASSED = new Set(["success", "neutral", "skipped"]);
const RUNNING = new Set(["in_progress", "queued", "pending", "waiting", "expected", "requested", ""]);

/** `CHECKS n OF m`, the running and the failed counts. */
export function checksSummary(checks: readonly LaneCheck[] | undefined): {
  passed: number;
  total: number;
  failed: number;
  running: number;
} | undefined {
  if (!checks || checks.length === 0) return undefined;
  let passed = 0;
  let running = 0;
  let failed = 0;
  for (const check of checks) {
    const state = String(check.state ?? "").toLowerCase();
    if (PASSED.has(state)) passed += 1;
    else if (RUNNING.has(state)) running += 1;
    else failed += 1;
  }
  return { passed, total: checks.length, failed, running };
}

/** The base branch as the PR card says it (`origin/main` → `main`). */
export function baseWord(base: string | null | undefined): string {
  return String(base ?? "").replace(/^origin\//, "");
}

/* ── the timeline ─────────────────────────────────────────────────── */

const READ_TOOLS = new Set(["Read", "Grep", "Glob", "LS", "NotebookRead"]);
const WRITE_TOOLS = new Set(["Edit", "Write", "MultiEdit", "NotebookEdit", "apply_patch"]);
const RUN_TOOLS = new Set(["Bash", "shell", "exec_command", "local_shell"]);

/** A tool call the agent made (one PostToolUse row). */
export function isToolCall(event: LaneEvent): boolean {
  return event.event === "PostToolUse" && Boolean(event.tool);
}

/** The words of a test run's result when the event's detail carries them
 * (`6 passed`); the hook keeps none today, so this is usually empty. */
function runResult(event: LaneEvent): string {
  const detail = event.detail ?? {};
  const result = detail.result ?? detail.summary;
  return typeof result === "string" ? result.trim() : "";
}

/** One rail entry before its verbs are drawn: the face adds Brief,
 * Deny / Approve. `at` orders the entries; `heads` collapse repeated READs. */
export interface LaneEntry extends Omit<TimelineEntry, "verbs"> {
  at: number | null;
  kind: "brief" | "read" | "says" | "write" | "run" | "call" | "answer" | "end" | "commit" | "pr" | "held" | "asks" | "merge" | "rebrief";
  /** HELD: the gate proposal; the face draws Deny / Approve while it is held. */
  gated?: LaneGated;
  heads?: string[];
}

const MAX_READ_HEADS = 2;

function short(path: string | null | undefined): string {
  return String(path ?? "").trim();
}

function at(value: unknown): number | null {
  const date = wireDate(value);
  return date ? date.getTime() : null;
}

function readCode(heads: readonly string[]): string {
  // A call with no head (a Grep, a Glob: the hook keeps no path for them)
  // counts in `+n` and names nothing.
  const shown = heads.filter(Boolean).slice(0, MAX_READ_HEADS);
  const more = heads.length - shown.length;
  return [...shown, more > 0 ? `+${more}` : ""].filter(Boolean).join(" · ");
}

/** The events as rail entries: tool calls in words, consecutive READs as one
 * entry (`a · b · +n`), the agent's own words (Stop's message) quoted. A
 * SessionStart and the first prompt are the brief (the BRIEF entry comes from
 * the launch); a PreToolUse is the call before it ran (its PostToolUse is the
 * record); a Notification is the wait (the ASKS entry). */
export function eventEntries(events: readonly LaneEvent[]): LaneEntry[] {
  const out: LaneEntry[] = [];
  let promptSeen = false;
  for (const event of events) {
    const when = at(event.ts);
    const time = wireClock(event.ts);
    const id = `ev-${event.id}`;
    if (event.event === "UserPromptSubmit") {
      // The first prompt is the brief typed into the agent; later ones are
      // the owner's answers and steers.
      if (!promptSeen) {
        promptSeen = true;
        continue;
      }
      if (event.text) out.push({ id, at: when, time, kind: "answer", word: "ANSWER", quote: event.text });
      continue;
    }
    if ((event.event === "Stop" || event.event === "SubagentStop") && event.text) {
      out.push({ id, at: when, time, kind: "says", word: "SAYS", quote: event.text });
      continue;
    }
    if (event.event === "SessionEnd") {
      out.push({ id, at: when, time, kind: "end", word: "ENDED", text: String(event.detail?.reason ?? "") || undefined });
      continue;
    }
    if (!isToolCall(event)) continue;
    const tool = String(event.tool);
    if (READ_TOOLS.has(tool)) {
      const head = short(event.head);
      const last = out[out.length - 1];
      if (last && last.kind === "read" && last.heads) {
        if (!head || !last.heads.includes(head)) last.heads.push(head);
        last.code = readCode(last.heads);
        continue;
      }
      out.push({ id, at: when, time, kind: "read", word: "READ", heads: [head], code: readCode([head]) || undefined });
      continue;
    }
    if (WRITE_TOOLS.has(tool)) {
      out.push({ id, at: when, time, kind: "write", word: "WRITE", code: short(event.head) || tool });
      continue;
    }
    if (RUN_TOOLS.has(tool)) {
      const result = runResult(event);
      const code = [short(event.head), result].filter(Boolean).join(" · ");
      out.push({ id, at: when, time, kind: "run", word: "RUN", code: code || tool, tone: result ? "ok" : undefined });
      continue;
    }
    // Any other call (a task, a fetch, an MCP tool): its name; repeats fold.
    const last = out[out.length - 1];
    if (last && last.kind === "call" && last.heads) {
      const name = short(event.head) ? `${tool} ${short(event.head)}` : tool;
      if (!last.heads.includes(name)) last.heads.push(name);
      last.code = readCode(last.heads);
      continue;
    }
    const name = short(event.head) ? `${tool} ${short(event.head)}` : tool;
    out.push({ id, at: when, time, kind: "call", word: "CALL", heads: [name], code: name });
  }
  return out;
}

const HELD_STATES = new Set(["held", "pending"]);

/** A gate proposal the Control mode held (not one it passed at once). */
export function wasHeld(call: LaneGated): boolean {
  return call.was_held !== false;
}

/** The held calls of the lane: the ones the Control mode held. */
function heldCalls(lane: LaneWire): LaneGated[] {
  return Array.isArray(lane.gated) ? lane.gated.filter(wasHeld) : [];
}

/** PHILO-15 15 (B45): the HELD station's line, `9 HELD · 3 APPROVED ·
 * 5 DENIED · 1 EXPIRED` (a count of zero is not said); `—` with none. */
export function heldSummary(lane: LaneWire): string {
  const calls = heldCalls(lane);
  if (calls.length === 0) return "—";
  const count = (state: string) => calls.filter((c) => String(c.state).toLowerCase() === state).length;
  const waiting = calls.filter((c) => HELD_STATES.has(c.state)).length;
  const parts: Array<[number, string]> = [
    [calls.length, "HELD"],
    [waiting, "WAITING"],
    [count("approved"), "APPROVED"],
    [count("denied"), "DENIED"],
    [count("expired"), "EXPIRED"],
    [count("invalidated"), "ENDED BY A RESTART"],
  ];
  return parts.filter(([n]) => n > 0).map(([n, word]) => `${n} ${word}`).join(" · ");
}

/** Every rail entry of the lane, in time order: BRIEF first, the events,
 * the commits, the PR (after the last commit: the hub keeps no PR time), the
 * held calls, the wait, and the trailing MERGE. */
export function laneEntries(lane: LaneWire, events: readonly LaneEvent[]): LaneEntry[] {
  const timed: LaneEntry[] = [];
  const launch = lane.launch;
  const briefFacts = briefLine(launch.brief_text);
  const brief = briefState(launch);
  timed.push({
    id: "brief",
    at: at(brief.when ?? launch.launched_at),
    time: brief.state === "sent" ? wireClock(brief.when) : "",
    kind: "brief",
    word: "BRIEF",
    text: [brief.state === "sent" ? "" : brief.word, briefFacts].filter(Boolean).join(" · ") || undefined,
    ...(brief.state === "sent" ? {} : { pending: true }),
  });
  timed.push(...eventEntries(events));
  for (const receipt of Array.isArray(launch.rebriefs) ? launch.rebriefs : []) timed.push(rebriefEntry(receipt));
  const worktree = lane.worktree;
  if (!isNotRead(worktree)) {
    // git log is newest first; the rail reads oldest first.
    for (const commit of [...worktree.commits].reverse()) {
      timed.push({
        id: `commit-${commit.sha}`,
        at: commit.at ? commit.at * 1000 : null,
        time: wireClock(commit.at ?? null),
        kind: "commit",
        word: "COMMIT",
        code: [commit.sha, commit.subject].filter(Boolean).join(" "),
      });
    }
  }
  for (const call of heldCalls(lane)) {
    const held = HELD_STATES.has(call.state);
    const reason = String(call.hold_reason ?? "").trim();
    const text = [held ? "" : decidedWord(call), reason].filter(Boolean).join(" · ");
    timed.push({
      id: `held-${call.id}`,
      at: at(call.created_at),
      time: wireClock(call.created_at),
      kind: "held",
      word: "HELD",
      tone: held ? "warn" : undefined,
      code: gatedHead(call),
      text: text || undefined,
      gated: call,
    });
  }
  // A stable sort by time; an entry with no time keeps its place after the
  // one before it.
  const ordered = stableByTime(timed);
  const pr = lane.follow_through?.pr;
  if (pr && pr.number != null) {
    const checks = checksSummary(pr.checks);
    const text = [
      `#${pr.number} ${prStateWord(pr.state)}`,
      checks ? `checks ${checks.passed} of ${checks.total}` : "",
      `review ${reviewWord(pr.review_decision).toLowerCase()}`,
    ].filter(Boolean).join(" · ");
    const entry: LaneEntry = { id: "pr", at: null, time: "", kind: "pr", word: "PR", tone: "info", text };
    let index = -1;
    ordered.forEach((e, i) => { if (e.kind === "commit") index = i; });
    ordered.splice(index >= 0 ? index + 1 : ordered.length, 0, entry);
  }
  const wait = lane.wait;
  if (wait && !isNotRead(wait) && wait.question) {
    const turn = turnWord(wait);
    ordered.push({
      id: "asks",
      at: at(wait.started),
      time: wireClock(wait.started),
      kind: "asks",
      word: turn.word,
      tone: turn.tone,
      text: wait.question,
    });
  }
  const merged = lane.follow_through?.merged;
  if (merged) {
    const when = merged.merged_at ?? merged.mergedAt ?? merged.at ?? null;
    ordered.push({ id: "merge", at: at(when), time: wireClock(when), kind: "merge", word: "MERGED", tone: "ok", text: wireClock(when) ? undefined : "Merged" });
  } else {
    ordered.push({ id: "merge", at: null, time: "", kind: "merge", word: "MERGE", pending: true, text: "Your press in GitHub" });
  }
  return ordered;
}

function stableByTime(entries: LaneEntry[]): LaneEntry[] {
  let last = Number.NEGATIVE_INFINITY;
  const keyed = entries.map((entry, index) => {
    if (entry.at != null) last = entry.at;
    return { entry, key: entry.at ?? last, index };
  });
  keyed.sort((a, b) => a.key - b.key || a.index - b.index);
  return keyed.map((k) => k.entry);
}

function prStateWord(state: string | null | undefined): string {
  const s = String(state ?? "").toLowerCase();
  if (s === "merged") return "merged";
  if (s === "closed") return "closed";
  if (s === "draft") return "draft";
  return "opened";
}

function decidedWord(call: LaneGated): string {
  const state = String(call.state).toUpperCase();
  return call.decided_by ? `${state} · ${call.decided_by}` : state;
}

/** `<command>… +N CHARS` when the hub cannot show the call whole. */
export function cutMark(command: string, call: { args_cut?: boolean | null; args_hidden?: number | null }): string {
  if (!call.args_cut) return command;
  const hidden = Number(call.args_hidden ?? 0);
  return `${command}… ${hidden > 0 ? `+${hidden} CHARS` : "CUT"}`;
}

/** A held call's command: the gate keeps the JSON head of the arguments
 * (`{"command":"ls /etc"}`); the face shows the command. */
export function gatedHead(call: LaneGated): string {
  if (call.args_shown) return cutMark(String(call.args_shown), call);
  const head = String(call.args_head ?? "").trim();
  const match = /"(?:command|cmd|file_path|path|url)"\s*:\s*"((?:[^"\\]|\\.)*)/.exec(head);
  if (match) {
    try {
      return JSON.parse(`"${match[1]}"`);
    } catch {
      return match[1];
    }
  }
  return head || String(call.tool ?? "");
}

/** The brief's facts on one line: `n words` (the hub keeps the text, not its sources). */
export function briefLine(brief: string | null | undefined): string {
  const text = String(brief ?? "").trim();
  if (!text) return "";
  const words = text.split(/\s+/).length;
  const kb = new TextEncoder().encode(text).length / 1024;
  return kb >= 1 ? `${words} words · ${kb.toFixed(1)} KB` : `${words} words`;
}

/* ── the Re-brief receipts ───────────────────────────────────────── */

const REBRIEF_STATE_WORD: Record<string, string> = {
  sent: "SENT", superseded: "SUPERSEDED", expired: "EXPIRED", taken_back: "TAKEN BACK",
};

/** `SENT · 17:22 · BY YOUR PRESS 17:13`; `SUPERSEDED · …`; `EXPIRED · AGENT
 * NEVER RETURNED · BY YOUR PRESS …`. */
export function rebriefWords(receipt: LaneRebriefReceipt): string {
  const word = REBRIEF_STATE_WORD[receipt.state] ?? String(receipt.state).toUpperCase();
  const pressed = wireClock(receipt.approved_at);
  return [word, wireClock(receipt.at), receipt.detail || "", pressed ? `BY YOUR PRESS ${pressed}` : ""].filter(Boolean).join(" · ");
}

/** The rail entry of one Re-brief receipt; its code line names the
 * delivery's command id (the receipt is the owner's press). */
export function rebriefEntry(receipt: LaneRebriefReceipt): LaneEntry {
  const sent = receipt.state === "sent";
  return {
    id: `rebrief-${receipt.id ?? receipt.command_id ?? receipt.at}`,
    at: at(receipt.at),
    time: wireClock(receipt.at),
    kind: "rebrief",
    word: "RE-BRIEF",
    tone: sent ? "ok" : "warn",
    text: rebriefWords(receipt),
    quote: receipt.text_head ?? undefined,
    code: receipt.command_id ? `command ${receipt.command_id}` : receipt.press_id ? `press ${receipt.press_id}` : undefined,
  };
}

/* ── the station track ───────────────────────────────────────────── */

/** PHILO-15 B42: the brief as it is: `sent` at its delivery time; else
 * `waiting` (the launch holds it until the agent is ready) or `not sent`.
 * A launch with no delivery state is an older one: its launch time. */
export function briefState(launch: LaneLaunch): { state: "sent" | "waiting" | "not_sent"; word: string; when: string | null } {
  const state = String(launch.instruction_state ?? "");
  if (!state || state === "sent") {
    return { state: "sent", word: "sent", when: launch.brief_sent_at ?? (state ? null : launch.launched_at ?? null) };
  }
  if (state === "pending" || state === "delivering") return { state: "waiting", word: "waiting", when: null };
  return { state: "not_sent", word: "not sent", when: null };
}

/** PHILO-15 B48: the word of a turn end. ASKS only when a real question (or
 * a permission prompt) waits; IDLE when the turn ended with no question;
 * DONE when it ended with no question and the PR is open. */
export function turnWord(wait: LaneWait): { word: "ASKS" | "IDLE" | "DONE"; tone: ObjectTone } {
  if (wait.kind === "TO APPROVE" || wait.kind === "DECIDING") return { word: "ASKS", tone: "ask" };
  const hidden = turnEndWord(wait);  // PHILO-15 15: the responder's DONE / IDLE
  if (hidden === "DONE") return { word: "DONE", tone: "ok" };
  if (hidden === "IDLE") return { word: "IDLE", tone: "info" };
  if (wait.turn_end === "idle") return { word: "IDLE", tone: "info" };
  if (wait.turn_end === "done") return { word: "DONE", tone: "ok" };
  return { word: "ASKS", tone: "ask" };
}

/** BRIEF · WORK · COMMIT · PR · HELD · ASKS · MERGE from the lane: a station
 * with nothing in it is hollow and says `—`, never a zero. */
export function laneStations(lane: LaneWire, events: readonly LaneEvent[]): Station[] {
  const calls = events.filter(isToolCall).length;
  const worktree = lane.worktree;
  const commits = isNotRead(worktree) ? null : worktree.commits.length;
  const pr = lane.follow_through?.pr;
  const held = heldCalls(lane).filter((g) => HELD_STATES.has(g.state)).length;
  const everHeld = heldCalls(lane).length;
  const wait = lane.wait && !isNotRead(lane.wait) ? lane.wait : null;
  const asking = Boolean(wait && (wait.kind === "TO ANSWER" || wait.kind === "TO APPROVE"));
  const turn = wait && (asking || turnEndWord(wait)) ? turnWord(wait) : null;
  const brief = briefState(lane.launch);
  const merged = Boolean(lane.follow_through?.merged);
  const reached = (on: boolean, tone: ObjectTone = "ok"): Pick<Station, "state" | "tone"> =>
    on ? { state: "reached", tone } : { state: "ahead" };
  return [
    brief.state === "sent"
      ? { word: "BRIEF", sub: wireClock(brief.when) || "sent", ...reached(true) }
      : { word: "BRIEF", sub: brief.word, state: "current" as const, tone: brief.state === "waiting" ? ("warn" as const) : ("fail" as const) },
    { word: "WORK", sub: calls > 0 ? `${calls} ${calls === 1 ? "call" : "calls"}` : "—", ...reached(calls > 0) },
    {
      word: "COMMIT",
      sub: commits == null ? "not read" : commits > 0 ? String(commits) : "—",
      ...reached(Boolean(commits)),
    },
    { word: "PR", sub: pr?.number != null ? `#${pr.number}` : "—", ...reached(pr?.number != null, "info") },
    {
      word: "HELD",
      sub: heldSummary(lane),
      ...(held > 0
        ? { state: "current" as const, tone: "warn" as const }
        : everHeld > 0 ? { state: "reached" as const, tone: "warn" as const } : { state: "ahead" as const }),
    },
    !turn
      ? { word: "ASKS", sub: "—", state: "ahead" as const }
      : turn.word === "ASKS"
        ? { word: "ASKS", sub: "now", state: "current" as const, tone: "ask" as const }
        : { word: turn.word, sub: wireClock(wait?.started) || "now", state: turn.word === "DONE" ? ("reached" as const) : ("current" as const), tone: turn.tone },
    { word: "MERGE", sub: merged ? "merged" : "yours", ...reached(merged) },
  ];
}

/* ── the window's title ─────────────────────────────────────────── */

/** `<Agent>: <item>`, the item's own name; with no name, the agent alone. */
export function laneTitle(agent: string | null | undefined, item: string | null | undefined): string {
  return windowName({ kind: "lane", agent: agentName(agent), item });
}
