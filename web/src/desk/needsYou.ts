import { useEffect, useSyncExternalStore } from "react";
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
  [key: string]: unknown;
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
  count: number;
  /** Ranked, deduplicated rows that are visible to the owner. */
  unmutedItems: NeedsYouRoomItem[];
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
        _isUnassigned: column === "unassigned",
      });
    }
  }
  return rows;
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
 * The one meaning of `needs you`.
 *
 * R1 is Door's four asking columns plus Room rows. A Room commitment owns its
 * action item, so its matching Door card is removed before mute handling.
 * The merged rows then use the shared deduplication and ranking functions.
 * R2 and R3 are appended as members with stable refs of their own.
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
  const combined = [...doorItems(asBoard(input), covered, now), ...room];
  const ranked = rankAttention(dependencies.dedupAttention(combined, now), now) as NeedsYouRoomItem[];
  const mutedProjects = mutedSet(input);
  const mutedItems: NeedsYouRoomItem[] = [];
  const unmutedItems: NeedsYouRoomItem[] = [];
  for (const item of ranked) {
    if (Boolean(item.muted) || (item.projectId && mutedProjects.has(String(item.projectId))))
      mutedItems.push(item);
    else unmutedItems.push(item);
  }

  const assignmentRead = input.assignmentRead ?? "pending";
  const assignments = input.assignments ?? null;
  const blockers = meetingPathBlockers(
    assignmentRead === "failed" ? null : assignments,
    assignmentRead,
  );
  const failedMeetings = [...(input.meetings ?? [])].filter(meetingNeedsYou);
  const members: NeedsYouMember[] = [
    ...unmutedItems.map((item) => ({ ref: itemRef(item), kind: "attention" as const, item })),
    ...blockers.map((blocker) => ({ ref: `blocker:${blocker.key}`, kind: "blocker" as const, blocker })),
    ...failedMeetings.map((meeting) => ({ ref: meeting.id, kind: "meeting" as const, meeting })),
  ];
  return {
    members,
    count: members.length,
    unmutedItems,
    mutedItems,
    blockers,
    failedMeetings,
  };
}

type SourceName = "door" | "room" | "assignments" | "meetings" | "mutedProjects";
export type NeedsYouErrors = Partial<Record<SourceName, string>>;

export interface NeedsYouSnapshot extends NeedsYouResult {
  complete: boolean;
  loading: boolean;
  errors: NeedsYouErrors;
  room: NeedsYouRoomEnvelope | null;
}

interface SourceState {
  door: NeedsYouDoorProjection | null;
  room: NeedsYouRoomEnvelope | null;
  assignments: AssignmentSummary | null;
  assignmentRead: AssignmentRead;
  meetings: Meeting[];
  mutedProjectIds: string[];
  loaded: Record<SourceName, boolean>;
  errors: NeedsYouErrors;
}

const EMPTY_SOURCE: SourceState = {
  door: null,
  room: null,
  assignments: null,
  assignmentRead: "pending",
  meetings: [],
  mutedProjectIds: [],
  loaded: { door: false, room: false, assignments: false, meetings: false, mutedProjects: false },
  errors: {},
};

let sourceState: SourceState = EMPTY_SOURCE;
let snapshot: NeedsYouSnapshot = {
  ...computeNeedsYou({}),
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

function publish(next: Partial<NeedsYouSnapshot> = {}): void {
  snapshot = { ...snapshot, ...next };
  for (const listener of listeners) listener();
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed. Retry the read.";
}

function bodyRows<T>(body: unknown, key: string): T[] {
  if (Array.isArray(body)) return body as T[];
  if (!body || typeof body !== "object") return [];
  const rows = (body as Record<string, unknown>)[key];
  return Array.isArray(rows) ? rows as T[] : [];
}

async function readMeetings(): Promise<Meeting[]> {
  const out: Meeting[] = [];
  let offset = 0;
  for (;;) {
    const params = new URLSearchParams({
      summary_attention: "true",
      limit: "500",
      offset: String(offset),
    });
    const body = await apiFetch<unknown>(`/api/meetings?${params.toString()}`);
    const rows = bodyRows<unknown>(body, "meetings");
    out.push(...rows.map(fromWireMeeting).filter((meeting): meeting is Meeting => meeting !== null));
    if (!body || typeof body !== "object") break;
    const total = Number((body as Record<string, unknown>).total);
    const nextOffset = offset + rows.length;
    if ((Number.isFinite(total) && nextOffset >= total) || rows.length < 500) break;
    if (!Number.isFinite(nextOffset) || nextOffset <= offset) throw new Error("Meeting read returned an invalid page cursor.");
    offset = nextOffset;
  }
  return out;
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
    const reads = await Promise.allSettled([
      apiFetch<NeedsYouDoorProjection>("/api/door"),
      apiFetch<{
        items?: NeedsYouRoomItem[];
        projects?: unknown;
        coverage?: CoverageRecord[];
        complete?: unknown;
        computedAt?: unknown;
        stale?: unknown;
        next?: unknown;
        sweepId?: unknown;
      }>(fresh ? "/api/desk/needs-you?fresh=1" : "/api/desk/needs-you"),
      apiFetch<AssignmentSummary>("/api/inference/assignments"),
      readMeetings(),
      apiFetch<{ muted_projects?: unknown }>("/api/settings/heartbeat"),
    ]);
    if (started !== generation) return;
    const names: SourceName[] = ["door", "room", "assignments", "meetings", "mutedProjects"];
    const errors: NeedsYouErrors = {};
    const loaded = { ...sourceState.loaded };
    reads.forEach((result, index) => {
      if (result.status === "rejected") errors[names[index]] = errorText(result.reason);
      else loaded[names[index]] = true;
    });
    const doorRead = reads[0];
    if (doorRead.status === "fulfilled") sourceState.door = doorRead.value;
    const roomRead = reads[1];
    if (roomRead.status === "fulfilled") {
      // A null body is an empty Room, never a crash of the whole read.
      const value = roomRead.value ?? {};
      sourceState.room = {
        items: Array.isArray(value.items) ? value.items : [],
        projects: Array.isArray(value.projects) ? value.projects.map(String) : [],
        coverage: Array.isArray(value.coverage) ? value.coverage : [],
        complete: typeof value.complete === "boolean" ? value.complete : null,
        computedAt: typeof value.computedAt === "string" ? value.computedAt : null,
        stale: value.stale === true,
        next: value.next,
        sweepId: typeof value.sweepId === "string" ? value.sweepId : null,
      };
    }
    const assignmentRead = reads[2];
    if (assignmentRead.status === "fulfilled") {
      sourceState.assignments = assignmentRead.value;
      sourceState.assignmentRead = "ok";
    }
    const meetingsRead = reads[3];
    if (meetingsRead.status === "fulfilled") sourceState.meetings = meetingsRead.value;
    const mutedRead = reads[4];
    if (mutedRead.status === "fulfilled") {
      const raw = mutedRead.value?.muted_projects;
      sourceState.mutedProjectIds = Array.isArray(raw) ? raw.map(String) : [];
    }
    if (reads[2].status === "rejected") sourceState.assignmentRead = "failed";
    sourceState = { ...sourceState, loaded, errors };
    const result = computeNeedsYou({
      door: sourceState.door,
      roomItems: sourceState.room?.items,
      mutedProjectIds: sourceState.mutedProjectIds,
      assignments: sourceState.assignments,
      assignmentRead: sourceState.assignmentRead,
      meetings: sourceState.meetings,
    });
    publish({
      ...result,
      complete:
        names.every((name) => sourceState.loaded[name]) &&
        Object.keys(errors).length === 0 &&
        readCoverage(
          sourceState.room?.coverage,
          sourceState.room?.complete ?? undefined,
          Boolean(errors.room),
        ).complete &&
        sourceState.room?.stale !== true,
      loading: false,
      errors,
      room: sourceState.room,
    });
  })().catch((error) => {
    // A transport-level failure outside the individual reads keeps the last
    // result visible and names the retryable state.
    if (started !== generation) return;
    publish({ loading: false, errors: { ...snapshot.errors, room: errorText(error) } });
  }).finally(() => {
    if (started !== generation) return;
    inflight = null;
    inflightFresh = false;
  });
  inflight = request;
  return request;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  if (listeners.size === 1) {
    void refreshNeedsYou(false);
    pollTimer = setInterval(() => { void refreshNeedsYou(false); }, 60_000);
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0 && pollTimer !== null) {
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
export function useNeedsYou(): NeedsYouSnapshot & { refresh: () => Promise<void> } {
  const value = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
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
  sourceState = {
    door: null, room: null, assignments: null, assignmentRead: "pending", meetings: [], mutedProjectIds: [],
    loaded: { door: false, room: false, assignments: false, meetings: false, mutedProjects: false },
    errors: {},
  };
  snapshot = { ...computeNeedsYou({}), complete: false, loading: false, errors: {}, room: null };
}
// The test setup resets through this handle and never imports this module:
// an import there would bind the real API client before a test's mock.
if (import.meta.env?.MODE === "test") {
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou = resetNeedsYou;
}

// Keep this import in the public module's type surface for consumers that
// re-home existing Room source metadata without importing attention.ts.
export type { AttentionSource };
