/* One link list and one editor for the selected person. Writes keep their captured target. */
import { useEffect, useRef, useState } from "react";
import { ActionNotice, CycleGadget, InspectorFacts, InspectorForm, InspectorQuestion, ListPane, ListView, PaneInspector, PreferencePane, StringGadget, SurfaceState, type ListVerb } from "../../desk/surface";
import * as hub from "../../desk/people/api";
import { wireWords } from "../../desk/surface/words";
import { keptDraft, useDeskDraft } from "../../desk/deskMemory";
import { useDesk } from "../../desk/store";
import { shortWhen, type Commitment, type ExecutionItem, type Project, type RelationshipDetail, type UpcomingEvent, type Workbench } from "./peopleModel";

type LinkRow = {id:string; name:string; kind:"project"|"calendar"|"alias"; value:string; source?:string; detail?:string};
export function PersonLinks({relationship,onRefresh,onProtectedFailure,onArchived}: {relationship:RelationshipDetail;onRefresh():void;onProtectedFailure(cause:unknown):void;onArchived():void}) {
  const [projects,setProjects]=useState<Project[]>([]),[events,setEvents]=useState<UpcomingEvent[]>([]);
  const [loading,setLoading]=useState(true),[readError,setReadError]=useState("");
  const [attempt,setAttempt]=useState(0),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  const [picked,setPicked]=useState<string|null>(null),[mode,setMode]=useState<LinkRow["kind"]|null>(null),[armed,setArmed]=useState<string|null>(null);
  const aliasKey=`people/alias/${relationship.id}`;
  const [alias,setAlias,forgetAlias]=useDeskDraft(aliasKey);
  const [projectId,setProjectId]=useState(""),[eventId,setEventId]=useState("");
  const pending=useRef(false),mounted=useRef(true);
  const current=useRef({picked,mode,alias,projectId,eventId}); current.current={picked,mode,alias,projectId,eventId};
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
  useEffect(()=>{
    let live=true;setLoading(true);setReadError("");
    void hub.readUpcoming<UpcomingEvent>().then(answer=>{if(live)setEvents((answer.upcoming??[]).filter(row=>row.uid&&row.source==="calendar_event"));})
      .catch(()=>{if(live)setReadError("Calendar could not be read.");}).finally(()=>{if(live)setLoading(false);});
    void hub.readProjects<Project>().then(answer=>{if(live){setProjects(answer.projects??[]);setProjectId(id=>id||answer.projects?.[0]?.id||"");}})
      .catch(cause=>{if(live)onProtectedFailure(cause);});
    return()=>{live=false;};
  },[relationship.id,attempt]);
  const rows:LinkRow[]=[
    ...(relationship.project_refs??[]).map(id=>({id:`project:${id}`,kind:"project" as const,name:projects.find(row=>row.id===id)?.name??"Project",value:id})),
    ...(relationship.calendar_links??[]).map(row=>({id:`calendar:${row.uid}:${row.source_id}`,kind:"calendar" as const,name:row.label||"Linked series",value:row.uid,source:row.source_id})),
    ...(relationship.owner_aliases??[]).map(value=>({id:`alias:${value}`,kind:"alias" as const,name:value,value})),
  ];
  const selected=rows.find(row=>row.id===picked)??null;
  const linkedKeys=new Set((relationship.calendar_links??[]).map(row=>`${row.uid}:${row.source_id}`));
  const available=events.filter(row=>!linkedKeys.has(`${row.uid}:${row.source_id}`)).sort((a,b)=>Number(b.title.toLowerCase().includes(relationship.display_name.toLowerCase()))-Number(a.title.toLowerCase().includes(relationship.display_name.toLowerCase())));
  const event=available.find(row=>row.id===eventId);
  const act=async(work:()=>Promise<unknown>,after?:()=>void)=>{
    if(pending.current)return;pending.current=true;setBusy(true);setError("");
    try{await work();if(mounted.current){after?.();onRefresh();}}catch(cause){if(mounted.current){setError("Not saved; your choice stays, try again.");onProtectedFailure(cause);}}
    finally{pending.current=false;if(mounted.current)setBusy(false);}
  };
  const edit=(next:LinkRow["kind"])=>{setMode(next);setArmed(null);setError("");};
  const verbs:ListVerb[]=[
    { enabled: () => true,id:"project",label:"Link project",run:()=>edit("project")},
    { enabled: () => true,id:"calendar",label:"Link calendar event",testId:"people-link-event",run:()=>edit("calendar")},
    { enabled: () => true,id:"alias",label:"Add name",run:()=>edit("alias")},
    {id:"remove",label:selected?.kind==="alias"?"Remove":"Unlink",enabled:row=>Boolean(row)&&!busy,run:()=>{setMode(null);setArmed(selected?.id??null);setError("");}},
    {id:"archive",label:"Archive person",enabled:()=>!busy,run:()=>{setMode(null);setArmed("archive");setError("");}},
  ];
  const question=armed==="archive"?`Archive ${relationship.display_name}?`:selected&&armed===selected.id?`${selected.kind==="alias"?"Remove":"Unlink"} ${selected.name}?`:null;
  const target=JSON.stringify([relationship.id,relationship,armed,selected?.id]);
  const remove=()=>void act(()=>armed==="archive"?hub.archivePerson(relationship.id):selected?.kind==="project"?hub.unlinkProject(relationship.id,selected.value):selected?.kind==="calendar"?hub.unlinkSeries(relationship.id,selected.value,selected.source!):hub.unlinkAlias(relationship.id,selected!.value),()=>{setArmed(null);setPicked(null);if(armed==="archive")onArchived();});
  const save=()=>{
    const submitted={...current.current};
    if(mode==="alias"&&!alias.trim()||mode==="project"&&!projectId||mode==="calendar"&&!event)return;
    void act(()=>mode==="alias"?hub.linkAlias(relationship.id,alias.trim()):mode==="project"?hub.linkProject(relationship.id,projectId):hub.linkSeries(relationship.id,event!.uid,event!.source_id,event!.title),()=>{
      if(submitted.mode==="alias"&&(keptDraft(aliasKey)??"")===submitted.alias)forgetAlias();
      if(current.current.mode===submitted.mode&&current.current.alias===submitted.alias&&current.current.projectId===submitted.projectId&&current.current.eventId===submitted.eventId)setMode(null);
    });
  };
  return <PreferencePane label="Links" testId="people-links" data-feedback-redact="true"><ListPane label="Selected link" list={<ListView label="Person links" headerless ordered rows={rows.map(row=>({...row,cells:{type:row.kind==="alias"?"Name in meeting notes":row.kind==="calendar"?"Calendar series":"Project"}}))}
    columns={[{key:"name",word:"Link",priority:10},{key:"type",word:"Kind",priority:1}]} selectedId={selected?.id??null} onSelect={id=>{setPicked(id);setMode(null);setArmed(null);setError("");}} verbs={verbs} />}>
    {question?<InspectorQuestion actionId={armed==="archive"?"archive-person":"remove-link"} targetId={target} question={question} cancel={()=>{setArmed(null);setError("");}} verb={{label:armed==="archive"?"Archive":selected?.kind==="alias"?"Remove":"Unlink",busy,run:remove}} notice={error?<ActionNotice tone="danger" role="alert">{error}</ActionNotice>:undefined}/>
    :mode?<PaneInspector label={mode==="project"?"Link project":mode==="calendar"?"Link calendar event":"Name in meeting notes"}><InspectorForm testId={mode==="calendar"?"people-event-picker":mode==="alias"?"people-alias-add":"people-project-link"}
      rows={mode==="alias"?[{label:"Name",control:<StringGadget label="Name in meeting notes" value={alias} onChange={setAlias}/>}]:mode==="project"?[{label:"Project",control:<CycleGadget roster label="Project" value={projectId} onChange={setProjectId} options={projects.map(row=>({value:row.id,label:row.name}))}/>}]:[{label:"Event",control:loading?<SurfaceState loading/>:readError?<SurfaceState error={readError} onRetry={()=>setAttempt(n=>n+1)}/>:available.length?<ListView label="Calendar events" ordered headerless rows={available.map(row=>({id:row.id,kind:"meeting",name:row.title,detail:[row.title.toLowerCase().includes(relationship.display_name.toLowerCase())?"Suggested":"",shortWhen(row.starts_at),row.source_label].filter(Boolean).join(" · ")}))} columns={[{key:"name",word:"Event"}]} selectedId={eventId} onSelect={setEventId}/>:<SurfaceState empty emptyLabel="No upcoming events"/>}]}
      notice={error?<ActionNotice tone="danger" role="alert">{error}</ActionNotice>:undefined} completion={{cancel:()=>setMode(null),primary:{label:mode==="alias"?"Add":"Link",busy,disabled:busy||(mode==="alias"?!alias.trim():mode==="project"?!projectId||relationship.project_refs?.includes(projectId):!event),run:save}}}/></PaneInspector>
    :selected?<InspectorFacts name={selected.name} rows={[{label:"Kind",value:selected.kind==="alias"?"Name in meeting notes":selected.kind==="calendar"?"Calendar series":"Project"}]} data-feedback-redact="true"/>:<InspectorFacts name="Links" header={false} rows={rows.length?[]:[{label:"Links",value:"No links"}]}/>}
  </ListPane></PreferencePane>;
}

export function CommitmentInspector({commitment,onClose,onRefresh,onProtectedFailure}:{commitment:Commitment;onClose():void;onRefresh():void;onProtectedFailure(cause:unknown):void}) {
  const [workbenches,setWorkbenches]=useState<Workbench[]>([]),[workbenchId,setWorkbenchId]=useState("");
  const [items,setItems]=useState<ExecutionItem[]>([]),[rationale,setRationale]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");
  const [action,setAction]=useState("send");
  const [readFailed,setReadFailed]=useState(false);
  const pending=useRef(false);
  const load=async()=>{setReadFailed(false);try{const [catalog,execution]=await Promise.all([hub.readWorkbenches<Workbench>(),hub.readExecution<ExecutionItem>(commitment.id)]);setWorkbenches(catalog.workbenches??[]);setItems(execution.items??[]);setAction(current=>execution.items?.length&&current==="send"?"open":current);setWorkbenchId(current=>current||catalog.workbenches?.[0]?.id||"");}catch(cause){setReadFailed(true);setError("Automation could not be read; the commitment stays, try again.");onProtectedFailure(cause);}};
  useEffect(()=>{void load();},[commitment.id]);
  const linked=items[0];
  const run=async()=>{
    if(action==="open"&&linked){useDesk.getState().openWorkbenchWindow(linked.workbench_id);return;}
    if(pending.current)return;pending.current=true;setBusy(true);setError("");
    try{if(action==="send"){await hub.sendToWorkbench(commitment.id,workbenchId);await load();}else{await hub.satisfyCommitment(commitment.id,rationale.trim());onRefresh();}}
    catch(cause){setError("Not saved; your note stays, try again.");onProtectedFailure(cause);}finally{pending.current=false;setBusy(false);}
  };
  return <InspectorForm testId="people-commitment-inspector" facts={{name:"Commitment facts",testId:"people-commitment-facts","data-feedback-redact":true,rows:[
      ...(!linked?[{label:"Words",value:commitment.body}]:[]),
      ...(linked?[{label:"Automation",value:<>{workbenches.find(row=>row.id===linked.workbench_id)?.name??"Automation"} · <span>{wireWords(linked.status)}</span></>},...(linked.result?[{label:"Result",value:linked.result}]:[])]:[]),
    ]}} rows={[
    {label:"Action",control:<CycleGadget label="Commitment action" value={action} onChange={setAction} options={[linked?{value:"open",label:"Open automation"}:{value:"send",label:"Send to automation"},{value:"satisfy",label:"Mark satisfied"}]}/>},
    ...(action==="send"?[{label:"Automation",control:<CycleGadget roster label="Automation" value={workbenchId} onChange={setWorkbenchId} options={workbenches.map(row=>({value:row.id,label:row.name}))}/>}]:action==="satisfy"?[{label:"Note",control:<StringGadget label="Satisfaction note" value={rationale} onChange={setRationale} placeholder="What fulfilled the commitment?"/>}]:[]),
  ]} notice={error?<ActionNotice role="alert" tone="danger" action={readFailed?{label:"Try again",onClick:()=>void load()}:undefined}>{error}</ActionNotice>:undefined} completion={{cancel:onClose,primary:{label:action==="send"?"Send to automation":action==="open"?"Open automation":"Mark satisfied",busy,disabled:busy||(action==="send"&&!workbenchId),run:()=>void run()}}}/>;
}
