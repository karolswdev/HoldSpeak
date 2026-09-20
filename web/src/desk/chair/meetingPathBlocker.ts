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
 *  - `summary` -- nothing writes the summary. Only an exact
 *    `capability:meeting.deferred_analysis` head clears it: the
 *    meeting-intel queue is a SERVICE principal, and its route policy
 *    permits exactly one assignment source -- `capability`
 *    (`inference_service_route_policy.py:43`, refused at `:93`). A group
 *    or global head does NOT clear the meeting path, so it may not clear
 *    the row.
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
  const summaryMissing =
    Boolean(analysis) &&
    !(analysis!.has_override && analysis!.effective?.status === "assigned");

  if (speechMissing && summaryMissing) {
    return [{ key: "engines", label: "No engine yet", verb }];
  }
  const blockers: MeetingPathBlocker[] = [];
  if (speechMissing) blockers.push({ key: "speech", label: "No engine for speech", verb });
  if (summaryMissing) blockers.push({ key: "summary", label: "No engine for summaries", verb });
  return blockers;
}
