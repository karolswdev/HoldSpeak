/** PHILO-14 A1 — the screen's objects, composed from the desk's own reads.
 *
 *  Board A-1 (docs/internal/philo/phase-14/canvas/shots/A-1-1440.png): the
 *  drawers, Projects, loose notes and explicit Desk members, with Archive
 *  parked at the edge. Pure: the tests compose from a fixture world. */
import type { Items } from "../api";
import { qualifiedRef } from "../api";
import { type AgentFlight, type CoderSessionRow } from "../agentFlights";
import { objectSprite, type ObjectTone } from "../surface";
import { objectByRef } from "../world";
import type { ScreenTarget } from "./open";

export type ScreenRole = "drawer" | "needs" | "parked" | "loose" | "agent";

/** The packaged directory that records an owner's explicit Floor choices. */
export const SEED_DESK_DIRECTORY_ID = "hs-seed-desk";
/** Notes leave the Floor through the ordinary Inbox drawer. */
export const SEED_INBOX_DIRECTORY_ID = "hs-seed-inbox";

const SEED_VISIBLE_DIRECTORY_ORDER = new Map([
  ["hs-seed-inbox", 0],
  ["hs-seed-work", 1],
  ["hs-seed-personal", 2],
  ["hs-seed-reference", 3],
]);

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
/** Notes with content are the only records that arrive on an unfiled Floor.
 * All other Floor records must be kept explicitly in the Desk directory. */
const LOOSE_KINDS = new Set(["note"]);
const KEEPABLE_KINDS = new Set(["meeting", "note", "decision", "artifact", "repository", "thread"]);

function canonicalMemberRef(stored: string): string {
  return normalizeRef(stored);
}

function directoryRefs(directory: Items["directory"][number] | undefined): ReadonlySet<string> {
  return new Set((directory?.memberIds ?? []).map(canonicalMemberRef));
}

function hasUserOwnedContent(object: { kind: string; ref?: unknown; title?: string; bodyMarkdown?: string }): boolean {
  const value = (object.ref ?? object) as Record<string, unknown>;
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

/** Directories that have a visible home in the Desk and Go faces. */
export function visibleRootDirectories(items: Items): Items["directory"] {
  return rootDirectories(items)
    .filter((directory) => {
      if (directory.id === SEED_DESK_DIRECTORY_ID) return false;
      return !(
        (directory.id === "hs-seed-meetings" || directory.id === "hs-seed-decisions") &&
        (directory.memberIds ?? []).length === 0
      );
    })
    .sort((left, right) => {
      const leftOrder = SEED_VISIBLE_DIRECTORY_ORDER.get(left.id);
      const rightOrder = SEED_VISIBLE_DIRECTORY_ORDER.get(right.id);
      if (leftOrder === undefined && rightOrder === undefined) {
        return String(left.createdAt ?? "").localeCompare(String(right.createdAt ?? "")) || left.id.localeCompare(right.id);
      }
      if (leftOrder === undefined) return 1;
      if (rightOrder === undefined) return -1;
      return leftOrder - rightOrder;
    });
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

export function composeScreen(input: ScreenInputs): ScreenObject[] {
  const out: ScreenObject[] = [];

  // ── drawers: the real folders and Projects ──
  for (const directory of visibleRootDirectories(input.items)) {
    const ref = qualifiedRef("directory", directory.id);
    out.push({
      key: ref,
      role: "drawer",
      kind: "directory",
      kindWord: "Drawer",
      name: directory.name || "Drawer",
      ...sprites("directory", directory.id),
      target: { type: "ref", ref },
    });
  }
  // Betterment Q10 (Knowledge becomes drawers): each knowledge collection
  // is a drawer of the same name. Its members stay on the desk too (a
  // collection is many-to-many; only a real drawer files its members away).
  for (const kb of input.items.kb ?? []) {
    if (!kb.name?.trim()) continue;
    const ref = qualifiedRef("kb", kb.id);
    out.push({
      key: ref,
      role: "drawer",
      kind: "kb",
      // W2-BUILDER (atlas 2026-10-27): the caption says what it is. It
      // opens a Knowledge window (its own Add), not a drawer's.
      kindWord: "Knowledge",
      name: kb.name,
      ...sprites("directory", kb.id),
      target: { type: "ref", ref },
    });
  }
  const projects = [...(input.items.project ?? [])].sort((left, right) => (
    String(left.createdAt ?? "").localeCompare(String(right.createdAt ?? "")) || left.id.localeCompare(right.id)
  ));
  for (const project of projects) {
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
  // The People, Agents and Needs you doors have their own homes in the Dock,
  // Go and the bell. They are deliberately absent from the Floor.
  // Floor lane (owner 2026-10-26, "the trash can being there"): Archive is
  // no floor icon either; its bottom-right seat read as the Mac's Trash. Go ▸
  // Archive and ⌘K open its window. The old icon is parked in
  // screen/_parked/floorTalkAndArchive.tsx.

  // ── the Floor: unfiled content notes, then explicit Desk members ──
  // Unknown stays unknown (Astra's P1 on #939): a failed Project filing read
  // must not make a note appear loose while the read is still unresolved.
  const deskDirectory = (input.items.directory ?? []).find((d) => d.id === SEED_DESK_DIRECTORY_ID);
  const keptRefs = directoryRefs(deskDirectory);
  const filed = new Set([...input.filed].map(normalizeRef));
  for (const directory of input.items.directory ?? []) {
    for (const ref of directoryMemberRefs(input.items, directory.memberIds)) filed.add(ref);
  }

  const floorCandidates: Array<{ object: ScreenObject; arrivalAt: string; sourceOrder: number }> = [];
  if (input.membersLoaded && !input.unknownAll) {
    // Notes are the one automatic Floor species. Keep them in the same
    // arrival stream as explicit Desk members so a later note does not insert
    // itself before an icon the owner already kept.
    for (const o of (input.items.note ?? [])) {
      if (!LOOSE_KINDS.has(o.kind) || !hasUserOwnedContent(o)) continue;
      const ref = qualifiedRef(o.kind, o.id);
      if (filed.has(normalizeRef(ref))) continue;
      const needs = input.needsRefs.has(ref);
      floorCandidates.push({
        object: {
          key: ref,
          role: "loose",
          kind: o.kind,
          name: o.title,
          ...sprites(o.kind, o.id),
          lamp: needs ? { tone: "warn", label: "NEEDS YOU" } : undefined,
          target: { type: "ref", ref },
        },
        arrivalAt: o.createdAt,
        sourceOrder: floorCandidates.length,
      });
    }
  }

  // A Desk membership is an explicit owner's choice. Its record timestamp (or
  // membership edge order when no timestamp exists) joins the same arrival
  // stream as notes, so a later note never inserts before a kept icon.
  for (const [memberIndex, stored] of (deskDirectory?.memberIds ?? []).entries()) {
    const ref = canonicalMemberRef(stored);
    if (!ref || !keptRefs.has(ref)) continue;
    if (ref.startsWith("people:")) {
      const person = input.persons.find((candidate) => `people:${candidate.id}` === ref);
      if (!person?.name.trim()) continue;
      floorCandidates.push({
        object: {
          key: ref,
          role: "loose",
          kind: "person",
          name: person.name,
          ...sprites("person", person.id),
          target: { type: "ref", ref },
        },
        arrivalAt: "",
        sourceOrder: 100_000 + memberIndex,
      });
      continue;
    }
    const object = objectByRef(input.items, ref);
    if (!object || !KEEPABLE_KINDS.has(object.kind)) continue;
    const needs = input.needsRefs.has(ref);
    const source = object.ref as { startedAt?: unknown; createdAt?: unknown };
    const arrivalAt = object.kind === "meeting"
      ? typeof source.startedAt === "string" ? source.startedAt : ""
      : typeof source.createdAt === "string" ? source.createdAt : "";
    floorCandidates.push({
      object: {
        key: ref,
        role: "loose",
        kind: object.kind,
        name: object.title,
        ...sprites(object.kind, object.id),
        lamp: needs ? { tone: "warn", label: "NEEDS YOU" } : undefined,
        target: { type: "ref", ref },
      },
      arrivalAt,
      sourceOrder: 100_000 + memberIndex,
    });
  }

  floorCandidates.sort((left, right) => {
    if (left.arrivalAt && right.arrivalAt) {
      return left.arrivalAt.localeCompare(right.arrivalAt) || left.sourceOrder - right.sourceOrder;
    }
    if (left.arrivalAt) return -1;
    if (right.arrivalAt) return 1;
    return left.sourceOrder - right.sourceOrder;
  });
  for (const candidate of floorCandidates) out.push(candidate.object);

  // Betterment AG8: the per-agent desk icons left the floor (the Agents
  // drawer, its Dock tile and Needs you carry them); parked in
  // desk/_parked/agents/floorAgents.ts.
  return out;
}

/** True when the desk holds nothing but the drawers that always exist. */
export function screenIsBare(objects: readonly ScreenObject[]): boolean {
  return !objects.some((o) => o.role === "loose" || o.role === "agent" || o.kind === "directory" || o.key.startsWith("project:"));
}
