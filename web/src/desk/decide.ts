/** PHILO-13-08 (B3) — decide where the meeting is.
 *
 * A desk decision is born with a title he typed, never as a `New decision`
 * placeholder (grounding F9). One made from a meeting carries the meeting
 * (the tag `meeting:<id>`), the project he chose before Save and the
 * meeting's participants as its deciders.
 * One decision writer (2026-11-08): ONE call, `POST
 * /api/decision-records/from-desk`, creates the record AND files it in the
 * project in the hub's own transaction; the client makes no filing write.
 * An uncertain answer never creates again. */
import { ApiError, apiFetch } from "../lib/api";
import { fromWireDecision } from "./api";
import type { Decision } from "../lib/primitives";

export const meetingTag = (meetingId: string) => `meeting:${meetingId}`;
export const projectTag = (projectId: string) => `project:${projectId}`;

/** The decisions made from one meeting, newest first. */
export function decisionsFromMeeting(
  decisions: readonly Decision[] | undefined,
  meetingId: string,
): Decision[] {
  const tag = meetingTag(meetingId);
  return (decisions ?? [])
    .filter((d) => Array.isArray(d.tags) && d.tags.includes(tag))
    .sort((a, b) => String(b.createdAt || "").localeCompare(String(a.createdAt || "")));
}

/** HS-S42: what the meeting says about a decision's project, before Save.
 *  `known` holds every linked project in rank order; never only the first.
 *  `none` is a meeting with no linked project; `unavailable` is a failed
 *  lookup, which is not "no project". */
export type MeetingScope =
  | { state: "known"; projects: Array<{ id: string; name: string }> }
  | { state: "none" }
  | { state: "unavailable"; reason: string };

export async function meetingScope(meetingId: string): Promise<MeetingScope> {
  let body: unknown;
  try {
    body = await apiFetch<unknown>(`/api/meetings/${encodeURIComponent(meetingId)}/projects`);
  } catch (cause) {
    return { state: "unavailable", reason: String((cause as Error)?.message ?? cause) };
  }
  const rows = (body as { projects?: unknown })?.projects;
  if (!Array.isArray(rows)) return { state: "unavailable", reason: "The hub answered no project list" };
  const seen = new Set<string>();
  const projects: Array<{ id: string; name: string }> = [];
  for (const row of rows as Array<{ project_id?: unknown; project_name?: unknown }>) {
    const id = typeof row?.project_id === "string" ? row.project_id.trim() : "";
    if (!id || seen.has(id)) continue;
    seen.add(id);
    projects.push({ id, name: String(row.project_name ?? "").trim() || id });
  }
  return projects.length ? { state: "known", projects } : { state: "none" };
}

/** The decision's context: the meeting it came from, then its summary. */
export function meetingContext(meeting: {
  title: string;
  startedAt?: string | null;
  summary?: string | null;
}): string {
  const day = String(meeting.startedAt ?? "").slice(0, 10);
  const head = `Meeting: ${meeting.title}${day ? ` · ${day}` : ""}`;
  const summary = String(meeting.summary ?? "").trim();
  return summary ? `${head}\n\n${summary}` : head;
}

/** HS-S42: the canonical POST answered nothing usable (a malformed 2xx, a
 *  5xx or a lost response). The decision may exist: never create again. */
export class DecisionUnconfirmed extends Error {
  constructor(reason: string) {
    super(reason);
    this.name = "DecisionUnconfirmed";
  }
}

/** The project filing of a created decision record, as the hub answered
 *  it: `unfiled` is his explicit choice; `filed` the record names the
 *  project; `unknown` an answer that does not name it. */
export type FilingState = "unfiled" | "filed" | "unknown";

export interface MeetingDecision {
  decision: Decision;
  /** The canonical record every face opens. */
  recordId: string;
  /** The retained source (`desk_decision`) the meeting lists. */
  sourceId: string;
  project: { id: string; name: string } | null;
  filing: FilingState;
}

export const recordRef = (recordId: string) => `decision_record:${recordId}`;

const nonEmpty = (value: unknown): value is string => typeof value === "string" && value.trim() !== "";

/** A refusal the hub stated before it wrote (HTTP 4xx). Anything else after
 *  the POST was sent is unconfirmed. */
export const isKnownRefusal = (cause: unknown) =>
  cause instanceof ApiError && cause.status >= 400 && cause.status < 500;

export interface DeskDecisionRecordInput {
  decision: string;
  project?: { id: string; name?: string } | null;
  why?: string;
  meeting?: { id: string; title?: string; summary?: string | null } | null;
  status?: "accepted" | "proposed";
  /** Who decided, as the meeting names them; the hub resolves each name
   *  to a Person where one matches. */
  deciders?: readonly string[];
}

/** The canonical Desk producer: one POST (the hub files it) and no fallback. It
 *  returns only when both identities are acknowledged. A known refusal throws
 *  the ApiError; anything else after the send throws DecisionUnconfirmed. */
export async function createDeskDecisionRecord(input: DeskDecisionRecordInput): Promise<{
  record: Record<string, unknown>;
  recordId: string;
  decision: Decision;
}> {
  let response: Record<string, unknown>;
  try {
    response = await apiFetch<Record<string, unknown>>("/api/decision-records/from-desk", {
      method: "POST",
      json: {
        decision_text: input.decision.trim(),
        title: input.decision.trim(),
        status: input.status ?? "accepted",
        project_id: input.project?.id,
        project_name: input.project?.name,
        why: input.why,
        meeting_id: input.meeting?.id,
        meeting_title: input.meeting?.title,
        meeting_summary: input.meeting?.summary,
        deciders: input.deciders?.length ? [...input.deciders] : undefined,
      },
    });
  } catch (cause) {
    if (isKnownRefusal(cause)) throw cause;
    throw new DecisionUnconfirmed(String((cause as Error)?.message ?? cause));
  }
  const record = response?.record as Record<string, unknown> | undefined;
  const wire = response?.decision as Record<string, unknown> | undefined;
  if (!record || typeof record !== "object" || !nonEmpty(record.id) || !nonEmpty(wire?.id)) {
    throw new DecisionUnconfirmed("The hub answered no decision record");
  }
  const decision = fromWireDecision(wire);
  if (!decision) throw new DecisionUnconfirmed("The hub answered no decision record");
  return { record, recordId: String(record.id), decision };
}

/** Create one named decision from a meeting in the project he chose (`null`:
 *  deliberately no project), in one call. Throws only before both IDs are
 *  acknowledged. */
export async function decideFromMeeting(input: {
  title: string;
  meetingId: string;
  meetingTitle: string;
  startedAt?: string | null;
  summary?: string | null;
  project: { id: string; name: string } | null;
  deciders?: readonly string[];
}): Promise<MeetingDecision> {
  const title = input.title.trim();
  if (!title) throw new Error("A decision needs a title");
  const project = input.project;
  const created = await createDeskDecisionRecord({
    decision: title,
    project,
    why: meetingContext({
      title: input.meetingTitle,
      startedAt: input.startedAt,
      summary: input.summary,
    }),
    meeting: {
      id: input.meetingId,
      title: input.meetingTitle,
      summary: input.summary,
    },
    status: "accepted",
    deciders: input.deciders,
  });
  const filing: FilingState = !project ? "unfiled"
    : created.record.project_id === project.id ? "filed" : "unknown";
  return {
    decision: created.decision,
    recordId: created.recordId,
    sourceId: created.decision.id,
    project,
    filing,
  };
}
