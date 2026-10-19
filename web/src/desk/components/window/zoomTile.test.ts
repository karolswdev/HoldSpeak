// C1-4e (STATUS: "the Chair reopens 12 px low"): zoom on a Chair window the
// owner never moved must not turn its CSS tile place into an arranged rect.
// With the rect written, the next open clamped it into the shell band
// (54 px) and the window came back 12 px under its tile place (42 px).
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useDesk } from "../../store";
import { shellEls } from "./windowRegistry";
import { zoomWindow } from "./windowCommands";

function shellAt(id: string, rect: { x: number; y: number; w: number; h: number }) {
  const el = document.createElement("div");
  el.getBoundingClientRect = () =>
    ({ left: rect.x, top: rect.y, width: rect.w, height: rect.h, right: rect.x + rect.w, bottom: rect.y + rect.h, x: rect.x, y: rect.y, toJSON: () => ({}) }) as DOMRect;
  shellEls.set(id, el);
}

beforeEach(() => {
  useDesk.setState({ panelRects: {}, panelSaved: [], panelMax: [], panelOrder: [] });
});
afterEach(() => {
  shellEls.clear();
});

describe("zoom keeps a Chair window's tile place", () => {
  it("writes no rect for a Chair window at its tile place, and unzoom returns to the tile", () => {
    shellAt("chair:capture", { x: 728, y: 42, w: 698, h: 483 });
    zoomWindow("chair:capture");
    expect(useDesk.getState().panelMax).toContain("chair:capture");
    expect(useDesk.getState().panelRects["chair:capture"]).toBeUndefined();
    zoomWindow("chair:capture");
    expect(useDesk.getState().panelMax).not.toContain("chair:capture");
    expect(useDesk.getState().panelRects["chair:capture"]).toBeUndefined();
  });

  it("keeps a Chair window's arranged rect", () => {
    const moved = { x: 300, y: 120, w: 600, h: 400 };
    useDesk.setState({ panelRects: { "chair:capture": moved } });
    shellAt("chair:capture", moved);
    zoomWindow("chair:capture");
    expect(useDesk.getState().panelRects["chair:capture"]).toEqual(moved);
  });

  it("still keeps the normal rect of any other window on its first zoom (PR #731)", () => {
    shellAt("surface-meetings", { x: 100, y: 80, w: 500, h: 400 });
    zoomWindow("surface-meetings");
    expect(useDesk.getState().panelRects["surface-meetings"]).toEqual({ x: 100, y: 80, w: 500, h: 400 });
  });
});
