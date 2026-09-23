/** PHILO-3-01 round 2 (Astra condition 2) — a failed create keeps its
 * Retry when the read that follows also fails; after both recover, the
 * rendered Retry creates the record. Real store slice; hub transport double. */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hub = vi.hoisted(() => ({
  decisions: [] as Array<Record<string, unknown>>,
  failPost: false,
  failRead: false,
  posts: 0,
}));

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  return {
    ...real,
    apiRequest: vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/decisions" && init?.method === "POST") {
        hub.posts += 1;
        if (hub.failPost)
          return Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({ error: "x" }) });
        const decision = {
          id: "decision_retry", title: "New decision", status: "proposed", deciders: [],
          decided_at: null, context_markdown: "", decision_markdown: "", alternatives: [],
          consequences_markdown: "", tags: [], created_at: "2026-09-23T00:00:00Z",
          updated_at: "2026-09-23T00:00:00Z", deleted: false,
        };
        hub.decisions = [decision];
        return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ decision }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }),
    apiFetch: vi.fn((url: string) => {
      if (url === "/api/decisions") {
        if (hub.failRead) return Promise.reject({ status: 500, message: "read fault" });
        return Promise.resolve({ decisions: hub.decisions });
      }
      return Promise.resolve({});
    }),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));

import { useDesk } from "../store";
import { clearWriteFailure, useDeskWriteReceipt } from "../hooks/useWriteReceipt";

function ReceiptLine() {
  const { receipt } = useDeskWriteReceipt({ fallback: true });
  return <div data-testid="line">{receipt}</div>;
}

beforeEach(() => {
  hub.decisions = [];
  hub.failPost = false;
  hub.failRead = false;
  hub.posts = 0;
  clearWriteFailure();
  useDesk.setState({ pullouts: [], editingId: null, newIds: [] });
});

describe("PHILO-3-01 a read failure never takes a pending write's Retry", () => {
  it("create fails, read fails, both recover, Retry creates the record", async () => {
    render(<ReceiptLine />);
    hub.failPost = true;
    hub.failRead = true;
    await act(async () => {
      await useDesk.getState().createPrimitive("decision");
    });
    expect(hub.posts).toBe(1);
    expect(screen.getByTestId("line").textContent).toContain("CREATE DECISION FAILED · HTTP 500");

    // a later refresh that still fails keeps the write's receipt too
    await act(async () => { await useDesk.getState().refresh(); });
    expect(screen.getByTestId("line").textContent).toContain("CREATE DECISION FAILED");

    hub.failPost = false;
    hub.failRead = false;
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Retry" }));
      await new Promise((r) => setTimeout(r, 0));
    });
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    expect(hub.posts).toBe(2);
    expect(hub.decisions.map((d) => d.id)).toEqual(["decision_retry"]);
    expect(useDesk.getState().pullouts.map((p) => p.id)).toContain("decision_retry");
    expect(screen.getByTestId("line").textContent).toBe("");
  });
});
