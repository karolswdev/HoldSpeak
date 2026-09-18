// HS-200-12 — the review wing: five proposals on three axes, one verb per
// row, MORE holding Edit / Dismiss / Open evidence, Confirm rendering the
// durable result the canonical route returns, and the processing face's
// ATTEMPT n · SAME JOB + ALREADY KEPT n.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../../../lib/api", () => ({
  apiFetch,
  readableError: (e: unknown) => String((e as Error)?.message ?? e),
}));
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: () => () => undefined }),
}));
vi.mock("../../../../desk/shell", () => ({ openSurfaceOr: vi.fn() }));

import { MeetingReview } from "../MeetingReview";

const STARTED = "2026-09-07T11:00:00";

function proposal(over: Record<string, unknown>) {
  return {
    id: "p1",
    kind: "decision",
    text: "Cut-over runs on the read replica first",
    original_text: "Cut-over runs on the read replica first",
    owner: null,
    due: null,
    state: "proposed",
    support: "supported",
    support_record: { method: "field_mapping" },
    acceptance: "unreviewed",
    unknowns: [],
    span_start: 1080,
    span_end: 1260,
    segment_index: 1,
    job_attempt: 1,
    model_host: "192.168.1.43",
    extraction_model: "qwen3-35b",
    decision_record_id: null,
    commitment_id: null,
    decided_at: null,
    text_edited: false,
    ...over,
  };
}

const FIVE = [
  proposal({}),
  proposal({ id: "p2", text: "Freeze window moves to Sunday 02:00", support: "source_linked", support_record: null, span_start: 1860, span_end: 1980, segment_index: 2 }),
  proposal({ id: "p3", kind: "action", text: "Confirm the freeze window with the payments team", unknowns: [{ type: "owner", value: "unknown" }], span_start: 1980, span_end: 2100, segment_index: 3 }),
  proposal({ id: "p4", kind: "action", text: "Write the rollback runbook", support: "source_linked", support_record: null, unknowns: [{ type: "owner", value: "unknown" }, { type: "due", value: "unknown" }], span_start: 2400, span_end: 2520, segment_index: 4 }),
  proposal({ id: "p5", kind: "action", text: "Re-run the load test on the replica", support: "unknown", support_record: null, span_start: null, span_end: null, segment_index: null, owner: "Karol", due: "Friday" }),
];

function review(over: Record<string, unknown> = {}) {
  return {
    meeting_id: "m1",
    title: "Architecture review",
    started_at: STARTED,
    project: { id: "prj", name: "Q4 platform" },
    job: { job_id: "ij_k8c21", status: "succeeded", attempt: 1, same_job: false, last_error: null, model_host: "192.168.1.43", extraction_model: "qwen3-35b", updated_at: STARTED },
    coverage: { turns: 47, read: 47, state: "available", observed_at: "2026-09-07T12:04:00" },
    extracted_at: "2026-09-07T12:04:00",
    proposals: FIVE,
    ...over,
  };
}

function mount(payload = review()) {
  apiFetch.mockImplementation(async (path: string) => {
    if (path.endsWith("/outcome-review")) return payload;
    throw new Error(`unexpected ${path}`);
  });
  const onOpenEvidence = vi.fn();
  const onOpenTranscript = vi.fn();
  const utils = render(
    <MeetingReview meetingId="m1" onOpenEvidence={onOpenEvidence} onOpenTranscript={onOpenTranscript} />,
  );
  return { ...utils, onOpenEvidence, onOpenTranscript };
}

beforeEach(() => {
  apiFetch.mockReset();
});

describe("MeetingReview (HS-200-12)", () => {
  it("draws five proposals on three axes with one verb each and typed unknowns", async () => {
    mount();
    await screen.findByText("5 to review");
    expect(screen.getByText("COVERAGE").parentElement?.textContent).toContain("47 OF 47 TURNS");
    expect(screen.getByText("DECISIONS 2")).toBeInTheDocument();
    expect(screen.getByText("COMMITMENTS 3")).toBeInTheDocument();
    // One verb per row (Confirm) and one MORE.
    expect(screen.getAllByTestId("review-confirm")).toHaveLength(5);
    expect(screen.getAllByTestId("review-more")).toHaveLength(5);
    // The three axes.
    expect(screen.getAllByTestId("review-kind").map((n) => n.textContent)).toEqual(["PROPOSAL", "PROPOSAL", "PROPOSAL", "PROPOSAL", "PROPOSAL"]);
    const support = screen.getAllByTestId("review-support").map((n) => n.textContent?.replace(/^[^A-Z]*/, ""));
    expect(support).toEqual(["SUPPORTED", "LINKED", "SUPPORTED", "LINKED", "UNSUPPORTED"]);
    expect(screen.getAllByTestId("review-acceptance")).toHaveLength(5);
    // The span, as MTG mm-dd · hh:mm–hh:mm from the meeting's own clock.
    expect(screen.getAllByTestId("review-span")[0].textContent).toBe("MTG 09-07 · 11:18–11:21");
    // No source, no source chip; the typed unknowns.
    expect(screen.getByTestId("review-no-source")).toBeInTheDocument();
    const unknowns = screen.getAllByTestId("review-unknown").map((n) => n.textContent?.replace(/^[^A-Z]*/, ""));
    expect(unknowns).toEqual(["OWNER · UNKNOWN", "OWNER · UNKNOWN", "DUE · UNKNOWN"]);
    // Never a counter of zero, never the head repeating the title.
    expect(screen.queryByText(/\b0 /)).toBeNull();
    expect(screen.queryByText("Architecture review")).toBeNull();
    // The way back to the Project; the extraction's egress.
    expect(screen.getByRole("button", { name: "Open the Project: Q4 platform" })).toBeInTheDocument();
    expect(screen.getByText("192.168.1.43 · LAN")).toBeInTheDocument();
    expect(screen.getByText("QWEN3-35B")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept reviewed" })).not.toBeDisabled();
    // The extracted owner/due read plain; nothing is SUPPLIED yet.
    expect(screen.getByTestId("review-owner").textContent).toBe("OWNER · KAROL");
    expect(screen.getByTestId("review-owner").hasAttribute("data-supplied")).toBe(false);
  });

  it("Accept reviewed is a two-step primary that calls the bulk verb and names what was left", async () => {
    mount();
    await screen.findByText("5 to review");
    const verb = screen.getByRole("button", { name: "Accept reviewed" });
    fireEvent.click(verb);                                    // arms
    expect(verb.textContent).toBe("Accept 2?");             // the eligible count, not five
    expect(apiFetch).toHaveBeenCalledTimes(1);               // nothing sent yet
    apiFetch.mockImplementationOnce(async (path: string, init: { method?: string }) => {
      expect(path).toBe("/api/meetings/m1/proposals/accept-reviewed");
      expect(init.method).toBe("POST");
      return {
        success: true, accepted_count: 2, left_count: 3, unsupported: 1, unknown: 2, prior: 0,
        accepted: [
          { proposal: proposal({ state: "confirmed", acceptance: "accepted", decided_at: STARTED }) },
          { proposal: proposal({ id: "p2", text: "Freeze window moves to Sunday 02:00", state: "confirmed", acceptance: "accepted", decided_at: STARTED }) },
        ],
        left: [{ proposal_id: "p3", reason: "unknown" }, { proposal_id: "p4", reason: "unknown" }, { proposal_id: "p5", reason: "unsupported" }],
      };
    });
    fireEvent.click(verb);                                    // fires
    await waitFor(() => expect(screen.getByTestId("review-receipt").textContent).toBe("ACCEPTED 2 · LEFT 3 · UNSUPPORTED 1 · UNKNOWN 2"));
    expect(screen.getByText("3 to review")).toBeInTheDocument();
    // The left rows are still there, with their verbs and chips.
    expect(screen.getAllByTestId("review-confirm")).toHaveLength(3);
    expect(screen.getByTestId("review-no-source")).toBeInTheDocument();
    expect(screen.getAllByTestId("review-row-decision").every((r) => r.getAttribute("data-state") === "confirmed")).toBe(true);
    // Nothing eligible remains: the primary is drawn refused.
    expect(screen.getByRole("button", { name: "Accept reviewed" })).toBeDisabled();
  });

  it("a supplied owner reads SUPPLIED; an extracted one does not", async () => {
    mount(review({ proposals: [
      proposal({ id: "a1", kind: "action", text: "Write the rollback runbook", owner: "Priya", owner_supplied: "Priya", due: "Friday", due_supplied: null }),
    ] }));
    await screen.findByText("1 to review");
    expect(screen.getByTestId("review-owner").textContent).toBe("OWNER · PRIYA · SUPPLIED");
    expect(screen.getByTestId("review-owner").hasAttribute("data-supplied")).toBe(true);
    expect(screen.getByTestId("review-due").textContent).toBe("DUE · FRIDAY");
  });

  it("rows from an earlier transcript revision sit in PRIOR REVISION, out of the ledgers", async () => {
    mount(review({
      revision: "rev-b",
      prior_revision: { decided: 2, open: 0 },
      proposals: [
        proposal({ id: "old1", extraction_revision: "rev-a", state: "confirmed", acceptance: "accepted", decided_at: STARTED }),
        proposal({ id: "old2", kind: "action", text: "Draft the rollback runbook", extraction_revision: "rev-a", state: "dismissed", acceptance: "rejected", decided_at: STARTED }),
        proposal({ id: "new1", extraction_revision: "rev-b" }),
        proposal({ id: "new2", kind: "action", text: "Draft the rollback runbook", extraction_revision: "rev-b", unknowns: [{ type: "owner", value: "unknown" }, { type: "due", value: "unknown" }] }),
      ],
    }));
    await screen.findByText("2 to review");
    const disclosure = screen.getByRole("button", { name: /PRIOR REVISION/ });
    expect(disclosure.textContent).toContain("2 DECIDED");
    expect(screen.queryAllByTestId("review-prior-row")).toHaveLength(0);   // closed by default
    fireEvent.click(disclosure);
    const rows = screen.getAllByTestId("review-prior-row");
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain("ACCEPTED");
    expect(rows[1].textContent).toContain("DISMISSED");
    // The ledgers hold the CURRENT revision only: 1 decision, 1 commitment.
    expect(screen.getByText("DECISIONS 1")).toBeInTheDocument();
    expect(screen.getByText("COMMITMENTS 1")).toBeInTheDocument();
    expect(screen.getAllByTestId("review-confirm")).toHaveLength(2);
    // ACCEPTED counts the current revision's rows only.
    expect(screen.getByText("NOTHING ACCEPTED YET")).toBeInTheDocument();
  });

  it("Confirm calls the canonical route and renders the durable result in place", async () => {
    mount();
    await screen.findByText("5 to review");
    apiFetch.mockImplementationOnce(async (path: string, init: { method?: string }) => {
      expect(path).toBe("/api/proposals/p1/confirm");
      expect(init.method).toBe("POST");
      return {
        success: true, state: "confirmed", replayed: false,
        decision_record_id: "record-1", commitment_id: "commitment-1",
        proposal: proposal({ state: "confirmed", acceptance: "accepted", decision_record_id: "record-1", commitment_id: "commitment-1", decided_at: "2026-09-07T12:10:00" }),
      };
    });
    fireEvent.click(screen.getAllByTestId("review-confirm")[0]);
    await waitFor(() => expect(screen.getByText("4 to review")).toBeInTheDocument());
    const row = screen.getAllByTestId("review-row-decision")[0];
    expect(row.getAttribute("data-state")).toBe("confirmed");
    expect(within(row).getByTestId("review-acceptance").textContent).toContain("ACCEPTED");
    expect(within(row).getByTestId("review-kept").textContent).toBe("DECISION RECORD · KEPT 12:10");
    expect(screen.getByText("ACCEPTED 1")).toBeInTheDocument();
    expect(screen.getByTestId("review-receipt").textContent).toMatch(/^CONFIRMED \d\d:\d\d$/);
    // The row stays in place, with no verb left to press.
    expect(within(row).queryByTestId("review-confirm")).toBeNull();
  });

  it("Enter on a focused row fires Confirm; MORE holds Edit, Dismiss and Open evidence", async () => {
    const { onOpenEvidence } = mount();
    await screen.findByText("5 to review");
    const row = screen.getAllByTestId("review-row-decision")[1];
    fireEvent.click(within(row).getByTestId("review-more"));
    expect(screen.getByRole("button", { name: "Edit: Freeze window moves to Sunday 02:00" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss: Freeze window moves to Sunday 02:00" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open evidence: Freeze window moves to Sunday 02:00" }));
    expect(onOpenEvidence).toHaveBeenCalledWith(2);
    // Escape closes MORE.
    fireEvent.keyDown(row, { key: "Escape" });
    expect(screen.queryByRole("button", { name: "Edit: Freeze window moves to Sunday 02:00" })).toBeNull();
    // Enter confirms.
    apiFetch.mockImplementationOnce(async (path: string) => {
      expect(path).toBe("/api/proposals/p2/confirm");
      return { success: true, state: "confirmed", replayed: false, proposal: proposal({ id: "p2", state: "confirmed", acceptance: "accepted", decided_at: STARTED }) };
    });
    fireEvent.keyDown(row, { key: "Enter" });
    await waitFor(() => expect(row.getAttribute("data-state")).toBe("confirmed"));
    // Backspace never dismisses.
    const other = screen.getAllByTestId("review-row-action")[0];
    fireEvent.keyDown(other, { key: "Backspace" });
    expect(apiFetch).not.toHaveBeenCalledWith("/api/proposals/p3/dismiss", expect.anything());
  });

  it("Open evidence is withheld on a proposal without a span", async () => {
    mount();
    await screen.findByText("5 to review");
    const row = screen.getAllByTestId("review-row-action")[2];
    fireEvent.click(within(row).getByTestId("review-more"));
    expect(within(row).queryByTestId("review-evidence")).toBeNull();
    expect(within(row).getByTestId("review-edit")).toBeInTheDocument();
  });

  it("Edit in place posts the sentence and the support drops to LINKED · EDITED", async () => {
    mount();
    await screen.findByText("5 to review");
    const row = screen.getAllByTestId("review-row-decision")[0];
    fireEvent.click(within(row).getByTestId("review-more"));
    fireEvent.click(within(row).getByTestId("review-edit"));
    const editor = within(row).getByRole("textbox");
    fireEvent.change(editor, { target: { value: "Cut-over runs on the read replica first, writes frozen" } });
    apiFetch.mockImplementationOnce(async (path: string, init: { json?: { text?: string } }) => {
      expect(path).toBe("/api/proposals/p1/edit");
      expect(init.json?.text).toBe("Cut-over runs on the read replica first, writes frozen");
      return {
        success: true,
        proposal: proposal({ text: "Cut-over runs on the read replica first, writes frozen", support: "source_linked", support_record: { method: "field_mapping", invalidated_at: STARTED, invalidation_reason: "text_edited" }, text_edited: true }),
      };
    });
    fireEvent.keyDown(editor, { key: "Enter" });
    await waitFor(() => expect(within(row).getByTestId("review-support").textContent).toContain("LINKED · EDITED"));
    expect(screen.getByTestId("review-receipt").textContent).toMatch(/^EDITED \d\d:\d\d$/);
    // The original stays as provenance, inside MORE.
    expect(within(row).getByTestId("review-was").textContent).toBe("WAS · Cut-over runs on the read replica first");
  });

  it("Dismiss (two-step, in world) removes the row and moves focus to its successor", async () => {
    mount();
    await screen.findByText("5 to review");
    const rows = screen.getAllByTestId("review-row-action");
    fireEvent.click(within(rows[0]).getByTestId("review-more"));
    const dismiss = screen.getByRole("button", { name: "Dismiss: Confirm the freeze window with the payments team" });
    fireEvent.click(dismiss);            // arms
    apiFetch.mockImplementationOnce(async (path: string) => {
      expect(path).toBe("/api/proposals/p3/dismiss");
      return { success: true, state: "dismissed", replayed: false, proposal: proposal({ id: "p3", kind: "action", state: "dismissed", acceptance: "rejected", decided_at: STARTED }) };
    });
    fireEvent.click(dismiss);            // fires
    await waitFor(() => expect(screen.getAllByTestId("review-row-action")).toHaveLength(2));
    expect(screen.getByText("COMMITMENTS 2")).toBeInTheDocument();
    expect(screen.getByText("DISMISSED 1")).toBeInTheDocument();
    await act(async () => { await new Promise((r) => window.requestAnimationFrame(() => r(null))); });
    expect(document.activeElement?.getAttribute("data-proposal-id")).toBe("p4");
  });

  it("supplying an owner resolves that typed unknown through the edit route", async () => {
    mount();
    await screen.findByText("5 to review");
    const row = screen.getAllByTestId("review-row-action")[1];
    fireEvent.click(within(row).getByTestId("review-more"));
    const owner = within(within(row).getByTestId("review-supply-owner")).getByRole("button");
    fireEvent.click(owner);
    const field = within(row).getByRole("textbox", { name: /owner:/ });
    fireEvent.change(field, { target: { value: "Priya" } });
    apiFetch.mockImplementationOnce(async (path: string, init: { json?: { owner?: string } }) => {
      expect(path).toBe("/api/proposals/p4/edit");
      expect(init.json).toEqual({ owner: "Priya" });
      return { success: true, proposal: proposal({ id: "p4", kind: "action", text: "Write the rollback runbook", owner: "Priya", unknowns: [{ type: "due", value: "unknown" }], support: "source_linked", support_record: null }) };
    });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(within(row).getAllByTestId("review-unknown")).toHaveLength(1));
    expect(within(row).getByText("OWNER · PRIYA")).toBeInTheDocument();
  });

  it("the processing face says ATTEMPT 2 · SAME JOB and ALREADY KEPT n opens the kept rows", async () => {
    mount(review({
      job: { job_id: "ij_k8c21", status: "queued", attempt: 2, same_job: true, last_error: "provider exploded", model_host: "192.168.1.43", extraction_model: "qwen3-35b", updated_at: STARTED },
      coverage: { turns: 47, read: null, state: "queued", observed_at: "2026-09-07T12:04:00" },
      extracted_at: null,
      proposals: [
        proposal({ state: "confirmed", acceptance: "accepted", decided_at: "2026-09-07T12:06:00" }),
        proposal({ id: "p2", kind: "action", text: "Priya confirms the freeze window", state: "confirmed", acceptance: "accepted", decided_at: "2026-09-07T12:06:00" }),
      ],
    }));
    await screen.findByText("Reading the meeting");
    expect(screen.getByTestId("review-job").textContent).toBe("JOB K-8C21");
    expect(screen.getByTestId("review-attempt").textContent).toBe("ATTEMPT 2 · SAME JOB");
    // Coverage above the answer, with no invented numerator.
    expect(screen.getByText("COVERAGE").textContent).toBe("COVERAGE");
    expect(screen.getByText("47 TURNS NOT YET READ")).toBeInTheDocument();
    expect(screen.getByText("READ · RETRY")).toBeInTheDocument();
    expect(screen.queryByText(/provider exploded/)).toBeNull();
    // The kept rows sit behind the verb, stamped with their attempt.
    const kept = screen.getByRole("button", { name: /ALREADY KEPT/ });
    expect(kept.textContent).toContain("ALREADY KEPT");
    expect(kept.textContent).toContain("2");
    expect(screen.getAllByTestId("review-kept-row")).toHaveLength(2);
    expect(screen.getAllByText("ATTEMPT 1")).toHaveLength(2);
    expect(screen.getByText("NOT COMPLETE")).toBeInTheDocument();
    // Every kept row can be opened (the board's Open; a dead end is a lie).
    expect(screen.getAllByTestId("review-kept-open")).toHaveLength(2);
    fireEvent.click(kept);
    expect(screen.queryAllByTestId("review-kept-row")).toHaveLength(0);
    // No ledger row is offered for review while the read is in flight; the
    // primary is drawn refused, not withheld.
    expect(screen.queryAllByTestId("review-confirm")).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Accept reviewed" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Skip" })).toBeInTheDocument();
  });

  it("a finished meeting with no proposals reads NOTHING TO REVIEW with the coverage kept", async () => {
    mount(review({ proposals: [] }));
    await screen.findByText("Nothing to review");
    expect(screen.getByText("COVERAGE").parentElement?.textContent).toContain("47 OF 47 TURNS");
    expect(screen.getByRole("button", { name: "Accept reviewed" })).toBeDisabled();
  });
});
