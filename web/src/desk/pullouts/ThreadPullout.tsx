/** HS-151-05 — Thread pullout content: head (in-place title, egress lamp,
 * status line, token meter), body (user/assistant rows with StreamingMaterial,
 * reasoning folded behind RAW, error row in-flow, CRASHED + Retry, sibling
 * picker, receipt short-id), foot (ThreadComposer — story 06). */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  SurfaceState,
} from "../surface/Surface";
import { Material } from "../surface/Material";
import { LampGadget } from "../surface/gadgets";
import { ContextualAssignment } from "../../pages/cores/ContextualAssignment";
import { boundaryEgressLamp, egressScopeLamp, type EgressLamp } from "../inferenceEgress";

/** The server stores the boundary name (e.g. "same_device") in egress_scope,
 * not the abstract scope ("local"). Try boundary first, fall back to scope. */
function threadEgressLamp(scope: string | null | undefined): EgressLamp {
  if (!scope) return { label: "NO MODEL", tone: "fail" };
  const boundary = boundaryEgressLamp(scope);
  if (boundary.label !== "NO MODEL") return boundary;
  return egressScopeLamp(scope);
}
import { useWriteReceipt } from "../hooks/useWriteReceipt";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import {
  useThreadStore,
  isCrashed,
  sendTurn,
  abortThread,
  patchThread,
  keepMessage,
  branchThread,
  regenerateThread,
  createThread,
  type ThreadMessage,
  type ThreadDeltaPayload,
  type ThreadTurnStartedPayload,
  type ThreadTurnDonePayload,
} from "../threads";
import { useDesk } from "../store";
import { ThreadComposer, InlineEditor } from "../components/ThreadComposer";
import type { PulloutContentProps } from "./types";
import "./thread-pullout.css";

// ── StreamingMaterial ────────────────────────────────────────────────
// Append-safe wrapper: renders the live text cheaply while streaming,
// hands the finished text to Material at turn_done so code blocks and
// mermaid finalize.
function StreamingMaterial({ text, done }: { text: string; done: boolean }) {
  if (done) return <Material>{text}</Material>;
  // While streaming, render as plain pre-wrapped text for performance.
  return (
    <div className="thread-streaming-text">
      {text}
      <span className="thread-cursor" />
    </div>
  );
}

// ── Sibling picker ──────────────────────────────────────────────────
// The server returns { message_id: [position(1-based), total] }.
// When total > 1 the picker renders; navigation reloads the thread
// with the chosen sibling path (the server picks the canonical path).
function SiblingPicker({
  position,
  total,
  onPrev,
  onNext,
}: {
  position: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}) {
  if (total <= 1) return null;
  return (
    <span className="thread-sibling-picker">
      <button
        type="button"
        className="thread-sibling-nav"
        disabled={position <= 1}
        onClick={onPrev}
        aria-label="Previous sibling"
      >
        &#x2039;
      </button>
      <span className="thread-sibling-count">
        {position}/{total}
      </span>
      <button
        type="button"
        className="thread-sibling-nav"
        disabled={position >= total}
        onClick={onNext}
        aria-label="Next sibling"
      >
        &#x203a;
      </button>
    </span>
  );
}

// ── Message row ─────────────────────────────────────────────────────
function MessageRow({
  msg,
  bufferText,
  siblingPosition,
  siblingTotal,
  onSiblingPrev,
  onSiblingNext,
  onRetry,
  onKeep,
  onBranch,
}: {
  msg: ThreadMessage;
  bufferText: string;
  siblingPosition: number;
  siblingTotal: number;
  onSiblingPrev: () => void;
  onSiblingNext: () => void;
  onRetry: (messageId: string) => void;
  onKeep: (messageId: string, as: "note" | "artifact") => void;
  /** Branch from this message: edit-and-resend (user row) or fork (assistant row). */
  onBranch: (messageId: string, text: string) => void;
}) {
  const crashed = isCrashed(msg);
  const hasError = msg.errorJson !== null && !msg.streaming;
  const isStreaming = msg.streaming && !crashed;
  const isDone = !msg.streaming && !hasError && !crashed;

  // Assemble the display text: from buffer if streaming, from parts if done.
  const displayText = isStreaming
    ? bufferText
    : msg.parts.filter((p) => p.kind === "text").map((p) => p.text).join("");
  const reasoningText = msg.parts
    .filter((p) => p.kind === "reasoning")
    .map((p) => p.text)
    .join("");

  const [showRaw, setShowRaw] = useState(false);
  const [editing, setEditing] = useState(false);
  const receiptShort = msg.receiptId && msg.receiptId.length > 4
    ? msg.receiptId.slice(-4)
    : msg.receiptId || null;

  if (msg.role === "user") {
    const userText = msg.parts.map((p) => p.text).join("") || "";
    return (
      <div className="thread-row thread-row-user" data-message-id={msg.id}>
        <div className="thread-row-label">YOU</div>
        {editing ? (
          <InlineEditor
            initialText={userText}
            onConfirm={(text) => {
              setEditing(false);
              onBranch(msg.id, text);
            }}
            onCancel={() => setEditing(false)}
            placeholder="Edit message"
          />
        ) : (
          <div
            className="thread-row-body thread-row-body-editable"
            onClick={() => setEditing(true)}
            title="Click to edit and resend"
          >
            {userText || "(empty)"}
          </div>
        )}
        <SiblingPicker
          position={siblingPosition}
          total={siblingTotal}
          onPrev={onSiblingPrev}
          onNext={onSiblingNext}
        />
      </div>
    );
  }

  return (
    <div
      className={
        "thread-row thread-row-assistant" +
        (crashed ? " thread-row-crashed" : "") +
        (hasError ? " thread-row-error" : "") +
        (isStreaming ? " thread-row-streaming" : "")
      }
      data-message-id={msg.id}
    >
      <div className="thread-row-head">
        <span className="thread-row-label">
          {msg.modelId || "ASSISTANT"}
        </span>
        {receiptShort && (
          <span className="thread-row-receipt" title={msg.receiptId ?? undefined}>
            {"receipt ····"}{receiptShort}
          </span>
        )}
        {msg.egressScope && (
          <LampGadget on {...threadEgressLamp(msg.egressScope)} />
        )}
      </div>

      {crashed && (
        <div className="thread-row-crashed-body">
          <span className="thread-crash-label">CRASHED</span>
          <button
            type="button"
            className="desk-chip is-primary"
            onClick={() => onRetry(msg.id)}
          >
            Retry
          </button>
        </div>
      )}

      {hasError && (
        <div className="thread-row-error-body">
          <span className="thread-error-severity">ERROR</span>
          <span className="thread-error-message">
            {typeof msg.errorJson?.error === "string"
              ? msg.errorJson.error
              : "Turn failed"}
          </span>
        </div>
      )}

      {!crashed && !hasError && (
        <div className="thread-row-body">
          <StreamingMaterial text={displayText} done={isDone} />
        </div>
      )}

      {reasoningText && isDone && (
        <details className="thread-raw-fold">
          <summary
            className="thread-raw-toggle"
            onClick={() => setShowRaw(!showRaw)}
          >
            RAW
          </summary>
          <pre className="thread-raw-content">{reasoningText}</pre>
        </details>
      )}

      <div className="thread-row-actions">
        <SiblingPicker
          position={siblingPosition}
          total={siblingTotal}
          onPrev={onSiblingPrev}
          onNext={onSiblingNext}
        />
        {isDone && !editing && (
          <>
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => onKeep(msg.id, "note")}
            >
              Keep as note
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => onKeep(msg.id, "artifact")}
            >
              Keep as artifact
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => setEditing(true)}
            >
              Fork here
            </button>
          </>
        )}
        {editing && (
          <InlineEditor
            initialText=""
            onConfirm={(text) => {
              setEditing(false);
              onBranch(msg.id, text);
            }}
            onCancel={() => setEditing(false)}
            placeholder="Fork message"
          />
        )}
      </div>
    </div>
  );
}

// ── ThreadPullout ───────────────────────────────────────────────────

export function ThreadPullout({ object: o }: PulloutContentProps) {
  if (o.ref.kind !== "thread") return null;
  return <ThreadPulloutInner threadId={o.id} title={o.title} />;
}

function ThreadPulloutInner({
  threadId,
  title: initialTitle,
}: {
  threadId: string;
  title: string;
}) {
  const detail = useThreadStore((s) => s.threads[threadId]);
  const buffers = useThreadStore((s) => s.buffers);
  const loading = useThreadStore((s) => s.loading[threadId]);
  const { loadThread, applyTurnStarted, applyDelta, applyTurnDone, reconcile, getBufferText } =
    useThreadStore.getState();

  const { attempt, receipt } = useWriteReceipt();
  const { subscribe, state: busState } = useRuntimeBus();

  // Title editing
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(initialTitle);
  const titleRef = useRef<HTMLInputElement>(null);

  // HS-151-06: track turn_done for focus restore
  const [restoreFocus, setRestoreFocus] = useState(false);

  const bodyRef = useRef<HTMLDivElement>(null);

  // Load thread on mount
  useEffect(() => {
    void loadThread(threadId);
  }, [threadId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [detail?.messages.length, buffers]);

  // Subscribe to bus frames for this thread
  useEffect(() => {
    const unsubs = [
      subscribe("thread_turn_started", (frame) => {
        const p = frame.data as ThreadTurnStartedPayload;
        if (p.thread_id !== threadId) return;
        applyTurnStarted(p);
      }),
      subscribe("thread_delta", (frame) => {
        const p = frame.data as ThreadDeltaPayload;
        if (p.thread_id !== threadId) return;
        applyDelta(p);
      }),
      subscribe("thread_turn_done", (frame) => {
        const p = frame.data as ThreadTurnDonePayload;
        if (p.thread_id !== threadId) return;
        applyTurnDone(p);
        // HS-151-06: restore focus to the composer after turn_done
        setRestoreFocus(true);
        requestAnimationFrame(() => setRestoreFocus(false));
      }),
    ];
    return () => unsubs.forEach((u) => u());
  }, [threadId, subscribe]);

  // Reconcile on reconnect
  const prevBusState = useRef(busState);
  useEffect(() => {
    if (prevBusState.current === "reconnecting" && busState === "connected") {
      void reconcile(threadId);
    }
    prevBusState.current = busState;
  }, [busState, threadId]);

  // Handlers
  const commitTitle = useCallback(async () => {
    setEditingTitle(false);
    if (titleDraft !== initialTitle) {
      await attempt("rename", () => patchThread(threadId, { title: titleDraft }));
    }
  }, [titleDraft, initialTitle, threadId, attempt]);

  const handleSend = useCallback(
    (text: string, refs: Array<{ ref_kind: string; ref_id: string }>) => {
      void attempt("send turn", () =>
        sendTurn(threadId, { text, refs: refs.length > 0 ? refs : undefined }),
      );
    },
    [threadId, attempt],
  );

  const handleStop = useCallback(async () => {
    const result = await attempt("stop", () => abortThread(threadId));
    // Optimistically mark messages as aborted so the UI flips from
    // Stop to Send immediately, without waiting for the bus frame.
    if (result.ok) {
      useThreadStore.getState().markAborted(threadId);
    }
  }, [threadId, attempt]);

  const handleRetry = useCallback(
    async (messageId: string) => {
      await attempt("retry", () =>
        regenerateThread(threadId, { message_id: messageId }),
      );
    },
    [threadId, attempt],
  );

  const handleKeep = useCallback(
    async (messageId: string, as: "note" | "artifact") => {
      await attempt(`keep as ${as}`, () =>
        keepMessage(threadId, { message_id: messageId, as }),
      );
    },
    [threadId, attempt],
  );

  /** HS-151-06: branch from a message (edit-and-resend + fork). No modal. */
  const handleBranch = useCallback(
    async (messageId: string, text: string) => {
      await attempt("branch", () =>
        branchThread(threadId, { message_id: messageId, text }),
      );
    },
    [threadId, attempt],
  );

  /** HS-151-06: create a new thread (/ new verb). */
  const handleNewThread = useCallback(async () => {
    const t = await createThread({});
    useDesk.getState().openPullout(`thread:${t.id}`);
    void useDesk.getState().refresh();
  }, []);

  const isStreaming = detail?.messages.some((m) => m.streaming) ?? false;

  // Token meter — guard against detail or detail.thread being absent.
  const tokenIn = detail?.thread?.token_in ?? 0;
  const tokenOut = detail?.thread?.token_out ?? 0;

  // Egress from the latest assistant message
  const lastAssistant = detail?.messages
    .filter((m) => m.role === "assistant")
    .at(-1);
  const egressLamp = lastAssistant?.egressScope
    ? threadEgressLamp(lastAssistant.egressScope)
    : null;

  if (loading && !detail) {
    return (
      <div className="desk-pullout-body desk-surface-body">
        <SurfaceState empty emptyLabel="Loading thread" emptyGlyph="..." />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="desk-pullout-body desk-surface-body">
        <SurfaceState
          empty
          emptyLabel="Thread not found"
          emptyGlyph="?"
          actionLabel="Close"
          onAction={() => undefined}
        />
      </div>
    );
  }

  return (
    <>
      <div className="desk-pullout-body desk-surface-body thread-pullout-body" ref={bodyRef}>
        {/* Head: title, egress, status, token meter */}
        <div className="thread-head">
          {editingTitle ? (
            <input
              ref={titleRef}
              className="thread-title-input"
              value={titleDraft}
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={(e) => {
                if (e.key === "Enter") void commitTitle();
                if (e.key === "Escape") {
                  setTitleDraft(initialTitle);
                  setEditingTitle(false);
                }
              }}
              autoFocus
            />
          ) : (
            <button
              type="button"
              className="thread-title"
              onClick={() => {
                setEditingTitle(true);
                setTitleDraft(detail.thread?.title || initialTitle);
              }}
            >
              {detail.thread?.title || initialTitle}
            </button>
          )}
          <div className="thread-head-instruments">
            {egressLamp && <LampGadget on {...egressLamp} />}
            {detail.thread?.status_line && (
              <span className="thread-status-line">{detail.thread?.status_line}</span>
            )}
            <span className="thread-token-meter">
              {tokenIn + tokenOut > 0 && (
                <span className="thread-token-count">
                  IN {tokenIn} / OUT {tokenOut}
                </span>
              )}
            </span>
          </div>
          {/* HS-150 assignment control — replaces PersonaChat's recipe.chat
              ContextualAssignment. Scoped to the recipe when the thread is
              recipe-bound; hidden for bare threads (no subject). */}
          {detail.thread?.recipe_id && (
            <ContextualAssignment
              label="Thread assignment"
              capabilityId="chat.turn"
              scope={{
                kind: "subject",
                subject_kind: "recipe",
                subject_id: detail.thread.recipe_id,
                capability_id: "chat.turn",
              }}
            />
          )}
        </div>

        {/* Body: turn rows */}
        {detail.messages.length === 0 ? (
          <SurfaceState
            empty
            emptyLabel="No turns"
            emptyGlyph={"▬"}
          />
        ) : (
          <div className="thread-messages">
            {detail.messages.map((msg) => {
              // Siblings: server returns { message_id: [position(1-based), total] }.
              const sibData = detail.siblings[msg.id];
              const sibPosition = Array.isArray(sibData) ? Number(sibData[0]) : 1;
              const sibTotal = Array.isArray(sibData) ? Number(sibData[1]) : 1;
              return (
                <MessageRow
                  key={msg.id}
                  msg={msg}
                  bufferText={getBufferText(msg.id)}
                  siblingPosition={sibPosition}
                  siblingTotal={sibTotal}
                  onSiblingPrev={() => void loadThread(threadId)}
                  onSiblingNext={() => void loadThread(threadId)}
                  onRetry={handleRetry}
                  onKeep={handleKeep}
                  onBranch={handleBranch}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* The foot is a direct flex child of the window shell (not
          SurfaceFooter, which is a 36px bar). The composer needs its
          full height to render the textarea + mic + Send/Stop. */}
      <div className="thread-foot">
        {receipt}
        <ThreadComposer
          onSend={handleSend}
          onStop={handleStop}
          onKeep={handleKeep}
          onFork={(messageId) => {
            void handleBranch(messageId, "");
          }}
          onNewThread={handleNewThread}
          streaming={isStreaming}
          lastAssistantId={lastAssistant?.id ?? null}
          restoreFocus={restoreFocus}
        />
      </div>
    </>
  );
}
