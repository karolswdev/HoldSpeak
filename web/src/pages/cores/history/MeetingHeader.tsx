// HS-172 — the detail header. Phase 16 (the interior kit; the canvas window
// "Cutover sync"): the meeting's title is the window's ONE big fact (the
// AppHead), and its facts are the StatusStrip on the same baseline:
// `TUE 14:00 · 42 MIN` · the summary's state (a lamp + its word) · the
// run's seconds and its egress chip · the transcript's gaps · `4 PEOPLE`.
import type { ReactNode } from "react";
import { AppHead, StatusStrip, type StatusStripItem } from "../../../desk/surface";
import { ledgerDate, durationToken, stateToken, unclearLampLabel } from "./helpers";
import { EgressChip } from "../../../desk/surface/gadgets";
import { egressFor } from "../../../desk/surface/egress";
import type { MeetingData } from "./useMeetingData";
import { readMeetingIntel } from "../../../meetings/MeetingSummarySlab";

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
  // HS-172: the run's seconds and host from the wire (intel_duration_s,
  // intel_model_host), not from proposals.
  const intelDurS = Number(source.intel_duration_s ?? 0);
  const rawHost = String(source.intel_model_host ?? "") || null;
  const items: StatusStripItem[] = [];
  if (when) items.push({ key: "when", text: when });
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
  // Egress where egress happened: the summary's host, for RAN, RUNNING, QUEUED.
  if (["RAN", "RUNNING", "QUEUED"].includes(runToken.label) && rawHost) {
    const eg = egressFor(rawHost);
    items.push({ key: "intel-host", text: <EgressChip label={eg.label} scope={eg.scope} /> });
  }
  const people = peopleCount(segments ?? []);
  if (people > 0) items.push({ key: "people", text: `${people} ${people === 1 ? "PERSON" : "PEOPLE"}` });
  return items;
}

export function MeetingHeader({
  meeting,
  data,
  compact,
}: {
  meeting: Record<string, unknown>;
  data: MeetingData;
  /** HS-200-12: on the review wing the display line belongs to the
   *  review (`5 to review`) and the meeting's name is in the window title
   *  bar (the subject, said once); the strip keeps only the facts. */
  compact?: boolean;
}) {
  const title = String(data.detail?.title ?? meeting.title ?? "Meeting");
  const strip = <StatusStrip className="meetings-detail-facts" items={meetingStripItems(meeting, data)} />;
  if (compact) {
    return (
      <div className="meetings-detail-head" data-compact>
        {strip}
      </div>
    );
  }
  return (
    <AppHead className="meetings-detail-head" fact={title} as="div">
      {strip}
    </AppHead>
  );
}
