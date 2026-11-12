/** One selected need, read and answered in its window. */
import { createContext, useContext } from "react";
import { AgentWords } from "../components/AgentWords";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { refreshNeedsYou } from "../needsYou";
import { openSourceRef } from "../surface/citations";
import { useAgentFlights } from "../agentFlights";
import { questionChoices } from "../agents/choices";
import { InspectorFacts, InspectorForm, PaneActions, PaneInspector, PreferenceWell, StringGadget, SurfaceState, SurfaceCode, SegmentedTabs } from "../surface";
import { SendFace } from "../surface/send";
import { egressOf, previewOf, farSide, wire, failedWord, type Send, type Channel } from "../../features/channels/channels";
import { faceOpener } from "./NeedVerbs";
import { dismissAnswer, fixedAnswers, sendNeed, type NeedAnswer } from "./needActions";
import { followThrough } from "./needsApi";
import { needName, type SelectedNeed } from "./selection";
import { dayWord, tierWord, whenWord, type NeedFace } from "./needsFace";
import { wireDate } from "../surface/format";
import { openCoderSession, openSurfaceOr, openProjectRoom } from "../shell";
import { openPhoneWing } from "../calls/phoneFocus";
import { useDesk } from "../store";
import { recheckSource, useSourceReceipt, type Well, NudgeWell } from "./NeedVerbs";
import { AddToProject } from "../AddToProject";

const ITEM_REF = /^(?:follow-through|action_item|action):(.+)$/;
export function readsInPlace(face: Pick<NeedFace, "verbs" | "openRef" | "proposal">): string | null {
  if (face.verbs.kind !== "work" || face.proposal || (face.openRef && !ITEM_REF.test(face.openRef))) return null;
  return face.verbs.cardId || null;
}
export const ItemReaderContext = createContext<((id: string) => void) | null>(null);
export function useReadInPlace(face: Pick<NeedFace, "verbs" | "openRef" | "proposal">): (() => void) | null {
  const read = useContext(ItemReaderContext), id = readsInPlace(face);
  return read && id ? () => read(id) : null;
}
export function readerFacts(face: NeedFace, now = new Date()): string {
  const v = face.verbs;
  if (v.kind !== "work") return "";
  const since = face.since ? wireDate(face.since) : null;
  return [face.tier ? tierWord(face.tier) : "", v.direction === "theirs" ? v.person || face.personName : "Yours",
    since ? `since ${whenWord(since, now)}` : "", v.due ? `due ${dayWord(v.due) || v.due}` : "", face.origin].filter(Boolean).join(" · ");
}
export type AnswerNeed = (need: SelectedNeed, answer: NeedAnswer) => void;
export interface ItemReaderProps {
  need: SelectedNeed;
  answer: AnswerNeed;
  busy: boolean;
  onBack(): void;
  edit?: Well | null;
  draft: string;
  unsentAnswer?: string;
  onDraftChange(value: string): void;
}
function facts(need: SelectedNeed) {
  const face = need.face;
  const context = face.kind !== "agent" && face.name !== needName(need) && face.verbs.kind === "answer" ? face.name : "";
  return [
    {label: "Brief", value: String(need.item?.brief_words && typeof need.item.brief_words === "object" && "item_brief" in need.item.brief_words ? need.item.brief_words.item_brief : context)},
    {label: "Question", value: face.verbs.kind === "program" ? face.factTitle : face.verbs.kind === "answer" ? <AgentWords text={String(need.item?.question || face.fact)} data-testid="needs-agent-question" /> : ""},
    {label: "From", value: need.from},

    {label: "Evidence", value: need.permissionCommand || face.factCode ? <div data-feedback-redact="true"><SurfaceCode>{need.permissionCommand || face.fact}</SurfaceCode></div> : face.fact && face.verbs.kind !== "answer" ? face.fact : ""},
    {label: "Work", value: readerFacts(face)},
    ...(face.detail ?? []).map((line, index) => ({key: `${index}`, label: line.name, value: line.reason})),
  ];
}
/** The kit has one-primary form completion. Fixed answers compose its facts
 * well and PaneActions; no local form grid, question or control material. */
export function ItemReader({need, answer, busy, onBack, edit, draft, onDraftChange, unsentAnswer}: ItemReaderProps) {
  const {face} = need, v = face.verbs;
  const name = needName(need);
  const details = facts(need).map(row => ({...row, control: row.value})).filter(row => row.value && row.value !== name);
  const typed = v.kind === "answer" && !need.permission && !questionChoices(String(need.item?.question || face.fact)).length;
  const field = edit === "date" ? "Due" : "Owner";
  if (typed || v.kind === "name-owner" && v.cardId || edit === "date" || edit === "owner") {
    const cardId = v.kind === "name-owner" || v.kind === "work" ? v.cardId : null;
    const canSend = typed ? Boolean(need.waitId) : Boolean(cardId);
    const label = typed ? "Send answer" : "Save";
    const send = () => answer(need, {id: "typed", label, keeps: !typed, run: typed && v.kind === "answer"
      ? () => apiFetch(`/api/coders/${encodeURIComponent(v.sessionKey)}/steer`, {method: "POST", json: {text: draft.trim(), submit: true, kind: "answer", wait_id: need.waitId, ...need.waitBinding}})
      : () => followThrough(String(cardId), edit === "date" ? "due" : "delegate", edit === "date" ? {due_at: draft.trim()} : {to: draft.trim()})});
    return <PaneInspector label={name} testId="needs-reader" nameTestId="needs-reader-text"><InspectorForm testId="needs-answer-form" rows={[
      ...details.filter(row => !typed || row.label !== "From"), {label: typed ? "Answer" : field, control: <StringGadget label={typed ? "Answer" : field} value={draft} onChange={onDraftChange} type={edit === "date" ? "date" : "text"} micDraftScope={need.revision + String(edit)} inputProps={typed ? {autoComplete: "off", ...{"data-feedback-redact": "true"}} : undefined} disabled={busy} />},
    ]} completion={{cancel: onBack, primary: {label, disabled: !canSend || !draft.trim() || busy, busy, run: send, testId: "needs-send-answer"}}}
      notice={typed && !canSend ? <PaneActions><span>Read the current question before you answer.</span><Button dense onClick={() => void useAgentFlights.getState().load()}>Read again</Button></PaneActions> : undefined} /></PaneInspector>;
  }
  if (edit === "project" && (v.kind === "confirm" || v.kind === "decide")) return <PaneInspector label={name} testId="needs-reader"><InspectorForm completion={{done: onBack}} rows={[
    ...details, {label: "Project", control: <AddToProject meetingId={v.meetingId} />},
  ]} /></PaneInspector>;
  if (edit === "nudge") return <PaneInspector label={name} testId="needs-reader"><NudgeWell face={face} embedded /></PaneInspector>;
  if (v.kind === "send") return <div className="surface-preference-pane" data-testid="needs-reader" aria-label={name}><PreparedNeed need={need} answer={answer} busy={busy} onBack={onBack} /></div>;
  let choices = fixedAnswers(face);
  if (v.kind === "answer") {
    const send = (body: Record<string, unknown>, path: "keys" | "steer") => () => apiFetch(`/api/coders/${encodeURIComponent(v.sessionKey)}/${path}`, {method: "POST", json: {...body, kind: "answer", wait_id: need.waitId, ...need.waitBinding}});
    choices = need.waitId ? need.permission ? [
      {id: "deny", label: "Deny", run: send({keys: ["Escape"]}, "keys")},
      ...(need.permissionCommand ? [{id: "allow", label: "Allow", run: send({keys: ["Enter"]}, "keys")}] : []),
    ] : questionChoices(String(need.item?.question || face.fact)).map(choice => ({id: choice.n, label: choice.label, run: send({text: choice.n, submit: true}, "steer")})) : [];
  }
  return <PaneInspector label={name} testId="needs-reader" nameTestId="needs-reader-text"><NeedReading need={need} unsentAnswer={unsentAnswer}>
    <PaneActions>{v.kind === "answer" && !need.waitId ? <><span>Read the current question before you answer.</span><Button dense onClick={() => void useAgentFlights.getState().load()}>Read again</Button></> : null}{choices.map((choice, index) => <Button key={choice.id} dense disabled={busy} variant={choice.id === "approve" || choice.id === "allow" || index === 0 && !["gate", "gate-cut"].includes(v.kind) && !need.permission ? "primary" : "secondary"}
      data-testid="needs-answer-choice" data-choice={choice.id} onClick={() => answer(need, choice)}>{choice.label}</Button>)}
      <SourceActions need={need} answer={answer} busy={busy} />
    </PaneActions>
  </NeedReading></PaneInspector>;
}
function NeedReading({need, children, unsentAnswer}: {need: SelectedNeed; children: React.ReactNode; unsentAnswer?: string}) {
  return <><PreferenceWell><InspectorFacts name={needName(need)} rows={[...facts(need), ...(unsentAnswer ? [{label: "Unsent answer", value: <span data-feedback-redact="true">{unsentAnswer}</span>}] : [])]} /></PreferenceWell>{children}</>;
}
function PreparedNeed({need, answer, busy, onBack}: {need: SelectedNeed; answer: AnswerNeed; busy: boolean; onBack(): void}) {
  const v = need.face.verbs;
  if (v.kind !== "send") return null;
  const s = v.send as unknown as Send, channel = String(s.channel || "file") as Channel;
  const preview = previewOf(channel, s.target, s.account, s.preview, s.file_path);
  const url = farSide(channel, s.target, s.account), discard = dismissAnswer(need.face);
  return <SegmentedTabs label="Send to" showSingle value={channel} tabs={[{id:channel,label:channel === "file" ? "Folder" : channel}]} onChange={() => {}}>
    <SendFace destination={{id:v.destinationId,name:s.destination_name ?? "Destination",channel,target:s.target,account:s.account}}
      preview={preview} previewTestId="needs-send-preview" notice={<span>{need.from}{v.state === "failed" ? ` · Not sent · ${failedWord(String(s.reason || "not_sent"))}` : ""}</span>}
      secondary={<>{discard ? <Button dense variant="ghost" disabled={busy} data-testid="needs-send-discard" onClick={() => answer(need,discard)}>Discard</Button> : null}
        {v.state === "failed" ? <Button dense onClick={() => openSourceRef(v.documentRef)}>Open source</Button> : null}
         {v.state === "unknown" ? <Button dense variant="ghost" disabled={busy} onClick={() => answer(need,{id:"check",label:"Checked destination",keeps:true,run:async()=>{if(url)window.open(url,"_blank","noopener");await wire.sends(v.documentRef);}})}>Check</Button> : null}</>}
      completion={v.state === "failed" || v.state === "unknown" && !s.retry_command ? {done:onBack} : {cancel:onBack,cancelDisabled:busy,primary:{label:v.state === "prepared" ? "Send" : "Try again",busy,
        disabled:v.state === "unknown" && !s.retry_command,testId:"needs-send",
        run:()=>answer(need,{id:"send",label:v.state === "prepared" ? "Sent" : "Sent again",run:()=>sendNeed(v)})}}} />
  </SegmentedTabs>;

}

function SourceActions({need, answer, busy}: {need: SelectedNeed; answer: AnswerNeed; busy: boolean}) {
  const face = need.face, v = face.verbs;
  const act = (label: string, run: () => Promise<unknown>, keeps = true) => answer(need, {id: label, label, run, keeps});
  switch (v.kind) {
    case "repair": return <Button dense disabled={busy} title={v.host ? `Checks ${v.host} again` : undefined} onClick={() => {
      if (v.verb === "Retry" && v.watchIds?.length) act("Checked", async () => {const receipt = await recheckSource(face.name, v.watchIds!); useSourceReceipt.getState().set(receipt); if (receipt.tone === "fail") throw new Error(receipt.text);});
      else if (v.verb === "Retry") act("Read again", () => refreshNeedsYou(true));
      else if (v.href.startsWith("/settings")) openSurfaceOr("configure-settings", "/settings", `integration:${v.provider ?? "connections"}`);
      else if (v.projectId) openProjectRoom(v.projectId);
    }}>{v.verb}</Button>;
    case "setup": return <Button dense onClick={() => v.key === "unknown" ? void refreshNeedsYou(true) : openSurfaceOr("open-concierge", "/models", v.key)}>{v.verb}</Button>;
    case "calendar": return <Button dense onClick={() => openSurfaceOr("configure-settings", "/settings", "integration:calendar")}>Connect calendar</Button>;
    case "summarize": return <><AddToProject meetingId={v.meetingId} /><Button dense onClick={() => openSourceRef(`meeting:${v.meetingId}`)}>Summarize</Button></>;
    case "gate-cut": return <Button dense onClick={() => openCoderSession(v.sessionKey, {raw: true})}>Open raw lane</Button>;
    case "arming": return v.failed ? <Button dense onClick={() => void useDesk.getState().startRecording(v.calendarEventId ? {calendarEventId: v.calendarEventId} : undefined)}>Record now</Button> : null;
    case "phone": return v.verbs.some(verb => verb.needs_text) ? <Button dense onClick={() => openPhoneWing(v.msgId)}>Answer here</Button> : null;
    case "answer": return need.permission && !need.permissionCommand ? <Button dense onClick={() => openCoderSession(v.sessionKey, {raw: true})}>Open raw lane</Button> : null;
    case "name-owner": return v.openRef ? <Button dense onClick={() => useDesk.getState().openPullout(v.openRef!)}>Name an owner</Button> : null;
    case "pr": return <Button dense title={v.url} onClick={() => window.open(v.url, "_blank", "noopener")}>Open PR</Button>;
    case "link": return <Button dense title={v.url} onClick={() => window.open(v.url, "_blank", "noopener")}>Open link</Button>;
    case "review": case "session": case "open": case "none": return faceOpener(face) ? <Button dense onClick={() => faceOpener(face)?.()}>Open source</Button> : null;
    default: return null;
  }
}
