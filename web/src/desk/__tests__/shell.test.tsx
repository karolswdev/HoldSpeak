// HS-95-03 — the shell: the dock (chips, focus/restore/close, reset), MRU
// keyboard cycling, edge-snap math, and the surface dispatcher the chrome
// routes through instead of navigating.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  DeskWindowFrame,
  Dock,
  snapForPointer,
} from "../components/DeskWindow";
import { openSurface, registerSurface, __resetSurfaces } from "../shell";
import { useDesk } from "../store";

beforeEach(() => {
  localStorage.clear();
  __resetSurfaces();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
  });
});

function TwoWindows({ onCloseA = () => {} }) {
  return (
    <>
      <DeskWindowFrame id="wa" title="Alpha" open onClose={onCloseA}>
        <p>alpha body</p>
      </DeskWindowFrame>
      <DeskWindowFrame id="wb" title="Beta" open onClose={() => {}}>
        <p>beta body</p>
      </DeskWindowFrame>
      <Dock />
    </>
  );
}

describe("the dock", () => {
  it("shows a chip per open window and none when nothing is open", () => {
    const { unmount } = render(<TwoWindows />);
    expect(screen.getByRole("toolbar", { name: "Open windows" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Focus Alpha" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Focus Beta" })).toBeTruthy();
    unmount();
    render(<Dock />);
    expect(screen.queryByRole("toolbar", { name: "Open windows" })).toBeNull();
  });

  it("tap focuses; a parked window's chip restores it", () => {
    render(<TwoWindows />);
    fireEvent.click(screen.getByRole("button", { name: "Focus Alpha" }));
    expect(useDesk.getState().panelOrder.at(-1)).toBe("wa");
    fireEvent.click(screen.getByRole("button", { name: "Minimize Alpha" }));
    expect(useDesk.getState().panelMin).toEqual(["wa"]);
    fireEvent.click(screen.getByRole("button", { name: "Restore Alpha" }));
    expect(useDesk.getState().panelMin).toEqual([]);
    expect(useDesk.getState().panelOrder.at(-1)).toBe("wa");
  });

  it("the dock close affordance drives the window's own close", () => {
    const onCloseA = vi.fn();
    render(<TwoWindows onCloseA={onCloseA} />);
    // Two "Close Alpha" buttons exist (window verb + dock ✕); the dock's
    // lives inside the toolbar.
    const dock = screen.getByRole("toolbar", { name: "Open windows" });
    const x = Array.from(dock.querySelectorAll("button")).find(
      (b) => b.getAttribute("aria-label") === "Close Alpha",
    )!;
    fireEvent.click(x);
    expect(onCloseA).toHaveBeenCalledTimes(1);
  });

  it("Ctrl+` cycles focus in MRU order, restoring as it lands", () => {
    render(<TwoWindows />);
    useDesk.getState().focusPanel("wa");
    useDesk.getState().focusPanel("wb");
    fireEvent.keyDown(document, { key: "`", ctrlKey: true });
    expect(useDesk.getState().panelOrder.at(-1)).toBe("wa");
    useDesk.getState().minimizePanel("wb");
    fireEvent.keyDown(document, { key: "`", ctrlKey: true });
    expect(useDesk.getState().panelMin).toEqual([]);
    expect(useDesk.getState().panelOrder.at(-1)).toBe("wb");
  });

  it("reset layout forgets rects and lifecycle and persists the wipe", () => {
    render(<TwoWindows />);
    useDesk.getState().setPanelRect("wa", { x: 5, y: 6, w: 400, h: 300 }, true);
    useDesk.getState().minimizePanel("wb");
    fireEvent.click(screen.getByRole("button", { name: "Reset layout" }));
    const s = useDesk.getState();
    expect(s.panelRects).toEqual({});
    expect(s.panelMin).toEqual([]);
    expect(s.panelMax).toEqual([]);
    expect(
      JSON.parse(localStorage.getItem("hs.desk.panels") || "{}"),
    ).toEqual({ rects: {}, min: [], max: [] });
  });
});

describe("snapForPointer (edge tiling)", () => {
  const VW = 1440;
  const VH = 900;

  it("left/right flanks take halves below the chrome band", () => {
    const left = snapForPointer(10, 450, VW, VH)!;
    expect(left.x).toBe(10);
    expect(left.y).toBe(54);
    expect(left.h).toBe(VH - 54 - 52);
    const right = snapForPointer(VW - 5, 450, VW, VH)!;
    expect(right.x + right.w).toBe(VW - 10);
    expect(right.w).toBe(left.w);
  });

  it("corners take quarters", () => {
    const tl = snapForPointer(40, 80, VW, VH)!;
    const br = snapForPointer(VW - 40, VH - 40, VW, VH)!;
    expect(tl.y).toBe(54);
    expect(br.y).toBeGreaterThan(tl.y + tl.h - 1);
    expect(tl.w).toBe(br.w);
  });

  it("the open middle is a free park (no snap)", () => {
    expect(snapForPointer(VW / 2, VH / 2, VW, VH)).toBeNull();
  });
});

describe("the surface dispatcher", () => {
  it("routes a registered surface and reports unregistered ones", () => {
    const opened: string[] = [];
    const off = registerSurface("dictate", (scope) =>
      opened.push(scope || "-"),
    );
    expect(openSurface("dictate", "note:n1")).toBe(true);
    expect(opened).toEqual(["note:n1"]);
    expect(openSurface("review-meetings")).toBe(false);
    off();
    expect(openSurface("dictate")).toBe(false);
  });
});
