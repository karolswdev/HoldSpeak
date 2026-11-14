import { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { GadgetRow } from "../../gadgets";
import { InspectorFacts, PaneInspector } from "../PreferencePane";
import { InspectorFigures } from "../../live/InspectorFigures";
import { Mast, MastSlotContext, type MastDeclaration } from "../Mast";
import { SurfaceWell, ListView, StatusBar, ListPane, ObjectReader } from "../../index";
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

it.each([40, 40.75])("paints complete %s-pixel form rows while keeping the full field scroll range", async (rowHeight) => {
  const { InspectorForm } = await import("../../index");
  vi.spyOn(HTMLElement.prototype,"clientHeight","get").mockReturnValue(115);
  vi.spyOn(HTMLElement.prototype,"getBoundingClientRect").mockImplementation(function(this:HTMLElement) {
    if (this.classList.contains("surface-inspector-fields")) return new DOMRect(0,0,240,75);
    if (this.classList.contains("gadget-row")) return new DOMRect(0,this.textContent?.includes("Second")?rowHeight:0,240,rowHeight);
    if (this.classList.contains("surface-inspector-actions")) return new DOMRect(0,75,240,40);
    return new DOMRect(0,0,240,120);
  });
  const {container}=render(<InspectorForm wholeRows rows={[{label:"First",control:"First value"},{label:"Second",control:"Second value"}]} completion={{cancel:()=>{},primary:{label:"Save",run:()=>{}}}} />);
  const fields=container.querySelector<HTMLElement>(".surface-inspector-fields")!;
  expect(parseFloat(fields.style.maxHeight)).toBe(rowHeight);
  expect(fields.style.clipPath).not.toBe("");
  const bottom=75-parseFloat(fields.style.clipPath.split(" ")[2]);
  for (const row of fields.querySelectorAll(".gadget-row")) {
    const rect=row.getBoundingClientRect();
    expect(rect.top>=bottom || rect.bottom<=bottom).toBe(true);
  }
  expect(fields).toHaveTextContent("Second value");
  expect(screen.getByRole("button",{name:"Save"})).toBeVisible();
});

it("fits a path-led inspector name in whole lines and keeps its full identity", () => {
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(160);
  const name = "web/src/desk/pullouts/views/today/reconcile_owner_commitments_49.tsx::KeepTheSelectedRevisionBoundToItsSource keeps the saved answer when the next read completes";
  const {container} = render(<PaneInspector label={name} rows={[]} />);
  const title = container.querySelector(".surface-inspector-heading > strong")!;
  const lines = title.textContent!.split("\n");
  expect(lines.length).toBeGreaterThan(1);
  expect(lines.length).toBeLessThanOrEqual(3);
  for (const line of lines) expect(line.length * 8).toBeLessThanOrEqual(160);
  expect(title.textContent).not.toBe("…");
  expect(title.textContent).toMatch(/…$/);
  expect(title.querySelector("[title]")).toHaveAttribute("title", name);
  expect(screen.getByRole("region", {name})).toBeTruthy();
});

it("breaks a fact path at separators before splitting its filename", () => {
  render(<InspectorFacts name="Next" rows={[{label:"Then",paths:true,value:"web/src/desk/programs/ProgramSteps.tsx: read the saved requirement"}]} />);
  expect(screen.getByText("ProgramSteps.tsx:")).toHaveClass("surface-path-part");
  expect(screen.getByText("ProgramSteps.tsx:").previousElementSibling?.tagName).toBe("WBR");
});

it.each(["web/src/pages/cores/history/MeetingRecord.tsx: Keep the saved selection after a failed read", "meeting_followthrough_revision_0123456789abcdef [0]", "`proposal.binding` keeps the selected revision"])("a technical name uses the file object: %s", name => {
  const {container} = render(<InspectorFacts name={name} rows={[]} />);
  expect(container.querySelector(".surface-inspector-object img")).toHaveAttribute("src", expect.stringContaining("artifact"));
});

it("a wrapping inspector exposes all of a long decision without a hover", () => {
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(160);
  const name = "web/src/desk/pullouts/views/today/reconcile_owner_commitments_49.tsx::KeepTheSelectedRevisionBoundToItsSource keeps the saved answer when the next read completes";
  const {container} = render(<InspectorFacts name={name} nameMode="wrap" rows={[{label:"State",value:"To confirm"}]} />);
  expect(container.querySelector(".surface-inspector-heading > strong")).toHaveTextContent(name);
  expect(container.querySelector(".surface-inspector-name[data-wrap]")).toHaveAttribute("data-feedback-redact", "true");
});

it("keeps a fitted scope when the first Mast fact is wider than its seat", () => {
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(176);
  const scope = "Review the platform recovery point, retained draft, migration result and next owner action before the architecture team signs the deployment checkpoint.";
  const {container} = render(<Mast framed kind="thread" title="Ask" facts={`${scope} · Local engine`} />);
  const line = container.querySelector(".surface-mast-facts")!;
  expect(line).toHaveAttribute("aria-label", `${scope} · Local engine`);
  expect(line.textContent).toMatch(/^Review/);
  expect(line.textContent).not.toBe("…");
  expect(line.textContent!.length * 8).toBeLessThanOrEqual(176);
});


it("an optional source list leaves the reader and its position control mounted", () => {
  const pane = (listed: boolean) => <ListPane deck label="Answer" listTestId="sources" list={listed ? <ListView label="Sources" rows={[{id:"n",kind:"note",name:"Review"}]} columns={[{key:"name",word:"Sources"}]} /> : null}><ObjectReader label="Conversation"><input aria-label="Reading position" defaultValue="First line" /></ObjectReader></ListPane>;
  const {rerender} = render(pane(false));
  const position = screen.getByRole("textbox", {name:"Reading position"});
  expect(screen.queryByTestId("sources")).toBeNull();
  fireEvent.change(position,{target:{value:"Kept line"}});
  rerender(pane(true));
  expect(screen.getByRole("textbox", {name:"Reading position"})).toBe(position);
  expect(position).toHaveValue("Kept line");
  rerender(pane(false));
  expect(screen.queryByTestId("sources")).toBeNull();
  expect(screen.getByRole("textbox", {name:"Reading position"})).toBe(position);
  expect(position).toHaveValue("Kept line");
});
