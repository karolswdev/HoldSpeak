// HS-95-02 — OS-grade windows: the one container, the lifecycle store, the
// persistence slot (including the Phase 93 flat-shape tolerance), and the
// minimized tray. jsdom hosts the DOM; physics gestures stay pinned by the
// Playwright walk.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DeskWindowFrame, Dock } from "../components/DeskWindow";
import { useDesk } from "../store";

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    windowsById: {},
    zoneWindows: [],
    zoneViewPrefs: {},
  });
});

function Host({ open = true, onClose = () => {} }) {
  return (
    <DeskWindowFrame
      id="t1"
      title="Test window"
      icon={<span>◈</span>}
      open={open}
      onClose={onClose}
    >
      <p>window content</p>
    </DeskWindowFrame>
  );
}

describe("DeskWindowFrame (the one chrome)", () => {
  it("hosts arbitrary children under one head with the Workbench gadget set (PHILO-13-11)", () => {
    render(<Host />);
    expect(screen.getByText("window content")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Test window" })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Iconify Test window" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Zoom Test window" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Close Test window" }),
    ).toBeTruthy();
  });

  it("close is a callback, never a store mutation (open is the feature's)", () => {
    const onClose = vi.fn();
    render(<Host onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Close Test window" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("minimize parks the window (mounted but hidden) and its dock seat restores it", () => {
    // PHILO-16 (A1) §5: seated windows live in the dock, on their
    // application's tile (the window chips are parked). The Intelligence
    // application's window is `pullout:intelligence:desk`.
    const { container } = render(
      <>
        <DeskWindowFrame
          id="pullout:intelligence:desk"
          title="Test window"
          open
          onClose={() => {}}
        >
          <p>window content</p>
        </DeskWindowFrame>
        <Dock />
      </>,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Iconify Test window" }),
    );
    expect(useDesk.getState().panelMin).toEqual(["pullout:intelligence:desk"]);
    // display:none removes it from the a11y tree; the mount itself parks.
    const shell = container.querySelector(
      '[aria-label="Test window"][role="region"]',
    ) as HTMLElement;
    expect(shell).toBeTruthy();
    expect(shell.style.display).toBe("none");
    expect(screen.getByText("window content")).toBeInTheDocument();
    // The dock names it on its tile, lights the seat and restores it.
    const tile = screen.getByRole("button", { name: /^Intelligence.*, iconified$/ });
    expect(tile.querySelector(".desk-dock-seat")).toBeTruthy();
    expect(tile.classList.contains("is-seated")).toBe(true);
    fireEvent.click(tile);
    expect(useDesk.getState().panelMin).toEqual([]);
    expect(shell.style.display).not.toBe("none");
  });

  it("a seated window with no application tile gets its own seat tile; a press restores it and the tile goes (PHILO-16 A1 §5)", () => {
    const { container } = render(
      <>
        <DeskWindowFrame
          id="pullout:thread:t9"
          title="Ledger questions"
          kindWord="Thread"
          icon={<img src="/thread.png" alt="" />}
          open
          onClose={() => {}}
        >
          <p>thread body</p>
        </DeskWindowFrame>
        <Dock />
      </>,
    );
    const dock = screen.getByRole("toolbar", { name: "Dock" });
    // open, the window is on the desk: no seat tile
    expect(dock.querySelector(".desk-dock-seat-tile")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Iconify Ledger questions" }));
    expect(useDesk.getState().panelMin).toEqual(["pullout:thread:t9"]);
    // seated: one tile with its name, its title-bar icon and the seat lamp
    const tile = screen.getByRole("button", { name: "Ledger questions, iconified" });
    expect(tile.classList.contains("desk-dock-seat-tile")).toBe(true);
    expect(tile.querySelector(".desk-dock-label")?.textContent).toBe("Ledger questions");
    expect(tile.querySelector(".desk-dock-seat-icon img")?.getAttribute("src")).toBe("/thread.png");
    expect(tile.querySelector(".desk-dock-seat")).toBeTruthy();
    expect(dock.querySelectorAll(".desk-dock-seat-tile")).toHaveLength(1);
    // the press restores it to the front; the tile goes
    fireEvent.click(tile);
    expect(useDesk.getState().panelMin).toEqual([]);
    expect(useDesk.getState().panelOrder.at(-1)).toBe("pullout:thread:t9");
    const shell = container.querySelector('[role="region"][aria-label="Ledger questions"]') as HTMLElement;
    expect(shell.style.display).not.toBe("none");
    expect(dock.querySelector(".desk-dock-seat-tile")).toBeNull();
  });

  it("unmountOnMinimize opts heavy content out of a parked mount", () => {
    render(
      <DeskWindowFrame
        id="t2"
        title="Heavy"
        open
        onClose={() => {}}
        unmountOnMinimize
      >
        <p>heavy content</p>
      </DeskWindowFrame>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Iconify Heavy" }));
    expect(screen.queryByText("heavy content")).toBeNull();
  });

  it("maximize toggles the full-stage form and restore returns the rect", () => {
    render(<Host />);
    fireEvent.click(
      screen.getByRole("button", { name: "Zoom Test window" }),
    );
    expect(useDesk.getState().panelMax).toEqual(["t1"]);
    const shell = screen.getByRole("region", { name: "Test window" });
    expect(shell.className).toContain("is-max");
    // PHILO-13-11: zoom is one gadget that toggles; it reads pressed while zoomed.
    const zoom = screen.getByRole("button", { name: "Zoom Test window" });
    expect(zoom.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(zoom);
    expect(useDesk.getState().panelMax).toEqual([]);
    expect(shell.className).not.toContain("is-max");
  });

  it("windows coexist as regions and never trap focus (no modal roles)", () => {
    render(
      <>
        <Host />
        <DeskWindowFrame id="t3" title="Second" open onClose={() => {}}>
          <p>second content</p>
        </DeskWindowFrame>
      </>,
    );
    // Both windows live side by side; neither claims a takeover role
    // (the Phase 73 mechanical lock forbids modal roles on the desk).
    expect(screen.getByRole("region", { name: "Test window" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Second" })).toBeTruthy();
  });
});

describe("focus depth (HS-97-04)", () => {
  it("exactly the front window wears is-front; raising moves it", () => {
    render(
      <>
        <DeskWindowFrame id="fa" title="Alpha" open onClose={() => {}}>
          <p>a</p>
        </DeskWindowFrame>
        <DeskWindowFrame id="fb" title="Beta" open onClose={() => {}}>
          <p>b</p>
        </DeskWindowFrame>
      </>,
    );
    const alpha = screen.getByRole("region", { name: "Alpha" });
    const beta = screen.getByRole("region", { name: "Beta" });
    expect(beta.className).toContain("is-front");
    expect(alpha.className).not.toContain("is-front");
    fireEvent.pointerDown(alpha);
    expect(alpha.className).toContain("is-front");
    expect(beta.className).not.toContain("is-front");
  });

  it("a minimized front hands depth to the next window", () => {
    render(
      <>
        <DeskWindowFrame id="fa" title="Alpha" open onClose={() => {}}>
          <p>a</p>
        </DeskWindowFrame>
        <DeskWindowFrame id="fb" title="Beta" open onClose={() => {}}>
          <p>b</p>
        </DeskWindowFrame>
      </>,
    );
    act(() => useDesk.getState().minimizePanel("fb"));
    const alpha = screen.getByRole("region", { name: "Alpha" });
    expect(alpha.className).toContain("is-front");
  });
});

describe("HS-103-01: Reset Layout clears an open window's rect too", () => {
  it("an open, arranged window loses its inline geometry on reset (no stale rect survives)", () => {
    render(<Host />);
    act(() => {
      useDesk.getState().setPanelRect("t1", { x: 10, y: 20, w: 400, h: 300 }, true);
    });
    const shell = screen.getByRole("region", { name: "Test window" });
    expect(shell.style.top).toBe("20px");
    expect(shell.style.left).toBe("10px");
    act(() => {
      useDesk.getState().resetLayout();
    });
    expect(shell.style.top).toBe("");
    expect(shell.style.left).toBe("");
    expect(useDesk.getState().panelRects.t1).toBeUndefined();
  });
});

describe("the lifecycle store + versioned workspace persistence", () => {
  // PHILO-13-07 (B2) supersedes HS-97-03's session-only minimize.
  it("round-trips rects + order + max + min through one slot (PHILO-13-07 B2)", () => {
    useDesk.getState().setPanelRect("a", { x: 10, y: 20, w: 400, h: 300 }, true);
    useDesk.getState().minimizePanel("a");
    useDesk.getState().toggleMaximizePanel("b");
    const raw = JSON.parse(localStorage.getItem("hs.desk.workspace.v1") || "{}");
    expect(raw.rects).toBeUndefined();
    expect(raw.panel.rects.a).toEqual({ x: 10, y: 20, w: 400, h: 300 });
    expect(raw.panel.min).toEqual(["a"]);
    expect(raw.panel.order).toEqual(["b"]);
    expect(raw.panel.max).toEqual(["b"]);
    expect(useDesk.getState().panelMin).toEqual(["a"]);
  });

  it("restore and un-maximize persist their removals", () => {
    useDesk.getState().minimizePanel("a");
    useDesk.getState().restorePanel("a");
    useDesk.getState().toggleMaximizePanel("b");
    useDesk.getState().toggleMaximizePanel("b");
    const raw = JSON.parse(localStorage.getItem("hs.desk.workspace.v1") || "{}");
    expect(raw.panel.min).toEqual([]);
    expect(raw.panel.max).toEqual([]);
  });

  it("focus order still raises the last-touched window", () => {
    useDesk.getState().focusPanel("a");
    useDesk.getState().focusPanel("b");
    useDesk.getState().focusPanel("a");
    expect(useDesk.getState().panelOrder).toEqual(["b", "a"]);
  });

  it("hard-cuts the retired Phase 93 panel slot", async () => {
    localStorage.setItem(
      "hs.desk.panels",
      JSON.stringify({ legacy: { x: 1, y: 2, w: 300, h: 200 } }),
    );
    vi.resetModules();
    const fresh = await import("../store");
    expect(fresh.useDesk.getState().panelRects.legacy).toBeUndefined();
    expect(fresh.useDesk.getState().panelMin).toEqual([]);
  });
});

describe("HS-99-02: the title bar owns a right-click menu", () => {
  it("opens on head contextmenu, executes verbs, closes on Escape", () => {
    const onClose = vi.fn();
    render(
      <DeskWindowFrame id="hm" title="Menu test" open onClose={onClose}>
        <p>body</p>
      </DeskWindowFrame>,
    );
    const head = screen
      .getByRole("region", { name: "Menu test" })
      .querySelector("header") as HTMLElement;
    fireEvent.contextMenu(head);
    const menu = screen.getByRole("menu", { name: "Menu test window menu" });
    expect(menu).toBeInTheDocument();
    // The first Escape (bubbling through the SHELL, as in a real
    // browser) closes the MENU only — the window must survive.
    fireEvent.keyDown(screen.getByRole("region", { name: "Menu test" }), {
      key: "Escape",
    });
    expect(
      screen.queryByRole("menu", { name: "Menu test window menu" }),
    ).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.contextMenu(head);
    fireEvent.click(screen.getByRole("menuitem", { name: /Close/ }));
    expect(onClose).toHaveBeenCalled();
  });
});

// PHILO-16 (A1) §5: the window chips are parked (Dock.tsx NUB_CHIPS); the
// right-click menu rides the application tile that seats the window.
describe("HS-99-04: the dock chip owns a right-click menu", () => {
  it("opens on chip contextmenu and executes Close", () => {
    const onClose = vi.fn();
    render(
      <>
        <DeskWindowFrame id="pullout:intelligence:desk" title="Chip menu" open onClose={onClose}>
          <p>body</p>
        </DeskWindowFrame>
        <Dock />
      </>,
    );
    fireEvent.contextMenu(screen.getByRole("button", { name: /^Intelligence/ }));
    const menu = screen.getByRole("menu", { name: "Intelligence dock menu" });
    expect(menu).toBeInTheDocument();
    fireEvent.click(screen.getByRole("menuitem", { name: /Close/ }));
    expect(onClose).toHaveBeenCalled();
  });

  it("dock chip menu entries have VerbGlyph glyphs", () => {
    render(
      <>
        <DeskWindowFrame id="pullout:intelligence:desk" title="Glyph dock" open onClose={() => {}}>
          <p>body</p>
        </DeskWindowFrame>
        <Dock />
      </>,
    );
    fireEvent.contextMenu(screen.getByRole("button", { name: /^Intelligence/ }));
    const menu = screen.getByRole("menu", { name: "Intelligence dock menu" });
    // Both items must carry an SVG glyph (the lane law).
    const items = menu.querySelectorAll("[role='menuitem']");
    expect(items.length).toBe(2);
    for (const item of items) {
      expect(item.querySelector("svg")).toBeTruthy();
    }
  });

  it("dock chip menu shows keycap wells from the registry", () => {
    render(
      <>
        <DeskWindowFrame id="pullout:intelligence:desk" title="Keycap dock" open onClose={() => {}}>
          <p>body</p>
        </DeskWindowFrame>
        <Dock />
      </>,
    );
    fireEvent.contextMenu(screen.getByRole("button", { name: /^Intelligence/ }));
    const menu = screen.getByRole("menu", { name: "Intelligence dock menu" });
    // At least one keycap well should be present (window.minimize has key ⌘M).
    const wells = menu.querySelectorAll(".desk-menu-well");
    expect(wells.length).toBeGreaterThan(0);
  });
});

describe("HS-148-04: head menu scopes to its window, not the front", () => {
  it("back window's head Close closes THAT window; front stays", () => {
    const closeAlpha = vi.fn();
    const closeBeta = vi.fn();
    render(
      <>
        <DeskWindowFrame id="sc-a" title="Alpha" open onClose={closeAlpha}>
          <p>a</p>
        </DeskWindowFrame>
        <DeskWindowFrame id="sc-b" title="Beta" open onClose={closeBeta}>
          <p>b</p>
        </DeskWindowFrame>
      </>,
    );
    // Beta is the front window (rendered last). Open Alpha's head menu.
    const alphaHead = screen
      .getByRole("region", { name: "Alpha" })
      .querySelector("header") as HTMLElement;
    fireEvent.contextMenu(alphaHead);
    const menu = screen.getByRole("menu", { name: "Alpha window menu" });
    expect(menu).toBeInTheDocument();
    fireEvent.click(screen.getByRole("menuitem", { name: /Close/ }));
    // Alpha's close was called, Beta's was not.
    expect(closeAlpha).toHaveBeenCalledTimes(1);
    expect(closeBeta).not.toHaveBeenCalled();
    // Beta is still in the document.
    expect(screen.getByRole("region", { name: "Beta" })).toBeTruthy();
  });
});
