/** Activity: one selection list, one source of each verb, no work on open. */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import type { CoreProps } from "./core-types";
import type { DeskProjection } from "../../desk/projections";
import { openSurface } from "../../desk/shell";
import { ALL_DESK_CHANGE_KINDS, useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { ActionNotice, InspectorFacts, InspectorQuestion, ListApp, PreferencePane, SegmentedTabs, useListApp, useWindowMast, countWords, wireDayClock, type ListVerb, type ObjectListRow } from "../../desk/surface";
import { recheckProvider } from "./connections/api";
import { ShowMe } from "../../desk/walk/ShowMe";
import { activityRow, activityItems, activityWords, receiptDoor, type ActivityItem, type ActivityKind } from "./activityModel";

const VIEWS = [{id:"records",label:"Records"},{id:"rules",label:"Rules"},{id:"candidates",label:"Candidates"},{id:"connectors",label:"Connectors"}];
type Rows = Record<string, unknown>[];
export function ActivityCore(_props: CoreProps) {
  const [view, setView] = useState<ActivityKind>("records");
  return <PreferencePane label="Activity"><SegmentedTabs label="Activity views" tabs={VIEWS} value={view} onChange={id => setView(id as ActivityKind)}><ActivityList key={view} view={view} /></SegmentedTabs></PreferencePane>;
}
function ActivityList({view}: {view: ActivityKind}) {
  const [enabled,setEnabled] = useState(false), [busy,setBusy] = useState(false), [notice,setNotice] = useState("");
  const [question,setQuestion] = useState<{id:string;target:string}|null>(null);
  const [dryRun,setDryRun] = useState<unknown>(null);
  const pending=useRef(false);
  const [account,setAccount]=useState("");
  const [sort,setSort]=useState<{key:string;dir:"asc"|"desc"}>({key:"when",dir:"desc"});
  const readStatus = useCallback(async () => {
    const answer=await apiFetch<{settings?:{enabled?:boolean}}>("/api/activity/status");
    setEnabled(Boolean(answer.settings?.enabled));
  },[]);
  useEffect(()=>{void readStatus().catch(error=>setNotice(readableError(error)));},[readStatus]);
  const read = useCallback(async ({query,offset,limit}:{query:string;offset:number;limit:number}) => {
    if (view === "records") {
      const watched=await apiFetch<{records?:Rows;items?:Rows}>("/api/activity/records?limit=100");
      const pages=(watched.records ?? watched.items ?? []).filter(row=>!query||JSON.stringify(row).toLocaleLowerCase().includes(query.toLocaleLowerCase()));
      const params=new URLSearchParams({kind:"receipt",attention_state:"resolved",offset:String(Math.max(0,offset-pages.length)),limit:String(limit)});
      if(query)params.set("q",query);
      const answer=await apiFetch<{projections:DeskProjection[];page:{total:number}}>(`/api/desk/projections?${params}`);
      return {rows:[...answer.projections.map(receipt=>({id:receipt.id,kind:view,raw:receipt as unknown as Record<string,unknown>,receipt})),...(offset ? [] : activityItems(pages,view))] as ActivityItem[],total:answer.page.total+pages.length};
    }
    const path=view === "rules" ? "project-rules" : view === "candidates" ? "meeting-candidates" : "enrichment/connectors";
    const answer=await apiFetch<Record<string,Rows>>(`/api/activity/${path}`);
    const rows:ActivityItem[]=activityItems(answer[view] ?? [],view);
    return {rows:rows.filter(row=>!query||JSON.stringify(row.raw).toLocaleLowerCase().includes(query.toLocaleLowerCase()))};
  },[view]);
  const app=useListApp({read,keyOf:row=>row.id});
  useOnDeskChanged(()=>void app.reload(),ALL_DESK_CHANGE_KINDS);
  useWindowMast({line:app.page ? countWords(app.total,view === "records" ? "record" : view === "rules" ? "rule" : view === "candidates" ? "candidate" : "connector") ?? undefined : undefined});
  const binding=JSON.stringify(view === "rules" ? app.selected?.raw : app.rows.filter(row=>!row.receipt).map(row=>row.raw));
  useEffect(()=>{if(question && question.target!==binding)setQuestion(null);},[binding,question]);
  const act=async(write:()=>Promise<unknown>,done="")=>{
    if(pending.current)return;pending.current=true;setBusy(true);setNotice("");
    try {await write();if(done)setNotice(done);setQuestion(null);await app.reload();await readStatus();}
    catch(error){setNotice(readableError(error));}finally{pending.current=false;setBusy(false);}
  };
  const selected=(row:ObjectListRow|null)=>app.rows.find(item=>item.id===row?.id);
  const open=(row:ObjectListRow|null)=>{
    const item=selected(row),door=item?.receipt && receiptDoor(item.receipt);
    if(!door || !openSurface(door.key,door.scope))setNotice("Receipt view unavailable");
  };
  const verbs:ListVerb[]=[
    {id:"sort",toolbar:false,run:()=>{},label:`Sort: ${sort.key==="when"?(sort.dir==="desc"?"newest":"oldest"):sort.key==="state"?"outcome":sort.key}`,enabled:()=>true,items:[{id:"newest",label:"Newest first",enabled:()=>true,run:()=>setSort({key:"when",dir:"desc"})},{id:"oldest",label:"Oldest first",enabled:()=>true,run:()=>setSort({key:"when",dir:"asc"})},{id:"by-name",label:"Name",enabled:()=>true,run:()=>setSort({key:"name",dir:"asc"})},{id:"by-who",label:"Who",enabled:()=>true,run:()=>setSort({key:"who",dir:"asc"})},{id:"by-outcome",label:"Outcome",enabled:()=>true,run:()=>setSort({key:"state",dir:"asc"})}]},
    {id:"refresh",label:"Refresh now",enabled:()=>!busy,run:()=>void act(()=>apiFetch("/api/activity/refresh",{method:"POST",json:{}}))},
    {id:"watch",label:enabled?"Pause watching":"Start watching",testId:"activity-watching",enabled:()=>!busy,run:()=>void act(()=>apiFetch("/api/activity/settings",{method:"PUT",json:{enabled:!enabled}}))},
    ...(view === "records" ? [
      {id:"open",label:"Open receipt",testId:"activity-open-receipt",key:"Enter",enabled:(row:ObjectListRow|null)=>Boolean(selected(row)?.receipt),run:open},
      {id:"clear",label:"Clear records",enabled:()=>!busy && app.rows.some(row=>!row.receipt),run:()=>setQuestion({id:"clear",target:binding})},
      {id:"more",label:"Load more",enabled:()=>!app.more && app.rows.length<app.total,run:()=>void app.showMore()},
    ] : view === "rules" ? [{id:"delete",label:"Delete",key:"Delete",enabled:(row:ObjectListRow|null)=>Boolean(row)&&!busy,run:()=>setQuestion({id:"delete",target:binding})}]
    : view === "candidates" ? [{id:"start",label:"Start meeting",enabled:(row:ObjectListRow|null)=>Boolean(row)&&selected(row)?.raw.status!=="started"&&!busy,run:(row:ObjectListRow|null)=>void act(()=>apiFetch(`/api/activity/meeting-candidates/${encodeURIComponent(row!.id)}/start`,{method:"POST",json:{}}))}]
    : [
      {id:"dry-run",label:"Dry run",enabled:(row:ObjectListRow|null)=>Boolean(row)&&!busy,run:(row:ObjectListRow|null)=>void act(async()=>setDryRun(await apiFetch(`/api/activity/enrichment/connectors/${encodeURIComponent(row!.id)}/dry-run?limit=25`)))},
      {id:"recheck",label:"Recheck Confluence",enabled:()=>!busy,run:()=>void act(async()=>{const tool=await recheckProvider("confluence");setAccount(tool?.state.replaceAll("_"," ") ?? "Not read");})},
      {id:"accounts",label:"Open Accounts",enabled:()=>true,run:()=>{openSurface("configure-settings","accounts");}},
    ]),
  ];
  return <ListApp app={app} label="Activity" row={activityRow}
    ids={{windowTestId:"activity-window",listTestId:"activity-list",paneTestId:"activity-pane",toolbarTestId:"activity-toolbar",statusTestId:"activity-status"}}
    words={{find:"Find activity",empty:view==="rules"?"No rules yet":"No activity yet",noMatch:"No activity matches"}}
    list={{ordered:false,sort,onSort:key=>setSort(current=>({key,dir:current.key===key&&current.dir==="asc"?"desc":"asc"})),columns:[{key:"name",word:"What",track:"minmax(0, 1fr)",minWidth:180,priority:100},...(app.visible.some(item=>activityRow(item).state) ? [{key:"state",word:"Outcome",track:"max-content",minWidth:80,priority:20}] : [])],verbs,defaultVerb:view==="records"?"open":undefined,onOpen:id=>open(activityRow(app.rows.find(row=>row.id===id)!)),rowProps:item=>({id:item.id.startsWith("record:")?`activity-${item.id.replace(":","-")}`:`activity-receipt-${item.id}`,"data-testid":"activity-row"})}}
    onSelect={()=>{setQuestion(null);setDryRun(null);setNotice("");}}
    notice={notice ? <ActionNotice role="alert" tone="danger">{notice}</ActionNotice> : undefined}
    pane={item=>question ? <InspectorQuestion actionId={question.id} targetId={question.target} question={question.id==="clear"?"Clear all records?":"Delete this rule?"} cancel={()=>setQuestion(null)} verb={{label:question.id==="clear"?"Clear records":"Delete",busy,run:()=>void act(()=>apiFetch(question.id==="clear"?"/api/activity/records":`/api/activity/project-rules/${encodeURIComponent(item!.id)}`,{method:"DELETE"}))}} />
      :item ? <InspectorFacts data-feedback-redact="true" name={activityRow(item).name} rows={[
        ...(item.receipt ? [{label:"What",value:item.receipt.summary},{label:"To",value:item.receipt.subject_label},{label:"When",value:wireDayClock(item.receipt.timestamp)},{label:"By",value:item.receipt.origin==="remote"?"Another device":"You"}]
          :Object.entries(item.raw).filter(([key,value])=>["title","name","domain","url","pattern","source","source_browser","entity_type","status","last_error","last_seen_at","occurred_at","starts_at","kind","label","enabled"].includes(key)&&value!=null).map(([key,value])=>({label:key.replaceAll("_"," "),paths:key==="url",value:typeof value==="boolean"?(value?"On":"Off"):["last_seen_at","occurred_at","starts_at"].includes(key)?wireDayClock(String(value)):["source_browser","entity_type","status","kind"].includes(key)?activityWords(value):String(value)}))),
        ...(dryRun ? (()=>{const preview=(dryRun as {dry_run:{proposed_annotations:unknown[];proposed_candidates:unknown[];commands:{command?:string[]}[];warnings:string[]}}).dry_run;const changes=preview.proposed_annotations.length+preview.proposed_candidates.length;return [{label:"Dry run",value:changes ? `${changes} changes` : "No changes"},{label:"Commands",value:preview.commands.map(command=>command.command?.join(" ") ?? "").filter(Boolean).join(" · ")},{label:"Notice",value:preview.warnings.map(word=>word.split(". ")[0]).join(" · ")}];})() : []),
      ]} /> : null}
    status={[{text:countWords(app.total,"item")},!enabled&&{text:"Watching paused"},Boolean(account)&&{text:`Confluence: ${account}`}]}><ShowMe app="inspect-activity" /></ListApp>;
}
