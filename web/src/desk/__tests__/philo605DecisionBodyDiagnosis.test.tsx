/**
 * PHILO-6-05 diagnosis probe. It drives the real dataSlice updatePrimitive
 * through a subscribed host and records the store/render result after Done.
 * One held-WorldObject case remains as an explicit synthetic negative
 * control; it is not a production-host diagnosis.
 */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const requests = vi.hoisted(() => ({
  deferDecisionRead: false,
  resolveDecisionRead: null as (() => void) | null,
  failDecisionRead: false,
  deferPut: false,
  putResolvers: [] as Array<(status?: number) => void>,
  calls: [] as Array<{ input: string; method: string }>,
  failPut: false,
}));

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const wireDecision = {
    id: "decision_probe",
    title: "New decision",
    status: "proposed",
    deciders: [],
    decided_at: null,
    context_markdown: "",
    decision_markdown: "",
    alternatives: [],
    consequences_markdown: "",
    superseded_by: null,
    tags: [],
    created_at: "2026-09-24T00:00:00Z",
  };
  const response = (body: unknown, status = 200) => ({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  });
  return {
    ...real,
    apiRequest: vi.fn((input: string, init?: RequestInit) => {
      const method = String(init?.method || "GET").toUpperCase();
      requests.calls.push({ input, method });
      if (method === "PUT") {
        const status = requests.failPut ? 500 : 200;
        if (requests.deferPut) {
          return new Promise((resolve) => {
            requests.putResolvers.push((resolvedStatus = status) =>
              resolve(response({}, resolvedStatus)),
            );
          });
        }
        return Promise.resolve(response({}, status));
      }
      if (input === "/api/decisions") {
        if (requests.failDecisionRead) {
          return Promise.reject(new Error("decision read unavailable"));
        }
        if (requests.deferDecisionRead) {
          return new Promise((resolve) => {
            requests.resolveDecisionRead = () => resolve(response({ decisions: [wireDecision] }));
          });
        }
        return Promise.resolve(response({ decisions: [wireDecision] }));
      }
      if (input === "/api/setup/status") return Promise.resolve(response({}));
      if (input === "/api/inference-targets") return Promise.resolve(response({ targets: [] }));
      return Promise.resolve(response({}));
    }),
    apiFetch: vi.fn((input: string) => {
      if (input === "/api/decisions") {
        if (requests.failDecisionRead) {
          return Promise.reject(new Error("decision read unavailable"));
        }
        if (requests.deferDecisionRead) {
          return new Promise((resolve) => {
            requests.resolveDecisionRead = () => resolve({ decisions: [wireDecision] });
          });
        }
        return Promise.resolve({ decisions: [wireDecision] });
      }
      if (input === "/api/inference-targets") return Promise.resolve({ targets: [] });
      if (input === "/api/setup/status") return Promise.resolve({});
      return Promise.resolve({});
    }),
  };
});

import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { objectByRef, type WorldObject } from "../world";
import { DecisionPullout } from "../pullouts/DecisionPullout";
import { Pullout } from "../components/Pullout";
import { DeskReceiptRow } from "../components/DeskReceiptRow";
import {
  clearWriteFailure,
  currentWriteFailure,
} from "../hooks/useWriteReceipt";

const decision = {
  kind: "decision" as const,
  id: "decision_probe",
  title: "New decision",
  status: "proposed" as const,
  deciders: [],
  decidedAt: undefined,
  contextMarkdown: "",
  decisionMarkdown: "",
  alternatives: [],
  consequencesMarkdown: "",
  supersededBy: undefined,
  tags: [],
  createdAt: "2026-09-24T00:00:00Z",
};

function heldObject(): WorldObject {
  const object = objectByRef(useDesk.getState().items, decision.id);
  if (!object) throw new Error("diagnosis decision missing from store");
  return object;
}

/** The same live host projection used by DeskApp (lines 80, 133–135). */
function ProductionHost() {
  const items = useDesk((s) => s.items);
  const object = objectByRef(items, decision.id);
  return (
    <>
      {object ? <Pullout o={object} /> : null}
      <DeskReceiptRow />
    </>
  );
}

beforeEach(() => {
  clearWriteFailure();
  requests.deferDecisionRead = false;
  requests.resolveDecisionRead = null;
  requests.failDecisionRead = false;
  requests.deferPut = false;
  requests.putResolvers = [];
  requests.calls = [];
  requests.failPut = false;
  useDesk.setState({
    items: { ...EMPTY_ITEMS, decision: [decision] },
    newIds: [decision.id],
    pullouts: [],
    editingId: null,
  });
});

/** PHILO-8-04 — the read view's "Decision" section, found by its heading
 * (an empty field draws no heading, so a position is not stable). */
function decisionSection(): Element | undefined {
  return Array.from(document.querySelectorAll(".desk-decision-card > section")).find(
    (section) => section.querySelector("h3")?.textContent === "Decision",
  );
}

describe("PHILO-6-05 decision body fences", () => {
  it("rolls a failed save back to the prior body before a slow refresh resolves", async () => {
    const prior = { ...decision, decisionMarkdown: "Prior saved decision" };
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [prior] }, newIds: [] });
    render(<ProductionHost />);

    requests.failPut = true;
    requests.deferDecisionRead = true;
    let save!: Promise<void>;
    act(() => {
      save = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "Rejected new decision",
      });
    });
    await waitFor(() => expect(currentWriteFailure()?.verb).toBe("SAVE"));
    const body = decisionSection();
    expect(document.querySelector(".write-receipt-label")?.textContent).toContain(
      "SAVE FAILED",
    );
    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe("Prior saved decision");
    expect(body?.textContent).toContain("Prior saved decision");
    expect(body?.textContent).not.toContain("Rejected new decision");
    requests.resolveDecisionRead?.();
    await act(async () => {
      await save;
    });
  });

  it("keeps the prior body when a refused save's refresh fails", async () => {
    const prior = { ...decision, decisionMarkdown: "Prior saved decision" };
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [prior] }, newIds: [] });
    render(<ProductionHost />);

    requests.failPut = true;
    requests.failDecisionRead = true;
    let save!: Promise<void>;
    act(() => {
      save = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "Rejected new decision",
      });
    });
    await waitFor(() => expect(currentWriteFailure()?.verb).toBe("SAVE"));
    const body = decisionSection();
    expect(document.querySelector(".write-receipt-label")?.textContent).toContain(
      "SAVE FAILED",
    );
    expect(useDesk.getState().items.decision[0]?.decisionMarkdown).toBe(
      "Prior saved decision",
    );
    expect(body?.textContent).toContain("Prior saved decision");
    expect(body?.textContent).not.toContain("Rejected new decision");
    await act(async () => {
      await save;
    });
    // The failed rollback read has now committed, not merely posted a receipt.
    expect(useDesk.getState().items.decision[0]?.decisionMarkdown).toBe(
      "Prior saved decision",
    );
    expect(body?.textContent).toContain("Prior saved decision");
    expect(document.querySelector(".write-receipt-label")?.textContent).toContain(
      "SAVE FAILED",
    );
  });

  it("negative control: a held pullout prop stays stale after the store write", async () => {
    const object = heldObject();
    render(<DecisionPullout object={object} onClose={() => {}} />);

    fireEvent.change(screen.getByRole("textbox", { name: "Decision" }), {
      target: { value: "Keep the local ledger" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Done" }));
    });

    const stored = useDesk.getState().items.decision[0];
    const sections = [undefined, decisionSection()];
    const held = sections[1];
    // The real store producer has the value before the request resolves.
    expect(stored.decisionMarkdown).toBe("Keep the local ledger");
    // The held prop intentionally carries the old record. This synthetic
    // control stays green and must not be cited as the production cause.
    // PHILO-8-04: the old record's decision is empty, so its heading hides.
    expect(held).toBeUndefined();
  });

  it("does not reproduce when the production host derives the object from items", async () => {
    render(<ProductionHost />);

    fireEvent.change(screen.getByRole("textbox", { name: "Decision" }), {
      target: { value: "Keep the local ledger" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Done" }));
    });

    const sections = [undefined, decisionSection()];
    // This is the production-host control: if it fails, inspect refresh or
    // host/window caching rather than assuming a stale prop.
    expect(sections[1]?.textContent).toContain("Keep the local ledger");
  });

  it("keeps an optimistic body when a pre-write refresh resolves", async () => {
    render(<ProductionHost />);
    requests.deferDecisionRead = true;
    const refresh = useDesk.getState().refresh();
    // Let loadAll start the deferred /api/decisions read before Done.
    await waitFor(() => {
      if (!requests.resolveDecisionRead) throw new Error(JSON.stringify(requests.calls));
    });

    fireEvent.change(screen.getByRole("textbox", { name: "Decision" }), {
      target: { value: "Keep the local ledger" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Done" }));
    });
    const liveSections = [undefined, decisionSection()];
    expect(liveSections[1]?.textContent).toContain("Keep the local ledger");
    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe("Keep the local ledger");

    await act(async () => {
      requests.resolveDecisionRead?.();
      await refresh;
    });
    const staleSections = [undefined, decisionSection()];
    // This is the red acceptance assertion: a refresh that began before the
    // write must not replace the newer optimistic item when it resolves.
    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe(
      "Keep the local ledger",
    );
    expect(staleSections[1]?.textContent).toContain("Keep the local ledger");
  });

  it("keeps an optimistic body when a refresh starts during a pending write", async () => {
    useDesk.setState({ newIds: [] });
    render(<ProductionHost />);
    requests.deferPut = true;
    let save!: Promise<void>;
    act(() => {
      save = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "Keep the local ledger",
      });
    });
    await waitFor(() => expect(requests.putResolvers).toHaveLength(1));

    requests.deferDecisionRead = true;
    const refresh = useDesk.getState().refresh();
    await waitFor(() => expect(requests.resolveDecisionRead).not.toBeNull());

    requests.putResolvers.shift()?.(200);
    requests.resolveDecisionRead?.();
    await act(async () => {
      await Promise.all([save, refresh]);
    });

    const sections = [undefined, decisionSection()];
    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe(
      "Keep the local ledger",
    );
    expect(sections[1]?.textContent).toContain("Keep the local ledger");
  });

  it("does not let an older refusal roll back or receipt a newer decision write", async () => {
    useDesk.setState({ newIds: [] });
    render(<ProductionHost />);
    requests.deferPut = true;
    requests.deferDecisionRead = true;
    let firstSave!: Promise<void>;
    act(() => {
      firstSave = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "First decision",
      });
    });
    await waitFor(() => expect(requests.putResolvers).toHaveLength(1));
    let secondSave!: Promise<void>;
    act(() => {
      secondSave = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "Second decision",
      });
    });
    await waitFor(() => expect(requests.putResolvers).toHaveLength(2));

    // The newer write lands first. The older refusal must not leave a Retry
    // that can replay its superseded patch.
    requests.putResolvers[1]?.(200);
    await act(async () => {
      await secondSave;
    });
    requests.putResolvers[0]?.(500);
    await act(async () => {
      await Promise.resolve();
    });
    // The pre-fix store starts a stale refresh; release it so the red result
    // is semantic rather than a hanging promise. The fenced store skips it.
    requests.resolveDecisionRead?.();
    await act(async () => {
      await firstSave;
    });

    const sections = [undefined, decisionSection()];
    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe(
      "Second decision",
    );
    expect(sections[1]?.textContent).toContain("Second decision");
    expect(document.querySelector(".write-receipt-label")).toBeNull();
  });
});
