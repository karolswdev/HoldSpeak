/** Narrow HS-141 thought custody client.  Thought cursors never become Note fields. */
import { apiFetch } from "../lib/api";

export interface ThoughtNote {
  id: string;
  title: string;
  body_markdown: string;
  tags: string[];
  deleted?: boolean;
  last_modified?: string | null;
}

export interface Thought {
  id: string;
  source: { kind: "typed" | "voice" | "note" };
  raw_captured_at: string;
  raw_text?: string;
  state: "working" | "completed" | "tombstoned";
  aggregate_revision: number;
  lifecycle_revision: number;
  working_revision: number;
  attachment_revision: number;
  working_note: ThoughtNote;
  filing_status: "filed" | "missing";
  continuity?: { state: string; invocation_id?: string; review_result_id?: string; code?: string };
}

export interface ThoughtCompletionReceipt {
  id: string;
  kind: "thought_completed";
  thought_id: string;
  note_ref: string;
  aggregate_revision: number;
  lifecycle_revision: number;
  created_at: string;
}

export type NoteThoughtStatus =
  | { ownership: "ordinary"; note: ThoughtNote; source_precondition: { content_sha256: string; last_modified: string } }
  | { ownership: "thought"; thought: Thought };

export interface UnfinishedThought {
  id: string;
  working_note_id: string;
  source_kind: Thought["source"]["kind"];
  title: string;
  body_preview: string;
  updated_at: string;
  filing_status: "filed" | "missing";
}

export function sourceLabel(kind: Thought["source"]["kind"]): string {
  return kind === "voice" ? "Voice" : kind === "note" ? "This note" : "Typed";
}

export async function createThought(input: { request_id: string; raw_text: string; title?: string }): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>("/api/thoughts", {
    method: "POST",
    json: { request_id: input.request_id, raw_text: input.raw_text, source: { kind: "typed" }, initial_note: { title: input.title || "Thought", body_markdown: input.raw_text, tags: [] } },
  });
  return response.thought;
}

export async function thoughtForNote(noteId: string): Promise<NoteThoughtStatus> {
  return apiFetch<NoteThoughtStatus>(`/api/thoughts/for-note/${encodeURIComponent(noteId)}`);
}

export async function adoptThought(input: { request_id: string; note_id: string; expected_source_content_sha256: string; expected_source_last_modified: string }): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>("/api/thoughts/adopt", { method: "POST", json: input });
  return response.thought;
}

export async function originalThought(thoughtId: string): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>(`/api/thoughts/${encodeURIComponent(thoughtId)}/original`);
  return response.thought;
}

export async function saveThoughtWorking(thought: Thought, patch: Pick<ThoughtNote, "title" | "body_markdown" | "tags">): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>(`/api/thoughts/${encodeURIComponent(thought.id)}/working`, {
    method: "PATCH",
    json: { expected_aggregate_revision: thought.aggregate_revision, expected_working_revision: thought.working_revision, ...patch },
  });
  return response.thought;
}

export async function completeThought(input: { thought: Thought; request_id: string }): Promise<{ thought: Thought; receipt: ThoughtCompletionReceipt }> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(input.thought.id)}/complete`, {
    method: "POST",
    json: {
      request_id: input.request_id,
      expected_aggregate_revision: input.thought.aggregate_revision,
      expected_lifecycle_revision: input.thought.lifecycle_revision,
    },
  });
}

export async function resumeThought(thought: Thought): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>(`/api/thoughts/${encodeURIComponent(thought.id)}/resume`, {
    method: "POST",
    json: {
      expected_aggregate_revision: thought.aggregate_revision,
      expected_lifecycle_revision: thought.lifecycle_revision,
    },
  });
  return response.thought;
}

export async function refineThought(thought: Thought, request_id: string): Promise<{ thought: Thought; continuity: NonNullable<Thought["continuity"]> }> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(thought.id)}/refine`, { method: "POST", json: { request_id, expected_aggregate_revision: thought.aggregate_revision, expected_working_revision: thought.working_revision, expected_attachment_revision: thought.attachment_revision } });
}

export async function stopRefinement(thought: Thought, invocation_id: string): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>(`/api/thoughts/${encodeURIComponent(thought.id)}/refinements/${encodeURIComponent(invocation_id)}/stop`, { method: "POST", json: { expected_aggregate_revision: thought.aggregate_revision } });
  return response.thought;
}

export interface ThoughtReview {
  id: string;
  kind: "question" | "synthesis";
  question?: string;
  reason?: string;
  title?: string;
  body_markdown?: string;
  tags?: string[];
}

export async function reconcileThought(thought: Thought, invocation_id?: string): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>(`/api/thoughts/${encodeURIComponent(thought.id)}/reconcile`, {
    method: "POST", json: { expected_aggregate_revision: thought.aggregate_revision, invocation_id },
  });
  return response.thought;
}

export async function reviewThought(thought: Thought, reviewId: string): Promise<ThoughtReview> {
  const response = await apiFetch<{ review: ThoughtReview }>(`/api/thoughts/${encodeURIComponent(thought.id)}/reviews/${encodeURIComponent(reviewId)}`);
  return response.review;
}

export async function actOnReview(input: { thought: Thought; reviewId: string; action: "answer" | "accept" | "reject"; request_id: string; answer?: string }): Promise<{ thought: Thought }> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(input.thought.id)}/reviews/${encodeURIComponent(input.reviewId)}/${input.action}`, {
    method: "POST", json: { request_id: input.request_id, answer: input.answer || "", expected_aggregate_revision: input.thought.aggregate_revision, expected_working_revision: input.thought.working_revision, expected_attachment_revision: input.thought.attachment_revision },
  });
}

export async function unfinishedThoughts(cursor?: string): Promise<{ items: UnfinishedThought[]; next_cursor: string | null }> {
  const suffix = cursor ? `&cursor=${encodeURIComponent(cursor)}` : "";
  return apiFetch(`/api/thoughts?state=unfinished&limit=20${suffix}`);
}
