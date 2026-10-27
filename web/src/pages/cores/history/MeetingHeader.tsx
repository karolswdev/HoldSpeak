// HS-172 — the detail header. Window grammar (2026-10-24): the title bar IS
// the meeting's name, so the body never repeats it as a headline. The head
// is compact: the meeting's glyph and ONE muted line (`Oct 24 · 30 min`, a
// gap a dot and a word, the people as avatars). The summary's state and the
// engine's egress chip are the window's status bar (meetingSummaryState).
import type { ReactNode } from "react";
import { AvatarStack, DotWord, Steps, type Step, type StatusStripItem } from "../../../desk/surface";
import type { ObjectTone } from "../../../desk/surface/objects/kinds";
import { objectSprite } from "../../../desk/surface/objects/kinds";
import { listSprite } from "../../../desk/sprites";
import { ledgerDate, durationToken, stateToken, unclearLampLabel } from "./helpers";
import type { MeetingData } from "./useMeetingData";
import { readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { speechWasMissing } from "../../../desk/firstrun/speechTruth";

/** The distinct speakers the transcript names (`4 PEOPLE`); 0 when none. */
export function peopleCount(segments: readonly Record<string, unknown>[]): number {
  const names = new Set<string>();
  for (const row of segments) {
    const speaker = String(row.speaker ?? "").trim();
    if (speaker) names.add(speaker.toLowerCase());
  }
  return names.size;
}

/** The meeting's strip tokens (pure; the header draws them). */
export function meetingStripItems(
  meeting: Record<string, unknown>,
  data: Pick<MeetingData, "detail" | "startedAt" | "durationS" | "segments">,
): StatusStripItem[] {
  const { detail, startedAt, durationS, segments } = data;
  const source = detail ?? meeting;
  const runToken = stateToken(source);
  // PHILO-13-04 (A3): a meeting that holds a summary says so, never "SUMMARY
  // OFF" above its own summary (J2-02).
  const stored = Boolean(String(readMeetingIntel(source)?.summary ?? "").trim());
  const summarised = runToken.label === "RAN" || (runToken.label === "OFF" && stored);
  // HS-201-10: `durationToken` says seconds under a minute; no floor.
  const when = [ledgerDate(startedAt), durationS > 0 ? durationToken(durationS) : ""].filter(Boolean).join(" · ");
  // HS-172: the run's seconds from the wire (intel_duration_s), not from
  // proposals.
  const intelDurS = Number(source.intel_duration_s ?? 0);
  const items: StatusStripItem[] = [];
  if (when) items.push({ key: "when", text: when });
  // PHILO-17 speech: the meeting has audio only because the speech model
  // was not on this device. It says so before the summary's word.
  if (speechWasMissing(source)) {
    items.push({ key: "speech", lamp: "fail", text: "NO TRANSCRIPT · SPEECH NOT SET UP", testId: "meeting-speech-missing" });
  }
  if (summarised) {
    items.push({ key: "state", lamp: "ok", text: "SUMMARISED", testId: "meeting-summary-state" });
  } else if (runToken.label === "RUNNING") {
    items.push({ key: "state", lamp: "info", text: "SUMMARY RUNNING", testId: "meeting-summary-state" });
  } else {
    const word: ReactNode = runToken.axis ? `${runToken.axis} ${runToken.label}` : runToken.label;
    items.push({
      key: "state",
      lamp: runToken.tone === "danger" ? "fail" : runToken.tone === "warn" ? "warn" : undefined,
      text: word,
      testId: "meeting-summary-state",
    });
  }
  if (runToken.label === "RAN" && intelDurS > 0) items.push({ key: "intel-dur", text: `${intelDurS} S` });
  // PHILO-15-07 (B01): the record says when its transcript has gaps. The
  // fresh detail is authoritative; the list row speaks only before it loads.
  const unclear = unclearLampLabel(source);
  if (unclear) items.push({ key: "unclear", lamp: "warn", text: unclear, testId: "unclear-lamp" });
  // No host chip in the strip (owner ruling 2026-10-25).
  const people = peopleCount(segments ?? []);
  if (people > 0) items.push({ key: "people", text: `${people} ${people === 1 ? "PERSON" : "PEOPLE"}` });
  return items;
}

/** PHILO-17 (the Today language): where this meeting is, as four steps:
 *  Record, Summary, Decide, Send follow-up. Read from the record: the
 *  capture state, the summary's state and the proposals still to decide. */
export function meetingSteps(
  meeting: Record<string, unknown>,
  data: Pick<MeetingData, "detail" | "ftProposals">,
): Step[] {
  const source = data.detail ?? meeting;
  const token = stateToken(source);
  const stored = Boolean(String(readMeetingIntel(source)?.summary ?? "").trim());
  const recording = token.label === "REC";
  const summarised = token.label === "RAN" || stored;
  const summaryFailed = !summarised && (token.tone === "danger" || token.label === "FAILED");
  const pending = (data.ftProposals ?? []).some(
    (p) => p.state === "proposed" && !p.deferred_until,
  );
  const summary: Step["state"] = recording ? "later" : summarised ? "done" : summaryFailed ? "failed" : "now";
  const decide: Step["state"] = !summarised ? "later" : pending ? "now" : "done";
  const send: Step["state"] = summarised && !pending ? "now" : "later";
  return [
    { key: "record", label: "Record", state: recording ? "now" : "done" },
    { key: "summary", label: "Summary", state: summary },
    { key: "decide", label: "Decide", state: decide },
    { key: "send", label: "Send follow-up", state: send },
  ];
}

/** W2-LIVE-2 (canvas live-direction-2026-10-27, A, After): the record's rail
 *  is Today's four steps (kit MEETING_STEPS: Prep · Record · Summary · Send
 *  follow-up), drawn under the record's toolbar at every state. Prep is done;
 *  Record is now while it records; Summary is now while he reads and decides
 *  (failed when the summary failed); Send follow-up is now when nothing is
 *  left to review. */
export function recordSteps(meeting: Record<string, unknown>, reviewCount: number): Step[] {
  const token = stateToken(meeting);
  const stored = Boolean(String(readMeetingIntel(meeting)?.summary ?? "").trim());
  const recording = token.label === "REC";
  const summarised = token.label === "RAN" || stored;
  const failed = !summarised && (token.tone === "danger" || token.label === "FAILED");
  const sendNow = summarised && reviewCount === 0;
  return [
    { key: "Prep", label: "Prep", state: "done" },
    { key: "Record", label: "Record", state: recording ? "now" : "done" },
    { key: "Summary", label: "Summary", state: recording ? "later" : failed ? "failed" : sendNow ? "done" : "now" },
    { key: "Send follow-up", label: "Send follow-up", state: sendNow ? "now" : "later" },
  ];
}

/** The saved review face keeps the window name in its title bar. This is the
 * one useful fact in the body: pending work, or the current summary state. */
/** What this meeting still asks of him: the legacy needs and the
 *  proposals still to decide (not deferred). */
export function meetingReviewCount(data: Pick<MeetingData, "ftProposals" | "needsCount">): number {
  const legacyPending = Number(data.needsCount ?? 0);
  return (Number.isFinite(legacyPending) ? Math.max(0, legacyPending) : 0)
    + (data.ftProposals ?? []).filter(
      (proposal) => proposal.state === "proposed" && !proposal.deferred_until,
    ).length;
}

export function meetingOutcomeFact(
  meeting: Record<string, unknown>,
  data: Pick<MeetingData, "detail" | "ftProposals" | "needsCount">,
): string {
  const pending = meetingReviewCount(data);
  if (pending > 0) return `${pending} to review`;

  const token = stateToken(data.detail ?? meeting);
  if (token.axis && ["OFF", "SKIPPED", "FAILED", "PARTIAL"].includes(token.label)) {
    return `${token.axis} ${token.label}`;
  }
  if (["CAPTURE FAILED", "RECOVERABLE", "INTERRUPTED", "IMPORT FAILED"].includes(token.label)) {
    return token.label;
  }
  return "Outcomes";
}

/** Steps describe work in progress. A settled Outcomes record uses the
 * compact strip and does not present a static progress ladder. */
export function meetingPipelineActive(
  meeting: Record<string, unknown>,
  data: Pick<MeetingData, "detail">,
): boolean {
  return ["REC", "TRANSCRIBING", "QUEUED", "RUNNING", "IMPORTING"].includes(
    stateToken(data.detail ?? meeting).label,
  );
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

/** `30 MIN` → `30 min`, `OCT 24` → `Oct 24`: the head is quiet sans. */
function quietWord(token: string): string {
  return token
    .replace(/\b([A-Z])([A-Z]+)\b/g, (_, first: string, rest: string) => first + rest.toLowerCase())
    .replace(/\b(MIN|HR|S)\b/gi, (word) => word.toLowerCase());
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

export function MeetingHeader({
  meeting,
  data,
  compact,
  ladder = false,
}: {
  meeting: Record<string, unknown>;
  data: MeetingData;
  /** A settled record: no step ladder (the pipeline is done). */
  compact?: boolean;
  /** The head's own ladder (Record · Summary · Decide · Send follow-up).
   *  Off in the meeting window, which draws Today's rail under its toolbar. */
  ladder?: boolean;
}) {
  const source = data.detail ?? meeting;
  const when = [
    quietWord(ledgerDate(data.startedAt)),
    data.durationS > 0 ? quietWord(durationToken(data.durationS)) : "",
  ].filter(Boolean).join(" · ");
  const unclear = unclearLampLabel(source);
  const people = peopleNames(data.segments ?? []);
  const steps = !compact && meetingPipelineActive(meeting, data);
  return (
    <>
      <div className="meetings-detail-head meeting-head" data-testid="meeting-head">
        <img className="meeting-head-glyph" src={listSprite(objectSprite("meeting", String(meeting.id ?? "")))} alt="" draggable={false} />
        <span className="meetings-detail-facts meeting-head-line">
          {when ? <span className="meeting-head-fact" data-testid="meeting-head-when">{when}</span> : null}
          {speechWasMissing(source) ? (
            <DotWord tone="fail" data-testid="meeting-speech-missing">No transcript · Speech not set up</DotWord>
          ) : null}
          {unclear ? (
            <DotWord tone="warn" data-testid="unclear-lamp">
              {quietWord(unclear.replace(/^WARN · /, "")).toLowerCase()}
            </DotWord>
          ) : null}
          {people.length ? <AvatarStack names={people} data-testid="meeting-head-people" /> : null}
        </span>
      </div>
      {/* W2-LIVE-2: the record's rail (recordSteps) is drawn under its
          toolbar by MeetingRecord; the head keeps this ladder only where a
          host asks for it (`ladder`). */}
      {steps && ladder ? <Steps steps={meetingSteps(meeting, data)} label="Meeting steps" data-testid="meeting-steps" /> : null}
    </>
  );
}
