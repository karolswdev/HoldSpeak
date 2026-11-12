import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ListApp, useListApp, InspectorFacts, SurfaceState } from "../../index";
import { recordingReady } from "../../../recordings/__fixtures__/recording.ready";
import { recordingFailed } from "../../../recordings/__fixtures__/recording.failed";
import type { Recording } from "../../../recordings/types";
const page = (rows = [recordingReady, recordingFailed]) => ({ rows });
const readPage = async ({query}: {query:string}) => ({rows:page().rows.filter(row => `${row.title} ${row.state}`.toLowerCase().includes(query.toLowerCase()))});
const read = vi.fn(readPage);
function App({server = false, failure = false}: {server?:boolean;failure?:boolean}) {
  const app = useListApp({ read, keyOf: (row: Recording) => row.id, search: server ? undefined : (row, query) => `${row.title} ${row.state}`.toLowerCase().includes(query) });
  return <ListApp notice={failure ? <SurfaceState error="Disk full" /> : undefined} app={app} label="Recordings" ids={{windowTestId:"app",listTestId:"list",paneTestId:"pane",toolbarTestId:"toolbar",statusTestId:"status"}}
    words={{find:"Find",empty:"No recordings",noMatch:"No match",select:"Select",failed:"Not read"}}
    list={{columns:[{key:"name",word:"Recording"}],verbs:[{enabled:()=>true,id:"reload",label:"Reload",run:() => void app.reload()}]}}
    row={row => ({id:row.id,kind:"recording",name:row.title})}
    pane={row => row ? <InspectorFacts name={row.title} testId="facts" rows={[{label:"State",value:row.state}]} /> : null} />;
}
const pick = async () => {
  const row = await waitFor(() => {
    const found = document.querySelector(`[data-object-id="${recordingReady.id}"]`);
    expect(found).toBeTruthy(); return found!;
  });
  fireEvent.click(row); return row;
};
const reload = () => fireEvent.click(screen.getByRole("button", {name:"Reload"}));
afterEach(() => { cleanup(); read.mockReset().mockImplementation(readPage); });
it("drops a late reply after a newer reload", async () => {
  let finish!: (value: ReturnType<typeof page>) => void;
  read.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  render(<App />); reload(); await pick();
  await act(async () => { finish(page([])); });
  expect(screen.getByTestId("facts")).toHaveTextContent("ready");
});
it("clears the selection and closes its pane when the picked row leaves", async () => {
  render(<App />); await pick(); read.mockResolvedValue(page([recordingFailed])); reload();
  await waitFor(() => expect(screen.queryByTestId("facts")).toBeNull());
  await waitFor(() => expect(document.querySelector('[aria-selected="true"]')).toBeNull());
});
it("keeps the selected identity across reload", async () => {
  render(<App />); await pick(); read.mockResolvedValue(page([recordingFailed, recordingReady])); reload();
  await waitFor(() => expect(document.querySelectorAll('[data-object-id]')[0]).toHaveAttribute("data-object-id",recordingFailed.id));
  expect(document.querySelector(`[data-object-id="${recordingReady.id}"]`)).toHaveAttribute("aria-selected","true");
  expect(screen.getByTestId("facts")).toHaveTextContent("ready");
});
it("shows a failed load and heals on a later good read", async () => {
  read.mockRejectedValueOnce(new Error("Hub offline")); render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Not read · Hub offline");
  fireEvent.click(screen.getByRole("button",{name:"Try again"})); await pick();
  expect(screen.queryByRole("alert")).toBeNull();
});
it.each([false, true])("Find keeps a matching selection and clears one that no longer matches (server=%s)", async server => {
  render(<App server={server} />); await pick();
  fireEvent.change(screen.getByRole(server ? "searchbox" : "textbox",{name:"Find"}),{target:{value:"ready"}});
  await waitFor(() => expect(document.querySelectorAll('[data-object-id]')).toHaveLength(1));
  expect(screen.getByTestId("facts")).toHaveTextContent("ready");
  fireEvent.change(screen.getByRole(server ? "searchbox" : "textbox",{name:"Find"}),{target:{value:"failed"}});
  await waitFor(() => expect(document.querySelector(`[data-object-id="${recordingFailed.id}"]`)).toBeTruthy());
  expect(screen.queryByTestId("facts")).toBeNull();
  fireEvent.change(screen.getByRole(server ? "searchbox" : "textbox",{name:"Find"}),{target:{value:""}});
  await waitFor(() => expect(document.querySelector('[aria-selected="true"]')).toBeNull());
});

it("passes producer groups and two-line rows through the hook and ListApp", async () => {
  const { ListApp } = await import("../ListApp");
  const read = async () => ({rows:[{id:"a",kind:"program",name:"Overnight",group:0,detail:"Step 1 of 4 · Waits on you"},{id:"b",kind:"program",name:"Calls",group:1,detail:"Step 3 of 6 · Codex works"}]});
  function App() {
    const app=useListApp({read,keyOf:row=>row.id,groups:[{id:0,label:"Needs you"},{id:1,label:"Running"}]});
    return <ListApp app={app} label="Programs" row={row=>row} list={{headerless:true,columns:[{key:"name",word:"Program"}]}}
      ids={{windowTestId:"example",listTestId:"list",paneTestId:"pane",toolbarTestId:"toolbar",statusTestId:"status"}}
      words={{find:"Find a program",empty:"No programs",noMatch:"No programs match"}} />;
  }
  render(<App />);
  await screen.findByRole("rowgroup",{name:"Needs you"});
  expect(screen.getByText("Step 1 of 4 · Waits on you")).toBeVisible();
  const first=screen.getByText("Overnight").closest<HTMLElement>('[role=row]')!;
  const last=screen.getByText("Calls").closest<HTMLElement>('[role=row]')!;
  first.focus();fireEvent.keyDown(first,{key:"ArrowDown"});expect(last).toHaveFocus();
});

it("an action notice retains the selected reader and its row", async () => {
  const {rerender}=render(<App />);
  const row=await pick();
  rerender(<App failure />);
  expect(screen.getByRole("alert")).toHaveTextContent("Disk full");
  expect(row).toHaveAttribute("aria-selected","true");
  expect(screen.getByTestId("facts")).toHaveTextContent("ready");
});
