// HS-201-01 — the ONE thing the meeting path needs.
//
// The product already knows it. A meeting summary runs under the
// `meeting-intel-queue` SERVICE principal, whose route policy permits
// exactly one assignment source -- `capability`
// (`holdspeak/services/inference_service_route_policy.py:43`, refused at
// `:93`; consumed at
// `holdspeak/services/inference_route_plan_service.py:387-390`). So the
// queue reads ONLY the `capability:meeting.deferred_analysis` head, and
// with no head it refuses terminally with `no_assignment`
// (`inference_route_plan_service.py:399-403` -- the very refusal the
// charter walk found in the hub log with nothing on the glass).
//
// `GET /api/inference/assignments` states that fact per capability in
// `task_overrides[]`: `has_override` is literally "an exact
// `capability:<id>` head exists"
// (`holdspeak/services/inference_assignment_service.py:248`), and
// `effective.status` says whether what is there can be used. A group or
// global head does NOT clear the meeting path, so neither may clear the
// row.
import type { AssignmentSummary } from "../../pages/cores/assignmentExperience";

/** The capability that writes a meeting summary. */
export const SUMMARY_CAPABILITY = "meeting.deferred_analysis";

export type MeetingPathBlocker = {
  /** The state, in the product's plainest words. */
  label: string;
  /** The one verb. */
  verb: string;
};

/** The meeting-path blocker, or `null` when nothing blocks it.
 *
 *  `null` for an unread summary too: an unknown is never reported as a
 *  blocker (UX-CANON A.10 -- honest states, never a guess). */
export function meetingPathBlocker(
  summary: AssignmentSummary | null,
): MeetingPathBlocker | null {
  if (!summary) return null;
  const row = (summary.task_overrides ?? []).find(
    (task) => task.id === SUMMARY_CAPABILITY,
  );
  if (!row) return null;
  const usable = row.has_override && row.effective?.status === "assigned";
  if (usable) return null;
  return { label: "No engine for summaries", verb: "Choose an engine" };
}
