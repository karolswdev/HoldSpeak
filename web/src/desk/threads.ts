/** HS-150-05 — the Thread data layer: typed API client for the D4 contract
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

export interface ThreadWire {
  id: string;
  title: string;
  recipe_id: string | null;
  profile_override: string | null;
  directory_id: string | null;
  parent_thread_id: string | null;
  status_line: string | null;
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

  return { thread, messages, siblings, refs };
}

export async function patchThread(
  id: string,
  patch: { title?: string; profile_override?: string },
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
}

export const useThreadStore = create<ThreadStoreState & ThreadStoreActions>((set, get) => ({
  threads: {},
  buffers: {},
  loading: {},
  focusMessageId: null,

  async loadThread(id) {
    set((s) => ({ loading: { ...s.loading, [id]: true } }));
    try {
      const detail = await getThread(id);
      set((s) => ({
        threads: { ...s.threads, [id]: detail },
        loading: { ...s.loading, [id]: false },
      }));
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
}));
