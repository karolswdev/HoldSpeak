import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { WindowIdContext } from "../../components/window/windowIdContext";
import { useListMenu } from "../../components/window/listMenu";
import { ListView, CycleGadget, CheckGadget, PaneInspector, InspectorForm, GadgetRow, StringGadget, ListPane, DotWord, type ListVerb } from "..";
afterEach(cleanup);

describe("the shared selection list", () => {
  it("selects with a click, opens with Return or double-click, and projects the same verbs into its context menu", () => {
    const open = vi.fn(); const remove = vi.fn(); const select = vi.fn();
    const verbs: ListVerb[] = [
      { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: (row) => open(row?.id) },
      { id: "remove", label: "Remove", key: "Delete", enabled: (row) => Boolean(row), run: remove },
    ];
    render(<ListView label="Accounts" rows={[{ id: "one", kind: "account", name: "GitHub" }, { id: "two", kind: "account", name: "Jira" }]} columns={[{ key: "name", word: "Service" }]} verbs={verbs} defaultVerb="open" onSelect={select} />);
    const bar = screen.getByRole("toolbar", { name: "Accounts actions" });
    expect(within(bar).getByRole("button", { name: "Open" })).toBeDisabled();
    const row = screen.getByText("GitHub").closest('[role="row"]')!;
    expect(row.querySelector("button")).toBeNull();
    fireEvent.click(row);
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(open).not.toHaveBeenCalled();
    expect(select).toHaveBeenCalledTimes(1);
    expect(select).toHaveBeenCalledWith("one");
    expect(within(bar).getByRole("button", { name: "Open" })).toBeEnabled();
    fireEvent.keyDown(row, { key: "Enter" });
    expect(open).toHaveBeenLastCalledWith("one");
    fireEvent.doubleClick(row);
    expect(open).toHaveBeenCalledTimes(2);
    fireEvent.contextMenu(row, { clientX: 50, clientY: 50 });
    const menu = screen.getByRole("menu");
    expect(within(menu).getAllByRole("menuitem").map((item) => item.textContent?.replace(/Return|Delete/g, ""))).toEqual(["Open", "Remove"]);
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Remove/ }));
    expect(remove).toHaveBeenCalledWith(expect.objectContaining({ id: "one" }));
  });

  it("Escape dismisses the context menu before focus settles and keeps its window open", () => {
    const close = vi.fn();
    render(<div onKeyDown={(event) => { if (event.key === "Escape") close(); }}>
      <ListView label="Services" rows={[{ id: "one", kind: "account", name: "GitHub" }]} verbs={[{ id: "open", label: "Open", run: () => {} }]} />
    </div>);
    const row = screen.getByText("GitHub").closest('[role="row"]') as HTMLElement;
    fireEvent.contextMenu(row);
    expect(screen.getByRole("menu")).toBeInTheDocument();
    fireEvent.keyDown(row, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
    expect(close).not.toHaveBeenCalled();
    expect(row).toHaveFocus();
  });

  it("moves selection with arrows, Home and End; keeps choice and tick input keys", () => {
    const toggle = vi.fn(); const choose = vi.fn();
    render(<ListView label="Jobs" ordered rows={[
      { id: "a", kind: "job", name: "Everything", cells: { chain: <CycleGadget label="Engine" value="a" options={[{ value: "a" }, { value: "b" }]} onChange={choose} /> } },
      { id: "b", kind: "job", name: "Meetings", cells: { tick: <CheckGadget label="Read" checked onChange={toggle} /> } },
    ]} columns={[{ key: "name", word: "Job" }, { key: "chain", word: "Engine" }]} />);
    const first = screen.getByText("Everything").closest('[role="row"]') as HTMLElement;
    const last = screen.getByText("Meetings").closest('[role="row"]') as HTMLElement;
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(last).toHaveFocus(); expect(last).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(last, { key: "Home" }); expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: "End" }); expect(last).toHaveFocus();
    fireEvent.click(screen.getByRole("checkbox", { name: "Read" })); expect(toggle).toHaveBeenCalledWith(false);
    fireEvent.change(screen.getByRole("combobox", { name: "Engine" }), { target: { value: "b" } }); expect(choose).toHaveBeenCalledWith("b");
  });
});


it("the top toolbar publishes its unselected verbs to the app menu on mount", () => {
  function MenuProbe() { const entries = useListMenu("records-test"); return <output data-testid="menu-probe">{entries.map((entry) => entry.id).join(",")}</output>; }
  render(<WindowIdContext.Provider value="records-test"><MenuProbe /><ListView label="Records" rows={[]}
    toolbar={{ trailing: <span>Find</span> }} verbs={[{ id: "record", label: "Record", run: () => {} }]} /></WindowIdContext.Provider>);
  expect(screen.getByTestId("menu-probe")).toHaveTextContent("record");
  expect(screen.getByRole("toolbar", { name: "Records" })).toBeTruthy();
  expect(screen.getAllByRole("toolbar")).toHaveLength(1);
});


it("puts the inspector's single Done after its last field", () => {
  const done = vi.fn();
  const { container } = render(<PaneInspector label="Calendar" onClose={done}><GadgetRow label="From">Mac calendar</GadgetRow></PaneInspector>);
  const inspector = screen.getByRole("region", { name: "Calendar" });
  const field = within(inspector).getByText("Mac calendar");
  const action = within(inspector).getByRole("button", { name: "Done" });
  expect(field.compareDocumentPosition(action) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(container.querySelectorAll(".surface-inspector-actions")).toHaveLength(1);
  expect(inspector.querySelector(".surface-pane-inspector-head button")).toBeNull();
  fireEvent.click(action); expect(done).toHaveBeenCalledOnce();
});

it("draws a draft's fields on one grid and keeps facts and errors out of Cancel and Save", () => {
  const cancel = vi.fn(), save = vi.fn();
  const { container } = render(<PaneInspector label="Folder Drive"><InspectorForm completion={{ cancel, primary: { label: "Save", run: save } }} notice={<span role="alert">Not saved</span>}>
    <GadgetRow label="Destination">Synced folder</GadgetRow>
    <GadgetRow label="Name"><StringGadget label="Name" value="Folder Drive" onChange={() => {}} /></GadgetRow>
  </InspectorForm></PaneInspector>);
  const action = container.querySelector(".surface-inspector-actions")!;
  expect([...action.querySelectorAll("button")].map((el) => el.textContent)).toEqual(["Cancel", "Save"]);
  expect(action).not.toHaveTextContent("Synced folder");
  expect(action).not.toHaveTextContent("Not saved");
  expect(screen.getByText("Synced folder").closest(".gadget-row")?.parentElement).toHaveClass("surface-inspector-rows");
  expect(screen.getByRole("textbox", { name: "Name" }).closest(".gadget-row")?.parentElement).toHaveClass("surface-inspector-rows");
  fireEvent.click(screen.getByRole("button", { name: "Save" })); expect(save).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole("button", { name: "Cancel" })); expect(cancel).toHaveBeenCalledOnce();
});

it("rejects a heading or arbitrary app layout inside an inspector form", () => {
  const error = vi.spyOn(console, "error").mockImplementation(() => {});
  expect(() => render(<InspectorForm><h3>Edit destination</h3></InspectorForm>)).toThrow("only GadgetRow");
  error.mockRestore();
});

it("reserves the header and three rows when inspection opens", () => {
  const measure = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function(this: HTMLElement) {
    const height = this.classList.contains("object-list-row") ? 26 : this.classList.contains("object-list-head") ? 26 : 200;
    return { x: 0, y: 0, top: 0, left: 0, right: 500, bottom: 200, width: 500, height, toJSON() {} };
  });
  vi.stubGlobal("ResizeObserver", class {
    constructor(private callback: ResizeObserverCallback) {}
    observe(target: Element) { if (target.classList.contains("surface-list-pane-list")) this.callback([], this as unknown as ResizeObserver); }
    disconnect() {}
  });
  const { container } = render(<ListPane label="Inspector" list={<ListView label="Sources" rows={[{ id: "source", kind: "calendar", name: "Home" }]} />}><PaneInspector label="Calendar" rows={[]} onClose={() => {}} /></ListPane>);
  expect(parseFloat((container.querySelector(".surface-list-pane-list") as HTMLElement).style.getPropertyValue("--surface-list-min"))).toBeGreaterThanOrEqual(104);
  measure.mockRestore();
  vi.unstubAllGlobals();
});


it("keeps the full value on retained text cells and state words", () => {
  const state = "Waiting for the enrolled machine to answer";
  const value = "A long relationship value";
  render(<ListView label="Machines" rows={[{ id: "one", kind: "machine", name: "Office machine", cells: { detail: value, status: <DotWord>{state}</DotWord> }, state: { label: state, tone: "warn" } }]} columns={[
    { key: "name", word: "Machine", priority: 100 }, { key: "detail", word: "Details", priority: 10 }, { key: "status", word: "Line", priority: 30 }, { key: "state", word: "State", priority: 20 },
  ]} />);
  expect(screen.getByText(value)).toHaveAttribute("title", value);
  for (const word of screen.getAllByText(state)) expect(word.closest("[title]")).toHaveAttribute("title", state);
});
