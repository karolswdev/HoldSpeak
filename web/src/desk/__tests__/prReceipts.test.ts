// HS-104-04 — PR receipts store: label honesty and the wire verbs.
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  attributionLabel,
  prStateLabel,
  usePrReceipts,
  type PrRow,
} from "../prReceipts";

const apiFetch = vi.fn();
vi.mock("../../lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

const row = (extra: Partial<PrRow>): PrRow => ({
  source_id: "src_1",
  number: 42,
  title: "t",
  url: "https://github.com/o/r/pull/42",
  head_ref: "b",
  base_ref: "main",
  head_sha: "a".repeat(40),
  base_sha: "b".repeat(40),
  state: "open",
  ci: "passing",
  author: "k",
  observed_at: "2026-07-26T18:00:00Z",
  attribution: "none",
  basis: "no worktree or attempt match",
  ...extra,
});

describe("PR receipt labels", () => {
  it("attribution never claims more than the match", () => {
    expect(attributionLabel(row({ attribution: "exact" }))).toBe("exact");
    expect(attributionLabel(row({ attribution: "heuristic" }))).toBe("name match");
    expect(attributionLabel(row({ attribution: "none" }))).toBe("unattributed");
  });

  it("state label carries the CI conclusion, not the logs", () => {
    expect(prStateLabel(row({ ci: "failing" }))).toBe("open · CI failing");
    expect(prStateLabel(row({ ci: "pending" }))).toBe("open · CI running");
    expect(prStateLabel(row({ ci: "passing" }))).toBe("open · CI green");
    expect(prStateLabel(row({ state: "merged" }))).toBe("merged");
  });
});

describe("PR receipts store", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    usePrReceipts.setState({ sources: [], loaded: false, busy: false });
  });

  it("load reads the cached rows and refresh POSTs the verb", async () => {
    apiFetch.mockResolvedValueOnce({ sources: [{ source_id: "s", prs: null }] });
    await usePrReceipts.getState().load();
    expect(apiFetch).toHaveBeenCalledWith("/api/delivery/prs");
    expect(usePrReceipts.getState().sources).toHaveLength(1);

    apiFetch.mockResolvedValueOnce({ sources: [] });
    await usePrReceipts.getState().refresh();
    expect(apiFetch).toHaveBeenLastCalledWith("/api/delivery/prs/refresh", {
      method: "POST",
    });
  });

  it("diff hits the read-only route and failure is typed", async () => {
    apiFetch.mockResolvedValueOnce({ status: "ok", diff: "d" });
    const ok = await usePrReceipts.getState().diff("s", 42);
    expect(ok.status).toBe("ok");
    expect(apiFetch).toHaveBeenCalledWith("/api/delivery/prs/s/42/diff");

    apiFetch.mockRejectedValueOnce(new Error("boom"));
    const bad = await usePrReceipts.getState().diff("s", 42);
    expect(bad.status).toBe("failed");
  });
});
