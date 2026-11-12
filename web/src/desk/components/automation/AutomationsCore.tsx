import { useGuideView } from "../../walk/viewState";
/** Automations is a selection list; an automation's own window keeps its results. */
import { useEffect, useRef, useState, type ReactNode } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import type { CoreProps } from "../../../pages/cores/core-types";
import { keepPlace } from "../../deskMemory";
import { useDesk } from "../../store";
import { ActionNotice, CheckGadget, InspectorForm, InspectorFacts, InspectorQuestion, ListApp, useListApp, PaneInspector, SurfaceState, countWords, type ListVerb } from "../../surface";
import { WORKBENCH_CHANGE_KINDS, useOnDeskChanged } from "../../useDeskChangedRefresh";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { setWorkbenchAutomationEnabled, triggerWorkbenchRun, updateWorkbenchField } from "../../api";
import { programVerb, readProgram } from "../../programs/api";
import { answerBinding } from "../../programs/liveModel";
import { AutomationStarters } from "./Starters";
import { AutomationSetup } from "./AutomationSetup";
import { PutValue } from "./PutEditor";
import { NEW_AUTOMATION_PLACE, PICKED_AUTOMATION_PLACE } from "./places";
import { endedRuns, engineWords, eventSubjectWords, failureWords, hasStarts, isOn, nextWords, programDoWords, resultWhen, whenWords, type AutomationDetail } from "./model";

const runningProgram = (detail: AutomationDetail) => detail.results?.find((row) => row.status === "running" && row.program)?.program?.id
  ?? (detail.program?.latest && ["running","working"].includes(detail.program.latest.state) ? detail.program.latest.id : null);
const running = (detail: AutomationDetail) => Boolean(runningProgram(detail) || detail.last_run?.status === "running" || detail.items?.some((row) => row.status === "claimed"));
const runsWhen = (detail: AutomationDetail) => hasStarts(detail) || detail.when_needs_reset ? whenWords(detail) : "On request";
const lastRun = (detail: AutomationDetail, withState = true) => {
  const result = endedRuns(detail)[0];
  const stamp = resultWhen(result?.completed_at ?? detail.last_run?.completed_at ?? detail.last_run?.started_at);
  const failed = result ? result.status === "failed" : detail.last_run?.status === "failed";
  return [stamp, withState && failed ? "Failed" : ""].filter(Boolean).join(" · ");
};

export function AutomationsCore(_props: CoreProps) {
  const [making, setMaking] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTab, setEditTab] = useState("do");
  const [pending, setPending] = useState<Record<string, boolean>>({});
  const [setupPending, setSetupPending] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState("");
  const [deleting, setDeleting] = useState<AutomationDetail | null>(null);
  const kept = useDesk((state) => state.places[PICKED_AUTOMATION_PLACE]) || null;
  const app = useListApp({
    read: readAutomations, keyOf: row => row.id,
    search: (row, query) => `${row.name} ${row.instruction_shown ?? ""}`.toLocaleLowerCase().includes(query),
    initialPicked: kept,
  });
  const { rows: automations, picked, setPicked, selected, apply: onRead, reload } = app;
  useEffect(() => keepPlace(PICKED_AUTOMATION_PLACE, picked ?? ""), [picked]);
  useGuideView(() => ({picked,making,editing,deleting}), saved => {setPicked(saved.picked);keepPlace(PICKED_AUTOMATION_PLACE,saved.picked ?? "");setMaking(saved.making);setEditing(saved.editing);setDeleting(saved.deleting);}, undefined, 1);
  const view = useRef(0);
  const actions = useRef(new Set<string>());
  useOnDeskChanged(() => void reload(), WORKBENCH_CHANGE_KINDS);
  const bus = useOptionalRuntimeBus();
  useEffect(() => bus?.subscribe("program_changed", (frame) => {
    const id = String((frame.data as {program_id?:string})?.program_id ?? "");
    if (actions.current.size || automations.some((row) => row.results?.some((result) => result.program?.id === id) || row.program?.latest?.id === id)) void reload();
  }), [bus,automations,reload]);
  useEffect(() => { if (!selected) { view.current += 1; setEditing(false); setDeleting(null); } }, [selected]);
  const asked = useDesk((state) => state.places[NEW_AUTOMATION_PLACE]) || "";
  useEffect(() => { if (asked) { view.current += 1; keepPlace(NEW_AUTOMATION_PLACE,""); setMaking(true); setEditing(false); setDeleting(null); } },[asked]);
  const select = (id: string | null) => {
    view.current += 1;
    setPicked(id); keepPlace(PICKED_AUTOMATION_PLACE,id ?? ""); setMaking(false); setEditing(false); setDeleting(null); setError(""); setReceipt("");
  };
  const reveal = async (id: string) => {
    const requestedView = view.current;
    try {
      const answer = await apiFetch<{workbench:AutomationDetail}>(`/api/workbenches/${encodeURIComponent(id)}`);
      onRead(answer.workbench); if (view.current === requestedView) { select(id); setEditTab("do"); setEditing(true); } void useDesk.getState().refresh();
    } catch (failure) { if (view.current === requestedView) { select(id); setError(`Automation not loaded: ${readableError(failure)}`); } void reload(); }
  };
  const act = async (id: string, verb: string, write: () => Promise<unknown>, done?: () => void) => {
    const key = `${verb}:${id}`;
    const requestedView = view.current;
    if (actions.current.has(key)) return;
    actions.current.add(key); setPending((rows) => ({...rows,[key]:true})); setError(""); setReceipt("");
    try { await write(); done?.(); await reload(); }
    catch (failure) { const message = `${verb === "run" ? "Run not started" : verb === "cancel" ? "Run not cancelled" : verb === "delete" ? "Not deleted" : "Not saved"}: ${readableError(failure)}`; if (view.current === requestedView) setError(message); else setReceipt(`${automations.find((row) => row.id === id)?.name ?? "Automation"} · ${message}`); }
    finally { actions.current.delete(key); setPending((rows) => { const next = {...rows}; delete next[key]; return next; }); }
  };
  const byRow = (row: {id:string} | null) => automations.find((entry) => entry.id === row?.id);
  const verbs: ListVerb[] = [
    { enabled: () => true,id:"new",label:"New automation",key:"n",testId:"automation-new",run:() => { view.current += 1; setMaking(true); setEditing(false); setDeleting(null); setError(""); }},
    {id:"open",label:"Open",key:"Enter",enabled:(row) => Boolean(row),run:(row) => { if (row) useDesk.getState().openWorkbenchWindow(row.id); }},
    {id:"edit",label:"Edit",key:"F2",enabled:(row) => Boolean(row) && !setupPending && !pending[`delete:${row?.id}`],run:() => { view.current += 1; setEditTab("do"); setEditing(true); setMaking(false); setDeleting(null); }},
    {id:"run",label:"Run now",key:"r",testId:"automation-run-now",title:selected ? `Run with ${engineWords(selected) ?? "the chosen engine"}` : undefined,
      enabled:(row) => { const detail = byRow(row); return Boolean(detail && (detail.instruction_shown?.trim() || detail.instruction?.trim() || detail.do_kind === "run_program") && !running(detail) && !pending[`run:${detail.id}`] && !setupPending); },
      run:(row) => { if (row) { void act(row.id,"run",async () => { const ran = await triggerWorkbenchRun(row.id); setReceipt(ran?.skipped && typeof ran.reason === "string" ? ran.reason : `Run finished · ${byRow(row)?.name ?? "Automation"}`); }); void reload(); } }},
    {id:"cancel",label:"Cancel run",key:"c",enabled:(row) => { const detail = byRow(row); return Boolean(detail && runningProgram(detail) && !pending[`cancel:${detail.id}`]); },
      run:(row) => { const detail = byRow(row); const program = detail && runningProgram(detail); if (detail && program) void act(detail.id,"cancel",async () => programVerb(program,"park",answerBinding(await readProgram(program))),() => setReceipt("Run cancelled")); }},
    {id:"delete",label:"Delete",key:"Delete",enabled:(row) => Boolean(row) && !setupPending && !pending[`delete:${row?.id}`],run:(row) => { const detail = byRow(row); if (detail) { view.current += 1; setDeleting(detail); setMaking(false); setEditing(false); setError(""); } }},
  ];
  const toRow = (detail: AutomationDetail) => ({
    id:detail.id,kind:"automation",name:detail.name || "Automation",nameTestId:"automation-home-name",
    cells:{runs:runsWhen(detail),last:lastRun(detail),next:nextWords(detail.next_run_at)?.replace(/^Next: /,"") ?? ""},
  });
  const fresh = automations.reduce((n,row) => n + endedRuns(row).filter((result) => result.new).length,0);
  const attention = automations.filter((row) => endedRuns(row)[0]?.status === "failed" || row.when_needs_reset || row.sources_shown?.some((source) => source.missing) || row.program?.latest?.state === "waiting" || row.results?.some((result) => result.program?.state === "waiting")).length;
  const toggleStarts = (detail: AutomationDetail, enabled: boolean) => void act(detail.id,"save",async () => {
    if (detail.schedule) await updateWorkbenchField(detail.id,{schedule_enabled:enabled});
    for (const start of detail.event_starts ?? []) if (start.id) await setWorkbenchAutomationEnabled(detail.id,start.id,enabled);
  });
  return <ListApp app={{...app,loading:app.loading && !app.page}} label="Automations" row={toRow}
    ids={{windowTestId:"automations-window",listTestId:"automation-home-rows",paneTestId:"automations-pane",toolbarTestId:"automation-toolbar",statusTestId:"automation-home-status"}}
    words={{find:"Find an automation",empty:"No automations. Use New automation.",noMatch:"No automations match.",select:"Select an automation.",failed:"Automations not loaded"}}
    list={{verbs,defaultVerb:"open",columns:[{key:"name",word:"Automation",track:"minmax(0, 2fr)",priority:4,minWidth:160},{key:"runs",word:"Runs",track:"minmax(0, 1.5fr)",priority:3,minWidth:160},{key:"last",word:"Last run",track:"minmax(0, 1.3fr)",priority:2,minWidth:150},{key:"next",word:"Next run",track:"minmax(0, 1fr)",priority:1,minWidth:110}]}}
    onSelect={() => { view.current += 1; setMaking(false); setEditing(false); setDeleting(null); setError(""); setReceipt(""); }}
    pane={() => making || selected || error ? <>
      {making ? <PaneInspector label="New automation"><AutomationStarters onCreated={(id) => void reveal(id)} onCancel={() => setMaking(false)} /></PaneInspector>
      : deleting && selected ? <InspectorQuestion actionId="delete-automation" targetId={deleting.id} question={`Delete ${deleting.name}?`} keeps={["Past results"]} notice={error ? <ActionNotice role="alert" tone="danger">{error}</ActionNotice> : undefined}
          cancel={() => { setDeleting(null); setError(""); }} verb={{label:"Delete",busy:Boolean(pending[`delete:${deleting.id}`]),testId:"automation-delete-confirm",run:() => void act(deleting.id,"delete",() => apiFetch(`/api/workbenches/${encodeURIComponent(deleting.id)}`,{method:"DELETE"}),() => { const id = deleting.id; setDeleting((current) => current?.id === id ? null : current); app.drop(id); setReceipt(`Automation deleted · ${deleting.name}`); })}} />
      : selected && editing ? <PaneInspector label="Edit automation"><AutomationSetup key={selected.id} detail={selected} initialTab={editTab} onRead={onRead} onDone={() => setEditing(false)} onPending={setSetupPending} /></PaneInspector>
      : selected ? <PaneInspector label={selected.name}><AutomationFacts><InspectorFacts data-feedback-redact="true" name={selected.name} testId="automation-summary" notice={error ? <ActionNotice role="alert" tone="danger">{error}</ActionNotice> : selected.sources_shown?.some(source=>source.missing) ? <ActionNotice role="alert" tone="danger" action={{label:"Edit sources",disabled:setupPending||Boolean(pending[`delete:${selected.id}`]),onClick:()=>{view.current+=1;setEditTab("about");setEditing(true);setMaking(false);setDeleting(null);}}}>Source missing</ActionNotice> : undefined} rows={[
        {label:"Runs",value:runsWhen(selected)},
        {label:"Do",value:selected.do_kind === "run_program" ? programDoWords(selected) : selected.instruction_shown || selected.instruction || ""},
        ...(["hand_to_agent","run_program"].includes(selected.do_kind ?? "") && selected.instruction ? [{label:selected.do_kind === "run_program" ? "Goal" : "Agent brief",value:selected.instruction}] : []),
        {label:"About",value:eventSubjectWords(selected) || selected.sources_shown?.filter(source=>!source.missing).map(source=>source.label).join(", ") || ""},
        {label:"With",value:engineWords(selected) ?? ""}, ...(selected.do_kind === "run_program" ? [] : [{label:"Put it in",value:<PutValue target={selected.output_target} />}]),
        {label:"Last run",value:lastRun(selected,false)}, {label:"Next run",value:nextWords(selected.next_run_at)?.replace(/^Next: /,"") ?? ""},
        ...(endedRuns(selected)[0]?.error ? [{label:"Failed",value:failureWords(endedRuns(selected)[0].error)}] : []),
      ]} />{hasStarts(selected) ? <InspectorForm rows={[{label:"On",control:<CheckGadget label="Automation on" checked={isOn(selected)} disabled={Boolean(pending[`save:${selected.id}`])} onChange={(enabled) => toggleStarts(selected,enabled)} />}]} completion={{done:() => select(null)}} /> : null}</AutomationFacts></PaneInspector> : null}
    </> : null}
    status={[
      automations.length ? {key:"count",text:countWords(automations.length,"automation"),testId:"automation-home-count"} : null,
      fresh ? {key:"new",lamp:"info",text:`${fresh} new`} : null,
      attention ? {key:"attention",lamp:"ask",text:`${attention} ${attention === 1 ? "needs" : "need"} you`} : null,
      receipt ? {key:"receipt",text:receipt} : null,
      error && !selected ? {key:"failure",lamp:"fail",text:error} : null,
    ]} />;
}
export default AutomationsCore;

async function readAutomations() {
  const answer = await apiFetch<{workbenches: AutomationDetail[]}>("/api/workbenches");
  return {rows: answer.workbenches};
}

function AutomationFacts({children}: {children: ReactNode}) { return <>{children}</>; }
