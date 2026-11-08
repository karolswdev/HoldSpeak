/** PHILO-3-01 (A1) — New Decision opens the decision face; a failed read
 * is named on the desk receipt line. */
import { act, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hub = vi.hoisted(() => ({
  decisions: [] as Array<Record<string, unknown>>,
  failDecisions: false,
}));

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  return {
    ...real,
    apiRequest: vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/decisions" && init?.method === "POST") {
        const decision = {
          id: "decision_new1", title: "Adopt the one bus", status: "proposed",
          deciders: [], decided_at: null, context_markdown: "", decision_markdown: "",
          alternatives: [], consequences_markdown: "", tags: [],
          created_at: "2026-09-22T00:00:00Z", updated_at: "2026-09-22T00:00:00Z", deleted: false,
        };
        hub.decisions = [decision];
        return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ decision }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }),
    apiFetch: vi.fn((url: string) => {
      if (url === "/api/decisions") {
        if (hub.failDecisions) return Promise.reject({ status: 500, message: "boom" });
        return Promise.resolve({ decisions: hub.decisions });
      }
      return Promise.resolve({});
    }),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));

import { useDesk } from "../store";
import { currentWriteFailure, clearWriteFailure } from "../hooks/useWriteReceipt";

beforeEach(() => {
  hub.decisions = [];
  hub.failDecisions = false;
  clearWriteFailure();
  useDesk.setState({ pullouts: [], editingId: null, newIds: [] });
});

describe("PHILO-3-01 the decision face", () => {
  it("New Decision on an older hub opens the Decisions window, never the Decision pullout", async () => {
    await act(async () => {
      // PHILO-13-08 (B3): a decision is created only once it is named.
      await useDesk.getState().createPrimitive("decision", { title: "Adopt the one bus" });
    });
    // The one decision face (2026-11-08): with no record in the create
    // answer, the decision opens through its record lookup, in the
    // Decisions window.
    await waitFor(() => expect(useDesk.getState().windowsById["surface-decisions"]).toBeTruthy());
    const s = useDesk.getState();
    expect(s.pullouts.map((p) => p.id)).not.toContain("decision_new1");
    expect(s.editingId).toBeNull();
    expect(s.newIds).toContain("decision_new1");
  });

  it("a failed decisions read is named with Retry; a clean read clears it", async () => {
    hub.failDecisions = true;
    await act(async () => { await useDesk.getState().refresh(); });
    const failure = currentWriteFailure();
    expect(failure?.verb).toBe("READ DECISIONS");
    expect(failure?.reason).toBe("HTTP 500");
    expect(failure?.retry).toBeTypeOf("function");
    hub.failDecisions = false;
    await act(async () => { await useDesk.getState().refresh(); });
    expect(currentWriteFailure()).toBeNull();
  });
});

// The first-line title and the owner's own title are fenced on the reader's
// editor (decision.app.test.tsx); the pullout's cases are parked with it
// (pullouts/_parked/__tests__/philo301DecisionFace.test.tsx).
