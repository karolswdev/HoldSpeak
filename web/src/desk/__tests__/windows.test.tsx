// HS-95-02 — OS-grade windows: the one container, the lifecycle store, the
// persistence slot (including the Phase 93 flat-shape tolerance), and the
// minimized tray. jsdom hosts the DOM; physics gestures stay pinned by the
// Playwright walk.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DeskWindowFrame, MinimizedTray } from "../components/DeskWindow";
import { useDesk } from "../store";

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
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
  it("hosts arbitrary children under one head with the three verbs", () => {
    render(<Host />);
    expect(screen.getByText("window content")).toBeInTheDocument();
    expect(screen.getByRole("dialog", { name: "Test window" })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Minimize Test window" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Maximize Test window" }),
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

  it("minimize parks the window (mounted but hidden) and the tray restores it", () => {
    render(
      <>
        <Host />
        <MinimizedTray />
      </>,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Minimize Test window" }),
    );
    expect(useDesk.getState().panelMin).toEqual(["t1"]);
    // display:none removes it from the a11y tree; the mount itself parks.
    const dialog = document.querySelector(
      '[aria-label="Test window"][role="dialog"]',
    ) as HTMLElement;
    expect(dialog).toBeTruthy();
    expect(dialog.style.display).toBe("none");
    expect(screen.getByText("window content")).toBeInTheDocument();
    // The tray names it and restores it.
    const chip = screen.getByRole("button", { name: /Test window/ });
    fireEvent.click(chip);
    expect(useDesk.getState().panelMin).toEqual([]);
    expect(dialog.style.display).not.toBe("none");
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
    fireEvent.click(screen.getByRole("button", { name: "Minimize Heavy" }));
    expect(screen.queryByText("heavy content")).toBeNull();
  });

  it("maximize toggles the full-stage form and restore returns the rect", () => {
    render(<Host />);
    fireEvent.click(
      screen.getByRole("button", { name: "Maximize Test window" }),
    );
    expect(useDesk.getState().panelMax).toEqual(["t1"]);
    const dialog = screen.getByRole("dialog", { name: "Test window" });
    expect(dialog.className).toContain("is-max");
    fireEvent.click(screen.getByRole("button", { name: "Restore Test window" }));
    expect(useDesk.getState().panelMax).toEqual([]);
    expect(dialog.className).not.toContain("is-max");
  });

  it("windows coexist and never trap focus (no aria-modal)", () => {
    render(
      <>
        <Host />
        <DeskWindowFrame id="t3" title="Second" open onClose={() => {}}>
          <p>second content</p>
        </DeskWindowFrame>
      </>,
    );
    const dialogs = screen.getAllByRole("dialog");
    expect(dialogs).toHaveLength(2);
    for (const d of dialogs)
      expect(d.getAttribute("aria-modal")).toBe("false");
  });
});

describe("the lifecycle store + hs.desk.panels persistence", () => {
  it("round-trips rects + min + max through one slot", () => {
    useDesk.getState().setPanelRect("a", { x: 10, y: 20, w: 400, h: 300 }, true);
    useDesk.getState().minimizePanel("a");
    useDesk.getState().toggleMaximizePanel("b");
    const raw = JSON.parse(localStorage.getItem("hs.desk.panels") || "{}");
    expect(raw.rects.a).toEqual({ x: 10, y: 20, w: 400, h: 300 });
    expect(raw.min).toEqual(["a"]);
    expect(raw.max).toEqual(["b"]);
  });

  it("restore and un-maximize persist their removals", () => {
    useDesk.getState().minimizePanel("a");
    useDesk.getState().restorePanel("a");
    useDesk.getState().toggleMaximizePanel("b");
    useDesk.getState().toggleMaximizePanel("b");
    const raw = JSON.parse(localStorage.getItem("hs.desk.panels") || "{}");
    expect(raw.min).toEqual([]);
    expect(raw.max).toEqual([]);
  });

  it("focus order still raises the last-touched window", () => {
    useDesk.getState().focusPanel("a");
    useDesk.getState().focusPanel("b");
    useDesk.getState().focusPanel("a");
    expect(useDesk.getState().panelOrder).toEqual(["b", "a"]);
  });

  it("accepts the Phase 93 flat rect shape on load", async () => {
    localStorage.setItem(
      "hs.desk.panels",
      JSON.stringify({ legacy: { x: 1, y: 2, w: 300, h: 200 } }),
    );
    vi.resetModules();
    const fresh = await import("../store");
    expect(fresh.useDesk.getState().panelRects.legacy).toEqual({
      x: 1,
      y: 2,
      w: 300,
      h: 200,
    });
    expect(fresh.useDesk.getState().panelMin).toEqual([]);
  });
});
