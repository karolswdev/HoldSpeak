import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DESK_WINDOW } from "../../../../lib/tokens.gen";
import {
  clampIntoBand,
  clampRect,
  placeWindow,
  snapForPointer,
  workBand,
} from "../windowGeometry";

// Browsers resolve custom-property aliases in getComputedStyle. jsdom leaves
// var(...) untouched, so supply the resolved values for these geometry checks.
function computedBand(top: string, bottom: string, dock = "") {
  const values: Record<string, string> = {
    "--desk-work-top": top,
    "--desk-work-bottom": bottom,
    "--desk-dock-h": dock,
  };
  vi.spyOn(globalThis, "getComputedStyle").mockReturnValue({
    getPropertyValue: (name: string) => values[name] ?? "",
  } as CSSStyleDeclaration);
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("window working band", () => {
  it("uses the screen bar token and has a 28 px fallback before CSS arrives", () => {
    const css = readFileSync("src/styles/tokens.css", "utf8");
    expect(css).toMatch(/--desk-work-top:\s*var\(--wb-screen-h\);/);
    expect(DESK_WINDOW.snapTop).toBe(28);
    expect(DESK_WINDOW.snapBottom).toBe(60);
    computedBand("", "");
    expect(workBand()).toEqual({ top: 28, bottom: 60 });
  });

  it.each([
    { name: "desktop", top: 28, bottom: 60, width: 1440 },
    { name: "phone", top: 44, bottom: 56, width: 393 },
    { name: "explicit working-band override", top: 36, bottom: 60, width: 1440 },
  ])("keeps drag, restore, open and snap at the $name boundary", ({ top, bottom, width }) => {
    computedBand(`${top}px`, `${bottom}px`, `${bottom}px`);
    vi.stubGlobal("innerWidth", width);
    vi.stubGlobal("innerHeight", 900);
    const aboveBar = { x: 20, y: -100, w: 320, h: 300 };

    expect(workBand()).toEqual({ top, bottom });
    const dragged = clampRect(aboveBar, 320, 220);
    expect(dragged.y).toBe(top);
    expect(clampIntoBand(dragged, width, 900)).toEqual(dragged);
    expect(clampIntoBand(aboveBar, width, 900).y).toBe(top);
    expect(placeWindow(aboveBar, [], width, 900).y).toBe(top);
    expect(snapForPointer(0, 0, width, 900)?.y).toBe(top);

    const tall = clampIntoBand({ ...aboveBar, h: 1200 }, width, 900);
    expect(tall.y).toBe(top);
    expect(tall.y + tall.h).toBe(900 - bottom);
  });

  it.each([
    { band: 60, dock: "76px", expected: 76 },
    { band: 60, dock: "48px", expected: 60 },
    { band: 56, dock: "56px", expected: 56 },
    { band: 60, dock: "", expected: 60 },
  ])("reserves $expected px for band $band and measured Dock $dock", ({ band, dock, expected }) => {
    computedBand("28px", `${band}px`, dock);
    expect(workBand().bottom).toBe(expected);
    const restored = clampIntoBand({ x: 20, y: 800, w: 400, h: 300 }, 1440, 900);
    expect(restored.y + restored.h).toBe(900 - expected);
  });
});
