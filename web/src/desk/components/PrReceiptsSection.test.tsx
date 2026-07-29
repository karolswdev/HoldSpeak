import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
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
  afterEach(() => usePrReceipts.setState({ sources: [], loaded: false, busy: false }));

  it("keeps unavailable verbs visible with their named reason", () => {
    usePrReceipts.setState({ sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }], loaded: true });
    render(<PrReceiptsSection />);
    const status = screen.getByRole("button", { name: "Post status" });
    expect(status).toBeDisabled();
    expect(status).toHaveAttribute("title", "gh credentials unavailable");
    expect(screen.getByRole("button", { name: "Send agent" })).toBeEnabled();
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
    fireEvent.click(screen.getByRole("button", { name: "Info" }));
    expect(screen.getByText("Agent").nextSibling).toHaveTextContent("UNGATED");
    expect(screen.getByRole("button", { name: "Send agent" })).toBeDisabled();
  });

  it("shows the complete proposed comment before approval and offers deny", async () => {
    usePrReceipts.setState({
      sources: [{ source_id: "src_1", label: "HoldSpeak", status: "live", detail: "", observed_at: row.observed_at, prs: [row] }],
      loaded: true,
      propose: vi.fn(async () => ({ proposal_id: "proposal-1", preview: "Complete review\n\nFinding one.", state: "awaiting_decision" })),
    });
    render(<PrReceiptsSection />);
    fireEvent.click(screen.getByRole("button", { name: "Post comment" }));
    fireEvent.change(screen.getByLabelText("Comment"), { target: { value: "Complete review\n\nFinding one." } });
    fireEvent.click(screen.getByRole("button", { name: "Propose" }));
    expect(await screen.findByText("PROPOSED")).toBeInTheDocument();
    expect(screen.getByText(/Finding one/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Deny" })).toBeInTheDocument();
  });
});
