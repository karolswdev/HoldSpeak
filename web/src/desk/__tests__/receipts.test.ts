// HS-104-05 — the receipt line's tier legibility: a reader can tell
// which tier a number belongs to from the glass alone, and an absent
// tier never renders as zero.
import { describe, expect, it, vi } from "vitest";
import { receiptSegments, type SessionReceipt } from "../receipts";

vi.mock("../../lib/api", () => ({ apiFetch: vi.fn() }));

const base: SessionReceipt = {
  receipt_schema: 1,
  session_key: "claude:s1",
  always: {
    provenance: "hub records",
    elapsed_seconds: 754,
    steers_delivered: 3,
    steers_refused: 1,
    holds: { held: 0, approved: 2, denied: 1, expired: 0, invalidated: 0 },
  },
  tools: [{ tool: "Bash", samples: 3, max_seconds: 9.5 }],
};

describe("receiptSegments", () => {
  it("always tier is bare hub records; below-floor tools show count and max", () => {
    const segments = receiptSegments(base);
    expect(segments).toContain("12m 34s");
    expect(segments).toContain("3 of 4 steers landed");
    expect(segments).toContain("3 holds");
    expect(segments).toContain("Bash holds 3, max 9.5s");
    expect(segments.join(" ")).not.toMatch(/\$|tokens/);
  });

  it("reported tier is labeled and keeps cache figures separate", () => {
    const segments = receiptSegments({
      ...base,
      reported: {
        provenance: "authoritative",
        model: "claude-fable-5",
        input_tokens: 1000,
        output_tokens: 2000,
        cache_read_tokens: 500,
        cache_creation_tokens: 250,
        reported_at: "2026-07-26T18:00:00Z",
      },
    });
    const tokens = segments.find((s) => s.startsWith("tokens"));
    expect(tokens).toBe(
      "tokens in 1,000 · out 2,000 · cache read 500 · cache new 250 (reported)",
    );
  });

  it("estimate wears the marker, the source, and the date; absent price = no line", () => {
    const segments = receiptSegments({
      ...base,
      estimated: {
        provenance: "price table",
        cost_usd: 4.5,
        source: "price table",
        as_of: "2026-07-26",
      },
    });
    expect(segments).toContain("≈ $4.50 (price table, 2026-07-26)");
    expect(receiptSegments(base).join(" ")).not.toContain("$");
  });

  it("at the sample floor the percentiles replace count and max", () => {
    const segments = receiptSegments({
      ...base,
      tools: [{ tool: "Bash", samples: 20, p50_seconds: 3.1, p95_seconds: 9.9 }],
    });
    expect(segments).toContain("Bash holds p50 3.1s · p95 9.9s (20)");
  });
});
