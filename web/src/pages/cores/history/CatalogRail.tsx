// HS-170-04 — the meetings stream (the board's list face).
// Window grammar (2026-10-24): the stream is a native list view (the dense
// ObjectList: Name · When · Length · Summary, a state as a dot and a word).
// A press selects the row; Enter or a double press opens the meeting. The
// selected row's verbs (Run summary, Retry, Transcribe), its route and its
// receipts sit at the status bar's right (`MeetingSelectionVerbs`).
import { speechWasMissing } from "../../../desk/firstrun/speechTruth";
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceState,
} from "../../../desk/surface/Surface";
import { ObjectList, type ObjectListRow, type ObjectListSort } from "../../../desk/surface/objects/ObjectList";
import type { ObjectTone } from "../../../desk/surface/objects/kinds";
import {
  RefusalToken,
  RouteDisclosure,
  RunAttempts,
  routeTitle,
} from "../../../meetings/RouteDisclosure";
import {
  executedReceipt,
  readLastRefusal,
  readPlannedRoute,
  readRunReceipt,
  routeOff,
  routeReady,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import { countToken } from "../../../desk/surface";
import {
  durationToken, ledgerDate, wordsToken, unclearLampLabel,
  meetingRowState, stateToken,
} from "./helpers";
import { AudioOnlyVerb } from "./TranscribeVerb";

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
export function leadRunRowId(
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

/** PHILO-13-04 A3-W — the process states a NEEDS YOU count never covers:
 *  capture, failure, and an active summary run. */
const PROCESS_LEADS = new Set([
  "REC", "INTERRUPTED", "CAPTURE FAILED", "RECOVERABLE",
  "FAILED", "IMPORT FAILED", "RUNNING", "QUEUED",
]);

/** PHILO-17 ALIVE: a state pill speaks in sentence case (`Summary
 *  stored`, `2 to review`); the rail's labels are written in caps. */
export function pillWord(label: string): string {
  const lower = label.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** The catalog's words in sentence case (`OCT 24` → `Oct 24`, `30 MIN` →
 *  `30 min`): a list view's cells are quiet sans, never caps. */
function quiet(token: string): string {
  return token.replace(/\b([A-Z])([A-Z]+)\b/g, (_, first: string, rest: string) => first + rest.toLowerCase())
    .replace(/\b(MIN|HR|S|WORDS)\b/gi, (word) => word.toLowerCase());
}

type MeetingRowView = {
  label: string;
  tone: ObjectTone;
  /** The audio-only meeting with no transcript (no summary to run). */
  noTranscript: boolean;
  verb: string | null;
  plannedRoute: PlannedRoute | null;
  runReceipt: ReturnType<typeof executedReceipt>;
  isRunning: boolean;
  showRoute: boolean;
};

function toneOf(tone: string | undefined): ObjectTone {
  switch (tone) {
    case "danger":
      return "fail";
    case "warn":
      return "warn";
    case "accent":
      return "ask";
    case "success":
    case "ok":
      return "ok";
    default:
      return "info";
  }
}

/** HS-170-04 — what one meeting row says and offers: its summary state
 *  (word + tone), and the verb its selection puts in the status bar. */
export function meetingRowView(
  row: Record<string, unknown>,
  { runningId, drainerAbsent, refusal }: {
    runningId: string | null;
    drainerAbsent?: boolean;
    refusal?: SummaryRefusal | null;
  },
): MeetingRowView {
  const state = meetingRowState(row);
  const noTranscript = row.transcriptWords == null;
  const isRunning = runningId === String(row.id);
  const needsYouCount = Number(row.needs_you_count ?? row.needsYouCount ?? 0);
  // PHILO-13-04 A3-W: the process state leads, so a failure is never
  // hidden. Order: capture states, FAILED (with Retry), RUNNING / QUEUED,
  // then TO REVIEW, then SUMMARY STORED, then the rest.
  const token = stateToken(row);
  let displayLabel = state.label;
  let displayTone: string | undefined = state.tone;
  // PHILO-15 10 (B14): `OFF` only when summaries ARE off.
  if (displayLabel === "OFF" && !routeOff(readPlannedRoute(row))) {
    displayLabel = "NOT RUN";
  }
  if (needsYouCount > 0 && !PROCESS_LEADS.has(token.label)) {
    displayLabel = countToken(needsYouCount, "TO REVIEW", "TO REVIEW") ?? displayLabel;
    displayTone = "accent";
  }
  // HS-200-42: `isRunning` is this client's optimism about a click; with no
  // drainer the hub will never run it.
  if (isRunning) {
    displayLabel = drainerAbsent ? "NOT DRAINING" : "RUNNING";
    displayTone = drainerAbsent ? "danger" : "warn";
  }
  if (displayLabel === "QUEUED" && drainerAbsent) {
    displayLabel = "NOT DRAINING";
    displayTone = "danger";
  }
  const plannedRoute = refusal?.route ?? readPlannedRoute(row);
  const runReceipt = executedReceipt(String(row.id ?? ""), refusal?.receipt, readRunReceipt(row));
  let verb = state.verb;
  if (isRunning) verb = null;
  // UX-CANON A.11: with no resolvable route there is nothing to run.
  if ((verb === "Run summary" || verb === "Retry") && !routeReady(plannedRoute)) verb = null;
  const audioOnly = noTranscript && token.label === "OFF";
  if (audioOnly) verb = "Open";
  const label = audioOnly
    ? speechWasMissing(row) ? "No transcript · Speech not set up" : "No transcript"
    : pillWord(displayLabel);
  return {
    label,
    tone: audioOnly ? "warn" : toneOf(displayTone),
    noTranscript: audioOnly,
    verb,
    plannedRoute,
    runReceipt,
    isRunning,
    showRoute: state.verb === "Run summary" || state.verb === "Retry" || isRunning,
  };
}

/** The selected meeting's verbs, at the status bar's right: its run verb
 *  (Run summary / Retry, or Transcribe for an audio-only meeting), the
 *  route that run will use (egress where egress happens, Article III), the
 *  hub's refusal and the run's attempts. Open is the list's own Enter. */
export function MeetingSelectionVerbs({
  row,
  primary,
  onRunIntelligence,
  runningId,
  drainerAbsent,
  refusal,
  onTranscribe,
  saidOnFace,
}: {
  row: Record<string, unknown>;
  /** The run verb wears the window's one primary. */
  primary: boolean;
  onRunIntelligence: (id: string, route: PlannedRoute | null) => void;
  runningId: string | null;
  drainerAbsent?: boolean;
  refusal?: SummaryRefusal | null;
  onTranscribe?: (id: string) => Promise<unknown>;
  saidOnFace?: string | null;
}) {
  const view = meetingRowView(row, { runningId, drainerAbsent, refusal });
  const runs = view.verb === "Run summary" || view.verb === "Retry";
  const runButton = runs ? (
    <Button
      dense
      variant={primary ? "primary" : "secondary"}
      title={view.showRoute ? routeTitle(view.plannedRoute) : undefined}
      onClick={() => onRunIntelligence(String(row.id), view.plannedRoute)}
      data-testid={view.verb === "Run summary" ? "run-intelligence-btn" : "retry-intelligence-btn"}
    >
      {view.verb}
    </Button>
  ) : null;
  const unclear = unclearLampLabel(row);
  const words = wordsToken(row.transcriptWords);
  return (
    <span className="meetings-selection" data-testid="meetings-selection">
      {onTranscribe ? (
        <AudioOnlyVerb row={row} onTranscribe={onTranscribe} otherwise={runButton} testId="row-transcribe" />
      ) : runButton}
      {view.showRoute ? <RouteDisclosure route={view.plannedRoute} testId="row-route" /> : null}
      <RunAttempts receipt={view.runReceipt} testId="row-attempts" saidOnFace={saidOnFace} />
      <RefusalToken refusal={refusal} durable={readLastRefusal(row)} testId="row-refusal" />
      {/* PHILO-15-07 (B01): honest gaps carry a warn lamp beside the words. */}
      {unclear ? (
        <span className="meetings-selection-fact" data-testid="unclear-lamp">
          <span className="kit-dot" data-tone="warn" aria-hidden="true" />
          {quiet(unclear.replace(/^WARN · /, "")).toLowerCase()}
        </span>
      ) : null}
      {words ? <span className="meetings-selection-fact">{quiet(words)}</span> : null}
    </span>
  );
}

const MEETING_COLUMNS = [
  { key: "when", word: "When", track: "88px" },
  { key: "length", word: "Length", track: "80px" },
  { key: "state", word: "Summary", track: "minmax(140px, 0.6fr)" },
] as const;

export function CatalogRail({
  meetingRows,
  meetings,
  selected,
  setSelected,
  onOpen,
  runningId,
  drainerAbsent,
  runRefusal,
  narrowed,
  emptyImage,
}: {
  /** The app's illustrated icon for the empty list (one true line under it). */
  emptyImage?: string;
  meetingRows: Record<string, unknown>[];
  meetings: { loading: boolean; error: string; reload(): Promise<unknown> };
  /** The selected row (the list's own selection; it opens nothing). */
  selected: Record<string, unknown> | null;
  setSelected: (row: Record<string, unknown> | null) => void;
  /** Enter or a double press: open the meeting (default: select it). */
  onOpen?: (row: Record<string, unknown>) => void;
  /** Retired with the row verbs (they live in the status bar now:
   *  MeetingSelectionVerbs); accepted so older callers still compile. */
  onRunIntelligence?: (id: string, route: PlannedRoute | null) => void;
  onTranscribe?: (id: string) => Promise<unknown>;
  saidOnFace?: string | null;
  restoredId?: string | null;
  runningId: string | null;
  /** The `runtime_queue` frame says no hub drainer will execute the queue. */
  drainerAbsent?: boolean;
  /** HS-201-04 — the hub's 409 on the last run gesture, with its row. */
  runRefusal?: { meetingId: string; refusal: SummaryRefusal } | null;
  /** When true, shown as the narrowed left side in SurfaceSplit. */
  narrowed?: boolean;
}) {
  // The hub's order (newest first) until a header asks for another.
  const [sort, setSort] = useState<ObjectListSort>({ key: "when", dir: "desc" });
  const byId = new Map(meetingRows.map((row) => [String(row.id), row]));
  const rows: ObjectListRow[] = meetingRows.map((row, index) => {
    const id = String(row.id);
    const view = meetingRowView(row, {
      runningId,
      drainerAbsent,
      refusal: runRefusal && runRefusal.meetingId === id ? runRefusal.refusal : null,
    });
    const at = new Date(String(row.started_at ?? row.created_at ?? "")).getTime();
    return {
      id,
      kind: "meeting",
      name: String(row.title ?? "Meeting"),
      when: quiet(ledgerDate(row.started_at ?? row.created_at)),
      // Equal or missing times keep the hub's order (index breaks ties).
      whenSort: Number.isFinite(at) ? at * 1000 - index : -index,
      cells: { length: quiet(durationToken(row.duration_seconds)) },
      sortValues: { length: Number(row.duration_seconds) || 0 },
      state: {
        label: view.label,
        tone: view.tone,
        testId: view.noTranscript ? "no-transcript-token" : "state-token",
      },
    };
  });
  return (
    <div className="meetings-stream" data-narrowed={narrowed || undefined}>
      <SurfaceState
        loading={meetings.loading}
        error={meetings.error}
        empty={!meetingRows.length}
        /* UX-CANON A.3: an empty state is ONE true line with the next move. */
        emptyLabel="Record or import a meeting"
        emptyImage={emptyImage}
        onRetry={() => void meetings.reload()}
      >
        <ObjectList
          label="Meetings"
          density="dense"
          rows={rows}
          columns={MEETING_COLUMNS}
          sort={sort}
          onSort={(key: string) => setSort((current) => ({
            key,
            dir: current.key === key ? (current.dir === "asc" ? "desc" : "asc") : key === "when" ? "desc" : "asc",
          }))}
          selectedId={selected ? String(selected.id) : null}
          onSelect={(id) => setSelected(byId.get(id) ?? null)}
          onOpen={(id) => {
            const row = byId.get(id);
            if (row) (onOpen ?? setSelected)(row);
          }}
          rowProps={(row) => ({ "data-testid": `meeting-row-${row.id}` })}
        />
      </SurfaceState>
    </div>
  );
}
