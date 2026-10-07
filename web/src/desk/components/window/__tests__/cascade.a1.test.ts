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
