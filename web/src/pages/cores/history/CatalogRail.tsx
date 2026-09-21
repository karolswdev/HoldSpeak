// HS-170-04 — the meetings stream (the board's list face).
// Each row: title at primary, date/duration/words/state tokens, verb at right.
// Token separators: middle dot (U+00B7) between EVERY token, muted.
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  RefusalToken,
  RouteDisclosure,
  RunAttempts,
} from "../../../meetings/RouteDisclosure";
import {
  executedReceipt,
  readLastRefusal,
  readPlannedRoute,
  readRunReceipt,
  routeReady,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import { rowId } from "../../pageSupport";
import { countToken } from "../../../desk/surface";
import {
  durationToken, ledgerDate, wordsToken, needsIntelligence,
  meetingRowState, stateToken,
} from "./helpers";
import type { ReactNode } from "react";

/** HS-201-04 — true when this row would draw a verb that STARTS a summary
 *  run: the verb is a run verb AND a route resolves for it. The rail uses
 *  it to pick the ONE row that may carry the filled primary. */
function rowStartsRun(row: Record<string, unknown>): boolean {
  const verb = meetingRowState(row).verb;
  if (verb !== "Run summary" && verb !== "Retry") return false;
  return routeReady(readPlannedRoute(row));
}

/** The row that may wear the filled primary: the SELECTED row when it can
 *  start a run, else the top-most row that can. Every other row's verb is
 *  the default species (UX-CANON: one filled primary per window). */
function leadRunRowId(
  rows: Record<string, unknown>[],
  selected: Record<string, unknown> | null,
): string | null {
  const selectedId = selected ? String(selected.id) : null;
  if (selectedId) {
    const row = rows.find((item) => String(item.id) === selectedId);
    if (row && rowStartsRun(row)) return selectedId;
  }
  const first = rows.find(rowStartsRun);
  return first ? String(first.id) : null;
}

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
  drainerAbsent,
  refusal,
  isLead,
}: {
  row: Record<string, unknown>;
  isSelected: boolean;
  /** HS-201-04 — the one row of the rail that may wear a filled primary. */
  isLead: boolean;
  onSelect: () => void;
  onRunIntelligence: (id: string, route: PlannedRoute | null) => void;
  runningId: string | null;
  /** The `runtime_queue` frame says no hub drainer will execute the queue. */
  drainerAbsent?: boolean;
  /** HS-201-04 — the hub's 409 on THIS row's last run gesture. */
  refusal?: SummaryRefusal | null;
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
  if (needsYouCount > 0 && (token.label === "SAVED" || token.label === "RAN")) {
    displayLabel = countToken(needsYouCount, "NEEDS YOU", "NEED YOU") ?? "";
    displayTone = "accent";
  } else if (needsYouCount > 0 && token.label !== "OFF") {
    displayLabel = countToken(needsYouCount, "NEEDS YOU", "NEED YOU") ?? displayLabel;
    displayTone = "accent";
  }

  // If the job is running, override the state. HS-200-42: `isRunning` is
  // this client's OPTIMISM about a click, not the server's state — so when
  // the hub has no drainer it is not running and never will be.
  if (isRunning) {
    displayLabel = drainerAbsent ? "NOT DRAINING" : "RUNNING";
    displayTone = drainerAbsent ? "danger" : "warn";
  }
  // HS-200-42 (counsel N1): a job the hub has nobody to execute is not
  // "queued" in any useful sense. Same token and tone the Chair uses.
  if (displayLabel === "QUEUED" && drainerAbsent) {
    displayLabel = "NOT DRAINING";
    displayTone = "danger";
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

  // HS-201-04 — the disclosed route (before the click) and the receipt's
  // destinations (after the run), both from this row's read model.
  const plannedRoute = refusal?.route ?? readPlannedRoute(row);
  const runReceipt = executedReceipt(
    String(row.id ?? ""),
    refusal?.receipt,
    readRunReceipt(row),
  );
  const canRun = routeReady(plannedRoute);

  // Determine verb
  let verb = state.verb;
  let verbVariant = state.verbVariant;
  if (isRunning) {
    verb = null;
    verbVariant = "ghost";
  }
  // UX-CANON A.11: `Run summary` and `Retry` both start a summary
  // run. With no resolvable route there is nothing to run, so the verb is
  // withheld and the disclosure says why.
  if ((verb === "Run summary" || verb === "Retry") && !canRun) {
    verb = null;
  }
  // HS-201-04 (Astra's counsel round 2; one filled primary per window).
  // Two rules compose:
  //   - only the LEAD row (the selected one when it can run, else the
  //     top-most that can) may wear the filled species. Two summary-ready
  //     meetings used to draw two filled `Run summary` verbs.
  //   - and when that row's RECORD is open, the record carries the filled
  //     verb, so the row's own copy steps down too.
  if (verbVariant === "primary" && (!isLead || isSelected)) {
    verbVariant = "ghost";
  }
  // No transcript row: only ghost Open (no Run summary)
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
      {/* HS-202-03 — the clickable body IS the library Button (UX-CANON
          A.1): it was a `div role="button" tabIndex={0}`, the last raw
          control on the Meetings stream. The chrome variant withholds the
          plate so `.meetings-stream-row-body` keeps drawing the row, and
          the explicit Enter/Space handler stays so the keyboard behaviour
          is the one the 201 rigs recorded. */}
      <Button
        variant="chrome"
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
      </Button>
      <div className="meetings-stream-row-verb">
        {/* Article III — after the run: every destination contacted, in
            order. Before the click (and while it is in flight): the route
            the run WILL use.
            HS-201-04: this REPLACES the old in-flight chip, which took the
            POST response's `host` straight to the glass and printed the
            wire word `same_device` at a person (caught by the HS-170 S-3
            rig). One egress chip per row, through the one mapper. */}
        <RunAttempts receipt={runReceipt} testId="row-attempts" />
        {state.verb === "Run summary" || state.verb === "Retry" || isRunning ? (
          <RouteDisclosure route={plannedRoute} testId="row-route" />
        ) : null}
        <RefusalToken
          refusal={refusal}
          durable={readLastRefusal(row)}
          testId="row-refusal"
        />
        {verb ? (
          <Button
            dense
            variant={verbVariant === "primary" ? "primary" : "ghost"}
            onClick={(e: React.MouseEvent) => {
              e.stopPropagation();
              // HS-201-04 (audit defect 2): `Retry` used to fall through to
              // `onSelect` and issue ZERO requests. Both run verbs dispatch.
              if (verb === "Run summary" || verb === "Retry") {
                // The route this row DISCLOSED is the route that travels.
                onRunIntelligence(String(row.id), plannedRoute);
              } else {
                onSelect();
              }
            }}
            data-testid={
              verb === "Run summary"
                ? "run-intelligence-btn"
                : verb === "Retry"
                  ? "retry-intelligence-btn"
                  : undefined
            }
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
  drainerAbsent,
  runRefusal,
  narrowed,
}: {
  meetingRows: Record<string, unknown>[];
  meetings: { loading: boolean; error: string; reload(): Promise<unknown> };
  selected: Record<string, unknown> | null;
  setSelected: (row: Record<string, unknown> | null) => void;
  onRunIntelligence: (id: string, route: PlannedRoute | null) => void;
  runningId: string | null;
  /** The `runtime_queue` frame says no hub drainer will execute the queue. */
  drainerAbsent?: boolean;
  /** HS-201-04 — the hub's 409 on the last run gesture, with its row. */
  runRefusal?: { meetingId: string; refusal: SummaryRefusal } | null;
  /** When true, shown as the narrowed left side in SurfaceSplit. */
  narrowed?: boolean;
}) {
  const leadId = leadRunRowId(meetingRows, selected);
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
              isLead={leadId === String(row.id)}
              runningId={runningId}
              drainerAbsent={drainerAbsent}
              refusal={
                runRefusal && runRefusal.meetingId === String(row.id)
                  ? runRefusal.refusal
                  : null
              }
            />
          ))}
        </div>
      </SurfaceState>
    </div>
  );
}
