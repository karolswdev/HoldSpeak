/* Conductor F2: the agents in flight, read once for every face.
 *
 * `GET /api/coders/sessions?include_ended=false` (holdspeak/web/routes/system/
 * coders.py) answers the live agent sessions and, beside them, `flights`:
 * each desk item an agent was handed (`services/agent_flights.py`: the launch
 * ledger joined to the Work attempt and the session), with the agent, the
 * state (working | waiting | pr_open | merged | ended), the session key and
 * the PR. The Door row, the Room's OPEN HERE row, the arrival AGENTS section,
 * the Agents window and the Needs you coder row all read this one store.
 */
import { useCallback, useEffect } from "react";
import { create } from "zustand";
import { apiFetch } from "../lib/api";
import { reportWriteFailure } from "./hooks/useWriteReceipt";
import { useOnCoderFrame, useOnDeskChanged } from "./useDeskChangedRefresh";
import { coderTurnEnd, isBlockedCoder, type NeedsYouCoder } from "./needsYou";

export type FlightState =
  | "starting" | "working" | "waiting" | "done" | "pr_open" | "merged" | "ended" | "expired" | "stopped_by_restart"
  /** Betterment AG5: a hand that waits for a free agent (no launch yet). */
  | "queued"
  /** Betterment AG6: Resume was pressed; the agent has not reported yet,
   *  or not within the window (a shell waits in its worktree). */
  | "resuming" | "resume_failed"
  /** Betterment AG7: an agent is there, but no hook and no screen rule told
   *  its state for ten minutes. */
  | "no_signal";
export type AgentName = "claude" | "codex" | "pi";

export interface AgentReview {
  requested: "codex" | "claude" | "pi" | string;
  status: string;
  role: "builder" | "reviewer" | string;
  builder?: string;
  round: number;
  rounds: number;
  findingsLeft: Array<{ level: string; text: string }>;
  reviewerLaunchId: string | null;
  pairResult: { rounds?: number; findings_left?: Array<{ level: string; text: string }> } | null;
}

export interface AgentFlight {
  originRef: string;
  kind: string;
  id: string;
  title: string;
  projectId: string;
  projectName: string;
  agent: AgentName;
  state: FlightState;
  sessionKey: string | null;
  /** `title`: the PR's own title (PHILO-15 B50); empty until the hub read it. */
  pr: { number: number | null; url: string; state: string; title?: string } | null;
  /** PHILO-15 B48: how a waiting agent's turn ended (`asks`, `idle`, `done`);
   * PHILO-15 15: the responder's DONE / IDLE first (also with the PR open). */
  turnEnd?: "asks" | "idle" | "done" | null;
  /** Betterment AG0: the done turn's id, and whether the owner has not
   * opened the agent since (`POST /api/agent/launches/{id}/seen`). */
  turnId?: string | null;
  isNew?: boolean;
  close: string | null;
  /** K4's cleanup of the agent's session (`killed`, `session_gone`,
   * `no_session`): the evidence that it left. Null while the close waits
   * for the owner (Secure) or cleanup is outstanding. */
  sessionCleanup: string | null;
  mergedAt: string | null;
  /** PHILO-14 C2: the launch, the agent's lane window opens on it. */
  launchId: string | null;
  /** Betterment AG5: a queued hand's id and when he pressed it. */
  queueId?: string | null;
  queuedAt?: string | null;
  /** Betterment AG3: the desk's own answer under YOLO (drafting, then what
   * it typed and the line it used; New until he opens the agent). */
  deskAnswer?: DeskAnswer | null;
  /** Betterment AG11: the launch that started this helper. */
  helperOf?: string | null;
  /** Betterment AG11: Secure asked the owner for one helper Allow press. */
  helperRequest?: { requestId: string; status: "awaiting_owner"; instruction: string; profile: string | null } | null;
  /** Betterment AG12: the explicit builder/reviewer pair. */
  review?: AgentReview | null;
  /** Betterment AG7: which source decided the state (`hook`, `screen`). */
  stateSource?: "hook" | "screen" | null;
  /** Betterment AG7: the agent's screen as the hub's rules read it. */
  screen?: AgentScreen | null;
}

/** Betterment AG7: what the hub's screen rules read on an agent's pane:
 *  its state in the desk's words, and what a prompt on it asks (the command
 *  an approval wants to run, the numbered choices). */
export interface AgentScreen {
  state: "working" | "approve" | "asks" | "done" | "idle" | "no_signal" | null;
  rule: string | null;
  wait: "approve" | "question" | null;
  command: string | null;
  choices: Array<{ n: string; label: string }>;
  /** The agent's last words above its prompt (a finished turn). */
  said: string | null;
  at: string | null;
  /** When this state began: the prompt's token an answer names. */
  since: string | null;
}

export function fromWireScreen(body: any): AgentScreen | null {
  if (!body || typeof body !== "object") return null;
  const states = ["working", "approve", "asks", "done", "idle", "no_signal"];
  return {
    state: states.includes(body.state) ? body.state : null,
    rule: body.rule ? String(body.rule) : null,
    wait: body.wait === "approve" || body.wait === "question" ? body.wait : null,
    command: body.command ? String(body.command) : null,
    choices: Array.isArray(body.choices)
      ? body.choices.filter((c: any) => c && c.n).map((c: any) => ({ n: String(c.n), label: String(c.label ?? "") }))
      : [],
    said: body.said ? String(body.said) : null,
    at: body.at ? String(body.at) : null,
    since: body.since ? String(body.since) : null,
  };
}

/** Betterment AG3: where the line the desk used comes from. */
export interface DeskAnswerSource {
  text: string;
  kind: "decision" | "memory" | "meeting" | "note" | "brief" | string;
  title: string;
}

export type DeskAnswer =
  | { state: "drafting"; waitId: string | null }
  | { state: "answered"; text: string; source: DeskAnswerSource | null; at: string | null; waitId: string | null; isNew: boolean };

export function fromWireDeskAnswer(body: any): DeskAnswer | null {
  if (body?.state === "drafting") return { state: "drafting", waitId: body.wait_id ? String(body.wait_id) : null };
  if (body?.state !== "answered" || !body.text) return null;
  const source = body.source && body.source.text
    ? { text: String(body.source.text), kind: String(body.source.kind ?? "brief"), title: String(body.source.title ?? "") }
    : null;
  return {
    state: "answered",
    text: String(body.text),
    source,
    at: body.at ? String(body.at) : null,
    waitId: body.wait_id ? String(body.wait_id) : null,
    isNew: body.new === true,
  };
}

export interface CoderSessionRow {
  key: string;
  agent: string;
  sessionId: string;
  /** The session's repository folder name (never the path). */
  name: string;
  state: string;
  blocked: boolean;
  /** PHILO-15 B48: blocked, but the turn ended with no question (IDLE). */
  idle?: boolean;
  question: string;
  flight: AgentFlight | null;
  /** Betterment AG7: the session's screen (null when no pane was read). */
  screen?: AgentScreen | null;
  /** The wire row as it came, for faces that read more of it. */
  raw: Record<string, unknown>;
}

const AGENT_WORD: Record<AgentName, string> = { claude: "CLAUDE CODE", codex: "CODEX", pi: "PI" };

export function agentWord(agent: string): string {
  return AGENT_WORD[agent as AgentName] ?? agent.toUpperCase();
}

const FLIGHT_STATES: readonly string[] = [
  "starting", "working", "waiting", "done", "pr_open", "merged", "ended", "expired", "stopped_by_restart", "queued",
  "resuming", "resume_failed", "no_signal",
];

export function fromWireFlight(body: any): AgentFlight {
  const pr = body?.pr;
  return {
    originRef: String(body?.origin_ref ?? ""),
    kind: String(body?.kind ?? ""),
    id: String(body?.id ?? ""),
    title: String(body?.title ?? ""),
    projectId: String(body?.project_id ?? ""),
    projectName: String(body?.project_name ?? ""),
    agent: body?.agent === "codex" || body?.agent === "pi" ? body.agent : "claude",
    state: (FLIGHT_STATES.includes(body?.state) ? body.state : "starting") as FlightState,
    sessionKey: body?.session_key ? String(body.session_key) : null,
    pr: pr ? { number: pr.number == null ? null : Number(pr.number), url: String(pr.url ?? ""), state: String(pr.state ?? ""), title: String(pr.title ?? "") } : null,
    turnEnd: ["asks", "idle", "done"].includes(body?.turn_end) ? body.turn_end : null,
    turnId: body?.turn_id ? String(body.turn_id) : null,
    isNew: body?.new === true,
    close: body?.close ? String(body.close) : null,
    sessionCleanup: body?.session_cleanup ? String(body.session_cleanup) : null,
    mergedAt: body?.merged_at ? String(body.merged_at) : null,
    launchId: body?.launch_id ? String(body.launch_id) : null,
    queueId: body?.queue_id ? String(body.queue_id) : null,
    queuedAt: body?.queued_at ? String(body.queued_at) : null,
    deskAnswer: fromWireDeskAnswer(body?.desk_answer),
    helperOf: body?.helper_of ? String(body.helper_of) : null,
    helperRequest: body?.helper_request?.status === "awaiting_owner"
      ? {
          requestId: String(body.helper_request.request_id ?? ""),
          status: "awaiting_owner",
          instruction: String(body.helper_request.instruction ?? ""),
          profile: body.helper_request.profile ? String(body.helper_request.profile) : null,
        }
      : null,
    review: body?.review ? {
      requested: String(body.review.requested ?? ""),
      status: String(body.review.status ?? ""),
      role: String(body.review.role ?? "builder"),
      builder: body.review.builder ? String(body.review.builder) : undefined,
      round: Number(body.review.round ?? 0),
      rounds: Number(body.review.rounds ?? body.review.round ?? 0),
      findingsLeft: Array.isArray(body.review.findings_left)
        ? body.review.findings_left.filter((f: any) => f && f.level).map((f: any) => ({ level: String(f.level), text: String(f.text ?? "") }))
        : [],
      reviewerLaunchId: body.review.reviewer_launch_id ? String(body.review.reviewer_launch_id) : null,
      pairResult: body.review.pair_result && typeof body.review.pair_result === "object" ? body.review.pair_result : null,
    } : null,
    stateSource: body?.state_source === "hook" || body?.state_source === "screen" ? body.state_source : null,
    screen: fromWireScreen(body?.screen),
  };
}

export function fromWireSessionRow(row: any): CoderSessionRow {
  const session = (row?.session ?? row ?? {}) as Record<string, unknown>;
  const agent = String(session.agent ?? "claude");
  const sessionId = String(session.session_id ?? "");
  const folder = String(session.project_name ?? session.repo_root ?? session.cwd ?? "")
    .replace(/[\\/]+$/, "").split(/[\\/]/).pop() ?? "";
  return {
    key: `${agent}:${sessionId}`,
    agent,
    sessionId,
    name: folder || sessionId || "session",
    state: String(session.state ?? session.lifecycle ?? ""),
    blocked: isBlockedCoder(session as NeedsYouCoder),
    idle: isBlockedCoder(session as NeedsYouCoder) && coderTurnEnd(session as NeedsYouCoder) === "idle",
    question: String(session.question ?? ""),
    flight: row?.flight ? fromWireFlight(row.flight) : null,
    screen: fromWireScreen(row?.screen),
    raw: row ?? {},
  };
}

/** The chip's words: once a PR exists the PR is the fact, else the agent's state. */
export function flightLabel(flight: AgentFlight): string | null {
  if ((flight.state === "pr_open" || flight.state === "merged") && flight.pr?.number) {
    return `PR #${flight.pr.number} · ${flight.state === "pr_open" ? "OPEN" : "MERGED"}`;
  }
  if (flight.state === "starting") return `${agentWord(flight.agent)} · STARTING`;
  if (flight.state === "queued") return `${agentWord(flight.agent)} · WAITS FOR A FREE AGENT`;
  if (flight.state === "resuming") return `${agentWord(flight.agent)} · RESUMING`;
  if (flight.state === "working") return `${agentWord(flight.agent)} · WORKING`;
  if (flight.state === "done") return `${agentWord(flight.agent)} · ${flight.isNew ? "DONE · NEW" : "DONE"}`;
  if (flight.state === "waiting") return `${agentWord(flight.agent)} · ${flight.turnEnd === "idle" ? "IDLE" : "WAITING"}`;
  if (flight.state === "no_signal") return `${agentWord(flight.agent)} · NO SIGNAL`;
  return null;
}

export function flightTone(state: FlightState): "working" | "warning" | "active" | "success" | "idle" {
  if (state === "starting" || state === "queued" || state === "resuming" || state === "no_signal") return "idle";
  if (state === "done") return "success";
  return state === "waiting" ? "warning" : state === "pr_open" ? "active" : state === "merged" ? "success" : "working";
}

/** A Room issue row's item id, `<watch_id>.<entity_id>` (agent_issue.py), or null. */
export function issueOriginId(item: { kind?: string | null; watchId?: string | null; entityId?: string | null }): string | null {
  if (item.kind !== "issue" || !item.watchId || !item.entityId) return null;
  return `${item.watchId}.${item.entityId}`;
}

/** The desk refs a Needs you / OPEN HERE row is known by, in the launch's
 * `origin_ref` grammar (`action:<id>`, `decision:<id>`, `decision_record:<id>`, `issue:<watch>.<entity>`). */
export function itemOriginRefs(item: {
  actionItemId?: string | null;
  ref?: string | null;
  openRef?: string | null;
  id?: string | null;
  _doorCard?: { target_ref?: string | null; open_ref?: string | null } | null;
  /** A Room issue row (Conductor R4): its Watch and its entity. */
  kind?: string | null;
  watchId?: string | null;
  entityId?: string | null;
}): string[] {
  const refs = new Set<string>();
  if (item.actionItemId) refs.add(`action:${item.actionItemId}`);
  const issue = issueOriginId(item);
  if (issue) refs.add(`issue:${issue}`);
  for (const raw of [item._doorCard?.target_ref, item._doorCard?.open_ref, item.ref, item.openRef, item.id]) {
    const ref = String(raw ?? "").trim();
    if (!ref.includes(":")) continue;
    const [kind, ...rest] = ref.split(":");
    const id = rest.join(":");
    if (!id) continue;
    if (kind === "action_item" || kind === "action") refs.add(`action:${id}`);
    else if (kind === "decision") refs.add(`decision:${id}`);
    else if (kind === "desk_decision" || kind === "decision_record") refs.add(`decision_record:${id}`);
    else if (kind === "note" || kind === "project_item") refs.add(`${kind}:${id}`);
  }
  return [...refs];
}

/** The flights whose agent left: no row shows them as its agent. */
export const GONE: ReadonlySet<FlightState> = new Set<FlightState>(["ended", "expired", "stopped_by_restart", "resume_failed"]);

export function flightForItem(flights: readonly AgentFlight[], item: Parameters<typeof itemOriginRefs>[0]): AgentFlight | null {
  const refs = itemOriginRefs(item);
  if (!refs.length) return null;
  return flights.find((f) => refs.includes(f.originRef) && !GONE.has(f.state)) ?? null;
}

/** An agent holds the item: QUEUED (AG5), STARTING, WORKING, WAITING, DONE, PR OPEN, or MERGED
 * with the close still awaiting the owner's confirmation (Secure). Such a row
 * shows its flight and not Hand to coder. */
export function isInFlight(flight: AgentFlight | null | undefined): flight is AgentFlight {
  if (!flight) return false;
  if (["queued", "starting", "resuming", "working", "waiting", "done", "pr_open", "no_signal"].includes(flight.state)) return true;
  return flight.state === "merged" && flight.close === "awaiting_confirm";
}

/** K4's cleanup outcomes that end the agent's session. */
const SESSION_LEFT = new Set(["killed", "session_gone", "no_session"]);

/** The live sessions the AGENTS section lists. A session leaves only on
 * terminal evidence: its own SessionEnd, or K4's cleanup of it. A merged
 * launch whose close waits for the owner (Secure) or whose cleanup is still
 * outstanding keeps its session listed. */
export function liveAgentSessions(rows: readonly CoderSessionRow[]): CoderSessionRow[] {
  return rows.filter((row) => row.state !== "ended" && !SESSION_LEFT.has(String(row.flight?.sessionCleanup ?? "")));
}

interface AgentFlightsState {
  sessions: CoderSessionRow[];
  flights: AgentFlight[];
  loaded: boolean;
  /** PHILO-17 (phonepass): a first read has ended, read or failed. */
  settled: boolean;
  load(): Promise<void>;
}

let inflight: Promise<void> | null = null;
let again = false;

export const useAgentFlights = create<AgentFlightsState>((set, get) => ({
  sessions: [],
  flights: [],
  loaded: false,
  settled: false,
  load() {
    // A refresh that arrives while a read is out is kept: one trailing read
    // follows it, so a transition that happened mid-read is never lost.
    if (inflight) {
      again = true;
      return inflight;
    }
    inflight = apiFetch<{ sessions?: unknown[]; flights?: unknown[] }>("/api/coders/sessions?include_ended=false")
      .then((body) => {
        if (!body || typeof body !== "object") return;
        set({
          sessions: (Array.isArray(body.sessions) ? body.sessions : []).map(fromWireSessionRow),
          flights: (Array.isArray(body.flights) ? body.flights : []).map(fromWireFlight),
          loaded: true,
        });
      })
      .catch(() => undefined)   // the last read stays; the next frame reads again
      .finally(() => {
        inflight = null;
        if (!get().settled) set({ settled: true });
        if (again) {
          again = false;
          void get().load();
        }
      });
    return inflight;
  },
}));

/** Betterment AG0: the owner opened this agent, so its done turn is seen
 * (Done · New becomes Quiet). The store says so at once; the hub keeps it. */
export async function markLaunchSeen(launchId: string, turnId: string | null): Promise<void> {
  // `null`: the hub marks the launch's current done turn (the window opened).
  // Betterment AG3: opening the agent also sees the desk's answer.
  const seenAnswer = (f: AgentFlight) =>
    turnId === null && f.deskAnswer?.state === "answered" ? { ...f.deskAnswer, isNew: false } : f.deskAnswer;
  const mark = (flights: AgentFlight[]) =>
    flights.map((f) =>
      f.launchId === launchId && (turnId === null || f.turnId === turnId) ? { ...f, isNew: false, deskAnswer: seenAnswer(f) } : f,
    );
  useAgentFlights.setState((s) => ({
    flights: mark(s.flights),
    sessions: s.sessions.map((row) => (row.flight ? { ...row, flight: mark([row.flight])[0] } : row)),
  }));
  try {
    await apiFetch(`/api/agent/launches/${encodeURIComponent(launchId)}/seen`, { method: "POST", json: turnId ? { wait_id: turnId } : {} });
  } catch (cause) {
    // The next read says NEW again; the next open marks it again.
    reportWriteFailure("Mark seen", cause, () => void markLaunchSeen(launchId, turnId), `agent:${launchId}`);
  }
}

/** Read on mount and again when an agent moves (the `scope:"coder"` frame)
 * or the desk changes (a merge closed an item). */
export function useAgentFlightsLive(): void {
  const reload = useCallback(() => { void useAgentFlights.getState().load(); }, []);
  useEffect(() => { reload(); }, [reload]);
  useOnCoderFrame(reload);
  useOnDeskChanged(reload);
}

/** Conductor F2 (K6): the Room's receipt for a commitment an agent's PR
 * closed: the newest merged flight of this Project whose follow-through
 * closed its item, within the last day. */
const CLOSED = new Set(["closed", "linked", "already_closed"]);
const RECEIPT_WINDOW_MS = 24 * 60 * 60 * 1000;

export function mergeReceipt(
  flights: readonly AgentFlight[],
  projectId: string | null | undefined,
  now: Date = new Date(),
): AgentFlight | null {
  if (!projectId) return null;
  const merged = flights
    .filter((f) => f.state === "merged" && f.projectId === projectId && CLOSED.has(String(f.close)) && f.mergedAt)
    .filter((f) => now.getTime() - Date.parse(String(f.mergedAt)) < RECEIPT_WINDOW_MS)
    .sort((a, b) => String(b.mergedAt).localeCompare(String(a.mergedAt)));
  return merged[0] ?? null;
}
