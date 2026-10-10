// PHILO-14 A1 (Muad'Dib's ruling on #939): a window that opens on a full
// desk is never stacked: it cascades 24/24 off the window placed last and
// leaves every title bar partly in view.
import { describe, expect, it } from "vitest";
import { placeWindow } from "../windowGeometry";

describe("placeWindow on a saturated desk", () => {
  it("cascades 24/24 off the last placed window, hiding no title bar whole", () => {
    // The J1 walk's desk: two halves and a window on the right; a tall new
    // window touches a title bar wherever it stands (saturated).
    const existing = [
      { x: 12, y: 40, w: 700, h: 700 },
      { x: 720, y: 40, w: 700, h: 700 },
      { x: 1000, y: 60, w: 420, h: 700 },
    ];
    const last = existing[existing.length - 1];
    const seed = { x: 1000, y: 60, w: 400, h: 780 };
    const at = placeWindow(seed, existing, 1440, 900);
    for (const r of existing) {
      const hides = at.x <= r.x && at.x + at.w >= r.x + r.w && at.y <= r.y && at.y + at.h >= r.y + 44;
      expect(hides, JSON.stringify(r)).toBe(false);
    }
    // 24 to the right of the window placed last (clamped into the band)
    expect(at.x).toBe(last.x + 24);
  });
});

// PHILO-17 U28a: every app opened at its CSS home (24,72), on top of the
// Chair's icon column, and two in a row sat exactly on each other.
describe("placeWindow clear of the icon column", () => {
  const home = { x: 24, y: 72, w: 640, h: 600 };

  it("opens right of the icon column", () => {
    const at = placeWindow(home, [], 1440, 900, 420, 220, 144);
    expect(at.x).toBeGreaterThanOrEqual(144);
  });

  it("a second window does not sit on the first", () => {
    const first = placeWindow(home, [], 1440, 900, 420, 220, 144);
    const second = placeWindow(home, [first], 1440, 900, 420, 220, 144);
    expect(second.x).toBeGreaterThanOrEqual(144);
    expect([second.x, second.y]).not.toEqual([first.x, first.y]);
  });

  it("a window too wide to clear the column stays on the screen", () => {
    const at = placeWindow({ ...home, w: 1400 }, [], 1440, 900, 420, 220, 144);
    expect(at.x).toBeGreaterThanOrEqual(10);
    expect(at.x + at.w).toBeLessThanOrEqual(1430);
  });
});
