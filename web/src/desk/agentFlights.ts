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
import { useOnCoderFrame, useOnDeskChanged } from "./useDeskChangedRefresh";
import { coderTurnEnd, isBlockedCoder, type NeedsYouCoder } from "./needsYou";

export type FlightState = "starting" | "working" | "waiting" | "pr_open" | "merged" | "ended" | "expired";
export type AgentName = "claude" | "codex" | "pi";

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
  close: string | null;
  /** K4's cleanup of the agent's session (`killed`, `session_gone`,
   * `no_session`): the evidence that it left. Null while the close waits
   * for the owner (Secure) or cleanup is outstanding. */
  sessionCleanup: string | null;
  mergedAt: string | null;
  /** PHILO-14 C2: the launch, the agent's lane window opens on it. */
  launchId: string | null;
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
  /** The wire row as it came, for faces that read more of it. */
  raw: Record<string, unknown>;
}

const AGENT_WORD: Record<AgentName, string> = { claude: "CLAUDE CODE", codex: "CODEX", pi: "PI" };

export function agentWord(agent: string): string {
  return AGENT_WORD[agent as AgentName] ?? agent.toUpperCase();
}

const FLIGHT_STATES: readonly string[] = ["starting", "working", "waiting", "pr_open", "merged", "ended", "expired"];

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
    close: body?.close ? String(body.close) : null,
    sessionCleanup: body?.session_cleanup ? String(body.session_cleanup) : null,
    mergedAt: body?.merged_at ? String(body.merged_at) : null,
    launchId: body?.launch_id ? String(body.launch_id) : null,
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
    raw: row ?? {},
  };
}

/** The chip's words: once a PR exists the PR is the fact, else the agent's state. */
export function flightLabel(flight: AgentFlight): string | null {
  if ((flight.state === "pr_open" || flight.state === "merged") && flight.pr?.number) {
    return `PR #${flight.pr.number} · ${flight.state === "pr_open" ? "OPEN" : "MERGED"}`;
  }
  if (flight.state === "starting") return `${agentWord(flight.agent)} · STARTING`;
  if (flight.state === "working") return `${agentWord(flight.agent)} · WORKING`;
  if (flight.state === "waiting") return `${agentWord(flight.agent)} · ${flight.turnEnd === "idle" ? "IDLE" : "WAITING"}`;
  return null;
}

export function flightTone(state: FlightState): "working" | "warning" | "active" | "success" | "idle" {
  if (state === "starting") return "idle";
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

export function flightForItem(flights: readonly AgentFlight[], item: Parameters<typeof itemOriginRefs>[0]): AgentFlight | null {
  const refs = itemOriginRefs(item);
  if (!refs.length) return null;
  return flights.find((f) => refs.includes(f.originRef) && f.state !== "ended" && f.state !== "expired") ?? null;
}

/** An agent holds the item: STARTING, WORKING, WAITING, PR OPEN, or MERGED
 * with the close still awaiting the owner's confirmation (Secure). Such a row
 * shows its flight and not Hand to agent. */
export function isInFlight(flight: AgentFlight | null | undefined): flight is AgentFlight {
  if (!flight) return false;
  if (["starting", "working", "waiting", "pr_open"].includes(flight.state)) return true;
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
  load(): Promise<void>;
}

let inflight: Promise<void> | null = null;
let again = false;

export const useAgentFlights = create<AgentFlightsState>((set, get) => ({
  sessions: [],
  flights: [],
  loaded: false,
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
        if (again) {
          again = false;
          void get().load();
        }
      });
    return inflight;
  },
}));

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
