// HS-117-09 — extracted from HistoryCore.tsx: helpers and constants.
// HS-100-08 — Meetings opens on OUTCOMES (thesis §1.2): what needs
// you, what settled, the transcript as a receipt. Record/import and
// the typed artifacts are wings; speakers/projects/queues plumbing
// stacks behind the one gear door.
import type { ReactNode } from "react";

export const WINGS = [
  { id: "outcomes", label: "Outcomes" },
  { id: "record", label: "Record" },
  { id: "artifacts", label: "Artifacts" },
];
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
    error: "Intelligence failed",
    partial: "Intelligence incomplete",
    skipped: "Intelligence skipped",
    queued: "Intelligence queued",
    running: "Intelligence running",
    ready: "Intelligence ready",
  };
  return (
    known[state] ||
    state
      .replace(/_/g, " ")
      .replace(/^./, (character) => character.toUpperCase())
  );
}

/* HS-111-03 — the catalog's state token: axis-named, tone as color on
   the words (never a shuffle, never a pill). "Intelligence", never
   the banned abbreviation (HS-100-05 vocabulary guard). The axis word
   rides its own span so the narrow rail can fold it away without
   losing the state. */
export type StateToken = { axis?: string; label: string; tone?: "warn" | "danger" };

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
  const axis = "INTELLIGENCE";
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
  };
  if (row.status === "failed") return { label: "FAILED", tone: "danger" };
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

/** n MIN, folding to n HR past ten hours — a catalog cell, not a
 * six-digit minute wall. Empty when the wire has no duration. */
export function durationToken(seconds: unknown): string {
  const minutes = Math.round(Number(seconds ?? 0) / 60);
  if (!Number.isFinite(minutes) || minutes <= 0) return "";
  if (minutes >= 600) return `${Math.round(minutes / 60)} HR`;
  return `${minutes} MIN`;
}

/** hh:mm — the receipt stamp's clock. */
export function clockTime(value: unknown): string {
  const date = new Date(String(value ?? ""));
  if (Number.isNaN(date.getTime())) return "";
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
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
export type Receipt = { text: string; tone?: "danger" };

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

/** HS-170-04 — true when the meeting is OFF (intel disabled) AND has a
 *  transcript (words > 0): the Run intelligence verb is honest. */
export function needsIntelligence(row: Record<string, unknown>): boolean {
  const token = stateToken(row);
  if (token.label !== "OFF") return false;
  return row.transcriptWords != null && Number(row.transcriptWords) > 0;
}

/** HS-170-04 — the face's meeting state for list rows: label + verb.
 *  OFF with transcript: `Run intelligence` (primary dense).
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

  // OFF with transcript => Run intelligence
  if (token.label === "OFF" && hasTranscript) {
    return { label: "OFF", verb: "Run intelligence", verbVariant: "primary" };
  }
  // OFF without transcript => no Run verb, just Open
  if (token.label === "OFF" && !hasTranscript) {
    return { label: "OFF", verb: "Open", verbVariant: "ghost" };
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
  // SAVED (complete)
  if (token.label === "SAVED") {
    return { label: "SAVED", tone: "success", verb: "Open", verbVariant: "ghost" };
  }
  // Catch-all
  return { label: token.label, tone: token.tone, verb: "Open", verbVariant: "ghost" };
}
