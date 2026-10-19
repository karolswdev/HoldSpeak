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
  type AgentScreen,
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
export type LiveState = "ask" | "held" | "idle" | "pr" | "work" | "done" | "queued" | "no_signal";

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
  /** live, done: the turn the owner has not opened yet (Betterment AG0). */
  isNew?: boolean;
  /** live, done: the done turn's id (the seen mark names it). */
  turnId?: string | null;
  /** stale: the flight's state (Betterment AG6: `stopped_by_restart` offers Resume). */
  flightState?: AgentFlight["state"];
  /** live: the desk's own answer (Betterment AG3). */
  deskAnswer?: AgentFlight["deskAnswer"];
  /** live: the agent's screen as the hub's rules read it (Betterment AG7):
   *  the command an approval wants to run, the numbered choices. */
  screen?: AgentScreen | null;
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

const AGENT_IDS: readonly AgentId[] = ["claude", "codex", "pi"];

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
    case "done":
      return { tone: "ok", label: "DONE" };
    case "queued":
      // Betterment AG5: the hand waits for a free agent.
      return { tone: "info", label: "WAITS" };
    case "no_signal":
      // Betterment AG7: nothing told its state for ten minutes.
      return { tone: "info", label: "NO SIGNAL" };
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
  if (flight.state === "done") return "done";
  if (flight.state === "queued") return "queued";
  if (flight.state === "no_signal") return "no_signal";
  // Betterment AG7: an approval prompt the screen read is "Wants to run".
  if (flight.state === "waiting" && flight.screen?.wait === "approve" && flight.stateSource === "screen") return "held";
  if (flight.state === "waiting") return flight.turnEnd === "idle" ? "idle" : "ask";
  if (flight.state === "pr_open" || flight.state === "merged") return "pr";
  return "work";
}

/** A stale launch's close receipt, in words (`ENDED`, `PR #413 MERGED · ITEM CLOSED`). */
export function closeReceipt(flight: AgentFlight): string {
  const words: string[] = [];
  if (flight.state === "merged") words.push(flight.pr?.number ? `PR #${flight.pr.number} MERGED` : "MERGED");
  else if (flight.state === "expired") words.push("SESSION GONE");
  else if (flight.state === "stopped_by_restart") words.push("STOPPED BY RESTART");
  else if (flight.state === "resume_failed") words.push("COULD NOT RESUME");
  else words.push("ENDED");
  if (flight.close === "closed") words.push("ITEM CLOSED");
  else if (flight.close === "linked") words.push("ITEM LINKED");
  else if (flight.close === "already_closed") words.push("ITEM WAS CLOSED");
  else if (flight.close && flight.close !== "awaiting_confirm") words.push(codeWords(flight.close));
  if (flight.sessionCleanup === "killed") words.push("SESSION STOPPED");
  return words.join(" · ");
}

/** PHILO-17 U32: a coder can run when it is on this Mac and its hooks are in.
 *  The sign-in blocks only when the hub read it as signed out; an unread
 *  sign-in (Claude Code keeps its token in the Keychain) does not block: the
 *  Get Info says SIGN-IN NOT CHECKED as a fact. NO HOOKS is not ready. */
export function canRun(row: AgentRow): boolean {
  return row.installed && row.hooks === "installed" && (row.signed_in as string) !== "no";
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
            { key: "signin", word: "Sign-in", value: row.signed_in === "yes" ? "SIGNED IN" : "NOT CHECKED" },
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
  const turnOf = (flight: AgentFlight | null | undefined): "done" | "idle" | null =>
    flight?.turnEnd === "done" || flight?.turnEnd === "idle" ? flight.turnEnd : null;
  const asking = (row: CoderSessionRow) => agentState(row) === "ask" && !turnOf(row.flight);
  for (const row of [...sessionRows.filter(asking), ...sessionRows.filter((r) => !asking(r))]) {
    liveKeys.add(row.key);
    const flight = row.flight;
    const launchId = flight?.launchId ?? null;
    // PHILO-15 15: a turn end the responder read as DONE / IDLE is not an ask.
    const turned = turnOf(flight);
    const state: LiveState = turned && sessionState(row) === "ask" ? turned : sessionState(row);
    const lamp = liveLamp(state, flight?.pr?.number);
    const raw = (row.raw?.session ?? row.raw ?? {}) as Record<string, unknown>;
    // Betterment AG8: an ask is as old as its wait, not its last hook.
    const at = (state === "ask" || state === "held") && raw.wait_started_at ? raw.wait_started_at : raw.updated_at;
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
      isNew: state === "done" && Boolean(flight?.isNew),
      turnId: flight?.turnId ?? null,
      deskAnswer: flight?.deskAnswer ?? null,
      screen: flight?.screen ?? row.screen ?? null,
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
    // Betterment AG5: a queued hand has no launch yet; its queue id names it.
    const ref = flight.launchId ? `launch:${flight.launchId}` : flight.queueId ? `queue:${flight.queueId}` : null;
    if (!inFlight(flight) || !ref) continue;
    if (flight.sessionKey && liveKeys.has(flight.sessionKey)) continue;
    const state = flightState(flight);
    const lamp = flight.state === "starting"
      ? { tone: "info" as const, label: "STARTS" }
      : flight.state === "resuming"
        ? { tone: "info" as const, label: "RESUMES" }
        : liveLamp(state, flight.pr?.number);
    const at = flight.launchId ? reads.launchedAt[flight.launchId] : flight.queuedAt ?? undefined;
    add({
      id: ref,
      ref,
      role: "live",
      live: state,
      agent: flight.agent,
      kind: "coder",
      kindWord: "AGENT",
      name: `${titleOf(flight.agent)}: ${shortItemName(flight.title)}`,
      ...sprites(flight.agent, ref),
      when: ageWord(at, now),
      whenSort: wireDate(at)?.getTime(),
      state: lamp,
      lamp,
      sessionKey: flight.sessionKey,
      launchId: flight.launchId,
      isNew: state === "done" && Boolean(flight.isNew),
      turnId: flight.turnId ?? null,
      deskAnswer: flight.deskAnswer ?? null,
      screen: flight.screen ?? null,
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
      flightState: flight.state,
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
  /** The hub's own count of agents that work or need him and its limit
   *  (Betterment AG5: `working_launches`, the setting `agents.working_at_once`);
   *  null when the hub did not serve it. */
  launches: { live: number; cap: number } | null;
}

export function conductorHead(
  members: readonly ConductorMember[],
  launches: { live: number; cap: number } | null,
): ConductorHead {
  const live = members.filter((m) => m.role === "live");
  const ask = live.filter((m) => m.live === "ask" || m.live === "held").length;
  // Betterment AG0: a finished agent is not at work; AG5: nor a queued hand;
  // AG7: nor one that sends no signal.
  const done = live.filter((m) => m.live === "done" || m.live === "queued" || m.live === "no_signal").length;
  return { atWork: live.length - ask - done, ask, launches };
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

/* ── Betterment AG8: the Agents list is the fleet ───────────────────────
 * One glance tells him who needs him, who finished and who works
 * (agents/DESIGN.md §4, "The Agents window"; herdr's sidebar). */

/** Where a live agent stands in the list: Needs you, New, Working, Quiet. */
export type FleetRank = 0 | 1 | 2 | 3;
export const FLEET_WORD: Record<FleetRank, string> = { 0: "Needs you", 1: "New", 2: "Working", 3: "Quiet" };

export function fleetRank(member: ConductorMember): FleetRank {
  if (member.live === "ask" || member.live === "held") return 0;
  if (member.live === "done") return member.isNew ? 1 : 3;
  if (member.live === "idle" || member.live === "no_signal") return 3;
  return 2;
}

/** The live agents in the fleet's order: Needs you (the oldest ask first),
 *  New (the newest first), Working, Quiet (each newest first). */
export function fleetOrder(members: readonly ConductorMember[]): ConductorMember[] {
  const live = members.filter((m) => m.role === "live");
  return live
    .map((m, i) => [m, i] as const)
    .sort(([a, ai], [b, bi]) => {
      const rank = fleetRank(a) - fleetRank(b);
      if (rank) return rank;
      // A hand that waits for a free agent stands after the working ones.
      const waits = Number(a.live === "queued") - Number(b.live === "queued");
      if (waits) return waits;
      const at = a.whenSort ?? 0;
      const bt = b.whenSort ?? 0;
      if (at !== bt) return fleetRank(a) === 0 ? at - bt : bt - at;
      return ai - bi;
    })
    .map(([m]) => m);
}

export interface FleetCounts {
  needYou: number;
  fresh: number;
  working: number;
}

export function fleetCounts(members: readonly ConductorMember[]): FleetCounts {
  const live = members.filter((m) => m.role === "live");
  return {
    needYou: live.filter((m) => fleetRank(m) === 0).length,
    fresh: live.filter((m) => fleetRank(m) === 1).length,
    // A queued hand waits; it does not work.
    working: live.filter((m) => fleetRank(m) === 2 && m.live !== "queued").length,
  };
}

/** `2 need you · 1 new · 2 working`; only what is there (no zero). */
export function fleetWords(counts: FleetCounts): string {
  return [
    counts.needYou ? `${counts.needYou} ${counts.needYou === 1 ? "needs" : "need"} you` : "",
    counts.fresh ? `${counts.fresh} new` : "",
    counts.working ? `${counts.working} working` : "",
  ].filter(Boolean).join(" · ");
}

export interface FleetGroup {
  /** The project's name; "" for agents on no project. */
  project: string;
  members: ConductorMember[];
  /** The worst state of its agents (herdr's workspace rollup). */
  worst: FleetRank;
}

/** The fleet by project, only when the agents span two or more projects;
 *  else null (no group lines). The group with the worst state leads. */
export function fleetGroups(members: readonly ConductorMember[]): FleetGroup[] | null {
  const ordered = fleetOrder(members);
  const projects = new Map<string, ConductorMember[]>();
  for (const m of ordered) {
    const name = String(m.facts.where ?? "");
    projects.set(name, [...(projects.get(name) ?? []), m]);
  }
  if ([...projects.keys()].filter(Boolean).length < 2) return null;
  return [...projects.entries()]
    .map(([project, rows]) => ({
      project,
      members: rows,
      worst: Math.min(...rows.map(fleetRank)) as FleetRank,
    }))
    .sort((a, b) => a.worst - b.worst || (a.project ? 0 : 1) - (b.project ? 0 : 1) || a.project.localeCompare(b.project));
}

/** The Dock tile's state: the worst lamp, a dot for New, the count that
 *  needs him (null with no live agent: the tile says nothing). */
export function fleetTile(members: readonly ConductorMember[]): { lamp: "ask" | "new" | "work" | null; needYou: number; fresh: boolean } {
  const counts = fleetCounts(members);
  const lamp = counts.needYou ? "ask" : counts.fresh ? "new" : counts.working ? "work" : null;
  return { lamp, needYou: counts.needYou, fresh: counts.fresh > 0 };
}
