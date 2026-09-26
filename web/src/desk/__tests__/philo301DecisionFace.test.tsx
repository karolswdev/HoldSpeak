/** PHILO-3-01 (A1) — New Decision opens the decision face; a failed read
 * is named on the desk receipt line; the first line of the decision text
 * replaces the default title. */
import { act, fireEvent, render, screen } from "@testing-library/react";
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
          id: "decision_new1", title: "New decision", status: "proposed",
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
import { DecisionPullout } from "../pullouts/DecisionPullout";
import type { WorldObject } from "../world";

beforeEach(() => {
  hub.decisions = [];
  hub.failDecisions = false;
  clearWriteFailure();
  useDesk.setState({ pullouts: [], editingId: null, newIds: [] });
});

describe("PHILO-3-01 the decision face", () => {
  it("New Decision opens the DecisionPullout for the created decision", async () => {
    await act(async () => {
      await useDesk.getState().createPrimitive("decision");
    });
    const s = useDesk.getState();
    expect(s.pullouts.map((p) => p.id)).toContain("decision_new1");
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

  it("a new decision opens in Edit; Done titles it from the first line", async () => {
    const update = vi.fn();
    useDesk.setState({ newIds: ["decision_new1"], updatePrimitive: update } as never);
    const o = {
      id: "decision_new1", kind: "decision", title: "New decision",
      ref: { id: "decision_new1", kind: "decision", title: "New decision", status: "proposed" },
    } as unknown as WorldObject;
    render(<DecisionPullout object={o} onClose={() => {}} />);
    const well = screen.getByRole("textbox", { name: "Decision" });
    fireEvent.change(well, { target: { value: "# Adopt the one bus\nfor every frame" } });
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(update).toHaveBeenCalledWith(
      "decision", "decision_new1",
      expect.objectContaining({ title: "Adopt the one bus", decision_markdown: "# Adopt the one bus\nfor every frame" }),
    );
  });

  it("an owner title is never replaced", () => {
    const update = vi.fn();
    useDesk.setState({ newIds: ["d2"], updatePrimitive: update } as never);
    const o = {
      id: "d2", kind: "decision", title: "Bus choice",
      ref: { id: "d2", kind: "decision", title: "Bus choice", status: "proposed" },
    } as unknown as WorldObject;
    render(<DecisionPullout object={o} onClose={() => {}} />);
    fireEvent.change(screen.getByRole("textbox", { name: "Decision" }), { target: { value: "Adopt it" } });
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(update.mock.calls[0][2]).not.toHaveProperty("title");
  });
});

describe("PHILO-8-04 the decision window shows no empty heading", () => {
  const decision = (fields: Record<string, string>) =>
    ({
      id: "d8", kind: "decision", title: "Glass decision",
      ref: { id: "d8", kind: "decision", title: "Glass decision", status: "proposed", ...fields },
    }) as unknown as WorldObject;
  const heads = () =>
    Array.from(document.querySelectorAll(".desk-decision-card h3")).map((h) => h.textContent);

  it("a title-only decision shows no heading; Edit offers all three fields", () => {
    render(<DecisionPullout object={decision({})} onClose={() => {}} />);
    expect(heads()).toEqual([]);
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    for (const name of ["Context", "Decision", "Consequences"]) {
      expect(screen.getByRole("textbox", { name })).toBeTruthy();
    }
  });

  it("only the fields with text show their heading", () => {
    render(
      <DecisionPullout
        object={decision({ contextMarkdown: "Runners are full.", consequencesMarkdown: "  " })}
        onClose={() => {}}
      />,
    );
    expect(heads()).toEqual(["Decision context"]);
  });

  it("all three fields with text show all three headings", () => {
    render(
      <DecisionPullout
        object={decision({ contextMarkdown: "C", decisionMarkdown: "D", consequencesMarkdown: "Q" })}
        onClose={() => {}}
      />,
    );
    expect(heads()).toEqual(["Decision context", "Decision", "Consequences"]);
  });
});
