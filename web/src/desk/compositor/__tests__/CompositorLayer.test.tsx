import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DESK_WORKSPACE_STORAGE_KEY, useDesk, type PanelRect } from "../../store";
import { CompositorLayer } from "../CompositorLayer";
import { computePlanes, mountWindow, setPresentation, unmountWindow, zOfWindow } from "../live";

const IDS = ["settings", "decision", "today"] as const;
const RECTS: Record<string, PanelRect> = {
  settings: { x: 10, y: 54, w: 700, h: 700 },
  decision: { x: 710, y: 54, w: 700, h: 700 },
  // Today covers the middle of the Settings/Decision seam, leaving both ends exposed.
  today: { x: 500, y: 150, w: 700, h: 450 },
};

beforeEach(() => {
  vi.stubGlobal("innerWidth", 1440);
  vi.stubGlobal("innerHeight", 900);
  setPresentation({ mode: "free", plates: {}, saved: {}, staged: null });
  useDesk.setState({
    panelRects: { ...RECTS },
    panelDepth: { settings: 1, decision: 2, today: 3 },
    panelOrder: [...IDS],
    panelMin: [],
    panelMax: [],
    panelSaved: [],
  });
  for (const id of IDS) mountWindow(id, { layer: "window", minW: 420, minH: 220 });
});

afterEach(() => {
  cleanup();
  for (const id of IDS) unmountWindow(id);
  setPresentation({ mode: "free", plates: {}, saved: {}, staged: null });
  useDesk.setState({ panelRects: {}, panelDepth: {}, panelOrder: [], panelMin: [], panelMax: [], panelSaved: [] });
  localStorage.removeItem(DESK_WORKSPACE_STORAGE_KEY);
  vi.unstubAllGlobals();
});

describe("the shared divider follows its participant windows", () => {
  it("stays below an unrelated front window covering the seam", () => {
    render(<CompositorLayer />);
    const divider = screen.getByRole("separator", { name: "Resize the windows on both sides" });
    const live = computePlanes();

    // The mounted windows, shown ranks and touching boundary are all real.
    expect(live.shown).toEqual([...IDS]);
    expect(IDS.map((id) => zOfWindow(id, live))).toEqual([42, 43, 44]);
    expect(screen.getAllByRole("separator")).toHaveLength(1);
    expect(divider).toHaveAttribute("aria-orientation", "vertical");
    expect(divider).toHaveStyle({ left: "707px", top: "54px", width: "6px", height: "700px" });
    expect(Number(divider.style.zIndex)).toBe(zOfWindow("decision", live));
    expect(Number(divider.style.zIndex)).toBeLessThan(zOfWindow("today", live));
    // Actual paint and pointer ownership require the production browser probe.
  });

  it("keeps the seam at its highest participant when that window is raised", () => {
    render(<CompositorLayer />);
    const divider = screen.getByRole("separator");

    act(() => { useDesk.getState().focusPanel("settings"); });
    const live = computePlanes();
    expect(live.front).toBe("settings");
    expect(Number(divider.style.zIndex)).toBe(zOfWindow("settings", live));
    expect(Number(divider.style.zIndex)).toBeGreaterThan(zOfWindow("today", live));
  });

  it("still saves both participant rects from the exposed seam's arrow key", () => {
    render(<CompositorLayer />);
    const divider = screen.getByRole("separator");
    divider.focus();
    fireEvent.keyDown(divider, { key: "ArrowRight" });

    const state = useDesk.getState();
    expect(state.panelRects.settings).toEqual({ x: 10, y: 54, w: 716, h: 700 });
    expect(state.panelRects.decision).toEqual({ x: 726, y: 54, w: 684, h: 700 });
    expect(state.panelRects.today).toEqual(RECTS.today);
    expect(state.panelSaved).toEqual(["settings", "decision"]);
  });
});
