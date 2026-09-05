// HS-170-04 — the meetings stream (the board's list face).
// Each row: title at primary, date/duration/words/state tokens, verb at right.
// Token separators: middle dot (U+00B7) between EVERY token, muted.
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceState,
} from "../../../desk/surface/Surface";
import { EgressChip } from "../../../desk/surface/gadgets";
import { rowId } from "../../pageSupport";
import { countToken } from "../../../desk/surface";
import {
  durationToken, ledgerDate, wordsToken, needsIntelligence,
  meetingRowState, stateToken,
} from "./helpers";
import type { ReactNode } from "react";

/** Render a list of tokens joined by middle dots (U+00B7).
 *  Dots are sibling flex children for equal spacing on both sides. */
function TokenLine({ parts }: { parts: ReactNode[] }) {
  const filtered = parts.filter(Boolean);
  const interleaved: ReactNode[] = [];
  filtered.forEach((part, i) => {
    if (i > 0) interleaved.push(
      <span key={`dot-${i}`} className="meetings-stream-dot" aria-hidden="true">{"·"}</span>
    );
    interleaved.push(<span key={`part-${i}`}>{part}</span>);
  });
  return <>{interleaved}</>;
}

/** HS-170-04 — the stream row: title at primary, tokens under, verb right. */
function MeetingStreamRow({
  row,
  isSelected,
  onSelect,
  onRunIntelligence,
  runningId,
  runHost,
}: {
  row: Record<string, unknown>;
  isSelected: boolean;
  onSelect: () => void;
  onRunIntelligence: (id: string) => void;
  runningId: string | null;
  runHost: string | null;
}) {
  const state = meetingRowState(row);
  const words = wordsToken(row.transcriptWords);
  const noTranscript = row.transcriptWords == null;
  const isRunning = runningId === String(row.id);
  const needsYouCount = Number(row.needs_you_count ?? row.needsYouCount ?? 0);

  // The board: NEEDS YOU N (accent) replaces OFF/SAVED for meetings with outcomes
  const token = stateToken(row);
  let displayLabel = state.label;
  let displayTone = state.tone;
  if (needsYouCount > 0 && token.label === "SAVED") {
    displayLabel = countToken(needsYouCount, "NEEDS YOU", "NEED YOU") ?? "";
    displayTone = "accent";
  } else if (needsYouCount > 0 && token.label !== "OFF") {
    displayLabel = countToken(needsYouCount, "NEEDS YOU", "NEED YOU") ?? displayLabel;
    displayTone = "accent";
  }

  // If the job is running, override the state
  if (isRunning) {
    displayLabel = "RUNNING";
    displayTone = "warn";
  }

  // Build token parts: SEP 04 · 30 MIN · 1,204 WORDS · OFF
  const dateStr = ledgerDate(row.started_at ?? row.created_at);
  const dur = durationToken(row.duration_seconds);

  // Assemble all parts for the token line
  const tokenParts: ReactNode[] = [];
  if (dateStr) tokenParts.push(
    <span className="meetings-stream-fact">{dateStr}</span>
  );
  if (dur) tokenParts.push(
    <span className="meetings-stream-fact">{dur}</span>
  );
  if (words) tokenParts.push(
    <span className="meetings-stream-fact">{words}</span>
  );
  // The state token or NO TRANSCRIPT
  if (noTranscript && token.label === "OFF") {
    tokenParts.push(
      <span className="meetings-stream-no-transcript" data-testid="no-transcript-token">
        NO TRANSCRIPT
      </span>
    );
  } else if (displayLabel) {
    tokenParts.push(
      <span
        className="surface-token"
        data-chip
        data-tone={displayTone}
        data-testid="state-token"
      >
        {displayLabel}
      </span>
    );
  }

  // Determine verb
  let verb = state.verb;
  let verbVariant = state.verbVariant;
  if (isRunning) {
    verb = null;
    verbVariant = "ghost";
  }
  // No transcript row: only ghost Open (no Run intelligence)
  if (noTranscript && token.label === "OFF") {
    verb = "Open";
    verbVariant = "ghost";
  }

  // Compact line for narrowed mode: "SEP 04 · OFF"
  const compactParts: string[] = [];
  if (dateStr) compactParts.push(dateStr);
  compactParts.push(displayLabel || "");

  return (
    <div
      className="meetings-stream-row"
      data-selected={isSelected || undefined}
      data-testid={`meeting-row-${String(row.id)}`}
    >
      {/* Clickable body: a div with role/tabindex, not a <button> */}
      <div
        role="button"
        tabIndex={0}
        className="meetings-stream-row-body"
        onClick={onSelect}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(); } }}
      >
        <div className="meetings-stream-row-head">
          <span className="surface-primary meetings-stream-title">
            {String(row.title ?? "Meeting")}
          </span>
          {/* Compact fact line for narrowed mode */}
          <span className="meetings-stream-compact-facts">
            {compactParts.filter(Boolean).join(" · ")}
          </span>
        </div>
        <div className="meetings-stream-tokens">
          <TokenLine parts={tokenParts} />
        </div>
      </div>
      <div className="meetings-stream-row-verb">
        {isRunning && runHost ? (
          <EgressChip label={runHost} />
        ) : null}
        {verb ? (
          <Button
            dense
            variant={verbVariant === "primary" ? "primary" : "ghost"}
            onClick={(e: React.MouseEvent) => {
              e.stopPropagation();
              if (verb === "Run intelligence") {
                onRunIntelligence(String(row.id));
              } else {
                onSelect();
              }
            }}
            data-testid={verb === "Run intelligence" ? "run-intelligence-btn" : undefined}
          >
            {verb}
          </Button>
        ) : null}
      </div>
    </div>
  );
}

export function CatalogRail({
  meetingRows,
  meetings,
  selected,
  setSelected,
  onRunIntelligence,
  runningId,
  runHost,
  narrowed,
}: {
  meetingRows: Record<string, unknown>[];
  meetings: { loading: boolean; error: string; reload(): Promise<unknown> };
  selected: Record<string, unknown> | null;
  setSelected: (row: Record<string, unknown> | null) => void;
  onRunIntelligence: (id: string) => void;
  runningId: string | null;
  runHost: string | null;
  /** When true, shown as the narrowed left side in SurfaceSplit. */
  narrowed?: boolean;
}) {
  return (
    <div className="meetings-stream" data-narrowed={narrowed || undefined}>
      <SurfaceState
        loading={meetings.loading}
        error={meetings.error}
        empty={!meetingRows.length}
        emptyLabel="No meetings yet"
        onRetry={() => void meetings.reload()}
      >
        <div className="meetings-stream-rows">
          {meetingRows.map((row, index) => (
            <MeetingStreamRow
              key={rowId(row, index)}
              row={row}
              isSelected={Boolean(
                selected && String(selected.id) === String(row.id),
              )}
              onSelect={() => {
                const isOpen = Boolean(
                  selected && String(selected.id) === String(row.id),
                );
                setSelected(isOpen ? null : row);
              }}
              onRunIntelligence={onRunIntelligence}
              runningId={runningId}
              runHost={runHost}
            />
          ))}
        </div>
      </SurfaceState>
    </div>
  );
}
