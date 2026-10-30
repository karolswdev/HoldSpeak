// PHILO-14 B1 — the object species (contract.md "The object species").
// Render, keyboard, aria, no text-mode marks, and the 393 fold (jsdom has
// no container queries, so the fold is proven by its rule in objects.css
// plus the fold line in the DOM; the browser contact sheet shows it drawn).
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { Button } from "../../../components/signal/Signal";
import {
  AskWell,
  ConfirmLine,
  DeskIcon,
  DotWord,
  DragGhost,
  DropTarget,
  FilesChanged,
  GetInfo,
  IconGrid,
  NeedsList,
  NeedsRow,
  ObjectList,
  PRCard,
  StationTrack,
  TimelineRail,
  Toolbar,
  objectSprite,
  type ObjectListRow,
  type ObjectSort,
} from "..";

// jsdom has no PointerEvent: without it fireEvent.pointer* drops button and
// clientX. A MouseEvent carries both.
if (typeof window.PointerEvent === "undefined")
  (window as unknown as { PointerEvent: typeof MouseEvent }).PointerEvent = MouseEvent;


/** The text-mode selection marks the owner forbade ("[ ]" in the copy). */
const noTextMarks = (root: HTMLElement) => {
  expect(root.textContent ?? "").not.toMatch(/\[\s?\]|\[x\]/i);
};

/** Every verb is the library Button (UX-CANON A.1). */
const allLibraryButtons = (root: HTMLElement) => {
  for (const button of root.querySelectorAll("button"))
    expect(button.className).toMatch(/\bbtn\b|btn--chrome/);
};


const a11y = async (container: HTMLElement) => {
  const result = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(result.violations).toEqual([]);
};

describe("DeskIcon + IconLamp", () => {
  it("renders the sprite over its name, the lamp, the count notch and the badge", () => {
    const { container } = render(
      <DeskIcon
        id="p-ledger"
        kind="project"
        name="Payments ledger cutover"
        lamp={{ tone: "ask", count: 3, label: "3 need you" }}
        badge="/badge.png"
      />,
    );
    const icon = screen.getByRole("button", { name: "Payments ledger cutover, Project, 3 need you" });
    expect(icon.className).toContain("btn--chrome");
    expect(icon.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("ask");
    expect(icon.querySelector(".desk-icon-count")?.textContent).toBe("3");
    expect(icon.querySelector(".desk-icon-badge")?.getAttribute("src")).toBe("/badge.png");
    expect(icon.querySelector("img")?.getAttribute("src")).toBe(objectSprite("project", "p-ledger"));
    noTextMarks(container);
  });

  it("draws no count notch at zero", () => {
    render(<DeskIcon id="x" kind="note" name="Note" lamp={{ tone: "ok", count: 0 }} />);
    expect(document.querySelector(".desk-icon-count")).toBeNull();
  });

  it("selected: aria-pressed, the _sel sprite, the inverted plate", () => {
    render(<DeskIcon id="n1" kind="note" name="Ledger cutover risks" selected />);
    const icon = screen.getByRole("button", { name: /Ledger cutover risks/ });
    expect(icon).toHaveAttribute("aria-pressed", "true");
    expect(icon).toHaveAttribute("data-selected", "true");
    expect(icon.querySelector("img")?.getAttribute("src")).toMatch(/_sel\.png$/);
  });

  it("keyboard: Space selects, Enter opens, a press selects, a double press opens", async () => {
    const onSelect = vi.fn();
    const onOpen = vi.fn();
    render(<DeskIcon id="a" kind="agent" name="Claude Code" onSelect={onSelect} onOpen={onOpen} />);
    const icon = screen.getByRole("button", { name: /Claude Code/ });
    icon.focus();
    await userEvent.keyboard(" ");
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onOpen).not.toHaveBeenCalled();
    await userEvent.keyboard("{Enter}");
    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledTimes(1);
    await userEvent.click(icon);
    expect(onSelect).toHaveBeenCalledTimes(2);
    await userEvent.dblClick(icon);
    expect(onOpen).toHaveBeenCalledTimes(2);
  });

  it("non-pointer activation selects: element.click() (assistive press) fires onSelect once", () => {
    const onSelect = vi.fn();
    const onOpen = vi.fn();
    render(<DeskIcon id="a" kind="agent" name="Claude Code" onSelect={onSelect} onOpen={onOpen} />);
    const icon = screen.getByRole("button", { name: /Claude Code/ });
    icon.click();
    expect(onSelect).toHaveBeenCalledTimes(1);
    fireEvent.click(icon, { detail: 0 });
    expect(onSelect).toHaveBeenCalledTimes(2);
    expect(onOpen).not.toHaveBeenCalled();
  });

  it("keyboard fires exactly once: Space = one select, Enter = one open and no select", async () => {
    const onSelect = vi.fn();
    const onOpen = vi.fn();
    render(<DeskIcon id="a" kind="agent" name="Claude Code" onSelect={onSelect} onOpen={onOpen} />);
    screen.getByRole("button", { name: /Claude Code/ }).focus();
    await userEvent.keyboard(" ");
    expect([onSelect.mock.calls.length, onOpen.mock.calls.length]).toEqual([1, 0]);
    await userEvent.keyboard("{Enter}");
    expect([onSelect.mock.calls.length, onOpen.mock.calls.length]).toEqual([1, 1]);
  });
});

describe("IconGrid", () => {
  it("is a named group; one Tab stop; a press on the glass clears", () => {
    const onClear = vi.fn();
    render(
      <IconGrid label="Payments ledger cutover" onClear={onClear}>
        <DeskIcon id="a" kind="meeting" name="Ledger cutover sync" />
        <DeskIcon id="b" kind="decision" name="Freeze the old ledger" />
      </IconGrid>,
    );
    const grid = screen.getByRole("group", { name: "Payments ledger cutover" });
    const [first, second] = within(grid).getAllByRole("button");
    expect(first.tabIndex).toBe(0);
    expect(second.tabIndex).toBe(-1);
    fireEvent.pointerDown(grid, { button: 0, clientX: 5, clientY: 5, pointerId: 1 });
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("reports the rubber band to the caller and draws the caller's rectangle", () => {
    const seen: unknown[] = [];
    function Host() {
      const [rect, setRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
      return (
        <IconGrid
          label="Floor"
          marquee={rect}
          onMarquee={(next) => {
            seen.push(next);
            if (next) setRect(next);
          }}
        >
          <DeskIcon id="a" kind="note" name="A" />
        </IconGrid>
      );
    }
    render(<Host />);
    const grid = screen.getByRole("group", { name: "Floor" });
    fireEvent.pointerDown(grid, { button: 0, clientX: 10, clientY: 10, pointerId: 1 });
    fireEvent.pointerMove(grid, { clientX: 60, clientY: 40, pointerId: 1 });
    expect(seen[0]).toEqual({ x: 10, y: 10, w: 50, h: 30 });
    expect(grid.querySelector(".desk-icon-marquee")).not.toBeNull();
    fireEvent.pointerUp(grid, { pointerId: 1 });
    expect(seen.at(-1)).toBeNull();
  });

  it("PHILO-14 A1: the arrows follow an irregular layout (a drawer column beside a field)", () => {
    render(
      <IconGrid label="Desk">
        {["p1", "p2", "p3", "m1", "m2", "m3", "needs"].map((id) => (
          <DeskIcon key={id} id={id} kind="note" name={id} />
        ))}
      </IconGrid>,
    );
    const icons = within(screen.getByRole("group", { name: "Desk" })).getAllByRole("button");
    // A-1: drawers down the left (DOM first), the field beside them, Needs you far right.
    const at = [[20, 12], [20, 124], [20, 236], [210, 24], [330, 24], [210, 140], [1300, 12]];
    icons.forEach((icon, i) => {
      const [left, top] = at[i];
      icon.getBoundingClientRect = () =>
        ({ top, left, width: 112, height: 96, right: left + 112, bottom: top + 96, x: left, y: top, toJSON: () => ({}) }) as DOMRect;
    });
    const focused = () => icons.indexOf(document.activeElement as HTMLElement);
    const press = (key: string) => fireEvent.keyDown(document.activeElement as HTMLElement, { key });
    icons[0].focus();
    press("ArrowRight"); // the drawer -> the first loose object beside it
    expect(focused()).toBe(3);
    press("ArrowRight");
    expect(focused()).toBe(4);
    press("ArrowRight"); // far across the field -> Needs you
    expect(focused()).toBe(6);
    press("ArrowLeft");
    expect(focused()).toBe(4);
    press("ArrowLeft");
    expect(focused()).toBe(3);
    press("ArrowDown");
    expect(focused()).toBe(5);
    press("ArrowLeft"); // back to the drawer column, the nearest one
    expect(focused()).toBe(1);
    press("ArrowDown");
    expect(focused()).toBe(2);
  });

  it("2-D navigation by the RENDERED columns: Left/Right in the row, Up/Down by the column count, Home/End", () => {
    render(
      <IconGrid label="Drawer">
        {["a", "b", "c", "d", "e", "f", "g"].map((id) => (
          <DeskIcon key={id} id={id} kind="note" name={id.toUpperCase()} />
        ))}
      </IconGrid>,
    );
    const icons = within(screen.getByRole("group", { name: "Drawer" })).getAllByRole("button");
    // A fixed-width grid of three columns: the rows sit at top 0, 100, 200.
    icons.forEach((icon, i) => {
      icon.getBoundingClientRect = () =>
        ({ top: Math.floor(i / 3) * 100, left: (i % 3) * 112, width: 112, height: 96, right: (i % 3) * 112 + 112, bottom: Math.floor(i / 3) * 100 + 96, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;
    });
    const at = () => icons.indexOf(document.activeElement as HTMLElement);
    const press = (key: string) => fireEvent.keyDown(document.activeElement as HTMLElement, { key });
    icons[0].focus();
    press("ArrowRight");
    expect(at()).toBe(1);
    press("ArrowRight");
    expect(at()).toBe(2);
    press("ArrowRight"); // the row's end: no wrap
    expect(at()).toBe(2);
    press("ArrowDown");
    expect(at()).toBe(5);
    press("ArrowDown"); // 8 does not exist
    expect(at()).toBe(5);
    press("ArrowLeft");
    expect(at()).toBe(4);
    press("ArrowUp");
    expect(at()).toBe(1);
    press("End");
    expect(at()).toBe(6);
    press("Home");
    expect(at()).toBe(0);
    expect(icons[0].tabIndex).toBe(0);
    expect(icons.filter((i) => i.tabIndex === 0)).toHaveLength(1);
  });
});

const ROWS: ObjectListRow[] = [
  { id: "r1", kind: "action", name: "Write the rollback runbook", when: "TODAY", whenSort: 3, state: { label: "CLAUDE CODE ASKS", tone: "ask" } },
  { id: "r2", kind: "agent", name: "Codex: reconciliation", when: "30 MIN", whenSort: 2, state: { label: "WORKS", tone: "info" } },
  { id: "r3", kind: "note", name: "Ledger cutover risks", when: "OCT 5", whenSort: 1 },
];

function ListHost(props: { onOpen?(id: string): void }) {
  const [sort, setSort] = useState<ObjectSort>({ key: "name", dir: "asc" });
  const [sel, setSel] = useState<string | null>(null);
  return (
    <ObjectList
      label="Payments ledger cutover"
      rows={ROWS}
      sort={sort}
      onSort={(key) => setSort((s) => ({ key, dir: s.key === key && s.dir === "asc" ? "desc" : "asc" }))}
      selectedId={sel}
      onSelect={setSel}
      onOpen={props.onOpen}
    />
  );
}

describe("ObjectList", () => {
  it("is a grid with Name/Kind/When/State headers (aria-sort) and no text-mode marks", async () => {
    const { container } = render(<ListHost />);
    const grid = screen.getByRole("grid", { name: "Payments ledger cutover" });
    const headers = within(grid).getAllByRole("columnheader");
    expect(headers.map((h) => h.textContent?.replace(/[▲▼]/, ""))).toEqual(["Name", "Kind", "When", "State"]);
    expect(headers[0]).toHaveAttribute("aria-sort", "ascending");
    expect(headers[1]).toHaveAttribute("aria-sort", "none");
    const names = within(grid).getAllByRole("row").slice(1).map((row) => row.querySelector(".object-list-name-word")?.textContent);
    expect(names).toEqual(["Codex: reconciliation", "Ledger cutover risks", "Write the rollback runbook"]);
    noTextMarks(container);
    allLibraryButtons(container);
    await a11y(container);
  });

  it("a Name/Kind projection has matching headers and cells, with the same row keys and sort door", async () => {
    const onSelect = vi.fn();
    const onOpen = vi.fn();
    const onSort = vi.fn();
    render(<ObjectList label="Filed notes" rows={ROWS} sort={{ key: "name", dir: "asc" }}
      visibleColumns={["kind"]} onSelect={onSelect} onOpen={onOpen} onSort={onSort} />);
    const grid = screen.getByRole("grid", { name: "Filed notes" });
    expect(grid).toHaveAttribute("data-compact-columns", "true");
    const headers = within(grid).getAllByRole("columnheader");
    expect(headers.map((head) => head.getAttribute("data-col"))).toEqual(["name", "kind"]);
    for (const row of within(grid).getAllByRole("row").slice(1))
      expect(within(row).getAllByRole("gridcell").map((cell) => cell.getAttribute("data-col"))).toEqual(["name", "kind"]);
    expect(grid.querySelector('[data-object-id="r1"] .object-list-open')).toHaveAttribute("aria-label",
      expect.stringContaining("CLAUDE CODE ASKS"));
    await userEvent.click(within(grid).getByRole("button", { name: "Kind" }));
    expect(onSort).toHaveBeenCalledWith("kind");
    const open = grid.querySelector('[data-object-id="r2"] .object-list-open') as HTMLButtonElement;
    open.focus();
    await userEvent.keyboard(" ");
    await userEvent.keyboard("{Enter}");
    expect(onSelect).toHaveBeenCalledWith("r2");
    expect(onOpen).toHaveBeenCalledExactlyOnceWith("r2");
  });

  it("a header press sorts; a second press flips the direction", async () => {
    render(<ListHost />);
    const grid = screen.getByRole("grid");
    await userEvent.click(within(grid).getByRole("button", { name: "When" }));
    const header = within(grid).getAllByRole("columnheader")[2];
    expect(header).toHaveAttribute("aria-sort", "ascending");
    const order = () => within(grid).getAllByRole("row").slice(1).map((r) => r.getAttribute("data-object-id"));
    expect(order()).toEqual(["r3", "r2", "r1"]);
    await userEvent.click(within(grid).getByRole("button", { name: /When/ }));
    expect(header).toHaveAttribute("aria-sort", "descending");
    expect(order()).toEqual(["r1", "r2", "r3"]);
  });

  it("non-pointer activation: element.click() on a row selects it", () => {
    render(<ListHost />);
    const grid = screen.getByRole("grid");
    const row = grid.querySelector('[role="row"][data-object-id="r2"]')!;
    act(() => (row.querySelector("button") as HTMLButtonElement).click());
    expect(row).toHaveAttribute("aria-selected", "true");
  });

  it("keyboard fires exactly once: Space selects once, Enter opens once and does not select", async () => {
    const onSelect = vi.fn();
    const onOpen = vi.fn();
    render(
      <ObjectList label="L" rows={ROWS} sort={{ key: "name", dir: "asc" }} onSelect={onSelect} onOpen={onOpen} />,
    );
    (screen.getByRole("grid").querySelector('[data-object-id="r1"] button') as HTMLButtonElement).focus();
    await userEvent.keyboard(" ");
    expect([onSelect.mock.calls.length, onOpen.mock.calls.length]).toEqual([1, 0]);
    await userEvent.keyboard("{Enter}");
    expect([onSelect.mock.calls.length, onOpen.mock.calls.length]).toEqual([1, 1]);
  });

  it("the selection is the row: a press selects, Space selects, Enter opens, arrows walk", async () => {
    const onOpen = vi.fn();
    render(<ListHost onOpen={onOpen} />);
    const grid = screen.getByRole("grid");
    const rowOf = (id: string) => grid.querySelector(`[role="row"][data-object-id="${id}"]`)!;
    const open = (id: string) => rowOf(id).querySelector("button")!;
    await userEvent.click(open("r3"));
    expect(rowOf("r3")).toHaveAttribute("aria-selected", "true");
    open("r2").focus();
    await userEvent.keyboard(" ");
    expect(rowOf("r2")).toHaveAttribute("aria-selected", "true");
    expect(rowOf("r3")).toHaveAttribute("aria-selected", "false");
    await userEvent.keyboard("{Enter}");
    expect(onOpen).toHaveBeenCalledWith("r2");
    fireEvent.keyDown(open("r2"), { key: "ArrowDown" });
    expect(document.activeElement).toBe(open("r3"));
  });

  it("the state cell is one lamp and its word", () => {
    render(<ListHost />);
    const lamp = screen.getByRole("grid").querySelector('[data-object-id="r1"] .gadget-lamp');
    expect(lamp?.textContent).toBe("Claude Code asks");
  });

  it("one object, one colour: the row's lamp carries the icon's tone (ask, info), not a lossy map", () => {
    render(<ListHost />);
    const grid = screen.getByRole("grid");
    expect(grid.querySelector('[data-object-id="r1"] .gadget-lamp')).toHaveAttribute("data-tone", "ask");
    expect(grid.querySelector('[data-object-id="r2"] .gadget-lamp')).toHaveAttribute("data-tone", "info");
    render(<DeskIcon id="r2" kind="agent" name="Codex" lamp={{ tone: "info" }} />);
    expect(document.querySelector(".desk-icon-lamp")).toHaveAttribute("data-tone", "info");
  });

  it("393: the fold is visual; headers and cells name the same four columns", () => {
    render(<ListHost />);
    const grid = screen.getByRole("grid");
    const fold = grid.querySelector('[data-object-id="r3"] .object-list-fold');
    expect(fold?.textContent).toBe("NoteOCT 5");
    expect(fold).toHaveAttribute("aria-hidden", "true");
    const headers = within(grid).getAllByRole("columnheader").map((h) => h.getAttribute("data-col"));
    for (const row of within(grid).getAllByRole("row").slice(1))
      expect(within(row).getAllByRole("gridcell").map((c) => c.getAttribute("data-col"))).toEqual(headers);
  });
});

describe("PHILO-14 A0c: the list species read the 32 px set", () => {
  it("an ObjectList row, a Needs-you row and a confirm line show the drawn 32 px file", () => {
    render(<ListHost />);
    const srcs = within(screen.getByRole("grid", { name: "Payments ledger cutover" }))
      .getAllByRole("row")
      .slice(1)
      .map((row) => row.querySelector("img")?.getAttribute("src"));
    expect(srcs.length).toBeGreaterThan(0);
    for (const src of srcs) expect(src).toMatch(/\/desk\/sprites\/32\/[a-z-]+\.png$/);
    render(
      <NeedsList label="Needs 32">
        <NeedsRow id="pr:1" kind="pr" name="PR" lamp={{ label: "PR OPEN", tone: "ok" }} />
      </NeedsList>,
    );
    const needs = within(screen.getByRole("list", { name: "Needs 32" })).getByRole("listitem");
    expect(needs.querySelector("img")?.getAttribute("src")).toMatch(/\/desk\/sprites\/32\/pull-request\.png$/);
  });

  it("a row that brings its own 64 px sprite URL gets the 32 px sibling; the icon keeps the 64", () => {
    const sprite = objectSprite("meeting", "m1");
    render(
      <ObjectList
        label="Own sprite"
        rows={[{ id: "m1", kind: "meeting", name: "Standup", sprite }]}
        sort={{ key: "name", dir: "asc" }}
      />,
    );
    const row = within(screen.getByRole("grid", { name: "Own sprite" })).getAllByRole("row")[1];
    expect(row.querySelector("img")?.getAttribute("src")).toBe(sprite.replace("/sprites/", "/sprites/32/"));
    const icon = render(<DeskIcon id="m1" kind="meeting" name="Standup" sprite={sprite} />);
    expect(icon.container.querySelector(".desk-icon img")?.getAttribute("src")).toBe(sprite);
  });
});

describe("GetInfo", () => {
  it("draws identity and only the facts it is given, verbs in the footer", async () => {
    const { container } = render(
      <GetInfo
        id="r1"
        kind="action"
        name="Write the rollback runbook"
        facts={{
          where: "Payments ledger cutover",
          from: "Ledger cutover sync",
          made: "TODAY 08:40",
          owner: "Claude Code (agent)",
          state: { label: "CLAUDE CODE ASKS", tone: "ask" },
          branch: "hs/write-the-rollback-runbook",
        }}
        verbs={<Button dense variant="primary">Open</Button>}
      />,
    );
    expect(screen.getByRole("heading", { name: "Write the rollback runbook" })).toBeInTheDocument();
    expect(screen.getByText("Action item")).toBeInTheDocument();
    const terms = [...container.querySelectorAll("dt")].map((dt) => dt.textContent);
    expect(terms).toEqual(["Where", "From", "Made", "Owner", "State", "Branch"]);
    expect(container.querySelector('[data-fact="due"]')).toBeNull();
    expect(container.querySelector(".surface-footer-verbs")?.textContent).toBe("Open");
    await a11y(container);
  });
});

describe("TimelineRail + StationTrack", () => {
  it("draws the rail: time, square, WORD, text/code/quote, verbs, the pending MERGE", async () => {
    const { container } = render(
      <TimelineRail
        label="Lane"
        entries={[
          { time: "09:42", word: "BRIEF", text: "6 sources · 4.2 KB · 3 checks", verbs: <Button dense variant="ghost">Brief</Button> },
          { time: "09:45", word: "SAYS", quote: "I will draft the runbook." },
          { time: "09:55", word: "HELD", tone: "warn", code: "psql -h staging-ledger", verbs: <><Button dense variant="ghost">Deny</Button><Button dense>Approve</Button></> },
          { time: "09:56", word: "ASKS", tone: "ask", text: "Jordan or Avery?" },
          { word: "MERGE", text: "Your press in GitHub", pending: true },
        ]}
      />,
    );
    const rail = screen.getByRole("list", { name: "Lane" });
    const items = within(rail).getAllByRole("listitem");
    expect(items).toHaveLength(5);
    expect(items[1].querySelector("q")?.textContent).toBe("I will draft the runbook.");
    expect(items[2].querySelector(".lane-square")?.getAttribute("data-tone")).toBe("warn");
    expect(within(items[2]).getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(items[4]).toHaveAttribute("data-pending", "true");
    expect(items[4].querySelector(".lane-square")).toHaveAttribute("data-pending", "true");
    allLibraryButtons(container);
    await a11y(container);
  });

  it("draws the track: reached filled, current lit (aria-current step), the rest hollow; subs fold at 393", () => {
    render(
      <StationTrack
        label="Lane stations"
        stations={[
          { word: "BRIEF", sub: "09:42", state: "reached" },
          { word: "PR", sub: "#413", state: "reached", tone: "info" },
          { word: "ASKS", sub: "now", state: "current", tone: "ask" },
          { word: "MERGE", sub: "yours", state: "ahead" },
        ]}
      />,
    );
    const items = within(screen.getByRole("list", { name: "Lane stations" })).getAllByRole("listitem");
    expect(items[0].querySelector(".lane-square")).toHaveAttribute("data-tone", "ok");
    expect(items[1].querySelector(".lane-square")).toHaveAttribute("data-tone", "info");
    expect(items[2]).toHaveAttribute("aria-current", "step");
    expect(items[2].querySelector(".lane-square")).toHaveAttribute("data-lit", "true");
    expect(items[3].querySelector(".lane-square")).toHaveAttribute("data-pending", "true");
  });
});

describe("AskWell", () => {
  it("caption, question, the field with its mic, Answer on Enter and press, Use draft, egress", async () => {
    const onAnswer = vi.fn();
    const onUseDraft = vi.fn();
    function Host() {
      const [value, setValue] = useState("");
      return (
        <AskWell
          agent="Claude Code"
          age="6 min"
          question="The runbook needs a rollback owner. Jordan or Avery?"
          value={value}
          onChange={setValue}
          onAnswer={onAnswer}
          draft="Jordan owns it. Avery reviews."
          onUseDraft={(d) => { onUseDraft(d); setValue(d); }}
          draftEgress={{ label: "API.ANTHROPIC.COM", scope: "cloud" }}
        />
      );
    }
    const { container } = render(<Host />);
    expect(screen.getByText("Claude Code asks · 6 min")).toBeInTheDocument();
    // The field is the StringGadget (its mic draws where the browser can listen).
    expect(container.querySelector(".ask-well-answer > .gadget-string")).not.toBeNull();
    const field = screen.getByRole("textbox", { name: "Answer" });
    await userEvent.click(screen.getByRole("button", { name: "Answer" }));
    expect(onAnswer).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(field);
    await userEvent.type(field, "Jordan{Enter}");
    expect(onAnswer).toHaveBeenCalledWith("Jordan");
    expect(container.querySelectorAll(".ask-well-answer .gadget-chip-egress")).toHaveLength(0);
    await userEvent.click(screen.getByRole("button", { name: "Use draft" }));
    expect(onUseDraft).toHaveBeenCalledWith("Jordan owns it. Avery reviews.");
    await userEvent.click(screen.getByRole("button", { name: "Answer" }));
    expect(onAnswer).toHaveBeenLastCalledWith("Jordan owns it. Avery reviews.");
    expect(screen.getByText("API.ANTHROPIC.COM")).toBeInTheDocument();
    await a11y(container);
  });
});

describe("PRCard + FilesChanged", () => {
  it("all pending: Checks · 7 running, never Checks 0 of 7; never 0 failed", () => {
    const { container, rerender } = render(<PRCard number={9} title="t" checks={{ passed: 0, total: 7, running: 7 }} />);
    expect(container.textContent).toContain("Checks · 7 running");
    expect(container.textContent).not.toMatch(/\b0 of\b|\b0 failed\b|\b0 running\b/i);
    rerender(<PRCard number={9} title="t" checks={{ passed: 0, total: 7, failed: 2, running: 5 }} />);
    expect(container.textContent).toContain("Checks · 2 failed");
    expect(container.textContent).toContain("5 running");
    expect(container.textContent).not.toMatch(/\b0 of\b/i);
    rerender(<PRCard number={9} title="t" checks={{ passed: 7, total: 7, failed: 0, running: 0 }} />);
    expect(container.textContent).toContain("Checks 7 of 7");
    expect(container.textContent).not.toMatch(/\b0 (failed|running)\b/i);
    rerender(<PRCard number={9} title="t" checks={{ passed: 0, total: 3 }} />);
    expect(container.textContent).toContain("Checks · 3 pending");
  });

  it("checks as a lamp, running only when running, review, branch → base", () => {
    render(
      <PRCard
        number={413}
        title="Draft the ledger rollback runbook"
        checks={{ passed: 6, total: 7, running: 1 }}
        review="none yet"
        branch="hs/write-the-rollback-runbook"
        base="main"
      />,
    );
    const card = screen.getByRole("article", { name: /#413/ });
    expect(within(card).getByText("Checks 6 of 7")).toBeInTheDocument();
    expect(within(card).getByText("1 running")).toBeInTheDocument();
    expect(card.textContent).toContain("Review none yet");
    expect(card.textContent).toContain("hs/write-the-rollback-runbook → main");
  });

  it("no counters of zero: no RUNNING lamp at zero, no +0 / −0", () => {
    render(
      <>
        <PRCard number={1} title="t" checks={{ passed: 7, total: 7, running: 0 }} />
        <FilesChanged files={[{ path: "a.py", added: 3, removed: 1 }, { path: "b.md", added: 84, removed: 0 }]} />
      </>,
    );
    expect(screen.queryByText(/running/i)).toBeNull();
    expect(screen.getByText("Files changed · 2")).toBeInTheDocument();
    expect(screen.getByText("+3 −1")).toBeInTheDocument();
    expect(screen.getByText("+84")).toBeInTheDocument();
  });

  it("draws nothing for no files", () => {
    const { container } = render(<FilesChanged files={[]} />);
    expect(container.innerHTML).toBe("");
  });
});

describe("ConfirmLine", () => {
  it("from → to, title, fact line, Brief ▸ / Cancel / Hand (one primary)", async () => {
    const onHand = vi.fn();
    const onCancel = vi.fn();
    const onBrief = vi.fn();
    const { container } = render(
      <ConfirmLine
        from={{ kind: "action", id: "act-comms" }}
        to={{ kind: "agent", id: "claude:launcher" }}
        title="Write the cutover comms"
        fact="CLAUDE CODE · OPEN THROTTLE · hs/write-the-cutover-comms"
        onBrief={onBrief}
        onCancel={onCancel}
        onHand={onHand}
      />,
    );
    const group = screen.getByRole("group", { name: "Hand: Write the cutover comms" });
    expect(within(group).getByText("CLAUDE CODE · OPEN THROTTLE · hs/write-the-cutover-comms")).toBeInTheDocument();
    const verbs = within(group).getAllByRole("button").map((b) => b.textContent);
    expect(verbs).toEqual(["Brief ▸", "Cancel", "Hand"]);
    expect(container.querySelectorAll(".btn--primary")).toHaveLength(1);
    await userEvent.click(within(group).getByRole("button", { name: "Brief ▸" }));
    await userEvent.click(within(group).getByRole("button", { name: "Hand" }));
    await userEvent.click(within(group).getByRole("button", { name: "Cancel" }));
    expect([onBrief, onHand, onCancel].map((f) => f.mock.calls.length)).toEqual([1, 1, 1]);
    allLibraryButtons(container);
    await a11y(container);
  });
});

describe("NeedsRow + DropTarget + DragGhost", () => {
  it("the row is the object: sprite, name, fact, one lamp, its verbs; folds at 393", async () => {
    const { container } = render(
      <NeedsList label="Needs you">
        <NeedsRow
          id="claude:c1"
          kind="agent"
          name="Claude Code: rollback runbook"
          fact="The runbook needs a rollback owner. Jordan or Avery?"
          lamp={{ label: "ASKS · 6 MIN", tone: "ask" }}
          verbs={<><Button dense variant="ghost">Open</Button><Button dense variant="primary">Answer</Button></>}
        />
      </NeedsList>,
    );
    const row = within(screen.getByRole("list", { name: "Needs you" })).getByRole("listitem");
    expect(row.querySelectorAll(".gadget-lamp")).toHaveLength(1);
    expect(within(row).getByText("Asks · 6 min")).toBeInTheDocument();
    expect(within(row).getAllByRole("button").map((b) => b.textContent)).toEqual(["Open", "Answer"]);
    noTextMarks(container);
    await a11y(container);
  });

  it("DropTarget lights; DragGhost is an aria-hidden sprite at the pointer", () => {
    const { container } = render(
      <>
        <DropTarget lit>
          <DeskIcon id="conductor" kind="conductor" name="Conductor" drop />
        </DropTarget>
        <DragGhost kind="action" id="act-comms" x={62} y={486} />
      </>,
    );
    expect(container.querySelector(".drop-target")).toHaveAttribute("data-lit", "true");
    expect(screen.getByRole("button", { name: /Conductor/ })).toHaveAttribute("data-drop", "true");
    const ghost = container.querySelector(".drag-ghost") as HTMLImageElement;
    expect(ghost).toHaveAttribute("aria-hidden", "true");
    expect(ghost.style.left).toBe("62px");
  });
});

describe("PHILO-14 C3: the drag props", () => {
  it("DeskIcon passes the drop-target events; DragGhost draws the dotted path from `from`", () => {
    const over = vi.fn((e: React.DragEvent) => e.preventDefault());
    const leave = vi.fn();
    const drop = vi.fn();
    const end = vi.fn();
    const { container } = render(
      <>
        <DeskIcon id="conductor" kind="conductor" name="Conductor" onDragOver={over} onDragLeave={leave} onDrop={drop} />
        <DeskIcon id="act" kind="action" name="Write the cutover comms" draggable onDragEnd={end} />
        <DragGhost kind="action" id="act" x={62} y={486} from={{ x: 840, y: 250 }} />
      </>,
    );
    const target = screen.getByRole("button", { name: /Conductor/ });
    fireEvent.dragOver(target);
    fireEvent.dragLeave(target);
    fireEvent.drop(target);
    fireEvent.dragEnd(screen.getByRole("button", { name: /Write the cutover comms/ }));
    expect([over, leave, drop, end].map((f) => f.mock.calls.length)).toEqual([1, 1, 1, 1]);
    const path = container.querySelector(".drag-path line")!;
    expect(container.querySelector(".drag-path")).toHaveAttribute("aria-hidden", "true");
    expect([path.getAttribute("x1"), path.getAttribute("y1"), path.getAttribute("x2"), path.getAttribute("y2")]).toEqual([
      "840",
      "250",
      "94",
      "518",
    ]);
  });

  it("ConfirmLine: egress on the Hand side, a status line, Hand disabled, verbs after the press", () => {
    const { rerender } = render(
      <ConfirmLine
        from={{ kind: "action", id: "a" }}
        to={{ kind: "coder", id: "claude" }}
        title="Write the cutover comms"
        fact="CLAUDE CODE · OPEN THROTTLE"
        onCancel={() => undefined}
        onHand={() => undefined}
        disabled
        egress={<span data-testid="egress">API.ANTHROPIC.COM</span>}
        status={<span>AGENT LIMIT REACHED</span>}
      />,
    );
    const group = screen.getByRole("group", { name: "Hand: Write the cutover comms" });
    expect(within(group).getByRole("button", { name: "Hand" })).toBeDisabled();
    expect(within(group).getByText("AGENT LIMIT REACHED")).toBeInTheDocument();
    // The egress sits on the Hand side, just before the verbs (it wraps above them at 393).
    expect(group.querySelector(".confirm-line-verbs")!.previousElementSibling!.firstElementChild).toHaveAttribute(
      "data-testid",
      "egress",
    );
    rerender(
      <ConfirmLine
        from={{ kind: "action", id: "a" }}
        to={{ kind: "coder", id: "claude" }}
        title="Write the cutover comms"
        fact="CLAUDE CODE · OPEN THROTTLE"
        onCancel={() => undefined}
        onHand={() => undefined}
        verbs={<Button dense variant="ghost">Close</Button>}
      />,
    );
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(["Close"]);
  });
});

describe("the bevel grammar", () => {
  it("the SAYS quote is flat text in its quotes", () => {
    render(<TimelineRail label="L" entries={[{ word: "SAYS", quote: "Hello" }]} />);
    expect(document.querySelector("q.lane-rail-quote")?.textContent).toBe("Hello");
  });
});

describe("AskWell egress", () => {
  it("names the Answer's egress beside Answer, with no draft at all", () => {
    const { container } = render(
      <AskWell
        agent="Codex"
        question="Run the migration?"
        value=""
        onChange={() => undefined}
        onAnswer={() => undefined}
        egress={{ label: "API.OPENAI.COM", scope: "cloud" }}
      />,
    );
    expect(container.querySelector(".ask-well-draft")).toBeNull();
    const chip = container.querySelector(".ask-well-answer .gadget-chip-egress");
    expect(chip?.textContent).toBe("API.OPENAI.COM");
  });
});

describe("ObjectList dense: avatar, idle tone, fold join (window grammar kit polish)", () => {
  const rows = [
    { id: "a", kind: "person", name: "Avery Chen", avatar: { initials: "AC", hue: 1 }, cells: { role: "", next: "1:1 Today", owe: "2" }, state: { label: "Quiet", tone: "idle" as const, live: false } },
    { id: "b", kind: "person", name: "Sam Rivera", cells: { role: "Peer", next: "", owe: "" }, state: { label: "Working", tone: "info" as const, live: true } },
  ];
  const columns = [
    { key: "role", word: "Role" },
    { key: "next", word: "Next" },
    { key: "owe", word: "Owe" },
    { key: "state", word: "State" },
  ];
  it("leads an avatar row with the initials disc, not the sprite", () => {
    render(<ObjectList label="People" density="dense" rows={rows} columns={columns} sort={{ key: "name", dir: "asc" }} />);
    const avery = document.querySelector("[data-object-id='a']")!;
    const disc = avery.querySelector(".object-list-avatar")!;
    expect(disc.textContent).toBe("AC");
    expect(disc.getAttribute("data-hue")).toBe("1");
    expect(avery.querySelector(".object-list-open img")).toBeNull();
    expect(avery.hasAttribute("data-avatar")).toBe(true);
    expect(document.querySelector("[data-object-id='b'] .object-list-open img")).not.toBeNull();
  });
  it("draws idle as the grey dot and word, and marks a live state", () => {
    render(<ObjectList label="People" density="dense" rows={rows} columns={columns} sort={{ key: "name", dir: "asc" }} />);
    const idle = document.querySelector("[data-object-id='a'] .object-list-dot-word")!;
    expect(idle.getAttribute("data-tone")).toBe("idle");
    expect(idle.querySelector(".kit-dot")?.getAttribute("data-tone")).toBe("idle");
    expect(idle.hasAttribute("data-live")).toBe(false);
    expect(document.querySelector("[data-object-id='b'] .object-list-dot-word")?.hasAttribute("data-live")).toBe(true);
  });
  it("joins only filled cells: the first filled cell leads the fold, empty ones carry no fold", () => {
    render(<ObjectList label="People" density="dense" rows={rows} columns={columns} sort={{ key: "name", dir: "asc" }} />);
    const fold = (id: string) => [...document.querySelectorAll(`[data-object-id='${id}'] .object-list-cell`)]
      .map((cell) => `${cell.getAttribute("data-col")}:${cell.getAttribute("data-fold") ?? "-"}`);
    expect(fold("a")).toEqual(["role:-", "next:lead", "owe:next"]);
    expect(fold("b")).toEqual(["role:lead", "next:-", "owe:-"]);
  });
});

describe("Toolbar trailingStays + DotWord (window grammar kit polish)", () => {
  it("a staying trailing control marks the band; a search well does not", () => {
    const { rerender } = render(<Toolbar label="Note actions" trailingStays trailing={<span>mic</span>}><Button dense>Done</Button></Toolbar>);
    expect(screen.getByRole("toolbar", { name: "Note actions" }).getAttribute("data-trailing")).toBe("stays");
    rerender(<Toolbar label="Note actions" trailing={<span>search</span>}><Button dense>Done</Button></Toolbar>);
    expect(screen.getByRole("toolbar", { name: "Note actions" }).hasAttribute("data-trailing")).toBe(false);
  });
  it("a state fact is a dot and a word; idle by default", () => {
    render(<><DotWord tone="warn" data-testid="w">No engine for answers</DotWord><DotWord data-testid="i">Quiet</DotWord></>);
    expect(screen.getByTestId("w").textContent).toBe("No engine for answers");
    expect(screen.getByTestId("w").querySelector(".kit-dot")?.getAttribute("data-tone")).toBe("warn");
    expect(screen.getByTestId("i").getAttribute("data-tone")).toBe("idle");
  });
});
