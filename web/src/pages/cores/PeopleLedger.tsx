/* A person's ledger keeps its write attempts while the View pop-up changes the reading seat. */
import { useEffect, useRef, useState, type ReactNode } from "react";
import { ActionNotice, CycleGadget, InspectorBody, InspectorFacts, InspectorForm, InspectorQuestion, ListPane, ListView, PadGadget, PaneInspector, PreferencePane, StatusBar, SurfaceState, type ListVerb, type ObjectListRow } from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { ApiError } from "../../lib/api";
import * as hub from "../../desk/people/api";
import { refOpener } from "../../desk/openObject";
import { composePeoplePrep } from "../../desk/people/prepData";
import { keptDraft, useDeskDraft } from "../../desk/deskMemory";
import { useDesk } from "../../desk/store";
import { useDeskWriteReceipt } from "../../desk/hooks/useWriteReceipt";
import { nudgeText } from "../../desk/needs/NeedsDrawer";
import { NoteSendWells } from "../../desk/documentSendsLazy";
import { personPages, useStandingPages } from "../../desk/standingPages";
import { personProgramsOf } from "../../desk/programs/PersonPrograms";
import { openProgram } from "../../desk/programs/open";
import { wireWords } from "../../desk/surface/words";
import { Readiness, Session, Commitment, OneOnOneBrief, RelationshipDetail, stateOf, isStoreOutage, isProtectedFailure, OweAttempt, CREATE_NO_EFFECT, ACCEPT_NO_EFFECT, failureCode, isAuthOrKeyFailure, checkSavedRequest, oneOnOneWhen, shortDay, lowerDay, PrepNext, untilWords, isOverdue, dayLabel } from "./peopleModel";
import { CommitmentInspector } from "./PeopleLinks";
export type PersonView = "ledger" | "links" | "brief" | "agenda";

type RecordRow = ObjectListRow & { text?:string; meta?:string; source?:()=>void; inspect?:Commitment; done?:()=>void; accept?:()=>void; nudge?:()=>void; event?:{uid:string;source_id:string;title:string}; testId?:string; side?:string };
function PrepNudge({task,person,due,onClose}:{task:string;person:string;due:string|null;onClose():void}) {
  const [note,setNote]=useState<{id:string;title:string}|null>(null),[failed,setFailed]=useState(false),[attempt,retry]=useState(0);
  const text=nudgeText(task,person,due);
  useEffect(()=>{let live=true;setFailed(false);const title=`Nudge: ${task}`;void hub.keepNudge(title,text).then(made=>{if(live){const id=String(made.note?.id??"");if(id)setNote({id,title});else setFailed(true);}}).catch(()=>{if(live)setFailed(true);});return()=>{live=false;};},[task,text,attempt]);
  if(note)return <NoteSendWells id={note.id} title={note.title} onBack={onClose}/>;
  return <InspectorFacts name="Nudge" header={false} data-feedback-redact="true" rows={[{label:"Message",value:<span data-testid="prep-nudge-text">{text}</span>}]} testId="prep-nudge"
    notice={failed?<ActionNotice role="alert" tone="danger" action={{label:"Try again",onClick:()=>retry(n=>n+1)}}>The message could not be prepared; nothing changed, try again.</ActionNotice>:<SurfaceState loading/>}/>;
}
function OweReceipt({attempt}:{attempt:OweAttempt}) {
  if(attempt.phase==="creating"||attempt.phase==="accepting")return null;
  const words=attempt.phase==="saved"?attempt.saved.body:attempt.body;
  const message=attempt.phase==="saved"?(attempt.saved.state==="open"?"Saved":`Saved · ${wireWords(attempt.saved.state)}`):attempt.phase==="creation_uncertain"?"The promise may be saved. Look in the list before you add it again.":attempt.phase==="acceptance_uncertain"?attempt.note:"Checking saved request";
  return <ActionNotice tone={attempt.phase==="saved"?"ok":"warn"}><span data-testid="people-owe-receipt" data-phase={attempt.phase}>{message} · <span data-feedback-redact="true" data-testid="people-owe-submitted">{words}</span></span></ActionNotice>;
}
export function PeopleLedger({relationship,onRefresh,onProtectedFailure,onNext,composerRequest,view="ledger",links,issue=""}:{relationship:RelationshipDetail;onRefresh():void;onProtectedFailure(cause:unknown,mayHaveSaved?:boolean):void;onNext?(next:PrepNext):void;composerRequest?:number;view?:PersonView;links?:ReactNode;issue?:string}) {
  const [picked,setPicked]=useState<string|null>(null),[briefPicked,setBriefPicked]=useState<string|null>(null),[agendaPicked,setAgendaPicked]=useState<string|null>(null);
  const [composing,setComposing]=useState(true),[agendaAdding,setAgendaAdding]=useState(false),[removing,setRemoving]=useState<string|null>(null);
  const pages=useStandingPages("desk");
  const [brief, setBrief] = useState<OneOnOneBrief | null>(null);
  const [failure, setFailure] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState<string | null>(null);
  const recordingState = useDesk((state) => state.recording);
  const { failure: recordingFailure, receipt: recordingReceipt } = useDeskWriteReceipt();
  const [selectedCommitment, setSelectedCommitment] = useState<{ commitment: Commitment } | null>(null);
  const commitmentOrigin = useRef<HTMLElement | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [preparedAt] = useState(() => new Date().toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false }));
  // The person's record is re-read after each write; the brief follows it.
  // A failed brief read is a state: it stays on screen until Try again (a
  // new `attempt`); a quiet re-read of the record never erases it
  // (peoplePrepB4: "a failed brief read is a named failure with Try again").
  const failedAt = useRef<{ attempt: number; id: string } | null>(null);
  useEffect(() => {
    if (failedAt.current?.attempt === attempt && failedAt.current.id === relationship.id) return;
    failedAt.current = null;
    let live = true;
    void hub.readBrief<OneOnOneBrief>(relationship.id)
      .then((result) => { if (live) { setBrief(result.brief ?? ({ open_commitments: [], agenda_items: [] } as unknown as OneOnOneBrief)); setFailure(""); } })
      .catch((cause) => {
        if (!live) return;
        if (isProtectedFailure(cause) && !isStoreOutage(cause)) { onProtectedFailure(cause); return; }
        failedAt.current = { attempt, id: relationship.id };
        setFailure("Could not load the prep · Nothing changed · Try again");
      });
    return () => { live = false; };
  }, [relationship, attempt]); // eslint-disable-line react-hooks/exhaustive-deps
  // The countdown ticks; the words change in a fixed box.
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);
  const [agendaDraft, setAgendaDraft, forgetAgenda] = useDeskDraft(`people/1on1/${relationship.id}`);
  const [oweDraft, setOweDraftRaw, forgetOwe] = useDeskDraft(`people/request/${relationship.id}`);
  // HS-S33: the I owe attempt. The ref is the synchronous guard (a second
  // Enter cannot start a second request); the state draws it.
  const oweRef = useRef<OweAttempt | null>(null);
  const [owe, setOweState] = useState<OweAttempt | null>(null);
  const setOwe = (next: OweAttempt | null) => { oweRef.current = next; setOweState(next); };
  const oweSeq = useRef(0);
  const oweEdits = useRef(0);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; oweRef.current = null; }; }, []);
  const setOweDraft = (value: string) => { oweEdits.current += 1; setOweDraftRaw(value); };
  const [owedDraft, setOwedDraft, forgetOwed] = useDeskDraft(`people/owed/${relationship.id}`);
  const [noteDraft, setNoteDraft, forgetNote] = useDeskDraft(`people/context/${relationship.id}/body`);
  const [visibility, setVisibility, forgetVisibility] = useDeskDraft(`people/context/${relationship.id}/visibility`);
  const [savedKind, setComposeKind] = useDeskDraft(`people/compose/${relationship.id}`);
  const composeKind = savedKind || "agenda";
  useEffect(() => {
    if (!composerRequest) return;
    setComposeKind("note"); setComposing(true);
  }, [composerRequest, Boolean(brief || failure)]);
  // Betterment D7: Nudge on her row prepares a message; he presses Send.
  const [nudging, setNudging] = useState<{ id: string; task: string; due: string | null } | null>(null);
  const toggleNudge = (row: { id: string; task: string; due: string | null }) => setNudging((current) => (current?.id === row.id ? null : row));

  useEffect(() => {
    const event = brief ? composePeoplePrep(brief).nextOneOnOne ?? null : null;
    const last = brief?.last_time?.one_on_one ? brief.last_time.started_at : null;
    onNext?.({ at: relationship.next_one_on_one ?? event?.starts_at ?? null, eventId: event?.id ?? null, last });
  }, [brief, relationship.next_one_on_one, onNext]);

  const closeCommitment = () => {
    setSelectedCommitment(null);
    commitmentOrigin.current?.focus();
  };
  const run = async (key: string, work: () => Promise<unknown>, after?: () => void) => {
    setBusy(key);
    try { await work(); after?.(); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(null); }
  };
  const addAgenda = (onSaved?: () => void) => {
    const submitted = agendaDraft;
    const body = submitted.trim(); if (!body || busy === "agenda") return;
    void run("agenda", async () => {
      const session = relationship.sessions?.[0] ?? (await hub.createOneOnOne<Session>(relationship.id)).one_on_one;
      await hub.addAgendaItem(session.id, body);
    }, () => { if ((keptDraft(`people/1on1/${relationship.id}`) ?? "") === submitted) { forgetAgenda(); onSaved?.(); } });
  };
  // What he owes: the hub's own path (a request he accepts becomes his
  // commitment). HS-S33: two writes, one held request id.
  const live = (seq: number) => mounted.current && oweRef.current?.seq === seq;
  const finishOwe = (attempt: Extract<OweAttempt, { requestId: string }>, mark: { edits: number; drafts: unknown } | null, onSaved?: () => void) => {
    void (async () => {
      const { seq, relationshipId, body, requestId } = attempt;
      setOwe({ phase: "accepting", seq, relationshipId, body, requestId });
      let made: { commitment?: { id?: unknown; request_id?: unknown; body?: unknown; state?: unknown } };
      try {
        made = await hub.acceptRequest(requestId);
      } catch (cause) {
        if (!live(seq)) return;
        await settleFailure(seq, cause, () => setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId, acceptable: !ACCEPT_NO_EFFECT.has(failureCode(cause)),
          note: ACCEPT_NO_EFFECT.has(failureCode(cause)) ? "Request saved · Accept was refused" : "Request saved · Not yet a promise" }));
        return;
      }
      if (!live(seq)) return;
      const commitment = made?.commitment;
      if (!commitment || typeof commitment.id !== "string" || !commitment.id || commitment.request_id !== requestId) {
        setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId, acceptable: true, note: "Request saved · Not yet a promise" });
        return;
      }
      setOwe({ phase: "saved", seq, relationshipId, body, requestId, saved: { body: String(commitment.body ?? body), state: String(commitment.state ?? "open") } });
      // Clear only the exact unchanged draft of this attempt: same text, no
      // edit here, no draft write anywhere since the press.
      const key = `people/request/${relationshipId}`;
      if (mark && mark.edits === oweEdits.current && mark.drafts === useDesk.getState().drafts && (keptDraft(key) ?? "").trim() === body) {
        forgetOwe(); setOwe(null); onSaved?.();
      }
      onRefresh();
    })();
  };
  /** A failed write of this attempt: a key or owner failure clears the
   *  private view; a store 503 asks readiness which one it was. */
  const settleFailure = async (seq: number, cause: unknown, keep: () => void) => {
    let clear = isAuthOrKeyFailure(cause);
    if (!clear && cause instanceof ApiError && cause.status === 503) {
      try {
        const ready = await hub.readReadiness<Readiness>();
        clear = stateOf(ready) !== "ready";
      } catch { clear = true; }
      if (!live(seq)) return;
    }
    if (clear) { setOwe(null); onProtectedFailure(cause, true); return; }
    keep();
  };
  const addOwe = (onSaved?: () => void) => {
    const submitted = oweDraft;
    const body = submitted.trim(); if (!body) return;
    const current = oweRef.current;
    if (current && current.phase !== "saved") return;
    const seq = ++oweSeq.current;
    const relationshipId = relationship.id;
    const mark = { edits: oweEdits.current, drafts: useDesk.getState().drafts };
    setOwe({ phase: "creating", seq, relationshipId, body });
    void (async () => {
      let made: { request?: { id?: unknown; relationship_id?: unknown } };
      try {
        made = await hub.createRequest(relationship.id, body);
      } catch (cause) {
        if (!live(seq)) return;
        if (cause instanceof ApiError && CREATE_NO_EFFECT.has(failureCode(cause)) && !isAuthOrKeyFailure(cause)) {
          setOwe(null); onProtectedFailure(cause); return;
        }
        await settleFailure(seq, cause, () => setOwe({ phase: "creation_uncertain", seq, relationshipId, body }));
        return;
      }
      if (!live(seq)) return;
      const request = made?.request;
      if (!request || typeof request.id !== "string" || !request.id || (request.relationship_id !== undefined && request.relationship_id !== relationshipId)) {
        setOwe({ phase: "creation_uncertain", seq, relationshipId, body });
        return;
      }
      finishOwe({ phase: "accepting", seq, relationshipId, body, requestId: request.id }, mark, onSaved);
    })();
  };
  /** Check saved request: one read of the person; it never writes. */
  const checkOwe = () => {
    const current = oweRef.current;
    if (!current || current.phase !== "acceptance_uncertain") return;
    const { seq, relationshipId, body, requestId } = current;
    setOwe({ phase: "checking", seq, relationshipId, body, requestId });
    void hub.readPerson(relationshipId)
      .then((read) => {
        if (!live(seq)) return;
        const found = checkSavedRequest(read, relationshipId, requestId, body);
        if (found.kind === "saved") { setOwe({ phase: "saved", seq, relationshipId, body, requestId, saved: found.saved }); onRefresh(); return; }
        setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId,
          acceptable: found.kind === "acceptable", note: found.kind === "acceptable" ? "Request saved · Not yet a promise" : found.note });
      })
      .catch((cause) => {
        if (!live(seq)) return;
        void settleFailure(seq, cause, () => setOwe({ phase: "acceptance_uncertain", seq, relationshipId, body, requestId, acceptable: true, note: "Could not read the saved request · Check again" }));
      });
  };
  /** Accept saved request: the same id again (the store returns the one
   *  commitment if it was already accepted). */
  const acceptSavedOwe = () => {
    const current = oweRef.current;
    if (!current || current.phase !== "acceptance_uncertain" || !current.acceptable) return;
    finishOwe(current, null);
  };
  const addOwed = (onSaved?: () => void) => {
    const submitted = owedDraft;
    const body = submitted.trim(); if (!body || busy === "owed") return;
    void run("owed", () => hub.createOwed(relationship.id, body),
      () => { if ((keptDraft(`people/owed/${relationship.id}`) ?? "") === submitted) { forgetOwed(); onSaved?.(); } });
  };
  const addNote = () => {
    const submitted = noteDraft;
    const selectedVisibility = visibility === "shared_intent" ? "shared_intent" : "leader_private";
    if (!submitted.trim() || busy) return;
    void run("note", () => hub.createNote(relationship.id, { topic: "", body: submitted.trim(), visibility: selectedVisibility }),
      () => { if ((keptDraft(`people/context/${relationship.id}/body`) ?? "") === submitted
        && (keptDraft(`people/context/${relationship.id}/visibility`) ?? "") === visibility) { forgetNote(); forgetVisibility(); } });
  };
  const done = (id: string) => void run(`done:${id}`, () => hub.commitmentDone(id));
  const completeAction = (id: string) => void run(`action-done:${id}`, () => hub.completeAction(id));
  const removeAgenda = (id: string) => void run(`remove:${id}`, () => hub.removeAgendaItem(id), () => setRemoving(null));
  // HS-S33: Asked of you for the held request goes through the attempt.
  const heldRequest = owe && "requestId" in owe && owe.phase !== "saved" ? owe.requestId : null;
  const accept = (id: string) => {
    if (id === heldRequest) { setComposing(true); acceptSavedOwe(); return; }
    void run(`accept:${id}`, () => hub.acceptRequest(id));
  };

  const prep = brief ? composePeoplePrep(brief) : null;
  const nextEvent = prep?.nextOneOnOne ?? null;
  const nextAt = relationship.next_one_on_one ?? nextEvent?.starts_at ?? null;
  const suggestions = !nextAt && prep ? prep.calendarLinkSuggestions : [];
  const nextTitle = nextEvent?.title || (relationship.calendar_links ?? [])[0]?.label || "1:1";
  const until = nextAt ? untilWords(nextAt, now) : "";

  const displayName=brief?.display_name??relationship.display_name,firstName=displayName.trim().split(/\s+/)[0]||displayName;
  const youOwe=(relationship.commitments??[]).filter(row=>(row.state??"open")==="open"),theyOwe=(relationship.owed_to_you??[]).filter(row=>(row.state??"open")==="open");
  const actions=prep?.openMeetingActions??[],myActions=(brief?.i_owe_meeting_actions??[]).filter(row=>!["done","dismissed","completed"].includes(String(row.status??"")));
  const ledger:RecordRow[]=[
    ...(relationship.requests??[]).filter(row=>row.state==="requested").map(row=>({id:`q:${row.id}`,kind:"commitment",name:row.body,detail:"Asked of you",group:2,testId:"people-asked",accept:()=>accept(row.id)})),
    ...theyOwe.map(row=>({id:`o:${row.id}`,kind:"commitment",name:row.body,detail:[row.due?`By ${shortDay(row.due)}`:"",isOverdue(row.due)?"Overdue":""].filter(Boolean).join(" · "),group:0,inspect:row,side:"they",done:()=>done(row.id),nudge:isOverdue(row.due)?()=>toggleNudge({id:row.id,task:row.body,due:row.due??null}):undefined})),
    ...actions.map(row=>({id:`a:${row.id}`,kind:"action",name:row.task,detail:[row.meeting_title,row.due?`By ${shortDay(row.due)}`:""].filter(Boolean).join(" · "),group:0,side:"they",source:refOpener(row.source_ref||(row.meeting_id?`meeting:${row.meeting_id}`:null))??undefined,done:()=>completeAction(row.id),nudge:isOverdue(row.due)?()=>toggleNudge({id:row.id,task:row.task,due:row.due}):undefined})),
    ...youOwe.map(row=>({id:`c:${row.id}`,kind:"commitment",name:row.body,detail:[row.due?`By ${shortDay(row.due)}`:"",row.execution_links?.length?"On an automation":""].filter(Boolean).join(" · "),group:1,side:"you",inspect:row,done:()=>done(row.id)})),
    ...myActions.map(row=>({id:`m:${row.id}`,kind:"action",name:row.task,detail:row.meeting_title??"",group:1,side:"you",testId:"prep-i-owe-action",source:refOpener(row.meeting_id?`meeting:${row.meeting_id}`:null)??undefined,done:()=>completeAction(row.id)})),
    ...[...(relationship.owed_to_you??[]),...(relationship.commitments??[])].filter(row=>row.state==="done").map(row=>({id:`d:${row.id}`,kind:"commitment",name:row.body,detail:"Done",group:3,inspect:row})),
  ];
  const selected=ledger.find(row=>row.id===picked)??null;
  const ledgerFacts=[theyOwe.length+actions.length?`${theyOwe.length+actions.length} owed to you`:"",youOwe.length+myActions.length?`${youOwe.length+myActions.length} you owe`:""].filter(Boolean).join(" · ");
  const agenda=prep?.agenda??[],selectedAgenda=agenda.find(row=>row.id===agendaPicked)??null;
  const fromRow=(row:{id:string}|null)=>ledger.find(item=>item.id===row?.id);
  const openRow=(row:RecordRow)=>{if(row.inspect){commitmentOrigin.current=document.querySelector<HTMLElement>(`[data-testid="people-commitments"] [data-object-id="${row.id}"]`);setSelectedCommitment({commitment:row.inspect});}else row.source?.();};
  const ledgerVerbs:ListVerb[]=[
    {id:"add",label:"Add…",key:"n",run:()=>{setComposing(true);setSelectedCommitment(null);setNudging(null);}},
    {id:"note",label:"Note",testId:"person-add-note",run:()=>{setComposing(true);setSelectedCommitment(null);setComposeKind("note");}},
    {id:"open",label:"Open",key:"Enter",enabled:row=>Boolean(fromRow(row)?.inspect||fromRow(row)?.source),run:row=>{const item=fromRow(row);if(item)openRow(item);}},
    {id:"done",label:"Done",enabled:row=>Boolean(fromRow(row)?.done)&&!busy,run:row=>fromRow(row)?.done?.()},
    {id:"accept",label:"Accept",enabled:row=>Boolean(fromRow(row)?.accept)&&!busy&&(!heldRequest||fromRow(row)?.id!==`q:${heldRequest}`||Boolean(owe?.phase==="acceptance_uncertain"&&owe.acceptable)),run:row=>fromRow(row)?.accept?.()},
    {id:"nudge",label:"Nudge",enabled:row=>Boolean(fromRow(row)?.nudge)&&!busy,run:row=>{setComposing(false);fromRow(row)?.nudge?.();}},
  ];
  const addKind=view==="agenda"?"agenda":composeKind;
  const held=owe&&owe.phase!=="saved";
  const oweHere=addKind==="you"?owe:null;
  const primary=oweHere?.phase==="creation_uncertain"?{label:"Start another promise",testId:"people-owe-start-another",run:()=>setOwe(null)}
    :oweHere?.phase==="acceptance_uncertain"||oweHere?.phase==="checking"?{label:"Accept saved request",testId:"people-owe-accept-saved",disabled:oweHere.phase==="checking"||!oweHere.acceptable,run:acceptSavedOwe}
    :{label:"Add",testId:"people-composer-add",busy:Boolean(busy)||oweHere?.phase==="creating"||oweHere?.phase==="accepting",disabled:Boolean(busy)||Boolean(held)||!(addKind==="note"?noteDraft:addKind==="agenda"?agendaDraft:addKind==="they"?owedDraft:oweDraft).trim(),run:()=>{if(addKind==="note")addNote();else if(addKind==="agenda")addAgenda();else if(addKind==="they")addOwed();else addOwe();}};
  const readFailure=failure?<ActionNotice role="alert" tone="danger" action={{label:"Try again",onClick:()=>setAttempt(n=>n+1)}}>{failure}</ActionNotice>:undefined;
  const composer=<InspectorForm testId="people-composer" rows={[
    ...(view==="agenda"?[]:[{label:"Add to",control:<CycleGadget label="Add to this person" value={addKind} onChange={setComposeKind} options={[{value:"agenda",label:"Agenda"},{value:"note",label:"Note"},{value:"they",label:`${firstName} owes me`},{value:"you",label:`I owe ${firstName}`}]}/>}]),
    {label:"Words",control:<PadGadget autoFocus key={addKind} micDraftScope={addKind==="note"?`people/context/${relationship.id}/body`:addKind==="agenda"?`people/1on1/${relationship.id}`:addKind==="they"?`people/owed/${relationship.id}`:`people/request/${relationship.id}`} label={addKind==="note"?"Note":addKind==="agenda"?"Add to the agenda":addKind==="they"?`${firstName} owes me`:`I owe ${firstName}`} value={addKind==="note"?noteDraft:addKind==="agenda"?agendaDraft:addKind==="they"?owedDraft:oweDraft} onChange={addKind==="note"?setNoteDraft:addKind==="agenda"?setAgendaDraft:addKind==="they"?setOwedDraft:setOweDraft} rows={2}/>},
    ...(addKind==="note"?[{label:"Visibility",control:<CycleGadget label="Visibility" value={visibility==="shared_intent"?"shared_intent":"leader_private"} onChange={setVisibility} options={[{value:"leader_private",label:"Leader private"},{value:"shared_intent",label:"Shared"}]}/>}]:[]),
  ]} notice={issue?<ActionNotice role="alert" tone="danger">{issue}</ActionNotice>:oweHere?<OweReceipt attempt={oweHere}/>:held?<ActionNotice tone="warn">Select I owe {firstName} to continue.</ActionNotice>:readFailure} completion={{cancel:()=>view==="agenda"?setAgendaAdding(false):setComposing(false),primary,leading:oweHere&&(oweHere.phase==="acceptance_uncertain"||oweHere.phase==="checking")?<Button dense variant="secondary" disabled={oweHere.phase==="checking"} data-testid="people-owe-check" onClick={checkOwe}>Check saved request</Button>:undefined}}/>;
  const briefRows:RecordRow[]=[];
  if(nextAt)briefRows.push({id:"next",kind:"meeting",name:nextTitle,detail:[oneOnOneWhen(nextAt),until].filter(Boolean).join(" · "),group:0,testId:"people-plate",text:nextTitle});
  else for(const ev of suggestions)briefRows.push({id:`event:${ev.uid}:${ev.source_id}`,kind:"meeting",name:ev.title,detail:oneOnOneWhen(ev.starts_at),group:0,event:ev,testId:"prep-link-suggestion"});
  for(const pr of brief?.watch_summary?.prs_waiting??[])briefRows.push({id:`pr:${pr.repo}:${pr.pr_number}`,kind:"pull_request",name:`#${pr.pr_number} · ${pr.title}`,detail:`${pr.days_waiting} ${pr.days_waiting===1?"day":"days"} · ${pr.repo}`,group:3,state:pr.days_waiting>=3?{label:"Waiting for review",tone:"ask"}:undefined,source:pr.url?()=>window.open(pr.url,"_blank","noopener"):undefined});
  for(const row of brief?.watch_summary?.open_assignments??[])briefRows.push({id:`issue:${row.key}`,kind:"action",name:`${row.key} · ${row.summary}`,detail:[wireWords(row.status),row.overdue?"Overdue":""].filter(Boolean).join(" · "),group:3,state:row.overdue?{label:"Overdue",tone:"fail"}:undefined,source:row.url?()=>window.open(row.url,"_blank","noopener"):undefined});
  for(const row of (brief?.open_commitments??[]).filter(item=>isOverdue(item.due)))briefRows.push({id:`overdue:${row.id}`,kind:"commitment",name:row.body,detail:row.due?`By ${shortDay(row.due)}`:"",group:3,state:{label:"Overdue",tone:"fail"}});
  const lastTime=brief?.last_time,last=brief?.linked_meetings?.[0],lm=brief?.last_meeting,lastId=lastTime?.meeting_id??last?.meeting_id??lm?.meeting_id;
  if(lastId){const title=lastTime?(lastTime.one_on_one?"1:1":lastTime.title||"Meeting"):last?.title||lm?.title||"Meeting";briefRows.push({id:"last",kind:"meeting",name:title,detail:[lastTime?.started_at||last?.started_at?dayLabel((lastTime?.started_at??last?.started_at)!):"",lm?.item_count?`${lm.item_count} items`:"",lm?.open_count?`${lm.open_count} open`:""].filter(Boolean).join(" · "),group:4,source:refOpener(`meeting:${lastId}`)??undefined,testId:"prep-last"});
    for(const row of lastTime?.decisions??last?.decisions??[])briefRows.push({id:`decision:${row.id}`,kind:"decision",name:row.decision_text,group:4,source:refOpener(`meeting:${lastId}`)??undefined});
    for(const row of lastTime?.points??last?.open_action_items??[])briefRows.push({id:`point:${row.id}`,kind:"action",name:row.task,detail:row.owner??"",group:4,source:refOpener(`meeting:${lastId}`)??undefined});}
  for(const row of prep?.projects??[])briefRows.push({id:`project:${row.id}`,kind:"project",name:row.name,group:5,source:refOpener(`project:${row.id}`)??undefined,testId:"prep-projects"});
  for(const [i,row]of(brief?.memory?.excerpts??[]).entries())briefRows.push({id:`memory:${i}`,kind:row.kind,name:row.title||row.text,text:row.text,group:6,source:row.ref?()=>refOpener(row.ref)?.():undefined,testId:"prep-memory"});
  for(const row of relationship.notes??[])briefRows.push({id:`note:${row.id}`,kind:"note",name:row.topic||row.body,text:row.body,detail:[row.created_at?dayLabel(row.created_at):"",row.visibility==="leader_private"?"Leader private":"Shared"].filter(Boolean).join(" · "),group:7,testId:"people-note"});
  for(const program of personProgramsOf(brief,relationship)){
    briefRows.push({id:`program:${program.id}`,kind:"program",name:program.title,detail:wireWords(program.state),group:1,source:()=>openProgram(program.id)});
    for(const step of program.to_show??[])briefRows.push({id:`show:${program.id}:${step.step_id}`,kind:"program",name:step.title,detail:[program.title,step.pr_number?`Merged #${step.pr_number}`:""].filter(Boolean).join(" · "),group:2,source:()=>openProgram(program.id)});
    for(const step of program.to_ask??[])briefRows.push({id:`ask:${program.id}:${step.step_id}`,kind:"program",name:step.kind==="ask_review"?`Ask ${firstName} to review ${step.title}`:step.title,detail:program.title,group:3,source:()=>openProgram(program.id)});
  }
  for(const page of personPages(pages,displayName))for(const [i,sentence]of page.sentences.entries())for(const [j,ref]of(sentence.refs.length?sentence.refs:[null]).entries())briefRows.push({id:`page:${page.slug}:${i}:${j}`,kind:"note",name:sentence.text,detail:ref?.token||page.question,group:8,source:ref?.opens?refOpener(ref.ref)??undefined:undefined});
  const selectedBrief=briefRows.find(row=>row.id===briefPicked)??null;
  const briefVerbs:ListVerb[]=[
    {id:"open",label:selectedBrief?.id.startsWith("pr:")?"Open PR":selectedBrief?.id.startsWith("issue:")?"Open issue":selectedBrief?.id==="last"||selectedBrief?.group===4?"Open meeting":"Open source",key:"Enter",enabled:()=>Boolean(selectedBrief?.source),run:()=>selectedBrief?.source?.()},
    {id:"link",label:"Link this 1:1",enabled:()=>Boolean(selectedBrief?.event)&&!busy,run:()=>{const event=selectedBrief?.event;if(event)void run("link",()=>hub.linkSeries(relationship.id,event.uid,event.source_id,event.title));}},
    {id:"record",label:"Record 1:1",testId:"prep-record-meeting",enabled:()=>Boolean(nextEvent?.id)&&recordingState==="idle",run:()=>{if(nextEvent?.id)void useDesk.getState().startRecording({calendarEventId:nextEvent.id});}},
  ];
  const status=<StatusBar data-testid="person-status" items={[
    nextAt?{key:"next",text:[`1:1 ${lowerDay(oneOnOneWhen(nextAt))}`,until].filter(Boolean).join(" · ")}:null,
    ledgerFacts?{key:"count",text:<span data-testid="people-commitments-facts">{ledgerFacts}</span>}:null,
    {key:"lock",text:<span title="Encrypted · Local storage · Notes only" data-testid="person-lock">Encrypted</span>},
    {key:"receipt",text:recordingFailure?recordingReceipt:brief?<span data-testid="prep-receipt">Prepared {preparedAt}</span>:null},
    issue?{key:"failure",lamp:"fail",text:issue}:failure?{key:"failure",lamp:"fail",text:"Prep could not be read"}:null,
  ]}/>;
  if(!brief&&!failure)return <><SurfaceState loading/>{status}</>;
  return <><PreferencePane label="Person records" testId="people-prep-lens" data-feedback-redact="true">
    {view==="links"?links:view==="ledger"?<ListPane label="Selected commitment" listTestId="people-commitments" previewTestId="people-commitment-pane" list={<ListView label="Commitments" data-testid="prep-commitments" ordered headerless rows={ledger} columns={[{key:"name",word:"Commitment"}]} groups={[{id:0,label:"Owed to you"},{id:1,label:"You owe"},{id:2,label:"Asked of you"},{id:3,label:"Done"}]} selectedId={selected?.id??null} onSelect={id=>{setPicked(id);setComposing(false);setSelectedCommitment(null);setNudging(null);}} verbs={ledgerVerbs} defaultVerb="open" rowProps={row=>({"data-testid":ledger.find(item=>item.id===row.id)?.testId})}/>}>
      {selectedCommitment?<PaneInspector label="Commitment"><CommitmentInspector commitment={selectedCommitment.commitment} onClose={closeCommitment} onRefresh={()=>{onRefresh();setSelectedCommitment(null);}} onProtectedFailure={onProtectedFailure}/></PaneInspector>
      :nudging?<PrepNudge key={nudging.id} task={nudging.task} person={displayName} due={nudging.due} onClose={()=>setNudging(null)}/>
      :composing?<PaneInspector label="Add to this person">{composer}</PaneInspector>
      :selected?<InspectorFacts name={selected.name} data-feedback-redact="true" rows={[{label:"State",value:selected.detail||"Open"},{label:"Commitments",value:ledgerFacts}]} notice={issue?<ActionNotice role="alert" tone="danger">{issue}</ActionNotice>:readFailure}/>:<InspectorFacts name="Commitments" header={false} rows={[{label:"Open",value:ledgerFacts||"No open commitments"}]} notice={readFailure}/>}
    </ListPane>:view==="agenda"?<ListPane label="Selected agenda item" list={<ListView label="Agenda" headerless ordered rows={agenda.map((row,i)=>({id:row.id,kind:"action",name:row.body,cells:{number:i+1},detail:row.rolled_from_id?"Rolled":""}))} columns={[{key:"name",word:"Agenda"},{key:"number",word:"#",priority:1}]} selectedId={selectedAgenda?.id??null} onSelect={id=>{setAgendaPicked(id);setAgendaAdding(false);setRemoving(null);}} rowProps={()=>({"data-testid":"prep-agenda"})} verbs={[
      {id:"add",label:"Add…",run:()=>{setAgendaAdding(true);setAgendaPicked(null);}},
      {id:"remove",label:"Remove",enabled:()=>Boolean(selectedAgenda)&&!busy,run:()=>setRemoving(selectedAgenda?.id??null)},
      ...briefVerbs.filter(verb=>verb.id==="record"),
    ]}/>}>{removing&&selectedAgenda?<InspectorQuestion actionId="remove-agenda" targetId={JSON.stringify([relationship.id,selectedAgenda])} question={`Remove ${selectedAgenda.body}?`} cancel={()=>setRemoving(null)} verb={{label:"Remove",busy:Boolean(busy),run:()=>removeAgenda(selectedAgenda.id)}} notice={issue?<ActionNotice role="alert" tone="danger">{issue}</ActionNotice>:undefined}/>:selectedAgenda?<InspectorFacts name="Agenda item" rows={[{label:"Words",value:selectedAgenda.body},{label:"State",value:wireWords(selectedAgenda.state)}]} data-feedback-redact="true"/>:agendaAdding?<PaneInspector label="Add to the agenda">{composer}</PaneInspector>:<InspectorFacts name="Agenda" header={false} rows={[]}/>}</ListPane>
    :<ListPane label="Selected brief item" list={<ListView label="1:1 brief" headerless ordered rows={briefRows} columns={[{key:"name",word:"Item",priority:10},{key:"state",word:"State",priority:1}]} groups={[{id:0,label:"Next 1:1"},{id:1,label:"Programs"},{id:2,label:"To show them"},{id:3,label:"To ask"},{id:4,label:"Last time"},{id:5,label:"Projects"},{id:6,label:"On the desk"},{id:7,label:"Notes"},{id:8,label:"From your work"}]} selectedId={selectedBrief?.id??null} onSelect={setBriefPicked} rowProps={row=>({"data-testid":briefRows.find(item=>item.id===row.id)?.testId})} verbs={briefVerbs} defaultVerb="open"/>}>
      {selectedBrief?<InspectorFacts name={selectedBrief.name} rows={[{label:"Words",value:selectedBrief.text},{label:"When",value:selectedBrief.detail}]} data-feedback-redact="true" notice={readFailure}/>:<InspectorFacts name="1:1 brief" header={false} rows={[{label:"Next 1:1",value:nextAt?oneOnOneWhen(nextAt):brief&&!suggestions.length?"No 1:1 planned":""},{label:"Open",value:ledgerFacts||"No open commitments"}]} notice={readFailure}/>}
    </ListPane>}
  </PreferencePane>{status}</>;
}
