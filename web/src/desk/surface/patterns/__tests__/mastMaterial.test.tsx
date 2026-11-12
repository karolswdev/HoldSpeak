import { useState } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { Mast, MastSlotContext, useWindowMast, type MastDeclaration } from "../Mast";
import { StatusBar, ListView, ActionNotice, PreferencePane, GadgetRow } from "../../index";
import { Button } from "../../../../components/signal/Signal";
afterEach(cleanup);
function Declaration({ count }: { count: number }) {
  useWindowMast({ line: "4 people", figures: [{ value: count, label: "wait on you", tone: "ask" }] });
  return null;
}
function Window({ declares = true, count = 3 }) {
  const [mast, publish] = useState<MastDeclaration | null>(null);
  return <MastSlotContext.Provider value={publish}><Mast framed kind="person" title="People" object={<img alt="" src="/person.png" />} facts={mast?.line} figures={mast?.figures} />{declares ? <Declaration count={count} /> : null}</MastSlotContext.Provider>;
}
it("seats an app's facts and owner figure in the same Mast as its title and object", () => {
  const { container, rerender } = render(<Window />);
  const mast = container.querySelector(".surface-mast")!;
  expect(mast).toHaveTextContent("People");
  expect(mast).toHaveTextContent("4 people");
  expect(mast.querySelector('[data-tone="ask"]')).toHaveTextContent("3");
  expect(mast.querySelector("img")).toBeTruthy();
  rerender(<Window count={1} />);
  expect(mast.querySelector("dd")).toHaveTextContent("1");
  rerender(<Window count={0} />);
  expect(mast.querySelector(".surface-mast-figures")).toBeNull();
  rerender(<Window declares={false} />);
  expect(mast.querySelector(".surface-mast-facts")).toBeNull();
  expect(mast.querySelector(".surface-mast-figures")).toBeNull();
});
it("renders an undeclared object window with only its object and title", () => {
  const { container } = render(<Window declares={false} />);
  expect(screen.getByRole("heading", { name: "People" })).toBeVisible();
  expect(container.querySelector("img")).toBeTruthy();
  expect(container.querySelector("dl")).toBeNull();
});
it("keeps a failure required and puts a clock beside the instrument parts", () => {
  const { container } = render(<StatusBar items={[{ text: "4 people" }, { notice: "Not saved", lamp: "fail", text: "Disk full" }]} />);
  expect(screen.getByText("Not saved")).toHaveAttribute("data-required", "true");
  expect(container.querySelector("time")).toHaveAccessibleName("Time");
});
it("derives a row lamp from its declared state and keeps selection and Return", () => {
  let opened = "";
  function App() {
    const [picked, setPicked] = useState<string | null>(null);
    return <><Button onClick={() => setPicked(null)}>Clear</Button><ListView label="Items" rows={[{id:"a",kind:"person",name:"Priya",meter:{total:100,current:50,state:"waiting",label:"Next 1:1"},meterColumn:"next",cells:{next:"Today 14:30"},state:{label:"Waits on you",tone:"ask"}}]} columns={[{key:"name",word:"Name"},{key:"next",word:"Next"}]} selectedId={picked} onSelect={setPicked} verbs={[{id:"open",label:"Open",run:row => {opened = row!.id;}}]} defaultVerb="open" /></>;
  }
  const { container } = render(<App />);
  const row = container.querySelector('[data-object-id="a"]')!;
  expect(row.querySelector('[data-col="next"] .surface-meter')).toHaveAccessibleName("Next 1:1");
  expect(screen.getByRole("img", {name:"Waits on you"})).toHaveAttribute("data-state", "waiting");
  fireEvent.click(row);
  expect(row).toHaveAttribute("aria-selected", "true");
  fireEvent.keyDown(row,{key:"Enter"});
  expect(opened).toBe("a");
  fireEvent.click(screen.getByRole("button", {name:"Clear"}));
  expect(row).toHaveAttribute("aria-selected", "false");
});

it("puts a coral lamp in the shared failure notice while keeping its words", () => {
  render(<ActionNotice tone="danger">Not saved. The name stays.</ActionNotice>);
  expect(screen.getByRole("img", {name:"Failed"})).toHaveAttribute("data-state", "failed");
  expect(screen.getByText("Not saved. The name stays.")).toBeVisible();
});

it("measures nested styled-pane labels when their hidden tab opens", async () => {
  const saved = ["clientWidth", "scrollWidth"].map(key => [key, Object.getOwnPropertyDescriptor(HTMLElement.prototype, key)] as const);
  Object.defineProperty(HTMLElement.prototype, "clientWidth", {configurable:true,get:()=>393});
  Object.defineProperty(HTMLElement.prototype, "scrollWidth", {configurable:true,get(){return this.closest("[hidden]") ? 0 : this.classList.contains("gadget-row-label") ? 174 : 393;}});
  try {
    const paneView = (hidden: boolean) => <PreferencePane label="Calls"><div className="surface-preference-pane" hidden={hidden}><GadgetRow label="SIP password">Stored in your keystore</GadgetRow></div></PreferencePane>;
    const {container,rerender} = render(paneView(true));
    const pane = container.querySelector<HTMLElement>('[aria-label="Calls"]')!;
    expect(pane.style.getPropertyValue("--surface-label-seat")).toBe("80px");
    rerender(paneView(false));
    await waitFor(() => expect(pane.style.getPropertyValue("--surface-label-seat")).toBe("174px"));
    rerender(paneView(true));
    await waitFor(() => expect(pane.style.getPropertyValue("--surface-label-seat")).toBe("80px"));
  } finally {
    saved.forEach(([key,descriptor])=>{if(descriptor)Object.defineProperty(HTMLElement.prototype,key,descriptor);else Reflect.deleteProperty(HTMLElement.prototype,key);});
  }
});
