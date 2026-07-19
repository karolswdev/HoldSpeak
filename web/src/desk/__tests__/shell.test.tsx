// HS-95-03 — the shell: the dock (chips, focus/restore/close, reset), MRU
// keyboard cycling, edge-snap math, and the surface dispatcher the chrome
// routes through instead of navigating.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  DeskWindowFrame,
  Dock,
  clampIntoBand,
  exposeLayout,
  placeWindow,
  resizeEdge,
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
  it("shows a chip per open window; the four applications ride always", () => {
    const { unmount } = render(<TwoWindows />);
    expect(screen.getByRole("toolbar", { name: "Dock" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Focus Alpha" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Focus Beta" })).toBeTruthy();
    unmount();
    // HS-100-11 — the dock IS the launcher: with nothing open it still
    // carries the four applications (no window chips, no running marks).
    render(<Dock />);
    expect(screen.getByRole("toolbar", { name: "Dock" })).toBeTruthy();
    for (const app of ["Speak", "Meetings", "Agents", "Settings"]) {
      expect(screen.getByRole("button", { name: app })).toBeTruthy();
    }
    expect(screen.queryByRole("button", { name: /Focus / })).toBeNull();
    expect(document.querySelector(".desk-dock-app.is-run")).toBeNull();
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
    const dock = screen.getByRole("toolbar", { name: "Dock" });
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
    ).toEqual({ rects: {}, order: [], max: [] });
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

describe("placeWindow (HS-97-02, the open-placement engine)", () => {
  const VW = 1440;
  const VH = 900;
  const TOP = 54;
  const BOTTOM = 52;

  const headsClash = (
    a: { x: number; y: number; w: number },
    b: { x: number; y: number; w: number },
  ) =>
    a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + 44 && a.y + 44 > b.y;

  it("a free stage keeps the seed", () => {
    const r = placeWindow({ x: 24, y: 72, w: 640, h: 480 }, [], VW, VH);
    expect(r).toEqual({ x: 24, y: 72, w: 640, h: 480 });
  });

  it("a second window at the same home moves off the first title bar", () => {
    const first = { x: 24, y: 72, w: 640, h: 480 };
    const r = placeWindow({ ...first }, [first], VW, VH);
    expect(headsClash(r, first)).toBe(false);
    expect(r.x).toBeGreaterThanOrEqual(10);
    expect(r.x + r.w).toBeLessThanOrEqual(VW - 10);
    expect(r.y).toBeGreaterThanOrEqual(TOP);
    expect(r.y + r.h).toBeLessThanOrEqual(VH - BOTTOM);
  });

  it("an off-viewport seed lands whole inside the working band", () => {
    const r = placeWindow({ x: -200, y: 1000, w: 640, h: 480 }, [], VW, VH);
    expect(r.x).toBeGreaterThanOrEqual(10);
    expect(r.y + r.h).toBeLessThanOrEqual(VH - BOTTOM);
    expect(r.w).toBe(640);
  });

  it("an oversize window shrinks to the band", () => {
    const r = placeWindow({ x: 24, y: 72, w: 640, h: 2000 }, [], VW, VH);
    expect(r.h).toBe(VH - TOP - BOTTOM);
    expect(r.y).toBe(TOP);
  });

  it("a window may shade another's body but never its title bar", () => {
    const wall = { x: 10, y: TOP, w: VW - 20, h: VH - TOP - BOTTOM };
    const r = placeWindow({ x: 24, y: 72, w: 640, h: 480 }, [wall], VW, VH);
    expect(headsClash(r, wall)).toBe(false);
    expect(r.y).toBeGreaterThanOrEqual(TOP + 44);
  });

  it("a saturated stage cascades off the home seat, still in band", () => {
    // Title bars tile the whole working band: every candidate collides.
    const rows: { x: number; y: number; w: number; h: number }[] = [];
    for (let y = TOP; y <= VH - BOTTOM; y += 32)
      rows.push({ x: 10, y, w: VW - 20, h: 44 });
    const r = placeWindow({ x: 24, y: 72, w: 640, h: 480 }, rows, VW, VH);
    expect(r.x).toBe(24 + 26 * 8);
    expect(r.y).toBe(72 + 26 * 8);
    expect(r.y + r.h).toBeLessThanOrEqual(VH - BOTTOM);
  });
});

describe("resizeEdge (HS-97-05, edge resize math)", () => {
  const base = { x: 100, y: 100, w: 400, h: 300 };

  it("right and bottom edges grow with the pointer", () => {
    expect(resizeEdge("r", base, 50, 0, 320, 220).w).toBe(450);
    expect(resizeEdge("b", base, 0, 40, 320, 220).h).toBe(340);
  });

  it("the left edge moves x and shrinks w together", () => {
    const r = resizeEdge("l", base, 30, 0, 320, 220);
    expect(r.x).toBe(130);
    expect(r.w).toBe(370);
  });

  it("the left edge keeps the right edge fixed at the minimum", () => {
    const r = resizeEdge("l", base, 200, 0, 320, 220);
    expect(r.w).toBe(320);
    expect(r.x).toBe(180);
  });

  it("the bottom-left corner drives both axes", () => {
    const r = resizeEdge("bl", base, -20, 30, 320, 220);
    expect(r.x).toBe(80);
    expect(r.w).toBe(420);
    expect(r.h).toBe(330);
  });
});

describe("exposeLayout (HS-97-06, the pick grid)", () => {
  it("four windows tile 2x2 inside the working band, no overlap", () => {
    const cells = exposeLayout(4, 1440, 900);
    expect(cells).toHaveLength(4);
    for (const c of cells) {
      expect(c.x).toBeGreaterThanOrEqual(10);
      expect(c.x + c.w).toBeLessThanOrEqual(1430);
      expect(c.y).toBeGreaterThanOrEqual(54);
      expect(c.y + c.h).toBeLessThanOrEqual(900 - 52);
    }
    for (let i = 0; i < cells.length; i++)
      for (let j = i + 1; j < cells.length; j++) {
        const a = cells[i];
        const b = cells[j];
        const overlap =
          a.x < b.x + b.w &&
          a.x + a.w > b.x &&
          a.y < b.y + b.h &&
          a.y + a.h > b.y;
        expect(overlap).toBe(false);
      }
  });

  it("a last-row straggler centers", () => {
    const cells = exposeLayout(3, 1440, 900);
    const last = cells[2];
    const mid = last.x + last.w / 2;
    expect(Math.abs(mid - 720)).toBeLessThan(last.w);
  });
});

describe("clampIntoBand (HS-97-02, clamp-on-open)", () => {
  it("a rect persisted on a larger viewport lands whole", () => {
    const r = clampIntoBand({ x: 1300, y: 800, w: 640, h: 480 }, 1440, 900);
    expect(r).toEqual({ x: 790, y: 368, w: 640, h: 480 });
  });

  it("an in-band rect is untouched", () => {
    const r = clampIntoBand({ x: 100, y: 100, w: 400, h: 300 }, 1440, 900);
    expect(r).toEqual({ x: 100, y: 100, w: 400, h: 300 });
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
