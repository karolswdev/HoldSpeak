/** HS-111-07 — the WorkMenu species v2: portal to the body (the z
 * fix), separators, key column, type-ahead, one-deep submenus. */
import { fireEvent, render, screen } from "@testing-library/react";
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
      keycap: "⌘1",
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

  it("renders separator, key column, and the ghost reason", () => {
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
    expect(screen.getByText("⌘1")).toBeInTheDocument();
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
