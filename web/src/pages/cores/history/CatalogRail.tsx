// Meeting list state and wire-to-row mapping; the kit owns interaction and drawing.
import { speechWasMissing } from "../../../desk/firstrun/speechTruth";
import type { ObjectTone } from "../../../desk/surface/objects/kinds";
import { executedReceipt, readPlannedRoute, readRunReceipt, routeOff, routeReady,
  type PlannedRoute, type SummaryRefusal } from "../../../meetings/summaryRoute";
import { countToken } from "../../../desk/surface";
import { durationToken, ledgerDate, clockTime, meetingRowState, stateToken } from "./helpers";
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

export function listMeetingState(row: Record<string, unknown>, options: Parameters<typeof meetingRowView>[1]) {
  const view = meetingRowView(row, options);
  const label = view.label === "Failed" ? "Summary failed"
    : view.label === "Not run" || view.label === "Off" || view.label === "Ran" || view.label === "Summary stored" ? (row.has_summary ? "" : "No summary")
    : /to review$/.test(view.label) ? "Tasks to confirm" : view.label;
  return label ? { label, tone: label === "No summary" ? "warn" as const : view.tone, live: view.live, testId: view.noTranscript ? "no-transcript-token" : "state-token" } : undefined;
}

export const meetingColumns = [
  { key: "name", word: "Meeting", priority: 100, track: "minmax(0, 1fr)" },
  { key: "when", word: "When", priority: 20, track: "132px" },
  { key: "length", word: "Length", priority: 10, track: "72px" },
  { key: "state", word: "State", priority: 30, track: "164px" },
];
export function meetingListRow(row: Record<string, unknown>, options: Parameters<typeof meetingRowView>[1]) {
  return { id: String(row.id), kind: "meeting", name: String(row.title || "Meeting"),
    when: [quiet(ledgerDate(row.started_at ?? row.created_at)), clockTime(row.started_at ?? row.created_at)].filter(Boolean).join(" "),
    cells: { length: quiet(durationToken(row.duration_seconds)) }, state: listMeetingState(row, options) };
}
