/* Shared People DTOs and acknowledged-write recovery. */
import { ApiError } from "../../lib/api";
import { wireDate } from "../../desk/surface/format";
import * as hub from "../../desk/people/api";
export type ReadinessState = "unconfigured" | "locked" | "key_unavailable" | "corrupt" | "unavailable" | "no_key_store" | "ready";
export type Visibility = "shared_intent" | "leader_private";
export type RelationshipKind = "direct_report" | "peer" | "extended";
export type Lens = "now" | "prep" | "one-on-ones" | "context" | "history" | "info";

export type Readiness = {
  readiness?: ReadinessState;
  state?: ReadinessState;
  store?: "encrypted" | "absent";
  sync?: "local_only";
  capture?: "notes_only";
};
export type CalendarLink = { uid: string; source_id: string; label: string; linked_at?: string };
export type UpcomingEvent = { id: string; uid: string; title: string; starts_at: string; ends_at: string; source_id: string; source_label?: string; source?: string };
export type CalendarRead = { loading: boolean; error: string; title?: string; retry(): void };
export type Relationship = {
  id: string;
  display_name: string;
  relationship_kind?: string;
  role_context?: string | null;
  cadence?: string | null;
  next_one_on_one?: string | null;
  manager_commitment_count?: number;
  open_request_count?: number;
  project_refs?: string[];
  calendar_links?: CalendarLink[] | null;
  /* HS-150-02: owner aliases for the delegation lane. */
  owner_aliases?: string[] | null;
  /** PHILO-17: `?counts=1` — open commitments each way. */
  you_owe_count?: number;
  owes_you_count?: number;
  /** The rail (2026-11-08): meeting actions they owe past their day; promises done. */
  overdue_count?: number;
  done_count?: number;
};
export type AgendaItem = { id: string; body: string; visibility: Visibility; state: string; rolled_from_id?: string | null };
export type Session = { id: string; occurred_at?: string; title?: string; agenda?: AgendaItem[] };
export type GroundingNote = { id: string; topic?: string; body: string; visibility: Visibility; created_at?: string; source?: string };
export type CommitmentEvent = { event: string; state: string; at: string; source: string; rationale?: string; evidence?: Array<Record<string, unknown>> };
export type Commitment = { id: string; body: string; due?: string | null; state?: string; history?: CommitmentEvent[]; execution_links?: Array<{ workbench_id: string; item_id: string }> };
export type Workbench = { id: string; name: string };
export type Project = { id: string; name: string; description?: string };
export type ExecutionItem = { id: string; workbench_id: string; status: string; result?: string | null; result_artifact_id?: string | null; completed_at?: string | null };
export type BriefActionItem = { id: string; task: string; owner: string | null; due: string | null };
export type BriefDecision = { id: string; decision_text: string; rationale: string | null; lifecycle: string };
export type BriefMeeting = { meeting_id: string; title: string | null; started_at: string; open_action_items: BriefActionItem[]; decisions: BriefDecision[] };
export type WatchPR = { title: string; repo: string; pr_number: number; days_waiting: number; url: string; room_id: string; room_name: string };
export type WatchAssignment = { summary: string; key: string; status: string; url: string; overdue: boolean; room_id: string; room_name: string };
export type WatchSummary = { prs_waiting: WatchPR[]; oldest_waiting_days: number; open_assignments: WatchAssignment[] };
export type BriefLastMeeting = { meeting_id: string; title: string | null; item_count: number; open_count: number };
/** Betterment D7: the last 1:1 with the person (else the last meeting she was in). */
export type BriefLastTime = {
  meeting_id: string; title: string | null; started_at: string; one_on_one: boolean;
  points: Array<{ id: string; task: string; owner: string | null; due: string | null; status: string | null }>;
  decisions: Array<{ id: string; decision_text: string; lifecycle: string }>;
};
/** Betterment D0/D7: his own meeting actions for this person ("I owe"). */
export type BriefMyAction = { id: string; task: string; owner: string | null; due: string | null; due_said?: string | null; status?: string | null; meeting_id: string; meeting_title: string | null };
export type OneOnOneBrief = {
  relationship_id: string;
  display_name: string | null;
  open_commitments: Array<{ id: string; body: string; visibility: Visibility; state?: string; due?: string | null }>;
  /** PHILO-17 (U09): what the person owes him, recorded by hand. */
  owed_to_you?: Array<{ id: string; body: string; visibility: Visibility; state?: string; due?: string | null }>;
  agenda_items: Array<{ id: string; body: string; visibility: Visibility; state: string }>;
  grounding_note_count: number;
  linked_meetings: BriefMeeting[];
  unlinked_meeting_count: number;
  watch_summary?: WatchSummary;
  last_meeting?: BriefLastMeeting | null;
  last_time?: BriefLastTime | null;
  i_owe_meeting_actions?: BriefMyAction[];
  /** The brief's memory: plaintext desk excerpts on this person's projects. */
  memory?: { excerpts?: Array<{ ref: string; kind: string; title: string; text: string; project_id?: string }> } | null;
};
/** Betterment D6: a name his work mentions that no Person has yet
 *  (`GET /api/people/suggestions`, PeopleService.suggestions). */
export type Suggestion = {
  key: string;
  name: string;
  said: string;
  relationship_kind: RelationshipKind;
  source: "meeting" | "1:1 series" | "jira";
  one_on_one: boolean;
  series: { uid: string; source_id: string; label: string; next_starts_at: string } | null;
  jira: boolean;
  meeting_count: number;
  promise_count: number;
  meetings: Array<{ id: string; title: string; started_at: string }>;
};
export type RelationshipDetail = Relationship & {
  commitments?: Commitment[];
  /** PHILO-17 (U09): commitments the person owes him (direction report_owes). */
  owed_to_you?: Commitment[];
  requests?: Array<{ id: string; body: string; state: string }>;
  sessions?: Session[];
  notes?: GroundingNote[];
};

export function stateOf(value: Readiness): ReadinessState {
  return value.state ?? value.readiness ?? "unconfigured";
}

export function readinessFace(state: ReadinessState) {
  switch (state) {
    case "locked": return { label: "Locked", action: "Retry" };
    case "key_unavailable": return { label: "Key unavailable", action: "Recovery" };
    case "corrupt": return { label: "Store unavailable", action: "Recovery" };
    // PHILO-13-04: a store that is down comes back by itself; the verb tries
    // it again here instead of sending him to Settings (J3-07).
    case "unavailable": return { label: "Store unavailable", action: "Try again" };
    default: return { label: "Not set up", action: "Set up" };
  }
}

export function readinessForError(cause: unknown): Readiness {
  if (!(cause instanceof ApiError)) return { readiness: "corrupt" };
  const code = String(
    cause.payload && typeof cause.payload === "object"
      ? (cause.payload as Record<string, unknown>).detail ?? ""
      : "",
  );
  if (cause.status === 423 || code === "people_key_store_locked") return { readiness: "locked" };
  // Betterment daily D8: no keychain on this Mac; not a failure to retry.
  if (code === "people_key_store_unavailable") return { readiness: "no_key_store" };
  if (code.startsWith("people_key_")) return { readiness: "key_unavailable" };
  if (cause.status === 503 || code.startsWith("people_store_")) return { readiness: "unavailable" };
  return { readiness: "corrupt" };
}

/** PHILO-13-04 (A3): the store is down (503 / `people_store_*`). The
 * person and the unsent draft stay on the window; the failure is one row
 * with Try again (J3-06). The owner's Tenet 1: no over-engineering for safety. */
export function isStoreOutage(cause: unknown): boolean {
  if (!(cause instanceof ApiError)) return false;
  const code = String(
    cause.payload && typeof cause.payload === "object"
      ? (cause.payload as Record<string, unknown>).detail ?? ""
      : "",
  ).toLowerCase();
  return cause.status === 503 || code.startsWith("people_store_");
}

/** A protected-plane failure means the encrypted DTOs must leave memory. */
export function isProtectedFailure(cause: unknown): boolean {
  if (!(cause instanceof ApiError)) return false;
  if ([409, 423, 503].includes(cause.status)) return true;
  const code = String(
    cause.payload && typeof cause.payload === "object"
      ? (cause.payload as Record<string, unknown>).detail ?? ""
      : "",
  ).toLowerCase();
  return code.startsWith("people_store_") || code.startsWith("people_key_");
}

/** HS-S33 (G33 = A): an I owe Add is two writes (the request, then its
 *  acceptance). The Prep keeps the acknowledged request id with the words
 *  he submitted while it is mounted, and finishes THAT request; it never
 *  makes a second request to repair the first. Unknown creation is said,
 *  never retried. Same mount only: a reload loses the receipt. */
export type OweAttempt =
  | { phase: "creating"; seq: number; relationshipId: string; body: string }
  | { phase: "accepting"; seq: number; relationshipId: string; body: string; requestId: string }
  | { phase: "acceptance_uncertain"; seq: number; relationshipId: string; body: string; requestId: string; note: string; acceptable: boolean }
  | { phase: "checking"; seq: number; relationshipId: string; body: string; requestId: string }
  | { phase: "saved"; seq: number; relationshipId: string; body: string; requestId: string; saved: { body: string; state: string } }
  | { phase: "creation_uncertain"; seq: number; relationshipId: string; body: string };

/** The exact codes the hub returns before any write for this invocation
 *  (V33). Every other failure of a write is unknown, not "Nothing changed". */
export const CREATE_NO_EFFECT = new Set(["principal_right_required", "people_owner_required", "people_relationship_not_found", "people_payload_required", "people_payload_invalid", "people_payload_too_large", "people_visibility_invalid"]);
export const ACCEPT_NO_EFFECT = new Set(["principal_right_required", "people_owner_required", "people_request_not_found", "people_relationship_not_found", "people_payload_invalid", "people_payload_too_large", "people_request_not_acceptable"]);

export function failureCode(cause: unknown): string {
  if (!(cause instanceof ApiError) || !cause.payload || typeof cause.payload !== "object") return "";
  const detail = (cause.payload as Record<string, unknown>).detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") return String((detail as Record<string, unknown>).code ?? "");
  return "";
}

/** An owner-auth or key failure: the private receipt leaves memory. */
export function isAuthOrKeyFailure(cause: unknown): boolean {
  if (!(cause instanceof ApiError)) return false;
  if (cause.status === 401 || cause.status === 403) return true;
  return isProtectedFailure(cause) && !isStoreOutage(cause);
}

/** Read the person once and say what happened to the held request. A read
 *  never accepts. Only a complete read with exact ids is an answer. */
export type SavedCheck =
  | { kind: "saved"; saved: { body: string; state: string } }
  | { kind: "acceptable" }
  | { kind: "unresolved"; note: string };
export function checkSavedRequest(read: unknown, relationshipId: string, requestId: string, body: string): SavedCheck {
  const relationship = read && typeof read === "object" ? (read as { relationship?: unknown }).relationship : null;
  const record = relationship && typeof relationship === "object" ? relationship as Record<string, unknown> : null;
  if (!record || record.id !== relationshipId || !Array.isArray(record.requests) || !Array.isArray(record.commitments)) {
    return { kind: "unresolved", note: "Could not read the saved request · Check again" };
  }
  const requests = (record.requests as Array<Record<string, unknown>>).filter((item) => item && item.id === requestId);
  const matches = (record.commitments as Array<Record<string, unknown>>).filter((item) => item && item.request_id === requestId);
  if (requests.length !== 1) return { kind: "unresolved", note: "The saved request is not on this person · Look in the list" };
  const state = String(requests[0].state ?? "");
  if (state === "accepted" && matches.length === 1) {
    return { kind: "saved", saved: { body: String(matches[0].body ?? ""), state: String(matches[0].state ?? "open") } };
  }
  if (state === "requested" && matches.length === 0) {
    return String(requests[0].body ?? "") === body
      ? { kind: "acceptable" }
      : { kind: "unresolved", note: "The saved words are different · Look in the list" };
  }
  // A requested record with a linked commitment can be two reads that
  // crossed; read again, never accept from it.
  return { kind: "unresolved", note: "Could not confirm the saved request · Check again" };
}

/** PHILO-13-07 (B2) — the People window's place: the person it was on. */
export const PEOPLE_PERSON_PLACE = "people/person";

/** The person's whole record: the relationship and its 1:1s, in one read. */
export async function readWhole(id: string): Promise<RelationshipDetail> {
  const [read, sessions] = await Promise.all([hub.readPerson<Relationship>(id), hub.readOneOnOnes<Session>(id)]);
  return { ...read.relationship, sessions: sessions.one_on_ones };
}

export type RosterNext = { startsAt: string; title: string };
/** Each person's soonest upcoming 1:1 from the Door's calendar rows. */
export function nextOneOnOnes(upcoming: Array<Record<string, unknown>>): Record<string, RosterNext> {
  const out: Record<string, RosterNext> = {};
  const now = Date.now();
  for (const row of upcoming) {
    const id = String(row.person_relationship_id ?? "");
    const startsAt = String(row.starts_at ?? "");
    const at = wireDate(startsAt)?.getTime();
    if (!id || at === undefined || !Number.isFinite(at)) continue;
    const ends = wireDate(String(row.ends_at ?? ""))?.getTime() ?? at;
    if (ends < now) continue;
    const current = out[id] ? wireDate(out[id].startsAt)?.getTime() ?? Infinity : Infinity;
    if (at < current) out[id] = { startsAt, title: String(row.title || row.event_title || "1:1") };
  }
  return out;
}
export const ROLE_CHOICES: Array<{ value: RelationshipKind; label: string }> = [
  { value: "direct_report", label: "Direct report" }, { value: "peer", label: "Peer" }, { value: "extended", label: "Extended" },
];
/** `Thu 10:00`, `Today 10:00`, `Oct 21 10:00`. */
export function oneOnOneWhen(isoDate: string): string {
  const d = wireDate(isoDate);
  if (!d) return "";
  const startOf = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const days = Math.round((startOf(d) - startOf(new Date())) / 86_400_000);
  const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  if (days === 0) return `Today ${time}`;
  if (days === 1) return `Tomorrow ${time}`;
  if (days > 1 && days < 7) return `${d.toLocaleDateString(undefined, { weekday: "short" })} ${time}`;
  return `${d.toLocaleDateString(undefined, { month: "short", day: "numeric" })} ${time}`;
}

export function shortWhen(isoDate: string): string {
  try {
    const d = wireDate(isoDate);
    if (!d) return "";
    const now = new Date();
    const startOf = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime(); // calendar days, not 24 h blocks
    const diffDays = Math.round((startOf(d) - startOf(now)) / 86_400_000);
    const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
    if (diffDays === 0) return `Today ${time}`;
    if (diffDays === 1) return `Tomorrow ${time}`;
    return `${d.toLocaleDateString(undefined, { weekday: "short" })} ${time}`;
  } catch { return ""; }
}

/** A due date as a short day (`Fri`); never the raw ISO string. A date-only
 * value (`YYYY-MM-DD`, the `Set a date` producer's calendar day) stays that
 * calendar day in the desk's zone; `new Date("2026-10-06")` would read it as
 * UTC midnight and show the day before west of UTC. */
export function shortDay(isoDate: string): string {
  const d = wireDate(isoDate);
  return !d ? isoDate : d.toLocaleDateString(undefined, { weekday: "short" });
}

/** The relationship's linked series, as one key: a change re-reads the brief. */
export function linkKey(relationship: Relationship): string {
  return (relationship.calendar_links ?? []).map((l) => `${l.uid}:${l.source_id}`).join("|");
}

/** `Today 17:12` → `today 17:12` inside a sentence; a weekday stays. */
export function lowerDay(words: string): string {
  return /^(Today|Tomorrow)\b/.test(words) ? words.charAt(0).toLowerCase() + words.slice(1) : words;
}

/** The first letter up (`named in Vendor sync` → `Named in Vendor sync`). */
export function sentence(words: string): string {
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : words;
}

export function relationshipLabel(kind?: string): string {
  if (kind === "direct_report") return "Direct report";
  if (kind === "peer") return "Peer";
  if (kind === "extended") return "Extended relationship";
  return "Relationship";
}

/** What the prep's read says of the last and the next 1:1. */
export type PrepNext = { at: string | null; eventId: string | null; last: string | null };

/** `in 50 min`, `in 2 h 05 min`, `now`; empty past a day. */
export function untilWords(isoDate: string, now: number): string {
  const at = wireDate(isoDate)?.getTime();
  if (at === undefined || !Number.isFinite(at)) return "";
  const minutes = Math.ceil((at - now) / 60_000);
  if (minutes <= 0) return "now";
  if (minutes < 60) return `in ${minutes} min`;
  if (minutes < 24 * 60) return `in ${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, "0")} min`;
  return "";
}

export function isOverdue(due?: string | null): boolean {
  if (!due) return false;
  const at = wireDate(due);
  if (!at) return false;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return at.getTime() < today.getTime();
}

/** `Thu Oct 8` (the day a meeting was held). */
export function dayLabel(isoDate: string): string {
  const d = wireDate(isoDate);
  return d ? d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }) : "";
}

/** A memory kind in a plain word. */
export function kindWord(kind: string): string {
  const k = String(kind || "").toLowerCase();
  if (k.includes("decision")) return "Decision";
  if (k.includes("meeting")) return "Meeting";
  if (k.includes("note")) return "Note";
  if (k.includes("item") || k.includes("action")) return "Action";
  if (k.includes("page")) return "Page";
  if (k.includes("update") || k.includes("send")) return "Update";
  return "Note";
}
