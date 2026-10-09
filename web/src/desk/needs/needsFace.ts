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
import { SELF_OWNER_NAMES, type NeedsYouMember, type NeedsYouRoomItem } from "../needsYou";
import type { AgentFlight, CoderSessionRow } from "../agentFlights";
import { flightForItem, isInFlight } from "../agentFlights";
import type { ObjectTone } from "../surface/objects";
import { sourceLabel, type CoverageRecord } from "../coverage";
import { wireDate } from "../surface/format";
import { needYouWords } from "../surface/count";
import { commandForDoorVerb, supportsDoorVerb, type DoorVerb } from "../chair/doorVerbs";

/** The verb set a row carries (the drawer turns it into library Buttons). */
export type NeedVerbs =
  | { kind: "answer"; sessionKey: string }
  | { kind: "gate"; proposalId: string }
  /** A held call whose command the hub cannot show whole: Deny, and Open on
   *  the agent's lane (Raw shows the whole command there); never Approve. */
  | { kind: "gate-cut"; proposalId: string; sessionKey: string }
  | { kind: "pr"; url: string; number: number | null }
  | { kind: "session"; sessionKey: string }
  | { kind: "review"; ref: string }
  | { kind: "commitment"; next: "name_owner" | "set_date" | "mark_done"; cardId: string }
  | { kind: "name-owner"; cardId: string | null; openRef: string | null }
  /** A proposal from a meeting, Project or not: Confirm / Defer / Decline
   *  (PHILO-15 08, B03). */
  | { kind: "confirm"; proposalId: string; projectId: string; meetingId: string }
  | { kind: "door"; card: NonNullable<DoorCardLike> }
  | { kind: "link"; url: string }
  | { kind: "summarize"; meetingId: string }
  | { kind: "setup"; key: string; verb: string }
  | { kind: "open"; ref: string }
  /** PHILO-15 B61: `watchIds` are the Watches Retry re-checks. */
  | { kind: "repair"; verb: string; href: string; projectId: string; watchIds?: string[]; host?: string }
  | { kind: "arming"; scheduleId: string; refused: boolean }
  | { kind: "calendar" }
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
  /** PHILO-15 15: the fact is a command (a held call): its lines are kept
   *  and it wraps, in the mono face. */
  factCode?: boolean;
  /** Phase 16: the fact is an agent's words (AgentWords, compact). */
  factWords?: boolean;
  lamp: { label: string; tone: ObjectTone };
  /** `agents` rows lead the drawer; the rest keep the hub's rank order. */
  group: "agents" | "rest";
  verbs: NeedVerbs;
  /** What a press on the row body opens (the one open grammar,
   *  `openObject.refOpener`); absent = the row body opens nothing. */
  openRef?: string;
  /** A source row (a source not read, no calendar), not a member. */
  source?: boolean;
  /** PHILO-15 B60: a row drawn under the head that the number does not
   *  count (a source held by quiet hours). */
  uncounted?: boolean;
  /** An agent's ask or held call: the session it belongs to. */
  askOf?: string;
  /** An item an agent works: that agent's session. */
  workedBy?: string;
  /** An agent row: the agent's name (`claude`, `codex`), for its sprite. */
  agent?: string;
  /** The hub's member ref of the row (`ref`, else `id`). */
  memberRef?: string;
  /** An agent ask the hub folded into an item: that item's member ref. */
  foldedInto?: string;
  /** The item's other asks (the row shows the most urgent one): `+N MORE`. */
  moreAsks?: number;
  /** The Project the row names (PHILO-14 A5b): the row draws its Project
   *  button, a generic open, which opens the Project's drawer (A2b). */
  project?: { id: string; name: string };
  /** A proposal is an object in the Room (A2b): the row opens the Room with
   *  THIS proposal selected, never the drawer (the drawer holds no proposals). */
  proposal?: { projectId: string; proposalId: string };
  /** PHILO-15-09 (B12): the row's kind word (`DECISION`, `ACTION`,
   *  `PROPOSAL`, `MEETING`, `AGENT`); a source row has none. */
  kindWord?: string;
}

/** PHILO-15-09 (B12): every member row says what it is. A proposal from a
 *  meeting is a PROPOSAL (decision or action); an agent's row and its PR are
 *  AGENT. A setup blocker and a source row are not objects: no word. */
export function kindWordOf(face: Pick<NeedFace, "kind" | "verbs" | "source">): string | undefined {
  if (face.source) return undefined;
  if (face.verbs.kind === "confirm") return "PROPOSAL";
  switch (face.kind) {
    case "decision": return "DECISION";
    case "action": return "ACTION";
    case "meeting": return "MEETING";
    case "agent":
    case "pr": return "AGENT";
    default: return undefined;
  }
}

/** What the face builder knows of the desk. `multipleProjects`: the rows
 *  draw their Project button, so the fact line does not repeat the name. */
export interface NeedCtx {
  flights: readonly AgentFlight[];
  sessions: readonly CoderSessionRow[];
  now: Date;
  multipleProjects?: boolean;
}

/** `Claude Code` / `Codex`: the agent's name in a sentence. */
export function agentName(agent: string): string {
  if (agent === "codex") return "Codex";
  if (agent === "claude") return "Claude Code";
  if (agent === "pi") return "pi";
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

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** PHILO-15 B74: a past time with its day: `21:23` today, `yesterday 21:23`,
 *  `Tue 21:23` this week, `Oct 3 21:23` before that. */
export function whenWord(at: Date, now: Date = new Date()): string {
  const hhmm = `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
  const day = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const days = Math.round((day(now) - day(at)) / 86_400_000);
  if (days <= 0) return hhmm;
  if (days === 1) return `yesterday ${hhmm}`;
  if (days < 7) return `${WEEKDAYS[at.getDay()]} ${hhmm}`;
  return `${MONTHS[at.getMonth()]} ${at.getDate()} ${hhmm}`;
}

/** A row kept from the last read of a source that failed since: `observed 09:00`. */
function observedWord(item: NeedsYouRoomItem, now?: Date): string {
  if (!item.fromLastObservation) return "";
  const at = wireDate(String(item.observedAt ?? ""));
  if (!at) return "observed earlier";
  return `observed ${whenWord(at, now)}`;
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

function attentionFace(item: NeedsYouRoomItem, ctx: NeedCtx): NeedFace {
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
      factWords: true,
      lamp: { label: `${approve ? "TO APPROVE" : "ASKS"} · ${waitAgeWord(item, ctx.now)}`, tone: "ask" },
      group: "agents",
      verbs: { kind: "answer", sessionKey: key },
      openRef: `coder:${key}`,
      askOf: key,
      agent,
    };
  }
  // Conductor R1: a held tool call of a launched agent.
  if (source === "gate") {
    const key = String(item.sessionKey ?? "");
    const agent = key.split(":", 1)[0] || "agent";
    // The command the hub keeps (its 120-char head; the title is an
    // excerpt); an older hub sends the title alone.
    const head = String(item.command || "") || title.replace(/^Approve:\s*/, "");
    const cut = Boolean(item.argsCut);
    const hidden = Number(item.argsHidden ?? 0);
    // The hub keeps the first 120 chars of the call (a design limit): a cut
    // command says so, and how much is missing.
    const shown = cut ? `${head}… ${hidden > 0 ? `+${hidden} CHARS` : "CUT"}` : head;
    const reason = String(item.holdReason ?? "").trim();
    const command = reason ? `${reason}\n${shown}` : shown;
    const proposalId = String(item.ref ?? id).replace(/^gate:/, "");
    return {
      id,
      kind: "agent",
      name: agentRowName(agent, sessionName(key, ctx.sessions, ctx.flights, project)),
      fact: command,
      factCode: true,
      // PHILO-15 15: the hub keeps 120 chars (Phase 14 law): a cut call is
      // approved in the pane (Raw), and the row says so.
      lamp: { label: cut ? "CUT · APPROVE IN RAW" : "HELD CALL", tone: "ask" },
      group: "agents",
      verbs: cut
        ? { kind: "gate-cut", proposalId, sessionKey: key }
        : { kind: "gate", proposalId },
      openRef: key ? `coder:${key}` : undefined,
      askOf: key || undefined,
      agent,
    };
  }

  const card = doorCardOf(item);
  const openRef = openRefOf(item, card) || undefined;
  // A row that names only its Project opens the Project's drawer (A2b).
  const projectRef = item.projectId ? `project:${String(item.projectId)}` : "";
  // The Project button names the Project (desk with two or more Projects):
  // the fact line does not say it again (UX-CANON A.7).
  const named = Boolean(ctx.multipleProjects && item.projectId && project);
  const factProject = named ? "" : project;
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
        fact: [who, named ? "" : flight.projectName || project].filter(Boolean).join(" · "),
        lamp: flight.state === "merged"
          ? { label: "MERGED · TO SECURE", tone: "warn" }
          : { label: "PR OPEN", tone: "ok" },
        group: "agents",
        verbs: { kind: "pr", url: flight.pr.url, number },
        openRef,
        workedBy: flight.sessionKey ?? undefined,
      };
    }
    const state = flight.state === "waiting" ? "WAITING" : flight.state === "starting" ? "STARTING" : "WORKING";
    return {
      id,
      kind: item.source === "decision" ? "decision" : "action",
      name: title,
      fact: [who, named ? "" : flight.projectName || project].filter(Boolean).join(" · "),
      // The fact line names the agent; the lamp says what it does (one word).
      lamp: { label: state, tone: flight.state === "waiting" ? "ask" : "info" },
      group: "agents",
      verbs: flight.sessionKey ? { kind: "session", sessionKey: flight.sessionKey } : { kind: "none" },
      openRef,
      workedBy: flight.sessionKey ?? undefined,
    };
  }

  const rawOwner = String(item.owner ?? "").trim();
  // The owner himself is not named on his own row.
  const owner = SELF_OWNER_NAMES.includes(rawOwner.toLowerCase()) ? "" : rawOwner;
  const fact = [owner, factProject, observedWord(item, ctx.now)].filter(Boolean).join(" · ");
  const lamp = { label: why || "NEEDS YOU", tone: toneOf(item.severity, why) };

  // R4: a decision that waits for the owner's review.
  if (source === "decision" && item.openRef) {
    return { id, kind: "decision", name: title, fact: factProject, lamp, group: "rest",
      verbs: { kind: "review", ref: String(item.openRef) }, openRef: String(item.openRef) };
  }
  // A proposal from a meeting: Confirm.
  if (item.proposalId) {
    return {
      id,
      kind: item.proposalKind === "decision" ? "decision" : "action",
      name: title,
      fact: [
        item.meetingTitle ? `from ${item.meetingTitle}` : "from a meeting",
        item.proposalDue ? `by ${item.proposalDue}` : "",
        factProject,
      ].filter(Boolean).join(" · "),
      // The act the proposal asks for: decide it, or confirm it.
      lamp: { label: item.proposalKind === "decision" ? "TO DECIDE" : "TO CONFIRM", tone: "warn" },
      group: "rest",
      verbs: {
        kind: "confirm",
        proposalId: String(item.proposalId),
        projectId: String(item.projectId ?? ""),
        meetingId: String(item.meetingId ?? ""),
      },
      // The row opens the Room with this proposal selected (A2b), not the drawer.
      proposal: item.projectId
        ? { projectId: String(item.projectId), proposalId: String(item.proposalId) }
        : undefined,
      // PHILO-15 08: a meeting in no Project has no Room; its row opens the
      // meeting on its Review wing, where the proposal is.
      openRef: !item.projectId && item.meetingId
        ? `meeting:${String(item.meetingId)}?view=review`
        : undefined,
    };
  }
  // A Room commitment: ONE lawful next act.
  if (source === "commitment" && item.actionItemId) {
    const next = item.nextAction
      ?? (item.unknowns?.includes("owner") ? "name_owner"
        : item.unknowns?.includes("due") ? "set_date" : "mark_done");
    return { id, kind: "action", name: title, fact, lamp, group: "rest",
      verbs: { kind: "commitment", next, cardId: String(item.actionItemId) },
      openRef: openRef ?? `action_item:${String(item.actionItemId)}` };
  }
  const ext = item as { _isUnassigned?: boolean; _toReview?: boolean };
  if (ext._toReview && card) {
    const ref = String(card.open_ref || card.target_ref || "");
    return { id, kind: "action", name: title, fact, lamp, group: "rest",
      verbs: ref ? { kind: "review", ref } : { kind: "none" }, openRef };
  }
  if (ext._isUnassigned && !rawOwner) {
    return { id, kind: "action", name: title, fact: factProject, lamp, group: "rest",
      verbs: { kind: "name-owner", cardId: doorDelegateCardId(card), openRef: card?.open_ref ? String(card.open_ref) : null },
      openRef };
  }
  if (card && doorCommand(card)) {
    return { id, kind: "action", name: title, fact, lamp, group: "rest", verbs: { kind: "door", card }, openRef };
  }
  if (item.verbHref) {
    return { id, kind: item.kind === "decision" ? "decision" : "action", name: title, fact, lamp, group: "rest",
      verbs: { kind: "link", url: String(item.verbHref) },
      openRef: openRef ?? (projectRef || undefined) };
  }
  const ref = openRefOf(item, card) || projectRef;
  return { id, kind: item.kind === "decision" ? "decision" : "action", name: title, fact, lamp, group: "rest",
    verbs: ref ? { kind: "open", ref } : { kind: "none" }, openRef: ref || undefined };
}

/** One hub member as its object face. */
export function needFace(member: NeedsYouMember, ctx: NeedCtx): NeedFace {
  const face = memberFace(member, ctx);
  face.kindWord = kindWordOf(face);
  return face;
}

function memberFace(member: NeedsYouMember, ctx: NeedCtx): NeedFace {
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
      openRef: `meeting:${meeting.id}`,
    };
  }
  const item = member.item ?? ({} as NeedsYouRoomItem);
  const face = attentionFace(item, ctx);
  // Every row of a Project names it (an agent's ask names its session instead).
  if (!face.askOf && item.projectId && item.projectName) {
    face.project = { id: String(item.projectId), name: String(item.projectName) };
  }
  face.memberRef = String(item.ref ?? item.id ?? "");
  if (item.foldedInto) face.foldedInto = String(item.foldedInto);
  return face;
}

/** One object, one row (UX-CANON D): when an agent works an item and that
 *  agent asks (a question or a held call), the ITEM row carries the ask: its
 *  icon and name stay the item's; the fact, the lamp and the verbs are the
 *  ask's. The agent's own row is not drawn. An agent with no item keeps its
 *  own row. */
export function foldAsks(faces: readonly NeedFace[]): NeedFace[] {
  // Owner ruling (2026-10-07): one object, one row, always. Every ask on an
  // item rides on its row: the hub's fold first (`foldedInto`: the one
  // count), then the flight's session for an answer that carries no mark.
  const byTarget = new Map<string, NeedFace[]>();
  const bySession = new Map<string, NeedFace[]>();
  for (const face of faces) {
    if (face.foldedInto) byTarget.set(face.foldedInto, [...(byTarget.get(face.foldedInto) ?? []), face]);
    else if (face.askOf) bySession.set(face.askOf, [...(bySession.get(face.askOf) ?? []), face]);
  }
  const folded = new Set<string>();
  const out: NeedFace[] = [];
  for (const face of faces) {
    if (face.askOf) { out.push(face); continue; }
    const asks = [
      ...(face.memberRef ? byTarget.get(face.memberRef) ?? [] : []),
      ...(face.workedBy ? bySession.get(face.workedBy) ?? [] : []),
    ].filter((ask) => !folded.has(ask.id));
    if (!asks.length) { out.push(face); continue; }
    for (const ask of asks) folded.add(ask.id);
    // The most urgent ask leads: a held call before a question.
    const lead = [...asks].sort((a, b) => askRank(a) - askRank(b))[0];
    out.push({
      ...face, fact: lead.fact, factCode: lead.factCode, factWords: lead.factWords, lamp: lead.lamp, verbs: lead.verbs, askOf: lead.askOf, agent: undefined,
      moreAsks: asks.length - 1,
      // The row's Open is the agent's lane, where every ask is answered.
      openRef: lead.askOf ? `coder:${lead.askOf}` : face.openRef,
      proposal: lead.askOf ? undefined : face.proposal,
    });
  }
  return out.filter((face) => !(face.askOf && folded.has(face.id)));
}

function askRank(face: NeedFace): number {
  return face.verbs.kind === "gate" || face.verbs.kind === "gate-cut" ? 0 : 1;
}

/** The drawer's rows: the agents first (when any), then the rest in the
 *  hub's rank order. One object, one row. */
export function needFaces(members: readonly NeedsYouMember[], ctx: NeedCtx): NeedFace[] {
  const faces = foldAsks(members.map((m) => needFace(m, ctx)));
  return [...faces.filter((f) => f.group === "agents"), ...faces.filter((f) => f.group === "rest")];
}

function observedAt(at: string | null | undefined, now?: Date): string {
  const d = at ? wireDate(at) : null;
  return d ? `observed ${whenWord(d, now)}` : "";
}

/** A source the hub could not read, as a row after the members (UX-CANON
 *  A10: an unknown is never a clear desk). PHILO-15 B60: a source held by
 *  HoldSpeak's own quiet hours reads `QUIET UNTIL 08:00` and is not counted. */
export function coverageFace(gap: CoverageRecord, now?: Date): NeedFace {
  const repair = gap.repair ?? null;
  const quiet = gap.state === "quiet";
  // The quiet end is the lamp's word; the fact keeps only the last check.
  const reason = quiet ? "" : String(gap.reason || gap.state);
  return {
    id: `coverage:${gap.source_id}`,
    kind: gap.kind === "project" ? "project" : "artifact",
    name: sourceLabel(gap),
    fact: [reason, observedAt(gap.observed_at, now)].filter(Boolean).join(" · "),
    lamp: {
      label: repair?.token || gap.state.toUpperCase(),
      tone: quiet ? "info" : gap.state === "stale" ? "warn" : "fail",
    },
    group: "rest",
    verbs: repair
      ? {
        kind: "repair", verb: repair.verb, href: repair.href, projectId: String(gap.project_id ?? ""),
        watchIds: (gap.watch_ids ?? []).filter(Boolean),
        ...(gap.host ? { host: String(gap.host) } : {}),
      }
      : { kind: "none" },
    source: true,
    uncounted: quiet || undefined,
  };
}

/** `0:45` under a minute, else `<n> MIN`. */
export function armsWord(seconds: number): string {
  const s = Math.max(0, Math.ceil(seconds));
  if (s < 60) return `0:${String(s).padStart(2, "0")}`;
  return `${Math.ceil(s / 60)} MIN`;
}

/** A scheduled recording about to start: first while it is live. */
export function armingFace(
  arming: { scheduleId: string; title: string },
  secondsLeft: number,
  refusal?: string | null,
): NeedFace {
  const word = armsWord(secondsLeft);
  return {
    id: `arming:${arming.scheduleId}`,
    kind: "meeting",
    name: arming.title || "Scheduled recording",
    // A refused Cancel is named here, by the hub's own reason.
    fact: refusal ? `NOT CANCELLED · ${refusal}` : `Arms in ${word.toLowerCase()}`,
    lamp: { label: `ARMS · ${word}`, tone: refusal ? "fail" : "ask" },
    kindWord: "MEETING",
    group: "agents",
    verbs: { kind: "arming", scheduleId: arming.scheduleId, refused: Boolean(refusal) },
  };
}

/** PARKED (PHILO-15-09, B11): the calendar offer left the rows for the
 *  drawer foot; this row face is kept, unrendered. */
export const CALENDAR_FACE: NeedFace = {
  id: "source:calendar",
  kind: "artifact",
  name: "Calendar",
  fact: "No calendar",
  lamp: { label: "NOT CONNECTED", tone: "info" },
  group: "rest",
  verbs: { kind: "calendar" },
  source: true,
};

/** The quiet footer line: `NEXT · 14:00 · Ledger cutover sync`. */
export function nextWord(next: { label?: string | null; at?: string | null } | null | undefined): string | null {
  if (!next || !next.label) return null;
  const at = next.at ? wireDate(next.at) : null;
  const time = at ? `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}` : "";
  // The Room is named on the week's own row, not on this quiet line.
  return ["NEXT", time, next.label].filter(Boolean).join(" · ");
}

/** The head: `N need you`, `Nothing needs you`, or an unknown said as one. */
export function needsHead(count: number, complete: boolean): string {
  // PHILO-15-09 (B11): `1 needs you`, `3 need you`.
  if (count > 0) return needYouWords(count);
  return complete ? "Nothing needs you" : "Coverage incomplete";
}
