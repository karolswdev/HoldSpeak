// PHILO-14 B1 — the object species (contract.md "The object species").
// Render, keyboard, aria, no text-mode marks, and the 393 fold (jsdom has
// no container queries, so the fold is proven by its rule in objects.css
// plus the fold line in the DOM; the browser contact sheet shows it drawn).
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { Button } from "../../../components/signal/Signal";
import {
  AskWell,
  ConfirmLine,
  DeskIcon,
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
  objectSprite,
  type ObjectListRow,
  type ObjectSort,
} from "..";

// jsdom has no PointerEvent: without it fireEvent.pointer* drops button and
// clientX. A MouseEvent carries both.
if (typeof window.PointerEvent === "undefined")
  (window as unknown as { PointerEvent: typeof MouseEvent }).PointerEvent = MouseEvent;

const CSS = readFileSync(join(__dirname, "../objects/objects.css"), "utf8");
const SURFACE_CSS = readFileSync(join(__dirname, "../surface.css"), "utf8");

/** The text-mode selection marks the owner forbade ("[ ]" in the copy). */
const noTextMarks = (root: HTMLElement) => {
  expect(root.textContent ?? "").not.toMatch(/\[\s?\]|\[x\]/i);
};

/** Every verb is the library Button (UX-CANON A.1). */
const allLibraryButtons = (root: HTMLElement) => {
  for (const button of root.querySelectorAll("button"))
    expect(button.className).toMatch(/\bbtn\b|btn--chrome/);
};

/** The 393 rule of a species lives under the `surface` container query. */
const foldsAt393 = (selector: string) => {
  const blocks = CSS.split("@container surface (max-width: 520px)").slice(1);
  expect(blocks.some((block) => block.includes(selector))).toBe(true);
  expect(CSS).not.toMatch(/@media[^{]*max-width/);
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
    const icon = screen.getByRole("button", { name: "Payments ledger cutover, PROJECT, 3 need you" });
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
    expect(CSS).toMatch(/\.desk-icon\[data-selected="true"\] \.desk-icon-name \{\s*background: var\(--wb-paper\);\s*color: var\(--wb-ink\);/);
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

  it("the name wraps to two lines then ellipsizes", () => {
    expect(CSS).toMatch(/\.desk-icon-name \{[^}]*-webkit-line-clamp: 2;[^}]*text-overflow: ellipsis;/);
  });
});

describe("IconGrid", () => {
  it("is a named group; arrows walk the icons; a press on the glass clears", () => {
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
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(document.activeElement).toBe(second);
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

  it("four columns at 393", () => foldsAt393(".desk-icon-grid {\n    grid-template-columns: repeat(4"));
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
    expect(lamp?.textContent).toBe("CLAUDE CODE ASKS");
  });

  it("393: Kind and When fold under the name; rows keep 44 px; sort gadgets 44 px", () => {
    render(<ListHost />);
    const fold = screen.getByRole("grid").querySelector('[data-object-id="r3"] .object-list-fold');
    expect(fold?.textContent).toBe("NOTEOCT 5");
    foldsAt393(".object-list-cell {\n    display: none;");
    foldsAt393(".object-list-fold {\n    display: flex;");
    foldsAt393(".object-list-sort {\n    min-height: 44px;");
    expect(CSS).toMatch(/\.object-list-row \{[^}]*min-height: 44px;/);
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
    expect(screen.getByText("ACTION ITEM")).toBeInTheDocument();
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
    foldsAt393(".lane-station-sub {\n    display: none;");
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
    expect(screen.getByText("CLAUDE CODE ASKS · 6 MIN")).toBeInTheDocument();
    // The field is the StringGadget (its mic draws where the browser can listen).
    expect(container.querySelector(".ask-well-answer > .gadget-string")).not.toBeNull();
    const field = screen.getByRole("textbox", { name: "Answer" });
    await userEvent.click(screen.getByRole("button", { name: "Answer" }));
    expect(onAnswer).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(field);
    await userEvent.type(field, "Jordan{Enter}");
    expect(onAnswer).toHaveBeenCalledWith("Jordan");
    await userEvent.click(screen.getByRole("button", { name: "Use draft" }));
    expect(onUseDraft).toHaveBeenCalledWith("Jordan owns it. Avery reviews.");
    await userEvent.click(screen.getByRole("button", { name: "Answer" }));
    expect(onAnswer).toHaveBeenLastCalledWith("Jordan owns it. Avery reviews.");
    expect(screen.getByText("API.ANTHROPIC.COM")).toBeInTheDocument();
    await a11y(container);
  });
});

describe("PRCard + FilesChanged", () => {
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
    expect(within(card).getByText("CHECKS 6 OF 7")).toBeInTheDocument();
    expect(within(card).getByText("1 RUNNING")).toBeInTheDocument();
    expect(card.textContent).toContain("REVIEW NONE YET");
    expect(card.textContent).toContain("hs/write-the-rollback-runbook → main");
  });

  it("no counters of zero: no RUNNING lamp at zero, no +0 / −0", () => {
    render(
      <>
        <PRCard number={1} title="t" checks={{ passed: 7, total: 7, running: 0 }} />
        <FilesChanged files={[{ path: "a.py", added: 3, removed: 1 }, { path: "b.md", added: 84, removed: 0 }]} />
      </>,
    );
    expect(screen.queryByText(/RUNNING/)).toBeNull();
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
        fact="CLAUDE CODE · YOLO · hs/write-the-cutover-comms"
        onBrief={onBrief}
        onCancel={onCancel}
        onHand={onHand}
      />,
    );
    const group = screen.getByRole("group", { name: "Hand: Write the cutover comms" });
    expect(within(group).getByText("CLAUDE CODE · YOLO · hs/write-the-cutover-comms")).toBeInTheDocument();
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
    expect(within(row).getByText("ASKS · 6 MIN")).toBeInTheDocument();
    expect(within(row).getAllByRole("button").map((b) => b.textContent)).toEqual(["Open", "Answer"]);
    noTextMarks(container);
    foldsAt393(".needs-row-verbs {\n    grid-column: 1 / -1;");
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

describe("the bevel grammar", () => {
  it("raised for a control, sunken for a well, flat for read text, from --bevel-* tokens", () => {
    expect(SURFACE_CSS).toMatch(/\.bevel-raised \{\s*box-shadow: var\(--bevel-raised\);/);
    expect(SURFACE_CSS).toMatch(/\.bevel-sunken \{\s*box-shadow: var\(--bevel-sunken\);/);
    expect(SURFACE_CSS).toMatch(/\.bevel-flat \{\s*box-shadow: none;/);
    // The species wear it: the ask well and PR card raised, the confirm well sunken.
    expect(CSS).toMatch(/\.ask-well \{[^}]*box-shadow: var\(--bevel-raised\);/);
    expect(CSS).toMatch(/\.pr-card \{[^}]*box-shadow: var\(--bevel-raised\);/);
    expect(CSS).toMatch(/\.confirm-line \{[^}]*box-shadow: var\(--bevel-sunken\);/);
  });

  it("no raw colours in the object species", () => {
    expect(CSS).not.toMatch(/#[0-9a-f]{3,8}\b|rgba?\(/i);
  });
});
