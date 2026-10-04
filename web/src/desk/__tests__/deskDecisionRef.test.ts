/* Inventory C, gap 1 (2026-10-03) — one ref name for a desk decision.
 *
 * Red on 6ccfa4e0: Decide filed the decision into its Project as
 * `decision:<id>`; memory's project filter reads `desk_decision:<id>`, so
 * the decision was lost to its Project. A `desk_decision:` ref (a memory
 * hit, a Brief row) opened nothing: the Desk keeps the window under
 * `decision:<id>`. */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { createDecision } from "../api";
import { decideFromMeeting } from "../decide";
import { refOpener } from "../openObject";
import { openPrimitive } from "../shell";
import { openSourceRef } from "../surface";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../api", async (original) => ({
  ...(await original<typeof import("../api")>()),
  createDecision: vi.fn(),
}));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openPrimitive: vi.fn(),
}));

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  vi.mocked(createDecision).mockReset();
  vi.mocked(openPrimitive).mockReset();
});

describe("a desk decision has one ref name", () => {
  it("Decide files the decision into the meeting's Project as desk_decision:<id>", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path) === "/api/meetings/m1/projects") {
        return { projects: [{ project_id: "proj-atlas", project_name: "Atlas" }] } as never;
      }
      return {} as never;
    });
    vi.mocked(createDecision).mockResolvedValue({ id: "decision_7ce0" } as never);

    await decideFromMeeting({ title: "Adopt quorumdb", meetingId: "m1", meetingTitle: "Ledger sync" });

    const puts = vi.mocked(apiFetch).mock.calls.filter(
      ([, init]) => (init as { method?: string } | undefined)?.method === "PUT",
    );
    expect(puts.map(([path]) => path)).toEqual([
      `/api/projects/proj-atlas/resources/${encodeURIComponent("desk_decision:decision_7ce0")}`,
    ]);
  });

  it("a desk_decision ref opens the decision window", () => {
    refOpener("desk_decision:decision_7ce0")?.();
    expect(openPrimitive).toHaveBeenCalledWith("decision:decision_7ce0");

    vi.mocked(openPrimitive).mockReset();
    openSourceRef("desk_decision:decision_7ce0");
    expect(openPrimitive).toHaveBeenCalledWith("decision:decision_7ce0");
  });
});
