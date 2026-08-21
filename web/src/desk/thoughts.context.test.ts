import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../lib/api";
import { attachThoughtContext, detachThoughtContext, listThoughtContext, refreshThoughtContext, replaceDefaultThoughtContext, type Thought } from "./thoughts";

vi.mock("../lib/api", () => ({ apiFetch: vi.fn() }));

const thought = {
  id: "thought-1",
  source: { kind: "typed" },
  raw_captured_at: "now",
  state: "working",
  aggregate_revision: 4,
  lifecycle_revision: 1,
  working_revision: 3,
  attachment_revision: 2,
  working_note: { id: "note-1", title: "Working", body_markdown: "PRIVATE BODY", tags: [] },
  filing_status: "filed",
} as Thought;

beforeEach(() => vi.mocked(apiFetch).mockReset());

describe("Thought context client", () => {
  it("lists compact context through a bounded server query", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ attachments: [], pinned: [], recent: [], results: [], next_cursor: null } as never);
    await listThoughtContext("thought-1", { view: "compact", query: "launch", limit: 20 });
    expect(apiFetch).toHaveBeenCalledWith("/api/thoughts/thought-1/context?view=compact&query=launch&limit=20");
  });

  it("attaches by ref and cursors only, never copied Note or candidate material", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ thought, receipt: {} } as never);
    await attachThoughtContext(thought, "knowledge:hs-seed-everyday-context", "request-1");
    expect(apiFetch).toHaveBeenCalledWith("/api/thoughts/thought-1/context/attach", {
      method: "POST",
      json: {
        request_id: "request-1",
        ref: "knowledge:hs-seed-everyday-context",
        expected_aggregate_revision: 4,
        expected_working_revision: 3,
        expected_attachment_revision: 2,
      },
    });
    expect(JSON.stringify(vi.mocked(apiFetch).mock.calls[0][1])).not.toContain("PRIVATE BODY");
  });

  it.each([
    ["detach", detachThoughtContext],
    ["refresh", refreshThoughtContext],
  ] as const)("sends the same exact CAS envelope for %s", async (action, command) => {
    vi.mocked(apiFetch).mockResolvedValue({ thought, receipt: {} } as never);
    await command(thought, "note:launch", "request-2");
    expect(apiFetch).toHaveBeenCalledWith(`/api/thoughts/thought-1/context/${action}`, {
      method: "POST",
      json: {
        request_id: "request-2",
        ref: "note:launch",
        expected_aggregate_revision: 4,
        expected_working_revision: 3,
        expected_attachment_revision: 2,
      },
    });
  });

  it("replaces the future default with refs and its independent revision only", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ default_context: {}, receipt: {} } as never);
    await replaceDefaultThoughtContext({ request_id: "default-1", expected_revision: 3, refs: ["note:launch", "knowledge:everyday"] });
    expect(apiFetch).toHaveBeenCalledWith("/api/thoughts/default-context", {
      method: "PUT",
      json: { request_id: "default-1", expected_revision: 3, refs: ["note:launch", "knowledge:everyday"] },
    });
    expect(JSON.stringify(vi.mocked(apiFetch).mock.calls[0][1])).not.toContain("PRIVATE BODY");
  });
});
