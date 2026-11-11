import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import type { ComponentProps } from "react";
import { afterEach, describe, expect, expectTypeOf, it, vi } from "vitest";
import { WindowIdContext } from "../../components/window/windowIdContext";
import { useListMenu } from "../../components/window/listMenu";
import {
  ListView,
  CycleGadget,
  CheckGadget,
  PaneInspector,
  InspectorForm,
  InspectorFacts,
  InspectorQuestion,
  StatusBar,
  SegmentedTabs,
  GadgetGroup,
  GadgetRow,
  PaneGroup,
  StringGadget,
  ListPane,
  DotWord,
  type ListVerb,
} from "..";
afterEach(cleanup);

describe("the shared selection list", () => {
  it("can omit a names-only header without losing selection or Return", () => {
    const focus = vi.fn();
    render(
      <ListView
        label="Preferences"
        headerless
        ordered
        columns={[{ key: "name", word: "Name" }]}
        rows={[{ id: "one", kind: "preference", name: "Digest" }]}
        selectedId="one"
        onOpen={focus}
      />,
    );
    const grid = screen.getByRole("grid", { name: "Preferences" });
    expect(within(grid).queryByRole("columnheader")).toBeNull();
    expect(grid).toHaveAttribute("aria-rowcount", "1");
    const row = within(grid).getByRole("row");
    expect(row).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(row, { key: "Enter" });
    expect(focus).toHaveBeenCalledWith("one");
    expect(screen.queryByRole("toolbar")).toBeNull();
  });
  it("selects with a click, opens with Return or double-click, and projects the same verbs into its context menu", () => {
    const open = vi.fn();
    const remove = vi.fn();
    const select = vi.fn();
    const verbs: ListVerb[] = [
      {
        id: "open",
        label: "Open",
        key: "Enter",
        enabled: (row) => Boolean(row),
        run: (row) => open(row?.id),
      },
      {
        id: "remove",
        label: "Remove",
        key: "Delete",
        enabled: (row) => Boolean(row),
        run: remove,
      },
    ];
    render(
      <ListView
        label="Accounts"
        rows={[
          { id: "one", kind: "account", name: "GitHub" },
          { id: "two", kind: "account", name: "Jira" },
        ]}
        columns={[{ key: "name", word: "Service" }]}
        verbs={verbs}
        defaultVerb="open"
        onSelect={select}
      />,
    );
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
    expect(
      within(menu)
        .getAllByRole("menuitem")
        .map((item) => item.textContent?.replace(/Return|Delete/g, "")),
    ).toEqual(["Open", "Remove"]);
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Remove/ }));
    expect(remove).toHaveBeenCalledWith(expect.objectContaining({ id: "one" }));
  });

  it("Escape dismisses the context menu before focus settles and keeps its window open", () => {
    const close = vi.fn();
    render(
      <div
        onKeyDown={(event) => {
          if (event.key === "Escape") close();
        }}
      >
        <ListView
          label="Services"
          rows={[{ id: "one", kind: "account", name: "GitHub" }]}
          verbs={[{ id: "open", label: "Open", run: () => {} }]}
        />
      </div>,
    );
    const row = screen
      .getByText("GitHub")
      .closest('[role="row"]') as HTMLElement;
    fireEvent.contextMenu(row);
    expect(screen.getByRole("menu")).toBeInTheDocument();
    fireEvent.keyDown(row, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
    expect(close).not.toHaveBeenCalled();
    expect(row).toHaveFocus();
  });

  it("moves selection with arrows, Home and End; keeps choice and tick input keys", () => {
    const toggle = vi.fn();
    const choose = vi.fn();
    render(
      <ListView
        label="Jobs"
        ordered
        rows={[
          {
            id: "a",
            kind: "job",
            name: "Everything",
            cells: {
              chain: (
                <CycleGadget
                  label="Engine"
                  value="a"
                  options={[{ value: "a" }, { value: "b" }]}
                  onChange={choose}
                />
              ),
            },
          },
          {
            id: "b",
            kind: "job",
            name: "Meetings",
            cells: {
              tick: <CheckGadget label="Read" checked onChange={toggle} />,
            },
          },
        ]}
        columns={[
          { key: "name", word: "Job" },
          { key: "chain", word: "Engine" },
        ]}
      />,
    );
    const first = screen
      .getByText("Everything")
      .closest('[role="row"]') as HTMLElement;
    const last = screen
      .getByText("Meetings")
      .closest('[role="row"]') as HTMLElement;
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(last).toHaveFocus();
    expect(last).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(last, { key: "Home" });
    expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: "End" });
    expect(last).toHaveFocus();
    fireEvent.click(screen.getByRole("checkbox", { name: "Read" }));
    expect(toggle).toHaveBeenCalledWith(false);
    fireEvent.change(screen.getByRole("combobox", { name: "Engine" }), {
      target: { value: "b" },
    });
    expect(choose).toHaveBeenCalledWith("b");
  });
});

describe.each([
  ["GadgetGroup", GadgetGroup],
  ["PaneGroup", PaneGroup],
] as const)("%s headings", (_name, Group) => {
  function WrappedRow() {
    return (
      <div>
        <GadgetRow label="Test call">Call</GadgetRow>
      </div>
    );
  }
  it("refuses a heading that repeats its only row, including a composed row", async () => {
    const view = render(
      <Group label="Test call">
        <WrappedRow />
      </Group>,
    );
    const group = screen.getByRole("region", { name: "Test call" });
    expect(within(group).queryByRole("heading")).toBeNull();
    expect(within(group).getByText("Test call")).toHaveClass(
      "gadget-row-label",
    );
    view.rerender(
      <Group label="Test call">
        <WrappedRow />
        <GadgetRow label="Number">123</GadgetRow>
      </Group>,
    );
    await waitFor(() =>
      expect(
        within(group).getByRole("heading", { name: "Test call" }),
      ).toBeInTheDocument(),
    );
    view.rerender(
      <Group label="Test call">
        <WrappedRow />
      </Group>,
    );
    await waitFor(() =>
      expect(within(group).queryByRole("heading")).toBeNull(),
    );
  });
});

it("the top toolbar publishes its unselected verbs to the app menu on mount", () => {
  function MenuProbe() {
    const entries = useListMenu("records-test");
    return (
      <output data-testid="menu-probe">
        {entries.map((entry) => entry.id).join(",")}
      </output>
    );
  }
  render(
    <WindowIdContext.Provider value="records-test">
      <MenuProbe />
      <ListView
        label="Records"
        rows={[]}
        toolbar={{ trailing: <span>Find</span> }}
        verbs={[{ id: "record", label: "Record", run: () => {} }]}
      />
    </WindowIdContext.Provider>,
  );
  expect(screen.getByTestId("menu-probe")).toHaveTextContent("record");
  expect(screen.getByRole("toolbar", { name: "Records" })).toBeTruthy();
  expect(screen.getAllByRole("toolbar")).toHaveLength(1);
});

it("puts the inspector's single Done after its last field", () => {
  const done = vi.fn();
  const { container } = render(
    <PaneInspector label="Calendar" onClose={done}>
      <GadgetRow label="From">
        <CheckGadget label="Mac calendar" checked onChange={() => {}} />
      </GadgetRow>
    </PaneInspector>,
  );
  const inspector = screen.getByRole("region", { name: "Calendar" });
  const field = within(inspector).getByRole("checkbox", {
    name: "Mac calendar",
  });
  const action = within(inspector).getByRole("button", { name: "Done" });
  expect(
    field.compareDocumentPosition(action) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(container.querySelectorAll(".surface-inspector-actions")).toHaveLength(
    1,
  );
  expect(
    inspector.querySelector(".surface-pane-inspector-head button"),
  ).toBeNull();
  fireEvent.click(action);
  expect(done).toHaveBeenCalledOnce();
});

it("draws a draft's fields on one grid and keeps facts and errors out of Cancel and Save", () => {
  const cancel = vi.fn(),
    save = vi.fn();
  const { container } = render(
    <PaneInspector label="Folder Drive">
      <InspectorForm
        completion={{ cancel, primary: { label: "Save", run: save } }}
        notice={<span role="alert">Not saved</span>}
      >
        <GadgetRow label="Destination">Synced folder</GadgetRow>
        <GadgetRow label="Name">
          <StringGadget label="Name" value="Folder Drive" onChange={() => {}} />
        </GadgetRow>
      </InspectorForm>
    </PaneInspector>,
  );
  const action = container.querySelector(".surface-inspector-actions")!;
  expect(
    [...action.querySelectorAll("button")].map((el) => el.textContent),
  ).toEqual(["Cancel", "Save"]);
  expect(action).not.toHaveTextContent("Synced folder");
  expect(action).not.toHaveTextContent("Not saved");
  expect(
    screen.getByText("Synced folder").closest(".gadget-row")?.parentElement,
  ).toHaveClass("surface-inspector-rows");
  expect(
    screen.getByRole("textbox", { name: "Name" }).closest(".gadget-row")
      ?.parentElement,
  ).toHaveClass("surface-inspector-rows");
  fireEvent.click(screen.getByRole("button", { name: "Save" }));
  expect(save).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
  expect(cancel).toHaveBeenCalledOnce();
});

it("rejects a heading or arbitrary app layout inside an inspector form", () => {
  const error = vi.spyOn(console, "error").mockImplementation(() => {});
  expect(() =>
    render(
      <InspectorForm>
        <h3>Edit destination</h3>
      </InspectorForm>,
    ),
  ).toThrow("only GadgetRow");
  error.mockRestore();
});

it("reserves the header and three rows when inspection opens", () => {
  const measure = vi
    .spyOn(HTMLElement.prototype, "getBoundingClientRect")
    .mockImplementation(function (this: HTMLElement) {
      const height = this.classList.contains("object-list-row")
        ? 26
        : this.classList.contains("object-list-head")
          ? 26
          : 200;
      return {
        x: 0,
        y: 0,
        top: 0,
        left: 0,
        right: 500,
        bottom: 200,
        width: 500,
        height,
        toJSON() {},
      };
    });
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(private callback: ResizeObserverCallback) {}
      observe(target: Element) {
        if (target.classList.contains("surface-list-pane-list"))
          this.callback([], this as unknown as ResizeObserver);
      }
      disconnect() {}
    },
  );
  const { container } = render(
    <ListPane
      label="Inspector"
      list={
        <ListView
          label="Sources"
          rows={[{ id: "source", kind: "calendar", name: "Home" }]}
        />
      }
    >
      <PaneInspector label="Calendar" rows={[]} onClose={() => {}} />
    </ListPane>,
  );
  expect(
    parseFloat(
      (
        container.querySelector(".surface-list-pane-list") as HTMLElement
      ).style.getPropertyValue("--surface-list-min"),
    ),
  ).toBeGreaterThanOrEqual(104);
  measure.mockRestore();
  vi.unstubAllGlobals();
});

it("yields list rows before cutting the selected fact rows", () => {
  const measure = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    const row = this.classList.contains("object-list-row");
    const pane = this.classList.contains("surface-list-pane");
    const height = row ? 46 : pane ? 300 : 142;
    return { x: 0, y: 0, top: 0, left: 0, right: 500, bottom: height, width: 500, height, toJSON() {} };
  });
  const scroll = vi.spyOn(HTMLElement.prototype, "scrollHeight", "get").mockImplementation(function (this: HTMLElement) {
    return this.classList.contains("surface-inspector-facts") ? 150 : 0;
  });
  vi.stubGlobal("ResizeObserver", class {
    constructor(private callback: ResizeObserverCallback) {}
    observe(target: Element) { if (target.classList.contains("surface-list-pane-list")) this.callback([], this as unknown as ResizeObserver); }
    disconnect() {}
  });
  const { container, unmount } = render(<ListPane label="Selected source" list={<ListView headerless label="Sources" rows={[{id:"home",kind:"calendar",name:"Home"}]} />}>
    <InspectorFacts header={false} name="Home" rows={[{label:"Account",value:"Personal"}]} />
  </ListPane>);
  const floor = parseFloat((container.querySelector(".surface-list-pane-list") as HTMLElement).style.getPropertyValue("--surface-list-min"));
  expect(floor + 150).toBeLessThanOrEqual(300);
  expect(floor).toBeGreaterThanOrEqual(46);
  unmount(); measure.mockRestore(); scroll.mockRestore(); vi.unstubAllGlobals();
});

it("keeps the full value on retained text cells and state words", () => {
  const state = "Waiting for the enrolled machine to answer";
  const value = "A long relationship value";
  render(
    <ListView
      label="Machines"
      rows={[
        {
          id: "one",
          kind: "machine",
          name: "Office machine",
          cells: { detail: value, status: <DotWord>{state}</DotWord> },
          state: { label: state, tone: "warn" },
        },
      ]}
      columns={[
        { key: "name", word: "Machine", priority: 100 },
        { key: "detail", word: "Details", priority: 10 },
        { key: "status", word: "Line", priority: 30 },
        { key: "state", word: "State", priority: 20 },
      ]}
    />,
  );
  expect(screen.getByText(value)).toHaveAttribute("title", value);
  for (const word of screen.getAllByText(state))
    expect(word.closest("[title]")).toHaveAttribute("title", state);
});

it("read-only facts omit blank values and have no completion row", () => {
  const { container } = render(
    <PaneInspector label="Selected automation">
      <InspectorFacts
        name="Selected automation"
        rows={[
          { label: "Do", value: "Draft the update" },
          { label: "With", value: "  " },
          { label: "Next run", value: null },
          { label: "Last run", value: <span /> },
        ]}
      />
    </PaneInspector>,
  );
  expect(
    screen.getByText("Draft the update").closest(".gadget-row")?.parentElement,
  ).toHaveClass("surface-inspector-rows");
  expect(screen.queryByText("With")).toBeNull();
  expect(screen.queryByText("Next run")).toBeNull();
  expect(screen.queryByText("Last run")).toBeNull();
  expect(container.querySelector(".surface-inspector-actions")).toBeNull();
});

it("a destructive question focuses Cancel, keeps consequences out of facts and uses danger", () => {
  const cancel=vi.fn(), remove=vi.fn();
  const {container} = render(<InspectorQuestion actionId="delete" targetId="friday" question="Delete Friday update?" keeps={["Past results"]} cancel={cancel} verb={{label:"Delete",run:remove}} />);
  const buttons=screen.getAllByRole("button");
  expect(buttons.map(button=>button.textContent)).toEqual(["Cancel","Delete"]);
  expect(buttons[0]).toHaveFocus();
  expect(buttons[1]).toHaveClass("btn--danger");
  expect(container.querySelector(".gadget-row")).toBeNull();
  expect(remove).not.toHaveBeenCalled();
  fireEvent.click(buttons[0]);
  expect(cancel).toHaveBeenCalledOnce();
  fireEvent.click(buttons[1]);
  expect(remove).toHaveBeenCalledOnce();
});

it("an empty status has no DOM even when a caller supplies empty nodes", () => {
  const { container } = render(
    <StatusBar
      items={[{ text: " " }, { text: <span /> }, null]}
      verbs={<></>}
    />,
  );
  expect(container).toBeEmptyDOMElement();
});

it("a long tab strip keeps every named tab instead of becoming an unnamed choice", () => {
  render(
    <SegmentedTabs
      label="Setup"
      tabs={["Do", "When", "About", "With", "Put it in"].map((label) => ({
        id: label,
        label,
      }))}
      value="About"
      onChange={() => {}}
    >
      Source list
    </SegmentedTabs>,
  );
  expect(screen.getByRole("tab", { name: "About" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  expect(screen.queryByRole("combobox")).toBeNull();
});

it("a nested selection choice retains one completion row", () => {
  render(
    <PaneInspector label="Engine order" onClose={() => {}}>
      <InspectorForm>
        <GadgetRow label="Order">
          <ListView
            label="Order choices"
            rows={[{ id: "codex", kind: "engine", name: "Codex" }]}
          />
        </GadgetRow>
      </InspectorForm>
    </PaneInspector>,
  );
  expect(screen.getAllByRole("button", { name: "Done" })).toHaveLength(1);
  expect(
    screen
      .getByRole("button", { name: "Done" })
      .closest(".surface-inspector-form"),
  ).toBeTruthy();
});

it("facts own the object's heading and omit its repeated value, including a node", () => {
  const { container } = render(
    <InspectorFacts
      name="Priya Nair"
      rows={[
        { label: "Name", value: <span>Priya Nair</span> },
        { label: "Relationship", value: "Peer" },
      ]}
    />,
  );
  expect(screen.getAllByText("Priya Nair")).toHaveLength(1);
  expect(
    screen.getByText("Priya Nair").closest(".surface-pane-inspector-head"),
  ).toBeTruthy();
  expect(screen.queryByText("Name")).toBeNull();
  expect(container.querySelector(".surface-inspector-facts")).toHaveAttribute(
    "data-facts-name",
    "Priya Nair",
  );
});

it("a question writes the cleared and kept things as sentences", () => {
  render(<InspectorQuestion actionId="delete" targetId="friday" question="Reset the desk?" clears="the desk" restores="the default items"
    keeps={["Meetings","Journal","Settings","Engines"]} cancel={()=>{}} verb={{label:"Reset desk",run:()=>{}}} />);
  expect(screen.getByText("Clears the desk and puts back the default items.")).toBeInTheDocument();
  expect(screen.getByText("Meetings, Journal, Settings, and Engines stay.")).toBeInTheDocument();
});

it("an inner list has one action bar above its header and the same context command", () => {
  const confirm = vi.fn();
  render(
    <ListView
      label="Tasks"
      rows={[{ id: "one", kind: "task", name: "Write the plan" }]}
      selectedId="one"
      verbs={[{ id: "confirm", label: "Confirm", run: confirm }]}
    />,
  );
  const grid = screen.getByRole("grid", { name: "Tasks" });
  const bar = within(grid).getByRole("toolbar", { name: "Tasks actions" });
  expect(
    bar.compareDocumentPosition(
      within(grid).getByRole("columnheader", { name: "Name" }),
    ) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  fireEvent.click(within(bar).getByRole("button", { name: "Confirm" }));
  fireEvent.contextMenu(
    within(grid).getByText("Write the plan").closest('[role="row"]')!,
  );
  fireEvent.click(screen.getByRole("menuitem", { name: "Confirm" }));
  expect(confirm).toHaveBeenCalledTimes(2);
});

it("declared scope ticks and cycles use the Find row", () => {
  const tick = vi.fn(),
    cycle = vi.fn();
  render(
    <ListView
      label="Decisions"
      rows={[]}
      toolbar={{
        scopes: [
          {
            id: "current",
            kind: "tick",
            label: "Current only",
            checked: true,
            onChange: tick,
          },
          {
            id: "state",
            kind: "cycle",
            label: "State",
            value: "active",
            onChange: cycle,
            options: [
              { value: "active", label: "Active" },
              { value: "parked", label: "Parked" },
            ],
          },
        ],
        trailing: (
          <StringGadget label="Find a decision" value="" onChange={() => {}} />
        ),
      }}
    />,
  );
  const find = screen
    .getByRole("textbox", { name: "Find a decision" })
    .closest(".object-list-find-row")!;
  expect(
    within(find as HTMLElement).getByRole("checkbox", { name: "Current only" }),
  ).toBeChecked();
  fireEvent.click(screen.getByRole("checkbox", { name: "Current only" }));
  expect(tick).toHaveBeenCalledWith(false);
  fireEvent.change(screen.getByRole("combobox", { name: "State" }), {
    target: { value: "parked" },
  });
  expect(cycle).toHaveBeenCalledWith("parked");
});

it("changing a verb keeps the Find field and its focus mounted", () => {
  const list = (label: string) => (
    <ListView
      label="Recordings"
      rows={[]}
      toolbar={{
        trailing: (
          <StringGadget
            label="Find a recording"
            value="release"
            onChange={() => {}}
          />
        ),
      }}
      verbs={[{ id: "share", label, run: () => {} }]}
    />
  );
  const view = render(list("Share"));
  const find = screen.getByRole("textbox", { name: "Find a recording" });
  find.focus();
  view.rerender(list("Stop sharing"));
  expect(screen.getByRole("textbox", { name: "Find a recording" })).toBe(find);
  expect(find).toHaveFocus();
});

it("a group owns its egress line outside its field sheet and action row", () => {
  const { container } = render(
    <GadgetGroup egress={<span>Audio: carrier</span>}>
      <GadgetRow label="Calls">On</GadgetRow>
    </GadgetGroup>,
  );
  const line = screen.getByText("Audio: carrier");
  expect(line.closest(".gadget-group")).toBe(
    container.querySelector(".gadget-group"),
  );
  expect(line.closest(".surface-pane-egress")).toBeTruthy();
  expect(line.closest(".gadget-sheet,.gadget-group-actions")).toBeNull();
});

it("an inspector question cancels when the selected target changes", () => {
  const cancel = vi.fn(), a = vi.fn(), b = vi.fn();
  const { rerender } = render(<InspectorQuestion actionId="delete" targetId="A" question="Delete A?" cancel={cancel} verb={{label:"Delete",run:a}} />);
  rerender(<InspectorQuestion actionId="delete" targetId="B" question="Delete B?" cancel={cancel} verb={{label:"Delete",run:b}} />);
  expect(screen.queryByRole("button", {name:"Delete"})).toBeNull();
  expect(cancel).toHaveBeenCalledOnce();
  expect(a).not.toHaveBeenCalled();
  expect(b).not.toHaveBeenCalled();
});
it("an inspector answer retains the callback that asked the question", () => {
  const a = vi.fn(), refreshed = vi.fn(), cancel = vi.fn();
  const { rerender } = render(<InspectorQuestion actionId="delete" targetId="A" question="Delete A?" cancel={cancel} verb={{label:"Delete",run:a}} />);
  rerender(<InspectorQuestion actionId="delete" targetId="A" question="Delete A?" cancel={cancel} verb={{label:"Delete",run:refreshed}} />);
  fireEvent.click(screen.getByRole("button", {name:"Delete"}));
  expect(a).toHaveBeenCalledOnce(); expect(refreshed).not.toHaveBeenCalled();
});

it("status fitting never generates a hiding rule for ask or fail, even at a lower declared priority", () => {
  let rules = "";
  const adopted = document.adoptedStyleSheets;
  vi.stubGlobal(
    "CSSStyleSheet",
    class {
      replaceSync(value: string) {
        rules = value;
      }
    },
  );
  document.adoptedStyleSheets = [];
  const { container, unmount } = render(
    <StatusBar
      items={[
        { text: "5 items" },
        { text: "2 new" },
        { text: "Check settings", lamp: "warn" },
        { text: "1 needs you", lamp: "ask", priority: -10 },
        { text: "Not saved", lamp: "fail", priority: -20 },
      ]}
    />,
  );
  try {
    for (const text of ["1 needs you", "Not saved"]) {
      const part = [...container.querySelectorAll(".kit-statusbar-item")].find(
        (node) => node.textContent === text,
      )!;
      expect(rules).not.toContain(
        `[data-part="${part.getAttribute("data-part")}"] { display: none; }`,
      );
    }
    expect(rules).toContain("display: none");
  } finally {
    unmount();
    document.adoptedStyleSheets = adopted;
    vi.unstubAllGlobals();
  }
});

it("requires a stable target when an inspector holds an answer", () => {
  expectTypeOf<ComponentProps<typeof InspectorQuestion>>().toExtend<{
    targetId: string | number;
  }>();
});

it("a read-only fact uses the value seat when there is no control", () => {
  const { container } = render(
    <GadgetRow
      label="Call"
      fact={<DotWord tone="idle">Not set in Settings ▸ Calls</DotWord>}
      controlWidth="standard"
    >
      <span />
    </GadgetRow>,
  );
  const value = screen.getByText("Not set in Settings ▸ Calls");
  expect(value.closest(".gadget-row-gadget")).toBe(
    container.querySelector(".gadget-row-gadget"),
  );
  expect(value.closest(".gadget-row-label")).toBeNull();
});

it("a field keeps its auxiliary fact beside the label", () => {
  render(
    <GadgetRow label="Name" fact="Required">
      <StringGadget label="Device name" value="Desk" onChange={() => {}} />
    </GadgetRow>,
  );
  expect(
    screen.getByText("Required").closest(".gadget-row-label"),
  ).toBeTruthy();
  expect(
    screen
      .getByRole("textbox", { name: "Device name" })
      .closest(".gadget-row-gadget"),
  ).toBeTruthy();
});

it("one tab shows its named content without drawing a tab strip", () => {
  render(
    <SegmentedTabs
      label="Recording"
      value="details"
      tabs={[{ id: "details", label: "Details" }]}
      onChange={() => {}}
    >
      Recording failed
    </SegmentedTabs>,
  );
  expect(screen.queryByRole("tablist")).toBeNull();
  expect(screen.queryByRole("tab")).toBeNull();
  expect(screen.getByRole("tabpanel", { name: "Details" })).toHaveTextContent(
    "Recording failed",
  );
});

it("keeps modified row verbs on the selection and leaves editor keys alone", () => {
  const move = vi.fn();
  render(
    <ListView
      label="Steps"
      headerless
      rows={[
        { id: "one", name: "First", kind: "program" },
        { id: "two", name: "Second", kind: "program" },
      ]}
      columns={[{ key: "name", word: "Step" }]}
      selectedId="two"
      verbs={[{ id: "up", label: "Move up", key: "Alt+ArrowUp", run: move }]}
    />,
  );
  const row = screen.getByText("Second").closest("[role=row]") as HTMLElement;
  row.focus();
  fireEvent.keyDown(row, { key: "ArrowUp", altKey: true });
  expect(move).toHaveBeenCalledTimes(1);
  expect(move).toHaveBeenCalledWith(expect.objectContaining({ id: "two" }));
  expect(document.activeElement).toBe(row);
  fireEvent.keyDown(row, { key: "ArrowUp" });
  expect(move).toHaveBeenCalledTimes(1);
});

it("disarms a Park/Go on question without pressing Park when its saved revision moves", () => {
  const park = vi.fn(),
    go = vi.fn(),
    disarm = vi.fn();
  const question = (target: string) => (
    <InspectorQuestion
      actionId="answer"
      targetId={target}
      question="Go on?"
      cancelLabel="Park"
      cancel={park}
      onDisarm={disarm}
      variant="brass"
      verb={{ label: "Go on", run: go }}
    />
  );
  const { rerender } = render(question("step:1"));
  expect(screen.getByRole("button", { name: "Park" })).toHaveFocus();
  rerender(question("step:2"));
  expect(disarm).toHaveBeenCalled();
  expect(park).not.toHaveBeenCalled();
  expect(go).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: "Go on" })).toBeNull();
});

it("a different action on the same target disarms its cached question", () => {
  const cancel=vi.fn(), skip=vi.fn(), send=vi.fn();
  const {rerender} = render(<InspectorQuestion targetId="finding:1" actionId="skip" question="Skip?" cancel={cancel} verb={{label:"Skip",run:skip}} />);
  rerender(<InspectorQuestion targetId="finding:1" actionId="telegram" question="Send to Telegram?" cancel={cancel} verb={{label:"Send to Telegram",run:send}} />);
  expect(screen.queryByRole("button", {name:"Send to Telegram"})).toBeNull();
  expect(cancel).toHaveBeenCalledOnce();
  expect(skip).not.toHaveBeenCalled(); expect(send).not.toHaveBeenCalled();
});
