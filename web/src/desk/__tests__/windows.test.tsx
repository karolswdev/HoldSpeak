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
    expect(screen.getByRole("region", { name: "Test window" })).toBeTruthy();
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

  it("minimize parks the window (mounted but hidden) and the dock restores it", () => {
    const { container } = render(
      <>
        <Host />
        <Dock />
      </>,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Minimize Test window" }),
    );
    expect(useDesk.getState().panelMin).toEqual(["t1"]);
    // display:none removes it from the a11y tree; the mount itself parks.
    const shell = container.querySelector(
      '[aria-label="Test window"][role="region"]',
    ) as HTMLElement;
    expect(shell).toBeTruthy();
    expect(shell.style.display).toBe("none");
    expect(screen.getByText("window content")).toBeInTheDocument();
    // The dock names it and restores it.
    const chip = screen.getByRole("button", { name: "Restore Test window" });
    fireEvent.click(chip);
    expect(useDesk.getState().panelMin).toEqual([]);
    expect(shell.style.display).not.toBe("none");
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
    const shell = screen.getByRole("region", { name: "Test window" });
    expect(shell.className).toContain("is-max");
    fireEvent.click(screen.getByRole("button", { name: "Restore Test window" }));
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

describe("the lifecycle store + hs.desk.panels persistence", () => {
  it("round-trips rects + order + max through one slot; min stays out (HS-97-03)", () => {
    useDesk.getState().setPanelRect("a", { x: 10, y: 20, w: 400, h: 300 }, true);
    useDesk.getState().minimizePanel("a");
    useDesk.getState().toggleMaximizePanel("b");
    const raw = JSON.parse(localStorage.getItem("hs.desk.panels") || "{}");
    expect(raw.rects.a).toEqual({ x: 10, y: 20, w: 400, h: 300 });
    expect(raw.min).toBeUndefined();
    expect(raw.order).toEqual(["b"]);
    expect(raw.max).toEqual(["b"]);
    expect(useDesk.getState().panelMin).toEqual(["a"]);
  });

  it("restore and un-maximize persist their removals", () => {
    useDesk.getState().minimizePanel("a");
    useDesk.getState().restorePanel("a");
    useDesk.getState().toggleMaximizePanel("b");
    useDesk.getState().toggleMaximizePanel("b");
    const raw = JSON.parse(localStorage.getItem("hs.desk.panels") || "{}");
    expect(raw.min).toBeUndefined();
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
