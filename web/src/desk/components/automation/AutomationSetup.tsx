/** Field custody stays here; the shared kit owns tabs, rows and completion. */
import { useEffect, useRef, useState, type ReactNode } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { CheckGadget, CycleGadget, InspectorForm, ListView, PadGadget, SegmentedTabs, StringGadget, SurfaceState } from "../../surface";
import { setAutomationEngine, setAutomationWhen, updateWorkbenchField, type AutomationWhenChoice } from "../../api";
import { useDesk } from "../../store";
import { aboutCandidates, aboutMatches } from "../about/AboutPicker";
import { registerRepository } from "../../repository";
import { readDetection } from "../../../features/runson/api";
import { buildEngines, type BoardEngine } from "../../../features/runson/model";
import { useDestinations } from "../../surface/send";
import { TEMPLATES } from "../../programs/api";
import { CONTROLS } from "../../programs/model";
import { ProgramAgent, programDraft, programFields } from "./ProgramDo";
import { readNativeAgentOptions, assignedId, usable, automationEngineProfile } from "./WithEditor";
import { engineWords, eventSubjectWords, schedulePick, whenWords, type AutomationDetail } from "./model";

type SetupDraft = {name:string;instruction:string;kind:string;program:ReturnType<typeof programDraft>;when:string;time:string;day:string;repository:string;profile:string;review:string;spend:string;target:string};

const TABS = [{id:"do",label:"Do"},{id:"when",label:"When"},{id:"about",label:"About"},{id:"with",label:"With"},{id:"put",label:"Put it in"}];
const DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];

export function AutomationSetup({ detail, onRead, onDone, onPending }: {
  detail: AutomationDetail; onRead(detail: AutomationDetail): void; onDone(): void; onPending(busy: boolean): void;
}) {
  const [tab, setTab] = useState("do");
  const [saving, setSaving] = useState(false);
  const drafts = useRef(new Map<string,SetupDraft>());
  const pending = (busy: boolean) => { setSaving(busy); onPending(busy); };
  return <SegmentedTabs label="Automation setup" tabs={TABS} value={tab} onChange={(next) => { if (!saving) setTab(next); }}>
    <SetupField key={`${detail.id}:${tab}`} {...{detail,onRead,onDone}} onPending={pending} part={tab} drafts={drafts.current} />
  </SegmentedTabs>;
}

function SetupField({ detail, part, onRead, onDone, onPending, drafts }: {
  detail: AutomationDetail; part: string; onRead(detail: AutomationDetail): void; onDone(): void; onPending(busy: boolean): void; drafts: Map<string,SetupDraft>;
}) {
  const kept = drafts.get(part);
  const [name, setName] = useState(kept?.name ?? detail.name);
  const [instruction, setInstruction] = useState(kept?.instruction ?? detail.instruction ?? "");
  const [kind, setKind] = useState(kept?.kind ?? detail.do_kind ?? "run");
  const [program, setProgram] = useState(() => kept?.program ?? programDraft(detail));
  const pick = schedulePick(detail.schedule);
  const [when, setWhen] = useState(kept?.when ?? "keep");
  const [time, setTime] = useState(kept?.time ?? pick?.time ?? "09:00");
  const [day, setDay] = useState(kept?.day ?? String(pick?.day ?? 1));
  const [repository, setRepository] = useState(kept?.repository ?? "");
  const [profile, setProfile] = useState(kept?.profile ?? (detail.do_kind === "hand_to_agent" ? detail.agent_profile : detail.assignment_summary?.profile_id) ?? "");
  const [review, setReview] = useState(kept?.review ?? detail.review_by ?? "none");
  const [spend, setSpend] = useState(kept?.spend ?? (detail.spend_limit_usd == null ? "" : String(detail.spend_limit_usd)));
  const [target, setTarget] = useState(kept?.target ?? detail.output_target ?? "inbox");
  const [folder, setFolder] = useState("");
  const [sourceQuery, setSourceQuery] = useState("");
  const [sourcePick, setSourcePick] = useState<string | null>(null);
  const [engines, setEngines] = useState<Array<{value:string;label:string;engine?:BoardEngine}>>([]);
  const [agents, setAgents] = useState<Array<{value:string;label:string}>>([]);
  const [people, setPeople] = useState<Array<{id:string;name:string}>>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [readError, setReadError] = useState("");
  const items = useDesk((state) => state.items);
  const destinations = useDestinations();
  const live = useRef(true);
  const inFlight = useRef(false);
  useEffect(() => { live.current = true; return () => { live.current = false; }; }, []);
  const readOptions = async () => {
    setReadError("");
    try {
      if (part === "with") {
        if (detail.do_kind === "hand_to_agent") {
          const rows = await readNativeAgentOptions();
          if (live.current) { setEngines(rows.filter((row) => row.ready).map((row) => ({value:row.profileId,label:row.label}))); setAgents(rows.filter((row) => row.ready).map((row) => ({value:row.agentId,label:row.label}))); }
        } else if (detail.do_kind !== "run_program") {
          const rows = buildEngines(null, await readDetection()).filter(usable);
          if (live.current) setEngines(rows.map((row) => ({value:row.found ? `add:${row.key}` : assignedId(row),label:row.found ? `Add ${row.name}` : row.name,engine:row})));
        }
      }
      if (part === "about") {
        const answer = await apiFetch<{relationships?: Array<{id:string;display_name:string}>}>("/api/people/relationships");
        if (live.current) setPeople((answer.relationships ?? []).map((row) => ({id:row.id,name:row.display_name})));
      }
    } catch (failure) { if (live.current) setReadError(readableError(failure)); }
  };
  useEffect(() => { void readOptions(); }, []);
  const latest = useRef({name,instruction,kind,program,when,time,day,repository,profile,review,spend,target});
  latest.current = {name,instruction,kind,program,when,time,day,repository,profile,review,spend,target};
  drafts.set(part,latest.current);
  const save = async (write: () => Promise<unknown>, close = true) => {
    if (inFlight.current) return;
    const submitted = JSON.stringify(latest.current);
    inFlight.current = true; setBusy(true); onPending(true); setError("");
    try {
      await write();
      const answer = await apiFetch<{workbench:AutomationDetail}>(`/api/workbenches/${encodeURIComponent(detail.id)}`);
      if (!live.current) return;
      onRead(answer.workbench);
      if (close && submitted === JSON.stringify(latest.current)) onDone();
    } catch (failure) { if (live.current) setError(`Not saved: ${readableError(failure)}`); }
    finally { inFlight.current = false; onPending(false); if (live.current) setBusy(false); }
  };
  const update = (fields: Record<string,unknown>, close = true) => save(() => updateWorkbenchField(detail.id,fields),close);
  const sources = detail.sources_shown ?? [];
  const refs = sources.map((source) => source.ref);
  const candidates = [...aboutCandidates(items,people), ...(detail.assignment_summary?.vendor ? (items.repository ?? []).map((row) => ({ref:`repository:${row.id}`,kind:"folder",label:`Folder ${row.name}`})) : [])];
  const happened = eventSubjectWords(detail);
  const isProgram = detail.do_kind === "run_program";
  const rows: Array<{label:string;control:ReactNode}> = [];
  let primary = () => void update({});
  let disabled = false;
  let immediate = false;
  if (part === "do") {
    rows.push({label:"Name",control:<StringGadget label="Automation name" value={name} onChange={setName} />},
      {label:"Do",control:<CycleGadget label="Do kind" value={kind} onChange={setKind} options={[{value:"run",label:"Run"},{value:"hand_to_agent",label:"Hand to an agent session"},{value:"run_program",label:"Run a program"}]} />},
      {label:kind === "run_program" ? "Goal" : kind === "hand_to_agent" ? "Agent brief" : "What it does",control:<PadGadget label={kind === "run_program" ? "Goal" : kind === "hand_to_agent" ? "Agent brief" : "What it does"} value={instruction} onChange={setInstruction} rows={3} />});
    if (kind === "run_program") rows.push(
      {label:"Template",control:<CycleGadget label="Program template" value={program.template} onChange={(template) => setProgram({...program,template})} options={TEMPLATES.map((row) => ({value:row.id,label:row.name}))} />},
      {label:"Control",control:<CycleGadget label="Program control" value={program.control} onChange={(control) => setProgram({...program,control})} options={[{value:"",label:"The template's"},...CONTROLS.map((row) => ({value:row.value,label:row.word}))]} />},
      {label:"Agent",control:<ProgramAgent draft={program} onChange={setProgram} fallback={detail.program?.runs_on_words} />});
    disabled = !name.trim() || (!instruction.trim() && !(kind === "run_program" && program.template === "from-the-desk")) || (kind === "run_program" && !program.template);
    primary = () => void update({name:name.trim(),instruction:instruction.trim(),do_kind:kind,...(kind === "run_program" ? programFields(program) : {})});
  } else if (part === "when") {
    rows.push({label:"Runs",control:<CycleGadget label="When" value={when} onChange={setWhen} options={[
      {value:"keep",label:whenWords(detail)},{value:"manual",label:"On request"},
      ...Object.entries({day:"Every day",weekday:"Every weekday",week:"Every week",hour:"Every hour"}).map(([value,label]) => ({value,label})),
      ...(detail.when_events ?? []).map((row) => ({value:`event:${row.id}`,label:row.words})),
    ]} />});
    if (["day","weekday","week"].includes(when)) rows.push({label:"At",control:<StringGadget label="At" value={time} onChange={setTime} type="time" />});
    if (when === "week") rows.push({label:"Day",control:<CycleGadget label="Day" value={day} onChange={setDay} options={DAYS.map((label,index) => ({value:String(index),label}))} />});
    if (when.startsWith("event:")) rows.push({label:"Repository",control:<StringGadget label="GitHub repository" value={repository} onChange={setRepository} placeholder="owner/name" />});
    disabled = when === "keep" || (when.startsWith("event:") && !/^[\w.-]+\/[\w.-]+$/.test(repository.trim())) || (["day","weekday","week"].includes(when) && !/^([01]\d|2[0-3]):[0-5]\d$/.test(time));
    primary = () => {
      const choice: AutomationWhenChoice = when === "manual" ? {kind:"manual"} : when.startsWith("event:")
        ? {kind:"event",event_id:when.slice(6),repository:repository.trim()}
        : {kind:"schedule",every:when as "day"|"weekday"|"week"|"hour",time,day:Number(day)};
      void save(() => setAutomationWhen(detail.id,choice));
    };
  } else if (part === "about") {
    immediate = !folder.trim();
    if (happened) rows.push({label:"Event",control:happened});
    for (const source of sources) rows.push({label:source.missing ? "Missing source" : "Source",control:<CheckGadget label={source.label} checked onChange={() => void update({sources:refs.filter((ref) => ref !== source.ref)},false)} disabled={busy} />});
    rows.push({label:"Add source",control:<ListView label="Sources to add" ordered selectedId={sourcePick} onSelect={setSourcePick}
      rows={aboutMatches(happened ? candidates.filter((row) => row.kind === "folder") : candidates,sourceQuery).filter((row) => !refs.includes(row.ref)).map((row) => ({id:row.ref,kind:row.kind,name:row.label}))}
      defaultVerb="add-source" verbs={[{id:"add-source",label:"Add source",key:"Enter",enabled:(row) => Boolean(row) && !busy,run:(row) => { if (row) void update({sources:[...refs,row.id]},false); }}]}
      toolbar={{trailing:<StringGadget label="Find by name" value={sourceQuery} onChange={(value) => { setSourceQuery(value); setSourcePick(null); }} placeholder="Find a source" />}} />});
    if (detail.assignment_summary?.vendor) rows.push({label:"Folder",control:<StringGadget label="Folder" value={folder} onChange={setFolder} placeholder="Repository folder" />});
    primary = () => void save(async () => { const answer = await registerRepository({path:folder.trim()}); await updateWorkbenchField(detail.id,{sources:[...refs,`repository:${answer.repository.id}`]}); if (live.current) setFolder(""); },false);
  } else if (part === "with") {
    if (isProgram) rows.push({label:"Agent",control:<ProgramAgent draft={program} onChange={setProgram} fallback={detail.program?.runs_on_words} />});
    else rows.push({label:detail.do_kind === "hand_to_agent" ? "Agent" : "Engine",control:<CycleGadget label="With" value={profile} onChange={setProfile} options={[
      {value:detail.assignment_summary?.profile_id ?? detail.agent_profile ?? "",label:engineWords(detail) ?? "Choose an engine"},...engines.filter((row) => row.value !== (detail.assignment_summary?.profile_id ?? detail.agent_profile ?? ""))]} />},
      {label:"Spend limit",control:<StringGadget label="Spend limit per run" value={spend} onChange={setSpend} placeholder="Engine's limit" type="number" inputProps={{min:0,step:"0.01"}} />});
    if (detail.do_kind === "hand_to_agent") rows.push({label:"Review by",control:<CycleGadget label="Review by" value={review} onChange={setReview} options={[{value:"none",label:"None"},...agents]} />});
    disabled = !isProgram && (!profile || (Boolean(spend) && (!Number.isFinite(Number(spend)) || Number(spend) < 0)));
    primary = () => void save(async () => {
      if (isProgram) await updateWorkbenchField(detail.id,programFields(program));
      else { const chosen = engines.find((row) => row.value === profile); const profileId = chosen?.engine ? await automationEngineProfile(chosen.engine) : profile; await setAutomationEngine(detail.id,{profile_id:profileId,spend_limit_usd:spend.trim() ? Number(spend) : null}); if (detail.do_kind === "hand_to_agent") await updateWorkbenchField(detail.id,{review_by:review}); }
    });
  } else {
    rows.push({label:"Put it in",control:<CycleGadget label="Put it in" value={target} onChange={setTarget} options={[
      {value:"inbox",label:"My Inbox"},{value:"needs_you",label:"Needs you"},{value:"today",label:"Today"},
      ...(destinations.data ?? []).map((row) => ({value:`destination:${row.id}`,label:row.name})),
    ]} />});
    primary = () => void update({output_target:target});
  }
  return <InspectorForm testId="automation-setup" rows={rows} notice={error || readError || (part === "put" && destinations.failed) ? <SurfaceState error={error || readError || "Destinations not loaded"} onRetry={readError ? () => void readOptions() : part === "put" && destinations.failed ? destinations.reload : undefined} /> : undefined}
    completion={immediate ? {done:onDone} : {cancel:onDone,cancelDisabled:busy,primary:{label:part === "about" ? "Add folder" : "Save",run:primary,disabled,busy,testId:"automation-setup-save"}}} />;
}
