import { createElement } from "react";
import type { DeskProjection } from "../../desk/projections";
import { deSnake, wireDayClock, type ObjectListRow } from "../../desk/surface";
export type ActivityKind = "records" | "rules" | "candidates" | "connectors";
export type ActivityItem = {id:string;kind:ActivityKind;raw:Record<string,unknown>;receipt?:DeskProjection;name?:string};
/** Repeated browser titles use the saved URL so separate visits have separate names. */
export function activityItems(rows:readonly Record<string,unknown>[],kind:ActivityKind):ActivityItem[] {
  const names=new Map<string,number>();
  const title=(row:Record<string,unknown>)=>String(row.title||row.name||row.label||"");
  for(const row of rows)names.set(title(row),(names.get(title(row))??0)+1);
  return rows.map((raw,index)=>({id:kind==="records"?`record:${raw.id??index}`:String(raw.id??index),kind,raw,
    name:kind==="records"&&raw.url&&(names.get(title(raw))??0)>1?String(raw.url):undefined}));
}
/** Only exact source doors with a current consumer open another window. */
export function receiptDoor(row: DeskProjection): {key:string;scope?:string}|null {
  if(row.detail_url === "/cadence")return {key:"configure-cadence"};
  if(!row.detail_url.startsWith("/history?")||row.detail_url.includes("#"))return null;
  const params=new URLSearchParams(row.detail_url.slice("/history?".length)), meeting=params.get("meeting");
  return params.size===1 && meeting && row.subject_ref===`meeting:${meeting}` ? {key:"review-meetings",scope:row.subject_ref}:null;
}
export const activityWords=(value:unknown)=>{const special:Record<string,string>={cli_enrichment:"Enrich with the CLI",candidate_inference:"Find meeting candidates",github_pull_request:"GitHub pull request",github_issue:"GitHub issue",jira_issue:"Jira issue"};if(special[String(value)])return special[String(value)];const text=deSnake(String(value??""));return text?text[0].toUpperCase()+text.slice(1):"";};
export function activityRow(item:ActivityItem):ObjectListRow {
  const row=item.raw, receipt=item.receipt;
  if(receipt){
    const title=receipt.source_kind==="pipeline_event"?activityWords(receipt.title):receipt.title;
    const outcome=activityWords(receipt.outcome)||"Done", lower=(receipt.outcome||"").toLowerCase();
    const tone=/fail|error|refus|denied|blocked/.test(lower)?"fail":/warn|partial|skip|held/.test(lower)?"warn":/complet|final|done|sent|saved|ok|ran|success/.test(lower)?"ok":"info";
    return {id:item.id,kind:"artifact",name:[title,receipt.subject_label].filter(Boolean).join(" · "),
      detail:createElement("span",null,createElement("span",null,receipt.origin==="remote"?"Another device":"You"),` · ${wireDayClock(receipt.timestamp)}`),
      when:wireDayClock(receipt.timestamp),whenSort:Date.parse(receipt.timestamp)||0,sortValues:{who:receipt.origin==="remote"?"Another device":"You"},
      state:{label:outcome,tone},nameTestId:`activity-receipt-name-${item.id}`};
  }
  const target=item.name||String(row.title||row.name||row.label||row.url||row.domain||row.pattern||row.id||"Activity item");
  const name=target;
  const stamp=String(row.occurred_at||row.last_seen_at||row.starts_at||row.last_run_at||row.updated_at||row.created_at||"");
  const cli=row.cli_status as {available?:boolean}|undefined;
  const state=row.last_error?"Failed":row.enabled===false?"Off":item.kind==="connectors"&&row.requires_cli&&cli?.available===false?"CLI not found":String(row.status||(row.enabled===true||item.kind==="connectors"?"On":""));
  return {id:item.id,kind:item.kind==="rules"?"project":"artifact",name,when:wireDayClock(stamp),whenSort:Date.parse(stamp)||0,sortValues:{who:"You"},
    detail:item.kind==="records"?createElement("span",null,createElement("span",null,"Seen"),` · ${activityWords(row.source_browser || row.entity_type)} · ${wireDayClock(stamp)}`):undefined,
    state:state?{label:activityWords(state),tone:row.last_error?"fail":row.enabled===false?"idle":"info"}:undefined};
}
