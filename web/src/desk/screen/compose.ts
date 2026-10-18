/** PHILO-14 A1 — the screen's objects, composed from the desk's own reads.
 *
 *  Board A-1 (docs/internal/philo/phase-14/canvas/shots/A-1-1440.png): the
 *  drawers (every Project with its count notch and lamp, People, the
 *  Conductor with the automaton badge), the loose objects (what no Project
 *  holds), the live agents, Needs you, Parked. Pure: the tests compose from
 *  a fixture world. */
import type { Items } from "../api";
import { qualifiedRef } from "../api";
import { isInFlight, liveAgentSessions, type AgentFlight, type CoderSessionRow } from "../agentFlights";
import { needYouWords, objectSprite, type ObjectTone } from "../surface";
import { spriteUrl } from "../sprites";
import { allObjects, objectByRef } from "../world";
import type { ScreenTarget } from "./open";

export type ScreenRole = "drawer" | "needs" | "parked" | "loose" | "agent";

export interface ScreenObject {
  /** Unique on the screen (stamped as data-object-id). */
  key: string;
  role: ScreenRole;
  /** The DeskIcon kind. */
  kind: string;
  kindWord?: string;
  name: string;
  sprite: string;
  spriteSelected: string;
  lamp?: { tone: ObjectTone; count?: number; label?: string };
  /** The count notch alone (no lamp): what runs and asks nothing. */
  count?: number;
  badge?: string;
  ariaExtra?: string;
  /** PHILO-17 (doors): a short line under the name (the People drawer's
   *  next 1:1, `1:1 15:00`). */
  caption?: string;
  /** A read for this drawer failed: it wears NOT READ and a Retry. */
  notRead?: { retry: { type: "project"; id: string } | { type: "people" } };
  target: ScreenTarget;
}

export interface ScreenPerson {
  id: string;
  name: string;
}

export interface ScreenInputs {
  items: Items;
  /** Needs you members by Project id. */
  projectCounts: Record<string, number>;
  /** The desk's Needs you count. */
  needsCount: number;
  /** Refs of the rows Needs you lists (a loose object among them wears a lamp). */
  needsRefs: ReadonlySet<string>;
  /** Held tool calls of launched agents (Needs you `gate:` rows). */
  heldCalls: number;
  sessions: readonly CoderSessionRow[];
  flights: readonly AgentFlight[];
  /** Refs filed in any Project (normalized: `meeting:<id>`, `decision:<id>`, `people:<id>`). */
  filed: ReadonlySet<string>;
  /** People not filed in a Project come out as loose person objects. */
  persons: readonly ScreenPerson[];
  /** False until the membership read answered: loose objects wait for it. */
  membersLoaded: boolean;
  /** Astra's P1 on #939: the Projects whose membership read failed. */
  notRead?: Readonly<Record<string, unknown>>;
  /** A resources read failed: no object's filing is known; nothing is loose. */
  unknownAll?: boolean;
  /** A meetings read failed: no meeting's filing is known. */
  unknownMeetings?: boolean;
  /** People could not be read. */
  peopleNotRead?: boolean;
  /** The next 1:1 (`1:1 15:00`); null or absent draws nothing. */
  peopleCaption?: string | null;
}

const NOT_READ = { tone: "fail" as const, label: "NOT READ" };

/** The kinds that lie loose on the screen (the brief's list). Betterment
 * Q4: a thread is a kept Ask; it lives in Ask ▸ Recent, not on the desk
 * (Save as note puts an answer on the desk). */
const LOOSE_KINDS = new Set(["meeting", "note", "decision", "artifact", "repository"]);

function hasUserOwnedContent(object: { kind: string; ref: unknown }): boolean {
  const value = (object.ref ?? {}) as Record<string, unknown>;
  if (object.kind === "artifact") {
    // Meeting artifacts stay reachable from their meeting record. They do
    // not become a second loose object on the Floor.
    return !value.meetingId && !value.meeting_id;
  }
  if (object.kind === "thread") {
    if (value.has_user_turn === false || value.hasUserTurn === false) return false;
    const turns = Array.isArray(value.turns) ? value.turns : Array.isArray(value.messages) ? value.messages : null;
    if (turns) {
      return turns.some((turn) => {
        const row = (turn ?? {}) as Record<string, unknown>;
        return row.role === "user" || row.speaker === "user" || row.author === "user";
      });
    }
    return Number(value.tokenIn ?? value.token_in ?? 0) > 0 || Boolean(value.lastTurnAt ?? value.last_turn_at);
  }
  if (object.kind === "note") {
    const title = String(value.title ?? "").trim();
    const body = String(value.bodyMarkdown ?? value.body_markdown ?? "").trim();
    return Boolean(title || body);
  }
  return true;
}

/** A Project's ref names its resources by more than one name: one name here. */
export function normalizeRef(ref: string): string {
  const clean = ref.trim();
  const at = clean.indexOf(":");
  if (at < 0) return clean;
  const kind = clean.slice(0, at);
  const id = clean.slice(at + 1);
  if (kind === "desk_decision" || kind === "decision_record") return `decision:${id}`;
  if (kind === "person") return `people:${id}`;
  if (kind === "action_item") return `action:${id}`;
  if (kind === "directory") return `zone:${id}`;
  return `${kind}:${id}`;
}

/** Bare member ids name the same single object the directory reader resolves.
 * An unresolved bare id cannot decide any other object's filing. */
function directoryMemberRefs(items: Items, members: readonly string[]): ReadonlySet<string> {
  const refs = new Set<string>();
  for (const stored of members) {
    const ref = normalizeRef(stored);
    const member = objectByRef(items, ref);
    if (member) refs.add(qualifiedRef(member.kind, member.id));
    else if (ref.includes(":")) refs.add(ref);
  }
  return refs;
}

/** Follow real parents first, then stored membership. Each cyclic group keeps
 * one Desk entry so filing an ancestor cannot hide the entire drawer tree. */
export function rootDirectories(items: Items): Items["directory"] {
  const directories = items.directory ?? [];
  const byId = new Map(directories.map((directory) => [directory.id, directory]));
  const members = new Map(directories.map((directory) => [directory.id, directoryMemberRefs(items, directory.memberIds)]));
  const parents = new Map<string, string | undefined>();
  const roots = new Set<string>();
  for (const directory of directories) {
    const ref = qualifiedRef("directory", directory.id);
    const parent = directory.parentId && byId.has(directory.parentId)
      ? directory.parentId
      : directories.find((candidate) => members.get(candidate.id)?.has(ref))?.id;
    parents.set(directory.id, parent);
    if (!parent) roots.add(directory.id);
  }
  const finished = new Set<string>();
  for (const directory of directories) {
    const path: string[] = [];
    const onPath = new Set<string>();
    let id: string | undefined = directory.id;
    while (id !== undefined && !finished.has(id)) {
      if (onPath.has(id)) {
        const cycle = path.slice(path.indexOf(id));
        const originalRoots = cycle.filter((candidate) => !byId.get(candidate)?.parentId);
        roots.add((originalRoots.length ? originalRoots : cycle).sort()[0]);
        break;
      }
      onPath.add(id);
      path.push(id);
      id = parents.get(id);
    }
    for (const visited of path) finished.add(visited);
  }
  return directories.filter((directory) => roots.has(directory.id));
}

function sprites(kind: string, id: string, agent?: string) {
  return {
    sprite: objectSprite(kind, id, "rest", 64, agent),
    spriteSelected: objectSprite(kind, id, "sel", 64, agent),
  };
}

const AGENT_TITLE: Record<string, string> = { claude: "Claude Code", codex: "Codex" };

/** The item's short name: the imperative and its article go
 *  (`Write the rollback runbook` → `rollback runbook`). */
export function shortItemName(title: string): string {
  const words = title.trim().split(/\s+/).filter(Boolean);
  if (words.length < 3) return title.trim();
  let rest = words.slice(1);
  if (/^(the|a|an)$/i.test(rest[0]) && rest.length > 1) rest = rest.slice(1);
  return rest.join(" ");
}

export function agentName(row: CoderSessionRow): string {
  const agent = AGENT_TITLE[row.agent] ?? row.agent;
  const item = row.flight?.title ? shortItemName(row.flight.title) : row.name;
  return `${agent}: ${item}`;
}

/** ask (it asks you) · done (its turn ended after work) · work (it works) · pr (a PR is open). */
export function agentState(row: CoderSessionRow): "ask" | "idle" | "done" | "work" | "pr" {
  // Betterment AG0: the hub reads a finished turn as done (never an ask; an
  // idle reminder after it does not make it one).
  if (row.flight?.state === "done") return "done";
  // PHILO-15 B48: a turn that ended with no question is IDLE, not ASKS.
  if (row.blocked) return row.idle ? "idle" : "ask";
  if (row.flight?.state === "waiting") return row.flight.turnEnd === "idle" ? "idle" : "ask";
  if (row.flight?.state === "pr_open") return "pr";
  return "work";
}

const AGENT_LAMP: Record<"ask" | "idle" | "done" | "work" | "pr", ObjectTone> = { ask: "ask", idle: "info", done: "ok", work: "info", pr: "ok" };

function agentWordFor(row: CoderSessionRow): string {
  const state = agentState(row);
  if (state === "ask") return "ASKS";
  if (state === "idle") return "IDLE";
  if (state === "done") return row.flight?.isNew ? "NEW" : "DONE";
  if (state === "pr") return row.flight?.pr?.number ? `PR #${row.flight.pr.number}` : "PR OPEN";
  return "WORKS";
}

export function composeScreen(input: ScreenInputs): ScreenObject[] {
  const out: ScreenObject[] = [];

  // ── drawers: the real folders, Projects, People, the Conductor ──
  for (const directory of rootDirectories(input.items)) {
    const ref = qualifiedRef("directory", directory.id);
    out.push({
      key: ref,
      role: "drawer",
      kind: "directory",
      kindWord: "DRAWER",
      name: directory.name || "Drawer",
      ...sprites("directory", directory.id),
      target: { type: "ref", ref },
    });
  }
  for (const project of input.items.project ?? []) {
    const n = input.projectCounts[project.id] ?? 0;
    const failed = Boolean(input.notRead?.[project.id]);
    out.push({
      key: `project:${project.id}`,
      role: "drawer",
      kind: "project",
      name: project.name || "Project",
      ...sprites("project", project.id),
      // Betterment D1: the hub's one count rule filtered to this Project
      // (`projectCounts`), the bell's number in its Project's share. A
      // failed membership read wears NOT READ.
      lamp: failed ? { ...NOT_READ, count: n || undefined } : n > 0 ? { tone: "ask", count: n } : undefined,
      ariaExtra: n > 0 ? `${n} open here` : undefined,
      notRead: failed ? { retry: { type: "project", id: project.id } } : undefined,
      target: { type: "project", id: project.id },
    });
  }
  out.push({
    key: "drawer:people",
    role: "drawer",
    kind: "person",
    kindWord: "DRAWER",
    name: "People",
    // The People drawer is the ledger; one person (loose, below) is the badge.
    ...sprites("people", "people"),
    lamp: input.peopleNotRead ? NOT_READ : undefined,
    caption: input.peopleCaption || undefined,
    notRead: input.peopleNotRead ? { retry: { type: "people" } } : undefined,
    target: { type: "people" },
  });
  const live = liveAgentSessions(input.sessions);
  const launched = input.flights.filter(isInFlight).length;
  const asking = live.some((row) => agentState(row) === "ask") || input.heldCalls > 0;
  out.push({
    key: "drawer:conductor",
    role: "drawer",
    kind: "conductor",
    name: "Agents",
    ...sprites("conductor", "conductor"),
    badge: spriteUrl("coder", "conductor-badge"),
    // A lamp is for what needs him: the ask/held lamp only when an agent
    // asks or a call is held; while they work, the count notch alone.
    lamp: asking ? { tone: "ask", count: launched } : undefined,
    count: asking ? undefined : launched,
    ariaExtra: [launched > 0 ? `${launched} launched` : "", asking ? "an agent asks" : ""].filter(Boolean).join(", ") || undefined,
    target: { type: "conductor" },
  });

  // ── the smart drawer and Parked ──
  out.push({
    key: "drawer:needs",
    role: "needs",
    kind: "smart",
    name: "Needs you",
    ...sprites("smart", "needs-you"),
    // Needs you has one number in its head. The Desk lamp only says that it
    // asks; duplicating the number here made the same membership read look
    // like two separate queues.
    lamp: input.needsCount > 0 ? { tone: "ask" } : undefined,
    ariaExtra: input.needsCount > 0 ? needYouWords(input.needsCount) : undefined,
    target: { type: "needs" },
  });
  out.push({
    key: "drawer:parked",
    role: "parked",
    kind: "parked",
    name: "Archive",
    ...sprites("parked", "parked"),
    target: { type: "parked" },
  });

  // ── loose objects: what no Project holds ──
  // Unknown stays unknown (Astra's P1 on #939): an object whose filing a
  // failed read would decide is not drawn loose.
  if (input.membersLoaded && !input.unknownAll) {
    const filed = new Set([...input.filed].map(normalizeRef));
    for (const directory of input.items.directory ?? []) {
      for (const ref of directoryMemberRefs(input.items, directory.memberIds)) filed.add(ref);
    }
    for (const o of allObjects(input.items)) {
      if (!LOOSE_KINDS.has(o.kind)) continue;
      if (!hasUserOwnedContent(o)) continue;
      if (o.kind === "meeting" && input.unknownMeetings) continue;
      const ref = qualifiedRef(o.kind, o.id);
      if (filed.has(normalizeRef(ref))) continue;
      const needs = input.needsRefs.has(ref);
      out.push({
        key: ref,
        role: "loose",
        kind: o.kind,
        name: o.title,
        ...sprites(o.kind, o.id),
        lamp: needs ? { tone: "warn", label: "NEEDS YOU" } : undefined,
        target: { type: "ref", ref },
      });
    }
    for (const person of input.persons) {
      if (!person.name.trim()) continue;
      const ref = `people:${person.id}`;
      if (filed.has(ref)) continue;
      out.push({
        key: ref,
        role: "loose",
        kind: "person",
        name: person.name,
        ...sprites("person", person.id),
        target: { type: "ref", ref },
      });
    }
  }

  // ── the live agents ──
  for (const row of live) {
    const state = agentState(row);
    out.push({
      key: `coder:${row.key}`,
      role: "agent",
      kind: "coder",
      kindWord: "AGENT",
      name: agentName(row),
      ...sprites("coder", row.key, row.agent),
      lamp: { tone: AGENT_LAMP[state], label: agentWordFor(row) },
      target: { type: "agent", key: row.key },
    });
  }
  return out;
}

/** True when the desk holds nothing but the drawers that always exist. */
export function screenIsBare(objects: readonly ScreenObject[]): boolean {
  return !objects.some((o) => o.role === "loose" || o.role === "agent" || o.kind === "directory" || o.key.startsWith("project:"));
}
