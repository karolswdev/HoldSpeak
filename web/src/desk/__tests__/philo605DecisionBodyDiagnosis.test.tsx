/**
 * PHILO-6-05 diagnosis probe. It drives the real dataSlice updatePrimitive
 * (the write the reader's Save makes, views/DeskDecisionEdit.tsx) through a
 * host subscribed to the desk's items and records the store/render result.
 * The Decision pullout is parked (2026-11-08, the one decision face); its
 * held-object negative control is parked with it
 * (pullouts/_parked/__tests__/philo605DecisionBodyDiagnosis.test.tsx).
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const requests = vi.hoisted(() => ({
  deferDecisionRead: false,
  resolveDecisionRead: null as (() => void) | null,
  failDecisionRead: false,
  decisionReadStatus: 200,
  emptyDecisionRead: false,
  failMeetingRead: false,
  failWorkbenchRead: false,
  deferPut: false,
  putResolvers: [] as Array<(status?: number) => void>,
  calls: [] as Array<{ input: string; method: string }>,
  failPut: false,
}));

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<typeof import("../../lib/api")>();
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
      if (input.startsWith("/api/meetings") && requests.failMeetingRead) {
        return Promise.reject(new real.ApiError(503, "meeting read unavailable", {}));
      }
      if (input === "/api/decisions") {
        if (requests.decisionReadStatus !== 200) {
          return Promise.reject(new real.ApiError(requests.decisionReadStatus, "decision access refused", {}));
        }
        if (requests.failDecisionRead) {
          return Promise.reject(new Error("decision read unavailable"));
        }
        if (requests.deferDecisionRead) {
          return new Promise((resolve) => {
            requests.resolveDecisionRead = () => resolve({ decisions: [wireDecision] });
          });
        }
        return Promise.resolve({ decisions: requests.emptyDecisionRead ? [] : [wireDecision] });
      }
      if (input === "/api/workbenches" && requests.failWorkbenchRead) {
        return Promise.reject(new real.ApiError(503, "workbench read unavailable", {}));
      }
      if (input === "/api/inference-targets") return Promise.resolve({ targets: [] });
      if (input === "/api/setup/status") return Promise.resolve({});
      return Promise.resolve({});
    }),
  };
});

import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
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

/** A host subscribed to the desk's items, as every decision face is: it
 *  draws the decision body the store holds, beside the desk's receipt line. */
function ProductionHost() {
  const body = useDesk((s) => s.items.decision.find((item) => item.id === decision.id)?.decisionMarkdown ?? "");
  return (
    <>
      {body ? <section aria-label="Decision">{body}</section> : null}
      <DeskReceiptRow />
    </>
  );
}

/** The reader's Save: one decision write through the store. The press does
 *  not wait for the write's answer, so neither does this. */
async function save(words: string) {
  await act(async () => {
    void useDesk.getState().updatePrimitive("decision", decision.id, { decision_markdown: words });
  });
}

beforeEach(() => {
  clearWriteFailure();
  requests.deferDecisionRead = false;
  requests.resolveDecisionRead = null;
  requests.failDecisionRead = false;
  requests.decisionReadStatus = 200;
  requests.emptyDecisionRead = false;
  requests.failMeetingRead = false;
  requests.failWorkbenchRead = false;
  requests.deferPut = false;
  requests.putResolvers = [];
  requests.calls = [];
  requests.failPut = false;
  useDesk.setState({
    items: { ...EMPTY_ITEMS, decision: [decision] },
    newIds: [decision.id],
    pullouts: [],
    editingId: null,
    status: {},
    error: "",
  });
});

describe("shared collection read truth", () => {
  it("keeps every known workbench through a failed collection read and names Retry", async () => {
    const workbenches = [
      { kind: "workbench" as const, id: "workbench_probe", name: "Ledger", createdAt: "" },
      { kind: "workbench" as const, id: "workbench_other", name: "Reports", createdAt: "" },
    ];
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [decision], workbench: workbenches } });
    requests.failWorkbenchRead = true;

    await useDesk.getState().refresh();

    expect(useDesk.getState().items.workbench).toEqual(workbenches);
    expect(useDesk.getState().status.workbench).toBe("unreachable");
    expect(useDesk.getState().error).toBe("Automations: workbench read unavailable");
    expect(currentWriteFailure()?.verb).toBe("READ AUTOMATIONS");
    expect(currentWriteFailure()?.reason).toBe("HTTP 503");
    expect(currentWriteFailure()?.retry).toBeTypeOf("function");
    expect(useDesk.getState().status.decision).toBe("live");
    expect(useDesk.getState().loading).toBe(false);
  });

  it("keeps an ordinary saved decision when its collection is unavailable", async () => {
    const saved = { ...decision, decisionMarkdown: "Keep the ledger local" };
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [saved] } });
    requests.failDecisionRead = true;

    await useDesk.getState().refresh();

    expect(useDesk.getState().items.decision).toEqual([saved]);
    expect(useDesk.getState().status.decision).toBe("unreachable");
    expect(useDesk.getState().error).toBe("Decisions: decision read unavailable");
    expect(currentWriteFailure()?.verb).toBe("READ DECISIONS");
  });

  it.each([401, 403])("keeps HTTP %s authorization refusals authoritative", async (status) => {
    requests.decisionReadStatus = status;

    await useDesk.getState().refresh();

    expect(useDesk.getState().items.decision).toEqual([]);
    expect(useDesk.getState().status.decision).toBe("unreachable");
    expect(currentWriteFailure()?.verb).toBe("READ DECISIONS");
    expect(currentWriteFailure()?.reason).toBe(`HTTP ${status}`);
  });

  it("retains a transient bucket without retaining a refused bucket when the first failure is HTTP 503", async () => {
    const workbench = { kind: "workbench" as const, id: "mixed_probe", name: "Ledger", createdAt: "" };
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [decision], workbench: [workbench] } });
    requests.failMeetingRead = true;
    requests.failWorkbenchRead = true;
    requests.decisionReadStatus = 403;

    await useDesk.getState().refresh();

    expect(useDesk.getState().items.workbench).toEqual([workbench]);
    expect(useDesk.getState().items.decision).toEqual([]);
    expect(useDesk.getState().status).toMatchObject({ meeting: "unreachable", workbench: "unreachable", decision: "unreachable" });
    expect(useDesk.getState().error).toBe("Meetings: meeting read unavailable");
    expect(currentWriteFailure()?.verb).toBe("READ MEETINGS");
    expect(currentWriteFailure()?.reason).toBe("HTTP 503");
  });

  it("clears a retained bucket after an authoritative successful empty read", async () => {
    requests.failDecisionRead = true;
    await useDesk.getState().refresh();
    expect(useDesk.getState().items.decision).toEqual([decision]);

    requests.failDecisionRead = false;
    requests.emptyDecisionRead = true;
    await useDesk.getState().refresh();

    expect(useDesk.getState().items.decision).toEqual([]);
    expect(useDesk.getState().status.decision).toBe("live");
    expect(useDesk.getState().error).toBe("");
    expect(currentWriteFailure()).toBeNull();
  });
});

/** The read view's "Decision" paper, found by its accessible name
 * (an empty field draws no heading, so a position is not stable). */
function expectSaid(words: string) {
  expect(decisionSection()?.textContent).toContain(words);
}

function decisionSection(): Element | undefined {
  return screen.queryByRole("region", { name: "Decision" }) ?? undefined;
}

describe("PHILO-6-05 decision body fences", () => {
  it("rolls a failed save back to the prior body before a slow refresh resolves", async () => {
    const prior = { ...decision, decisionMarkdown: "Prior saved decision" };
    useDesk.setState({ items: { ...EMPTY_ITEMS, decision: [prior] }, newIds: [] });
    render(<ProductionHost />);

    requests.failPut = true;
    requests.deferDecisionRead = true;
    let save!: Promise<unknown>; // updatePrimitive answers kept (PHILO-13-07 B2)
    act(() => {
      save = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "Rejected new decision",
      });
    });
    await waitFor(() => expect(currentWriteFailure()?.verb).toBe("SAVE"));
    const body = decisionSection();
    expect(document.querySelector(".write-receipt-label")?.textContent).toContain(
      "Could not save the decision",
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
    let save!: Promise<unknown>; // updatePrimitive answers kept (PHILO-13-07 B2)
    act(() => {
      save = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "Rejected new decision",
      });
    });
    await waitFor(() => expect(currentWriteFailure()?.verb).toBe("SAVE"));
    const body = decisionSection();
    expect(document.querySelector(".write-receipt-label")?.textContent).toContain(
      "Could not save the decision",
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
      "Could not save the decision",
    );
  });

  it("does not reproduce when the production host derives the object from items", async () => {
    render(<ProductionHost />);

    await save("Keep the local ledger");

    // This is the production-host control: if it fails, inspect refresh or
    // host/window caching rather than assuming a stale prop.
    expectSaid("Keep the local ledger");
  });

  it("keeps an optimistic body when a pre-write refresh resolves", async () => {
    render(<ProductionHost />);
    requests.deferDecisionRead = true;
    const refresh = useDesk.getState().refresh();
    // Let loadAll start the deferred /api/decisions read before Save.
    await waitFor(() => {
      if (!requests.resolveDecisionRead) throw new Error(JSON.stringify(requests.calls));
    });

    await save("Keep the local ledger");
    expectSaid("Keep the local ledger");
    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe("Keep the local ledger");

    await act(async () => {
      requests.resolveDecisionRead?.();
      await refresh;
    });
    // This is the red acceptance assertion: a refresh that began before the
    // write must not replace the newer optimistic item when it resolves.
    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe(
      "Keep the local ledger",
    );
    expectSaid("Keep the local ledger");
  });

  it("keeps an optimistic body when a refresh starts during a pending write", async () => {
    useDesk.setState({ newIds: [] });
    render(<ProductionHost />);
    requests.deferPut = true;
    let save!: Promise<unknown>; // updatePrimitive answers kept (PHILO-13-07 B2)
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

    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe(
      "Keep the local ledger",
    );
    expect(decisionSection()?.textContent).toContain("Keep the local ledger");
  });

  it("does not let an older refusal roll back or receipt a newer decision write", async () => {
    useDesk.setState({ newIds: [] });
    render(<ProductionHost />);
    requests.deferPut = true;
    requests.deferDecisionRead = true;
    let firstSave!: Promise<unknown>;
    act(() => {
      firstSave = useDesk.getState().updatePrimitive("decision", decision.id, {
        decision_markdown: "First decision",
      });
    });
    await waitFor(() => expect(requests.putResolvers).toHaveLength(1));
    let secondSave!: Promise<unknown>;
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

    expect(useDesk.getState().items.decision[0].decisionMarkdown).toBe(
      "Second decision",
    );
    expect(decisionSection()?.textContent).toContain("Second decision");
    expect(document.querySelector(".write-receipt-label")).toBeNull();
  });
});
