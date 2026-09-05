// HS-173-03/04/05 — vitest for the health row resolver and nudge card state machine.
// Pure function tests: no DOM, no React.

import { describe, it, expect } from "vitest";
import {
  resolveHealthRows,
  nudgeCardReducer,
  formatDays,
  type RoomHealthSignals,
  type NudgeCardState,
} from "./model";

/* ── resolveHealthRows ── */

describe("resolveHealthRows", () => {
  it("returns empty when signals undefined", () => {
    expect(resolveHealthRows(undefined, 0)).toEqual([]);
  });

  it("returns empty when no signal is present", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: false, tone: "green", agedCount: 0 },
      ci: { present: false, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: false, tone: "green", composite: "green", blockersCount: 0 },
    };
    expect(resolveHealthRows(signals, 0)).toEqual([]);
  });

  it("produces REVIEW WAIT row with tone and tokens", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: true, tone: "red", medianDays: 3.2, waitingCount: 3 },
      issueAging: { present: false, tone: "green", agedCount: 0 },
      ci: { present: false, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: false, tone: "green", composite: "green", blockersCount: 0 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows).toHaveLength(1);
    expect(rows[0].key).toBe("review_wait");
    expect(rows[0].label).toBe("REVIEW WAIT");
    expect(rows[0].tone).toBe("red");
    expect(rows[0].tokens).toEqual(["3.2 D MEDIAN", "3 WAITING"]);
  });

  it("produces ISSUE AGING CLEAR at zero aged", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: true, tone: "green", agedCount: 0 },
      ci: { present: false, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: false, tone: "green", composite: "green", blockersCount: 0 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows).toHaveLength(1);
    expect(rows[0].key).toBe("issue_aging");
    expect(rows[0].tokens).toEqual(["CLEAR"]);
    expect(rows[0].tone).toBe("green");
  });

  it("produces ISSUE AGING count when aged > 0", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: true, tone: "amber", agedCount: 4, thresholdDays: 14 },
      ci: { present: false, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: false, tone: "green", composite: "green", blockersCount: 0 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows[0].tokens).toEqual(["4 > 14 D"]);
    expect(rows[0].tone).toBe("amber");
  });

  it("produces CI with FLAKY and QUEUE tokens, absent at zero", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: false, tone: "green", agedCount: 0 },
      ci: { present: true, tone: "amber", flakyCount: 2, failuresLast3: 1 },
      release: { present: false, tone: "green", composite: "green", blockersCount: 0 },
    };
    const rows = resolveHealthRows(signals, 3);
    expect(rows).toHaveLength(1);
    expect(rows[0].key).toBe("ci");
    expect(rows[0].tone).toBe("amber");
    expect(rows[0].tokens).toEqual(["2 FLAKY", "QUEUE 3"]);
  });

  it("produces CI PASSING when zero flaky and zero queue", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: false, tone: "green", agedCount: 0 },
      ci: { present: true, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: false, tone: "green", composite: "green", blockersCount: 0 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows[0].tokens).toEqual(["PASSING"]);
  });

  it("produces RELEASE READY when composite green", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: false, tone: "green", agedCount: 0 },
      ci: { present: false, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: true, tone: "green", composite: "green", blockersCount: 0 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows[0].key).toBe("release");
    expect(rows[0].tokens).toEqual(["READY"]);
  });

  it("produces RELEASE N BLOCKERS when composite red", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: false, tone: "green", agedCount: 0 },
      ci: { present: false, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: true, tone: "red", composite: "red", blockersCount: 2 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows[0].tokens).toEqual(["2 BLOCKERS"]);
    expect(rows[0].tone).toBe("red");
  });

  it("produces RELEASE 1 BLOCKER singular", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: false, tone: "green", medianDays: 0, waitingCount: 0 },
      issueAging: { present: false, tone: "green", agedCount: 0 },
      ci: { present: false, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: true, tone: "red", composite: "red", blockersCount: 1 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows[0].tokens).toEqual(["1 BLOCKER"]);
  });

  it("formatDays: integer shows whole, decimal shows one place", () => {
    expect(formatDays(3)).toBe("3");
    expect(formatDays(1.5)).toBe("1.5");
    expect(formatDays(0)).toBe("0");
    expect(formatDays(2.04)).toBe("2");
    expect(formatDays(2.05)).toBe("2.1");
  });

  it("all-green produces four rows with CLEAR/PASSING/READY", () => {
    const signals: RoomHealthSignals = {
      reviewWait: { present: true, tone: "green", medianDays: 1, waitingCount: 1 },
      issueAging: { present: true, tone: "green", agedCount: 0 },
      ci: { present: true, tone: "green", flakyCount: 0, failuresLast3: 0 },
      release: { present: true, tone: "green", composite: "green", blockersCount: 0 },
    };
    const rows = resolveHealthRows(signals, 0);
    expect(rows).toHaveLength(4);
    const labels = rows.map((r) => r.key);
    expect(labels).toEqual(["review_wait", "issue_aging", "ci", "release"]);
    // All green
    expect(rows.every((r) => r.tone === "green")).toBe(true);
    // CLEAR, PASSING, READY present
    expect(rows[1].tokens).toEqual(["CLEAR"]);
    expect(rows[2].tokens).toEqual(["PASSING"]);
    expect(rows[3].tokens).toEqual(["READY"]);
  });
});

/* ── nudgeCardReducer ── */

describe("nudgeCardReducer", () => {
  it("starts closed", () => {
    const state: NudgeCardState = { phase: "closed" };
    expect(state.phase).toBe("closed");
  });

  it("opens with default text", () => {
    const state = nudgeCardReducer(
      { phase: "closed" },
      { type: "open", defaultText: "Please review" },
    );
    expect(state.phase).toBe("open");
    if (state.phase === "open") {
      expect(state.text).toBe("Please review");
      expect(state.busy).toBe(false);
    }
  });

  it("setText updates text", () => {
    const state = nudgeCardReducer(
      { phase: "open", text: "old", busy: false },
      { type: "setText", text: "new" },
    );
    if (state.phase === "open") {
      expect(state.text).toBe("new");
    }
  });

  it("sending sets busy", () => {
    const state = nudgeCardReducer(
      { phase: "open", text: "msg", busy: false },
      { type: "sending" },
    );
    if (state.phase === "open") {
      expect(state.busy).toBe(true);
    }
  });

  it("sent transitions to receipt", () => {
    const state = nudgeCardReducer(
      { phase: "open", text: "msg", busy: true },
      { type: "sent", displayName: "Ania", prNumber: 612, sentAt: "2026-09-05T18:02:00Z" },
    );
    expect(state.phase).toBe("sent");
    if (state.phase === "sent") {
      expect(state.displayName).toBe("Ania");
      expect(state.prNumber).toBe(612);
    }
  });

  it("failed keeps text and shows reason", () => {
    const state = nudgeCardReducer(
      { phase: "open", text: "msg", busy: true },
      { type: "failed", reason: "Auth error" },
    );
    expect(state.phase).toBe("failed");
    if (state.phase === "failed") {
      expect(state.text).toBe("msg");
      expect(state.reason).toBe("Auth error");
    }
  });

  it("dismiss returns to closed", () => {
    const state = nudgeCardReducer(
      { phase: "open", text: "msg", busy: false },
      { type: "dismiss" },
    );
    expect(state.phase).toBe("closed");
  });

  it("setText from failed reopens", () => {
    const state = nudgeCardReducer(
      { phase: "failed", text: "old", reason: "err" },
      { type: "setText", text: "retry" },
    );
    expect(state.phase).toBe("open");
    if (state.phase === "open") {
      expect(state.text).toBe("retry");
    }
  });
});
