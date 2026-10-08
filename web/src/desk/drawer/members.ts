/** PHILO-14 A2 — a Project's drawer: its members, composed from the hub's
 *  existing Project reads (the Room's data layer, never its JSX).
 *
 *  Every object filed in the Project becomes one member: a meeting, a
 *  decision, an action item, an artifact, a note, a thread, a repository, a
 *  person, a live agent, a pull request. Pure: the caller does the reads
 *  (`useDrawerData`), this module only names, dedupes and dates them.
 */
import type { GetInfoFacts, ObjectListRow, ObjectTone } from "../surface";
import type { AgentFlight, CoderSessionRow } from "../agentFlights";
import { agentWord } from "../agentFlights";
import { objectSprite } from "../surface/objects/kinds";
import type { Items } from "../api";
import { objectByRef } from "../world";
import { decisionRecordSourceRef } from "../openObject";
import { wireDate } from "../surface/format";
import { roomHealthWord, type RoomSnapshot } from "../../features/project-room/model";

/** One object in a drawer: a list row, plus what Get Info and Open need. */
export interface DrawerMember extends ObjectListRow {
  /** The ref the one open grammar takes (`meeting:<id>`, `coder:<key>`). */
  ref: string;
  /** A pull request opens its page; nothing else carries a URL. */
  url?: string;
  /** The Get Info facts the hub has for this object. */
  facts: GetInfoFacts;
  /** The object's lamp on its icon (the same word as its State). */
  lamp?: { tone: ObjectTone; label: string };
  /** The desk record that renames this object (`kind:id`), when one exists. */
  renameRef?: string;
  /** The object parks through a real park path (PHILO-13-02: meetings). */
  parks?: boolean;
  /** The selected sprite, when `sprite` is given (an agent's own `_sel`). */
  spriteSelected?: string;
}

/** The drawer's head: the Room's intelligence line. */
export interface DrawerHead {
  needsYou: number;
  /** `NOV 5`: the Project's target date, when it has one. */
  target: string | null;
  targetPassed: boolean;
  /** `ON TRACK` / `AT RISK` / `NEW`, when the Room read its health. */
  status: string | null;
  statusTone: ObjectTone;
}

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

/** `NOV 5` (the Room's target-date words). */
export function dayWord(value: unknown): string {
  const d = wireDate(value);
  return d ? `${MONTHS[d.getMonth()]} ${d.getDate()}` : "";
}

/** The When word: `TODAY`, or `OCT 5`. */
export function whenWord(value: unknown, now: Date = new Date()): string {
  const d = wireDate(value);
  if (!d) return "";
  const same =
    d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
  return same ? "TODAY" : dayWord(d);
}

/** The made fact: `TODAY 08:40`, or `OCT 5 08:40`. */
export function madeWord(value: unknown, now: Date = new Date()): string {
  const d = wireDate(value);
  if (!d) return "";
  const clock = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return `${whenWord(d, now)} ${clock}`;
}

/** An agent's age: `42 MIN`, `3 H`, else its day. */
export function ageWord(value: unknown, now: Date = new Date()): string {
  const d = wireDate(value);
  if (!d) return "";
  const minutes = Math.max(0, Math.round((now.getTime() - d.getTime()) / 60000));
  if (minutes < 60) return `${Math.max(1, minutes)} MIN`;
  if (minutes < 24 * 60) return `${Math.round(minutes / 60)} H`;
  return whenWord(d, now);
}

function epoch(value: unknown): number | undefined {
  const d = wireDate(value);
  return d ? d.getTime() : undefined;
}

const text = (value: unknown): string => (typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "");

/** The ref a decision record's opener resolves: a meeting record's source is
 *  a `decisions` row (`decision:<id>` reads `/api/decisions/<id>`); a desk
 *  record's is a desk decision (`desk_decision:<id>`, its own window). */
export function recordRef(sourceType: string | undefined, sourceId: string | undefined): string | null {
  return decisionRecordSourceRef(sourceType, sourceId);
}

/** The producer's kind, in the object vocabulary (kinds.ts). */
export function memberKind(kind: string | undefined, fallback: string): string {
  const k = text(kind).toLowerCase();
  if (!k) return fallback;
  if (k === "action_item" || k === "action") return "action";
  if (k === "decision" || k === "decision_record" || k === "desk_decision") return "decision";
  return k;
}

/** A launch's origin ref in the open grammar (`action_item:` → `action:`).
 *  PHILO-14 A2b: a decision record is named by its source, as the drawer's
 *  decision members are (`records`: record id → `decision:` /
 *  `desk_decision:` ref), so it opens its decision's own window. */
function flightRef(originRef: string, records: ReadonlyMap<string, string> = new Map()): string {
  const [kind, ...rest] = originRef.split(":");
  const id = rest.join(":");
  if (kind === "action_item") return `action:${id}`;
  if (kind === "decision_record") return records.get(id) ?? `decision_record:${id}`;
  return `${kind}:${id}`;
}

/** `owner/repo` from a pull request URL (github.com/<owner>/<repo>/pull/<n>). */
export function prRepo(url: string | undefined): string {
  const m = /^https?:\/\/[^/]+\/([^/]+\/[^/]+)\/pull\/\d+/.exec(text(url));
  return m ? m[1] : "";
}

/** The host a URL leaves for (`GITHUB.COM`), for the egress chip. */
export function urlHost(url: string | undefined): string {
  try {
    return new URL(text(url)).host.toUpperCase();
  } catch {
    return "";
  }
}

/** The agent's state word (the boards: ASKS, WORKS, PR OPEN). */
export function flightWord(flight: AgentFlight): { label: string; tone: ObjectTone } | null {
  switch (flight.state) {
    case "waiting":
      // PHILO-15 B48: a turn that ended with no question is IDLE, not ASKS.
      return flight.turnEnd === "idle" ? { label: "IDLE", tone: "info" } : { label: "ASKS", tone: "ask" };
    case "working":
    case "starting":
      return { label: "WORKS", tone: "info" };
    case "pr_open":
      return { label: "PR OPEN", tone: "info" };
    case "merged":
      return flight.close === "awaiting_confirm" ? { label: "MERGED", tone: "ok" } : null;
    default:
      return null;
  }
}

/** `Claude Code` / `Codex` (the agent's name in a sentence). */
function agentName(agent: string): string {
  const word = agentWord(agent);
  return word.charAt(0) + word.slice(1).toLowerCase().replace(/ (\w)/g, (_m, c: string) => ` ${c.toUpperCase()}`);
}

export interface DrawerReads {
  projectId: string;
  projectName: string;
  room: RoomSnapshot | null;
  meetings: Record<string, unknown>[];
  decisions: Record<string, unknown>[];
  artifacts: Record<string, unknown>[];
  people: { relationship_id: string; display_name: string }[];
  /** `GET /api/projects/<id>/resources`: the refs filed in the Project. */
  resources: { resource_ref: string; created_at?: string; deleted?: boolean }[];
  flights: readonly AgentFlight[];
  sessions: readonly CoderSessionRow[];
  /** The desk's records: they name the filed refs and carry rename paths. */
  items: Items;
  now?: Date;
}

/** The Room's intelligence line, from the one Room snapshot. */
export function drawerHead(room: RoomSnapshot | null): DrawerHead {
  const needsYou = room?.needsYou.state === "ok" ? room.needsYou.count : 0;
  const target = room?.target.state === "ok" && room.target.targetAt ? room.target : null;
  // PHILO-15 lane 12 (B25): an empty Project reads NEW, never ON TRACK.
  const health = roomHealthWord(room);
  return {
    needsYou,
    target: target ? dayWord(target.targetAt) : null,
    targetPassed: Boolean(target?.passed),
    status: health?.word ?? null,
    statusTone: health?.tone ?? "ok",
  };
}

/** The agent's word on its item (`CLAUDE CODE ASKS`); once a PR exists
 *  the PR is the fact (`PR #412 OPEN`), as flightLabel says it. */
function flightState(flight: AgentFlight | null): { label: string; tone: ObjectTone } | undefined {
  const word = flight ? flightWord(flight) : null;
  if (!word || !flight) return undefined;
  return flight.pr?.number
    ? { label: `PR #${flight.pr.number} ${word.label === "MERGED" ? "MERGED" : "OPEN"}`, tone: word.tone }
    : { label: `${agentWord(flight.agent)} ${word.label}`, tone: word.tone };
}

function flightOwner(flight: AgentFlight | null): string | undefined {
  return flight ? `${agentName(flight.agent)} (agent)` : undefined;
}

/** Every object filed in the Project, once each. */
export function drawerMembers(reads: DrawerReads): DrawerMember[] {
  const now = reads.now ?? new Date();
  const out: DrawerMember[] = [];
  const seen = new Set<string>();
  const meetingTitle = new Map<string, string>();
  const where = reads.projectName;
  const deskRef = (ref: string): string | undefined => (objectByRef(reads.items, ref) ? ref : undefined);
  const add = (member: DrawerMember) => {
    if (seen.has(member.ref)) return;
    seen.add(member.ref);
    out.push(member);
  };

  // The agents on this Project's items: the action rows wear their state.
  const flights = reads.flights.filter((f) => f.projectId === reads.projectId);
  const flightFor = (originRef: string) =>
    flights.find((f) => f.originRef === originRef && f.state !== "ended" && f.state !== "expired") ?? null;

  for (const m of reads.meetings) {
    const id = text(m.id);
    if (!id) continue;
    const title = text(m.title) || "Meeting";
    meetingTitle.set(id, title);
    const ref = `meeting:${id}`;
    add({
      id: ref, ref, kind: "meeting", name: title,
      when: whenWord(m.started_at, now), whenSort: epoch(m.started_at),
      facts: { where, made: madeWord(m.started_at, now) },
      renameRef: deskRef(ref), parks: true,
    });
  }

  // Decisions. Identity, never text: a Room record names its source (a
  // meeting record's source is the `decisions` row `decision:<id>` opens; a
  // desk record's is the desk decision), and the lifecycle read names the
  // same `decisions` rows, so one decision is one ref.
  // A confirmed proposal writes a record AND its commitment: the Room folds
  // the pair by the record's commitment id, and so does the drawer.
  const commitmentIds = new Set(
    reads.room?.commitments.state === "ok" ? reads.room.commitments.items.map((c) => c.id) : [],
  );
  const records = new Map<string, string>();
  if (reads.room?.decisions.state === "ok") {
    for (const d of reads.room.decisions.items) {
      const ref = recordRef(d.sourceType, d.sourceId);
      if (ref && d.id) records.set(d.id, ref);
      if (!ref || (d.commitmentId && commitmentIds.has(d.commitmentId))) continue;
      // An agent on the record: the decision wears its state.
      const state = flightState(flightFor(`decision_record:${d.id}`));
      add({
        id: ref, ref, kind: memberKind(d.kind, "decision"), name: d.text || "Decision",
        when: whenWord(d.at, now), whenSort: epoch(d.at),
        state, lamp: state,
        facts: { where, from: d.meetingTitle || undefined, made: madeWord(d.at, now), owner: flightOwner(flightFor(`decision_record:${d.id}`)), state },
        renameRef: ref.startsWith("desk_decision:") ? deskRef(`decision:${ref.slice("desk_decision:".length)}`) : undefined,
      });
    }
  }
  for (const d of reads.decisions) {
    const id = text(d.id);
    if (!id) continue;
    const ref = `decision:${id}`;
    const at = d.decided_at ?? d.created_at;
    add({
      id: ref, ref, kind: "decision", name: text(d.text) || text(d.title) || "Decision",
      when: whenWord(at, now), whenSort: epoch(at),
      facts: { where, from: meetingTitle.get(text(d.source_meeting_id)), made: madeWord(at, now) },
    });
  }

  // Action items: what needs you, the Room's commitments, an agent's item.
  // Follow-through keys its card by the action item: `action:<action item id>`.
  const action = (ref: string, kind: string, name: string, extra: { at?: unknown; due?: unknown; owner?: string | null; meetingId?: string; meetingTitle?: string }, originRef = ref) => {
    const flight = flightFor(originRef);
    const state = flightState(flight);
    add({
      id: ref, ref, kind, name,
      when: whenWord(extra.at, now), whenSort: epoch(extra.at),
      state,
      lamp: state,
      facts: {
        where,
        from: extra.meetingTitle || (extra.meetingId ? meetingTitle.get(extra.meetingId) : undefined),
        made: madeWord(extra.at, now),
        due: dayWord(extra.due) || undefined,
        owner: flightOwner(flight) ?? (extra.owner || undefined),
        state,
      },
    });
  };
  if (reads.room?.needsYou.state === "ok") {
    for (const item of reads.room.needsYou.items) {
      const raw = item as unknown as Record<string, unknown>;
      const id = text(item.actionItemId) || text(raw.action_item_id);
      if (!id) continue;
      action(`action:${id}`, "action", item.title, {
        at: item.createdAt ?? item.since,
        due: raw.due_at,
        owner: (raw.owner as string | null) ?? item.ownerHint,
        meetingId: text(raw.meeting_id),
        meetingTitle: item.meetingTitle,
      });
    }
  }
  if (reads.room?.commitments.state === "ok") {
    for (const c of reads.room.commitments.items) {
      // A commitment with an action item is that item's card; one without
      // opens as the Room opens it (`commitment:<id>`).
      const ref = c.actionItemId ? `action:${c.actionItemId}` : `commitment:${c.id}`;
      action(ref, memberKind(c.kind, "action"), c.text, { due: c.dueAt, owner: c.owner });
    }
  }
  const decisionsRead = reads.room?.decisions.state === "ok";
  for (const f of flights) {
    if (!f.originRef.includes(":") || !f.id) continue;
    const ref = flightRef(f.originRef, records);
    // A record the Room's decisions did not read cannot be named by its
    // source; it would be a second copy of its decision (the head says
    // DECISIONS · NOT READ).
    if (ref.startsWith("decision_record:") && reads.room && !decisionsRead) continue;
    action(ref, memberKind(f.kind, "action"), f.title, {}, f.originRef);
  }

  for (const a of reads.artifacts) {
    const id = text(a.id);
    if (!id) continue;
    const ref = `artifact:${id}`;
    add({
      id: ref, ref, kind: "artifact", name: text(a.title) || "Artifact",
      when: whenWord(a.created_at, now), whenSort: epoch(a.created_at),
      facts: { where, from: meetingTitle.get(text(a.meeting_id)), made: madeWord(a.created_at, now) },
      renameRef: deskRef(ref),
    });
  }

  // The refs filed in the Project (notes, threads, a repository, a desk
  // decision), named by the desk's own records.
  for (const r of reads.resources) {
    if (r.deleted) continue;
    const raw = text(r.resource_ref);
    // The filed ref verbatim (`desk_decision:<id>` stays itself: it is the
    // identity a Room record of a desk decision carries too).
    const ref = raw;
    if (!ref.includes(":") || seen.has(ref)) continue;
    const deskName = ref.startsWith("desk_decision:") ? `decision:${ref.slice("desk_decision:".length)}` : ref;
    const object = objectByRef(reads.items, deskName);
    if (!object) continue;
    const kind = object.kind === "coder" ? "agent" : object.kind;
    const record = object.ref as unknown as Record<string, unknown>;
    const at = record.lastModified ?? record.createdAt ?? r.created_at;
    add({
      id: ref, ref, kind, name: object.title,
      when: whenWord(at, now), whenSort: epoch(at),
      facts: { where, made: madeWord(record.createdAt ?? r.created_at, now), branch: text(record.branch) || undefined },
      renameRef: deskName,
    });
  }

  for (const p of reads.people) {
    if (!p.relationship_id) continue;
    const ref = `people:${p.relationship_id}`;
    add({ id: ref, ref, kind: "person", name: p.display_name || "Person", facts: { where } });
  }

  // The live agents on this Project, and the pull requests they opened.
  for (const f of flights) {
    const word = flightWord(f);
    if (f.sessionKey && word && f.state !== "pr_open") {
      const session = reads.sessions.find((s) => s.key === f.sessionKey);
      const at = session?.raw && (session.raw.session as Record<string, unknown> | undefined)?.updated_at;
      const ref = `coder:${f.sessionKey}`;
      const state = { label: word.label, tone: word.tone };
      add({
        id: ref, ref, kind: "agent", name: `${agentName(f.agent)}: ${f.title}`,
        // The agent's own sprite (Codex keeps its face; PHILO-14 A0c r2).
        sprite: objectSprite("agent", ref, "rest", 64, f.agent),
        spriteSelected: objectSprite("agent", ref, "sel", 64, f.agent),
        when: ageWord(at, now), whenSort: epoch(at),
        state, lamp: state,
        facts: { where, from: f.title, owner: `${agentName(f.agent)} (agent)`, state },
      });
    }
    if (f.pr?.number) {
      // Repository-qualified: two repositories' #412 are two objects.
      const ref = `pr:${prRepo(f.pr.url) || f.projectId}#${f.pr.number}`;
      const state = { label: f.pr.state === "merged" || f.state === "merged" ? "MERGED" : "OPEN", tone: f.state === "merged" ? "ok" as const : "info" as const };
      add({
        // PHILO-15 B50: the PR's own title; the item it is for stays a fact.
        id: ref, ref, kind: "pr", name: `#${f.pr.number} ${f.pr.title || f.title}`,
        url: f.pr.url || undefined,
        state, lamp: state,
        facts: { where, from: f.title, owner: `${agentName(f.agent)} (agent)`, state },
      });
    }
  }
  return out;
}
