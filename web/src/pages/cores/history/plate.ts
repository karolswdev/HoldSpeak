/* The Meetings app in the language (2026-11-08): where one meeting stands,
 * as the spine's four marks (captured, transcribed, intelligence run,
 * decisions filed) and the plate's one thing that matters now. Pure: the
 * rail reads a list row, the record reads its detail; both say the same. */
import type { SpineSegment, SpineTone } from "../../../desk/surface/patterns/Spine";
import type { ObjectTone } from "../../../desk/surface/objects/kinds";
import type { MeetingData } from "./useMeetingData";
import { readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { durationToken, stateToken, unclearLampLabel, wordsToken } from "./helpers";
import { speechWasMissing } from "../../../desk/firstrun/speechTruth";
import { clockOf } from "../../../desk/surface/format";

type Row = Record<string, unknown>;

/** True when the meeting has words to read (the detail's segments, the
 *  list row's segment count or transcript words). */
export function hasTranscript(row: Row): boolean {
  if (Array.isArray(row.segments)) return row.segments.length > 0;
  if (Number(row.segment_count ?? 0) > 0) return true;
  return row.transcriptWords != null && Number(row.transcriptWords) > 0;
}

/** True when a summary is stored (the hub's flag or the text). */
export function hasSummary(row: Row): boolean {
  return row.has_summary === true || String(readMeetingIntel(row)?.summary ?? "").trim() !== "";
}

const CAPTURE_RED = new Set(["CAPTURE FAILED", "INTERRUPTED", "IMPORT FAILED"]);
const BUSY = new Set(["RUNNING", "QUEUED"]);

export type MeetingMarks = {
  captured: SpineTone;
  transcribed: SpineTone;
  intelligence: SpineTone;
  filed: SpineTone;
};

/** The four marks. `pending`: the decisions and actions still to file. */
export function meetingMarks(row: Row, pending: number): MeetingMarks {
  const token = stateToken(row);
  const label = token.label;
  const captured: SpineTone = label === "REC" ? "steel" : CAPTURE_RED.has(label) ? "coral"
    : label === "RECOVERABLE" ? "brass" : "moss";
  const stored = hasSummary(row) || label === "RAN" || label === "STORED";
  const transcribed: SpineTone = label === "REC" || CAPTURE_RED.has(label) ? "idle"
    : label === "TRANSCRIBING" || label === "IMPORTING" ? "steel"
      : hasTranscript(row) || stored ? "moss" : "brass";
  const intelligence: SpineTone = transcribed !== "moss" ? "idle"
    : BUSY.has(label) ? "steel"
      : label === "FAILED" ? "coral"
        : stored ? "moss"
          : label === "SKIPPED" ? "graphite" : "brass";
  const filed: SpineTone = pending > 0 ? "brass" : intelligence === "moss" ? "moss" : "idle";
  return { captured, transcribed, intelligence, filed };
}

const WORDS: Record<keyof MeetingMarks, Partial<Record<SpineTone, string>>> = {
  captured: { steel: "recording", coral: "capture failed", brass: "capture to recover", moss: "captured" },
  transcribed: { steel: "transcribing", moss: "transcribed", brass: "not transcribed" },
  intelligence: { steel: "intelligence runs", coral: "intelligence failed", moss: "intelligence run",
    graphite: "intelligence skipped", brass: "intelligence not run" },
  filed: { moss: "decisions filed" },
};

/** The spine's segments and its words ("captured, transcribed, 2 to file"). */
export function meetingSpine(row: Row, pending: number): { segments: SpineSegment[]; label: string } {
  const marks = meetingMarks(row, pending);
  const keys = ["captured", "transcribed", "intelligence", "filed"] as const;
  const words = keys.map((key) => key === "filed" && marks.filed === "brass"
    ? `${pending} to file` : WORDS[key][marks[key]] ?? "").filter(Boolean);
  return { segments: keys.map((key) => ({ tone: marks[key], share: 1 })), label: words.join(", ") };
}

/** The one proposal the plate leads with (the record's ledger reports it). */
export type PlateLead = {
  id: string;
  text: string;
  facts: string;
  /** "Confirm", or "Fill in" when the action has no owner or date yet. */
  verb: string;
  act(): void;
  busy?: boolean;
};

export type PlateKind = "conflict" | "recording" | "capture" | "transcribe" | "transcribing" | "running" | "failed"
  | "run" | "proposal" | "review" | "send" | "settled";

export type Plate = { kind: PlateKind; title: string; facts: string; tone: SpineTone };

/** The one thing that matters now, in order: two versions to resolve, the
 *  capture, Transcribe, a run that runs or failed, Run intelligence, the
 *  first proposal to file, then Send the follow-up. */
export function meetingPlate(row: Row, { conflicts = 0, lead = null, pending = 0 }: {
  conflicts?: number; lead?: PlateLead | null; pending?: number;
}): Plate {
  const marks = meetingMarks(row, pending);
  if (conflicts > 0) {
    return { kind: "conflict", title: "Two versions of this meeting", facts: conflicts === 1 ? "1 sync conflict" : `${conflicts} sync conflicts`, tone: "brass" };
  }
  if (marks.captured === "steel") return { kind: "recording", title: "Recording", facts: "", tone: "steel" };
  if (marks.captured === "coral" || marks.captured === "brass") {
    return { kind: "capture", title: marks.captured === "coral" ? "The capture stopped" : "Recover the capture", facts: "", tone: marks.captured };
  }
  if (marks.transcribed === "steel") return { kind: "transcribing", title: "Transcribing", facts: "", tone: "steel" };
  if (marks.transcribed === "brass") return { kind: "transcribe", title: "Transcribe", facts: "audio kept · no transcript", tone: "brass" };
  if (marks.intelligence === "steel") return { kind: "running", title: "Intelligence runs", facts: "", tone: "steel" };
  if (marks.intelligence === "coral") return { kind: "failed", title: "Intelligence failed", facts: "the meeting and the transcript are saved", tone: "coral" };
  if (marks.intelligence === "brass") return { kind: "run", title: "Run intelligence", facts: "decisions · actions · summary", tone: "brass" };
  if (lead) return { kind: "proposal", title: lead.text, facts: lead.facts, tone: "brass" };
  if (pending > 0) return { kind: "review", title: `${pending} to review`, facts: "decisions · actions", tone: "brass" };
  if (marks.intelligence === "moss") return { kind: "send", title: "Send the follow-up", facts: "summary stored · nothing to file", tone: "moss" };
  return { kind: "settled", title: "Saved", facts: "", tone: "graphite" };
}

/** What this meeting still asks of him: the legacy needs and the
 *  proposals still to decide (not deferred). */
export function meetingReviewCount(data: Pick<MeetingData, "ftProposals" | "needsCount">): number {
  const legacyPending = Number(data.needsCount ?? 0);
  return (Number.isFinite(legacyPending) ? Math.max(0, legacyPending) : 0)
    + (data.ftProposals ?? []).filter(
      (proposal) => proposal.state === "proposed" && !proposal.deferred_until,
    ).length;
}

/** The distinct speakers the transcript names, as they first appear. */
export function peopleNames(segments: readonly Record<string, unknown>[]): string[] {
  const seen = new Map<string, string>();
  for (const row of segments) {
    const speaker = String(row.speaker ?? "").trim();
    if (speaker && !seen.has(speaker.toLowerCase())) seen.set(speaker.toLowerCase(), speaker);
  }
  return [...seen.values()];
}

/** Window grammar: the summary's state in the status bar, a dot and a word
 *  in sentence case (`Summary stored`, `Summary failed`). Pure. */
export function meetingSummaryState(
  source: Record<string, unknown>,
  summariesOff = false,
): { text: string; lamp?: ObjectTone } {
  const token = stateToken(source);
  const stored = Boolean(String(readMeetingIntel(source)?.summary ?? "").trim());
  if (token.label === "RAN" || (stored && !["RUNNING", "QUEUED", "FAILED"].includes(token.label))) {
    return { text: "Summary stored", lamp: "ok" };
  }
  switch (token.label) {
    case "RUNNING": return { text: "Summary running", lamp: "info" };
    case "QUEUED": return { text: "Summary queued", lamp: "info" };
    case "FAILED": return { text: token.axis ? "Summary failed" : "Failed", lamp: "fail" };
    case "SKIPPED": return { text: "Summary skipped", lamp: "warn" };
    case "PARTIAL": return { text: "Summary partial", lamp: "warn" };
    case "OFF": return summariesOff ? { text: "Summaries off" } : { text: "Summary not run" };
    default: {
      const word = token.label.charAt(0) + token.label.slice(1).toLowerCase();
      const lamp: ObjectTone | undefined = token.tone === "danger" ? "fail" : token.tone === "warn" ? "warn" : undefined;
      return { text: word, lamp };
    }
  }
}

/** The mast's facts line (mono): when, who, how long, then the transcript's
 *  honest gaps ("1 unclear span") and its words; no count of zero. */
export function mastFacts(meeting: Row): string {
  const started = new Date(String(meeting.started_at ?? meeting.created_at ?? ""));
  const when = Number.isNaN(started.getTime()) ? "" : `${started.toLocaleDateString(undefined, {
    weekday: "short", day: "numeric", month: "short",
  })}, ${clockOf(started)}`;
  const people = peopleNames(Array.isArray(meeting.segments) ? meeting.segments as Row[] : []);
  const who = people.length > 3 ? `${people.slice(0, 3).join(", ")} +${people.length - 3}` : people.join(", ");
  const length = durationToken(meeting.duration_seconds ?? meeting.duration).toLowerCase();
  const unclear = unclearLampLabel(meeting)?.replace(/^WARN · /, "").toLowerCase() ?? "";
  const words = wordsToken(meeting.transcriptWords)?.toLowerCase() ?? "";
  const speech = speechWasMissing(meeting) ? "speech not set up" : "";
  return [when, who, length, speech, unclear, words].filter(Boolean).join(" · ");
}
