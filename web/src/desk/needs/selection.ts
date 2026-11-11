import {waitBindingOf, type WaitBinding} from "../agents/waitBinding";
/** The selected need and the saved work its answer names. No clock or list rank is a revision. */
import type { CoderSessionRow } from "../agentFlights";
import type { NeedsYouRoomItem } from "../needsYou";
import type { NeedFace } from "./needsFace";
import { agentName, whenWord } from "./needsFace";
import { wireDate } from "../surface/format";

export interface SelectedNeed {
  face: NeedFace;
  item?: NeedsYouRoomItem;
  revision: string;
  waitId?: string;
  waitBinding?: WaitBinding;
  permission?: boolean;
  permissionCommand?: string;
  from: string;
  when: string;
}
export function selectedNeed(face: NeedFace, items: readonly NeedsYouRoomItem[], now = new Date(), sessions: readonly CoderSessionRow[] = []): SelectedNeed {
  const object = items.find(row => String(row.id ?? row.ref) === face.id || String(row.ref) === face.memberRef);
  // A folded ask keeps the work's row identity and the ask's authority.
  const ask = face.verbs.kind === "answer" ? items.find(row => row.source === "coder" && row.sessionKey === face.askOf)
    : face.verbs.kind === "gate" || face.verbs.kind === "gate-cut" ? items.find(row => row.source === "gate" && String(row.ref ?? row.id) === `gate:${"proposalId" in face.verbs ? face.verbs.proposalId : ""}`) : undefined;
  const item = ask ?? object;
  const at = wireDate(String(item?.since ?? face.since ?? face.arrival?.startedAt ?? ""));
  const session = face.verbs.kind === "answer" ? sessions.find(row => row.key === (face.verbs.kind === "answer" ? face.verbs.sessionKey : "")) : undefined;
  const raw = session?.raw.session as Record<string, unknown> | undefined;
  const binding = item?.waitBinding as Record<string, unknown> | undefined;
  const waitId = binding?.wait_id ? String(binding.wait_id) : raw?.wait_started_at === item?.waitStartedAt ? String(raw?.wait_id || "") : "";
  const permission = item?.waitKind === "approve";
  const waitBinding = waitBindingOf(binding);
  const permissionCommand = permission && item?.waitCommandComplete === true ? String(item.waitCommand || "") || undefined : undefined;
  const verbs = face.verbs.kind === "send" ? {...face.verbs, send: {
    id: face.verbs.sendId, state: face.verbs.state, payload_digest: face.verbs.send.payload_digest,
    target_digest: face.verbs.send.target_digest, prepare_operation_id: face.verbs.send.prepare_operation_id,
    send_operation_id: face.verbs.send.send_operation_id, retry_command: face.verbs.send.retry_command,
  }} : face.verbs;
  const revision = revisionToken(JSON.stringify([face.id, waitId, waitBinding, permission, permissionCommand, item?.revision, item?.updated_at, item?.updatedAt, item?.notifyKey,
    item?.waitStartedAt, face.name, face.uncounted, item?.dueAt, item?.later, verbs, face.factTitle, item?.question, item?.command, item?.program, item?.brief_words, item?.evidence, item?.argsCut, item?.holdReason, face.detail]));
  return { face, item, revision, waitId, waitBinding, permission, permissionCommand,
    from: face.project?.name || (face.agent ? agentName(face.agent) : "") || String(item?.group || item?.projectName || item?.preparedBy || "") ||
      (face.agent ? agentName(face.agent) : face.personName || String(item?.meetingTitle || "") || face.origin || "HoldSpeak"),
    when: at ? whenWord(at, now) : "" };
}
export function needName(need: SelectedNeed): string {
  const {face} = need;
  if (face.verbs.kind === "program") {
    const brief = need.item?.brief_words as {item_brief?: string} | undefined;
    const question = String(brief?.item_brief || need.item?.title || face.factTitle || face.name);
    return question.replace(/\s*\([^)]*\/[^)]*\)/g, "").replace(/(?:[\w.-]+\/)+[\w.-]+\.\w+/g, "a file");
  }
  if (face.verbs.kind === "answer") return String(need.item?.question || face.fact || face.name);
  if (face.verbs.kind === "gate" || face.verbs.kind === "gate-cut") return "Allow a command?";
  return face.name;
}
export function waitsOnOwner(face: NeedFace): boolean {
  return !face.uncounted && face.direction !== "theirs";
}
/** An opaque local change token, never a hub authority precondition. Do not
 * retain command/evidence/payload strings as completed-history or draft keys. */
function revisionToken(text: string): string {
  let a = 0xcbf29ce484222325n, b = 0x6c62272e07bb0142n;
  for (let i=0; i<text.length; i++) {
    a = BigInt.asUintN(64, (a ^ BigInt(text.charCodeAt(i))) * 0x100000001b3n);
    b = BigInt.asUintN(64, (b ^ BigInt(text.charCodeAt(i))) * 0x100000001b3n);
  }
  return a.toString(16) + b.toString(16);
}
export type NeedSource = {ref: string} | {projectId: string; proposalId: string};
export interface AnsweredNeed {id: string; name: string; answer: string; at: string; from: string; source: NeedSource | null}
export function answeredRecord(need: SelectedNeed, answer: string, at: string): AnsweredNeed {
  const {face} = need;
  const source = face.proposal ? {projectId: face.proposal.projectId, proposalId: face.proposal.proposalId} : face.verbs.kind === "send" ? {ref: face.verbs.documentRef} : face.verbs.kind === "session" || face.verbs.kind === "answer"
    ? {ref: `coder:${face.verbs.sessionKey}`} : face.openRef ? {ref: face.openRef} : null;
  return {id: `${face.id}:${at}`, name: needName(need), answer, at, from: need.from, source};
}
