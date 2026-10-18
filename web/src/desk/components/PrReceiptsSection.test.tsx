import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { usePrReceipts, type PrRow } from "../prReceipts";
import { PrReceiptsSection } from "./PrReceiptsSection";

vi.mock("./MicButton", () => ({ MicButton: () => <button type="button">Mic</button> }));

const row: PrRow = {
  source_id: "src_1", number: 393, title: "Kernel inference", url: "https://github.com/o/r/pull/393",
  repo: "o/r", head_ref: "agent/hs-106-07", base_ref: "main", head_sha: "a".repeat(40),
  base_sha: "b".repeat(40), state: "open", ci: "failing", author: "owner",
  observed_at: "2026-07-27T10:00:00Z", attribution: "exact", basis: "branch matches",
  needs_you: true, worktree_id: "wt_1", agent_gate: "gated",
  verbs: {
    send_agent: { available: true, reason: "" }, draft_review: { available: true, reason: "" },
    post_comment: { available: true, reason: "" }, post_status: { available: false, reason: "gh credentials unavailable" },
  },
};

describe("PR follow-through desk object", () => {
  beforeEach(() => usePrReceipts.setState({ load: vi.fn(async () => {}) }));
  afterEach(() => usePrReceipts.setState({ sources: [], loaded: false, busy: false }));

  // Betterment shell S0 (UX-CANON A.11): an unavailable verb is withheld.
  it("withholds unavailable verbs and keeps the live ones", () => {
    usePrReceipts.setState({ sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }], loaded: true });
    render(<PrReceiptsSection />);
    // PHILO-17 THE REFIT: one verb per row (Open PR); the rest in the ⋯ menu.
    expect(screen.getByRole("button", { name: "Open PR" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Send agent" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    expect(screen.queryByRole("menuitem", { name: /^Post status/ })).toBeNull();
    expect(screen.getByRole("menuitem", { name: "Send agent" })).not.toHaveAttribute("aria-disabled");
  });

  it("marks an ungated agent on the row and in Info", () => {
    const ungated = {
      ...row,
      agent_gate: "ungated" as const,
      verbs: {
        ...row.verbs!,
        send_agent: { available: false, reason: "not gated" },
      },
    };
    usePrReceipts.setState({ sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [ungated] }], loaded: true });
    render(<PrReceiptsSection />);
    expect(screen.getByText("UNGATED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Info" }));
    expect(screen.getByText("Agent").nextSibling).toHaveTextContent("UNGATED");
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    expect(screen.queryByRole("menuitem", { name: /^Send agent/ })).toBeNull();
  });

  it("shows the complete proposed comment before approval and offers deny", async () => {
    usePrReceipts.setState({
      sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }],
      loaded: true,
      propose: vi.fn(async () => ({ proposal_id: "proposal-1", preview: "Complete review\n\nFinding one.", state: "awaiting_decision" })),
    });
    render(<PrReceiptsSection />);
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Post comment" }));
    fireEvent.change(screen.getByLabelText("Comment"), { target: { value: "Complete review\n\nFinding one." } });
    fireEvent.click(screen.getByRole("button", { name: "Propose" }));
    expect(await screen.findByText("PROPOSED")).toBeInTheDocument();
    expect(screen.getByText(/Finding one/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Post to GitHub" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Deny" })).toBeInTheDocument();
  });

  it("shows Review ready for a completed draft and keeps identifiers inside the output fold", async () => {
    const output = "Review finding one.\n\nReview finding two.";
    const draftReview = vi.fn(async () => ({ output, operation_id: "delivery-pr-review:7a1b", artifact_id: "review-42" }));
    usePrReceipts.setState({
      sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }],
      loaded: true, draftReview,
    });
    const { container } = render(<PrReceiptsSection />);
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Draft review" }));
    expect(await screen.findByText("Review ready")).toBeVisible();
    expect(draftReview).toHaveBeenCalledWith(row);
    const result = container.querySelector(".desk-pr-result td")!;
    const fold = result.querySelector("details")!;
    expect(fold).not.toHaveAttribute("open");
    expect(fold.querySelector("pre")).toHaveTextContent("delivery-pr-review:7a1b");
    expect(fold.querySelector("pre")).toHaveTextContent("review-42");
    expect(fold.querySelector("pre")?.textContent).toContain(output);
    const resting = result.cloneNode(true) as HTMLElement;
    resting.querySelector("details")?.remove();
    expect(resting.textContent).toBe("Review ready");
    fireEvent.click(fold.querySelector("summary")!);
    expect(fold).toHaveAttribute("open");
    expect(fold.querySelector("pre")).toBeVisible();
  });

  it("retains the performed action so an accepted send is not reported as a ready review", async () => {
    usePrReceipts.setState({
      sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }],
      loaded: true,
      draftReview: vi.fn(async () => ({ output: "A completed review", artifact_id: "review-42" })),
      sendAgent: vi.fn(async () => ({ state: "accepted", output: "Request queued", operation_id: "spawn-accepted" })),
    });
    render(<PrReceiptsSection />);
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Draft review" }));
    expect(await screen.findByText("Review ready")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Send agent" }));
    fireEvent.change(screen.getByLabelText("Instruction"), { target: { value: "Inspect the receipt" } });
    fireEvent.click(screen.getByRole("button", { name: "Send agent" }));
    expect(await screen.findByText("Accepted")).toBeVisible();
    expect(usePrReceipts.getState().sendAgent).toHaveBeenCalledWith(row, "Inspect the receipt");
    expect(screen.queryByText("Review ready")).toBeNull();
    expect(screen.queryByText("Agent started")).toBeNull();
  });

  it("does not call an accepted draft ready without review output", async () => {
    usePrReceipts.setState({
      sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }],
      loaded: true, draftReview: vi.fn(async () => ({ operation_id: "draft-accepted", state: "accepted" })),
    });
    const { container } = render(<PrReceiptsSection />);
    fireEvent.click(screen.getByRole("button", { name: "More for #393" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Draft review" }));
    expect(await screen.findByText("Accepted")).toBeVisible();
    expect(screen.queryByText("Review ready")).toBeNull();
    expect(container.querySelector(".desk-pr-result details summary")).toHaveTextContent("RAW · RECEIPT");
  });
});
