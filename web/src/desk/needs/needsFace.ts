/** PHILO-14 A5 — what a Needs-you member looks like as an object.
 *
 *  Board A-5 (canvas README, RATIFIED A): a row is the object's icon, its
 *  name, ONE fact line in plain text, ONE lamp and its word, and the
 *  object's own verbs. This module maps one hub member (`needsYou.ts`, the
 *  one rule on the hub, #788) to that face. It is pure: the drawer
 *  (`NeedsDrawer.tsx`) draws it and wires the verbs.
 *
 *  Movement C repairs (PROPOSAL §3): an item an agent works is that
 *  agent's, never UNASSIGNED; a question is the `ask` lamp, never ⚠.
 */
import type { NeedsYouMember, NeedsYouRoomItem } from "../needsYou";
import type { AgentFlight, CoderSessionRow } from "../agentFlights";
import { flightForItem, isInFlight } from "../agentFlights";
import type { ObjectTone } from "../surface/objects";
import { sourceLabel, type CoverageRecord } from "../coverage";
import { wireDate } from "../surface/format";
import { commandForDoorVerb, supportsDoorVerb, type DoorVerb } from "../chair/doorVerbs";

/** The verb set a row carries (the drawer turns it into library Buttons). */
export type NeedVerbs =
  | { kind: "answer"; sessionKey: string }
  | { kind: "gate"; proposalId: string }
  | { kind: "pr"; url: string; number: number | null }
  | { kind: "session"; sessionKey: string }
  | { kind: "review"; ref: string }
  | { kind: "commitment"; next: "name_owner" | "set_date" | "mark_done"; cardId: string }
  | { kind: "name-owner"; cardId: string | null; openRef: string | null }
  | { kind: "confirm"; proposalId: string; projectId: string }
  | { kind: "door"; card: NonNullable<DoorCardLike> }
  | { kind: "link"; url: string }
  | { kind: "summarize"; meetingId: string }
  | { kind: "setup"; key: string; verb: string }
  | { kind: "open"; ref: string }
  | { kind: "repair"; verb: string; href: string; projectId: string }
  | { kind: "none" };

type DoorCardLike = {
  target_ref?: string;
  open_ref?: string;
  lawful_verbs?: Array<{ name: string; arguments: Record<string, string | number | null | undefined> }>;
  [key: string]: unknown;
} | null | undefined;

export interface NeedFace {
  id: string;
  /** The object kind (its icon): agent, pr, decision, action, meeting, ... */
  kind: string;
  name: string;
  fact: string;
  lamp: { label: string; tone: ObjectTone };
  /** `agents` rows lead the drawer; the rest keep the hub's rank order. */
  group: "agents" | "rest";
  verbs: NeedVerbs;
}

/** `Claude Code` / `Codex`: the agent's name in a sentence. */
export function agentName(agent: string): string {
  if (agent === "codex") return "Codex";
  if (agent === "claude") return "Claude Code";
  return agent ? agent.charAt(0).toUpperCase() + agent.slice(1) : "Agent";
}

/** How long a wait has run: `JUST NOW`, `<n> MIN`, `<n> H`. */
export function waitAgeWord(
  item: { since?: string | null; waitStartedAt?: unknown; ageSeconds?: unknown },
  now: Date,
): string {
  const stamp = Date.parse(String(item.waitStartedAt || item.since || ""));
  const seconds = Number.isFinite(stamp)
    ? Math.max(0, Math.floor((now.getTime() - stamp) / 1000))
    : Math.max(0, Number(item.ageSeconds ?? 0));
  if (seconds < 60) return "JUST NOW";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} MIN`;
  return `${Math.floor(seconds / 3600)} H`;
}

function toneOf(severity: unknown, why: string): ObjectTone {
  if (why.startsWith("OVERDUE")) return "fail";
  const s = String(severity ?? "");
  if (s === "danger" || s === "failure") return "fail";
  if (s === "warning") return "warn";
  return "info";
}

function urlHost(url: string): string {
  try {
    return new URL(url).host.toUpperCase();
  } catch {
    return "";
  }
}

export { urlHost };

/** The session a coder or gate row belongs to, for its name. */
function sessionName(
  sessionKey: string,
  sessions: readonly CoderSessionRow[],
  flights: readonly AgentFlight[],
  fallback: string,
): string {
  const session = sessions.find((s) => s.key === sessionKey);
  const flight = session?.flight ?? flights.find((f) => f.sessionKey === sessionKey) ?? null;
  return flight?.title || fallback || session?.name || "";
}

/** A row kept from the last read of a source that failed since: `observed 09:00`. */
function observedWord(item: NeedsYouRoomItem): string {
  if (!item.fromLastObservation) return "";
  const at = wireDate(String(item.observedAt ?? ""));
  if (!at) return "observed earlier";
  return `observed ${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
}

function agentRowName(agent: string, label: string): string {
  return label ? `${agentName(agent)}: ${label}` : agentName(agent);
}

function doorCardOf(item: NeedsYouRoomItem): DoorCardLike {
  return (item as { _doorCard?: DoorCardLike })._doorCard ?? null;
}

/** The action item an UNASSIGNED Door card writes an owner to. */
function doorDelegateCardId(card: DoorCardLike): string | null {
  for (const verb of card?.lawful_verbs ?? []) {
    if (verb.arguments?.verb === "delegate") {
      const id = verb.arguments.card_id;
      return id ? String(id) : null;
    }
  }
  return null;
}

/** The card's first lawful verb the Desk can run, or null. */
function doorCommand(card: DoorCardLike): boolean {
  const verb = (card?.lawful_verbs ?? []).find((v) => supportsDoorVerb(v as DoorVerb)) as DoorVerb | undefined;
  return Boolean(verb && commandForDoorVerb(verb));
}

/** What a row opens when it has no act of its own: the person a card names,
 *  then the card's own ref, then the row's. */
function openRefOf(item: NeedsYouRoomItem, card: DoorCardLike): string {
  const person = card?.target_ref?.startsWith("people:")
    ? card.target_ref
    : card?.person_relationship_id ? `people:${String(card.person_relationship_id)}` : "";
  return String(person || card?.open_ref || card?.target_ref || item.openRef || "");
}

function attentionFace(
  item: NeedsYouRoomItem,
  ctx: { flights: readonly AgentFlight[]; sessions: readonly CoderSessionRow[]; now: Date },
): NeedFace {
  const id = String(item.id ?? item.ref ?? "");
  const title = String(item.title || "Untitled");
  const why = String(item.why ?? "").toUpperCase();
  const project = String(item.projectName ?? "");
  const source = String(item.source ?? "");

  // R5: an agent asks (a question, or an input or permission prompt).
  if (source === "coder" && item.sessionKey) {
    const key = String(item.sessionKey);
    const agent = String(item.agent ?? key.split(":", 1)[0]);
    const label = sessionName(key, ctx.sessions, ctx.flights, project);
    const approve = item.waitKind === "approve";
    return {
      id,
      kind: "agent",
      name: agentRowName(agent, label),
      fact: String(item.question || item.title || ""),
      lamp: { label: `${approve ? "TO APPROVE" : "ASKS"} · ${waitAgeWord(item, ctx.now)}`, tone: "ask" },
      group: "agents",
      verbs: { kind: "answer", sessionKey: key },
    };
  }
  // Conductor R1: a held tool call of a launched agent.
  if (source === "gate") {
    const key = String(item.sessionKey ?? "");
    const agent = key.split(":", 1)[0] || "agent";
    const command = title.replace(/^Approve:\s*/, "");
    return {
      id,
      kind: "agent",
      name: agentRowName(agent, sessionName(key, ctx.sessions, ctx.flights, project)),
      fact: command,
      lamp: { label: "HELD CALL", tone: "ask" },
      group: "agents",
      verbs: { kind: "gate", proposalId: String(item.ref ?? id).replace(/^gate:/, "") },
    };
  }

  const card = doorCardOf(item);
  const flight = flightForItem(ctx.flights, { ...item, _doorCard: card ?? null });
  // An item an agent works is that agent's: its row is the flight.
  if (isInFlight(flight)) {
    const who = agentName(flight.agent);
    if ((flight.state === "pr_open" || flight.state === "merged") && flight.pr?.url) {
      const number = flight.pr.number;
      return {
        id,
        kind: "pr",
        name: number != null ? `#${number} ${title}` : title,
        fact: [who, flight.projectName || project].filter(Boolean).join(" · "),
        lamp: flight.state === "merged"
          ? { label: "MERGED · TO SECURE", tone: "warn" }
          : { label: "PR OPEN", tone: "ok" },
        group: "agents",
        verbs: { kind: "pr", url: flight.pr.url, number },
      };
    }
    const state = flight.state === "waiting" ? "WAITING" : flight.state === "starting" ? "STARTING" : "WORKING";
    return {
      id,
      kind: item.source === "decision" ? "decision" : "action",
      name: title,
      fact: [who, flight.projectName || project].filter(Boolean).join(" · "),
      lamp: { label: `${who.toUpperCase()} · ${state}`, tone: flight.state === "waiting" ? "ask" : "info" },
      group: "agents",
      verbs: flight.sessionKey ? { kind: "session", sessionKey: flight.sessionKey } : { kind: "none" },
    };
  }

  const owner = String(item.owner ?? "").trim();
  const fact = [owner, project, observedWord(item)].filter(Boolean).join(" · ");
  const lamp = { label: why || "NEEDS YOU", tone: toneOf(item.severity, why) };

  // R4: a decision that waits for the owner's review.
  if (source === "decision" && item.openRef) {
    return { id, kind: "decision", name: title, fact: project, lamp, group: "rest",
      verbs: { kind: "review", ref: String(item.openRef) } };
  }
  // A proposal from a meeting: Confirm.
  if (item.proposalId) {
    return {
      id,
      kind: item.proposalKind === "decision" ? "decision" : "action",
      name: title,
      fact: [item.meetingTitle ? `from ${item.meetingTitle}` : "", project].filter(Boolean).join(" · "),
      lamp: { label: why || "TO CONFIRM", tone: "warn" },
      group: "rest",
      verbs: { kind: "confirm", proposalId: String(item.proposalId), projectId: String(item.projectId ?? "") },
    };
  }
  // A Room commitment: ONE lawful next act.
  if (source === "commitment" && item.actionItemId) {
    const next = item.nextAction
      ?? (item.unknowns?.includes("owner") ? "name_owner"
        : item.unknowns?.includes("due") ? "set_date" : "mark_done");
    return { id, kind: "action", name: title, fact, lamp, group: "rest",
      verbs: { kind: "commitment", next, cardId: String(item.actionItemId) } };
  }
  const ext = item as { _isUnassigned?: boolean; _toReview?: boolean };
  if (ext._toReview && card) {
    const ref = String(card.open_ref || card.target_ref || "");
    return { id, kind: "action", name: title, fact, lamp, group: "rest",
      verbs: ref ? { kind: "review", ref } : { kind: "none" } };
  }
  if (ext._isUnassigned && !owner) {
    return { id, kind: "action", name: title, fact: project, lamp, group: "rest",
      verbs: { kind: "name-owner", cardId: doorDelegateCardId(card), openRef: card?.open_ref ? String(card.open_ref) : null } };
  }
  if (card && doorCommand(card)) {
    return { id, kind: "action", name: title, fact, lamp, group: "rest", verbs: { kind: "door", card } };
  }
  if (item.verbHref) {
    return { id, kind: item.kind === "decision" ? "decision" : "action", name: title, fact, lamp, group: "rest",
      verbs: { kind: "link", url: String(item.verbHref) } };
  }
  const ref = openRefOf(item, card);
  return { id, kind: item.kind === "decision" ? "decision" : "action", name: title, fact, lamp, group: "rest",
    verbs: ref ? { kind: "open", ref } : { kind: "none" } };
}

/** One hub member as its object face. */
export function needFace(
  member: NeedsYouMember,
  ctx: { flights: readonly AgentFlight[]; sessions: readonly CoderSessionRow[]; now: Date },
): NeedFace {
  if (member.kind === "blocker" && member.blocker) {
    return {
      id: member.ref,
      kind: "conductor",
      name: member.blocker.label,
      fact: "Meeting summaries",
      lamp: { label: "SETUP", tone: "warn" },
      group: "rest",
      verbs: { kind: "setup", key: member.blocker.key, verb: member.blocker.verb },
    };
  }
  if (member.kind === "meeting" && member.meeting) {
    const meeting = member.meeting;
    const job = String(meeting.intelJob?.status ?? "").toLowerCase();
    const retrying = job === "queued" || job === "retrying";
    const minutes = meeting.durationSeconds ? Math.max(1, Math.round(meeting.durationSeconds / 60)) : 0;
    return {
      id: member.ref,
      kind: "meeting",
      name: meeting.title || "Untitled meeting",
      fact: [minutes ? `${minutes} min` : "", retrying ? "summary retrying" : "summary failed"].filter(Boolean).join(" · "),
      lamp: retrying ? { label: "RETRYING", tone: "warn" } : { label: "NO SUMMARY", tone: "fail" },
      group: "rest",
      verbs: { kind: "summarize", meetingId: meeting.id },
    };
  }
  return attentionFace(member.item ?? ({} as NeedsYouRoomItem), ctx);
}

/** The drawer's rows: the agents first (when any), then the rest in the
 *  hub's rank order. */
export function needFaces(
  members: readonly NeedsYouMember[],
  ctx: { flights: readonly AgentFlight[]; sessions: readonly CoderSessionRow[]; now: Date },
): NeedFace[] {
  const faces = members.map((m) => needFace(m, ctx));
  return [...faces.filter((f) => f.group === "agents"), ...faces.filter((f) => f.group === "rest")];
}

/** A source the hub could not read, as a row after the members (UX-CANON
 *  A10: an unknown is never a clear desk). */
export function coverageFace(gap: CoverageRecord): NeedFace {
  const repair = gap.repair ?? null;
  return {
    id: `coverage:${gap.source_id}`,
    kind: gap.kind === "project" ? "project" : "artifact",
    name: sourceLabel(gap),
    fact: String(gap.reason || gap.state),
    lamp: { label: repair?.token || gap.state.toUpperCase(), tone: gap.state === "stale" ? "warn" : "fail" },
    group: "rest",
    verbs: repair
      ? { kind: "repair", verb: repair.verb, href: repair.href, projectId: String(gap.project_id ?? "") }
      : { kind: "none" },
  };
}

/** The head: `N need you`, `Nothing needs you`, or an unknown said as one. */
export function needsHead(count: number, complete: boolean): string {
  if (count > 0) return `${count} need you`;
  return complete ? "Nothing needs you" : "Coverage incomplete";
}
