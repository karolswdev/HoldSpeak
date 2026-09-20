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
import { SurfaceWell } from "../desk/surface/Surface";
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

export function MeetingSummarySlab({
  intel,
  receipt,
}: {
  intel: MeetingIntel | null;
  receipt: RunReceipt | null;
}) {
  const summary = String(intel?.summary ?? "").trim();
  if (!summary) return null;
  const topics = intel?.topics ?? [];
  return (
    <SurfaceWell
      head={
        <span className="summary-well-head">
          <span>SUMMARY</span>
          <RunAttempts receipt={receipt} testId="summary-record-attempts" />
        </span>
      }
    >
      <p className="summary-text" data-testid="meeting-summary-text">
        {summary}
      </p>
      {topics.length > 0 ? (
        <span className="summary-topics" data-testid="meeting-summary-topics">
          {topics.map((topic) => (
            <span key={topic} className="surface-token" data-chip>
              {topic.toUpperCase()}
            </span>
          ))}
        </span>
      ) : null}
    </SurfaceWell>
  );
}
