import { countLabel } from "../surface";
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
import { intelBadge } from "../chair/intelBadge";
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
  abortThread,
  patchThread,
  keepMessage,
  branchThread,
  regenerateThread,
  createThread,
  decideToolCall,
  addAnnotation,
  deleteAnnotation,
  type ThreadMessage,
  type ThreadDeltaPayload,
  type ThreadTurnStartedPayload,
  type ThreadTurnDonePayload,
  type ThreadToolPendingPayload,
  type ThreadToolResultPayload,
  type ThreadStatusLinePayload,
  type ThreadGuardrailPayload,
  type DraftAnnotation,
  type ToolRow,
  type ToolRowState,
  type GuardrailRow,
  type ThreadCallStatePayload,
} from "../threads";
import { useDesk } from "../store";
import { ThreadComposer, InlineEditor } from "../components/ThreadComposer";
import { MicButton } from "../components/MicButton";
import { Button } from "../../components/signal/Signal";
import { ModeTabs } from "../components/ModeTabs";
import { InterviewPanel } from "../components/InterviewPanel";
import { CallChip } from "../components/CallChip";
import { SpeakerGlyph } from "../components/SpeakerGlyph";
import {
  feedDelta as autoSpeakFeedDelta,
  flushTurn as autoSpeakFlushTurn,
  setCallActive as autoSpeakSetCallActive,
  bargeIn as autoSpeakBargeIn,
  wasAutoSpoken,
} from "../autoSpeak";
import type { PulloutContentProps } from "./types";
import "./thread-pullout.css";

// HS-152-04: stable empty refs for zustand selectors (avoid infinite re-render).
const EMPTY_TOOL_ROWS: Record<string, ToolRow> = {};
const EMPTY_GUARDRAIL_ROWS: Record<string, GuardrailRow> = {};
const EMPTY_DRAFT_ANNOTATIONS: DraftAnnotation[] = [];

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
              // UX-CANON: needs redesign (HS-170-04)
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
                {/* UX-CANON: needs redesign (HS-170-04) */}
                <input
                  type="checkbox"
                  checked={Boolean(values[key])}
                  onChange={(e) => handleChange(key, e.target.checked)}
                />
                <span className="thread-elicitation-label">{label}{isReq ? " *" : ""}</span>
              </label>
            ) : type === "number" || type === "integer" ? (
              // UX-CANON: needs redesign (HS-170-04)
              <input
                type="number"
                className="thread-elicitation-input"
                value={String(values[key] ?? "")}
                onChange={(e) => handleChange(key, Number(e.target.value))}
              />
            ) : (
              // UX-CANON: needs redesign (HS-170-04)
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
        <Button
          variant="primary"
          dense
          onClick={() => onSubmit(values)}
          data-testid="elicitation-submit"
        >
          Submit
        </Button>
        <Button
          variant="ghost"
          dense
          onClick={onDecline}
          data-testid="elicitation-decline"
        >
          Decline
        </Button>
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

// ── Guardrail row (HS-153-03) ─────────────────────────────────────
function GuardrailRowView({ row }: { row: GuardrailRow }) {
  const hasViolations = row.violations.length > 0;
  const hasWarnings = row.warnings.length > 0;
  const [rawOpen, setRawOpen] = useState(false);

  if (!hasViolations && !hasWarnings) return null;

  return (
    <div
      className={`thread-guardrail-row ${hasViolations ? "has-violations" : "has-warnings"}`}
      data-testid="guardrail-row"
    >
      <div className="thread-guardrail-head">
        <span className="thread-guardrail-glyph">{hasViolations ? "X" : "!"}</span>
        <span className="thread-guardrail-label">
          {hasViolations ? "Guardrail violation" : "Guardrail warning"}
        </span>
      </div>
      {row.violations.map((v, i) => (
        <div key={`v-${i}`} className="thread-guardrail-violation" data-testid="guardrail-violation">
          {v}
        </div>
      ))}
      {row.warnings.map((w, i) => (
        <div key={`w-${i}`} className="thread-guardrail-warning" data-testid="guardrail-warning">
          {w}
        </div>
      ))}
      {row.raw && (
        <details
          className="thread-guardrail-raw"
          open={rawOpen}
          onToggle={(e) => setRawOpen((e.target as HTMLDetailsElement).open)}
        >
          <summary>RAW</summary>
          <pre>{JSON.stringify(row.raw, null, 2)}</pre>
        </details>
      )}
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

      {/* Decision box: Allow once / Allow always / Deny
           HS-153-03: when defaultDecision === "deny", Deny gets primary styling
           and autoFocus; otherwise Allow once is primary. */}
      {row.state === "awaiting_decision" && (
        <div className="thread-tool-decision-box" data-testid="decision-box" data-default-decision={row.defaultDecision || "allow"}>
          <div className="thread-tool-decision-actions">
            <Button
              variant={row.defaultDecision === "deny" ? "ghost" : "primary"}
              dense
              onClick={() => onDecide(row.callId, "approve")}
              data-testid="allow-once"
              autoFocus={row.defaultDecision !== "deny"}
            >
              Allow once
            </Button>
            <Button
              variant="ghost"
              dense
              onClick={() => onDecide(row.callId, "approve", { always: true })}
              data-testid="allow-always"
            >
              Allow always
            </Button>
            <Button
              variant={row.defaultDecision === "deny" ? "primary" : "ghost"}
              dense
              onClick={() => onDecide(row.callId, "deny")}
              data-testid="deny"
              autoFocus={row.defaultDecision === "deny"}
            >
              Deny
            </Button>
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

// ── Annotation popover (HS-153-04) ──────────────────────────────────

function AnnotationPopover({
  anchorRect,
  quoteText,
  onSave,
  onCancel,
}: {
  anchorRect: { top: number; left: number; width: number; bottom: number };
  quoteText: string;
  onSave: (comment: string) => void;
  onCancel: () => void;
}) {
  const [comment, setComment] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onCancel();
      }
    };
    document.addEventListener("keydown", handler, true);
    return () => document.removeEventListener("keydown", handler, true);
  }, [onCancel]);

  const quoteHead = quoteText.length > 40 ? quoteText.slice(0, 40) + "..." : quoteText;

  return (
    <div
      ref={popoverRef}
      className="thread-annotation-popover"
      data-testid="annotation-popover"
      style={{
        position: "absolute",
        top: anchorRect.bottom + 4,
        left: Math.max(0, anchorRect.left),
        zIndex: 100,
      }}
    >
      <div className="thread-annotation-quote-head" title={quoteText}>
        {quoteHead}
      </div>
      <div className="thread-annotation-input-row">
        {/* UX-CANON: needs redesign (HS-170-04) */}
        <input
          ref={inputRef}
          type="text"
          className="thread-annotation-comment-input"
          data-testid="annotation-comment-input"
          placeholder="Comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && comment.trim()) {
              e.preventDefault();
              onSave(comment.trim());
            }
          }}
        />
        <MicButton
          onText={(text) => setComment((prev) => (prev ? prev + " " + text : text))}
          label="Dictate comment"
        />
      </div>
      <div className="thread-annotation-actions">
        <Button
          variant="primary"
          dense
          data-testid="annotation-save"
          disabled={!comment.trim()}
          onClick={() => onSave(comment.trim())}
        >
          Save
        </Button>
        <Button
          variant="ghost"
          dense
          data-testid="annotation-cancel"
          onClick={onCancel}
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}

// ── Annotation chips (HS-153-04) ────────────────────────────────────

function AnnotationChips({
  annotations,
  onRemove,
}: {
  annotations: DraftAnnotation[];
  onRemove: (partId: string) => void;
}) {
  if (annotations.length === 0) return null;
  return (
    <div className="thread-annotation-chips" data-testid="annotation-chips">
      {annotations.map((a) => {
        const quote = a.meta_json?.quote ?? "";
        const head = quote.length > 30 ? quote.slice(0, 30) + "..." : quote;
        return (
          <span key={a.id} className="thread-annotation-chip" data-testid="annotation-chip">
            <span className="thread-annotation-chip-text">{head}</span>
            <Button
              variant="ghost"
              dense
              className="thread-annotation-chip-remove"
              data-testid="annotation-chip-remove"
              aria-label="Remove annotation"
              onClick={() => onRemove(a.id)}
            >
              x
            </Button>
          </span>
        );
      })}
    </div>
  );
}

// ── HS-153-05: compaction cut marker ────────────────────────────────
function CompactionCutMarker({ msg }: { msg: ThreadMessage }) {
  const stats = msg.statsJson as { compaction: boolean; cut_at: string; count: number } | null;
  const summaryText = msg.parts.filter((p) => p.kind === "text").map((p) => p.text).join("");
  const count = stats?.count ?? 0;

  return (
    <div className="thread-compact-cut" data-testid="compact-cut-marker" data-message-id={msg.id}>
      <div className="thread-compact-cut-label">
        compacted · {count} message{count !== 1 ? "s" : ""}
      </div>
      {summaryText && (
        <details className="thread-raw-fold" data-testid="raw-fold">
          <summary className="thread-raw-toggle">{"RAW ▸"}</summary>
          <pre className="thread-raw-content">{summaryText}</pre>
        </details>
      )}
    </div>
  );
}

function CompactFailedRow({ msg }: { msg: ThreadMessage }) {
  const text = msg.parts.filter((p) => p.kind === "text").map((p) => p.text).join("");
  return (
    <div className="thread-compact-failed" data-testid="compact-failed-row" data-message-id={msg.id}>
      <span className="thread-compact-failed-label">compact failed</span>
      {text && <span className="thread-compact-failed-text">{text}</span>}
    </div>
  );
}

// ── HS-153-05: message list with compaction fold ────────────────────
function ThreadMessageList({
  messages,
  siblings,
  threadToolRows,
  guardrailRowsForThread,
  getBufferText,
  threadId,
  loadThread,
  handleRetry,
  handleKeep,
  handleBranch,
  handleDecide,
}: {
  messages: ThreadMessage[];
  siblings: Record<string, string[]>;
  threadToolRows: Record<string, ToolRow>;
  guardrailRowsForThread: Record<string, GuardrailRow>;
  getBufferText: (id: string) => string;
  threadId: string;
  loadThread: (id: string) => Promise<void>;
  handleRetry: (messageId: string) => void;
  handleKeep: (messageId: string, as: "note" | "artifact") => void;
  handleBranch: (messageId: string, text: string) => void;
  handleDecide: (callId: string, decision: "approve" | "deny", opts?: { always?: boolean; answer?: unknown }) => void;
}) {
  const [earlierExpanded, setEarlierExpanded] = useState(false);

  const filtered = messages.filter((m) => m.role !== "tool");

  // Find the latest compaction cut index.
  let cutIndex = -1;
  for (let i = filtered.length - 1; i >= 0; i--) {
    if (filtered[i].role === "system" && (filtered[i].statsJson as Record<string, unknown> | null)?.compaction) {
      cutIndex = i;
      break;
    }
  }

  const beforeCut = cutIndex > 0 ? filtered.slice(0, cutIndex) : [];
  const fromCut = cutIndex >= 0 ? filtered.slice(cutIndex) : filtered;

  function renderMsg(msg: ThreadMessage) {
    // Compaction cut marker row.
    if (msg.role === "system" && (msg.statsJson as Record<string, unknown> | null)?.compaction) {
      return <CompactionCutMarker key={msg.id} msg={msg} />;
    }
    // Compact-failed warning row.
    if (msg.role === "system" && (msg.statsJson as Record<string, unknown> | null)?.compact_failed) {
      return <CompactFailedRow key={msg.id} msg={msg} />;
    }

    const sibData = siblings[msg.id];
    const sibPosition = Array.isArray(sibData) ? Number(sibData[0]) : 1;
    const sibTotal = Array.isArray(sibData) ? Number(sibData[1]) : 1;
    const msgToolRows = msg.role === "assistant"
      ? Object.values(threadToolRows).filter((r) => r.messageId === msg.id)
      : undefined;
    const msgGuardrailRow = msg.role === "assistant"
      ? guardrailRowsForThread[msg.id]
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
        guardrailRow={msgGuardrailRow}
      />
    );
  }

  return (
    <div className="thread-messages">
      {beforeCut.length > 0 && (
        <div className="thread-earlier-fold" data-testid="earlier-messages-fold">
          <Button
            variant="ghost"
            dense
            className="thread-earlier-toggle"
            onClick={() => setEarlierExpanded(!earlierExpanded)}
          >
            {earlierExpanded ? "Hide" : `${beforeCut.length} earlier message${beforeCut.length !== 1 ? "s" : ""}`}
          </Button>
          {earlierExpanded && (
            <div className="thread-earlier-messages">
              {beforeCut.map(renderMsg)}
            </div>
          )}
        </div>
      )}
      {fromCut.map(renderMsg)}
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
  guardrailRow,
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
  /** HS-153-03: guardrail evaluation row for this message. */
  guardrailRow?: GuardrailRow;
}) {
  const crashed = isCrashed(msg);
  const hasError = msg.errorJson !== null && !msg.streaming;
  const isStreaming = msg.streaming && !crashed;
  const isDone = !msg.streaming && !hasError && !crashed;

  // Assemble the display text: from buffer if streaming, from parts if done.
  const savedText = msg.parts.filter((p) => p.kind === "text").map((p) => p.text).join("");
  const displayText = isStreaming && bufferText.startsWith(savedText) ? bufferText : savedText;
  const reasoningText = msg.parts
    .filter((p) => p.kind === "reasoning")
    .map((p) => p.text)
    .join("");

  const [showRaw, setShowRaw] = useState(false);
  const [editing, setEditing] = useState(false);
  const receiptShort = msg.receiptId && msg.receiptId.length > 4
    ? msg.receiptId.slice(-4)
    : msg.receiptId || null;
  const routineTools = toolRows?.filter((row) =>
    row.state === "pending" || row.state === "running" || row.state === "receipted",
  ) ?? [];
  const attentionTools = toolRows?.filter((row) =>
    row.state !== "pending" && row.state !== "running" && row.state !== "receipted",
  ) ?? [];
  const toolsWorking = routineTools.some((row) => row.state !== "receipted");

  if (msg.role === "user") {
    const userText = msg.parts.map((p) => p.text).join("") || "";
    return (
      <div className="thread-row thread-row-user" data-message-id={msg.id}>
        <div className="thread-row-label">YOU{msg.pending && <span> · Sending…</span>}</div>
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
            onClick={msg.pending ? undefined : () => setEditing(true)}
            title={msg.pending ? undefined : "Click to edit and resend"}
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
          <span className="thread-row-receipt">
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
          <Button
            variant="primary"
            dense
            onClick={() => onRetry(msg.id)}
          >
            Retry
          </Button>
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

      {/* HS-153-03: guardrail row (before tool rows) */}
      {guardrailRow && <GuardrailRowView row={guardrailRow} />}

      {/* Routine activity stays folded throughout the turn. Native details
          preserves the reader's choice to inspect it as results arrive. */}
      {routineTools.length > 0 && (
        <details className="thread-raw-fold" data-testid="tool-activity">
          <summary className="thread-raw-toggle">
            {countLabel("Actions ·", routineTools.length)}{toolsWorking && " · Working…"}
          </summary>
          <div className="thread-tool-rows">
            {routineTools.map((row) => <ToolRowView key={row.callId} row={row} threadId={threadId} onDecide={onDecide} />)}
          </div>
        </details>
      )}
      {attentionTools.length > 0 && (
        <div className="thread-tool-rows">
          {attentionTools.map((row) => <ToolRowView key={row.callId} row={row} threadId={threadId} onDecide={onDecide} />)}
        </div>
      )}

      <div className="thread-row-actions">
        {/* HS-154-04: speaker glyph — replay any finished assistant text */}
        {isDone && displayText && (
          <SpeakerGlyph messageId={msg.id} text={displayText} />
        )}
        <SiblingPicker
          position={siblingPosition}
          total={siblingTotal}
          onPrev={onSiblingPrev}
          onNext={onSiblingNext}
        />
        {isDone && !editing && (
          <>
            <Button
              variant="ghost"
              dense
              onClick={() => onKeep(msg.id, "note")}
            >
              Keep as note
            </Button>
            <Button
              variant="ghost"
              dense
              onClick={() => onKeep(msg.id, "artifact")}
            >
              Keep as artifact
            </Button>
            <Button
              variant="ghost"
              dense
              onClick={() => setEditing(true)}
            >
              Fork here
            </Button>
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
    decideOptimistic, setMode, applyGuardrail,
  } = useThreadStore.getState();
  const guardrailRowsForThread = useThreadStore((s) => s.guardrailRows[threadId] ?? EMPTY_GUARDRAIL_ROWS);

  const { attempt, receipt } = useWriteReceipt();
  const { subscribe, state: busState } = useRuntimeBus();

  // Title editing
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(initialTitle);
  const titleRef = useRef<HTMLInputElement>(null);

  // HS-151-06: track turn_done for focus restore
  const [restoreFocus, setRestoreFocus] = useState(false);

  const bodyRef = useRef<HTMLDivElement>(null);
  const followTail = useRef(true);

  // Load thread on mount
  useEffect(() => {
    void loadThread(threadId);
  }, [threadId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (bodyRef.current && followTail.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [detail?.messages, buffers, threadToolRows]);

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
        // HS-154-04: feed text deltas to auto-speak (not reasoning).
        // S1: guard against reconnect-replayed deltas for already-spoken turns.
        if (p.kind === "text" && !wasAutoSpoken(p.message_id)) {
          autoSpeakFeedDelta(p.message_id, p.text);
        }
      }),
      subscribe("thread_turn_done", (frame) => {
        const p = frame.data as ThreadTurnDonePayload;
        if (p.thread_id !== threadId) return;
        applyTurnDone(p);
        // HS-154-04: flush auto-speak tail at turn end.
        autoSpeakFlushTurn(p.message_id);
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
      // HS-153-03: guardrail evaluation frame
      subscribe("thread_guardrail", (frame) => {
        const p = frame.data as ThreadGuardrailPayload;
        if (p.thread_id !== threadId) return;
        applyGuardrail(p);
      }),
      // HS-153-05: compaction frame — refresh thread to get the cut row
      subscribe("thread_compacted", (frame) => {
        const p = frame.data as { thread_id: string };
        if (p.thread_id !== threadId) return;
        void loadThread(threadId);
      }),
      // HS-154-03: call state frame — reload thread to sync call_mode
      subscribe("thread_call_state", (frame) => {
        const p = frame.data as ThreadCallStatePayload;
        if (p.thread_id !== threadId) return;
        void loadThread(threadId);
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
    async (text: string, refs: Array<{ ref_kind: string; ref_id: string }>) => {
      followTail.current = true;
      // HS-153-04: clear draft annotations optimistically on send (they are promoted server-side).
      useThreadStore.setState((s) => ({
        draftAnnotations: { ...s.draftAnnotations, [threadId]: [] },
      }));
      const result = await attempt("send turn", () =>
        useThreadStore.getState().submitTurn(threadId, { text, refs: refs.length > 0 ? refs : undefined }),
        { retry: false },
      );
      return result.ok;
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
  const hasPendingSend = detail?.messages.some((m) => m.pending) ?? false;

  // Recover missed start/delta/done frames while a local turn is active.
  // Read-only reconciliation never resubmits the owner's message.
  useEffect(() => {
    if (!isStreaming && !hasPendingSend) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      if (!useThreadStore.getState().loading[threadId]) await loadThread(threadId);
      if (!stopped) timer = setTimeout(refresh, 1500);
    };
    timer = setTimeout(refresh, 1500);
    return () => { stopped = true; clearTimeout(timer); };
  }, [threadId, isStreaming, hasPendingSend, loadThread]);

  // HS-154-04: sync auto-speak active state with call_mode.
  const callMode = detail?.thread?.call_mode ?? 0;
  useEffect(() => {
    autoSpeakSetCallActive(callMode === 1);
  }, [callMode]);

  // HS-153-04: annotation popover state
  const draftAnnotations = useThreadStore((s) => s.draftAnnotations[threadId] ?? EMPTY_DRAFT_ANNOTATIONS);
  const [annotationPopover, setAnnotationPopover] = useState<{
    rect: { top: number; left: number; width: number; bottom: number };
    quote: string;
    messageId: string;
  } | null>(null);
  // Keep a ref to the setter so checkSelection never captures a stale one.
  const setPopoverRef = useRef(setAnnotationPopover);
  setPopoverRef.current = setAnnotationPopover;

  // Selection detection: show popover on text selection in assistant rows
  const checkSelection = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.toString().trim()) {
      return;
    }
    // Guard: don't open while focus is inside an input/textarea/contenteditable
    const active = document.activeElement;
    if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || (active as HTMLElement).isContentEditable)) {
      return;
    }
    // Check if the selection is inside an assistant text part
    const range = sel.getRangeAt(0);
    const container = range.commonAncestorContainer;
    const el = container instanceof Element ? container : container.parentElement;
    if (!el) return;
    const row = el.closest?.("[data-message-id]");
    if (!row) return;
    const msgId = row.getAttribute("data-message-id");
    if (!msgId) return;
    // Only assistant rows with class thread-row-assistant
    if (!row.classList.contains("thread-row-assistant")) return;
    // Only text parts (the row body); check if the element or any ancestor
    // up to the row is the row body itself.
    const rowBody = row.querySelector(".thread-row-body");
    if (!rowBody) return;
    // Walk from el upward to check containment (handles shadow DOM edge cases).
    let inBody = false;
    let walk: Element | null = el;
    while (walk && walk !== row) {
      if (walk === rowBody) { inBody = true; break; }
      walk = walk.parentElement;
    }
    if (!inBody) return;

    const quote = sel.toString().trim();
    if (!quote) return;
    const rect = range.getBoundingClientRect();
    const parentRect = bodyRef.current?.getBoundingClientRect() ?? { top: 0, left: 0 };
    setPopoverRef.current({
      rect: {
        top: rect.top - parentRect.top + (bodyRef.current?.scrollTop ?? 0),
        left: rect.left - parentRect.left,
        width: rect.width,
        bottom: rect.bottom - parentRect.top + (bodyRef.current?.scrollTop ?? 0),
      },
      quote,
      messageId: msgId,
    });
  }, []);

  // mouseup on the body opens the popover when a selection exists in
  // assistant text.  Attached as a native DOM listener (not React synthetic)
    // Open the popover on selectionchange when a non-empty selection
  // lies inside an assistant text part. selectionchange fires AFTER
  // the browser finalizes the selection (unlike mouseup which fires
  // before for multi-click gestures), so it works reliably for both
  // single-drag and triple-click.
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    const handler = () => {
      // Debounce: selectionchange fires many times during a drag.
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        timer = null;
        checkSelection();
      }, 80);
    };
    document.addEventListener("selectionchange", handler);
    return () => {
      document.removeEventListener("selectionchange", handler);
      if (timer) clearTimeout(timer);
    };
  }, [checkSelection]);

  // Callback ref: sets bodyRef.current when the body div mounts.
  const bodyCallbackRef = useCallback((node: HTMLDivElement | null) => {
    bodyRef.current = node;
  }, []);

  // Dismiss popover when clicking outside it (not on selectionchange,
  // because clicking the comment input collapses the text selection).
  useEffect(() => {
    if (!annotationPopover) return;
    const onMouseDown = (e: MouseEvent) => {
      const popoverEl = bodyRef.current?.querySelector("[data-testid='annotation-popover']");
      if (popoverEl && popoverEl.contains(e.target as Node)) return;
      // Clicked outside the popover -- dismiss.
      setAnnotationPopover(null);
    };
    // Use capture to fire before the click can open a new popover.
    document.addEventListener("mousedown", onMouseDown, true);
    return () => document.removeEventListener("mousedown", onMouseDown, true);
  }, [annotationPopover]);

  // `a` key opens the annotation popover when text is selected (keyboard route)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) return;
      if (e.key === "a" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const sel = window.getSelection();
        if (sel && !sel.isCollapsed && sel.toString().trim()) {
          e.preventDefault();
          checkSelection();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [checkSelection]);

  const handleAnnotationSave = useCallback(
    async (comment: string) => {
      if (!annotationPopover) return;
      try {
        const result = await addAnnotation(threadId, {
          message_id: annotationPopover.messageId,
          quote: annotationPopover.quote,
          comment,
        });
        // Optimistic add to store
        useThreadStore.setState((s) => ({
          draftAnnotations: {
            ...s.draftAnnotations,
            [threadId]: [...(s.draftAnnotations[threadId] ?? []), result],
          },
        }));
      } catch {
        // Rollback: reload
        void loadThread(threadId);
      }
      setAnnotationPopover(null);
      window.getSelection()?.removeAllRanges();
    },
    [annotationPopover, threadId, loadThread],
  );

  const handleAnnotationRemove = useCallback(
    async (partId: string) => {
      // Optimistic remove
      useThreadStore.setState((s) => ({
        draftAnnotations: {
          ...s.draftAnnotations,
          [threadId]: (s.draftAnnotations[threadId] ?? []).filter((a) => a.id !== partId),
        },
      }));
      try {
        await deleteAnnotation(threadId, partId);
      } catch {
        // Rollback: reload
        void loadThread(threadId);
      }
    },
    [threadId, loadThread],
  );

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
      <div className="desk-pullout-body desk-surface-body thread-pullout-body" ref={bodyCallbackRef}
        onScroll={(event) => {
          const body = event.currentTarget;
          followTail.current = body.scrollHeight - body.scrollTop - body.clientHeight < 40;
        }}>
        {/* Head: title, egress, status, token meter */}
        <div className="thread-head">
          {editingTitle ? (
            // UX-CANON: needs redesign (HS-170-04)
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
            {detail.thread?.mode && (
              <span
                className="thread-mode-badge"
                data-testid="mode-badge"
                style={{ borderColor: detail.thread.mode.avatar }}
              >
                <span
                  className="thread-mode-dot"
                  style={{ backgroundColor: detail.thread.mode.avatar }}
                />
                {detail.thread.mode.name}
              </span>
            )}
            <CallChip
              threadId={threadId}
              callMode={detail.thread?.call_mode ?? 0}
              isStreaming={isStreaming}
              onReload={() => void loadThread(threadId)}
            />
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
          <ThreadMessageList
            messages={detail.messages}
            siblings={detail.siblings}
            threadToolRows={threadToolRows}
            guardrailRowsForThread={guardrailRowsForThread}
            getBufferText={getBufferText}
            threadId={threadId}
            loadThread={loadThread}
            handleRetry={handleRetry}
            handleKeep={handleKeep}
            handleBranch={handleBranch}
            handleDecide={handleDecide}
          />
        )}
        {/* HS-153-04: annotation popover anchored to selection */}
        {annotationPopover && (
          <AnnotationPopover
            anchorRect={annotationPopover.rect}
            quoteText={annotationPopover.quote}
            onSave={(comment) => void handleAnnotationSave(comment)}
            onCancel={() => {
              setAnnotationPopover(null);
              window.getSelection()?.removeAllRanges();
            }}
          />
        )}
      </div>

      {/* The foot is a direct flex child of the window shell (not
          SurfaceFooter, which is a 36px bar). The composer needs its
          full height to render the textarea + mic + Send/Stop. */}
      <div className="thread-foot">
        {detail.thread.interview && <InterviewPanel
          key={threadId}
          state={detail.thread.interview}
          disabled={isStreaming}
          reload={() => loadThread(threadId)}
          onTry={(text) => handleSend(text, [])}
        />}
        <ModeTabs
          activeMode={detail.thread?.mode ?? null}
          onSelect={(recipeId) => void setMode(threadId, recipeId)}
          disabled={isStreaming}
        />
        {receipt}
        {/* HS-153-04: annotation chips above the composer */}
        <AnnotationChips
          annotations={draftAnnotations}
          onRemove={handleAnnotationRemove}
        />
        {detail.thread.interview?.section !== "people" && <ThreadComposer
          threadId={threadId}
          onSend={handleSend}
          onStop={handleStop}
          onKeep={handleKeep}
          onFork={(messageId) => {
            void handleBranch(messageId, "");
          }}
          onNewThread={handleNewThread}
          onModeSelect={(recipeId) => void setMode(threadId, recipeId)}
          onToggleGuardrail={(guardrailId, enable) => {
            // HS-153-03: toggle via PATCH /api/threads/:id/guardrail
            // S2: pass enable boolean so /guardrail off works.
            void patchThread(threadId, { toggle_guardrail: guardrailId, toggle_guardrail_enable: enable });
          }}
          currentMode={detail.thread?.mode ?? null}
          streaming={isStreaming}
          lastAssistantId={lastAssistant?.id ?? null}
          restoreFocus={restoreFocus}
        />}
      </div>
    </>
  );
}
