import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DecisionsView } from "./DecisionsView";

const apiFetch = vi.hoisted(() => vi.fn());

const bus = vi.hoisted(() => ({ handlers: new Set<(frame: unknown) => void>() }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      if (type !== "desk_changed") return () => undefined;
      bus.handlers.add(handler);
      return () => bus.handlers.delete(handler);
    },
  }),
}));

vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) => reason instanceof Error ? reason.message : "Request failed",
}));

const receipt = {
  id: "receipt-abcdef0123456789",
  decision_text: "Ship the Desk Intelligence pullout",
  rationale: "The Desk needs a durable answer to why.",
  alternatives: "Leave the placeholder in place",
  owner: "Karol",
  review_date: "2026-08-14",
  lifecycle: "active",
};

const detail = {
  ...receipt,
  sources: [{
    source_type: "segment",
    source_ref: "segment-1",
    meeting_id: "meeting-1",
    speaker: "Karol",
    text: "Receipts must explain the decision.",
  }],
  work: [{ id: "work-1", work_type: "story", work_ref: "HS-128-04" }],
  predecessor_id: "receipt-old",
  successor_id: "receipt-new",
  revisions: [{
    id: "revision-1",
    field_name: "rationale",
    old_value: "Old rationale",
    new_value: "The Desk needs a durable answer to why.",
    created_at: "2026-08-07T10:00:00Z",
  }],
};

describe("HS-128-04 Receipts view", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) => {
      if (path.includes("receipt-abcdef0123456789")) return Promise.resolve(detail);
      if (path.includes("/search")) return Promise.resolve([receipt]);
      return Promise.resolve([receipt]);
    });
  });

  it("searches on keystroke and supports a governing-only WHY filter", async () => {
    render(<DecisionsView />);
    await screen.findByText(receipt.decision_text);

    fireEvent.change(screen.getByRole("searchbox", { name: "Search decisions" }), {
      target: { value: "Intelligence" },
    });
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/api/decision-records/search?q=Intelligence"),
    );

    fireEvent.click(screen.getByRole("button", { name: "WHY ONLY" }));
    expect(screen.getByText("GOVERNING DECISIONS")).toBeInTheDocument();
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
  });

  it("opens full receipt evidence in place and returns to the preserved ledger", async () => {
    render(<DecisionsView />);
    const row = await screen.findByRole("button", { name: `Open decision ${receipt.decision_text}` });
    fireEvent.click(row);

    expect(await screen.findByText(receipt.rationale)).toBeInTheDocument();
    expect(screen.getByText(/Receipts must explain the decision/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "story: HS-128-04" })).toBeInTheDocument();
    expect(screen.getByText(/Old rationale/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "← RESULTS" }));
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
  });

  // Astra, #785 finding 2: a slow bus re-read for the old query landed after
  // the new query's rows and showed "alpha" rows under the field "beta".
  it("drops a late answer for an older query", async () => {
    const alpha = { ...receipt, id: "receipt-alpha", decision_text: "Alpha decision" };
    const beta = { ...receipt, id: "receipt-beta", decision_text: "Beta decision" };
    let releaseAlpha: (rows: unknown[]) => void = () => undefined;
    let alphaReads = 0;
    apiFetch.mockImplementation((path: string) => {
      if (path.includes("q=alpha")) {
        alphaReads += 1;
        // The first alpha read is the search; the second is the bus re-read, held.
        return alphaReads === 1
          ? Promise.resolve([alpha])
          : new Promise((resolve) => { releaseAlpha = resolve; });
      }
      if (path.includes("q=beta")) return Promise.resolve([beta]);
      return Promise.resolve([receipt]);
    });

    render(<DecisionsView />);
    const field = screen.getByRole("searchbox", { name: "Search decisions" });
    fireEvent.change(field, { target: { value: "alpha" } });
    await screen.findByText("Alpha decision");

    // A write somewhere: the view re-reads "alpha"; that read is slow.
    bus.handlers.forEach((handler) => handler({ type: "desk_changed", data: {} }));
    await waitFor(() => expect(alphaReads).toBe(2));

    fireEvent.change(field, { target: { value: "beta" } });
    await screen.findByText("Beta decision");

    releaseAlpha([alpha]);
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.getByText("Beta decision")).toBeTruthy();
    expect(screen.queryByText("Alpha decision")).toBeNull();
    expect((field as HTMLInputElement).value).toBe("beta");
  });
});
