// HS-170-04 — stateToken: capture_status=recording liveness heuristic.
// REC for a likely-live capture (no ended_at, started within 6 h).
// INTERRUPTED for a dead session (ended_at set, or started > 6 h ago).
import { describe, expect, it } from "vitest";
import { stateToken } from "../helpers";

describe("stateToken capture liveness (HS-170-04)", () => {
  it("returns REC for a recording started within 6 hours, no ended_at", () => {
    const now = new Date();
    const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);
    const row = {
      capture_status: "recording",
      started_at: twoHoursAgo.toISOString(),
      ended_at: null,
    };
    const token = stateToken(row);
    expect(token.label).toBe("REC");
    expect(token.tone).toBe("danger");
  });

  it("returns INTERRUPTED for a recording started 21 days ago", () => {
    const now = new Date();
    const threeWeeksAgo = new Date(now.getTime() - 21 * 24 * 60 * 60 * 1000);
    const row = {
      capture_status: "recording",
      started_at: threeWeeksAgo.toISOString(),
      ended_at: null,
    };
    const token = stateToken(row);
    expect(token.label).toBe("INTERRUPTED");
    expect(token.tone).toBe("warn");
  });

  it("returns INTERRUPTED for a recording with ended_at set (even if recent)", () => {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 1 * 60 * 60 * 1000);
    const row = {
      capture_status: "recording",
      started_at: oneHourAgo.toISOString(),
      ended_at: now.toISOString(),
    };
    const token = stateToken(row);
    expect(token.label).toBe("INTERRUPTED");
    expect(token.tone).toBe("warn");
  });

  it("returns INTERRUPTED for a recording with no started_at", () => {
    const row = {
      capture_status: "recording",
      started_at: null,
      ended_at: null,
    };
    const token = stateToken(row);
    expect(token.label).toBe("INTERRUPTED");
    expect(token.tone).toBe("warn");
  });
});
