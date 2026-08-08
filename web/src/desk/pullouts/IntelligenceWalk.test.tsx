import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { IntelligencePullout } from "./IntelligencePullout";

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) => reason instanceof Error ? reason.message : "Request failed",
}));

const object = {
  kind: "intelligence" as const,
  id: "desk",
  title: "Intelligence",
  ref: { kind: "intelligence" as const, id: "desk", name: "Intelligence" },
};

const brief = {
  id: "brief-1",
  headline: "One decision needs your attention.",
  is_empty: false,
  sections: {
    changed: [{
      id: "brief-item-1",
      section: "changed",
      text: "Desk Intelligence is ready.",
      detail: "The pullout is now openable from the dock.",
      source_ref: "follow-through:card-1",
      priority: 1,
    }],
    broke: [],
    waiting: [],
    decisions: [],
  },
};

const board = {
  now: [{
    id: "card-1",
    text: "Review the Intelligence walk",
    owner: "Karol",
    due: "2099-08-08",
    source: "decision",
    decision_id: "meeting-1",
    provenance: null,
  }],
  waiting: [],
  unassigned: [],
  overdue: [],
};

const receipt = {
  id: "receipt-1",
  decision_text: "Ship Desk Intelligence",
  rationale: "The Desk needs a durable operating picture.",
  alternatives: null,
  owner: "Karol",
  review_date: null,
  lifecycle: "active",
};

describe("HS-128-10 Desk Intelligence walk", () => {
  beforeEach(() => {
    localStorage.clear();
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/brief/latest") return Promise.resolve(brief);
      if (path === "/api/follow-through/board") return Promise.resolve(board);
      if (path.startsWith("/api/receipts")) return Promise.resolve([receipt]);
      return Promise.resolve([]);
    });
  });

  it("opens with the segmented Intelligence header", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(screen.getByRole("group", { name: "Intelligence view" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Brief" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Follow-through" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Receipts" })).toHaveAttribute("aria-pressed", "false");
    expect(await screen.findByText(brief.headline)).toBeInTheDocument();
  });

  it("renders the Brief headline and its operating groups", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(await screen.findByText(brief.headline)).toBeInTheDocument();
    expect(screen.getByText("Changed")).toBeInTheDocument();
    expect(screen.getByText("Broke")).toBeInTheDocument();
    expect(screen.getByText("Waiting")).toBeInTheDocument();
    expect(screen.getByText("Your Decisions")).toBeInTheDocument();
    expect(screen.getByText("Desk Intelligence is ready.")).toBeInTheDocument();
  });

  it("renders Follow-Through lanes and their cards", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Follow-through" }));

    expect(await screen.findByText("Now")).toBeInTheDocument();
    expect(screen.getByText("Waiting")).toBeInTheDocument();
    expect(screen.getByText("Unassigned")).toBeInTheDocument();
    expect(screen.getByText("Overdue")).toBeInTheDocument();
    expect(screen.getByText(board.now[0].text)).toBeInTheDocument();
  });

  it("renders Receipts with a search input that queries the ledger", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Receipts" }));

    const search = await screen.findByRole("searchbox", { name: "Search decision receipts" });
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
    fireEvent.change(search, { target: { value: "Intelligence" } });

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/api/receipts/search?q=Intelligence"),
    );
  });

  it("preserves the selected view when the pullout closes and reopens", async () => {
    const first = render(<IntelligencePullout object={object} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Receipts" }));
    await screen.findByRole("searchbox", { name: "Search decision receipts" });
    first.unmount();

    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(await screen.findByRole("searchbox", { name: "Search decision receipts" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Receipts" })).toHaveAttribute("aria-pressed", "true");
  });
});
