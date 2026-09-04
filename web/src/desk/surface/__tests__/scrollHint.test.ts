// HS-167-03 — ScrollHint pure function vitest + grep fence.
import { describe, expect, it } from "vitest";
import { computeScrollHint, type ScrollHintState } from "../Surface";
import { execSync } from "node:child_process";
import { resolve } from "node:path";

describe("computeScrollHint (axis-neutral pure function)", () => {
  it("returns none when content fits", () => {
    expect(computeScrollHint(0, 800, 800)).toBe("none");
    expect(computeScrollHint(0, 700, 800)).toBe("none");
  });

  it("returns end at the start edge", () => {
    expect(computeScrollHint(0, 1120, 393)).toBe("end");
  });

  it("returns start at the end edge", () => {
    expect(computeScrollHint(727, 1120, 393)).toBe("start");
  });

  it("returns both at a mid-scroll position", () => {
    expect(computeScrollHint(200, 1120, 393)).toBe("both");
  });

  it("absorbs the 20px tolerance", () => {
    // scrollOffset + clientExtent = 717, scrollExtent - 20 = 700 => atEnd = true
    expect(computeScrollHint(324, 720, 393)).toBe("start");
  });
});

describe("ScrollHint fence: no computeScrollHint outside the barrel", () => {
  const root = resolve(__dirname, "../../../../..");

  it("computeScrollHint is not defined outside desk/surface (re-exports allowed)", () => {
    // Grep for the function DEFINITION (not import/re-export).
    // The barrel owns the canonical definition; DoorBoardLane re-exports
    // via a thin wrapper (allowed). steward/model.ts re-exports too.
    // We check that no file OUTSIDE desk/surface and the two re-export
    // sites defines the function from scratch.
    const result = execSync(
      `grep -rn "export function computeScrollHint\\|export function computeVerticalScrollHint" web/src/ --include='*.ts' --include='*.tsx' --exclude-dir='__tests__' || true`,
      { cwd: root, encoding: "utf-8" },
    );
    const lines = result
      .trim()
      .split("\n")
      .filter(Boolean);
    // Only allowed locations:
    // 1. desk/surface/Surface.tsx (the canonical definition)
    // 2. desk/chair/lanes/DoorBoardLane.tsx (thin re-export wrapper)
    // 3. features/project-room/steward/model.ts (thin re-export wrapper)
    const forbidden = lines.filter(
      (line) =>
        !line.includes("desk/surface/Surface.tsx") &&
        !line.includes("desk/chair/lanes/DoorBoardLane.tsx") &&
        !line.includes("features/project-room/steward/model.ts"),
    );
    expect(
      forbidden,
      `computeScrollHint/computeVerticalScrollHint defined outside allowed locations:\n${forbidden.join("\n")}`,
    ).toEqual([]);
  });
});
