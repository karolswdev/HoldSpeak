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

export async function unfinishedThoughts(cursor?: string): Promise<{ items: UnfinishedThought[]; next_cursor: string | null }> {
  const suffix = cursor ? `&cursor=${encodeURIComponent(cursor)}` : "";
  return apiFetch(`/api/thoughts?state=unfinished&limit=20${suffix}`);
}
