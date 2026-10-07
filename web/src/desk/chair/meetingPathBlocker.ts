// HS-201-01 — the ONE thing the meeting path needs.
//
// The product already knows it. A meeting summary runs under the
// `meeting-intel-queue` SERVICE principal. Its sealed route policy
// (`meeting-intel-queue@2`, `builtin_service_route_policy_registry` in
// `holdspeak/services/inference_service_route_policy.py`) reads the exact
// `capability:meeting.deferred_analysis` head AND the owner's group and
// global heads ("Default for AI work").
//
// PHILO-15 01: the row does not copy that rule. `GET
// /api/inference/assignments` states the policy's answer per capability in
// `task_overrides[].queue` (`InferenceAssignmentService._queue_projection`):
// `queue.status` is "assigned" when the queue would run a summary now.
import type { AssignmentSummary } from "../../pages/cores/assignmentExperience";

/** The capability that writes a meeting summary. */
export const SUMMARY_CAPABILITY = "meeting.deferred_analysis";

/** The capability that turns admitted audio into text. */
export const SPEECH_CAPABILITY = "speech.transcribe";

/** How the assignment roster read went.
 *
 *  Counsel fix round (Astra finding 3): `pending` and `failed` are both
 *  UNKNOWN -- the Chair knows nothing about the meeting path -- and an
 *  unknown is never drawn as a clear desk (UX-CANON A10). */
export type AssignmentRead = "pending" | "failed" | "ok";

export type MeetingPathBlocker = {
  /** Which fact the row states. */
  key: "engines" | "summary" | "speech" | "unknown";
  /** The state, in the product's plainest words. */
  label: string;
  /** The one verb. */
  verb: string;
};

/** Every meeting-path blocker the roster states, in path order.
 *
 *  An empty list means nothing blocks the path. The rows:
 *
 *  - `unknown` -- the read FAILED. One row, one verb that re-reads it. A
 *    read still in flight draws NOTHING (counsel fix round, second pass,
 *    ruling 1): the desk is quiet on every arrival, and the Chair keeps
 *    the all-clear off the headline until the roster lands.
 *  - `engines` -- NEITHER half of the path has an engine. That is one
 *    state, so it is one row with one filled Button (ruling 2: one
 *    filled primary on the face).
 *  - `speech` -- nothing turns the recorded audio into text. ANY
 *    effective assignment clears it: an owner-started recording resolves
 *    `speech.transcribe` through the ordinary inheritance chain
 *    (`inference_service_route_policy.py:198-224` names the capability
 *    only for the SERVICE-fired wake and scheduled paths).
 *  - `summary` -- nothing writes the summary. The row asks the
 *    meeting-intel queue's route policy through `queue.status`: a
 *    capability, group or global head the queue may read clears it
 *    (`meeting-intel-queue@2`), and so does the owner's own OFF
 *    (`queue.status: "off"`): no summary runs, and nothing asks for one.
 *
 *  A capability the roster does not carry is left alone: absence of a
 *  row is not evidence of an absent engine. */
export function meetingPathBlockers(
  summary: AssignmentSummary | null,
  read: AssignmentRead = "ok",
): MeetingPathBlocker[] {
  if (read === "pending") return [];
  if (read === "failed" || !summary) {
    return [{ key: "unknown", label: "Could not read setup", verb: "Try again" }];
  }
  const tasks = summary.task_overrides ?? [];
  const row = (id: string) => tasks.find((task) => task.id === id);
  const verb = "Choose an engine";

  const speech = row(SPEECH_CAPABILITY);
  const speechMissing = Boolean(speech) && speech!.effective?.status !== "assigned";
  const analysis = row(SUMMARY_CAPABILITY);
  // The queue's own answer; a roster without it falls back to the owner chain.
  // `off` is the owner's own choice (PHILO-15 01 ruling): no row asks.
  const summaryStatus = analysis
    ? (analysis.queue ? analysis.queue.status : analysis.effective?.status)
    : undefined;
  const summaryMissing =
    Boolean(analysis) && summaryStatus !== "assigned" && summaryStatus !== "off";

  if (speechMissing && summaryMissing) {
    return [{ key: "engines", label: "No engine yet", verb }];
  }
  const blockers: MeetingPathBlocker[] = [];
  if (speechMissing) blockers.push({ key: "speech", label: "No engine for speech", verb });
  if (summaryMissing) blockers.push({ key: "summary", label: "No engine for summaries", verb });
  return blockers;
}
