/* Inventory C, gap 1 (2026-10-03) — one ref name for a desk decision.
 *
 * Red on 6ccfa4e0: Decide filed the decision into its Project as
 * `decision:<id>`; memory's project filter reads `desk_decision:<id>`, so
 * the decision was lost to its Project. A `desk_decision:` ref (a memory
 * hit, a Brief row) opened nothing: the Desk keeps the window under
 * `decision:<id>`. */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { createDecision } from "../api";
import { DecisionUnconfirmed, decideFromMeeting, fileAgain, meetingScope } from "../decide";
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
  // HS-S42: the meeting decision is the canonical record; it files as
  // decision_record:<id>, once, after both identities are acknowledged.
  const created = {
    record: { id: "rec_1", source_id: "decision_7ce0" },
    decision: { id: "decision_7ce0", title: "Adopt quorumdb", status: "accepted", tags: ["meeting:m1", "project:proj-atlas"] },
  };
  const calls = () => vi.mocked(apiFetch).mock.calls.map(([path, init]) =>
    `${(init as { method?: string } | undefined)?.method ?? "GET"} ${decodeURIComponent(String(path))}`);

  it("Decide files the canonical record into the chosen Project as decision_record:<id>", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string }) => {
      if (path === "/api/decision-records/from-desk") return created as never;
      if (init?.method === "PUT") return { resource: { project_id: "proj-atlas", relationship: "member" } } as never;
      throw new Error(`unexpected ${path}`);
    });

    const made = await decideFromMeeting({
      title: "Adopt quorumdb", meetingId: "m1", meetingTitle: "Ledger sync",
      project: { id: "proj-atlas", name: "Atlas" },
    });

    expect(calls()).toEqual([
      "POST /api/decision-records/from-desk",
      "PUT /api/projects/proj-atlas/resources/decision_record:rec_1",
    ]);
    expect(made).toMatchObject({ recordId: "rec_1", sourceId: "decision_7ce0", filing: "filed" });
    expect(createDecision).not.toHaveBeenCalled();
  });

  it("a malformed canonical answer never falls back to POST /api/decisions", async () => {
    vi.mocked(apiFetch).mockResolvedValue({} as never);
    vi.mocked(createDecision).mockResolvedValue({ id: "decision_dup" } as never);

    await expect(decideFromMeeting({
      title: "Adopt quorumdb", meetingId: "m1", meetingTitle: "Ledger sync", project: null,
    })).rejects.toBeInstanceOf(DecisionUnconfirmed);

    expect(createDecision).not.toHaveBeenCalled();
    expect(calls()).toEqual(["POST /api/decision-records/from-desk"]);
  });

  it("a lost or 5xx canonical answer is unconfirmed; a 4xx is a known refusal", async () => {
    vi.mocked(apiFetch).mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(decideFromMeeting({ title: "A", meetingId: "m1", meetingTitle: "M", project: null }))
      .rejects.toBeInstanceOf(DecisionUnconfirmed);
    vi.mocked(apiFetch).mockRejectedValueOnce(new ApiError(502, "bad gateway", {}));
    await expect(decideFromMeeting({ title: "A", meetingId: "m1", meetingTitle: "M", project: null }))
      .rejects.toBeInstanceOf(DecisionUnconfirmed);
    vi.mocked(apiFetch).mockRejectedValueOnce(new ApiError(400, "refused", {}));
    await expect(decideFromMeeting({ title: "A", meetingId: "m1", meetingTitle: "M", project: null }))
      .rejects.toBeInstanceOf(ApiError);
    expect(createDecision).not.toHaveBeenCalled();
    expect(calls().filter((c) => c.startsWith("POST"))).toEqual(Array(3).fill("POST /api/decision-records/from-desk"));
  });

  it("a refused filing after creation keeps both IDs and does not create again", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string }) => {
      if (path === "/api/decision-records/from-desk") return created as never;
      if (init?.method === "PUT") throw new ApiError(409, "refused", {});
      throw new Error(`unexpected ${path}`);
    });
    const made = await decideFromMeeting({
      title: "Adopt quorumdb", meetingId: "m1", meetingTitle: "Ledger sync",
      project: { id: "proj-atlas", name: "Atlas" },
    });
    expect(made).toMatchObject({ recordId: "rec_1", sourceId: "decision_7ce0", filing: "refused" });
    expect(calls().filter((c) => c.startsWith("POST"))).toHaveLength(1);
  });

  it("an unfiled decision writes no project edge", async () => {
    vi.mocked(apiFetch).mockResolvedValue(created as never);
    const made = await decideFromMeeting({ title: "Adopt quorumdb", meetingId: "m1", meetingTitle: "Ledger sync", project: null });
    expect(made.filing).toBe("unfiled");
    expect(calls()).toEqual(["POST /api/decision-records/from-desk"]);
  });

  it("File again reads first: member is filed, another kind is left, absence writes once", async () => {
    const rows = (relationship?: string) => ({ resource_ref: "decision_record:rec_1",
      projects: relationship ? [{ project_id: "proj-atlas", relationship }] : [] });
    vi.mocked(apiFetch).mockResolvedValueOnce(rows("member") as never);
    expect(await fileAgain("rec_1", "proj-atlas")).toBe("filed");
    vi.mocked(apiFetch).mockResolvedValueOnce(rows("source") as never);
    expect(await fileAgain("rec_1", "proj-atlas")).toBe("other");
    vi.mocked(apiFetch).mockResolvedValueOnce({} as never);
    expect(await fileAgain("rec_1", "proj-atlas")).toBe("unknown");
    expect(calls().filter((c) => c.startsWith("PUT"))).toEqual([]);
    vi.mocked(apiFetch).mockResolvedValueOnce(rows() as never)
      .mockResolvedValueOnce({ resource: { project_id: "proj-atlas", relationship: "member" } } as never);
    expect(await fileAgain("rec_1", "proj-atlas")).toBe("filed");
    expect(calls().filter((c) => c.startsWith("PUT"))).toEqual(["PUT /api/projects/proj-atlas/resources/decision_record:rec_1"]);
  });

  it("the meeting scope keeps every linked project and tells a failed read from none", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce({ projects: [
      { project_id: "a", project_name: "Atlas" }, { project_id: "b", project_name: "Ledger" },
    ] } as never);
    expect(await meetingScope("m1")).toEqual({ state: "known", projects: [{ id: "a", name: "Atlas" }, { id: "b", name: "Ledger" }] });
    vi.mocked(apiFetch).mockResolvedValueOnce({ projects: [] } as never);
    expect(await meetingScope("m1")).toEqual({ state: "none" });
    vi.mocked(apiFetch).mockRejectedValueOnce(new ApiError(500, "boom", {}));
    expect((await meetingScope("m1")).state).toBe("unavailable");
    vi.mocked(apiFetch).mockResolvedValueOnce({} as never);
    expect((await meetingScope("m1")).state).toBe("unavailable");
  });

  it("a desk_decision ref opens the decision window", () => {
    refOpener("desk_decision:decision_7ce0")?.();
    expect(openPrimitive).toHaveBeenCalledWith("decision:decision_7ce0");

    vi.mocked(openPrimitive).mockReset();
    openSourceRef("desk_decision:decision_7ce0");
    expect(openPrimitive).toHaveBeenCalledWith("decision:decision_7ce0");
  });
});
