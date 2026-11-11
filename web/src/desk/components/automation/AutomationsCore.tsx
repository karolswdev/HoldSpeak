import { useGuideView } from "../../walk/viewState";
/** Automations is a selection list; an automation's own window keeps its results. */
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import type { CoreProps } from "../../../pages/cores/core-types";
import { keepPlace } from "../../deskMemory";
import { useDesk } from "../../store";
import { CheckGadget, InspectorForm, InspectorFacts, InspectorQuestion, ListPane, ListView, PaneInspector, PreferencePane, StatusBar, StringGadget, SurfaceState, countWords, type ListVerb } from "../../surface";
import { useWindowInterior } from "../../surface/interior";
import { WORKBENCH_CHANGE_KINDS, useOnDeskChanged } from "../../useDeskChangedRefresh";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { setWorkbenchAutomationEnabled, triggerWorkbenchRun, updateWorkbenchField } from "../../api";
import { programVerb } from "../../programs/api";
import { AutomationStarters } from "./Starters";
import { AutomationSetup } from "./AutomationSetup";
import { PutValue } from "./PutEditor";
import { NEW_AUTOMATION_PLACE, PICKED_AUTOMATION_PLACE } from "./places";
import { endedRuns, engineWords, eventSubjectWords, failureWords, hasStarts, isOn, nextWords, programDoWords, resultWhen, whenWords, type AutomationDetail } from "./model";

const runningProgram = (detail: AutomationDetail) => detail.results?.find((row) => row.status === "running" && row.program)?.program?.id
  ?? (detail.program?.latest && ["running","working"].includes(detail.program.latest.state) ? detail.program.latest.id : null);
const running = (detail: AutomationDetail) => Boolean(runningProgram(detail) || detail.last_run?.status === "running" || detail.items?.some((row) => row.status === "claimed"));
const runsWhen = (detail: AutomationDetail) => hasStarts(detail) || detail.when_needs_reset ? whenWords(detail) : "On request";
const lastRun = (detail: AutomationDetail) => {
  const result = endedRuns(detail)[0];
  const stamp = resultWhen(result?.completed_at ?? detail.last_run?.completed_at ?? detail.last_run?.started_at);
  const failed = result ? result.status === "failed" : detail.last_run?.status === "failed";
  return [stamp, failed ? "Failed" : ""].filter(Boolean).join(" · ");
};

export function AutomationsCore(_props: CoreProps) {
  const [automations, setAutomations] = useState<AutomationDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [making, setMaking] = useState(false);
  const [editing, setEditing] = useState(false);
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState<Record<string, boolean>>({});
  const [setupPending, setSetupPending] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState("");
  const [deleting, setDeleting] = useState<AutomationDetail | null>(null);
  const kept = useDesk((state) => state.places[PICKED_AUTOMATION_PLACE]) || null;
  const [picked, setPicked] = useState<string | null>(kept);
  useGuideView(() => ({picked,making,editing,deleting}), saved => {setPicked(saved.picked);keepPlace(PICKED_AUTOMATION_PLACE,saved.picked ?? "");setMaking(saved.making);setEditing(saved.editing);setDeleting(saved.deleting);}, undefined, 1);
  const asks = useRef(0);
  const view = useRef(0);
  const pickedNow = useRef(picked); pickedNow.current = picked;
  const actions = useRef(new Set<string>());
  useWindowInterior("list");
  const load = useCallback(async (quiet = false) => {
    const ask = ++asks.current;
    if (!quiet) setLoading(true);
    try {
      const answer = await apiFetch<{workbenches:AutomationDetail[]}>("/api/workbenches");
      if (ask !== asks.current) return;
      setAutomations(answer.workbenches); setLoadError("");
    } catch (failure) { if (ask === asks.current) setLoadError(`Automations not loaded: ${readableError(failure)}`); }
    finally { if (ask === asks.current) setLoading(false); }
  }, []);
  useEffect(() => { void load(); return () => { asks.current += 1; }; }, [load]);
  useOnDeskChanged(() => void load(true),WORKBENCH_CHANGE_KINDS);
  const bus = useOptionalRuntimeBus();
  useEffect(() => bus?.subscribe("program_changed", (frame) => {
    const id = String((frame.data as {program_id?:string})?.program_id ?? "");
    if (actions.current.size || automations.some((row) => row.results?.some((result) => result.program?.id === id) || row.program?.latest?.id === id)) void load(true);
  }), [bus,automations,load]);
  const asked = useDesk((state) => state.places[NEW_AUTOMATION_PLACE]) || "";
  useEffect(() => { if (asked) { view.current += 1; keepPlace(NEW_AUTOMATION_PLACE,""); setMaking(true); setEditing(false); setDeleting(null); } },[asked]);
  const onRead = useCallback((detail: AutomationDetail) => {
    asks.current += 1; setLoading(false); setLoadError("");
    setAutomations((list) => list.some((row) => row.id === detail.id) ? list.map((row) => row.id === detail.id ? detail : row) : [...list,detail]);
  },[]);
  const select = (id: string | null) => {
    view.current += 1;
    setPicked(id); keepPlace(PICKED_AUTOMATION_PLACE,id ?? ""); setMaking(false); setEditing(false); setDeleting(null); setError(""); setReceipt("");
  };
  const reveal = async (id: string) => {
    const requestedView = view.current;
    try {
      const answer = await apiFetch<{workbench:AutomationDetail}>(`/api/workbenches/${encodeURIComponent(id)}`);
      onRead(answer.workbench); if (view.current === requestedView) { select(id); setEditing(true); } void useDesk.getState().refresh();
    } catch (failure) { if (view.current === requestedView) { select(id); setError(`Automation not loaded: ${readableError(failure)}`); } void load(true); }
  };
  const selected = automations.find((row) => row.id === picked) ?? null;
  const act = async (id: string, verb: string, write: () => Promise<unknown>, done?: () => void) => {
    const key = `${verb}:${id}`;
    const requestedView = view.current;
    if (actions.current.has(key)) return;
    actions.current.add(key); setPending((rows) => ({...rows,[key]:true})); setError(""); setReceipt("");
    try { await write(); done?.(); await load(true); }
    catch (failure) { const message = `${verb === "run" ? "Run not started" : verb === "cancel" ? "Run not cancelled" : verb === "delete" ? "Not deleted" : "Not saved"}: ${readableError(failure)}`; if (view.current === requestedView) setError(message); else setReceipt(`${automations.find((row) => row.id === id)?.name ?? "Automation"} · ${message}`); }
    finally { actions.current.delete(key); setPending((rows) => { const next = {...rows}; delete next[key]; return next; }); }
  };
  const byRow = (row: {id:string} | null) => automations.find((entry) => entry.id === row?.id);
  const verbs: ListVerb[] = [
    {id:"new",label:"New automation",key:"n",testId:"automation-new",run:() => { view.current += 1; setMaking(true); setEditing(false); setDeleting(null); setError(""); }},
    {id:"open",label:"Open",key:"Enter",enabled:(row) => Boolean(row),run:(row) => { if (row) useDesk.getState().openWorkbenchWindow(row.id); }},
    {id:"edit",label:"Edit",key:"F2",enabled:(row) => Boolean(row) && !setupPending && !pending[`delete:${row?.id}`],run:() => { view.current += 1; setEditing(true); setMaking(false); setDeleting(null); }},
    {id:"run",label:"Run now",key:"r",testId:"automation-run-now",title:selected ? `Run with ${engineWords(selected) ?? "the chosen engine"}` : undefined,
      enabled:(row) => { const detail = byRow(row); return Boolean(detail && (detail.instruction_shown?.trim() || detail.instruction?.trim() || detail.do_kind === "run_program") && !running(detail) && !pending[`run:${detail.id}`] && !setupPending); },
      run:(row) => { if (row) { void act(row.id,"run",async () => { const ran = await triggerWorkbenchRun(row.id); setReceipt(ran?.skipped && typeof ran.reason === "string" ? ran.reason : `Run finished · ${byRow(row)?.name ?? "Automation"}`); }); void load(true); } }},
    {id:"cancel",label:"Cancel run",key:"c",enabled:(row) => { const detail = byRow(row); return Boolean(detail && runningProgram(detail) && !pending[`cancel:${detail.id}`]); },
      run:(row) => { const detail = byRow(row); const program = detail && runningProgram(detail); if (detail && program) void act(detail.id,"cancel",() => programVerb(program,"park"),() => setReceipt("Run cancelled")); }},
    {id:"delete",label:"Delete",key:"Delete",enabled:(row) => Boolean(row) && !setupPending && !pending[`delete:${row?.id}`],run:(row) => { const detail = byRow(row); if (detail) { view.current += 1; setDeleting(detail); setMaking(false); setEditing(false); setError(""); } }},
  ];
  const rows = useMemo(() => automations.filter((row) => `${row.name} ${row.instruction_shown ?? ""}`.toLocaleLowerCase().includes(query.toLocaleLowerCase())).map((detail) => ({
    id:detail.id,kind:"automation",name:detail.name || "Automation",nameTestId:"automation-home-name",
    cells:{runs:runsWhen(detail),last:lastRun(detail),next:nextWords(detail.next_run_at)?.replace(/^Next: /,"") ?? ""},
  })),[automations,query]);
  const fresh = automations.reduce((n,row) => n + endedRuns(row).filter((result) => result.new).length,0);
  const attention = automations.filter((row) => endedRuns(row)[0]?.status === "failed" || row.when_needs_reset || row.sources_shown?.some((source) => source.missing) || row.program?.latest?.state === "waiting" || row.results?.some((result) => result.program?.state === "waiting")).length;
  const toggleStarts = (detail: AutomationDetail, enabled: boolean) => void act(detail.id,"save",async () => {
    if (detail.schedule) await updateWorkbenchField(detail.id,{schedule_enabled:enabled});
    for (const start of detail.event_starts ?? []) if (start.id) await setWorkbenchAutomationEnabled(detail.id,start.id,enabled);
  });
  return <PreferencePane label="Automations" testId="automations-window">
    <ListPane label="Selected automation" listTestId="automation-home-rows" previewTestId="automations-pane" list={<>
      <ListView label="Automations" rows={rows} selectedId={selected?.id ?? null} onSelect={select} onClearSelection={() => select(null)} verbs={verbs} defaultVerb="open" ordered
        columns={[{key:"name",word:"Automation",track:"minmax(0, 2fr)",priority:4,minWidth:160},{key:"runs",word:"Runs",track:"minmax(0, 1.5fr)",priority:3,minWidth:160},{key:"last",word:"Last run",track:"minmax(0, 1.3fr)",priority:2,minWidth:150},{key:"next",word:"Next run",track:"minmax(0, 1fr)",priority:1,minWidth:110}]}
        toolbar={{testId:"automation-toolbar",trailing:<StringGadget label="Find an automation" value={query} onChange={(value) => { setQuery(value); select(null); }} placeholder="Find" />}} />
      <SurfaceState loading={loading} error={loadError || undefined} onRetry={loadError ? () => void load() : undefined} />
    </>}>
      {making ? <PaneInspector label="New automation"><AutomationStarters onCreated={(id) => void reveal(id)} onCancel={() => setMaking(false)} /></PaneInspector>
      : deleting ? <InspectorQuestion actionId="delete-automation" targetId={deleting.id} question={`Delete ${deleting.name}?`} keeps={["Past results"]} notice={error ? <SurfaceState error={error} /> : undefined}
          cancel={() => { setDeleting(null); setError(""); }} verb={{label:"Delete",busy:Boolean(pending[`delete:${deleting.id}`]),testId:"automation-delete-confirm",run:() => void act(deleting.id,"delete",() => apiFetch(`/api/workbenches/${encodeURIComponent(deleting.id)}`,{method:"DELETE"}),() => { const id = deleting.id; setDeleting((current) => current?.id === id ? null : current); if (pickedNow.current === id) { setPicked(null); keepPlace(PICKED_AUTOMATION_PLACE,""); } setReceipt(`Automation deleted · ${deleting.name}`); })}} />
      : selected && editing ? <PaneInspector label="Edit automation"><AutomationSetup key={selected.id} detail={selected} onRead={onRead} onDone={() => setEditing(false)} onPending={setSetupPending} /></PaneInspector>
      : selected ? <PaneInspector label={selected.name}><AutomationFacts><InspectorFacts name={selected.name} testId="automation-summary" rows={[
        {label:"Runs",value:runsWhen(selected)},
        {label:"Do",value:selected.do_kind === "run_program" ? programDoWords(selected) : selected.instruction_shown || selected.instruction || "Choose what to do"},
        ...(["hand_to_agent","run_program"].includes(selected.do_kind ?? "") && selected.instruction ? [{label:selected.do_kind === "run_program" ? "Goal" : "Agent brief",value:selected.instruction}] : []),
        {label:"About",value:eventSubjectWords(selected) || selected.sources_shown?.map((source) => source.missing ? "Missing source" : source.label).join(", ") || selected.blanks?.about || ""},
        {label:"With",value:engineWords(selected) ?? ""}, ...(selected.do_kind === "run_program" ? [] : [{label:"Put it in",value:<PutValue target={selected.output_target} />}]),
        {label:"Last run",value:lastRun(selected)}, {label:"Next run",value:nextWords(selected.next_run_at)?.replace(/^Next: /,"") ?? ""},
        ...(endedRuns(selected)[0]?.error ? [{label:"Failed",value:failureWords(endedRuns(selected)[0].error)}] : []),
      ]} />{hasStarts(selected) ? <InspectorForm rows={[{label:"On",control:<CheckGadget label="Automation on" checked={isOn(selected)} disabled={Boolean(pending[`save:${selected.id}`])} onChange={(enabled) => toggleStarts(selected,enabled)} />}]} completion={{done:() => select(null)}} /> : null}</AutomationFacts></PaneInspector> : loading || (loadError && !automations.length) ? null : <p data-testid="automation-home-empty">{query && !rows.length ? "No automations match." : automations.length ? "Select an automation." : "No automations. Use New automation."}</p>}
      {!deleting && error ? <SurfaceState error={error} /> : null}
    </ListPane>
    <StatusBar data-testid="automation-home-status" items={[
      automations.length ? {key:"count",text:countWords(automations.length,"automation"),testId:"automation-home-count"} : null,
      fresh ? {key:"new",lamp:"info",text:`${fresh} new`} : null,
      attention ? {key:"attention",lamp:"ask",text:`${attention} ${attention === 1 ? "needs" : "need"} you`} : null,
      receipt ? {key:"receipt",text:receipt} : null,
      error ? {key:"failure",lamp:"fail",text:error} : null,
    ]} />
  </PreferencePane>;
}
export default AutomationsCore;

function AutomationFacts({children}: {children: ReactNode}) { return <>{children}</>; }
