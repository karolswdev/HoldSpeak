/** PHILO-14 C4 — the Conductor drawer's members (ratified board A-4: the
 *  Conductor window, a drawer of agent icons).
 *
 *  Three kinds of member, composed from reads that exist:
 *
 *  - READY: each coding agent the hub found on this Mac (`agents_detect`,
 *    `GET /api/onboarding/agents`): Claude Code, Codex. Kind `agent`.
 *  - LIVE: every live agent session (the screen's agent objects, the same
 *    rows and lamps) and every launch still in flight that has no live
 *    session row (starting; PR open after the session left). Kind `coder`,
 *    named `<Agent>: <item short name>`.
 *  - STALE: a launch that ended in the last 24 h, on its `_stale` sprite,
 *    with its close receipt.
 *
 *  Pure: the window does the reads, this module names and orders them.
 */
import type { GetInfoFacts, ObjectListRow, ObjectTone } from "../surface";
import { spriteUrl } from "../sprites";
import {
  isInFlight,
  liveAgentSessions,
  type AgentFlight,
  type CoderSessionRow,
} from "../agentFlights";
import { agentName, agentState, shortItemName } from "../screen/compose";
import { AGENT_NAME, type AgentId, type AgentRow } from "../firstrun/agentsStep";
import { codeWords } from "../firstrun/AgentsCard";
import { ageWord, madeWord } from "../drawer/members";
import { wireDate } from "../surface/format";

/** An ended launch stays in the drawer this long (stale); the hub cuts its
 *  `history` the same way, on the END of the launch. */
export const STALE_WINDOW_MS = 24 * 60 * 60 * 1000;

export type ConductorRole = "ready" | "live" | "stale";
export type LiveState = "ask" | "held" | "idle" | "pr" | "work";

export interface ConductorMember extends ObjectListRow {
  role: ConductorRole;
  /** The ref the open grammar takes: `launch:<id>` (the lane) or
   *  `coder:<agent>:<session>` (a session no launch holds); a ready agent's
   *  `agent:<id>` opens its Get Info. */
  ref: string;
  agent: string;
  spriteSelected?: string;
  lamp?: { tone: ObjectTone; label: string };
  facts: GetInfoFacts;
  /** live: the lamp's state; the head counts it. */
  live?: LiveState;
  sessionKey?: string | null;
  launchId?: string | null;
  /** ready: the detect row (Install hooks, Copy install). */
  detect?: AgentRow;
  /** stale: the close receipt (`PR #413 MERGED · ITEM CLOSED`). */
  receipt?: string;
}

export interface ConductorReads {
  /** null: not read yet, or the read failed (the window says which). */
  detect: readonly AgentRow[] | null;
  sessions: readonly CoderSessionRow[];
  flights: readonly AgentFlight[];
  /** `launched_at` per launch id (the flight wire's clock). */
  launchedAt: Readonly<Record<string, string>>;
  /** The route's `history`: every launch that ended in the last 24 h. */
  history?: readonly AgentFlight[];
  /** `ended_at` per launch id. */
  endedAt?: Readonly<Record<string, string>>;
  now?: Date;
}

const AGENT_IDS: readonly AgentId[] = ["claude", "codex"];

/** The list's group (the Floor list's `group`): askers first in every view. */
export const GROUP = { ask: 0, work: 1, ready: 2, stale: 3 } as const;
function liveGroup(state: LiveState): number {
  return state === "ask" || state === "held" ? GROUP.ask : GROUP.work;
}

/** `isInFlight` as a plain boolean (its type guard narrows the else to never). */
const inFlight = (flight: AgentFlight): boolean => isInFlight(flight);

function titleOf(agent: string): string {
  return AGENT_NAME[agent as AgentId] ?? agent;
}

function sprites(agent: string, id: string, stale = false) {
  return {
    sprite: spriteUrl("agent", id, stale ? "stale" : "rest", agent),
    spriteSelected: spriteUrl("agent", id, "sel", agent),
  };
}

/** The screen's lamp words, with HELD for a permission prompt. */
function liveLamp(state: LiveState, pr: number | null | undefined): { tone: ObjectTone; label: string } {
  switch (state) {
    case "ask":
      return { tone: "ask", label: "ASKS" };
    case "held":
      return { tone: "ask", label: "HELD" };
    case "idle":
      // PHILO-15 B48: the turn ended with no question.
      return { tone: "info", label: "IDLE" };
    case "pr":
      return { tone: "ok", label: pr ? `PR #${pr}` : "PR OPEN" };
    default:
      return { tone: "info", label: "WORKS" };
  }
}

function sessionState(row: CoderSessionRow): LiveState {
  const state = agentState(row);
  if (state === "ask") {
    const raw = (row.raw?.session ?? row.raw ?? {}) as Record<string, unknown>;
    if (String(raw.notification_type ?? "") === "permission_prompt") return "held";
  }
  return state;
}

function flightState(flight: AgentFlight): LiveState {
  if (flight.state === "waiting") return flight.turnEnd === "idle" ? "idle" : "ask";
  if (flight.state === "pr_open" || flight.state === "merged") return "pr";
  return "work";
}

/** A stale launch's close receipt, in words (`ENDED`, `PR #413 MERGED · ITEM CLOSED`). */
export function closeReceipt(flight: AgentFlight): string {
  const words: string[] = [];
  if (flight.state === "merged") words.push(flight.pr?.number ? `PR #${flight.pr.number} MERGED` : "MERGED");
  else if (flight.state === "expired") words.push("SESSION GONE");
  else words.push("ENDED");
  if (flight.close === "closed") words.push("ITEM CLOSED");
  else if (flight.close === "linked") words.push("ITEM LINKED");
  else if (flight.close === "already_closed") words.push("ITEM WAS CLOSED");
  else if (flight.close && flight.close !== "awaiting_confirm") words.push(codeWords(flight.close));
  if (flight.sessionCleanup === "killed") words.push("SESSION STOPPED");
  return words.join(" · ");
}

/** The ready rows: version, hooks, sign-in from the detect read. */
export function readyMember(row: AgentRow): ConductorMember {
  const id = `agent:${row.id}`;
  const hooks = row.hooks === "installed" ? "IN" : codeWords(row.hooks);
  const state = !row.installed
    ? { tone: "fail" as const, label: "NOT INSTALLED" }
    : row.hooks !== "installed"
      ? { tone: "warn" as const, label: row.hooks === "missing" ? "NO HOOKS" : `HOOKS ${hooks}` }
      : undefined;
  return {
    id,
    ref: id,
    role: "ready",
    agent: row.id,
    kind: "agent",
    kindWord: "AGENT",
    name: titleOf(row.id),
    ...sprites(row.id, id),
    state,
    lamp: state,
    detect: row,
    group: GROUP.ready,
    facts: {
      state,
      more: row.installed
        ? [
            { key: "version", word: "Version", value: row.version ?? "" },
            { key: "hooks", word: "Hooks", value: hooks },
            { key: "signin", word: "Sign-in", value: row.signed_in === "yes" ? "SIGNED IN" : "UNKNOWN" },
          ]
        : [],
    },
  };
}

/** Every member of the Conductor drawer, once each: ready, then live, then stale. */
export function conductorMembers(reads: ConductorReads): ConductorMember[] {
  const now = reads.now ?? new Date();
  const out: ConductorMember[] = [];
  const seen = new Set<string>();
  const add = (member: ConductorMember) => {
    if (seen.has(member.id)) return;
    seen.add(member.id);
    out.push(member);
  };

  // READY: the detect rows in the agents' own order.
  if (reads.detect) {
    for (const id of AGENT_IDS) {
      const row = reads.detect.find((r) => r.id === id);
      if (row) add(readyMember(row));
    }
  }

  // LIVE: the live sessions (the screen's agent objects).
  const liveKeys = new Set<string>();
  // The agent that asks comes first (the Agents application's pinned
  // order, kept): asking or held, then the rest, each in the hub's order.
  const sessionRows = liveAgentSessions(reads.sessions);
  const asking = (row: CoderSessionRow) => agentState(row) === "ask";
  for (const row of [...sessionRows.filter(asking), ...sessionRows.filter((r) => !asking(r))]) {
    liveKeys.add(row.key);
    const flight = row.flight;
    const launchId = flight?.launchId ?? null;
    const state = sessionState(row);
    const lamp = liveLamp(state, flight?.pr?.number);
    const raw = (row.raw?.session ?? row.raw ?? {}) as Record<string, unknown>;
    const at = raw.updated_at;
    // A launched agent is its launch for the launch's whole life (Astra r1
    // on #947, P2): the session key is a fact on it, never its identity.
    add({
      id: launchId ? `launch:${launchId}` : `coder:${row.key}`,
      ref: launchId ? `launch:${launchId}` : `coder:${row.key}`,
      role: "live",
      live: state,
      agent: row.agent,
      kind: "coder",
      kindWord: "AGENT",
      name: agentName(row),
      ...sprites(row.agent, row.key),
      when: ageWord(at, now),
      whenSort: wireDate(at)?.getTime(),
      state: lamp,
      lamp,
      sessionKey: row.key,
      launchId,
      group: liveGroup(state),
      facts: {
        where: flight?.projectName || undefined,
        from: flight?.title || row.name,
        owner: `${titleOf(row.agent)} (agent)`,
        state: lamp,
        made: launchId ? madeWord(reads.launchedAt[launchId], now) || undefined : undefined,
      },
    });
  }

  // LIVE: a launch in flight with no live session row (starting; its PR is
  // open after the session left).
  for (const flight of reads.flights) {
    if (!inFlight(flight) || !flight.launchId) continue;
    if (flight.sessionKey && liveKeys.has(flight.sessionKey)) continue;
    const state = flightState(flight);
    const lamp = flight.state === "starting" ? { tone: "info" as const, label: "STARTS" } : liveLamp(state, flight.pr?.number);
    const at = reads.launchedAt[flight.launchId];
    add({
      id: `launch:${flight.launchId}`,
      ref: `launch:${flight.launchId}`,
      role: "live",
      live: state,
      agent: flight.agent,
      kind: "coder",
      kindWord: "AGENT",
      name: `${titleOf(flight.agent)}: ${shortItemName(flight.title)}`,
      ...sprites(flight.agent, flight.launchId),
      when: ageWord(at, now),
      whenSort: wireDate(at)?.getTime(),
      state: lamp,
      lamp,
      sessionKey: flight.sessionKey,
      launchId: flight.launchId,
      group: liveGroup(state),
      facts: {
        where: flight.projectName || undefined,
        from: flight.title,
        owner: `${titleOf(flight.agent)} (agent)`,
        state: lamp,
        made: madeWord(at, now) || undefined,
      },
    });
  }

  // STALE: a launch that ended in the last 24 h (the hub's history: each
  // launch once, a relaunch keeps the earlier one), cut on its END.
  const ended = reads.endedAt ?? {};
  for (const flight of reads.history ?? []) {
    if (inFlight(flight) || !flight.launchId) continue;
    const at = ended[flight.launchId] || flight.mergedAt;
    const when = wireDate(at);
    if (!when || now.getTime() - when.getTime() > STALE_WINDOW_MS) continue;
    const receipt = closeReceipt(flight);
    const state = { tone: flight.state === "merged" ? ("ok" as const) : ("info" as const), label: receipt };
    add({
      id: `launch:${flight.launchId}`,
      ref: `launch:${flight.launchId}`,
      role: "stale",
      agent: flight.agent,
      kind: "coder",
      kindWord: "AGENT",
      name: `${titleOf(flight.agent)}: ${shortItemName(flight.title)}`,
      ...sprites(flight.agent, flight.launchId, true),
      when: ageWord(at, now),
      whenSort: when.getTime(),
      state,
      receipt,
      sessionKey: flight.sessionKey,
      launchId: flight.launchId,
      group: GROUP.stale,
      facts: {
        where: flight.projectName || undefined,
        from: flight.title,
        owner: `${titleOf(flight.agent)} (agent)`,
        state,
        made: madeWord(reads.launchedAt[flight.launchId], now) || undefined,
      },
    });
  }
  // Asking first in every view (icons follow this order; the list sorts
  // within `group`): asking/held, at work, ready, stale.
  return out
    .map((m, i) => [m, i] as const)
    .sort((a, b) => (a[0].group ?? 0) - (b[0].group ?? 0) || a[1] - b[1])
    .map(([m]) => m);
}

export interface ConductorHead {
  atWork: number;
  ask: number;
  /** The hub's own count of running launches and its cap (`live_launches`,
   *  `MAX_LIVE_LAUNCHES`); null when the hub did not serve it. */
  launches: { live: number; cap: number } | null;
}

export function conductorHead(
  members: readonly ConductorMember[],
  launches: { live: number; cap: number } | null,
): ConductorHead {
  const live = members.filter((m) => m.role === "live");
  const ask = live.filter((m) => m.live === "ask" || m.live === "held").length;
  return { atWork: live.length - ask, ask, launches };
}

/** `2 AT WORK · 1 ASK`, then `3 OF 3` only at the hub's cap; a zero is never said (A.8). */
export function headWords(head: ConductorHead): string[] {
  const cap = head.launches;
  return [
    head.atWork > 0 ? `${head.atWork} AT WORK` : "",
    head.ask > 0 ? `${head.ask} ASK` : "",
    cap && cap.live >= cap.cap ? `${cap.live} OF ${cap.cap}` : "",
  ].filter(Boolean);
}
