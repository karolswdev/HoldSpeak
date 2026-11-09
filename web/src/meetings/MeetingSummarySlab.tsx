/** HS-201-04 — the summary is shown on the record, with its meeting.
 *
 *  The hub persists it (`intel_snapshots.summary`,
 *  holdspeak/kernel/meeting_plugin_projection.py:274) and the meeting
 *  detail read model carries it as `intel.summary` with `intel.topics`
 *  (holdspeak/db/meetings.py:558, holdspeak/meeting_session/models.py:215).
 *  Until now only the desk pullout rendered it; the Meetings record — the
 *  place the owner lands from the Chair and from the ledger — did not.
 *
 *  The well's head carries the destinations actually contacted, from the
 *  run receipt (Article III: the truth AFTER the run, never composed from
 *  configuration).
 */
import { RunAttempts } from "./RouteDisclosure";
import type { RunReceipt } from "./summaryRoute";

export interface MeetingIntel {
  summary?: string | null;
  topics?: string[] | null;
}

/** Read `intel` off a meeting detail payload. */
export function readMeetingIntel(source: unknown): MeetingIntel | null {
  if (!source || typeof source !== "object") return null;
  const intel = (source as Record<string, unknown>).intel;
  if (!intel || typeof intel !== "object") return null;
  const row = intel as Record<string, unknown>;
  const topics = Array.isArray(row.topics)
    ? row.topics.map((topic) => String(topic)).filter(Boolean)
    : [];
  return {
    summary: row.summary == null ? null : String(row.summary),
    topics,
  };
}

/** The language (2026-11-08; owner 2026-10-31, "the brief IS the page"):
 *  the summary is one plain paragraph at the head of the meeting's ledger,
 *  no slab, no tint. Its topics and the run's attempts are one mono line
 *  under it. */
export function MeetingSummary({ intel, receipt }: { intel: MeetingIntel | null; receipt: RunReceipt | null }) {
  const summary = String(intel?.summary ?? "").trim();
  if (!summary) return null;
  const topics = (intel?.topics ?? []).map((topic) => topic.charAt(0).toUpperCase() + topic.slice(1));
  return (
    <div className="mt-ledger-summary" data-testid="meeting-summary">
      <p className="mt-ledger-summary-text" data-testid="meeting-summary-text">{summary}</p>
      <p className="mt-ledger-summary-facts">
        {topics.length ? <span data-testid="meeting-summary-topics">{topics.join(" · ")}</span> : null}
        <RunAttempts receipt={receipt} testId="summary-record-attempts" />
      </p>
    </div>
  );
}
