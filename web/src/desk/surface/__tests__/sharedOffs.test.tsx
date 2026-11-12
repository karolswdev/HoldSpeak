import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ActionNotice, CycleGadget, GadgetRow, InspectorFacts, ListView, StatusBar, StringGadget, SurfaceState, countWords, faceTimeWords } from "..";
afterEach(cleanup);

it("keeps the full failure in its notice and only the state in the status seat", () => {
  render(<><ActionNotice tone="danger" role="alert" keeps="Your name stays here." action={{label:"Try again",onClick:vi.fn()}}>The person was not saved.</ActionNotice>
    <StatusBar items={[{text:"The person was not saved.",notice:"Failed",lamp:"fail"}]} /></>);
  expect(screen.getAllByText("The person was not saved.")).toHaveLength(1);
  expect(screen.getByRole("status")).toHaveTextContent(/^Failed$/);
  expect(screen.getByRole("alert")).toHaveTextContent("Your name stays here.");
});

it("puts the retry in the notice once and retains its real action", () => {
  const retry=vi.fn();
  render(<SurfaceState error="Could not read the update · Nothing changed · Try again" onRetry={retry} />);
  const notice=screen.getByRole("alert");
  expect(notice.querySelector(".surface-state-glyph")).toBeNull();
  expect(within(notice).queryByText(/Nothing changed · Try again/)).toBeNull();
  fireEvent.click(within(notice).getByRole("button",{name:"Try again"}));
  expect(retry).toHaveBeenCalledOnce();
});

it("names a standalone pop-up and does not repeat a form row label", () => {
  const popup=<CycleGadget roster label="Delivery" value="manual" options={[{value:"manual",label:"Manual"}]} onChange={vi.fn()} />;
  const {rerender}=render(popup);
  expect(screen.getByText("Delivery:")).toBeVisible();
  expect(screen.getByRole("combobox",{name:"Delivery"})).toHaveValue("manual");
  rerender(<GadgetRow label="Delivery">{popup}</GadgetRow>);
  expect(screen.getByText("Delivery")).toBeVisible();
  expect(screen.queryByText("Delivery:")).toBeNull();
});

it.each(["2026-11-09T21:24:00Z", "2026-10-15"])("formats declared wire time %s and preserves saved titles and text", stamp => {
  render(<><InspectorFacts header={false} name="Context" rows={[{label:"When",value:faceTimeWords(stamp)}]} />
    <ListView label="Sources" columns={[{key:"name",word:"Source"},{key:"when",word:"When"}]} rows={[{id:"one",kind:"source",name:"Update "+stamp, when:stamp}]} />
    <StringGadget label="Text" value={stamp} onChange={vi.fn()} /></>);
  expect(screen.getByRole("region",{name:"Context"})).not.toHaveTextContent(stamp);
  expect(screen.getByRole("grid",{name:"Sources"})).toHaveTextContent("Update "+stamp);
  expect(screen.getByRole("grid").querySelector("[data-col=when]")).not.toHaveTextContent(stamp);
  expect(screen.getByRole("textbox",{name:"Text"})).toHaveValue(stamp);
});

it("marks an empty list so its well and header can yield to one pane state", () => {
  const {rerender}=render(<ListView label="Sources" columns={[{key:"name",word:"Source"}]} rows={[]} />);
  expect(screen.getByRole("grid")).toHaveAttribute("data-empty");
  rerender(<ListView label="Sources" columns={[{key:"name",word:"Source"}]} rows={[{id:"one",kind:"source",name:"Plan"}]} />);
  expect(screen.getByRole("grid")).not.toHaveAttribute("data-empty");
});

it("keeps a menu verb visibly armed until its menu closes", () => {
  render(<ListView label="Engines" columns={[{key:"name",word:"Engine"}]} rows={[]} verbs={[{id:"add",label:"Add",enabled:()=>true,run:vi.fn(),items:[{id:"one",label:"Codex",run:vi.fn()}]}]} />);
  const add=screen.getByRole("button",{name:"Add"});
  fireEvent.click(add);
  expect(add).toHaveAttribute("aria-expanded","true");
  fireEvent.keyDown(screen.getByRole("menu"),{key:"Escape"});
  expect(add).toHaveAttribute("aria-expanded","false");
});

it("counts one item with its singular noun", () => {
  expect(countWords(1,"item")).toBe("1 item");
  expect(countWords(2,"item")).toBe("2 items");
});

it.each(["Plan 2026-11-12", "2026-11-12", "Plan 2026-11-12T08:00:00Z"])("keeps saved title %s in names and facts", title => {
  render(<><InspectorFacts header={false} name="Document" rows={[{label:"Title",value:title}]} />
    <ListView label="Documents" columns={[{key:"name",word:"Document"}]} rows={[{id:"one",kind:"source",name:title}]} /></>);
  expect(screen.getByRole("region",{name:"Document"})).toHaveTextContent(title);
  expect(screen.getByRole("grid",{name:"Documents"})).toHaveTextContent(title);
});
