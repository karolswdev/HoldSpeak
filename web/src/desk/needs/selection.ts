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
  const waitId = raw?.wait_started_at === item?.waitStartedAt ? String(raw?.wait_id || "") : "";
  const permission = item?.waitKind === "approve";
  const permissionCommand = permission && session?.screen?.state === "approve" ? session.screen.command || undefined : undefined;
  const verbs = face.verbs.kind === "send" ? {...face.verbs, send: {
    id: face.verbs.sendId, state: face.verbs.state, payload_digest: face.verbs.send.payload_digest,
    target_digest: face.verbs.send.target_digest, prepare_operation_id: face.verbs.send.prepare_operation_id,
    send_operation_id: face.verbs.send.send_operation_id, retry_command: face.verbs.send.retry_command,
  }} : face.verbs;
  const revision = JSON.stringify([face.id, waitId, permission, permissionCommand, item?.revision, item?.updated_at, item?.updatedAt, item?.notifyKey,
    item?.waitStartedAt, face.name, face.uncounted, item?.dueAt, item?.later, verbs, face.factTitle, item?.question, item?.command, item?.program, item?.brief_words, item?.evidence, item?.argsCut, item?.holdReason, face.detail]);
  return { face, item, revision, waitId, permission, permissionCommand,
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
export type AnsweredNeed = SelectedNeed & { answer: string; at: string };
