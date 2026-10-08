// HS-117-09 — extracted from HistoryCore.tsx: helpers and constants.
// HS-100-08 — Meetings opens on OUTCOMES (thesis §1.2): what needs
// you, what settled, the transcript as a receipt. Record/import and
// the typed artifacts are wings; speakers/projects/queues plumbing
// stacks behind the one gear door.
import { wireClock } from "../../../desk/surface/format";
import { countToken } from "../../../desk/surface/count";
import type { ReactNode } from "react";

export const WINGS = [
  { id: "outcomes", label: "Outcomes" },
  { id: "review", label: "Review" },
  { id: "record", label: "Record" },
  { id: "artifacts", label: "Artifacts" },
];
/** HS-200-12 — the detail pane's faces: the outcomes face, the review
 *  wing (posture 4), the artifacts wing. */
export type DetailView = "outcomes" | "artifacts" | "review";
// Door sections (ids are part of the phase-91 archive lock).
export const DOOR_SECTIONS = ["actions", "speakers", "projects", "queues"] as const;
// Receipt sections inside a meeting ("transcript", "aftercare",
// "routing", "proposals" remain the wire vocabulary).

export function displayState(value: unknown): string {
  const state = String(value ?? "").trim();
  const known: Record<string, string> = {
    pending: "Queued",
    complete: "Succeeded",
    capture_failed: "Capture failed",
    import_failed: "Import failed",
    recoverable: "Recovery available",
    recording: "Recording",
    finalized: "Saved",
    // HS-201-06 (Constitution tenet 4, ASD-STE100): the thing the user
    // asked for is a summary; "intelligence" is the wire's word for it.
    error: "Summary failed",
    partial: "Summary incomplete",
    skipped: "Summary skipped",
    queued: "Summary queued",
    running: "Summary running",
    ready: "Summary ready",
  };
  return (
    known[state] ||
    state
      .replace(/_/g, " ")
      .replace(/^./, (character) => character.toUpperCase())
  );
}

/* HS-111-03 — the catalog's state token: axis-named, tone as color on
   the words (never a shuffle, never a pill). "Summary" since HS-201-06;
   never the banned abbreviation (HS-100-05 vocabulary guard). The axis word
   rides its own span so the narrow rail can fold it away without
   losing the state. */
export type StateToken = { axis?: string; label: string; tone?: "warn" | "danger" | "success" };

/** HS-170-04: liveness heuristic for capture_status=recording rows.
 *  No /api/meetings/active route exists (the active session is process-local
 *  runtime state); the list query carries only DB columns.
 *  Seam: ended_at is null AND started_at is within the last 6 hours →
 *  likely still live (REC). Otherwise → INTERRUPTED (dead session). */
function isLikelyLiveCapture(row: Record<string, unknown>): boolean {
  if (row.ended_at != null) return false;
  const started = new Date(String(row.started_at ?? ""));
  if (Number.isNaN(started.getTime())) return false;
  const sixHoursAgo = Date.now() - 6 * 60 * 60 * 1000;
  return started.getTime() > sixHoursAgo;
}

export function stateToken(row: Record<string, unknown>): StateToken {
  const capture = String(row.capture_status ?? "");
  // HS-170-04: capture_status=recording — REC when likely still live
  // (no ended_at, started within 6 h); INTERRUPTED otherwise (dead
  // session that never finalized, UX-CANON A.10 — honest states).
  if (capture === "recording") {
    return isLikelyLiveCapture(row)
      ? { label: "REC", tone: "danger" }
      : { label: "INTERRUPTED", tone: "warn" };
  }
  if (capture === "capture_failed")
    return { label: "CAPTURE FAILED", tone: "danger" };
  if (capture === "recoverable") return { label: "RECOVERABLE", tone: "warn" };
  const intelValue = row.intel_status;
  const state =
    typeof intelValue === "object" && intelValue !== null
      ? String((intelValue as Record<string, unknown>).state ?? "")
      : String(intelValue ?? "");
  // HS-201-06: the axis is the SUMMARY (audit row 4: `INTELLIGENCE
  // FAILED` on the meeting record said nothing a stranger could read).
  const axis = "SUMMARY";
  const known: Record<string, StateToken> = {
    disabled: { axis, label: "OFF" },
    skipped: { axis, label: "SKIPPED", tone: "warn" },
    queued: { axis, label: "QUEUED", tone: "warn" },
    pending: { axis, label: "QUEUED", tone: "warn" },
    running: { axis, label: "RUNNING", tone: "warn" },
    partial: { axis, label: "PARTIAL", tone: "warn" },
    error: { axis, label: "FAILED", tone: "danger" },
    failed: { axis, label: "FAILED", tone: "danger" },
    import_failed: { label: "IMPORT FAILED", tone: "danger" },
    // PHILO-15 10 (B14): an import still transcribing. It read SAVED, and
    // the headline said "All summaries done" before a word was heard.
    importing: { label: "IMPORTING", tone: "warn" },
  };
  if (row.status === "failed") return { label: "FAILED", tone: "danger" };
  // PHILO-13-04 A3-W (coordinator ruling): an ACTIVE run is the live fact,
  // so RUNNING, QUEUED and FAILED (with its Retry) show first.
  if (["running", "queued", "pending", "error", "failed", "importing"].includes(state)) {
    return known[state];
  }
  // Then the list row's `has_summary` (H-A3, #729): the STORED fact, read
  // from the persisted summary, not the config switch or a quiet run status.
  // The rail said `OFF` beside a stored summary (meetings-stored-1440.png).
  if (row.has_summary === true) return { axis: "SUMMARY", label: "STORED" };
  // HS-172: complete intel → RAN (success).  HS-200-12: the bound executor
  // writes `ready` when a real run finishes (db/intel.py, "Meeting
  // intelligence ready."); `complete` is the seeded/legacy word.  Both RAN.
  if (state === "complete" || state === "ready") return { label: "RAN", tone: "success" };
  return known[state] ?? { label: "SAVED" };
}

export const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
];

/** MMM DD — the catalog's date column. */
export function ledgerDate(value: unknown): string {
  const date = new Date(String(value ?? ""));
  if (Number.isNaN(date.getTime())) return "";
  return `${MONTHS[date.getMonth()]} ${String(date.getDate()).padStart(2, "0")}`;
}

/** The length of the recording, in the unit that tells the truth about it:
 * `n S` under a minute, `n MIN` above it, folding to `n HR` past ten hours —
 * a catalog cell, not a six-digit minute wall. Empty when the wire has no
 * duration.
 *
 * HS-201-10 (rehearsal defect 9): a 2.79 s import read `1 MIN` beside the
 * `5 S` the summary run took, in the same dot-line. Minutes were the only
 * unit this token had, so every short recording was rounded into a lie (or,
 * below thirty seconds, rounded to nothing at all). */
export function durationToken(seconds: unknown): string {
  const total = Number(seconds ?? 0);
  if (!Number.isFinite(total) || total <= 0) return "";
  if (total < 60) return `${Math.max(1, Math.round(total))} S`;
  const minutes = Math.round(total / 60);
  if (minutes >= 600) return `${Math.round(minutes / 60)} HR`;
  return `${minutes} MIN`;
}

/** HS-172: wall-clock seconds the intel job took, derived from
 *  intel_status.requested_at and intel_status.completed_at. */
export function intelDurationSeconds(row: Record<string, unknown>): number {
  const intel = row.intel_status;
  if (typeof intel !== "object" || intel === null) return 0;
  const obj = intel as Record<string, unknown>;
  const req = obj.requested_at;
  const comp = obj.completed_at;
  if (!req || !comp) return 0;
  const start = new Date(String(req)).getTime();
  const end = new Date(String(comp)).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return 0;
  return Math.max(0, Math.round((end - start) / 1000));
}

/** HS-172: intel run duration as `N S` token. Empty when unavailable. */
export function intelDurationToken(row: Record<string, unknown>): string {
  const s = intelDurationSeconds(row);
  return s > 0 ? `${s} S` : "";
}

/** hh:mm — the receipt stamp's clock. */
export function clockTime(value: unknown): string {
  return wireClock(value);
}

export function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** The one receipt channel: what the machine just did, on the footer. */
/** PHILO-15-07 (B15): the summary run a receipt speaks for. */
export type RunIdentity = { meetingId: string; jobId: string };
export type Receipt = { text: string; tone?: "danger"; run?: RunIdentity };

export const ACTIVE_RUN_STATES = new Set(["queued", "pending", "running", "claimed", "reserved", "retrying"]);
export const FINAL_RUN_STATES = new Set(["ready", "complete", "error", "failed"]);

/** PHILO-15-07 (Astra iteration 2): the footer receipt a face adopts on its
 *  first read of the rows, from durable state only. An active run (the row's
 *  intel state, or its job's status) gives a bound `QUEUED hh:mm`; otherwise
 *  the newest stored run receipt gives `RAN · hh:mm` / `FAILED · hh:mm` at the
 *  time its job was last written, but only when that was TODAY (a receipt
 *  from another day is not footer material; it lives on the meeting record).
 *  Null when no fresh run is on record. */
function isToday(value: string): boolean {
  const at = new Date(value);
  if (Number.isNaN(at.getTime())) return false;
  return at.toDateString() === new Date().toDateString();
}

export function adoptDurableRunReceipt(
  rows: Record<string, unknown>[],
): { receipt: Receipt; active: boolean } | null {
  const jobOf = (row: Record<string, unknown>) =>
    (row.intel_job && typeof row.intel_job === "object" ? row.intel_job : {}) as Record<string, unknown>;
  const active = rows.find((row) =>
    ACTIVE_RUN_STATES.has(intelStateOf(row.intel_status)) ||
    ACTIVE_RUN_STATES.has(String(jobOf(row).status ?? "")),
  );
  if (active) {
    const job = jobOf(active);
    const at = typeof job.requested_at === "string" ? job.requested_at : new Date().toISOString();
    return {
      active: true,
      receipt: {
        text: `QUEUED ${clockTime(at)}`,
        run: { meetingId: String(active.id), jobId: `durable:${String(active.id)}` },
      },
    };
  }
  let newest: { row: Record<string, unknown>; at: string } | null = null;
  for (const row of rows) {
    const receipt = row.run_receipt as Record<string, unknown> | null | undefined;
    const at = jobOf(row).updated_at;
    if (!receipt || typeof receipt !== "object" || typeof at !== "string") continue;
    if (!newest || at > newest.at) newest = { row, at };
  }
  if (!newest || !isToday(newest.at)) return null;
  const stored = newest.row.run_receipt as Record<string, unknown>;
  const state = stored.outcome === "succeeded" ? "ready" : "failed";
  return {
    active: false,
    receipt: {
      ...finishedRunReceipt(state, newest.at),
      run: { meetingId: String(newest.row.id), jobId: String(stored.job_id ?? newest.row.id) },
    },
  };
}

/** The intel state word from either wire shape (string or `{state}`). */
export function intelStateOf(raw: unknown): string {
  return typeof raw === "object" && raw !== null
    ? String((raw as Record<string, unknown>).state ?? "")
    : String(raw ?? "");
}

/** PHILO-15-07 (B15) — the footer receipt once a queued summary run ends:
 *  `RAN · 11:02` or `FAILED · 11:02`; another final state says its own word. */
export function finishedRunReceipt(state: string, at: string): Receipt {
  const s = String(state || "").toLowerCase();
  const clock = clockTime(at);
  if (s === "ready" || s === "complete") return { text: `RAN · ${clock}` };
  if (s === "error" || s === "failed") return { text: `FAILED · ${clock}`, tone: "danger" };
  return { text: `${(s || "done").toUpperCase().replace(/_/g, " ")} · ${clock}` };
}

/** Needs-you table row shape shared between useMeetingData and NeedsYouTable. */
export type NeedsRow = { cells: ReactNode[]; verbs: ReactNode };

/** HS-170-04 — `1,204 WORDS` token from transcriptWords. Null when
 *  the wire says None (no transcript) — the caller renders NO TRANSCRIPT. */
export function wordsToken(transcriptWords: unknown): string | null {
  if (transcriptWords == null) return null;
  const n = Number(transcriptWords);
  if (!Number.isFinite(n) || n <= 0) return null;
  return `${n.toLocaleString()} WORDS`;
}

/** PHILO-15-07 (B01) — the lamp a transcript with honest gaps carries:
 *  `WARN · 1 UNCLEAR SPAN`. Null at zero (no counters of zero). Reads the
 *  list row's `unclearSpans`, the detail's `unclearSpans`, or the desk
 *  model's field of the same name. */
export function unclearLampLabel(row: Record<string, unknown> | null | undefined): string | null {
  const raw = row?.unclearSpans ?? row?.unclear_spans;
  const token = countToken(Number(raw ?? 0) || 0, "UNCLEAR SPAN");
  return token ? `WARN · ${token}` : null;
}

/** HS-170-04 — true when the meeting is OFF (intel disabled) AND has a
 *  transcript (words > 0): the Run summary verb is honest. */
/** HS-202-02 — the summary is OFF for this meeting, whatever the list
 *  happens to know about its transcript yet. `needsIntelligence` also
 *  requires `transcriptWords`, which only the LIST carries; a record
 *  opened while its import was still running has a stale zero there long
 *  after the transcript is on the glass. */
export function summaryIsOff(row: Record<string, unknown>): boolean {
  return stateToken(row).label === "OFF";
}

export function needsIntelligence(row: Record<string, unknown>): boolean {
  const token = stateToken(row);
  if (token.label !== "OFF") return false;
  return row.transcriptWords != null && Number(row.transcriptWords) > 0;
}

/** HS-201-01 — true when the meeting's state token names a failure:
 *  FAILED, CAPTURE FAILED, IMPORT FAILED. A failed meeting needs the
 *  owner, so no headline may speak the all-clear over it. */
export function meetingFailed(row: Record<string, unknown>): boolean {
  return stateToken(row).label.endsWith("FAILED");
}

/** PHILO-13-03 — the summary is LIVE: the queue holds it running, or it
 *  waits (queued, or a retry after a failed attempt; the rail says QUEUED). */
function summaryRunning(row: Record<string, unknown>): boolean {
  return stateToken(row).label === "RUNNING";
}
function summaryQueued(row: Record<string, unknown>): boolean {
  return stateToken(row).label === "QUEUED";
}

/** PHILO-13-03 — a summary that should exist and does not: OFF over a
 *  transcript (the `Run summary` row), or a finished run with no stored
 *  summary (`has_summary` false on the list row, H-A3). */
function summaryMissing(row: Record<string, unknown>): boolean {
  if (needsIntelligence(row)) return true;
  return row.has_summary === false && stateToken(row).label === "RAN";
}

function counted(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** HS-170-04 — the display headline. PHILO-13-03 (Astra's pass on #736):
 *  the process state leads, as on the rail: `n meeting(s) failed`, then
 *  `n summary/summaries running`, then `n ... queued`, then `n meeting(s)
 *  need(s) a summary`. `All summaries done` only when no summary is live or
 *  failed, every summary that should exist exists, and a summary can run. `No meetings yet` when
 *  empty. HS-201-01: never the all-clear over a FAILED row. */
export function meetingsHeadline(
  meetingRows: Record<string, unknown>[],
  loading: boolean,
  /** The face read a summary route and it cannot run (no engine). The
   *  route is the hub's `planned_route`, resolved through the meeting-intel
   *  queue's route policy, so a Default for AI work makes it ready
   *  (PHILO-15 01). */
  routeMissing = false,
  /** The owner turned summaries OFF (PHILO-15 01 ruling): OFF, not "no engine". */
  routeOff = false,
): { text: string; accent: boolean } {
  if (loading) return { text: "", accent: false };
  if (meetingRows.length === 0) return { text: "No meetings yet", accent: false };
  const failed = meetingRows.filter(meetingFailed).length;
  if (failed > 0) {
    return { text: counted(failed, "meeting failed", "meetings failed"), accent: true };
  }
  // PHILO-15 10 (B14): no all-clear while a meeting is still importing.
  const importing = meetingRows.filter((row) => stateToken(row).label === "IMPORTING").length;
  if (importing > 0) {
    return { text: counted(importing, "meeting importing", "meetings importing"), accent: true };
  }
  const running = meetingRows.filter(summaryRunning).length;
  if (running > 0) {
    return { text: counted(running, "summary running", "summaries running"), accent: true };
  }
  const queued = meetingRows.filter(summaryQueued).length;
  if (queued > 0) {
    return { text: counted(queued, "summary queued", "summaries queued"), accent: true };
  }
  // PHILO-15 01 ruling: OFF wins over the unsummarised count. The owner
  // turned summaries off, so a meeting without one is not an ask.
  if (routeOff) return { text: "Summaries off", accent: false };
  const missing = meetingRows.filter(summaryMissing).length;
  if (missing > 0) {
    // HS-201-04 (tenet 4): the headline names the same thing its verb does.
    return { text: counted(missing, "meeting needs a summary", "meetings need summaries"), accent: true };
  }
  // PHILO-13-03 (canvas C1-4a): Meetings counts summaries, a narrower set
  // than "needs you"; its all-clear says what it counts, and only when true.
  // Inventory 2026-10-03 (UX-CANON A.10): the all-clear stood over the
  // footer's "NO SUMMARY ROUTE". With no engine the next meeting gets no
  // summary; the headline says so in the Chair's words, not "all done".
  if (routeMissing) return { text: "No engine for summaries", accent: true };
  return { text: "All summaries done", accent: false };
}

/** HS-201-11 — is there an open action a meeting facet could match?
 *
 *  `HAS OPEN ACTIONS` was drawn on every Meetings face, including one whose
 *  only meeting held zero actions (audits/rehearsal-07-opus.md, LANGUAGE
 *  row): a filter that can match nothing says nothing. `/api/all-action-items`
 *  answers only OPEN items -- `include_completed=false` becomes
 *  `a.status = 'pending'` (holdspeak/db/meetings.py:869-870), the same
 *  predicate the facet filters meetings on (`:651-655`). An item with no
 *  `meeting_id` came from a thread, which the meeting facet cannot reach.
 */
export function hasOpenMeetingActions(actionItems: unknown): boolean {
  if (!Array.isArray(actionItems)) return false;
  return actionItems.some((item) => {
    if (typeof item !== "object" || item === null) return false;
    const meetingId = (item as Record<string, unknown>).meeting_id;
    return meetingId != null && String(meetingId).length > 0;
  });
}

/** HS-170-04 — the face's meeting state for list rows: label + verb.
 *  OFF with transcript: `Run summary` (primary dense).
 *  NEEDS YOU N: `Open` (ghost). SAVED: `Open` (ghost). No transcript:
 *  `Open` (ghost). The verb is null when the state alone says everything. */
export type MeetingRowState = {
  label: string;
  tone?: "warn" | "danger" | "success" | "accent";
  verb: string | null;
  verbVariant: "primary" | "ghost";
};

export function meetingRowState(row: Record<string, unknown>): MeetingRowState {
  const token = stateToken(row);
  const hasTranscript = row.transcriptWords != null && Number(row.transcriptWords) > 0;

  // OFF with transcript => Run summary
  // HS-201-04 (Constitution tenet 4, ASD-STE100): the thing the user asks
  // for is a SUMMARY. "Intelligence" is the wire's word for it, and the
  // verb said it out loud on every meeting row.
  if (token.label === "OFF" && hasTranscript) {
    return { label: "OFF", verb: "Run summary", verbVariant: "primary" };
  }
  // OFF without transcript => no Run verb, just Open
  if (token.label === "OFF" && !hasTranscript) {
    return { label: "OFF", verb: "Open", verbVariant: "ghost" };
  }
  // IMPORTING (PHILO-15 10): the transcript is not here yet; no verb.
  if (token.label === "IMPORTING") {
    return { label: "IMPORTING", tone: "warn", verb: null, verbVariant: "ghost" };
  }
  // REC (live capture — no verb, the meeting is in the live room)
  if (token.label === "REC") {
    return { label: "REC", tone: "danger", verb: null, verbVariant: "ghost" };
  }
  // INTERRUPTED (dead capture session — ghost Open to view what exists)
  if (token.label === "INTERRUPTED") {
    return { label: "INTERRUPTED", tone: "warn", verb: "Open", verbVariant: "ghost" };
  }
  // RUNNING (intelligence)
  if (token.label === "RUNNING") {
    return { label: "RUNNING", tone: "warn", verb: null, verbVariant: "ghost" };
  }
  // QUEUED (intelligence queued — ghost Open)
  if (token.label === "QUEUED") {
    return { label: "QUEUED", tone: "warn", verb: "Open", verbVariant: "ghost" };
  }
  // FAILED
  if (token.label === "FAILED" || token.tone === "danger") {
    return { label: token.label, tone: "danger", verb: "Retry", verbVariant: "primary" };
  }
  // PHILO-13-04 A3-W: a stored summary. The rail drops the axis word on
  // every other state; `STORED` alone does not say what is stored.
  if (token.label === "STORED") {
    return { label: "SUMMARY STORED", verb: "Open", verbVariant: "ghost" };
  }
  // RAN (complete intel)
  if (token.label === "RAN") {
    return { label: "RAN", tone: "success", verb: "Open", verbVariant: "ghost" };
  }
  // SAVED (finalized, no intel)
  if (token.label === "SAVED") {
    return { label: "SAVED", tone: "success", verb: "Open", verbVariant: "ghost" };
  }
  // Catch-all
  return { label: token.label, tone: token.tone, verb: "Open", verbVariant: "ghost" };
}
