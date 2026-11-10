import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AutomationsCore } from "../components/automation/AutomationsCore";
import { useDesk } from "../store";
import { EMPTY_ITEMS } from "../api";
import type { AutomationDetail } from "../components/automation/model";
import home from "./fixtures/automation-hub/home-rows.json";
import starters from "./fixtures/automation-hub/starters.json";
import blank from "./fixtures/automation-hub/blank-sentence.json";
import friday from "./fixtures/automation-hub/friday-new.json";
import program from "./fixtures/automation-hub/program-still.json";

const recordedDetail = (recording: {workbench_id:string; gets:Record<string,unknown>}) => (recording.gets[`/api/workbenches/${recording.workbench_id}`] as {workbench:AutomationDetail}).workbench;
const initial = home.gets["/api/workbenches"].workbenches as unknown as AutomationDetail[];
const json = (body:unknown,status=200) => new Response(JSON.stringify(body),{status,headers:{"Content-Type":"application/json"}});
let rows: AutomationDetail[];
let fail: string;
let writes: Array<{url:string;method:string;body:Record<string,unknown>}>;
let hold: null | (() => void);
let calls: number;
let next: AutomationDetail | null;
function fetchHub(input:RequestInfo|URL, init?:RequestInit): Promise<Response> {
  const url = String(input), method = init?.method ?? "GET";
  if (method === "GET") {
    if (url === "/api/workbenches") return Promise.resolve(json({workbenches:structuredClone(rows)}));
    if (url === "/api/workbench-templates") return Promise.resolve(json(starters.gets["/api/workbench-templates"]));
    if (url.startsWith("/api/workbenches/")) return Promise.resolve(json({workbench:structuredClone(rows.find((row) => url.endsWith(row.id)))}));
    if (url === "/api/people/relationships") return Promise.resolve(json({relationships:[]}));
    if (url === "/api/channels/destinations") return Promise.resolve(json({destinations:[]}));
    if (url === "/api/channels/sends") return Promise.resolve(json({sends:[]}));
    throw new Error(`Unrecorded read ${url}`);
  }
  const body = init?.body ? JSON.parse(String(init.body)) : {};
  writes.push({url,method,body});
  if (fail === method || fail === url) return Promise.resolve(json({error:"Unavailable"},503));
  if (url.endsWith("/instantiate")) {
    const detail = recordedDetail(friday);
    rows = [structuredClone(detail)];
    return Promise.resolve(json({workbench:detail}));
  }
  if (method === "DELETE") { rows = rows.filter((row) => !url.endsWith(row.id)); return Promise.resolve(json({success:true})); }
  if (method === "PUT") {
    const answer = () => { if (next) rows = [structuredClone(next)]; return json({workbench:rows[0]}); };
    if (hold) return new Promise((resolve) => { hold = () => resolve(answer()); });
    return Promise.resolve(answer());
  }
  if (url.endsWith("/run")) { calls += 1; return new Promise((resolve) => { hold = () => resolve(json({run:{}})); }); }
  if (url.endsWith("/park")) return Promise.resolve(json({}));
  throw new Error(`Unrecorded write ${method} ${url}`);
}
beforeEach(() => {
  rows = structuredClone(initial); fail = ""; writes = []; hold = null; calls = 0; next = null;
  useDesk.setState({places:{},items:EMPTY_ITEMS,workbenchWindows:[],refresh:vi.fn(async () => undefined)});
  vi.stubGlobal("fetch",vi.fn(fetchHub));
});
afterEach(() => vi.unstubAllGlobals());
const row = () => screen.getByRole("row",{name:/Friday team update/});
const button = (name:string) => screen.getByRole("button",{name});
async function openList() { render(<AutomationsCore />); if (rows.length) await screen.findByTestId("automation-home-count"); else await waitFor(() => expect(screen.queryByText("Loading")).not.toBeInTheDocument()); }

describe("Automations selection grammar",() => {
  it("selects one row, keeps plain facts below it and opens only on Return",async () => {
    await openList();
    expect(screen.getByText("Select an automation.")).toBeInTheDocument();
    expect(screen.getAllByRole("columnheader").map((node) => node.textContent)).toEqual(["Automation","Runs","Last run","Next run"]);
    fireEvent.click(row());
    expect(row()).toHaveAttribute("aria-selected","true");
    expect(useDesk.getState().workbenchWindows).toEqual([]);
    expect(screen.getByTestId("automation-summary")).toHaveTextContent("Every Friday at 15:00");
    expect(row().querySelector("button")).toBeNull();
    expect(row().querySelector(".surface-spine")).toBeNull();
    expect(screen.queryByTestId("automation-mast")).toBeNull();
    fireEvent.click(within(screen.getByTestId("automation-summary")).getByRole("button",{name:"Done"}));
    expect(screen.getByText("Select an automation.")).toBeInTheDocument();
    fireEvent.click(row());
    fireEvent.keyDown(row(),{key:"Enter"});
    expect(useDesk.getState().workbenchWindows.map((entry) => entry.id)).toEqual([rows[0].id]);
    expect(writes.some((entry) => entry.url.includes("/results/"))).toBe(false);
  });
  it("uses the same verbs in the bar and right-click menu; Delete keeps its question and failed input",async () => {
    await openList(); fireEvent.contextMenu(row(),{clientX:20,clientY:20});
    const menu = screen.getByRole("menu",{name:"Automations actions"});
    for (const label of ["New automation","Open","Edit","Run now","Cancel run","Delete"]) expect(within(menu).getByRole("menuitem",{name:new RegExp(`^${label}`)})).toBeInTheDocument();
    fireEvent.click(within(menu).getByRole("menuitem",{name:/^Delete/}));
    const question = screen.getByRole("region",{name:"Delete Friday team update?"});
    expect(writes).toEqual([]);
    fail = "DELETE";
    fireEvent.click(within(question).getByRole("button",{name:"Delete"}));
    await screen.findByText(/Not deleted/);
    expect(row()).toBeInTheDocument();
    expect(question).toBeInTheDocument();
    fail = ""; fireEvent.click(within(question).getByRole("button",{name:"Delete"}));
    await screen.findByText("Automation deleted");
    expect(screen.queryByRole("row",{name:/Friday team update/})).toBeNull();
  });
  it("Find filters the existing read, and a new selection moves with arrows",async () => {
    rows = [...rows,{...rows[0],id:"other",name:"Morning prep"}];
    await openList(); fireEvent.click(row()); fireEvent.keyDown(row(),{key:"ArrowDown"});
    expect(screen.getByRole("row",{name:/Morning prep/})).toHaveAttribute("aria-selected","true");
    fireEvent.change(screen.getByRole("textbox",{name:"Find an automation"}),{target:{value:"Friday"}});
    expect(screen.queryByRole("row",{name:/Morning prep/})).toBeNull();
    expect(screen.getByText("Select an automation.")).toBeInTheDocument();
  });
  it("creates from a retained starter choice after refusal, in the inspector",async () => {
    rows=[]; await openList(); fireEvent.click(button("New automation"));
    const choice = await screen.findByRole("combobox",{name:"Automation starter"});
    fireEvent.change(choice,{target:{value:"friday-team-update"}});
    expect(screen.getByTestId("automation-starters")).toHaveTextContent("Every Friday at 15:00");
    fail = "POST"; fireEvent.click(button("Create"));
    await screen.findByText(/Friday team update was not made/);
    expect(choice).toHaveValue("friday-team-update");
    fail = ""; fireEvent.click(button("Create"));
    await screen.findByRole("textbox",{name:"Automation name"});
    expect(row()).toHaveAttribute("aria-selected","true");
    expect(useDesk.getState().workbenchWindows).toEqual([]);
    expect(writes.filter((entry) => entry.url.endsWith("/instantiate"))).toHaveLength(2);
  });
  it("keeps a refused Do draft and a newer edit through an older Save",async () => {
    const id = blank.workbench_id;
    rows = [recordedDetail({workbench_id:id,gets:blank.before.gets})];
    await openList(); fireEvent.click(screen.getByRole("row",{name:new RegExp(rows[0].name)})); fireEvent.click(button("Edit"));
    const input = await screen.findByRole("textbox",{name:"What it does"});
    const saved = blank.write.workbench.instruction;
    fireEvent.change(input,{target:{value:saved}});
    fail = "PUT"; fireEvent.click(button("Save")); await screen.findByText(/Not saved/);
    expect(input).toHaveValue(saved);
    fail=""; next=recordedDetail({workbench_id:id,gets:blank.after.gets});
    hold = () => undefined; fireEvent.click(button("Save"));
    await waitFor(() => expect(writes.filter((entry) => entry.method==="PUT")).toHaveLength(2));
    fireEvent.change(input,{target:{value:`${saved} Check owners.`}});
    await act(async () => hold?.());
    expect(input).toHaveValue(`${saved} Check owners.`);
    expect(screen.getByTestId("automation-setup")).toBeInTheDocument();
  });
  it("runs the selected automation once, retains a refusal and cancels its Program through the existing verb",async () => {
    await openList(); fireEvent.click(row()); fail="POST"; fireEvent.click(button("Run now"));
    await screen.findByText(/Run not started/);
    fail=""; fireEvent.click(button("Run now")); fireEvent.click(button("Run now"));
    await waitFor(() => expect(calls).toBe(1)); expect(button("Run now")).toBeDisabled();
    await act(async () => hold?.());
    expect(screen.getByTestId("automation-summary")).toBeInTheDocument();
  });
  it("Cancel run parks the selected running Program without deleting the automation",async () => {
    const detail = recordedDetail(program);
    rows=[structuredClone(detail)]; await openList(); fireEvent.click(screen.getByRole("row",{name:/Nightly fixes/}));
    expect(button("Run now")).toBeDisabled(); fireEvent.click(button("Cancel run"));
    await screen.findByText("Run cancelled");
    expect(writes).toContainEqual({url:`/api/programs/${detail.program!.latest!.id}/park`,method:"POST",body:{}});
    expect(screen.getByRole("row",{name:/Nightly fixes/})).toBeInTheDocument();
  });
});
