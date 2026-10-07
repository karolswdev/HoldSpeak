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
import type { Items } from "../api";
import { objectByRef } from "../world";
import { wireDate } from "../surface/format";
import type { RoomSnapshot } from "../../features/project-room/model";

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
}

/** The drawer's head: the Room's intelligence line. */
export interface DrawerHead {
  needsYou: number;
  /** `NOV 5`: the Project's target date, when it has one. */
  target: string | null;
  targetPassed: boolean;
  /** `ON TRACK` / `AT RISK`, when the Room read its health. */
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
const norm = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

/** The agent's state word (the boards: ASKS, WORKS, PR OPEN). */
export function flightWord(flight: AgentFlight): { label: string; tone: ObjectTone } | null {
  switch (flight.state) {
    case "waiting":
      return { label: "ASKS", tone: "ask" };
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
  const health = room?.health.state === "ok" ? room.health : null;
  return {
    needsYou,
    target: target ? dayWord(target.targetAt) : null,
    targetPassed: Boolean(target?.passed),
    status: health ? (health.assessment === "at_risk" ? "AT RISK" : "ON TRACK") : null,
    statusTone: health?.assessment === "at_risk" ? "fail" : "ok",
  };
}

/** Every object filed in the Project, once each. */
export function drawerMembers(reads: DrawerReads): DrawerMember[] {
  const now = reads.now ?? new Date();
  const out: DrawerMember[] = [];
  const seen = new Set<string>();
  const names = new Set<string>();
  const meetingTitle = new Map<string, string>();
  const where = reads.projectName;
  const deskRef = (ref: string): string | undefined => (objectByRef(reads.items, ref) ? ref : undefined);
  const add = (member: DrawerMember) => {
    if (seen.has(member.ref)) return;
    seen.add(member.ref);
    names.add(`${member.kind}|${norm(member.name)}`);
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

  // Decisions: the Room's records first (the Desk's decision window), then
  // a meeting's recorded decision the records do not already hold.
  if (reads.room?.decisions.state === "ok") {
    for (const d of reads.room.decisions.items) {
      const ref = `decision:${d.id}`;
      add({
        id: ref, ref, kind: "decision", name: d.text || "Decision",
        when: whenWord(d.at, now), whenSort: epoch(d.at),
        facts: { where, from: d.meetingTitle, made: madeWord(d.at, now) },
        renameRef: deskRef(ref),
      });
    }
  }
  for (const d of reads.decisions) {
    const id = text(d.id);
    const name = text(d.text) || text(d.title);
    if (!id || !name || names.has(`decision|${norm(name)}`)) continue;
    const ref = `decision:${id}`;
    const at = d.decided_at ?? d.created_at;
    add({
      id: ref, ref, kind: "decision", name,
      when: whenWord(at, now), whenSort: epoch(at),
      facts: { where, from: meetingTitle.get(text(d.source_meeting_id)), made: madeWord(at, now) },
    });
  }

  // Action items: what needs you, the Room's commitments, an agent's item.
  const action = (id: string, name: string, extra: { at?: unknown; due?: unknown; owner?: string | null; meetingId?: string; meetingTitle?: string }) => {
    const ref = `action:${id}`;
    const flight = flightFor(ref);
    const word = flight ? flightWord(flight) : null;
    // The agent's word on its item (`CLAUDE CODE ASKS`); once a PR exists
    // the PR is the fact (`PR #412 OPEN`), as flightLabel says it.
    const state = word && flight
      ? flight.pr?.number
        ? { label: `PR #${flight.pr.number} ${word.label === "MERGED" ? "MERGED" : "OPEN"}`, tone: word.tone }
        : { label: `${agentWord(flight.agent)} ${word.label}`, tone: word.tone }
      : undefined;
    add({
      id: ref, ref, kind: "action", name,
      when: whenWord(extra.at, now), whenSort: epoch(extra.at),
      state,
      lamp: state,
      facts: {
        where,
        from: extra.meetingTitle ?? (extra.meetingId ? meetingTitle.get(extra.meetingId) : undefined),
        made: madeWord(extra.at, now),
        due: dayWord(extra.due) || undefined,
        owner: flight ? `${agentName(flight.agent)} (agent)` : extra.owner || undefined,
        state,
      },
    });
  };
  if (reads.room?.needsYou.state === "ok") {
    for (const item of reads.room.needsYou.items) {
      const raw = item as unknown as Record<string, unknown>;
      const id = text(item.actionItemId) || text(raw.action_item_id);
      if (!id) continue;
      action(id, item.title, {
        at: item.createdAt ?? item.since,
        due: raw.due_at,
        owner: (raw.owner as string | null) ?? item.ownerHint,
        meetingId: text(raw.meeting_id),
        meetingTitle: item.meetingTitle,
      });
    }
  }
  if (reads.room?.commitments.state === "ok") {
    for (const c of reads.room.commitments.items) action(c.id, c.text, { due: c.dueAt, owner: c.owner });
  }
  for (const f of flights) {
    if (f.kind === "action" && f.id) action(f.id, f.title, {});
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
    const ref = raw.startsWith("desk_decision:") ? `decision:${raw.slice("desk_decision:".length)}` : raw;
    if (!ref.includes(":") || seen.has(ref)) continue;
    const object = objectByRef(reads.items, ref);
    if (!object) continue;
    const kind = object.kind === "coder" ? "agent" : object.kind;
    const record = object.ref as unknown as Record<string, unknown>;
    const at = record.lastModified ?? record.createdAt ?? r.created_at;
    add({
      id: ref, ref, kind, name: object.title,
      when: whenWord(at, now), whenSort: epoch(at),
      facts: { where, made: madeWord(record.createdAt ?? r.created_at, now), branch: text(record.branch) || undefined },
      renameRef: ref,
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
        when: ageWord(at, now), whenSort: epoch(at),
        state, lamp: state,
        facts: { where, from: f.title, owner: `${agentName(f.agent)} (agent)`, state },
      });
    }
    if (f.pr?.number) {
      const ref = `pr:${f.pr.number}`;
      const state = { label: f.pr.state === "merged" || f.state === "merged" ? "MERGED" : "OPEN", tone: f.state === "merged" ? "ok" as const : "info" as const };
      add({
        id: ref, ref, kind: "pr", name: `#${f.pr.number} ${f.title}`,
        url: f.pr.url || undefined,
        state, lamp: state,
        facts: { where, from: f.title, owner: `${agentName(f.agent)} (agent)`, state },
      });
    }
  }
  return out;
}
