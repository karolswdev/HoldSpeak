import { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { GadgetRow } from "../../gadgets";
import { PaneInspector } from "../PreferencePane";
import { InspectorFigures } from "../../live/InspectorFigures";
import { Mast, MastSlotContext, type MastDeclaration } from "../Mast";
import { SurfaceWell, ListView, StatusBar } from "../../index";
import { Button } from "../../../../components/signal/Signal";
vi.mock("../../objects/fitName", async importOriginal => ({...await importOriginal<object>(), textMeasure: () => ({average: 8, width: (text: string) => text.length * 8})}));
afterEach(() => {cleanup(); vi.restoreAllMocks();});

it("uses the frame as the only title and publishes an inline Mast's state", () => {
  function Window() {
    const [declaration, publish] = useState<MastDeclaration | null>(null);
    return <><Mast framed kind="dictation" title="Speak" facts={declaration?.line} /><MastSlotContext.Provider value={publish}><Mast kind="dictation" title="Your voice" facts={<span>Ready</span>}><Button>Record</Button></Mast></MastSlotContext.Provider></>;
  }
  const {container} = render(<Window />);
  expect(screen.getAllByRole("heading")).toHaveLength(1);
  expect(container.querySelector(".surface-mast--framed .surface-mast-facts")).toHaveTextContent("Ready");
  expect(screen.getByRole("button", {name:"Record"})).toBeVisible();
});

it("reserves the same lamp seat when a row has no state", () => {
  const {container} = render(<ListView label="Items" rows={[{id:"a",kind:"note",name:"Ready item",state:{label:"Ready",tone:"ok"}},{id:"b",kind:"note",name:"Other item"}]} columns={[{key:"name",word:"Name"}]} selectedId={null} onSelect={()=>{}} />);
  const names = [...container.querySelectorAll(".object-list-selection-name")];
  expect(names).toHaveLength(2);
  expect(screen.getByRole("row", {name:/^Ready item/})).toBeVisible();
  names.forEach(name => expect(name.querySelector(".object-list-lamp-seat")).toBeTruthy());
  expect(container.querySelector('[data-object-id="a"] .surface-lamp')).toBeTruthy();
  expect(container.querySelector('[data-object-id="b"] .surface-lamp')).toBeNull();
});

it("keeps the instrument strip and clock when there is no status", () => {
  const {container} = render(<StatusBar inPlace parts={[]} />);
  expect(container.querySelector(".kit-statusbar")).toBeVisible();
  expect(screen.getByLabelText("Time")).toBeVisible();
  expect(container.querySelector(".kit-statusbar-items")).toBeEmptyDOMElement();
});

it("fits a composed compact title at a word before sacrificing its state line", () => {
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(145);
  const {container} = render(<Mast framed compact kind="project" title={<span>Payments Platform migration</span>} facts="Project room" />);
  expect(container.querySelector("h2")).toHaveTextContent(/^Payments(?: Platform)?…$/);
  expect(container.querySelector("h2")).toHaveAccessibleName("Payments Platform migration");
});

it("keeps a partial final reading line below the edge and reachable by scrolling", () => {
  let scroll = 0;
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(() => new DOMRect(0,0,300,45));
  vi.spyOn(document, "createRange").mockImplementation(() => ({selectNodeContents:()=>{},getClientRects:()=>[new DOMRect(0,-scroll,300,18),new DOMRect(0,36-scroll,300,18)]}) as unknown as Range);
  const {container} = render(<SurfaceWell wholeLines>Keep all these words.</SurfaceWell>);
  const well = container.querySelector<HTMLElement>(".surface-well-body")!;
  expect(well.style.clipPath).toBe("inset(0 0 10px 0)");
  scroll = 20;
  fireEvent.scroll(well);
  expect(well.style.clipPath).toBe("");
  expect(well).toHaveTextContent("Keep all these words.");
});


it("keeps sentences outside the short-label species in each label seat", () => {
  const {container} = render(<><GadgetRow label="Next step">Ready</GadgetRow><GadgetRow label="Read the saved result again">Ready</GadgetRow><PaneInspector label="Plan" subtitle="Read the saved result again" rows={[]} /><InspectorFigures label="Recap" figures={[{value:1,label:"Waits on you"},{value:2,label:"Read the saved result again"}]} /><ListView label="Items" rows={[]} columns={[{key:"name",word:"From your desk now"}]} selectedId={null} onSelect={()=>{}} /></>);
  expect(container.querySelector('.gadget-row-label[data-caption="short"]')).toHaveTextContent("Next step");
  expect(container.querySelectorAll('.gadget-row-label')[1]).toHaveAttribute("data-caption", "content");
  expect(container.querySelector('.surface-inspector-subtitle')).toHaveAttribute("data-caption", "content");
  expect(container.querySelectorAll('.surface-inspector-figures dt')[1]).toHaveAttribute("data-caption", "content");
  expect(container.querySelector('.object-list-th')).toHaveAttribute("data-caption", "content");
});
