/* Astra's review of #768, finding 1 — a memory citation must open.
 *
 * The drafters (update, Prep, meeting summary, 1:1 brief) cite the refs
 * `holdspeak/services/memory_grounding.py` returns. That file names the ref
 * kinds it returns in `DESK_REF_KINDS`. This test reads the tuple from the
 * Python source and puts every kind through the real opener: a kind the
 * Desk does not open fails here. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { openIntelligence } from "../intelligenceNavigation";
import { openRef, refOpener } from "../openObject";
import { openPrimitive, openSurfaceOr } from "../shell";

vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openPrimitive: vi.fn(),
  openSurfaceOr: vi.fn(),
}));
vi.mock("../intelligenceNavigation", async (original) => ({
  ...(await original<typeof import("../intelligenceNavigation")>()),
  openIntelligence: vi.fn(),
}));
vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  // A meeting decision's read: no source meeting, so it opens as itself.
  apiFetch: vi.fn(async () => ({ decision: {} })),
}));

beforeEach(() => {
  vi.mocked(openPrimitive).mockClear();
  vi.mocked(openSurfaceOr).mockClear();
  vi.mocked(openIntelligence).mockClear();
});

const SOURCE = resolve(__dirname, "../../../../holdspeak/services/memory_grounding.py");

function helperRefKinds(): string[] {
  const match = /^DESK_REF_KINDS = \(([^)]*)\)/m.exec(readFileSync(SOURCE, "utf8"));
  if (!match) throw new Error("DESK_REF_KINDS not found in memory_grounding.py");
  return [...match[1].matchAll(/"([a-z_]+)"/g)].map((m) => m[1]);
}

describe("every ref the drafters' memory helper returns opens on the Desk", () => {
  const kinds = helperRefKinds();

  it("reads the kinds from the helper", () => {
    expect(kinds.length).toBeGreaterThan(0);
    expect(kinds).toContain("desk_decision");
  });

  it.each(kinds)("%s:<id> has an opener", (kind) => {
    expect(refOpener(`${kind}:x1`)).toBeTypeOf("function");
  });

  it.each(kinds)("a %s citation opens a window (the Room's claim-ref opener)", async (kind) => {
    openRef(`${kind}:x1`);
    await new Promise((done) => setTimeout(done, 0));
    const opened =
      vi.mocked(openPrimitive).mock.calls.length +
      vi.mocked(openSurfaceOr).mock.calls.length +
      vi.mocked(openIntelligence).mock.calls.length;
    expect(opened).toBe(1);
  });

  it("a desk decision opens the Desk's decision window, under the name the store keeps", () => {
    openRef("desk_decision:decision_7ce0");
    expect(openPrimitive).toHaveBeenCalledWith("decision:decision_7ce0");
  });

  it("the memory names with no Desk window are not openers (so the helper leaves them out)", () => {
    for (const kind of ["project_item", "decision_record", "cadence", "workbench_item"]) {
      expect(refOpener(`${kind}:x1`)).toBeNull();
    }
  });
});
