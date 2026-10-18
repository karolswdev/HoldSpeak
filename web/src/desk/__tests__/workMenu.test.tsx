/** HS-111-07 — the WorkMenu species v2: portal to the body (the z
 * fix), separators, key column, type-ahead, one-deep submenus.
 * HS-148-01 — the grammar core: drawn keycap wells, checkable lane, lane
 * law, submenu indicator. Betterment shell S0 (UX-CANON A.11): a ghosted
 * entry is withheld (the stipple and the ghost-reason footer are gone). */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";

/** Flush the double-rAF focus deferral used by WorkMenu's autoFocus.
 * In jsdom, rAF is a polyfill backed by setTimeout; we use fake timers
 * to tick both frames synchronously so the focus() call lands. */
async function flushAutoFocus() {
  // First rAF tick (outer)
  await act(async () => { vi.advanceTimersByTime(16); });
  // Second rAF tick (inner)
  await act(async () => { vi.advanceTimersByTime(16); });
}

function entries(onNote = vi.fn(), onSpeak = vi.fn()): WorkMenuEntry[] {
  return [
    {
      type: "sub",
      id: "new",
      label: "New",
      entries: [
        { type: "item", id: "n1", label: "New Note", onSelect: onNote },
        { type: "item", id: "n2", label: "New Zone", onSelect: vi.fn() },
      ],
    },
    { type: "sep" },
    {
      type: "item",
      id: "speak",
      label: "Speak",
      keycap: "⌘⇧1",
      onSelect: onSpeak,
    },
    {
      type: "item",
      id: "ghosted",
      label: "Arrange desk",
      ghost: "Nothing moved",
      onSelect: vi.fn(),
    },
  ];
}

describe("WorkMenu (HS-111-07 species v2)", () => {
  it("portals to the document body — never trapped in a chrome stacking context", () => {
    const { container } = render(
      <div className="host">
        <WorkMenu
          label="Test menu"
          x={10}
          y={10}
          entries={entries()}
          onClose={() => {}}
        />
      </div>,
    );
    const menu = screen.getByRole("menu", { name: "Test menu" });
    expect(container.contains(menu)).toBe(false);
    expect(document.body.contains(menu)).toBe(true);
  });

  it("renders separator and drawn keycap wells; the ghosted item is withheld", () => {
    render(
      <WorkMenu
        label="Test menu"
        x={10}
        y={10}
        entries={entries()}
        onClose={() => {}}
      />,
    );
    expect(screen.getByRole("separator")).toBeInTheDocument();
    // HS-148-01: keycap wells — modifier and key each get a well.
    const keycaps = document.querySelector(".desk-menu-keycaps");
    expect(keycaps).toBeTruthy();
    const wells = keycaps!.querySelectorAll(".desk-menu-well");
    expect(wells.length).toBe(3); // ⌘, ⇧, 1
    expect(screen.queryByRole("menuitem", { name: /Arrange desk/ })).toBeNull();
    expect(document.body.textContent).not.toContain("Nothing moved");
  });

  it("a live item runs and closes", () => {
    const onSpeak = vi.fn();
    const onClose = vi.fn();
    render(
      <WorkMenu
        label="Test menu"
        x={10}
        y={10}
        entries={entries(vi.fn(), onSpeak)}
        onClose={onClose}
      />,
    );
    fireEvent.click(screen.getByRole("menuitem", { name: /Speak/ }));
    expect(onSpeak).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  it("opens the one-deep submenu on ArrowRight and runs its verbs", () => {
    const onNote = vi.fn();
    render(
      <WorkMenu
        label="Test menu"
        x={10}
        y={10}
        entries={entries(onNote)}
        onClose={() => {}}
      />,
    );
    const sub = screen.getByRole("menuitem", { name: "New" });
    fireEvent.keyDown(sub, { key: "ArrowRight" });
    const submenu = screen.getByRole("menu", { name: "New submenu" });
    expect(submenu).toBeInTheDocument();
    fireEvent.click(screen.getByRole("menuitem", { name: "New Note" }));
    expect(onNote).toHaveBeenCalled();
  });

  it("type-ahead moves focus to the first matching item", () => {
    render(
      <WorkMenu
        label="Test menu"
        x={10}
        y={10}
        entries={entries()}
        onClose={() => {}}
        autoFocus
      />,
    );
    const menu = screen.getByRole("menu", { name: "Test menu" });
    fireEvent.keyDown(menu, { key: "s" });
    expect(document.activeElement).toBe(
      screen.getByRole("menuitem", { name: /Speak/ }),
    );
  });
});

describe("WorkMenu grammar (HS-148-01)", () => {
  // Betterment shell S0 (UX-CANON A.11, "withhold, never ghost").
  it("withholds every ghosted row; no stipple, no reason footer", () => {
    const ghostEntries: WorkMenuEntry[] = [
      ...Array.from({ length: 4 }, (_, i) => ({
        type: "item" as const, id: `g${i}`, label: `Verb ${i}`, keycap: "⌘G",
        ghost: "Select an object", onSelect: vi.fn(),
      })),
      { type: "item", id: "live", label: "Open", onSelect: vi.fn() },
    ];
    render(<WorkMenu label="T" x={0} y={0} entries={ghostEntries} onClose={() => {}} />);
    const menu = screen.getByRole("menu", { name: "T" });
    expect(within(menu).getAllByRole("menuitem").map((b) => b.textContent)).toEqual(["Open"]);
    expect(document.querySelector(".is-ghost, .desk-menu-ghost-hint, [aria-disabled='true']")).toBeNull();
    expect(menu.textContent).not.toContain("Select an object");
  });

  it("drops a submenu left empty and never leads, trails or doubles a separator", () => {
    const dead = (id: string): WorkMenuEntry => ({ type: "item", id, label: id, ghost: "no", onSelect: vi.fn() });
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          dead("a"),
          { type: "sep", id: "s1" },
          { type: "item", id: "live", label: "Live", onSelect: vi.fn() },
          { type: "sep", id: "s2" },
          dead("b"),
          { type: "sep", id: "s3" },
          { type: "sub", id: "sub", label: "Empty", entries: [dead("c")] },
          { type: "sep", id: "s4" },
        ]}
        onClose={() => {}}
      />,
    );
    const menu = screen.getByRole("menu", { name: "T" });
    expect(within(menu).getAllByRole("menuitem").map((b) => b.textContent)).toEqual(["Live"]);
    expect(within(menu).queryAllByRole("separator")).toHaveLength(0);
  });

  it("a note entry is one plain line, not a verb", () => {
    render(<WorkMenu label="T" x={0} y={0} entries={[{ type: "note", id: "none", label: "No windows open" }]} onClose={() => {}} />);
    const menu = screen.getByRole("menu", { name: "T" });
    expect(menu.textContent).toBe("No windows open");
    expect(within(menu).queryAllByRole("menuitem")).toHaveLength(0);
  });

  it("checkable item: boolean checked renders menuitemcheckbox + check mark", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          {
            type: "item",
            id: "toggle",
            label: "List View",
            checked: true,
            onSelect: vi.fn(),
          },
        ]}
        onClose={() => {}}
      />,
    );
    const item = screen.getByRole("menuitemcheckbox", { name: /List View/ });
    expect(item).toHaveAttribute("aria-checked", "true");
    // VerbGlyph check SVG is present.
    const svg = item.querySelector("svg");
    expect(svg).toBeTruthy();
  });

  it("checkable item: unchecked boolean renders menuitemcheckbox with aria-checked false", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          {
            type: "item",
            id: "toggle",
            label: "List View",
            checked: false,
            onSelect: vi.fn(),
          },
        ]}
        onClose={() => {}}
      />,
    );
    const item = screen.getByRole("menuitemcheckbox", { name: /List View/ });
    expect(item).toHaveAttribute("aria-checked", "false");
    // No check mark when unchecked — just a spacer.
    const svg = item.querySelector("svg");
    expect(svg).toBeNull();
  });

  it("checkable item: exclusive renders menuitemradio with circle-dot", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          {
            type: "item",
            id: "radio",
            label: "Icons",
            checked: "exclusive",
            onSelect: vi.fn(),
          },
        ]}
        onClose={() => {}}
      />,
    );
    const item = screen.getByRole("menuitemradio", { name: /Icons/ });
    expect(item).toHaveAttribute("aria-checked", "true");
    // Circle-dot SVG with filled inner circle.
    const circles = item.querySelectorAll("circle");
    expect(circles.length).toBe(2);
  });

  it("lane law: every row reserves the lane when any entry has a glyph", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          {
            type: "item",
            id: "a",
            label: "With Glyph",
            glyph: "⚙",
            onSelect: vi.fn(),
          },
          {
            type: "item",
            id: "b",
            label: "No Glyph",
            onSelect: vi.fn(),
          },
        ]}
        onClose={() => {}}
      />,
    );
    const menu = screen.getByRole("menu", { name: "T" });
    const glyphs = menu.querySelectorAll(".desk-menu-glyph");
    // Both rows have a glyph lane element (one with content, one spacer).
    expect(glyphs.length).toBe(2);
  });

  it("lane law: no lane reserved when no entry has a glyph or check", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          { type: "item", id: "a", label: "Plain A", onSelect: vi.fn() },
          { type: "item", id: "b", label: "Plain B", onSelect: vi.fn() },
        ]}
        onClose={() => {}}
      />,
    );
    const menu = screen.getByRole("menu", { name: "T" });
    const glyphs = menu.querySelectorAll(".desk-menu-glyph");
    expect(glyphs.length).toBe(0);
  });

  it("submenu indicator renders »", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          {
            type: "sub",
            id: "s",
            label: "Sub",
            entries: [
              { type: "item", id: "s1", label: "S1", onSelect: vi.fn() },
            ],
          },
        ]}
        onClose={() => {}}
      />,
    );
    const submark = document.querySelector(".desk-menu-submark");
    expect(submark).toBeTruthy();
    expect(submark!.textContent).toBe("»");
  });

  it("panel declares data-menu-context attribute", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          { type: "item", id: "a", label: "A", onSelect: vi.fn() },
        ]}
        onClose={() => {}}
        menuContext="launcher"
      />,
    );
    const menu = screen.getByRole("menu", { name: "T" });
    expect(menu.getAttribute("data-menu-context")).toBe("launcher");
  });

  it("panel defaults data-menu-context to verb", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          { type: "item", id: "a", label: "A", onSelect: vi.fn() },
        ]}
        onClose={() => {}}
      />,
    );
    const menu = screen.getByRole("menu", { name: "T" });
    expect(menu.getAttribute("data-menu-context")).toBe("verb");
  });

  it("autoFocus on open focuses the first item", async () => {
    vi.useFakeTimers();
    try {
      render(
        <WorkMenu
          label="T"
          x={0}
          y={0}
          entries={[
            { type: "item", id: "a", label: "First", onSelect: vi.fn() },
            { type: "item", id: "b", label: "Second", onSelect: vi.fn() },
          ]}
          onClose={() => {}}
          autoFocus
        />,
      );
      await flushAutoFocus();
      expect(document.activeElement).toBe(
        screen.getByRole("menuitem", { name: "First" }),
      );
    } finally {
      vi.useRealTimers();
    }
  });

  it("keyboard nav finds menuitemcheckbox and menuitemradio roles", async () => {
    vi.useFakeTimers();
    try {
      render(
        <WorkMenu
          label="T"
          x={0}
          y={0}
          entries={[
            {
              type: "item",
              id: "a",
              label: "Toggle",
              checked: true,
              onSelect: vi.fn(),
            },
            {
              type: "item",
              id: "b",
              label: "Radio",
              checked: "exclusive",
              onSelect: vi.fn(),
            },
            { type: "item", id: "c", label: "Plain", onSelect: vi.fn() },
          ]}
          onClose={() => {}}
          autoFocus
        />,
      );
      await flushAutoFocus();
      // Focus should be on first item (checkbox).
      const toggle = screen.getByRole("menuitemcheckbox", { name: /Toggle/ });
      expect(document.activeElement).toBe(toggle);
      // ArrowDown should move to radio.
      const menu = screen.getByRole("menu", { name: "T" });
      fireEvent.keyDown(menu, { key: "ArrowDown" });
      expect(document.activeElement).toBe(
        screen.getByRole("menuitemradio", { name: /Radio/ }),
      );
      // ArrowDown again to plain.
      fireEvent.keyDown(menu, { key: "ArrowDown" });
      expect(document.activeElement).toBe(
        screen.getByRole("menuitem", { name: /Plain/ }),
      );
    } finally {
      vi.useRealTimers();
    }
  });
});
