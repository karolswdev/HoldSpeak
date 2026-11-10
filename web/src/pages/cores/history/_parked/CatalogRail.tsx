// Parked: Records uses the shared selection list instead of the card rail.
// The Meetings app in the language (2026-11-08): the rail of meetings at
// the window's left. One row per meeting: its title, the day and length in
// mono, the spine (captured, transcribed, intelligence run, decisions filed)
// and the state in a word. A press picks the meeting; the pane at the right
// shows it (mast, plate, ledger). Up and Down move the focus along the rows.
import type { ReactNode } from "react";
import { speechWasMissing } from "../../../desk/firstrun/speechTruth";
import { SurfaceState } from "../../../desk/surface/Surface";
import { Loading } from "../../../desk/surface/kit";
import { Rail } from "../../../desk/surface";
import type { ObjectTone } from "../../../desk/surface/objects/kinds";
import {
  executedReceipt,
  readPlannedRoute,
  readRunReceipt,
  routeOff,
  routeReady,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import { countToken } from "../../../desk/surface";
import { durationToken, ledgerDate, meetingRowState, stateToken } from "./helpers";
import { meetingSpine } from "./plate";

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
  /** A summary runs (queued or running): the dot breathes. */
  live: boolean;
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
  // DELIGHT 2 (small joys): a summary that runs is blue, never the ember of a
  // warning. A failed row's Retry turns its red dot blue while the run is
  // queued or running, then green when the summary is stored (the hub's
  // state, polled by useSummaryRun). The meeting window's status bar uses
  // the same lamp (MeetingHeader meetingSummaryState: info).
  const runs = displayLabel === "RUNNING" || displayLabel === "QUEUED";
  if (runs) displayTone = "info";
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
    live: runs && !audioOnly,
    noTranscript: audioOnly,
    verb,
    plannedRoute,
    runReceipt,
    isRunning,
    showRoute: state.verb === "Run summary" || state.verb === "Retry" || isRunning,
  };
}

export function CatalogRail({
  meetingRows,
  meetings,
  picked,
  marked = null,
  onPick,
  onBack,
  runningId,
  drainerAbsent,
  runRefusal,
  emptyImage,
  onEmptyAction,
  head,
  rowsHidden = false,
}: {
  meetingRows: Record<string, unknown>[];
  meetings: { loading: boolean; error: string; reload(): Promise<unknown> };
  /** The meeting the pane shows. */
  picked: string | null;
  /** The row the rail marks: the picked one, else the last one picked or
   *  the one Restore brought back. */
  marked?: string | null;
  onPick: (row: Record<string, unknown>) => void;
  onBack?(): void;
  runningId: string | null;
  /** The `runtime_queue` frame says no hub drainer will execute the queue. */
  drainerAbsent?: boolean;
  /** HS-201-04 — the hub's 409 on the last run gesture, with its row. */
  runRefusal?: { meetingId: string; refusal: SummaryRefusal } | null;
  /** The app's illustrated icon for the empty list (one true line under it). */
  emptyImage?: string;
  /** The empty list's one verb (Import a recording). */
  onEmptyAction?: () => void;
  /** The rail's head: search, Record, Import, the filters. */
  head?: ReactNode;
  /** The parked rows take the rail's place (the head's Parked strip). */
  rowsHidden?: boolean;
}) {
  const rows = meetingRows.map((row) => {
    const id = String(row.id);
    const view = meetingRowView(row, { runningId, drainerAbsent,
      refusal: runRefusal?.meetingId === id ? runRefusal.refusal : null });
    const spine = meetingSpine(row, Number(row.needs_you_count ?? row.needsYouCount ?? 0) || 0);
    const title = String(row.title ?? "").trim() || "Meeting";
    return {
      id, label: <span title={title}>{title}</span>, accessibleLabel: `${title}, ${view.label}`,
      facts: [quiet(ledgerDate(row.started_at ?? row.created_at)), quiet(durationToken(row.duration_seconds))].filter(Boolean).join(" · "),
      state: <span data-tone={{ ask: "brass", fail: "coral", ok: "moss", info: "steel", warn: "coral", idle: "idle" }[view.tone]}
        data-live={view.live || undefined} data-testid={view.noTranscript ? "no-transcript-token" : "state-token"}>{view.label}</span>,
      spine, rowData: { "data-testid": `meeting-row-${id}`, "data-selected": id === (picked ?? marked) ? "true" : undefined },
    };
  });
  const unavailable = rowsHidden || meetings.loading || meetings.error || !meetingRows.length;
  return <Rail label="Meetings" data-testid="meetings-rail" picked={picked} onPick={(id) => {
    const row = meetingRows.find((row) => String(row.id) === id);
    if (row) onPick(row);
  }} head={head} onBack={onBack} items={rows} paneOpen={Boolean(picked)}>
    {unavailable ? rowsHidden ? <></> : meetings.loading ? <Loading data-testid="meetings-loading" /> : (
      <SurfaceState error={meetings.error} empty={!meetingRows.length} emptyLabel="Record or import a meeting"
        emptyImage={emptyImage} emptyKind="meeting" onAction={onEmptyAction} actionLabel="Import a recording" onRetry={() => void meetings.reload()} />
    ) : undefined}
  </Rail>;
}
