/** Existing needs operations, shared by the selection toolbar and its reader. */
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { useGate } from "../gate";
import { acceptDecision } from "../decide";
import { commandForDoorVerb, labelFor, supportsDoorVerb, type DoorVerb } from "../chair/doorVerbs";
import { discardPrepared, sendPrepared, mergeKnown } from "../surface/send";
import { type Send } from "../../features/channels/channels";
import { briefable, deferItem, LATER_TIMES } from "../reach";
import { followThrough, markDone, doneRoute, tomorrowDay } from "./needsApi";
import { cancelArming, useArmingOutcome } from "./arming";
import type { NeedFace } from "./needsFace";

export const PROGRAM_CHOICE_WORDS: Record<string, string> = {
  merge: "Merge", not_yet: "Not yet", fix_now: "Fix now", later: "Make a task", skip: "Skip", resume: "Resume", prepare: "Send…",
  continue: "Continue", wait: "Wait", met: "Met", unmet: "Unmet", send_back: "Send back", done: "Done", cant: "Can't do it",
  go_on: "Go on", park: "Park", pick: "Pick", add: "Add", apply: "Apply", send: "Send", allow: "Allow the commit", not_now: "Not now",
  file: "File", make: "Make", keep_program: "Keep for this program", keep_repo: "Keep for HoldSpeak", close: "Close",
};
export function programDecideBody(v: Extract<NeedFace["verbs"], {kind: "program"}>, choice: string) {
  return { kind: v.itemKind, choice, ...(v.commitBinding ? {expected_commit_binding: v.commitBinding} : {}), ...(v.findingId ? {finding_id: v.findingId} : {}), ...(v.lessonId != null ? {lesson_id: v.lessonId} : {}) };
}
export interface NeedAnswer {
  id: string;
  label: string;
  run(): Promise<unknown>;
  destructive?: boolean;
  /** Navigation, preparation and checks keep the row. */
  keeps?: boolean;
}
const post = (path: string, json?: unknown) => () => apiFetch(path, {method: "POST", ...(json === undefined ? {} : {json})});
export function fixedAnswers(face: NeedFace): NeedAnswer[] {
  const v = face.verbs;
  switch (v.kind) {
    case "program": return v.choices.map(choice => ({id: choice, label: PROGRAM_CHOICE_WORDS[choice] ?? choice.replaceAll("_", " "),
      run: post(v.decide, programDecideBody(v, choice)), destructive: ["park", "skip", "close"].includes(choice), keeps: choice === "prepare"}));
    case "gate": return [
      {id: "deny", label: "Deny", run: () => useGate.getState().decide(v.proposalId, "denied")},
      {id: "approve", label: "Approve", run: () => useGate.getState().decide(v.proposalId, "approved")},
    ];
    case "gate-cut": return [{id: "deny", label: "Deny", run: () => useGate.getState().decide(v.proposalId, "denied")}];
    case "allow-helper": return [{id: "allow-helper", label: "Allow helper", run: post(`/api/agent/launches/${encodeURIComponent(v.launchId)}/helper/allow`, {request_id: v.requestId})}];
    case "work": return [{id: "done", label: "Done", run: () => markDone(v)}];
    case "decision-confirm": return [{id: "confirm", label: "Confirm", run: () => acceptDecision(v.decisionId)}];
    case "confirm": case "decide": return [
      {id: "confirm", label: v.kind === "decide" ? "Accept" : "Confirm", run: post(`/api/proposals/${encodeURIComponent(v.proposalId)}/confirm`)},
      ...laterAnswers(face),
      ...(dismissAnswer(face) ? [dismissAnswer(face)!] : []),
    ];
    case "whose": return v.speakers.map(owner => ({id: owner, label: owner, run: post(`/api/proposals/${encodeURIComponent(v.proposalId)}/confirm`, {owner})}));
    case "door": {
      const verb = v.card.lawful_verbs?.find(x => supportsDoorVerb(x as DoorVerb)) as DoorVerb | undefined;
      const cmd = verb && commandForDoorVerb(verb);
      return verb && cmd ? [{id: "door", label: labelFor(verb), destructive: verb.arguments.verb === "dismiss" || verb.arguments.status === "killed",
        run: verb.arguments.verb === "done" && doneRoute(v) ? () => markDone(v) : post(cmd.endpoint, cmd.body)}] : [];
    }
    case "hub": return v.verbs.map(verb => ({id: verb.id, label: verb.label, run: () => apiFetch(verb.href, {method: verb.method || "POST", json: verb.body ?? {}})}));
    case "phone": return v.verbs.filter(verb => !verb.needs_text).map(verb => ({id: verb.id, label: verb.label,
      run: () => apiFetch(verb.href, {method: verb.method || "POST", json: verb.body ?? {}})}));
    case "arming": return v.failed ? [] : [{id: "cancel-recording", label: v.refused ? "Retry cancel" : "Cancel recording", run: async () => {
      await cancelArming(v.scheduleId);
      const refusal = useArmingOutcome.getState().refusal;
      if (refusal?.scheduleId === v.scheduleId) throw new Error("Could not cancel · Nothing changed");
    }}];
    default: return [];
  }
}
export function laterAnswers(face: NeedFace): NeedAnswer[] {
  const v = face.verbs;
  if (v.kind === "work") return [{id: "tomorrow", label: "Tomorrow", run: () => followThrough(v.cardId, "snooze", {until: tomorrowDay()})}];
  if (v.kind === "program" && v.ref && briefable(v.itemKind) && !v.later) return LATER_TIMES.map(time => ({id: time.id, label: time.label, run: () => deferItem(String(v.ref), time.id)}));
  if (v.kind === "confirm" || v.kind === "decide") return [{id: "defer", label: "Not now", run: post(`/api/proposals/${encodeURIComponent(v.proposalId)}/defer`, {})}];
  return [];
}
export function dismissAnswer(face: NeedFace): NeedAnswer | null {
  const v = face.verbs;
  if (v.kind === "door") {
    const verb = v.card.lawful_verbs?.find(x => x.arguments?.verb === "dismiss" && supportsDoorVerb(x as DoorVerb)) as DoorVerb | undefined;
    const command = verb && commandForDoorVerb(verb);
    if (command) return {id: "dismiss", label: "Dismiss", destructive: true, run: post(command.endpoint, command.body)};
  }
  if (v.kind === "work") return {id: "dismiss", label: "Dismiss", destructive: true, run: () => followThrough(v.cardId, "dismiss")};
  if (["confirm", "decide", "whose"].includes(v.kind) && "proposalId" in v) return {id: "dismiss", label: "Dismiss", destructive: true,
    run: post(`/api/proposals/${encodeURIComponent(v.proposalId)}/dismiss`)};
  if (v.kind === "send" && v.state === "prepared") return {id: "discard", label: "Discard", destructive: true, run: () => discardPrepared(v.sendId)};
  return null;
}
/** The shared send adapter retains the command through an unknown answer. Its
 * promise also resolves on refusal, so only the stored send proves completion. */
export async function sendNeed(v: Extract<NeedFace["verbs"], {kind: "send"}>): Promise<Send> {
  if (v.state === "failed") throw new Error("Not sent · Open source and take a new preview");
  const s = v.send as unknown as Send;
  await sendPrepared(v.documentRef, v.sendId, undefined, undefined, v.state === "unknown" ? s.retry_command : undefined);
  const rows = mergeKnown(v.documentRef, []);
  const result = rows.find(row => row.id === v.sendId);
  if (result?.state !== "sent") throw new Error(result?.state === "failed" ? "Not sent · Try again" : "Send not confirmed · Check the destination before you try again");
  return result;
}

/** Authority refusals use the owner's words, never a wire key. */
export function needFailure(error: unknown): string {
  const body = error instanceof ApiError ? error.payload as {status?: string; detail?: {status?: string}} | null : null;
  const status = body?.status || body?.detail?.status;
  if (status === "wait_not_current") return "The question changed · Nothing was sent";
  if (status === "pane_mismatch") return "The agent's terminal changed · Nothing was sent";
  if (["pane_gone", "target_gone"].includes(status || "")) return "The agent's terminal is gone · Nothing was sent";
  if (status === "tmux_absent") return "The terminal is not running · Nothing was sent";
  return readableError(error);
}
