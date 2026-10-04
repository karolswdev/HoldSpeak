import { useCallback, useEffect, useSyncExternalStore } from "react";
import { fromWireMeeting } from "./api";
import { apiFetch } from "../lib/api";
import {
  dedupAttention,
  rankAttention,
  type RankableItem,
  type AttentionSource,
} from "./attention";
import {
  meetingPathBlockers,
  type AssignmentRead,
  type MeetingPathBlocker,
} from "./chair/meetingPathBlocker";
import { intelBadge } from "./chair/intelBadge";
import { readCoverage, type CoverageRecord } from "./coverage";
import type { AssignmentSummary } from "../pages/cores/assignmentExperience";
import type { Meeting } from "../lib/primitives";

/** The four Door board columns that ask the owner. `active` is deliberately
 * absent: an active thought is a Door item, but it does not need the owner. */
export type DoorColumn = "overdue" | "now" | "waiting" | "unassigned";

export interface NeedsYouDoorCard {
  id: string;
  source?: string;
  target_ref?: string;
  open_ref?: string;
  title?: string;
  text?: string;
  owner?: string | null;
  due?: string | null;
  status?: string;
  project_id?: string | null;
  projectId?: string | null;
  lawful_verbs?: Array<{
    name: string;
    arguments: Record<string, string | number | null | undefined>;
    required_arguments?: string[];
  }>;
  [key: string]: unknown;
}

export interface NeedsYouRoomItem extends RankableItem {
  projectName?: string;
  ref?: string;
  verbHref?: string | null;
  muted?: boolean;
  actionItemId?: string | null;
  commitmentId?: string;
  owner?: string | null;
  unknowns?: string[];
  nextAction?: "name_owner" | "set_date" | "mark_done" | null;
  decisionRecordId?: string | null;
  proposalKind?: string;
  proposalHost?: string;
  proposalDue?: string | null;
  meetingTitle?: string;
  rank?: number;
  /** Kept for A2-W: a row remains openable after it joins the membership. */
  openRef?: string | null;
  proposalId?: string;
  /** True when the owner waits on someone else for this row: it is listed
   * (the WAITING filter shows it) and it is not counted. */
  waiting?: boolean;
  [key: string]: unknown;
}

/** A decision that waits for the owner's review, as the hub's rule reads it
 * (`needs_you_membership._read_decisions`). */
export interface NeedsYouDecision {
  id: string;
  title?: string | null;
  projectId?: string | null;
  since?: string | null;
}

export interface NeedsYouDoorProjection {
  board?: Partial<Record<DoorColumn | "active", NeedsYouDoorCard[]>>;
}

export interface NeedsYouInputs {
  /** Either the Door response or its board. Both forms keep fixture adapters
   * and existing callers small while the rule remains one function. */
  door?: NeedsYouDoorProjection | Partial<Record<DoorColumn | "active", NeedsYouDoorCard[]>> | null;
  roomItems?: readonly NeedsYouRoomItem[];
  mutedProjectIds?: readonly string[] | ReadonlySet<string>;
  assignments?: AssignmentSummary | null;
  assignmentRead?: AssignmentRead;
  meetings?: readonly Meeting[];
  /** R4: the decisions that wait for the owner's review. */
  decisions?: readonly NeedsYouDecision[];
  /** The names that mean the owner himself (the hub's `ownerNames`). */
  selfNames?: readonly string[];
  now?: Date;
}

export type NeedsYouMemberKind = "attention" | "blocker" | "meeting";

export interface NeedsYouMember {
  ref: string;
  kind: NeedsYouMemberKind;
  item?: NeedsYouRoomItem;
  blocker?: MeetingPathBlocker;
  meeting?: Meeting;
}

export interface NeedsYouResult {
  members: NeedsYouMember[];
  /** What needs the owner. A row he waits on someone else for is not in it. */
  count: number;
  /** The unmuted rows the owner waits on someone else for. */
  waitingCount: number;
  /** Ranked, deduplicated rows that are visible to the owner. Each row is
   * marked `waiting`: the counted rows and the waiting rows are both here. */
  unmutedItems: NeedsYouRoomItem[];
  /** The rows of `unmutedItems` that wait on someone else. */
  waitingItems: NeedsYouRoomItem[];
  /** Ranked, deduplicated rows retained for the muted section. */
  mutedItems: NeedsYouRoomItem[];
  blockers: MeetingPathBlocker[];
  failedMeetings: Meeting[];
}

/** Pure membership dependencies. The default is the production attention
 * deduplicator; the narrow seam also lets the real-producer oracle load a
 * code mutant that omits deduplication and prove the six-ref contract rejects
 * it. */
export interface NeedsYouDependencies {
  dedupAttention: (
    items: readonly NeedsYouRoomItem[],
    now: Date,
  ) => NeedsYouRoomItem[];
}

const DEFAULT_NEEDS_YOU_DEPENDENCIES: NeedsYouDependencies = {
  dedupAttention: (items, now) => dedupAttention(items, now),
};

/** The Room wire's coverage/freshness facts travel with the shared snapshot.
 * A consumer must not replace this with an empty Room when the aggregate says
 * that only a partial answer was observed. */
export interface NeedsYouRoomEnvelope {
  items: NeedsYouRoomItem[];
  projects: string[];
  coverage: CoverageRecord[];
  complete: boolean | null;
  computedAt: string | null;
  stale: boolean;
  next?: unknown;
  sweepId?: string | null;
}

function asBoard(
  input: NeedsYouInputs,
): Partial<Record<DoorColumn | "active", NeedsYouDoorCard[]>> {
  const door = input.door;
  if (door && "board" in door && door.board) return door.board;
  return (door as Partial<Record<DoorColumn | "active", NeedsYouDoorCard[]>> | undefined) ?? {};
}

function doorItems(
  board: Partial<Record<DoorColumn | "active", NeedsYouDoorCard[]>>,
  coveredActionItems: ReadonlySet<string>,
  now: Date,
): NeedsYouRoomItem[] {
  const rows: NeedsYouRoomItem[] = [];
  for (const column of ["overdue", "now", "waiting", "unassigned"] as const) {
    for (const card of board[column] ?? []) {
      const cardId = String(card.id ?? "");
      if (!cardId || coveredActionItems.has(cardId)) continue;
      const dueAt = card.due ?? null;
      const owner = card.owner ?? null;
      const hasOwner = String(owner ?? "").trim() !== "";
      let why = "";
      let severity = "info";
      if (column === "overdue") {
        const due = dueAt ? new Date(dueAt).getTime() : Number.NaN;
        const days = Number.isFinite(due)
          ? Math.max(1, Math.floor((now.getTime() - due) / 86_400_000))
          : 0;
        why = days > 0 ? `OVERDUE · ${days}D` : "OVERDUE";
        severity = "danger";
      } else if (column === "now") {
        why = "DUE TODAY";
        severity = "warning";
      } else if (column === "waiting") {
        why = owner ? `WAITING ON ${String(owner).toUpperCase()}` : "WAITING";
      } else if (hasOwner) {
        // The `unassigned` column also holds an item that HAS an owner and
        // is not reviewed yet. It reads "To review"; only an item with no
        // owner reads "Unassigned".
        why = "TO REVIEW";
        severity = "warning";
      } else {
        why = "UNASSIGNED";
        severity = "warning";
      }
      rows.push({
        id: `door:${cardId}`,
        ref: cardId,
        projectId: String(card.project_id ?? card.projectId ?? ""),
        projectName: "",
        title: String(card.title || card.text || "Untitled"),
        why,
        ageToken: "",
        since: "",
        dueAt,
        kind: "action_item",
        source: String(card.source ?? "action_item"),
        // `open_ref` is a Desk route token, not an external URL. Keep the
        // whole card in `_doorCard` for A2-W and never present it as egress.
        verbHref: null,
        openRef: card.open_ref ?? null,
        severity,
        owner,
        _doorCard: card,
        _isDoor: true,
        _isUnassigned: column === "unassigned" && !hasOwner,
        _toReview: column === "unassigned" && hasOwner,
      });
    }
  }
  return rows;
}

/** R4: decisions awaiting review, as attention rows. The ref is the Desk
 * route token `decision:<id>`; Review opens it. */
function decisionItems(decisions: readonly NeedsYouDecision[]): NeedsYouRoomItem[] {
  const rows: NeedsYouRoomItem[] = [];
  for (const decision of decisions) {
    const decisionId = String(decision.id ?? "");
    if (!decisionId) continue;
    const ref = `decision:${decisionId}`;
    const since = String(decision.since ?? "");
    rows.push({
      id: ref,
      ref,
      projectId: String(decision.projectId ?? ""),
      projectName: "",
      title: String(decision.title || "Untitled"),
      why: "TO REVIEW",
      ageToken: since,
      since,
      dueAt: null,
      kind: "decision",
      source: "decision",
      verbHref: null,
      openRef: ref,
      severity: "warning",
    });
  }
  return rows;
}

/** The names that mean the owner himself. The People store reserves `me`
 * and `you` and its follow-through projection names the owner `you` /
 * `manager`; the hub adds the configured meeting speaker label (`ownerNames`
 * on its answer). */
export const SELF_OWNER_NAMES: readonly string[] = ["me", "you", "manager"];

/** The reason token of a row the owner himself holds with no nearer due date. */
const YOURS = "YOURS";

function isSelf(owner: unknown, selfNames: readonly string[]): boolean {
  const name = String(owner ?? "").trim().toLowerCase();
  return name !== "" && selfNames.some((n) => String(n).trim().toLowerCase() === name);
}

function waitingOn(row: NeedsYouRoomItem): boolean {
  const owner = String(row.owner ?? "").trim();
  return owner !== "" && String(row.why ?? "").trim().toUpperCase() === `WAITING ON ${owner.toUpperCase()}`;
}

/** True when the owner waits on SOMEONE ELSE for this row: it names an owner
 * who is not the owner himself, and its reason is `WAITING ON <that owner>`
 * (a Door card in the `waiting` column, or a Room commitment with an owner
 * and a later due date). `WAITING ON YOUR REVIEW` names no owner and is the
 * owner's own work. */
export function waitsOnOther(
  row: NeedsYouRoomItem,
  selfNames: readonly string[] = SELF_OWNER_NAMES,
): boolean {
  return waitingOn(row) && !isSelf(row.owner, selfNames);
}

function mutedSet(input: NeedsYouInputs): ReadonlySet<string> {
  const values = input.mutedProjectIds ?? [];
  return values instanceof Set ? values : new Set([...values].map(String));
}

function itemRef(item: NeedsYouRoomItem): string {
  return String(item.ref ?? item.id ?? "");
}

function meetingSummaryBadge(meeting: Meeting): string {
  const job = meeting.intelJob;
  const jobStatus = String(job?.status ?? "").toLowerCase();
  // A retry remains RETRYING after its scheduled time. Time alone is not a
  // terminal fact; the failed lineage is the fact the owner needs.
  if (
    (jobStatus === "queued" || jobStatus === "retrying") &&
    (job?.attempts ?? 0) > 0 &&
    Boolean(job?.lastError)
  ) return "RETRYING";
  if (jobStatus === "failed") return "FAILED";
  return intelBadge(meeting.intelStatus);
}

export function meetingNeedsYou(meeting: Meeting): boolean {
  const badge = meetingSummaryBadge(meeting);
  return badge === "FAILED" || badge === "RETRYING";
}

/**
 * The one meaning of `needs you`, as a pure function.
 *
 * The hub applies this rule (`holdspeak/services/needs_you_membership.py`
 * is its line-for-line twin) and the faces read the hub's answer through
 * `useNeedsYou`. This function is the browser's statement of the same rule:
 * the real-producer oracle (`needsYou.test.ts`) holds it and the hub's answer
 * to the same six refs, so the two cannot drift.
 *
 * R1 is Door's four asking columns plus Room rows. A Room commitment owns its
 * action item, so its matching Door card is removed before mute handling.
 * The merged rows then use the shared deduplication and ranking functions.
 * R2 and R3 are appended as members with stable refs of their own.
 * R4 is the decisions that wait for the owner's review, as attention rows.
 *
 * Owner ruling 2026-10-04: a row the owner waits on someone else for
 * (`waitsOnOther`) is listed, marked `waiting`, and is not a member.
 * `count` is what needs him; `waitingCount` is what he waits on.
 */
export function computeNeedsYou(
  input: NeedsYouInputs,
  dependencies: NeedsYouDependencies = DEFAULT_NEEDS_YOU_DEPENDENCIES,
): NeedsYouResult {
  const room = [...(input.roomItems ?? [])];
  const covered = new Set(
    room
      .filter((item) => item.source === "commitment" && item.actionItemId)
      .map((item) => String(item.actionItemId)),
  );
  const now = input.now ?? new Date();
  const selfNames = input.selfNames ?? SELF_OWNER_NAMES;
  // An item the owner himself holds is his: it reads `YOURS`, never
  // `WAITING ON ME`, and it is counted.
  const combined = [...doorItems(asBoard(input), covered, now), ...room].map((row) =>
    waitingOn(row) && isSelf(row.owner, selfNames) ? { ...row, why: YOURS } : row,
  );
  // A People commitment never merges with another row: a merge would put its
  // text and its record ref inside another row's `sources`, past the custody
  // boundary. It stays one row of its own.
  const people = combined.filter((item) => item.source === "people_commitment");
  const others = combined.filter((item) => item.source !== "people_commitment");
  // A decision keeps its own row and its own ref (`decision:<id>`): the Brief
  // names the same ref, so the two count it once.
  // A merged row waits on someone else only when EVERY merged projection
  // does. When one projection is the owner's own (YOURS, due, overdue), the
  // row is his: it leads with his reason and it is counted.
  const waits = new Map<string, boolean>();
  for (const row of others) {
    const mark = waitsOnOther(row, selfNames);
    for (const key of [row.id, ...(row.sources ?? []).map((source) => source.id)]) {
      if (key != null && !waits.has(String(key))) waits.set(String(key), mark);
    }
  }
  const merged = dependencies.dedupAttention(others, now).map((row) => {
    const sources = row.sources ?? [];
    if (sources.length < 2) return { ...row, waiting: waitsOnOther(row, selfNames) };
    const marks = sources.map((source) => waits.get(String(source.id)) ?? false);
    const waiting = marks.every(Boolean);
    if (waiting || !waitsOnOther(row, selfNames)) return { ...row, waiting };
    const his = sources[marks.indexOf(false)];
    return { ...row, waiting, why: his.why || row.why, severity: his.severity || row.severity };
  });
  const singles = [...people, ...decisionItems(input.decisions ?? [])].map((row) => (
    { ...row, waiting: waitsOnOther(row, selfNames) }
  ));
  const ranked = rankAttention([...merged, ...singles], now) as NeedsYouRoomItem[];
  const mutedProjects = mutedSet(input);
  const mutedItems: NeedsYouRoomItem[] = [];
  const unmutedItems: NeedsYouRoomItem[] = [];
  for (const item of ranked) {
    if (Boolean(item.muted) || (item.projectId && mutedProjects.has(String(item.projectId))))
      mutedItems.push(item);
    else unmutedItems.push(item);
  }
  // What the owner waits on someone else for is listed and is not counted.
  const waitingItems = unmutedItems.filter((item) => item.waiting);
  const countedItems = unmutedItems.filter((item) => !item.waiting);

  const assignmentRead = input.assignmentRead ?? "pending";
  const assignments = input.assignments ?? null;
  const blockers = meetingPathBlockers(
    assignmentRead === "failed" ? null : assignments,
    assignmentRead,
  );
  const failedMeetings = [...(input.meetings ?? [])].filter(meetingNeedsYou);
  const members: NeedsYouMember[] = [
    ...countedItems.map((item) => ({ ref: itemRef(item), kind: "attention" as const, item })),
    ...blockers.map((blocker) => ({ ref: `blocker:${blocker.key}`, kind: "blocker" as const, blocker })),
    ...failedMeetings.map((meeting) => ({ ref: meeting.id, kind: "meeting" as const, meeting })),
  ];
  return {
    members,
    count: members.length,
    waitingCount: waitingItems.length,
    unmutedItems,
    waitingItems,
    mutedItems,
    blockers,
    failedMeetings,
  };
}

type SourceName = "door" | "room" | "assignments" | "meetings" | "decisions" | "mutedProjects";
export type NeedsYouErrors = Partial<Record<SourceName, string>>;

export interface NeedsYouSnapshot extends NeedsYouResult {
  complete: boolean;
  loading: boolean;
  errors: NeedsYouErrors;
  room: NeedsYouRoomEnvelope | null;
}

/** The hub's answer (`desk.needs_you`, `GET /api/desk/needs-you`).
 *
 * The hub applies the one rule (`holdspeak/services/needs_you_membership.py`,
 * the line-for-line twin of `computeNeedsYou` above) and every face reads
 * this answer: the bell, the Chair, the Dock, the system shade, the palette,
 * the Brief, notifications and MCP. The browser applies no rule of its own
 * to the live data, so the numbers cannot disagree. */
export interface NeedsYouAnswer {
  count?: number;
  /** The unmuted rows the owner waits on someone else for (not in `count`). */
  waitingCount?: number;
  /** The names that mean the owner himself. */
  ownerNames?: string[];
  members?: Array<{ ref: string; kind: NeedsYouMemberKind }>;
  /** Every attention row, ranked: the counted rows, then the muted rows. */
  items?: NeedsYouRoomItem[];
  blockers?: MeetingPathBlocker[];
  /** Meetings whose summary failed, as `/api/meetings` rows. */
  failedMeetings?: unknown[];
  /** The Room rows alone (the Room input of R1). */
  roomItems?: NeedsYouRoomItem[];
  /** A hub source that could not be read, by name. */
  sourceErrors?: Partial<Record<"door" | "assignments" | "meetings" | "decisions", string>>;
  projects?: unknown;
  coverage?: CoverageRecord[];
  complete?: unknown;
  roomComplete?: unknown;
  computedAt?: unknown;
  stale?: unknown;
  next?: unknown;
  sweepId?: unknown;
}

/** Read the hub's answer into the shared result. No rule is applied here:
 * the rows, the blockers and the meetings are the hub's, in the hub's order. */
export function readNeedsYouAnswer(answer: NeedsYouAnswer | null | undefined): NeedsYouResult {
  const value = answer ?? {};
  const items = Array.isArray(value.items) ? value.items : [];
  const unmutedItems = items.filter((item) => !item.muted);
  const mutedItems = items.filter((item) => Boolean(item.muted));
  const blockers = Array.isArray(value.blockers) ? value.blockers : [];
  const failedMeetings = (Array.isArray(value.failedMeetings) ? value.failedMeetings : [])
    .map(fromWireMeeting)
    .filter((meeting): meeting is Meeting => meeting !== null);
  // The hub marks each row: a `waiting` row is listed and is not a member.
  const waitingItems = unmutedItems.filter((item) => Boolean(item.waiting));
  const members: NeedsYouMember[] = [
    ...unmutedItems.filter((item) => !item.waiting)
      .map((item) => ({ ref: itemRef(item), kind: "attention" as const, item })),
    ...blockers.map((blocker) => ({ ref: `blocker:${blocker.key}`, kind: "blocker" as const, blocker })),
    ...failedMeetings.map((meeting) => ({ ref: meeting.id, kind: "meeting" as const, meeting })),
  ];
  return {
    members, count: members.length, waitingCount: waitingItems.length,
    unmutedItems, waitingItems, mutedItems, blockers, failedMeetings,
  };
}

const EMPTY_RESULT: NeedsYouResult = {
  members: [], count: 0, waitingCount: 0, unmutedItems: [], waitingItems: [], mutedItems: [],
  blockers: [], failedMeetings: [],
};

let snapshot: NeedsYouSnapshot = {
  ...EMPTY_RESULT,
  complete: false,
  loading: false,
  errors: {},
  room: null,
};
let inflight: Promise<void> | null = null;
/** Bumped by `resetNeedsYou`: a read begun before a reset never publishes. */
let generation = 0;
let inflightFresh = false;
const listeners = new Set<() => void>();
let pollTimer: ReturnType<typeof setInterval> | null = null;
let pollingSubscribers = 0;

function publish(next: Partial<NeedsYouSnapshot> = {}): void {
  snapshot = { ...snapshot, ...next };
  for (const listener of listeners) listener();
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed. Retry the read.";
}

async function refreshNeedsYou(fresh = true): Promise<void> {
  if (inflight) {
    if (!fresh || inflightFresh) return inflight;
    await inflight;
    return refreshNeedsYou(true);
  }
  publish({ loading: true });
  inflightFresh = fresh;
  const started = generation;
  const request = (async () => {
    // ONE read. The hub's answer is the membership.
    const answer = await apiFetch<NeedsYouAnswer | null>(
      fresh ? "/api/desk/needs-you?fresh=1" : "/api/desk/needs-you",
    );
    if (started !== generation) return;
    // A null body is an empty desk, never a crash of the whole read.
    const value = answer ?? {};
    const roomComplete = typeof value.roomComplete === "boolean"
      ? value.roomComplete
      : typeof value.complete === "boolean" ? value.complete : null;
    const room: NeedsYouRoomEnvelope = {
      items: Array.isArray(value.roomItems)
        ? value.roomItems
        : Array.isArray(value.items) ? value.items : [],
      projects: Array.isArray(value.projects) ? value.projects.map(String) : [],
      coverage: Array.isArray(value.coverage) ? value.coverage : [],
      complete: roomComplete,
      computedAt: typeof value.computedAt === "string" ? value.computedAt : null,
      stale: value.stale === true,
      next: value.next,
      sweepId: typeof value.sweepId === "string" ? value.sweepId : null,
    };
    const errors: NeedsYouErrors = {};
    for (const [name, text] of Object.entries(value.sourceErrors ?? {})) {
      if (text) errors[name as SourceName] = String(text);
    }
    publish({
      ...readNeedsYouAnswer(value),
      complete:
        Object.keys(errors).length === 0 &&
        readCoverage(room.coverage, room.complete ?? undefined, false).complete &&
        room.stale !== true,
      loading: false,
      errors,
      room,
    });
  })().catch((error) => {
    // The read failed: the last result stays visible and the retryable state
    // is named. An unread desk is never drawn as a clear desk.
    if (started !== generation) return;
    publish({ loading: false, complete: false, errors: { room: errorText(error) } });
  }).finally(() => {
    if (started !== generation) return;
    inflight = null;
    inflightFresh = false;
  });
  inflight = request;
  return request;
}

function subscribe(listener: () => void, poll: boolean): () => void {
  listeners.add(listener);
  if (poll) pollingSubscribers += 1;
  if (listeners.size === 1) {
    void refreshNeedsYou(false);
  }
  if (poll && pollingSubscribers === 1) {
    pollTimer = setInterval(() => { void refreshNeedsYou(false); }, 60_000);
  }
  return () => {
    listeners.delete(listener);
    if (poll) pollingSubscribers = Math.max(0, pollingSubscribers - 1);
    if (pollingSubscribers === 0 && pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  };
}

function getSnapshot(): NeedsYouSnapshot {
  return snapshot;
}

/** Shared Desk membership read. Multiple mounted faces share one snapshot,
 * one in-flight refresh and one approximately-minute poll. */
export function useNeedsYou(
  options: { poll?: boolean } = {},
): NeedsYouSnapshot & { refresh: () => Promise<void> } {
  const poll = options.poll !== false;
  const subscribeForHook = useCallback(
    (listener: () => void) => subscribe(listener, poll),
    [poll],
  );
  const value = useSyncExternalStore(
    subscribeForHook,
    getSnapshot,
    getSnapshot,
  );
  useEffect(() => { void refreshNeedsYou(false); }, []);
  return { ...value, refresh: () => refreshNeedsYou(true) };
}

export { refreshNeedsYou };

/** Test seam (the pattern of `deskQueryClient.clear()` in the test setup):
 * one shared snapshot must not carry a prior case's read into the next. */
export function resetNeedsYou(): void {
  if (pollTimer !== null) clearInterval(pollTimer);
  pollTimer = null;
  listeners.clear();
  inflight = null;
  inflightFresh = false;
  generation += 1;
  snapshot = { ...EMPTY_RESULT, complete: false, loading: false, errors: {}, room: null };
}
// The test setup resets through this handle and never imports this module:
// an import there would bind the real API client before a test's mock.
if (import.meta.env?.MODE === "test") {
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou = resetNeedsYou;
}

// Keep this import in the public module's type surface for consumers that
// re-home existing Room source metadata without importing attention.ts.
export type { AttentionSource };
