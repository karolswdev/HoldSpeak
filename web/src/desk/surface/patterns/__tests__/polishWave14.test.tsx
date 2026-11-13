import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { InspectorFacts, ListApp, ListPane, ListView, Mast, StatusBar, useListApp } from "../../index";
import { recordingReady } from "../../../recordings/__fixtures__/recording.ready";
import { WorkMenu } from "../../../components/DeskMenu";

vi.mock("../../objects/fitName", async original => ({...await original<object>(), textMeasure: () => ({average: 8, width: (text: string) => text.length * 8})}));
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers(); });
const read = async () => ({rows:[recordingReady]});
function Collection({overview = false, deck = false}) {
  const app = useListApp({read, keyOf: row => row.id});
  return <ListApp app={app} layout={deck ? "deck" : undefined} label="Recordings"
    ids={{windowTestId:"app",listTestId:"list",paneTestId:"pane",toolbarTestId:"toolbar",statusTestId:"strip"}}
    words={{find:"Find",empty:"No recordings",noMatch:"No match",select:"Select a recording"}}
    row={row => ({id:row.id,name:row.title,kind:"recording"})}
    list={{columns:[{key:"name",word:"Recording"}]}}
    overview={overview ? [{label:"Recordings",value:app.visible.length}] : undefined}
    pane={row => row ? <InspectorFacts name={row.title} rows={[{label:"State",value:row.state}]} /> : null} />;
}
it.each([false,true])("gives the list the whole pane when no selection or whole facts exist (deck=%s)", async deck => {
  render(<Collection deck={deck} />);
  await screen.findByRole("row", {name:new RegExp(recordingReady.title)});
  await waitFor(() => expect(screen.queryByTestId("pane")).toBeNull());
  expect(screen.queryByText("Select a recording")).toBeNull();
});
it("shows collection facts until a selected object's facts take their seat", async () => {
  render(<Collection overview />);
  const row = await screen.findByRole("row", {name:new RegExp(recordingReady.title)});
  expect(screen.getByRole("region", {name:"Recordings facts"})).toHaveTextContent("Recordings1");
  fireEvent.click(row);
  expect(screen.queryByRole("region", {name:"Recordings facts"})).toBeNull();
  expect(screen.getByTestId("pane")).toHaveTextContent("ready");
});
it("keeps a deck's list in view when it has no reader to open", () => {
  const {container} = render(<ListPane deck open label="Selected item" list={<ListView label="Items" rows={[{id:"a",name:"First",kind:"note"}]} selectedId="a" />} />);
  expect(container.querySelector('.surface-list-pane')).not.toHaveAttribute('data-detail-open');
  expect(screen.getByRole('grid',{name:'Items'})).toBeVisible();
  expect(screen.queryByRole('button',{name:'Back'})).toBeNull();
});
it("fits Mast facts by whole parts instead of cutting a state word", () => {
  vi.spyOn(HTMLElement.prototype,"clientWidth","get").mockReturnValue(180);
  const {container} = render(<Mast framed compact kind="agent" title="Agents" facts="4 sessions · 3 agents on this Mac" />);
  expect(container.querySelector(".surface-mast-facts")).toHaveTextContent(/^4 sessions$/);
  expect(container.querySelector(".surface-mast-facts")).toHaveAccessibleName("4 sessions · 3 agents on this Mac");
});
it("fits styled titles by whole words in a wide window too", () => {
  vi.spyOn(HTMLElement.prototype,"clientWidth","get").mockReturnValue(145);
  const {container} = render(<Mast framed kind="project" title={<span>Payments Platform migration</span>} />);
  expect(container.querySelector("h2")).toHaveTextContent(/^Payments(?: Platform)?…$/);
});
it("keeps a transient result in the strip until its timer ends and resets for the next act", async () => {
  vi.useFakeTimers();
  const {rerender} = render(<StatusBar inPlace parts={[{text:"Recording"}]} transient={{id:1,item:{text:"Meeting saved"},durationMs:5000}} />);
  expect(screen.getByRole("status")).toHaveTextContent("Meeting saved");
  await act(async () => { await vi.advanceTimersByTimeAsync(4000); });
  rerender(<StatusBar inPlace parts={[{text:"Recording"}]} transient={{id:2,item:{text:"Added to project"},durationMs:5000}} />);
  await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
  expect(screen.getByRole("status")).toHaveTextContent("Added to project");
  await act(async () => { await vi.advanceTimersByTimeAsync(4000); });
  expect(screen.getByRole("status")).toHaveTextContent(/^Recording$/);
});
it("keeps one selection and the lamp seat when the next row has no state", () => {
  const {container,rerender} = render(<ListView label="Items" rows={[{id:"a",name:"First",kind:"note",state:{label:"Ready",tone:"info"}},{id:"b",name:"Second",kind:"note"}]} selectedId="a" />);
  expect(container.querySelectorAll('[aria-selected="true"]')).toHaveLength(1);
  expect(container.querySelectorAll('.object-list-lamp-seat')).toHaveLength(2);
  rerender(<ListView label="Items" rows={[{id:"a",name:"First",kind:"note"},{id:"b",name:"Second",kind:"note"}]} selectedId="b" />);
  expect(container.querySelectorAll('[aria-selected="true"]')).toHaveLength(1);
});
it.each([1440,393])("keeps a tall menu outside its button anchor at width %s", width => {
  vi.stubGlobal("innerWidth",width); vi.stubGlobal("innerHeight",900);
  const opener = document.createElement("button");
  document.body.append(opener);
  vi.spyOn(HTMLElement.prototype,"getBoundingClientRect").mockImplementation(function(this: HTMLElement) {
    return this === opener ? new DOMRect(8,700,100,44) : this.getAttribute("role") === "menu" ? new DOMRect(8,parseFloat(this.style.top)||0,232,260) : new DOMRect();
  });
  try {
    render(<WorkMenu label="Actions" x={8} y={744} opener={opener} entries={[{type:"item",id:"open",label:"Open",onSelect:()=>{}}]} onClose={()=>{}} />);
    const menu = screen.getByRole("menu",{name:"Actions"}).getBoundingClientRect();
    const anchor = opener.getBoundingClientRect();
    expect(menu.bottom <= anchor.top || menu.top >= anchor.bottom).toBe(true);
  } finally { opener.remove(); }
});
