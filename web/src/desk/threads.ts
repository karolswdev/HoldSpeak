/** HS-151-05 — the Thread data layer: typed API client for the D4 contract
 * (POST /api/threads, GET list/get, PATCH, DELETE, /turns, /abort, /branch,
 * /regenerate, /keep, /import) and a zustand slice holding threads by id,
 * message path + siblings map + refs, per-message streaming buffer.
 *
 * Bus subscription for thread_turn_started / thread_delta / thread_turn_done
 * applies deltas by seq, drops duplicates/out-of-order, and refetch-and-
 * reconcile on reconnect. */
import { create } from "zustand";
import { apiFetch } from "../lib/api";

// ── wire types (snake_case from the hub) ──────────────────────────────

/** HS-153-01: resolved mode from the server (recipe with kind='mode'). */
export interface ThreadMode {
  id: string;
  name: string;
  avatar: string;
}

export interface ThreadWire {
  id: string;
  title: string;
  recipe_id: string | null;
  profile_override: string | null;
  directory_id: string | null;
  parent_thread_id: string | null;
  status_line: string | null;
  call_mode: number;
  mode: ThreadMode | null;
  token_in: number;
  token_out: number;
  created_at: string;
  updated_at: string;
  last_turn_at: string | null;
}

export type MessageRole = "user" | "assistant" | "system" | "tool";

export interface ThreadMessageWire {
  id: string;
  thread_id: string;
  parent_id: string | null;
  role: MessageRole;
  streaming: number;
  operation_id: string | null;
  receipt_id: string | null;
  invocation_id: string | null;
  egress_scope: string | null;
  egress_host: string | null;
  model_id: string | null;
  route_plan_id: string | null;
  stats_json: Record<string, unknown> | null;
  error_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  aborted_at: string | null;
  deleted_at: string | null;
}

export type PartKind = "text" | "reasoning" | "tool_call" | "attachment" | "annotation";

export interface ThreadPartWire {
  id: string;
  message_id: string;
  ordinal: number;
  kind: PartKind;
  text: string | null;
  tool_call_id: string | null;
  attachment_ref: string | null;
  meta_json: Record<string, unknown> | null;
  sensitive: number;
}

export interface ThreadRefWire {
  id: string;
  thread_id: string;
  message_id: string;
  ref_kind: string;
  ref_id: string;
  version: string | null;
  frozen_json: Record<string, unknown> | null;
  created_at: string;
}

// ── app-side types (camelCase) ────────────────────────────────────────

export interface ThreadMessage {
  id: string;
  threadId: string;
  parentId: string | null;
  role: MessageRole;
  streaming: boolean;
  operationId: string | null;
  receiptId: string | null;
  egressScope: string | null;
  egressHost: string | null;
  modelId: string | null;
  statsJson: Record<string, unknown> | null;
  errorJson: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
  abortedAt: string | null;
  parts: ThreadPart[];
}

export interface ThreadPart {
  id: string;
  messageId: string;
  ordinal: number;
  kind: PartKind;
  text: string;
  sensitive: boolean;
  metaJson?: Record<string, unknown>;
  toolCallId?: string;
}

// ── Tool row model (HS-152-04) ─────────────────────────────────────

export type ToolRowState =
  | "pending"
  | "awaiting_decision"
  | "elicitation"
  | "running"
  | "receipted"
  | "failed"
  | "denied";

export interface ToolRow {
  callId: string;
  messageId: string;
  name: string;
  toolClass: string;
  argsHead: string;
  state: ToolRowState;
  decisionRequired: boolean;
  elicitation?: Record<string, unknown>;
  receiptId?: string;
  outcome?: string;
  kind?: string;
  summary?: string;
  sensitive?: boolean;
  error?: string;
  /** HS-152-05: structured result payload for per-kind renderers.
   * Populated on hydration from the tool-role message part text (full JSON).
   * Not available on live frames — renderers fall back to summary. */
  payload?: Record<string, unknown>;
  /** HS-153-03: guardrail-determined default decision.
   * "deny" when a violation names this call and control_mode != yolo;
   * "allow" otherwise; undefined when no guardrail ran. */
  defaultDecision?: "deny" | "allow";
}

/** HS-153-03: guardrail evaluation row (in-flow, beside tool rows). */
export interface GuardrailRow {
  messageId: string;
  violations: string[];
  warnings: string[];
  guardrails: string[];
  raw?: Record<string, unknown>;
}

// ── Tool frame payloads (HS-152-04) ────────────────────────────────

export interface ThreadToolPendingPayload {
  thread_id: string;
  message_id: string;
  call_id: string;
  name: string;
  args_head: string;
  class: string;
  decision_required: boolean;
  elicitation?: Record<string, unknown>;
  /** HS-153-03: guardrail-determined default decision. */
  default_decision?: "deny" | "allow";
}

/** HS-153-03: guardrail evaluation frame payload. */
export interface ThreadGuardrailPayload {
  thread_id: string;
  message_id: string;
  violations: string[];
  warnings: string[];
  guardrails: string[];
  raw?: Record<string, unknown>;
}

export interface ThreadToolResultPayload {
  thread_id: string;
  message_id: string;
  call_id: string;
  name: string;
  receipt_id: string;
  outcome: string;
  kind: string;
  summary: string;
  sensitive: boolean;
}

export interface ThreadStatusLinePayload {
  thread_id: string;
  text: string;
}

export interface ThreadRef {
  id: string;
  threadId: string;
  messageId: string;
  refKind: string;
  refId: string;
  frozenJson: Record<string, unknown> | null;
  createdAt: string;
}

// ── wire → app mappers ───────────────────────────────────────────────

/** Convert a wire timestamp to an ISO-8601 string.  The hub returns epoch
 * seconds (float) for all timestamps; the app stores ISO-8601 strings. */
function wireTimestamp(v: unknown): string {
  if (typeof v === "number" && v > 1_000_000) {
    return new Date(v * 1000).toISOString();
  }
  return typeof v === "string" && v ? v : new Date().toISOString();
}

/** Parse a timestamp the same way the crash rule will compare it. */
export function parseTimestamp(v: string): number {
  const ms = new Date(v).getTime();
  return Number.isFinite(ms) ? ms : Date.now();
}

/** Convert a wire message dict (which may carry inline parts) to a
 * ThreadMessage.  The server embeds parts inside each message dict
 * (not as a separate top-level array). */
function toMessage(w: Record<string, unknown>): ThreadMessage {
  const inlineParts = Array.isArray(w.parts) ? w.parts : [];
  return {
    id: String(w.id ?? ""),
    threadId: String(w.thread_id ?? ""),
    parentId: w.parent_id != null ? String(w.parent_id) : null,
    role: (w.role as MessageRole) ?? "assistant",
    streaming: w.streaming === 1 || w.streaming === true,
    operationId: w.operation_id != null ? String(w.operation_id) : null,
    receiptId: w.receipt_id != null ? String(w.receipt_id) : null,
    egressScope: w.egress_scope != null ? String(w.egress_scope) : null,
    egressHost: w.egress_host != null ? String(w.egress_host) : null,
    modelId: w.model_id != null ? String(w.model_id) : null,
    statsJson: (w.stats_json as Record<string, unknown>) ?? null,
    errorJson: (w.error_json as Record<string, unknown>) ?? null,
    createdAt: wireTimestamp(w.created_at),
    updatedAt: wireTimestamp(w.updated_at),
    completedAt: w.completed_at != null ? wireTimestamp(w.completed_at) : null,
    abortedAt: w.aborted_at != null ? wireTimestamp(w.aborted_at) : null,
    parts: inlineParts
      .sort((a: Record<string, unknown>, b: Record<string, unknown>) =>
        Number(a.ordinal ?? 0) - Number(b.ordinal ?? 0))
      .map((p: Record<string, unknown>) => ({
        id: String(p.id ?? ""),
        messageId: String(p.message_id ?? w.id ?? ""),
        ordinal: Number(p.ordinal ?? 0),
        kind: (p.kind as PartKind) ?? "text",
        text: String(p.text ?? ""),
        sensitive: p.sensitive === 1 || p.sensitive === true,
        ...(p.meta_json && typeof p.meta_json === "object"
          ? { metaJson: p.meta_json as Record<string, unknown> }
          : {}),
        ...(p.tool_call_id
          ? { toolCallId: String(p.tool_call_id) }
          : {}),
      })),
  };
}

function toRef(w: Record<string, unknown>): ThreadRef {
  return {
    id: String(w.id ?? ""),
    threadId: String(w.thread_id ?? ""),
    messageId: String(w.message_id ?? ""),
    refKind: String(w.ref_kind ?? ""),
    refId: String(w.ref_id ?? ""),
    frozenJson: (w.frozen_json as Record<string, unknown>) ?? null,
    createdAt: wireTimestamp(w.created_at),
  };
}

// ── API client ──────────────────────────────────────────────────────

export interface ThreadDetail {
  thread: ThreadWire;
  messages: ThreadMessage[];
  siblings: Record<string, string[]>;
  refs: ThreadRef[];
  /** HS-153-04: draft annotation parts from the server. */
  draftAnnotations: DraftAnnotation[];
}

export async function createThread(opts: {
  title?: string;
  recipe_id?: string;
  profile_override?: string;
  seed_refs?: Array<{ ref_kind: string; ref_id: string }>;
}): Promise<ThreadWire> {
  return apiFetch<ThreadWire>("/api/threads", { method: "POST", json: opts });
}

export async function listThreads(): Promise<ThreadWire[]> {
  const d = await apiFetch<Record<string, unknown>>("/api/threads");
  return (Array.isArray(d.threads) ? d.threads : []) as ThreadWire[];
}

/** List threads whose refs name a specific object id. */
export async function listThreadsByRef(refId: string): Promise<ThreadWire[]> {
  const d = await apiFetch<Record<string, unknown>>(
    `/api/threads?ref_id=${encodeURIComponent(refId)}`,
  );
  return (Array.isArray(d.threads) ? d.threads : []) as ThreadWire[];
}

export async function getThread(id: string): Promise<ThreadDetail> {
  const d = await apiFetch<Record<string, unknown>>(`/api/threads/${encodeURIComponent(id)}`);

  // The server returns a FLAT dict: thread fields at root level, plus
  // messages, siblings, refs arrays mixed in.  Extract the thread wire
  // from the root (not a nested "thread" key).
  const thread: ThreadWire = {
    id: String(d.id ?? id),
    title: String(d.title ?? "Thread"),
    recipe_id: d.recipe_id != null ? String(d.recipe_id) : null,
    profile_override: d.profile_override != null ? String(d.profile_override) : null,
    directory_id: d.directory_id != null ? String(d.directory_id) : null,
    parent_thread_id: d.parent_thread_id != null ? String(d.parent_thread_id) : null,
    status_line: d.status_line != null ? String(d.status_line) : null,
    call_mode: Number(d.call_mode ?? 0),
    mode: d.mode && typeof d.mode === "object"
      ? { id: String((d.mode as Record<string, unknown>).id ?? ""),
          name: String((d.mode as Record<string, unknown>).name ?? ""),
          avatar: String((d.mode as Record<string, unknown>).avatar ?? "") }
      : null,
    token_in: Number(d.token_in ?? 0),
    token_out: Number(d.token_out ?? 0),
    created_at: wireTimestamp(d.created_at),
    updated_at: wireTimestamp(d.updated_at),
    last_turn_at: d.last_turn_at != null ? wireTimestamp(d.last_turn_at) : null,
  };

  // Messages carry inline parts (not a separate flat array).
  const rawMessages = Array.isArray(d.messages) ? d.messages : [];
  const messages = rawMessages.map((m: unknown) =>
    toMessage(m as Record<string, unknown>),
  );

  // Server returns siblings as { message_id: [n, total] } — the position
  // of this message among its siblings and the total count.  The UI
  // needs { parent_id: [sibling_id_1, sibling_id_2, ...] }.  Since the
  // server only gives the count, we store the raw map and the pullout
  // reads it as { message_id: [n, total] } (a 2-element array).
  const rawSiblings = (d.siblings ?? {}) as Record<string, unknown>;
  const siblings: Record<string, string[]> = {};
  for (const [msgId, val] of Object.entries(rawSiblings)) {
    if (Array.isArray(val) && val.length === 2) {
      // Convert [n, total] to a synthetic sibling id list so the picker works.
      // The message itself is at index n (1-based from the server).
      // We store { message_id: [position(1-based), total] } for the picker.
      siblings[msgId] = val.map(String);
    } else if (Array.isArray(val)) {
      siblings[msgId] = val.map(String);
    }
  }

  const rawRefs = Array.isArray(d.refs) ? d.refs : [];
  const refs = rawRefs.map((r: unknown) => toRef(r as Record<string, unknown>));

  // HS-153-04: parse draft annotations from the server response.
  const rawAnnotations = Array.isArray(d.draft_annotations) ? d.draft_annotations : [];
  const draftAnnotations: DraftAnnotation[] = rawAnnotations.map((a: unknown) => {
    const ann = a as Record<string, unknown>;
    return {
      id: String(ann.id ?? ""),
      kind: String(ann.kind ?? "annotation"),
      text: ann.text != null ? String(ann.text) : null,
      ordinal: Number(ann.ordinal ?? 0),
      sensitive: Boolean(ann.sensitive),
      ...(ann.meta_json && typeof ann.meta_json === "object"
        ? { meta_json: ann.meta_json as DraftAnnotation["meta_json"] }
        : {}),
    };
  });

  return { thread, messages, siblings, refs, draftAnnotations };
}

export async function patchThread(
  id: string,
  patch: {
    title?: string;
    profile_override?: string;
    recipe_id?: string;
    call_mode?: number;
    toggle_guardrail?: string;
    toggle_guardrail_enable?: boolean;
  },
): Promise<ThreadWire> {
  return apiFetch<ThreadWire>(`/api/threads/${encodeURIComponent(id)}`, {
    method: "PATCH",
    json: patch,
  });
}

export async function deleteThread(id: string): Promise<void> {
  await apiFetch(`/api/threads/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export interface TurnResult {
  thread_id: string;
  user_message_id: string;
  assistant_message_id: string;
}

export async function sendTurn(
  threadId: string,
  body: { text: string; refs?: Array<{ ref_kind: string; ref_id: string }>; parent_id?: string },
): Promise<TurnResult> {
  return apiFetch<TurnResult>(`/api/threads/${encodeURIComponent(threadId)}/turns`, {
    method: "POST",
    json: body,
  });
}

export async function abortThread(threadId: string): Promise<void> {
  await apiFetch(`/api/threads/${encodeURIComponent(threadId)}/abort`, { method: "POST" });
}

export async function branchThread(
  threadId: string,
  body: { message_id: string; text: string },
): Promise<TurnResult> {
  return apiFetch<TurnResult>(`/api/threads/${encodeURIComponent(threadId)}/branch`, {
    method: "POST",
    json: body,
  });
}

export async function regenerateThread(
  threadId: string,
  body: { message_id: string },
): Promise<TurnResult> {
  return apiFetch<TurnResult>(`/api/threads/${encodeURIComponent(threadId)}/regenerate`, {
    method: "POST",
    json: body,
  });
}

export async function keepMessage(
  threadId: string,
  body: { message_id: string; as: "artifact" | "note" },
): Promise<{ id: string }> {
  return apiFetch<{ id: string }>(`/api/threads/${encodeURIComponent(threadId)}/keep`, {
    method: "POST",
    json: body,
  });
}

export async function importThreads(
  payload: Record<string, unknown>,
): Promise<{ imported: string[] }> {
  return apiFetch<{ imported: string[] }>("/api/threads/import", {
    method: "POST",
    json: payload,
  });
}

/** HS-152-04: Resolve a held tool call. */
export async function decideToolCall(
  threadId: string,
  callId: string,
  decision: "approve" | "deny",
  opts?: { always?: boolean; answer?: unknown },
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/api/threads/${encodeURIComponent(threadId)}/decide`,
    {
      method: "POST",
      json: {
        call_id: callId,
        decision,
        ...(opts?.always ? { always: true } : {}),
        ...(opts?.answer !== undefined ? { answer: opts.answer } : {}),
      },
    },
  );
}

// ── annotations (HS-153-04) ─────────────────────────────────────────

export interface DraftAnnotation {
  id: string;
  kind: string;
  text: string | null;
  ordinal: number;
  sensitive: boolean;
  meta_json?: {
    source: string;
    quote: string;
    comment: string;
    anchor_message_id: string;
  };
}

export async function addAnnotation(
  threadId: string,
  body: { message_id: string; quote: string; comment: string },
): Promise<DraftAnnotation> {
  return apiFetch<DraftAnnotation>(
    `/api/threads/${encodeURIComponent(threadId)}/annotations`,
    { method: "POST", json: body },
  );
}

export async function deleteAnnotation(
  threadId: string,
  partId: string,
): Promise<void> {
  await apiFetch(
    `/api/threads/${encodeURIComponent(threadId)}/annotations/${encodeURIComponent(partId)}`,
    { method: "DELETE" },
  );
}

// ── streaming buffer ────────────────────────────────────────────────

export interface StreamingBuffer {
  messageId: string;
  /** Parts accumulated by ordinal, keyed by ordinal for O(1) append. */
  parts: Map<number, { kind: PartKind; text: string }>;
  /** Highest seq processed — deltas with seq <= this are duplicates. */
  highSeq: number;
}

// ── bus frame payloads (D3 contract) ────────────────────────────────

export interface ThreadTurnStartedPayload {
  thread_id: string;
  message_id: string;
  user_message_id: string;
  model_id: string;
  /** The server sends egress as a plain scope string. */
  egress: string | null;
}

export interface ThreadDeltaPayload {
  thread_id: string;
  message_id: string;
  ordinal: number;
  kind: PartKind;
  text: string;
  seq: number;
}

export interface ThreadTurnDonePayload {
  thread_id: string;
  message_id: string;
  receipt_id: string;
  outcome: string;
  /** The server sends egress as a plain scope string (e.g. "same_device"),
   * not as an object. */
  egress: string | null;
  stats: { prompt_tokens?: number; completion_tokens?: number; error?: string } | null;
}

/** HS-154-03: call mode state frame from the server. */
export interface ThreadCallStatePayload {
  thread_id: string;
  state: "off" | "listening" | "thinking" | "speaking";
}

// ── zustand store ───────────────────────────────────────────────────

/** The crash rule: streaming=1 and updated_at older than 10s = CRASHED. */
export const CRASH_TIMEOUT_MS = 10_000;

export function isCrashed(msg: ThreadMessage): boolean {
  if (!msg.streaming) return false;
  const elapsed = Date.now() - parseTimestamp(msg.updatedAt);
  return elapsed > CRASH_TIMEOUT_MS;
}

export interface ThreadStoreState {
  /** Thread detail keyed by thread id. */
  threads: Record<string, ThreadDetail>;
  /** Per-message streaming buffers keyed by message id. */
  buffers: Record<string, StreamingBuffer>;
  /** Loading flag per thread id. */
  loading: Record<string, boolean>;
  /** Message id to scroll/focus when opening a thread from search. */
  focusMessageId: string | null;
  /** HS-152-04: tool rows keyed by thread id -> call id. */
  toolRows: Record<string, Record<string, ToolRow>>;
  /** HS-152-04: live status line per thread. */
  statusLines: Record<string, string>;
  /** HS-153-03: guardrail rows keyed by thread id -> message id. */
  guardrailRows: Record<string, Record<string, GuardrailRow>>;
  /** HS-153-04: draft annotations keyed by thread id. */
  draftAnnotations: Record<string, DraftAnnotation[]>;
}

export interface ThreadStoreActions {
  /** Load a thread detail from the API, merging into the store. */
  loadThread(id: string): Promise<void>;
  /** Apply a thread_turn_started frame. */
  applyTurnStarted(payload: ThreadTurnStartedPayload): void;
  /** Apply a thread_delta frame by seq. Drops duplicates and out-of-order. */
  applyDelta(payload: ThreadDeltaPayload): boolean;
  /** Apply a thread_turn_done frame. Finalizes the message. */
  applyTurnDone(payload: ThreadTurnDonePayload): void;
  /** Refetch and reconcile after reconnect. */
  reconcile(threadId: string): Promise<void>;
  /** Remove a thread from the store. */
  removeThread(id: string): void;
  /** Get the assembled text for a streaming buffer. */
  getBufferText(messageId: string): string;
  /** Set the message id to scroll to when opening a thread from search. */
  setFocusMessage(messageId: string | null): void;
  /** Optimistically mark all streaming messages as aborted for a thread,
   * so the UI flips from Stop to Send immediately without waiting for
   * the bus frame. */
  markAborted(threadId: string): void;
  /** HS-152-04: Apply a thread_tool_pending frame. */
  applyToolPending(payload: ThreadToolPendingPayload): void;
  /** HS-152-04: Apply a thread_tool_result frame. */
  applyToolResult(payload: ThreadToolResultPayload): void;
  /** HS-152-04: Apply a thread_status_line frame. */
  applyStatusLine(payload: ThreadStatusLinePayload): void;
  /** HS-152-04: Optimistically decide a tool call, reconcile on result. */
  decideOptimistic(threadId: string, callId: string, decision: "approve" | "deny"): void;
  /** HS-152-04: Hydrate tool rows from persisted parts after load. */
  hydrateToolRows(threadId: string): void;
  /** HS-153-01: Set the active mode for a thread (optimistic + PATCH + GET). */
  setMode(threadId: string, recipeId: string): Promise<void>;
  /** HS-153-03: Apply a thread_guardrail frame. */
  applyGuardrail(payload: ThreadGuardrailPayload): void;
}

export const useThreadStore = create<ThreadStoreState & ThreadStoreActions>((set, get) => ({
  threads: {},
  buffers: {},
  loading: {},
  focusMessageId: null,
  toolRows: {},
  statusLines: {},
  guardrailRows: {},
  draftAnnotations: {},

  async loadThread(id) {
    set((s) => ({ loading: { ...s.loading, [id]: true } }));
    try {
      const detail = await getThread(id);
      set((s) => ({
        threads: { ...s.threads, [id]: detail },
        loading: { ...s.loading, [id]: false },
        // HS-153-04: hydrate draft annotations from server response.
        draftAnnotations: {
          ...s.draftAnnotations,
          [id]: detail.draftAnnotations ?? [],
        },
      }));
      // HS-152-04: hydrate tool rows from persisted parts
      get().hydrateToolRows(id);
    } catch {
      set((s) => ({ loading: { ...s.loading, [id]: false } }));
    }
  },

  applyTurnStarted(payload) {
    const { thread_id, message_id, model_id, egress } = payload;
    const detail = get().threads[thread_id];
    if (!detail) return;
    // Create a new streaming message stub if not already present.
    const existing = detail.messages.find((m) => m.id === message_id);
    if (existing) return;
    const stub: ThreadMessage = {
      id: message_id,
      threadId: thread_id,
      parentId: null,
      role: "assistant",
      streaming: true,
      operationId: null,
      receiptId: null,
      egressScope: (typeof egress === "string" && egress) ? egress : null,
      egressHost: null,
      modelId: model_id,
      statsJson: null,
      errorJson: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      completedAt: null,
      abortedAt: null,
      parts: [],
    };
    set((s) => ({
      threads: {
        ...s.threads,
        [thread_id]: {
          ...detail,
          messages: [...detail.messages, stub],
        },
      },
      buffers: {
        ...s.buffers,
        [message_id]: { messageId: message_id, parts: new Map(), highSeq: -1 },
      },
    }));
  },

  applyDelta(payload) {
    const { message_id, ordinal, kind, text, seq } = payload;
    const buffer = get().buffers[message_id];
    // No buffer means we missed turn_started — ignore or it is for another thread.
    if (!buffer) return false;
    // Drop duplicates and out-of-order.
    if (seq <= buffer.highSeq) return false;
    const existing = buffer.parts.get(ordinal);
    const newParts = new Map(buffer.parts);
    if (existing) {
      newParts.set(ordinal, { kind, text: existing.text + text });
    } else {
      newParts.set(ordinal, { kind, text });
    }
    set((s) => ({
      buffers: {
        ...s.buffers,
        [message_id]: { ...buffer, parts: newParts, highSeq: seq },
      },
    }));
    return true;
  },

  applyTurnDone(payload) {
    const { thread_id, message_id, receipt_id, outcome, egress, stats } = payload;
    const detail = get().threads[thread_id];
    if (!detail) return;
    const buffer = get().buffers[message_id];
    // Finalize: merge buffer parts into the message.
    const finalParts: ThreadPart[] = [];
    if (buffer) {
      const sorted = [...buffer.parts.entries()].sort((a, b) => a[0] - b[0]);
      for (const [ordinal, p] of sorted) {
        finalParts.push({
          id: `${message_id}-${ordinal}`,
          messageId: message_id,
          ordinal,
          kind: p.kind,
          text: p.text,
          sensitive: false,
        });
      }
    }
    const messages = detail.messages.map((m) => {
      if (m.id !== message_id) return m;
      return {
        ...m,
        streaming: false,
        receiptId: receipt_id || m.receiptId,
        // egress is a plain scope string from the server, not {scope, host}.
        egressScope: (typeof egress === "string" && egress) ? egress : m.egressScope,
        completedAt: (outcome === "succeeded" || outcome === "failed")
          ? new Date().toISOString() : m.completedAt,
        abortedAt: outcome === "aborted" ? new Date().toISOString() : m.abortedAt,
        errorJson: (outcome === "failed" || outcome === "error")
          ? {
              error:
                typeof stats?.error === "string"
                  ? stats.error
                  : typeof stats?.error === "object" && stats.error !== null
                    ? String((stats.error as Record<string, unknown>).message || "turn failed")
                    : "turn failed",
            }
          : m.errorJson,
        statsJson: stats ? { prompt_tokens: stats.prompt_tokens, completion_tokens: stats.completion_tokens } : m.statsJson,
        parts: finalParts.length > 0 ? finalParts : m.parts,
      };
    });
    // Clean up buffer.
    const newBuffers = { ...get().buffers };
    delete newBuffers[message_id];
    set((s) => ({
      threads: {
        ...s.threads,
        [thread_id]: { ...detail, messages },
      },
      buffers: newBuffers,
    }));
    // HS-152-05: refresh thread metadata (status_line, tokens) and hydrate
    // tool rows with full payloads from persisted parts (fire-and-forget).
    void get().loadThread(thread_id);
  },

  async reconcile(threadId) {
    // Refetch the thread to catch anything missed during reconnect.
    await get().loadThread(threadId);
  },

  removeThread(id) {
    set((s) => {
      const threads = { ...s.threads };
      delete threads[id];
      return { threads };
    });
  },

  getBufferText(messageId) {
    const buffer = get().buffers[messageId];
    if (!buffer) return "";
    const sorted = [...buffer.parts.entries()].sort((a, b) => a[0] - b[0]);
    return sorted
      .filter(([, p]) => p.kind === "text")
      .map(([, p]) => p.text)
      .join("");
  },

  setFocusMessage(messageId) {
    set({ focusMessageId: messageId });
  },

  markAborted(threadId) {
    const detail = get().threads[threadId];
    if (!detail) return;
    const hasStreaming = detail.messages.some((m) => m.streaming);
    if (!hasStreaming) return;
    const messages = detail.messages.map((m) =>
      m.streaming
        ? { ...m, streaming: false, abortedAt: new Date().toISOString() }
        : m,
    );
    // Clean up any streaming buffers for this thread's messages.
    const newBuffers = { ...get().buffers };
    for (const m of detail.messages) {
      if (m.streaming) delete newBuffers[m.id];
    }
    set((s) => ({
      threads: { ...s.threads, [threadId]: { ...detail, messages } },
      buffers: newBuffers,
    }));
  },

  // ── HS-152-04: tool row actions ──────────────────────────────────

  applyToolPending(payload) {
    const { thread_id, call_id, message_id, name, args_head } = payload;
    const toolClass = payload["class"] || "";
    const decisionRequired = payload.decision_required;
    const hasElicitation = !!payload.elicitation;

    const state: ToolRowState = hasElicitation
      ? "elicitation"
      : decisionRequired
        ? "awaiting_decision"
        : "pending";

    const row: ToolRow = {
      callId: call_id,
      messageId: message_id,
      name,
      toolClass,
      argsHead: args_head,
      state,
      decisionRequired,
      ...(payload.elicitation ? { elicitation: payload.elicitation } : {}),
      ...(payload.default_decision ? { defaultDecision: payload.default_decision } : {}),
    };

    set((s) => ({
      toolRows: {
        ...s.toolRows,
        [thread_id]: { ...(s.toolRows[thread_id] || {}), [call_id]: row },
      },
    }));
  },

  applyToolResult(payload) {
    const { thread_id, call_id, receipt_id, outcome, kind, summary, sensitive } = payload;
    const existing = get().toolRows[thread_id]?.[call_id];
    if (!existing) return;

    const isError = ["tool_execution_failed", "tool_denied", "tool_timeout", "pass_cap_reached", "tool_unknown", "cancelled", "error"].includes(kind);
    const newState: ToolRowState = kind === "tool_denied"
      ? "denied"
      : isError
        ? "failed"
        : "receipted";

    const updated: ToolRow = {
      ...existing,
      state: newState,
      receiptId: receipt_id,
      outcome,
      kind,
      summary,
      sensitive,
      ...(isError ? { error: kind } : {}),
    };

    set((s) => ({
      toolRows: {
        ...s.toolRows,
        [thread_id]: { ...(s.toolRows[thread_id] || {}), [call_id]: updated },
      },
    }));
  },

  applyStatusLine(payload) {
    const { thread_id, text } = payload;
    set((s) => ({
      statusLines: { ...s.statusLines, [thread_id]: text },
    }));
  },

  decideOptimistic(threadId, callId, decision) {
    const existing = get().toolRows[threadId]?.[callId];
    if (!existing) return;

    const newState: ToolRowState = decision === "approve" ? "running" : "denied";
    const updated: ToolRow = { ...existing, state: newState };

    set((s) => ({
      toolRows: {
        ...s.toolRows,
        [threadId]: { ...(s.toolRows[threadId] || {}), [callId]: updated },
      },
    }));
  },

  hydrateToolRows(threadId) {
    const detail = get().threads[threadId];
    if (!detail) return;

    const rows: Record<string, ToolRow> = {};

    // Build a map of tool_call_id -> result metadata + payload from tool-role messages
    const resultMap: Record<string, {
      kind: string;
      receiptId: string;
      sensitive: boolean;
      payload?: Record<string, unknown>;
      summary?: string;
    }> = {};
    for (const msg of detail.messages) {
      if (msg.role !== "tool") continue;
      for (const part of msg.parts) {
        const tcId = part.toolCallId;
        const meta = part.metaJson;
        if (tcId && meta) {
          // HS-152-05: parse the tool-role part text as JSON for the result payload
          let parsedPayload: Record<string, unknown> | undefined;
          if (part.text) {
            try {
              const parsed = JSON.parse(part.text);
              if (parsed && typeof parsed === "object") {
                parsedPayload = parsed as Record<string, unknown>;
              }
            } catch {
              // Not valid JSON — leave payload undefined
            }
          }
          resultMap[tcId] = {
            kind: String(meta.kind ?? "data"),
            receiptId: String(meta.receipt_id ?? ""),
            sensitive: part.sensitive,
            payload: parsedPayload,
            summary: part.text ? part.text.slice(0, 200) : undefined,
          };
        }
      }
    }

    // Extract tool_call parts from assistant messages
    for (const msg of detail.messages) {
      if (msg.role !== "assistant") continue;
      for (const part of msg.parts) {
        if (part.kind !== "tool_call" || !part.metaJson) continue;
        const meta = part.metaJson;
        const callId = String(meta.id ?? "");
        if (!callId) continue;

        const result = resultMap[callId];
        const isError = result && ["tool_execution_failed", "tool_denied", "tool_timeout", "cancelled", "error"].includes(result.kind);

        let state: ToolRowState;
        if (result) {
          state = result.kind === "tool_denied" ? "denied" : isError ? "failed" : "receipted";
        } else {
          const serverState = String(meta.state ?? "");
          state = serverState === "awaiting_decision" ? "awaiting_decision" : "pending";
        }

        rows[callId] = {
          callId,
          messageId: msg.id,
          name: String(meta.name ?? ""),
          toolClass: String(meta["class"] ?? ""),
          argsHead: String(meta.arguments ?? "").slice(0, 80),
          state,
          decisionRequired: !result && String(meta.state ?? "") === "awaiting_decision",
          ...(result ? {
            receiptId: result.receiptId,
            kind: result.kind,
            sensitive: result.sensitive,
            outcome: isError ? "failed" : "succeeded",
            ...(isError ? { error: result.kind } : {}),
            ...(result.payload ? { payload: result.payload } : {}),
            ...(result.summary ? { summary: result.summary } : {}),
          } : {}),
        };
      }
    }

    if (Object.keys(rows).length > 0) {
      set((s) => ({
        toolRows: { ...s.toolRows, [threadId]: { ...(s.toolRows[threadId] || {}), ...rows } },
      }));
    }
  },

  async setMode(threadId, recipeId) {
    // Optimistic: update the thread's recipe_id in the store immediately.
    const detail = get().threads[threadId];
    if (detail) {
      set((s) => ({
        threads: {
          ...s.threads,
          [threadId]: {
            ...detail,
            thread: { ...detail.thread, recipe_id: recipeId || null },
          },
        },
      }));
    }
    // PATCH the thread, then GET to confirm (reconciles the resolved mode).
    try {
      await patchThread(threadId, { recipe_id: recipeId });
      await get().loadThread(threadId);
    } catch {
      // Revert on failure — reload the thread to get the real state.
      await get().loadThread(threadId);
    }
  },

  // ── HS-153-03: guardrail actions ──────────────────────────────────

  applyGuardrail(payload) {
    const { thread_id, message_id, violations, warnings, guardrails, raw } = payload;
    const row: GuardrailRow = {
      messageId: message_id,
      violations: violations || [],
      warnings: warnings || [],
      guardrails: guardrails || [],
      ...(raw ? { raw } : {}),
    };
    set((s) => ({
      guardrailRows: {
        ...s.guardrailRows,
        [thread_id]: { ...(s.guardrailRows[thread_id] || {}), [message_id]: row },
      },
    }));
  },
}));
