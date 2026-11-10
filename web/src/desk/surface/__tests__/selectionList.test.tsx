import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ListView, CycleGadget, CheckGadget, type ListVerb } from "..";
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
    expect(within(menu).getAllByRole("menuitem").map((item) => item.textContent?.replace(/Enter|Delete/g, ""))).toEqual(["Open", "Remove"]);
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

it("composes a collection toolbar with Find from the same verb declaration", () => {
  render(<ListView label="People" actionBar="top" trailing={<input aria-label="Find a person" />} rows={[]} verbs={[{ id: "add", label: "Add person", run: () => {} }]} />);
  const toolbar = screen.getByRole("toolbar", { name: "People actions" });
  expect(toolbar).toHaveClass("kit-toolbar", "object-list-toolbar");
  expect(within(toolbar).getByRole("button", { name: "Add person" })).toBeEnabled();
  expect(within(toolbar).getByRole("textbox", { name: "Find a person" })).toBeTruthy();
});
