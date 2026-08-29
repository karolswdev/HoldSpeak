/** HS-111-07 — the WorkMenu species v2: portal to the body (the z
 * fix), separators, key column, type-ahead, one-deep submenus.
 * HS-148-01 — the grammar core: stipple ghosting, drawn keycap wells,
 * checkable lane, lane law, ghost-reason collapse, submenu indicator. */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";

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

  it("renders separator, drawn keycap wells, and the ghost reason", () => {
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
    const ghost = screen.getByRole("menuitem", { name: /Arrange desk/ });
    expect(ghost).toHaveAttribute("aria-disabled", "true");
    expect(ghost).toHaveTextContent("Nothing moved");
  });

  it("a ghosted item refuses to run; a live one runs and closes", () => {
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
    fireEvent.click(screen.getByRole("menuitem", { name: /Arrange desk/ }));
    expect(onClose).not.toHaveBeenCalled();
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
  it("ghosted items carry the is-ghost class for stipple", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          {
            type: "item",
            id: "g",
            label: "Ghost",
            ghost: "reason",
            onSelect: vi.fn(),
          },
        ]}
        onClose={() => {}}
      />,
    );
    const btn = screen.getByRole("menuitem", { name: /Ghost/ });
    expect(btn.classList.contains("is-ghost")).toBe(true);
  });

  it("keycap visible on ghosted rows (stippled with the row)", () => {
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={[
          {
            type: "item",
            id: "g",
            label: "Ghost",
            keycap: "⌘G",
            ghost: "reason",
            onSelect: vi.fn(),
          },
        ]}
        onClose={() => {}}
      />,
    );
    const btn = screen.getByRole("menuitem", { name: /Ghost/ });
    // Keycap wells must exist even on ghosted rows.
    const wells = btn.querySelectorAll(".desk-menu-well");
    expect(wells.length).toBeGreaterThan(0);
  });

  it("ghost-reason collapse: uniform reasons render one footer", () => {
    const reason = "Select an object";
    const ghostEntries: WorkMenuEntry[] = Array.from({ length: 4 }, (_, i) => ({
      type: "item" as const,
      id: `g${i}`,
      label: `Verb ${i}`,
      ghost: reason,
      onSelect: vi.fn(),
    }));
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={ghostEntries}
        onClose={() => {}}
      />,
    );
    // The collapsed footer is present.
    const footer = document.querySelector(".desk-menu-ghost-hint");
    expect(footer).toBeTruthy();
    expect(footer!.textContent).toBe(reason);
    // Per-row reasons are suppressed — no <small> tags.
    const smalls = document.querySelectorAll(".desk-menu-list .quiet");
    expect(smalls.length).toBe(0);
  });

  it("ghost-reason collapse: mixed reasons below threshold keep per-row display", () => {
    const ghostEntries: WorkMenuEntry[] = [
      {
        type: "item",
        id: "g1",
        label: "V1",
        ghost: "Reason A",
        onSelect: vi.fn(),
      },
      {
        type: "item",
        id: "g2",
        label: "V2",
        ghost: "Reason B",
        onSelect: vi.fn(),
      },
      {
        type: "item",
        id: "g3",
        label: "V3",
        ghost: "Reason A",
        onSelect: vi.fn(),
      },
    ];
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={ghostEntries}
        onClose={() => {}}
      />,
    );
    // No collapsed footer (neither reason hits 3).
    const footer = document.querySelector(".desk-menu-ghost-hint");
    expect(footer).toBeNull();
    // Per-row reasons shown on all 3.
    const smalls = document.querySelectorAll(".desk-menu-list .quiet");
    expect(smalls.length).toBe(3);
  });

  it("ghost-reason collapse: majority collapses, minority stays inline", () => {
    // 7x "Select an object" + 1x "Select a Project" + 1 sep
    const ghostEntries: WorkMenuEntry[] = [
      ...Array.from({ length: 7 }, (_, i) => ({
        type: "item" as const,
        id: `obj${i}`,
        label: `Verb ${i}`,
        ghost: "Select an object",
        onSelect: vi.fn(),
      })),
      { type: "sep" as const },
      {
        type: "item" as const,
        id: "proj",
        label: "Ask this project",
        ghost: "Select a Project",
        onSelect: vi.fn(),
      },
    ];
    render(
      <WorkMenu
        label="T"
        x={0}
        y={0}
        entries={ghostEntries}
        onClose={() => {}}
      />,
    );
    // The majority reason collapses to a footer.
    const footer = document.querySelector(".desk-menu-ghost-hint");
    expect(footer).toBeTruthy();
    expect(footer!.textContent).toBe("Select an object");
    // The minority reason stays inline (1 per-row echo for "Select a Project").
    const smalls = document.querySelectorAll(".desk-menu-list .quiet");
    expect(smalls.length).toBe(1);
    expect(smalls[0].textContent).toContain("Select a Project");
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

  it("autoFocus on open focuses the first item", () => {
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
    expect(document.activeElement).toBe(
      screen.getByRole("menuitem", { name: "First" }),
    );
  });

  it("keyboard nav finds menuitemcheckbox and menuitemradio roles", () => {
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
  });
});
