import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReceiptsView } from "./ReceiptsView";

const apiFetch = vi.hoisted(() => vi.fn());

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
    render(<ReceiptsView />);
    await screen.findByText(receipt.decision_text);

    fireEvent.change(screen.getByRole("searchbox", { name: "Search decision receipts" }), {
      target: { value: "Intelligence" },
    });
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/api/receipts/search?q=Intelligence"),
    );

    fireEvent.click(screen.getByRole("button", { name: "WHY ONLY" }));
    expect(screen.getByText("GOVERNING RECEIPTS")).toBeInTheDocument();
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
  });

  it("opens full receipt evidence in place and returns to the preserved ledger", async () => {
    render(<ReceiptsView />);
    const row = await screen.findByRole("button", { name: `Open receipt ${receipt.decision_text}` });
    fireEvent.click(row);

    expect(await screen.findByText(receipt.rationale)).toBeInTheDocument();
    expect(screen.getByText(/Receipts must explain the decision/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "story: HS-128-04" })).toBeInTheDocument();
    expect(screen.getByText(/Old rationale/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "← RESULTS" }));
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
  });
});
