/** PHILO-13-08 (B3) — decide where the meeting is.
 *
 * A desk decision is born with a title he typed, never as a `New decision`
 * placeholder (grounding F9). One made from a meeting carries:
 *   - the meeting: the tag `meeting:<id>` and the meeting in its context;
 *   - the meeting's project: the tag `project:<id>` and the project's
 *     membership edge (`PUT /api/projects/{id}/resources/desk_decision:<id>`,
 *     the same edge the filing strip writes).
 * Both go through the existing routes (`POST /api/decisions`, the project
 * resource route); no backend field is added (story Notes, Tenet 1). */
import { apiFetch } from "../lib/api";
import { createDecision, fromWireDecision, type DecisionInput } from "./api";
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

/** The meeting's project: the highest-confidence link, or none. */
export async function meetingProject(
  meetingId: string,
): Promise<{ id: string; name: string } | null> {
  try {
    const body = await apiFetch<{ projects?: Array<{ project_id?: string; project_name?: string }> }>(
      `/api/meetings/${encodeURIComponent(meetingId)}/projects`,
    );
    const first = (body.projects ?? []).find((p) => String(p.project_id ?? "").trim());
    return first ? { id: String(first.project_id), name: String(first.project_name ?? "") } : null;
  } catch {
    return null;
  }
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

export interface MeetingDecision {
  decision: Decision;
  project: { id: string; name: string } | null;
}

export interface DeskDecisionRecordInput {
  decision: string;
  project?: { id: string; name?: string } | null;
  why?: string;
  meeting?: { id: string; title?: string; summary?: string | null } | null;
  status?: "accepted" | "proposed";
}

/** The one Desk producer. The legacy decision is retained as the source row,
 * but the returned identity is the canonical record that every face opens. */
export async function createDeskDecisionRecord(input: DeskDecisionRecordInput): Promise<{
  record: Record<string, unknown>;
  decision: Decision;
} | null> {
  const response = await apiFetch<Record<string, unknown>>("/api/decision-records/from-desk", {
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
    },
  });
  const record = response?.record;
  const decision = fromWireDecision(response?.decision);
  // Older isolated hubs (and the compatibility unit harness) answer no
  // canonical envelope. Let their existing producer remain available until
  // the hub has the record route; a live hub always takes the branch above.
  if (!record || typeof record !== "object" || !decision) return null;
  const canonical = record as Record<string, unknown>;
  if (input.project?.id && canonical.id) {
    await apiFetch(
      `/api/projects/${encodeURIComponent(input.project.id)}/resources/${encodeURIComponent(`decision_record:${canonical.id}`)}`,
      { method: "PUT", json: { relationship: "member" } },
    );
  }
  return { record: canonical, decision };
}

/** Create one named decision from a meeting. Throws when the hub refuses
 * the decision; a refused project edge leaves the decision and its project
 * tag (the tag still names the project). */
export async function decideFromMeeting(input: {
  title: string;
  meetingId: string;
  meetingTitle: string;
  startedAt?: string | null;
  summary?: string | null;
}): Promise<MeetingDecision> {
  const title = input.title.trim();
  if (!title) throw new Error("A decision needs a title");
  const project = await meetingProject(input.meetingId);
  const canonical = await createDeskDecisionRecord({
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
  });
  if (canonical) return { decision: canonical.decision, project };
  const body: DecisionInput = {
    title,
    // PHILO-15-09 (B12): a decision he makes himself is DECIDED, never one
    // he must review (an agent's launch still proposes; the hub refuses it
    // any other status).
    status: "accepted",
    context_markdown: meetingContext({
      title: input.meetingTitle,
      startedAt: input.startedAt,
      summary: input.summary,
    }),
    tags: [meetingTag(input.meetingId), ...(project ? [projectTag(project.id)] : [])],
  };
  const decision = await createDecision(body);
  if (!decision) throw new Error("The hub returned no decision");
  if (project) {
    await apiFetch(
      `/api/projects/${encodeURIComponent(project.id)}/resources/${encodeURIComponent(`desk_decision:${decision.id}`)}`,
      { method: "PUT", json: { relationship: "member" } },
    ).catch(() => undefined);
  }
  return { decision, project };
}
