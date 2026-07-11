import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useProjections } from "../projections";

const row = (id: string) => ({
  version: 1,
  id,
  projection_kind: "attention",
  subject_ref: "meeting:m1",
  subject_label: "Daily return",
  title: "Meeting capture needs recovery",
  summary: "Open the Meeting for its durable checkpoint.",
  reason_code: "capture_recoverable",
  decision_kind: "recovery",
  attention_state: "needs_attention",
  actual_destination: "this_machine",
  authority_basis: "explicit_capture",
  attempt: null,
  outcome: "recoverable",
  timestamp: "2026-07-11T01:00:00Z",
  correlation_id: "meeting:m1",
  source_kind: "meeting",
  source_id: "m1",
  source_api: "/api/meetings/m1",
  detail_url: "/history?meeting=m1",
  severity: "error",
  dismissed: false,
});

function response(projections: ReturnType<typeof row>[], offset = 0, total = projections.length) {
  return {
    ok: true,
    status: 200,
    json: async () => ({
      projections,
      counts: { needs_attention: total, receipts: 0 },
      subject_counts: { "meeting:m1": { needs_attention: total, receipts: 0 } },
      page: { offset, limit: 50, total, has_more: offset + projections.length < total },
    }),
  };
}

describe("Desk attention and receipt projection store", () => {
  beforeEach(() => {
    useProjections.setState({
      projections: [], counts: {}, subject_counts: {},
      ambient: [], ambientTotal: 0,
      page: { offset: 0, limit: 50, total: 0, has_more: false },
      open: false, loading: false, error: "", query: "", kind: "", selectedId: null,
    });
  });
  afterEach(() => vi.unstubAllGlobals());

  it("loads counts and subject badges from the shared read model", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response([row("p1")])));
    await useProjections.getState().refresh(true);
    expect(useProjections.getState().counts.needs_attention).toBe(1);
    expect(useProjections.getState().subject_counts["meeting:m1"].needs_attention).toBe(1);
    expect(useProjections.getState().projections[0].source_api).toBe("/api/meetings/m1");
  });

  it("keeps ambient attention independent from drawer filters", async () => {
    const fetcher = vi.fn(async (_url: string) => response([row("ambient")], 0, 7));
    vi.stubGlobal("fetch", fetcher);
    useProjections.setState({ query: "receipts", kind: "receipt" });
    await useProjections.getState().refreshAmbient();
    expect(fetcher.mock.calls[0][0]).toContain("attention_state=needs_attention");
    expect(fetcher.mock.calls[0][0]).not.toContain("receipts");
    expect(useProjections.getState().ambient[0].id).toBe("ambient");
    expect(useProjections.getState().ambientTotal).toBe(7);
  });

  it("paginates without replacing already-visible receipts", async () => {
    const fetcher = vi.fn(async (url: string) =>
      String(url).includes("offset=50")
        ? response([row("p2")], 50, 51)
        : response([row("p1")], 0, 51),
    );
    vi.stubGlobal("fetch", fetcher);
    await useProjections.getState().refresh(true);
    await useProjections.getState().loadMore();
    expect(useProjections.getState().projections.map((item) => item.id)).toEqual(["p1", "p2"]);
    expect(fetcher.mock.calls[1][0]).toContain("offset=50");
  });

  it("dismisses presentation then reloads authoritative projections", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(response([row("p1")]))
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ success: true }) })
      .mockResolvedValueOnce(response([]));
    vi.stubGlobal("fetch", fetcher);
    await useProjections.getState().refresh(true);
    await useProjections.getState().present("p1", "dismiss");
    expect(fetcher.mock.calls[1][1].method).toBe("PUT");
    expect(useProjections.getState().projections).toEqual([]);
  });
});
