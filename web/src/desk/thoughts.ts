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
  attachment_sha256?: string;
  attachments?: ThoughtAttachment[];
  working_note: ThoughtNote;
  filing_status: "filed" | "missing";
  continuity?: { state: string; invocation_id?: string; review_result_id?: string; code?: string };
}

export type ThoughtWorkspaceState =
  | "idle"
  | "reserved"
  | "in_flight"
  | "awaiting_projection"
  | "question"
  | "synthesis"
  | "stale"
  | "named_failure"
  | "completed";

export type ThoughtWorkspaceActionKind =
  | "refine"
  | "configure_ai"
  | "stop_refinement"
  | "answer_and_continue"
  | "answer_review"
  | "accept_review"
  | "reject_review"
  | "refresh_context"
  | "detach_context"
  | "complete"
  | "resume";

export interface ThoughtWorkspaceAction {
  kind: ThoughtWorkspaceActionKind;
  review_result_id?: string;
  invocation_id?: string;
  ref?: string;
}

export interface ThoughtWorkspaceCursor {
  hub_id: string;
  thought_id: string;
  aggregate_revision: number;
  continuity_revision: number;
}

export interface ThoughtPlacementReceipt {
  state: "available";
  actual_placement: {
    target_id: string;
    target_name: string;
    target_kind: string;
    boundary: string;
    owner: string;
    transport: string;
    data_classes: string[];
    engine: string;
    model?: string | null;
    fallback_reason?: string | null;
  };
  egress: { scope: "local" | "private_network" | "cloud" | "mesh"; host?: string | null };
}

export interface ThoughtAppendEffect {
  kind: "clarification_appended";
  thought_id: string;
  working_revision: number;
  prior_body_sha256: string;
  body_sha256: string;
  append_utf8_start: number;
  append_utf8_end: number;
  append_sha256: string;
  committed_post_cursor: ThoughtWorkspaceCursor;
}

export interface ThoughtWorkspaceReview extends ThoughtReview {
  placement?: ThoughtPlacementReceipt | { state: "unavailable" } | null;
  frozen_aggregate_revision: number;
  frozen_working_revision: number;
  frozen_attachment_revision: number;
}

export interface ThoughtWorkspaceProjection {
  schema_version: 1;
  process_scope: {
    kind: "hub_local";
    hub_id: string;
    state: "available" | "unavailable";
  };
  workspace_cursor: ThoughtWorkspaceCursor;
  thought: Thought;
  workspace_state: ThoughtWorkspaceState;
  actions: {
    primary: ThoughtWorkspaceAction | null;
    state: ThoughtWorkspaceAction[];
    ambient: Array<"update_working" | "attach_context" | "complete">;
  };
  review: ThoughtWorkspaceReview | null;
  context_status: {
    summary: string;
    state: "empty" | "current" | "stale" | "missing";
    repair_ref: string | null;
  };
  inference: {
    availability: "ready" | "unavailable";
    continuation_admission: "ready" | "unavailable";
    intended_placement: { target_id: string; target_name: string; target_kind: string; boundary: string; readiness: string } | null;
  };
  terminal_status: { code: string; category: "owner_terminal" | "integrity" | "indeterminate" | "retryable"; retryable: boolean; message?: string } | null;
}

export interface ThoughtAttachmentLeaf {
  ref: string;
  title: string;
  version_label: string;
}

export interface ThoughtAttachment {
  ref: string;
  kind: "note" | "knowledge";
  title: string;
  leaf_count: number;
  state: "current" | "stale" | "missing";
  leaves: ThoughtAttachmentLeaf[];
  is_default?: boolean;
}

export interface ThoughtContextCandidate {
  ref: string;
  kind: "note" | "knowledge";
  title: string;
  leaf_count: number;
  state: "current" | "stale" | "missing";
  selected?: boolean;
  disabled?: boolean;
  disabled_reason?: string;
  is_default?: boolean;
}

export interface ThoughtDefaultContextSelection {
  ref: string;
  title: string;
  leaf_count: number;
  state: "current" | "missing" | "invalid";
}

export interface ThoughtDefaultContext {
  revision: number;
  configuration_sha256: string;
  refs: string[];
  selections: ThoughtDefaultContextSelection[];
}

export interface ThoughtContextListing {
  attachments: ThoughtAttachment[];
  pinned: ThoughtContextCandidate[];
  recent: ThoughtContextCandidate[];
  results: ThoughtContextCandidate[];
  next_cursor: string | null;
  default_context: ThoughtDefaultContext;
}

export interface ThoughtContextReceipt {
  id: string;
  action: "attach" | "detach" | "refresh";
  ref: string;
  title: string;
  leaf_count: number;
  leaves: ThoughtAttachmentLeaf[];
  scope?: "this_thought";
  default_context_changed?: false;
}

export interface ThoughtDefaultContextReceipt {
  id: string;
  action: "replace_default_context";
  scope: "future_thoughts";
  prior_revision: number;
  revision: number;
  configuration_sha256: string;
  refs: string[];
  selections: Array<Pick<ThoughtDefaultContextSelection, "ref" | "title" | "leaf_count">>;
  no_op: boolean;
  existing_thoughts_changed: 0;
}

export interface ThoughtDefaultApplicationReceipt {
  id: string;
  action: "apply_default_context";
  scope: "this_thought";
  thought_id: string;
  default_revision: number;
  default_configuration_sha256: string;
  status: "empty" | "applied" | "not_applied";
  attachment_zero_sha256: string;
  attachment_revision: number;
  attachment_sha256: string;
  attachments: Array<Pick<ThoughtAttachment, "ref" | "title" | "leaf_count">>;
  failure?: {
    code: string;
    selections: Array<{ ref: string; title: string }>;
    leaf?: { ref: string; title: string };
  };
}

export interface ThoughtUsedContextReceipt {
  visible_count: number;
  leaf_count: number;
  summary: string;
  attachments: Array<Omit<ThoughtAttachment, "state">>;
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
  continuity_state:
    | "idle"
    | "reserved"
    | "in_flight"
    | "awaiting_projection"
    | "review_ready"
    | "stale"
    | "named_failure"
    | "unavailable_remote";
  filing_status: "filed" | "missing";
}

export function sourceLabel(kind: Thought["source"]["kind"]): string {
  return kind === "voice" ? "Voice" : kind === "note" ? "This note" : "Typed";
}

export async function createThought(input: { request_id: string; raw_text: string; title?: string }): Promise<{ thought: Thought; default_context_receipt: ThoughtDefaultApplicationReceipt }> {
  return apiFetch<{ thought: Thought; default_context_receipt: ThoughtDefaultApplicationReceipt }>("/api/thoughts", {
    method: "POST",
    json: { request_id: input.request_id, raw_text: input.raw_text, source: { kind: "typed" }, initial_note: { title: input.title || "Thought", body_markdown: input.raw_text, tags: [] } },
  });
}

export async function thoughtForNote(noteId: string): Promise<NoteThoughtStatus> {
  return apiFetch<NoteThoughtStatus>(`/api/thoughts/for-note/${encodeURIComponent(noteId)}`);
}

export async function thoughtWorkbench(thoughtId: string, signal?: AbortSignal): Promise<ThoughtWorkspaceProjection> {
  return apiFetch<ThoughtWorkspaceProjection>(
    `/api/thoughts/${encodeURIComponent(thoughtId)}/workbench`,
    { signal },
  );
}

export async function adoptThought(input: { request_id: string; note_id: string; expected_source_content_sha256: string; expected_source_last_modified: string }): Promise<{ thought: Thought; default_context_receipt: ThoughtDefaultApplicationReceipt }> {
  return apiFetch<{ thought: Thought; default_context_receipt: ThoughtDefaultApplicationReceipt }>("/api/thoughts/adopt", { method: "POST", json: input });
}

export async function originalThought(thoughtId: string): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought }>(`/api/thoughts/${encodeURIComponent(thoughtId)}/original`);
  return response.thought;
}

export async function saveThoughtWorking(thought: Thought, patch: Pick<ThoughtNote, "title" | "body_markdown" | "tags">): Promise<Thought> {
  const response = await saveThoughtWorkingInWorkspace(thought, patch);
  return response.thought;
}

export async function saveThoughtWorkingInWorkspace(thought: Thought, patch: Pick<ThoughtNote, "title" | "body_markdown" | "tags">, workspace_cursor?: ThoughtWorkspaceCursor): Promise<{ thought: Thought; workbench?: ThoughtWorkspaceProjection }> {
  return apiFetch<{ thought: Thought; workbench?: ThoughtWorkspaceProjection }>(`/api/thoughts/${encodeURIComponent(thought.id)}/working`, {
    method: "PATCH",
    json: { expected_aggregate_revision: thought.aggregate_revision, expected_working_revision: thought.working_revision, ...patch, ...(workspace_cursor ? { workspace_cursor } : {}) },
  });
}

export async function completeThought(input: { thought: Thought; request_id: string; workspace_cursor?: ThoughtWorkspaceCursor }): Promise<{ thought: Thought; receipt: ThoughtCompletionReceipt; workbench?: ThoughtWorkspaceProjection }> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(input.thought.id)}/complete`, {
    method: "POST",
    json: {
      request_id: input.request_id,
      expected_aggregate_revision: input.thought.aggregate_revision,
      expected_lifecycle_revision: input.thought.lifecycle_revision,
      ...(input.workspace_cursor ? { workspace_cursor: input.workspace_cursor } : {}),
    },
  });
}

export async function resumeThought(thought: Thought, workspace_cursor?: ThoughtWorkspaceCursor): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought; workbench?: ThoughtWorkspaceProjection }>(`/api/thoughts/${encodeURIComponent(thought.id)}/resume`, {
    method: "POST",
    json: {
      expected_aggregate_revision: thought.aggregate_revision,
      expected_lifecycle_revision: thought.lifecycle_revision,
      ...(workspace_cursor ? { workspace_cursor } : {}),
    },
  });
  return response.thought;
}

export async function refineThought(thought: Thought, request_id: string, workspace_cursor?: ThoughtWorkspaceCursor): Promise<{ thought: Thought; continuity: NonNullable<Thought["continuity"]>; workbench?: ThoughtWorkspaceProjection }> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(thought.id)}/refine`, { method: "POST", json: { request_id, expected_aggregate_revision: thought.aggregate_revision, expected_working_revision: thought.working_revision, expected_attachment_revision: thought.attachment_revision, ...(workspace_cursor ? { workspace_cursor } : {}) } });
}

export async function stopRefinement(thought: Thought, invocation_id: string, workspace_cursor?: ThoughtWorkspaceCursor): Promise<Thought> {
  const response = await apiFetch<{ thought: Thought; workbench?: ThoughtWorkspaceProjection }>(`/api/thoughts/${encodeURIComponent(thought.id)}/refinements/${encodeURIComponent(invocation_id)}/stop`, { method: "POST", json: { expected_aggregate_revision: thought.aggregate_revision, ...(workspace_cursor ? { workspace_cursor } : {}) } });
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
  used_context?: ThoughtUsedContextReceipt;
}

export async function listThoughtContext(
  thoughtId: string,
  input: { view?: "compact" | "browse"; query?: string; cursor?: string; limit?: number } = {},
): Promise<ThoughtContextListing> {
  const params = new URLSearchParams({ view: input.view || "compact" });
  if (input.query) params.set("query", input.query);
  if (input.cursor) params.set("cursor", input.cursor);
  if (input.limit) params.set("limit", String(input.limit));
  return apiFetch(`/api/thoughts/${encodeURIComponent(thoughtId)}/context?${params.toString()}`);
}

export async function replaceDefaultThoughtContext(input: {
  request_id: string;
  expected_revision: number;
  refs: string[];
}): Promise<{ default_context: ThoughtDefaultContext; receipt: ThoughtDefaultContextReceipt }> {
  return apiFetch("/api/thoughts/default-context", { method: "PUT", json: input });
}

async function mutateThoughtContext(
  thought: Thought,
  action: "attach" | "detach" | "refresh",
  ref: string,
  request_id: string,
  workspace_cursor?: ThoughtWorkspaceCursor,
): Promise<{ thought: Thought; receipt: ThoughtContextReceipt; workbench?: ThoughtWorkspaceProjection }> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(thought.id)}/context/${action}`, {
    method: "POST",
    json: {
      request_id,
      ref,
      expected_aggregate_revision: thought.aggregate_revision,
      expected_working_revision: thought.working_revision,
      expected_attachment_revision: thought.attachment_revision,
      ...(workspace_cursor ? { workspace_cursor } : {}),
    },
  });
}

export const attachThoughtContext = (
  thought: Thought, ref: string, request_id: string, workspace_cursor?: ThoughtWorkspaceCursor,
) => mutateThoughtContext(thought, "attach", ref, request_id, workspace_cursor);

export const detachThoughtContext = (
  thought: Thought, ref: string, request_id: string, workspace_cursor?: ThoughtWorkspaceCursor,
) => mutateThoughtContext(thought, "detach", ref, request_id, workspace_cursor);

export const refreshThoughtContext = (
  thought: Thought, ref: string, request_id: string, workspace_cursor?: ThoughtWorkspaceCursor,
) => mutateThoughtContext(thought, "refresh", ref, request_id, workspace_cursor);

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

export async function actOnReview(input: { thought: Thought; reviewId: string; action: "answer" | "accept" | "reject"; request_id: string; answer?: string; workspace_cursor?: ThoughtWorkspaceCursor }): Promise<{ thought: Thought; receipt?: { effect?: ThoughtAppendEffect }; workbench?: ThoughtWorkspaceProjection }> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(input.thought.id)}/reviews/${encodeURIComponent(input.reviewId)}/${input.action}`, {
    method: "POST", json: { request_id: input.request_id, answer: input.answer || "", expected_aggregate_revision: input.thought.aggregate_revision, expected_working_revision: input.thought.working_revision, expected_attachment_revision: input.thought.attachment_revision, ...(input.workspace_cursor ? { workspace_cursor: input.workspace_cursor } : {}) },
  });
}

export async function answerAndContinue(input: {
  thought_id: string;
  reviewId: string;
  command_id: string;
  answer: string;
  workspace_cursor: ThoughtWorkspaceCursor;
  expected_aggregate_revision: number;
  expected_working_revision: number;
  expected_attachment_revision: number;
}): Promise<{
  thought: Thought;
  receipt: { id: string; kind: "answer_and_continue"; effect: ThoughtAppendEffect; child_invocation_id: string };
  workbench: ThoughtWorkspaceProjection;
}> {
  return apiFetch(`/api/thoughts/${encodeURIComponent(input.thought_id)}/reviews/${encodeURIComponent(input.reviewId)}/answer-and-continue`, {
    method: "POST",
    json: {
      command_id: input.command_id,
      answer: input.answer,
      expected_aggregate_revision: input.expected_aggregate_revision,
      expected_working_revision: input.expected_working_revision,
      expected_attachment_revision: input.expected_attachment_revision,
      workspace_cursor: input.workspace_cursor,
    },
  });
}

export async function unfinishedThoughts(cursor?: string): Promise<{ items: UnfinishedThought[]; next_cursor: string | null }> {
  const suffix = cursor ? `&cursor=${encodeURIComponent(cursor)}` : "";
  return apiFetch(`/api/thoughts?state=unfinished&limit=3${suffix}`);
}
