/** The automation object composes the same setup form as its collection. */
import { useCallback, useEffect, useRef, useState, type DragEvent } from "react";
import { fetchWorkbenchDetail, fetchWorkbenchMemory, forgetAutomationLesson, makeOneAutomation, openAutomationResult, setWorkbenchAutomationEnabled, triggerWorkbenchRun, updateWorkbenchField } from "../../api";
import type { MemoryEntry } from "../../detail-types";
import { readableError } from "../../../lib/api";
import { stateWords } from "../../surface/words";
import { ObjectReader, DotWord, InspectorFacts, InspectorQuestion, LampGadget, ListPane, ListView, PaneActions, PaneInspector, PreferencePane, PreferenceWell, ReadingDocument, SegmentedTabs, StatusBar, SurfaceState, useWindowBack, type ListVerb, type ObjectListRow } from "../../surface";
import { ShowMe } from "../../walk/ShowMe";
import { ObjectActions } from "../../decisions/ObjectActions";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { WORKBENCH_CHANGE_KINDS, useOnDeskChanged } from "../../useDeskChangedRefresh";
import { WORKBENCH_RUN_FRAME_TYPES } from "../workbench/runLifecycle";
import { useDropHand } from "../../hand";
import { openRef } from "../../openObject";
import { UsedLines } from "../UsedLines";
import { openNewProgram } from "../../programs/newProgram";
import { openProgram } from "../../programs/open";
import { useCopyReceipt } from "../../hooks/useCopyReceipt";
import { artifactDoc, noteDoc } from "../../documentSends";
import { SendWells } from "../../surface/send";
import { PutValue } from "./PutEditor";
import { AutomationSetup } from "./AutomationSetup";
import { canMakeOne, costWords, endedRuns, engineWords, eventSubjectWords, failureWords, hasStarts, isOldQueue, oldQueuePrefill, isOn, nextWords, programDoWords, putWords, queueTasks, resultLine, resultWhen, secondsWords, taskStateWords, whenWords, withoutIds, type AutomationDetail, type AutomationResult } from "./model";

const ABOUT_DROP_KINDS = new Set(["note","meeting","artifact","decision","decision_record","action","project_item"]);

export function AutomationBody({ workbenchId, onRead }: { workbenchId: string; onRead?: (detail: AutomationDetail) => void }) {
  const [detail, setDetail] = useState<AutomationDetail | null>(null);
  const [lessons, setLessons] = useState<MemoryEntry[]>([]);
  const [failure, setFailure] = useState("");
  const [readError, setReadError] = useState("");
  const [runRefused, setRunRefused] = useState(false);
  const [busy, setBusy] = useState(false);
  const [runStart, setRunStart] = useState<number | null>(null);
  const [hubRunSeen, setHubRunSeen] = useState<number | null>(null);
  const [editing, setEditing] = useState(false);
  const [returning, setReturning] = useState(false);
  const [setupPending, setSetupPending] = useState(false);
  const [sending, setSending] = useState(false);
  const [tab, setTab] = useState("about");
  const [shownId, setShownId] = useState<string | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<string | null>(null);
  const [forgetting, setForgetting] = useState<{index:number; entry:MemoryEntry} | null>(null);
  const [notice, setNotice] = useState("");
  const [dropReady, setDropReady] = useState(false);
  const hasInspector = editing || sending || Boolean(forgetting);
  const closeInspector = () => {
    if (busy || setupPending) return;
    setEditing(false); setSending(false); setForgetting(null); setReturning(true);
  };
  useWindowBack(hasInspector ? {onBack:closeInspector,testId:"automation-inspector-back"} : null, [hasInspector,busy,setupPending]);
  const reads = useRef(0);
  const inFlight = useRef(false);
  const { copy, state: copyState } = useCopyReceipt();
  const load = useCallback(async () => {
    const mine = ++reads.current;
    try {
      const [answer, memory] = await Promise.all([fetchWorkbenchDetail(workbenchId), fetchWorkbenchMemory(workbenchId)]);
      if (mine !== reads.current) return;
      setDetail(answer as AutomationDetail); setLessons(memory); setReadError("");
    } catch (cause) { if (mine === reads.current) setReadError(readableError(cause)); }
  }, [workbenchId]);
  useEffect(() => { void load(); return () => { reads.current += 1; }; }, [load]);
  useEffect(() => { if (detail) onRead?.(detail); }, [detail, onRead]);
  useOnDeskChanged(load, WORKBENCH_CHANGE_KINDS);
  const bus = useOptionalRuntimeBus();
  useEffect(() => {
    if (!bus) return;
    const offs = WORKBENCH_RUN_FRAME_TYPES.map(type => bus.subscribe(type, frame => {
      if (String((frame.data as {workbench_id?:string})?.workbench_id ?? "") === workbenchId) void load();
    }));
    return () => offs.forEach(off => off());
  }, [bus, load, workbenchId]);
  const write = async (action: () => Promise<unknown>) => {
    if (inFlight.current) return false;
    inFlight.current = true; setBusy(true); setFailure("");
    try { await action(); await load(); return true; }
    catch (cause) { setFailure(readableError(cause)); return false; }
    finally { inFlight.current = false; setBusy(false); }
  };
  const results = endedRuns(detail);
  const shown = results.find(row => row.item_id === shownId) ?? results[0] ?? null;
  const hubRunning = Boolean(detail?.items?.some(row => row.status === "claimed"));
  useEffect(() => {
    if (hubRunning) setHubRunSeen(seen => seen ?? Date.now());
    else setHubRunSeen(null);
  }, [hubRunning]);
  const startedAt = runStart ?? (hubRunning ? detail?.last_run?.started_at ?? hubRunSeen : null);
  const running = busy || hubRunning;
  const oldQueue = Boolean(detail && (detail.do_kind ?? "run") === "run" && detail.instruction_from !== "automation" && isOldQueue(detail));
  const [readResult, setReadResult] = useState<string | null>(null);
  useEffect(() => {
    if (tab !== "results" || !shown?.new || !shown.artifact_id || shown.artifact_id === readResult) return;
    setReadResult(shown.artifact_id);
    void openAutomationResult(workbenchId,shown.artifact_id).then(load).catch(cause => setFailure(readableError(cause)));
  }, [tab, shown?.artifact_id, shown?.new, readResult, workbenchId, load]);
  const showResult = (result: AutomationResult) => {
    if (result.program && !result.program_run) openProgram(result.program.id);
    setShownId(result.item_id); setTab("results");
    if (result.new && result.artifact_id) {
      setReadResult(result.artifact_id);
      void openAutomationResult(workbenchId,result.artifact_id).then(load).catch(cause => setFailure(readableError(cause)));
    }
  };
  const run = async (queue = false) => {
    if (inFlight.current || setupPending || (oldQueue && !queue)) return;
    setNotice(""); setTab("results"); setShownId(null); setRunStart(Date.now());
    const ran = await write(async () => {
      const answer = await triggerWorkbenchRun(workbenchId);
      if (answer?.skipped && typeof answer.reason === "string") setNotice(answer.reason);
    });
    setRunStart(null); setRunRefused(!ran);
  };
  const drop = (event: DragEvent) => {
    setDropReady(false);
    const drag = useDropHand.getState().drag;
    if (!detail || !drag || !ABOUT_DROP_KINDS.has(drag.origin.kind) || eventSubjectWords(detail)) return;
    event.preventDefault(); useDropHand.getState().endDrag();
    const ref = drag.origin.kind + ":" + drag.origin.id;
    const sources = (detail.sources_shown ?? []).map(source => source.ref);
    if (!sources.includes(ref)) void write(() => updateWorkbenchField(workbenchId,{sources:[...sources,ref]}));
  };
  if (!detail) return <PreferencePane label="Automation" testId="automation-window"><SurfaceState loading={!readError} error={readError || undefined} onRetry={() => void load()} /></PreferencePane>;
  const taskRows = queueTasks(detail);
  const tasks = new Map(taskRows.map(task => [task.item_id,task]));
  const program = shown && !shown.program_run && shown.status !== "failed" ? shown.program : null;
  const doc = shown?.program_run ? (shown.note_id ? noteDoc(shown.note_id,shown.title) : null)
    : shown?.artifact_id ? artifactDoc(shown.artifact_id,shown.title,"automation result") : null;
  const ready = () => !running && !setupPending && !editing && !forgetting;
  const verbs: ListVerb[] = [
    {id:"edit",label:"Edit",testId:"automation-edit",enabled:ready,run:() => {setSending(false);setEditing(true);}},
    ...(!oldQueue && !(tab === "results" && shown?.status === "failed") ? [{id:"run",label:runRefused || shown?.status === "failed" ? "Run again" : "Run now",testId:runRefused || shown?.status === "failed" ? "automation-run-again" : "automation-run-now",enabled:() => ready() && Boolean(detail.instruction_shown?.trim() || detail.instruction?.trim()),run:() => void run()}] : []),
    ...(hasStarts(detail) ? [{id:"on",label:isOn(detail) ? "Turn off" : "Turn on",enabled:ready,run:() => void write(async () => {
      if (detail.schedule) await updateWorkbenchField(workbenchId,{schedule_enabled:!isOn(detail)});
      for (const start of detail.event_starts ?? []) if (start.id) await setWorkbenchAutomationEnabled(workbenchId,start.id,!isOn(detail));
    })}] : []),
    ...(oldQueue ? [{id:"program",label:"Set this up as a program",testId:"automation-set-up-program",enabled:ready,run:() => openNewProgram(oldQueuePrefill(detail))}] : []),
    ...(canMakeOne(detail) ? [{id:"one",label:"Make this one automation",testId:"automation-make-one",enabled:ready,run:() => void write(() => makeOneAutomation(workbenchId))}] : []),
    ...(shown?.text ? [{id:"copy",label:"Copy",testId:"automation-copy",run:() => void copy(withoutIds(shown.text ?? ""))}] : []),
    ...(program ? [{id:"open-program",label:"Open program",testId:"automation-open-program",run:() => openProgram(program.id)}] : []),
    ...(shown?.note_id ? [{id:"open-note",label:"Open as note",testId:"automation-open-note",run:() => openRef("note:" + shown.note_id)}] : []),
    ...(doc ? [{id:"send",label:"Send…",enabled:ready,run:() => {setSending(!sending);setTab("results");}}] : []),
  ];
  const resultRows: ObjectListRow[] = results.map(result => ({id:result.item_id,kind:"artifact",name:resultLine(result),
    when:resultWhen(result.completed_at),state:result.status === "failed" ? {label:"Failed",tone:"fail"} : result.new && result.artifact_id !== readResult ? {label:"New",tone:"ask"} : undefined}));
  const tabs = [{id:"about",label:"About"},{id:"runs",label:"Runs"},{id:"results",label:"Results"},
    ...(tasks.size ? [{id:"tasks",label:"Tasks"}] : []),...(lessons.length ? [{id:"learned",label:"Learned"}] : [])];
  const view = tabs.some(item => item.id === tab) ? tab : "about";
  const missingSource = (detail.sources_shown ?? []).some(source => source.missing);
  const engine = engineWords(detail);
  const attention = missingSource ? "Source missing" : !engine ? "No engine" : null;
  return <PreferencePane label="Automation" testId="automation-window" data-drop-ready={dropReady || undefined}
    onKeyDown={event => {
      if (event.key === "Escape" && !event.defaultPrevented && hasInspector) {
        event.stopPropagation();
        if (!event.nativeEvent.isComposing) {event.preventDefault();closeInspector();}
      }
    }}
    onDragOver={event => {
      const drag = useDropHand.getState().drag;
      if (drag && ABOUT_DROP_KINDS.has(drag.origin.kind) && !eventSubjectWords(detail)) {event.preventDefault();setDropReady(true);}
    }} onDragLeave={() => setDropReady(false)} onDrop={drop}>
    {!editing ? <ObjectActions label="Automation" autoFocus={returning} verbs={verbs} testId="automation-toolbar" /> : null}
    {editing ? <PaneInspector label="Edit automation"><AutomationSetup detail={detail} onRead={setDetail} onDone={() => {setEditing(false);setReturning(true);}} onPending={setSetupPending} /></PaneInspector>
      : <SegmentedTabs label="Automation views" value={view} onChange={next => {if(!forgetting){setSending(false);setTab(next);}}} tabs={tabs}>
        {view === "about" ? <InspectorFacts name="Setup" data-feedback-redact="true" testId="automation-summary" notice={dropReady ? "Drop to add a source" : null} rows={[
          {label:"Do",value:detail.do_kind === "run_program" ? programDoWords(detail) : detail.do_kind === "hand_to_agent" ? "Hand to an agent session" : detail.instruction_shown},
          {label:"When",value:whenWords(detail)},{label:"Next",value:nextWords(detail.next_run_at)},
          {label:"About",value:eventSubjectWords(detail)},
          ...(detail.sources_shown ?? []).map(source => ({key:source.ref,label:"Source",value:source.missing
            ? <DotWord tone="fail">{(source.label || stateWords(source.kind || source.ref.split(":")[0] || "source")) + " · missing"}</DotWord>
            : source.label})),
          {label:"With",value:engine || <LampGadget on tone="ask" label="No engine" />},{label:"Review by",value:detail.review_by && detail.review_by !== "none" ? ({codex:"Codex",claude:"Claude Code",pi:"pi"}[detail.review_by] ?? detail.review_by) : null},{label:"Put it in",value:<PutValue target={detail.output_target} />},
        ]} /> : null}
        {view === "runs" ? <section className="surface-pane-inspector" data-testid="automation-runs-well">{results.length ? <ListView label="Runs" rows={resultRows} selectedId={shown?.item_id} onSelect={setShownId} ordered
          columns={[{key:"name",word:"Result",priority:100},{key:"when",word:"Finished",priority:20},{key:"state",word:"State",priority:30}]} defaultVerb="open"
          verbs={[{id:"open",label:"Open result",key:"Enter",enabled:row => Boolean(row),run:row => {const result = results.find(result => result.item_id === row?.id);if(result)showResult(result);}}]} /> : <SurfaceState empty emptyLabel="No runs yet" />}</section> : null}
        {view === "results" ? <section className="surface-pane-inspector" data-testid="automation-results-well">{sending && doc ? <PreferenceWell><SendWells doc={doc} onBack={() => setSending(false)} /></PreferenceWell>
          : startedAt ? <ObjectReader label="Automation" running={{start:startedAt}} facts={[{label:"Do",value:detail.instruction_shown},{label:"Engine",value:engine}]} lines={(detail.items ?? []).filter(item => item.status === "claimed").map(item => ({id:item.id,text:item.title}))} />
          : shown ? <ObjectReader label="Result" facts={[{label:"Finished",value:resultWhen(shown.completed_at)},{label:"Time",value:secondsWords(shown.seconds)},{label:"Engine",value:shown.model},{label:"Cost",value:costWords(shown.cost_usd)}]}
            failure={shown.status === "failed" ? failureWords(shown.error) : undefined} retry={shown.status === "failed" ? {label:"Run again",disabled:!ready(),run:() => void run(oldQueue)} : undefined}>
            {shown.status === "failed" ? null
              : program ? <InspectorFacts name="Program" rows={[{label:"Name",value:program.title},{label:"State",value:program.state_word},{label:"Steps",value:program.total ? program.done + " of " + program.total : null}]} />
              : <ReadingDocument data-testid="automation-reading">{withoutIds(shown.text ?? "") || "The engine gave no words."}</ReadingDocument>}
            <UsedLines used={shown.used} testPrefix="automation" />
          </ObjectReader> : <SurfaceState empty emptyLabel="No runs yet" />}</section> : null}
        {view === "tasks" ? <ListPane label="Task" list={<ListView label="Tasks" rows={taskRows.map(task => ({id:task.item_id,kind:"action",name:task.title || resultLine(task),cells:{state:taskStateWords(task.status)}}))}
          columns={[{key:"name",word:"Task",priority:100},{key:"state",word:"State",priority:10}]} selectedId={shownId} onSelect={setShownId} ordered
          defaultVerb="open" verbs={[{id:"open",label:"Open task",key:"Enter",enabled:row => Boolean(row),run:row => {if(row)setShownId(row.id);}},{id:"again",label:"Run again",enabled:row => Boolean(row && ["done","failed"].includes(tasks.get(row.id)?.status ?? "") && ready()),run:() => void run(true)}]} />}>
          {shownId && tasks.has(shownId) ? <ReadingDocument>{withoutIds(tasks.get(shownId)?.text ?? tasks.get(shownId)?.error ?? "")}</ReadingDocument> : "Select a task."}
        </ListPane> : null}
        {view === "learned" ? <section className="surface-pane-inspector" data-testid="automation-learned-well"><ListView label="Learned" columns={[{key:"name",word:"Lesson"}]} ordered rows={lessons.map((entry,index) => ({id:String(index),kind:"note",name:entry.content}))}
          selectedId={selectedLesson} onSelect={id => {if(!forgetting)setSelectedLesson(id);}} verbs={[{id:"forget",label:"Forget",enabled:row => Boolean(row) && ready(),run:row => {if(row)setForgetting({index:Number(row.id),entry:lessons[Number(row.id)]});}}]} /></section> : null}
      </SegmentedTabs>}
    {forgetting ? <PaneActions><InspectorQuestion question="Forget this lesson?" actionId="forget-lesson" targetId={workbenchId + JSON.stringify(lessons[forgetting.index] ?? null)}
      cancel={() => setForgetting(null)} verb={{label:"Forget",busy,run:() => void write(() => forgetAutomationLesson(workbenchId,forgetting.index,forgetting.entry.timestamp)).then(saved => {if(saved)setForgetting(null);})}} /></PaneActions> : null}
    <StatusBar items={[
      {key:"failure",lamp:"fail",text:failure || null,testId:"automation-failure"},
      {key:"read-failure",lamp:"fail",text:readError || null,testId:"automation-read-failure"},
      {key:"result-failure",lamp:"fail",text:!failure && !startedAt && shown?.status === "failed" ? failureWords(shown.error) : null,testId:"automation-result-failure"},
      {key:"attention",lamp:missingSource ? "fail" : "ask",text:!failure && !readError && !notice && copyState !== "failed" && shown?.status !== "failed" && attention ? <span>{attention}</span> : null,testId:"automation-attention"},
      {key:"unread",lamp:"ask",text:!attention && results.some(result => result.new && result.artifact_id !== readResult) ? "New result" : null},
      {key:"notice",lamp:"ask",text:notice || null,testId:"automation-run-notice"},
      {key:"copy",lamp:copyState === "failed" ? "fail" : undefined,text:copyState === "failed" ? "Copy failed. Text kept. Try again." : copyState === "copied" ? "Copied" : null},
      {key:"count",text:results.length ? results.length + (results.length === 1 ? " run" : " runs") : null,priority:1},
      {key:"last",text:resultWhen(results[0]?.completed_at),priority:2},
    ]} />
    <ShowMe app="surface-workbenches" />
  </PreferencePane>;
}
