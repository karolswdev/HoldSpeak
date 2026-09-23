/** PHILO-3-01 round 2 (Astra condition 1) — save, close, reopen inside the
 * new-object marker, press Done: the text the owner saved is kept.
 * Drives the REAL store slice (createPrimitive, updatePrimitive, the
 * optimistic items patch); only the hub transport is a double. */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hub = vi.hoisted(() => ({
  decisions: [] as Array<Record<string, unknown>>,
  puts: [] as Array<Record<string, unknown>>,
}));

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const ok = (body: unknown, status = 200) =>
    Promise.resolve({ ok: true, status, json: () => Promise.resolve(body) });
  return {
    ...real,
    apiRequest: vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/decisions" && init?.method === "POST") {
        const decision = {
          id: "decision_keep", title: "New decision", status: "proposed", deciders: [],
          decided_at: null, context_markdown: "", decision_markdown: "", alternatives: [],
          consequences_markdown: "", tags: [], created_at: "2026-09-23T00:00:00Z",
          updated_at: "2026-09-23T00:00:00Z", deleted: false,
        };
        hub.decisions = [decision];
        return ok({ decision }, 201);
      }
      if (url === "/api/decisions/decision_keep" && init?.method === "PUT") {
        const patch = JSON.parse(String(init.body));
        hub.puts.push(patch);
        hub.decisions = [{ ...hub.decisions[0], ...patch }];
        return ok({ decision: hub.decisions[0] });
      }
      return ok({});
    }),
    apiFetch: vi.fn((url: string) =>
      Promise.resolve(url === "/api/decisions" ? { decisions: hub.decisions } : {}),
    ),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));

import { useDesk } from "../store";
import { objectByRef } from "../world";
import { DecisionPullout } from "../pullouts/DecisionPullout";

function Face() {
  const items = useDesk((s) => s.items);
  const o = objectByRef(items, "decision_keep");
  return o ? <DecisionPullout object={o} onClose={() => {}} /> : null;
}

beforeEach(() => {
  hub.decisions = [];
  hub.puts = [];
  useDesk.setState({ pullouts: [], editingId: null, newIds: [] });
});

describe("PHILO-3-01 no data loss on an immediate reopen", () => {
  it("save -> close -> reopen inside the marker -> Done keeps the text", async () => {
    await act(async () => {
      await useDesk.getState().createPrimitive("decision");
    });
    expect(useDesk.getState().newIds).toContain("decision_keep");

    const first = render(<Face />);
    fireEvent.change(screen.getByRole("textbox", { name: "Context" }), { target: { value: "Source: review" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Decision" }), { target: { value: "Adopt the bus" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Consequences" }), { target: { value: "One path" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Done" })); });
    first.unmount(); // close

    // reopen at once: the marker still stands
    expect(useDesk.getState().newIds).toContain("decision_keep");
    render(<Face />);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Done" })); });

    const last = hub.puts[hub.puts.length - 1];
    expect(last.context_markdown).toBe("Source: review");
    expect(last.decision_markdown).toBe("Adopt the bus");
    expect(last.consequences_markdown).toBe("One path");
    expect(hub.decisions[0].decision_markdown).toBe("Adopt the bus");
  });
});
