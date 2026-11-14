/** Every answer is recorded from the isolated Activity hub rig. */
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import tape from "./fixtures/activity-grammar.json";
import { ActivityCore } from "../ActivityCore";
const opened=vi.hoisted(()=>vi.fn(()=>true));
vi.mock("../../../desk/shell",()=>({openSurface:opened}));
vi.mock("../../../desk/useDeskChangedRefresh",()=>({ALL_DESK_CHANGE_KINDS:[],useOnDeskChanged:()=>{}}));
let gets:Record<string,unknown>, writes:string[], failure:string, release:(()=>void)|undefined;
const reply=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"Content-Type":"application/json"}});
beforeEach(()=>{
  gets=structuredClone(tape.gets);writes=[];failure="";release=undefined;opened.mockClear();
  vi.stubGlobal("fetch",vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
    const raw=String(input),method=init?.method ?? "GET",url=new URL(raw,"http://desk.test"),path=url.pathname;
    if(method==="GET"){
      if(failure===path)return reply({detail:"Activity not read"},503);
      const lookup=path==="/api/desk/projections" ? "/api/desk/projections?kind=receipt&attention_state=resolved&offset=0&limit=50" : path==="/api/activity/records" ? path+"?limit=100" : path;
      if(path.includes('/dry-run'))return reply(tape.dryRun);
      if(path==="/api/desk/projections" && url.searchParams.get("q"))return reply({...gets[lookup] as object,projections:[],page:{offset:0,limit:50,total:0,has_more:false}});
      return lookup in gets?reply(gets[lookup]):reply({detail:"Unrecorded read"},404);
    }
    writes.push(`${method} ${path}`);
    if(path.endsWith('/recheck'))return reply(tape.recheckRefusal[1],Number(tape.recheckRefusal[0]));
    if(path.endsWith('/refresh')){if(release)await new Promise<void>(done=>{release=done;});return reply(tape.refreshed);}
    if(path.endsWith('/settings')){const enabled=JSON.parse(String(init?.body)).enabled;gets[path.replace('/settings','/status')]=(enabled?tape.watched:tape.paused).status;return reply(enabled?tape.watched:tape.paused);}
    if(method==="DELETE"&&path.endsWith('/records')){gets['/api/activity/records?limit=100']=tape.emptyRecords;return reply(tape.cleared);}
    if(method==="DELETE"&&path.includes('/project-rules/')){gets['/api/activity/project-rules']={rules:[]};return reply(tape.deletedRule);}
    if(path.endsWith('/start'))return reply((tape as unknown as Record<string,[number,unknown]>).candidateStart[1],Number((tape as unknown as Record<string,[number,unknown]>).candidateStart[0]));
    return reply({detail:"Unrecorded write"},400);
  }));
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const press=(name:string)=>fireEvent.click(screen.getByRole("button",{name}));
const view=(name:string)=>fireEvent.click(screen.getByRole("tab",{name}));
async function ready(){render(<ActivityCore/>);await screen.findAllByTestId("activity-row");}
it("opens a read-only collection, gives each row a target and time, and opens the exact receipt",async()=>{
  await ready();expect(writes).toEqual([]);
  const row=screen.getByText("Checked 2 rooms · Heartbeat").closest('[data-object-id]')!;
  expect(row).toHaveTextContent("Another device");
  expect(row.querySelector('.object-list-detail')).toHaveTextContent(/\d/);
  fireEvent.click(row);press("Open receipt");expect(opened).toHaveBeenCalledWith("configure-cadence",undefined);
  expect(writes).toEqual([]);
});
it("keeps an unspaced page identifier in the name and Seen in its second line",async()=>{
  await ready();const row=screen.getAllByTestId("activity-row").find(row=>row.textContent?.includes("activity_saved_revision_"))!;
  expect(row).toBeTruthy();expect(row).toHaveTextContent("Seen");expect(row).not.toHaveTextContent("Seen…");
});
it("refreshes once, and Watching changes only after the explicit press",async()=>{
  await ready();expect(writes).toEqual([]);
  const initial=tape.gets['/api/activity/status'].settings.enabled ? "Pause watching" : "Start watching";
  const changed=initial==="Pause watching"?"Start watching":"Pause watching";
  await waitFor(()=>expect(screen.getByRole("button",{name:initial})).toBeEnabled());
  press(initial);await waitFor(()=>expect(screen.getByRole("button",{name:changed})).toBeEnabled());
  press(changed);await waitFor(()=>expect(screen.getByRole("button",{name:initial})).toBeEnabled());
  press("Refresh now");await waitFor(()=>expect(writes.filter(path=>path.endsWith('/refresh'))).toHaveLength(1));
});
it("clear has one in-window question, Cancel keeps records and Clear retains receipts",async()=>{
  await ready();press("Clear records");expect(screen.getByRole("region",{name:"Clear all records?"})).toBeVisible();press("Cancel");expect(writes).toEqual([]);
  press("Clear records");const region=screen.getByRole("region",{name:"Clear all records?"});fireEvent.click(region.querySelector('button[data-variant="danger"]') ?? [...region.querySelectorAll('button')].find(button=>button.textContent==='Clear records')!);
  await waitFor(()=>expect(screen.getAllByTestId("activity-row").every(row=>row.id.startsWith('activity-receipt-'))).toBe(true));
});
it("Rules delete is bound to the selected row and has a Cancel door",async()=>{
  await ready();view("Rules");fireEvent.click(await screen.findByTestId("activity-row"));press("Delete");press("Cancel");expect(writes).toEqual([]);press("Delete");
  const question=screen.getByRole("region",{name:"Delete this rule?"});fireEvent.click([...question.querySelectorAll('button')].find(button=>button.textContent==='Delete')!);
  await screen.findByText("No rules yet");expect(writes[0]).toMatch(/^DELETE \/api\/activity\/project-rules\//);
});
it("Candidate start renders the hub refusal and keeps the candidate",async()=>{
  await ready();view("Candidates");fireEvent.click(await screen.findByTestId("activity-row"));press("Start meeting");
  expect(await screen.findByRole("alert")).toBeVisible();expect(screen.getByTestId("activity-row")).toBeVisible();
});
it("Connectors dry run renders its answer; recheck happens only on its verb",async()=>{
  await ready();view("Connectors");fireEvent.click((await screen.findAllByTestId("activity-row"))[0]);press("Dry run");await screen.findByText("Dry run",{selector:'.gadget-row-label'});
  expect(writes).toEqual([]);press("Recheck Confluence");await waitFor(()=>expect(writes).toContain("POST /api/connections/confluence/recheck"));
  expect(await screen.findByText(/Confluence:/)).toHaveTextContent("never checked");press("Open Accounts");expect(opened).toHaveBeenCalledWith("configure-settings","accounts");
});
it("keeps the failed read distinct from empty and retries the saved read",async()=>{
  failure="/api/activity/records";render(<ActivityCore/>);expect(await screen.findByRole("alert")).toHaveTextContent("Activity not read");
  expect(screen.queryByText("No activity yet")).toBeNull();failure="";press("Try again");await screen.findAllByTestId("activity-row");expect(writes).toEqual([]);
});

it("pages receipts beside watched pages without skipping the receipt offset",async()=>{
  const initialFetch=fetch, reads:number[]=[];
  const envelope=structuredClone(tape.gets['/api/desk/projections?kind=receipt&attention_state=resolved&offset=0&limit=50']);
  const receipt=envelope.projections[0];
  vi.stubGlobal("fetch",vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
    const url=new URL(String(input),"http://desk.test");
    if(url.pathname!=="/api/desk/projections")return initialFetch(input,init);
    const offset=Number(url.searchParams.get("offset"));reads.push(offset);
    const count=offset===0?50:1;
    return reply({...envelope,projections:Array.from({length:count},(_,index)=>({...receipt,id:`page-${offset+index}`})),page:{offset,limit:50,total:51,has_more:offset===0}});
  }));
  await ready();press("Load more");
  await waitFor(()=>expect(screen.getAllByTestId("activity-row")).toHaveLength(101));
  expect(reads).toEqual([0,50]);
});
it("dispatches one Refresh even before a pending write repaints its button",async()=>{
  const initialFetch=fetch;let finish!:()=>void;let dispatches=0;
  vi.stubGlobal("fetch",vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
    if(String(input).endsWith('/activity/refresh')&&init?.method==="POST"){
      dispatches++;await new Promise<void>(done=>{finish=done;});return reply(tape.refreshed);
    }
    return initialFetch(input,init);
  }));
  await ready();const refresh=screen.getByRole('button',{name:'Refresh now'});
  act(()=>{refresh.click();refresh.click();});expect(dispatches).toBe(1);
  await act(async()=>finish());await waitFor(()=>expect(refresh).toBeEnabled());
});

it("keeps receipt sorting in the shared header and Sort menu",async()=>{
  await ready();
  fireEvent.click(screen.getByRole("button",{name:"What"}));
  const first=screen.getAllByTestId("activity-row")[0];
  expect(first).toHaveTextContent("activity_saved_revision_");
  press("Actions ▾");
  expect(screen.getByRole("menuitem",{name:/Sort: name/})).toBeVisible();
});

it("distinguishes repeated page titles by the hub's saved URLs",async()=>{
  const pages=structuredClone(tape.gets['/api/activity/records?limit=100']);
  pages.records[0].title=pages.records[1].title="Read architecture notes";
  gets['/api/activity/records?limit=100']=pages;
  await ready();
  for(const page of pages.records.slice(0,2)){
    const row=document.getElementById(`activity-record-${page.id}`)!;
    expect(row.querySelector('.object-list-selection-name')).toHaveAttribute('title',page.url);
    expect(row).toHaveTextContent("Seen");
  }
});
