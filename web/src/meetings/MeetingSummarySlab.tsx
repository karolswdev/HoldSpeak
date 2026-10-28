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
import type { ReactNode } from "react";
import { SurfaceWell } from "../desk/surface/Surface";
import { ReadingDocument } from "../desk/surface/ReadingDocument";
import { RunAttempts } from "./RouteDisclosure";
import type { RunReceipt } from "./summaryRoute";
import { Token } from "../desk/surface/Token";

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

/** PHILO-15-03: the slab is the one owner of the summary text. A face that
 *  has more to say about the run (the Chair's RETRYING/FAILED facts) passes
 *  it as `facts`, under the topics; it never draws the summary itself. */
export function MeetingSummarySlab({
  intel,
  receipt,
  facts,
  reader = false,
}: {
  /** Window grammar (2026-10-24): the meeting window reads its summary as
   *  a document (the one place a document heading is allowed), at a
   *  comfortable measure, edge to edge; other faces keep the well. */
  reader?: boolean;
  intel: MeetingIntel | null;
  receipt: RunReceipt | null;
  facts?: ReactNode;
}) {
  const summary = String(intel?.summary ?? "").trim();
  if (!summary) return null;
  const topics = intel?.topics ?? [];
  if (reader) {
    return (
      <section className="meeting-summary-reader" aria-label="Summary" data-testid="meeting-summary">
        <header className="meeting-summary-reader-head">
          <h2 className="meeting-summary-heading">Summary</h2>
          <RunAttempts receipt={receipt} testId="summary-record-attempts" />
        </header>
        <ReadingDocument className="meeting-summary-document" data-testid="meeting-summary-text">{summary}</ReadingDocument>
        {topics.length > 0 ? (
          <p className="meeting-summary-topics" data-testid="meeting-summary-topics">
            {topics.map((topic, index) => (
              <span key={topic} className="meeting-summary-topic">
                {index > 0 ? <span aria-hidden="true"> · </span> : null}
                {topic.charAt(0).toUpperCase() + topic.slice(1)}
              </span>
            ))}
          </p>
        ) : null}
        {facts ?? null}
      </section>
    );
  }
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
            // PHILO-15 lane 12 (B28): a long topic wraps inside the window
            // (the chip species' wrap variant); it never runs past its edge.
            <Token key={topic} className="surface-token" data-chip data-wrap>
              {topic.toUpperCase()}
            </Token>
          ))}
        </span>
      ) : null}
      {facts ?? null}
    </SurfaceWell>
  );
}
