/** HS-151-05 — Thread pullout content: head (in-place title, egress lamp,
 * status line, token meter), body (user/assistant rows with StreamingMaterial,
 * reasoning folded behind RAW, error row in-flow, CRASHED + Retry, sibling
 * picker, receipt short-id), foot (ThreadComposer — story 06). */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  SurfaceState,
  SurfaceRows,
  SurfaceRow,
} from "../surface/Surface";
import { Material } from "../surface/Material";
import { intelBadge } from "../chair/lanes/MeetingsLane";
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
  decideToolCall,
  type ThreadMessage,
  type ThreadDeltaPayload,
  type ThreadTurnStartedPayload,
  type ThreadTurnDonePayload,
  type ThreadToolPendingPayload,
  type ThreadToolResultPayload,
  type ThreadStatusLinePayload,
  type ToolRow,
  type ToolRowState,
} from "../threads";
import { useDesk } from "../store";
import { ThreadComposer, InlineEditor } from "../components/ThreadComposer";
import type { PulloutContentProps } from "./types";
import "./thread-pullout.css";

// HS-152-04: stable empty refs for zustand selectors (avoid infinite re-render).
const EMPTY_TOOL_ROWS: Record<string, ToolRow> = {};

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

// ── Tool class glyphs (HS-152-04) ──────────────────────────────────
const CLASS_GLYPHS: Record<string, string> = {
  evidence_read: "R",
  candidate_builder: "B",
  effect_proposal: "E",
};

// ── Elicitation form (HS-152-04) ───────────────────────────────────
// Renders a minimal JSON-Schema form for string/number/boolean/enum fields.
function ElicitationForm({
  schema,
  onSubmit,
  onDecline,
}: {
  schema: Record<string, unknown>;
  onSubmit: (answer: Record<string, unknown>) => void;
  onDecline: () => void;
}) {
  const properties = (schema.properties ?? {}) as Record<string, Record<string, unknown>>;
  const required = (schema.required ?? []) as string[];
  const prompt = String(schema.prompt ?? schema.description ?? "");
  const [values, setValues] = useState<Record<string, unknown>>({});

  const fields = Object.entries(properties);

  const handleChange = (key: string, value: unknown) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="thread-elicitation-form" data-testid="elicitation-form">
      {prompt && <div className="thread-elicitation-prompt">{prompt}</div>}
      {fields.map(([key, prop]) => {
        const type = String(prop.type ?? "string");
        const enumVals = Array.isArray(prop.enum) ? prop.enum : null;
        const label = String(prop.title ?? key);
        const isReq = required.includes(key);
        return (
          <div key={key} className={`thread-elicitation-field${type === "boolean" ? " thread-elicitation-field--boolean" : ""}`}>
            {type !== "boolean" && (
              <label className="thread-elicitation-label">
                {label}{isReq ? " *" : ""}
              </label>
            )}
            {enumVals ? (
              <select
                className="thread-elicitation-select"
                value={String(values[key] ?? "")}
                onChange={(e) => handleChange(key, e.target.value)}
              >
                <option value="">--</option>
                {enumVals.map((v: unknown) => (
                  <option key={String(v)} value={String(v)}>{String(v)}</option>
                ))}
              </select>
            ) : type === "boolean" ? (
              <label className="thread-elicitation-boolean">
                <input
                  type="checkbox"
                  checked={Boolean(values[key])}
                  onChange={(e) => handleChange(key, e.target.checked)}
                />
                <span className="thread-elicitation-label">{label}{isReq ? " *" : ""}</span>
              </label>
            ) : type === "number" || type === "integer" ? (
              <input
                type="number"
                className="thread-elicitation-input"
                value={String(values[key] ?? "")}
                onChange={(e) => handleChange(key, Number(e.target.value))}
              />
            ) : (
              <input
                type="text"
                className="thread-elicitation-input"
                value={String(values[key] ?? "")}
                onChange={(e) => handleChange(key, e.target.value)}
              />
            )}
          </div>
        );
      })}
      <div className="thread-tool-decision-actions">
        <button
          type="button"
          className="desk-chip is-primary"
          onClick={() => onSubmit(values)}
          data-testid="elicitation-submit"
        >
          Submit
        </button>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={onDecline}
          data-testid="elicitation-decline"
        >
          Decline
        </button>
      </div>
    </div>
  );
}

// ── Per-kind result renderers (HS-152-05) ──────────────────────────
// Thin projection wrappers using the same Surface primitives (SurfaceRow,
// SurfaceRows, Material) that DoorBoardLane, MeetingsLane, DecisionPullout,
// and the People overlay build on. The full components cannot be imported
// directly because they depend on useDesk, apiFetch, useSurfaceWindows,
// and router context. These projections render the data the tool returned.

/** Meeting chip: SurfaceRow with title, date, intel badge — the same
 *  visual vocabulary as MeetingsLane (ChairLane + intelBadge). */
function MeetingResultView({ data }: { data: Record<string, unknown> }) {
  const meetings = Array.isArray(data.meetings) ? data.meetings : null;
  const items = meetings ?? [data];
  return (
    <div data-testid="result-meeting">
      <SurfaceRows>
        {items.slice(0, 8).map((m: Record<string, unknown>, i: number) => {
          const title = String(m.title ?? m.name ?? "Meeting");
          const date = m.started_at ?? m.created_at;
          const badge = intelBadge(m.intel_status as string | undefined);
          return (
            <SurfaceRow
              key={String(m.id ?? i)}
              glyph={<span className="thread-result-glyph">{"▣"}</span>}
              title={title}
              detail={date ? String(date).slice(0, 16) : undefined}
              meta={badge}
            />
          );
        })}
      </SurfaceRows>
      {items.length > 8 && <div className="thread-result-more">+{items.length - 8} more</div>}
    </div>
  );
}

/** People card projection: display name + readiness ONLY, never ledger text.
 *  Uses SurfaceRow like the People overlay's relationship grid. */
function PersonResultView({ data }: { data: Record<string, unknown> }) {
  const relationships = Array.isArray(data.relationships) ? data.relationships : null;
  const items = relationships ?? [data];
  return (
    <div data-testid="result-person">
      <SurfaceRows>
        {items.slice(0, 8).map((r: Record<string, unknown>, i: number) => {
          const displayName = String(r.display_name ?? r.name ?? "Person");
          const readiness = String(r.readiness_state ?? r.readiness ?? "");
          return (
            <SurfaceRow
              key={String(r.id ?? i)}
              title={displayName}
              meta={readiness ? readiness.toUpperCase() : undefined}
            />
          );
        })}
      </SurfaceRows>
      {items.length > 8 && <div className="thread-result-more">+{items.length - 8} more</div>}
    </div>
  );
}

/** Board projection: card titles grouped by column, using the same
 *  column/card vocabulary as DoorBoardLane. */
function BoardResultView({ data }: { data: Record<string, unknown> }) {
  // door.get returns {board: {overdue: [...], now: [...], ...}, counts: {...}}
  const board = data.board as Record<string, unknown[]> | undefined;
  const cards = Array.isArray(data.cards) ? data.cards : null;
  const counts = data.counts as Record<string, number> | undefined;

  if (board && typeof board === "object") {
    const columnNames = Object.keys(board);
    return (
      <div className="thread-result-board" data-testid="result-board">
        {counts && (
          <div className="thread-result-board-summary">
            {Object.entries(counts).filter(([, v]) => v > 0).map(([k, v]) => (
              <span key={k} className="thread-result-board-col">{k}: {v}</span>
            ))}
          </div>
        )}
        <SurfaceRows>
          {columnNames.flatMap((col) =>
            (Array.isArray(board[col]) ? board[col] : []).slice(0, 3).map((card: unknown, i: number) => {
              const c = card as Record<string, unknown>;
              return (
                <SurfaceRow
                  key={String(c.id ?? `${col}-${i}`)}
                  title={String(c.text ?? c.title ?? "Card")}
                  detail={String(c.owner ?? "")}
                  meta={col.toUpperCase()}
                />
              );
            }),
          )}
        </SurfaceRows>
      </div>
    );
  }
  // follow_through.board returns {cards: [...]}
  if (cards) {
    return (
      <div className="thread-result-board" data-testid="result-board">
        <SurfaceRows>
          {cards.slice(0, 8).map((card: unknown, i: number) => {
            const c = card as Record<string, unknown>;
            return (
              <SurfaceRow
                key={String(c.id ?? i)}
                title={String(c.text ?? c.title ?? "Card")}
                detail={String(c.owner ?? "")}
                meta={String(c.continuity_state ?? "").toUpperCase()}
              />
            );
          })}
        </SurfaceRows>
        {cards.length > 8 && <div className="thread-result-more">+{cards.length - 8} more</div>}
      </div>
    );
  }
  return <KeyValueTable data={data} />;
}

/** Note: renders through Material (the existing markdown renderer),
 *  same as DecisionPullout uses for decision body sections.
 *  desk.list(notes) returns a plain array; desk.get returns a single object. */
function NoteResultView({ data }: { data: Record<string, unknown> }) {
  // desk.list returns a plain array (JSON array at top level)
  const items: Array<Record<string, unknown>> | null = Array.isArray(data)
    ? (data as unknown as Array<Record<string, unknown>>)
    : Array.isArray(data.items)
      ? (data.items as Array<Record<string, unknown>>)
      : null;
  if (items) {
    if (items.length === 0) {
      return <div data-testid="result-note"><span className="thread-result-detail">(no notes)</span></div>;
    }
    return (
      <div data-testid="result-note">
        <SurfaceRows>
          {items.slice(0, 8).map((n: Record<string, unknown>, i: number) => {
            const title = String(n.title ?? n.name ?? "Note");
            const body = String(n.body_markdown ?? n.body ?? n.text ?? "");
            return (
              <SurfaceRow
                key={String(n.id ?? i)}
                title={title}
                detail={body.slice(0, 60) || undefined}
              />
            );
          })}
        </SurfaceRows>
        {items.length > 8 && <div className="thread-result-more">+{items.length - 8} more</div>}
      </div>
    );
  }
  // Single note (desk.get)
  const body = String(data.body_markdown ?? data.body ?? data.text ?? data.content ?? "");
  const title = String(data.title ?? data.name ?? "");
  return (
    <div data-testid="result-note">
      {title && <div className="thread-result-note-title">{title}</div>}
      {body ? <Material>{body}</Material> : <span className="thread-result-detail">(empty)</span>}
    </div>
  );
}

/** Decision card projection: title, lifecycle/outcome, rationale head.
 *  Uses the same layout as DecisionPullout's desk-decision-card section. */
function DecisionResultView({ data }: { data: Record<string, unknown> }) {
  const records = Array.isArray(data.records) ? data.records : null;
  const items = records ?? [data];
  return (
    <div data-testid="result-decision">
      <SurfaceRows>
        {items.slice(0, 8).map((r: Record<string, unknown>, i: number) => {
          const title = String(r.title ?? r.decision_text ?? r.decision ?? "Decision");
          const lifecycle = String(r.lifecycle ?? r.outcome ?? r.status ?? "");
          return (
            <SurfaceRow
              key={String(r.id ?? i)}
              title={title}
              meta={lifecycle ? lifecycle.toUpperCase() : undefined}
              detail={r.rationale ? String(r.rationale).slice(0, 80) : undefined}
            />
          );
        })}
      </SurfaceRows>
      {items.length > 8 && <div className="thread-result-more">+{items.length - 8} more</div>}
    </div>
  );
}

/** Unknown kind: key/value table (the fallback for unrecognized result shapes). */
function KeyValueTable({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data).filter(
    ([, v]) => v !== null && v !== undefined && typeof v !== "object",
  ).slice(0, 20);
  const objectEntries = Object.entries(data).filter(
    ([, v]) => v !== null && typeof v === "object",
  );
  return (
    <div className="thread-result-table" data-testid="result-table">
      {entries.map(([k, v]) => (
        <div key={k} className="thread-result-table-row">
          <span className="thread-result-table-key">{k}</span>
          <span className="thread-result-table-val">{String(v)}</span>
        </div>
      ))}
      {objectEntries.length > 0 && (
        <div className="thread-result-table-row">
          <span className="thread-result-table-key">+{objectEntries.length} object{objectEntries.length !== 1 ? "s" : ""}</span>
        </div>
      )}
    </div>
  );
}

/** RAW fold: collapsed JSON for any receipted row, always visible. */
function RawFold({ payload, summary }: { payload?: Record<string, unknown>; summary?: string }) {
  const text = payload ? JSON.stringify(payload, null, 2) : (summary || "");
  if (!text) return null;
  return (
    <details className="thread-raw-fold" data-testid="raw-fold">
      <summary className="thread-raw-toggle">{"RAW ▸"}</summary>
      <pre className="thread-raw-content">{text}</pre>
    </details>
  );
}

/** Dispatch to the right renderer based on kind. Always shows something
 *  for a receipted row: the per-kind view, the key/value table, or at
 *  minimum the summary text + RAW fold. */
function ToolResultRenderer({ row }: { row: ToolRow }) {
  if (row.state !== "receipted") return null;
  const kind = row.kind ?? "data";
  const data = row.payload;
  const truncated = row.payload?.truncated === true;

  // Without payload, show summary text + RAW fold
  if (!data) {
    return (
      <div className="thread-result-block" data-testid="result-block">
        {row.summary && (
          <div className="thread-result-summary" data-testid="result-summary">{row.summary}</div>
        )}
        <RawFold summary={row.summary} />
      </div>
    );
  }

  let renderer: React.ReactNode = null;
  switch (kind) {
    case "meeting":
      renderer = <MeetingResultView data={data} />;
      break;
    case "person":
      renderer = <PersonResultView data={data} />;
      break;
    case "board":
      renderer = <BoardResultView data={data} />;
      break;
    case "note":
      renderer = <NoteResultView data={data} />;
      break;
    case "decision":
      renderer = <DecisionResultView data={data} />;
      break;
    default:
      renderer = <KeyValueTable data={data} />;
      break;
  }

  return (
    <div className="thread-result-block" data-testid="result-block">
      {truncated && <span className="thread-result-truncated">TRUNCATED</span>}
      {renderer}
      <RawFold payload={data} />
    </div>
  );
}

// ── Tool row (HS-152-04) ───────────────────────────────────────────
function ToolRowView({
  row,
  threadId,
  onDecide,
}: {
  row: ToolRow;
  threadId: string;
  onDecide: (callId: string, decision: "approve" | "deny", opts?: { always?: boolean; answer?: unknown }) => void;
}) {
  const classGlyph = CLASS_GLYPHS[row.toolClass] || "?";
  const receiptShort = row.receiptId && row.receiptId.length > 4
    ? row.receiptId.slice(-4)
    : row.receiptId || null;

  const stateLabel: Record<ToolRowState, string> = {
    pending: "PENDING",
    awaiting_decision: "HELD",
    elicitation: "QUESTION",
    running: "RUNNING",
    receipted: "DONE",
    failed: "FAILED",
    denied: "DENIED",
  };

  const stateClass: Record<ToolRowState, string> = {
    pending: "",
    awaiting_decision: "thread-tool-held",
    elicitation: "thread-tool-held",
    running: "thread-tool-running",
    receipted: "",
    failed: "thread-tool-error",
    denied: "thread-tool-error",
  };

  return (
    <div
      className={`thread-tool-row ${stateClass[row.state] || ""}`}
      data-testid="tool-row"
      data-call-id={row.callId}
      data-tool-state={row.state}
    >
      <div className="thread-tool-row-head">
        <span className="thread-tool-class-glyph" title={row.toolClass}>{classGlyph}</span>
        <span className="thread-tool-name">{row.name}</span>
        <span className="thread-tool-state">{stateLabel[row.state]}</span>
        {row.sensitive && (
          <span className="thread-tool-people-badge" data-testid="people-badge">PEOPLE</span>
        )}
        {receiptShort && (
          <span className="thread-tool-receipt">{"····"}{receiptShort}</span>
        )}
        {row.outcome && row.state === "receipted" && (
          <span className="thread-tool-outcome">{row.outcome}</span>
        )}
      </div>

      {row.argsHead && (
        <div className="thread-tool-args-head" title={row.argsHead}>
          {row.argsHead.length > 60 ? row.argsHead.slice(0, 60) + "..." : row.argsHead}
        </div>
      )}

      {/* Decision box: Allow once / Allow always / Deny */}
      {row.state === "awaiting_decision" && (
        <div className="thread-tool-decision-box" data-testid="decision-box">
          <div className="thread-tool-decision-actions">
            <button
              type="button"
              className="desk-chip is-primary"
              onClick={() => onDecide(row.callId, "approve")}
              data-testid="allow-once"
            >
              Allow once
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => onDecide(row.callId, "approve", { always: true })}
              data-testid="allow-always"
            >
              Allow always
            </button>
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => onDecide(row.callId, "deny")}
              data-testid="deny"
            >
              Deny
            </button>
          </div>
        </div>
      )}

      {/* Elicitation form */}
      {row.state === "elicitation" && row.elicitation && (
        <ElicitationForm
          schema={row.elicitation}
          onSubmit={(answer) => onDecide(row.callId, "approve", { answer })}
          onDecline={() => onDecide(row.callId, "deny")}
        />
      )}

      {/* Error display */}
      {(row.state === "failed" || row.state === "denied") && row.error && (
        <div className="thread-tool-error-code" data-testid="error-code">{row.error}</div>
      )}

      {/* HS-152-05: per-kind result renderer + RAW fold */}
      <ToolResultRenderer row={row} />
    </div>
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
  toolRows,
  threadId,
  onDecide,
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
  /** HS-152-04: tool rows for this message. */
  toolRows?: ToolRow[];
  threadId: string;
  onDecide: (callId: string, decision: "approve" | "deny", opts?: { always?: boolean; answer?: unknown }) => void;
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

      {/* HS-152-04: tool rows */}
      {toolRows && toolRows.length > 0 && (
        <div className="thread-tool-rows">
          {toolRows.map((row) => (
            <ToolRowView
              key={row.callId}
              row={row}
              threadId={threadId}
              onDecide={onDecide}
            />
          ))}
        </div>
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
  const threadToolRows = useThreadStore((s) => s.toolRows[threadId] ?? EMPTY_TOOL_ROWS);
  const liveStatusLine = useThreadStore((s) => s.statusLines[threadId] ?? "");
  const {
    loadThread, applyTurnStarted, applyDelta, applyTurnDone, reconcile,
    getBufferText, applyToolPending, applyToolResult, applyStatusLine,
    decideOptimistic,
  } = useThreadStore.getState();

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
  }, [detail?.messages.length, buffers, threadToolRows]);

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
      // HS-152-04: tool frames
      subscribe("thread_tool_pending", (frame) => {
        const p = frame.data as ThreadToolPendingPayload;
        if (p.thread_id !== threadId) return;
        applyToolPending(p);
        // Scroll the tool row into view when a decision is required
        if (p.decision_required || p.elicitation) {
          requestAnimationFrame(() => {
            const row = bodyRef.current?.querySelector(
              `[data-call-id="${p.call_id}"]`,
            );
            if (row) row.scrollIntoView({ block: "nearest", behavior: "smooth" });
          });
        }
      }),
      subscribe("thread_tool_result", (frame) => {
        const p = frame.data as ThreadToolResultPayload;
        if (p.thread_id !== threadId) return;
        applyToolResult(p);
      }),
      subscribe("thread_status_line", (frame) => {
        const p = frame.data as ThreadStatusLinePayload;
        if (p.thread_id !== threadId) return;
        applyStatusLine(p);
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

  /** HS-152-04: decide a held tool call. */
  const handleDecide = useCallback(
    async (callId: string, decision: "approve" | "deny", opts?: { always?: boolean; answer?: unknown }) => {
      decideOptimistic(threadId, callId, decision);
      await attempt("decide", () =>
        decideToolCall(threadId, callId, decision, opts),
      );
    },
    [threadId, attempt, decideOptimistic],
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
            {(liveStatusLine || detail.thread?.status_line) && (
              <span className="thread-status-line">{liveStatusLine || detail.thread?.status_line}</span>
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
            {detail.messages.filter((m) => m.role !== "tool").map((msg) => {
              // Siblings: server returns { message_id: [position(1-based), total] }.
              const sibData = detail.siblings[msg.id];
              const sibPosition = Array.isArray(sibData) ? Number(sibData[0]) : 1;
              const sibTotal = Array.isArray(sibData) ? Number(sibData[1]) : 1;
              // HS-152-04: collect tool rows for this message
              const msgToolRows = msg.role === "assistant"
                ? Object.values(threadToolRows).filter((r) => r.messageId === msg.id)
                : undefined;
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
                  toolRows={msgToolRows}
                  threadId={threadId}
                  onDecide={handleDecide}
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
