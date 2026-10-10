import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DecisionsView } from "./DecisionsView";
import { useDesk } from "../../store";

const apiFetch = vi.hoisted(() => vi.fn());

// One `subscribe` for the whole file, as the real provider gives (a
// `useCallback`). A new function per render made the view subscribe again on
// each render, and that cancelled a re-read that was waiting.
const bus = vi.hoisted(() => {
  const handlers = new Set<(frame: unknown) => void>();
  const subscribe = (type: string, handler: (frame: unknown) => void) => {
    if (type !== "desk_changed") return () => undefined;
    handlers.add(handler);
    return () => handlers.delete(handler);
  };
  return { handlers, subscribe };
});
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: bus.subscribe }),
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

// PHILO-17: the list is every decision on the desk (`/api/decisions?scope=all`),
// each row with its date and its meeting; a row opens its record, its Desk
// window, or (a meeting's decision with no record) the decision itself.
const ledger = [
  {
    source: "meeting", id: "dec-1", text: receipt.decision_text, rationale: receipt.rationale,
    decided_at: "2026-10-09T14:00:00", lifecycle: "recorded", meeting_id: "m-1",
    meeting_title: "Ledger cutover sync", record_id: receipt.id,
  },
  {
    source: "meeting", id: "dec-2", text: "Freeze the old ledger on Nov 5", rationale: "Agreed in the meeting.",
    decided_at: "2026-10-09T14:05:00", lifecycle: "recorded", meeting_id: "m-1",
    meeting_title: "Ledger cutover sync", record_id: null,
  },
  {
    source: "meeting", id: "dec-3", text: "Keep the old ledger", rationale: null,
    decided_at: "2026-10-01T09:00:00", lifecycle: "superseded", meeting_id: "m-0",
    meeting_title: "Ledger kickoff", record_id: null,
  },
  {
    source: "desk", id: "d-adr", text: "Use OTel for tracing", rationale: null,
    decided_at: "2026-10-02", lifecycle: "accepted", meeting_id: null, meeting_title: null, record_id: null,
  },
];

describe("Intelligence → Decisions (PHILO-17: every decision, its date and its meeting)", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  beforeEach(() => {
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) => {
      if (path.includes("receipt-abcdef0123456789")) return Promise.resolve(detail);
      if (path.startsWith("/api/decisions?scope=all")) return Promise.resolve({ decisions: ledger });
      return Promise.resolve([receipt]);
    });
  });

  it("lists every decision with its date and meeting; no UNASSIGNED, no GOVERNING, no WHY", async () => {
    const { container } = render(<DecisionsView />);
    await screen.findByText("Freeze the old ledger on Nov 5");
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions?scope=all&limit=500");
    const rows = container.querySelectorAll("[data-testid=decisions-row]");
    expect(rows).toHaveLength(4);
    const freeze = [...rows].find((r) => r.textContent?.includes("Freeze the old ledger"))!;
    expect(freeze.textContent).toContain("Ledger cutover sync");
    expect(freeze.textContent).toContain(new Date("2026-10-09T14:05:00").toLocaleDateString());
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/UNASSIGNED|GOVERNING|WHY/);
    expect([...rows].find((r) => r.textContent?.includes("Use OTel"))!.textContent).toContain("Desk");
  });

  it("searches in place; Current only hides a replaced decision", async () => {
    render(<DecisionsView />);
    await screen.findByText("Keep the old ledger");
    expect(screen.getByText("REPLACED")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Current only" }));
    expect(screen.queryByText("Keep the old ledger")).toBeNull();
    expect(screen.getByText("Freeze the old ledger on Nov 5")).toBeInTheDocument();

    fireEvent.change(screen.getByRole("searchbox", { name: "Search decisions" }), {
      target: { value: "cutover freeze" },
    });
    expect(screen.getByText("Freeze the old ledger on Nov 5")).toBeInTheDocument();
    expect(screen.queryByText(receipt.decision_text)).toBeNull();
  });

  it("a row with a record opens full receipt evidence in place and returns to the list", async () => {
    render(<DecisionsView />);
    const row = await screen.findByRole("button", { name: `Open decision ${receipt.decision_text}` });
    fireEvent.click(row);

    expect(await screen.findByText(receipt.rationale)).toBeInTheDocument();
    expect(screen.getByText(/Receipts must explain the decision/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "story: HS-128-04" })).toBeInTheDocument();
    expect(screen.getByText(/Old rationale/)).toBeInTheDocument();
    expect(screen.getByText("CURRENT")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "← RESULTS" }));
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
  });

  it("a meeting's decision with no record opens itself: words, why, when, its meeting", async () => {
    const openPullout = vi.fn();
    useDesk.setState({ openPullout } as never);
    render(<DecisionsView />);
    fireEvent.click(await screen.findByRole("button", { name: "Open decision Freeze the old ledger on Nov 5" }));
    const card = await screen.findByTestId("decision-detail");
    expect(card.textContent).toContain("Freeze the old ledger on Nov 5");
    expect(card.textContent).toContain("Agreed in the meeting.");
    expect(card.textContent).toContain("Ledger cutover sync");
    fireEvent.click(screen.getByRole("button", { name: "Open meeting" }));
    expect(openPullout).toHaveBeenCalledWith("meeting:m-1");
  });

  it("decisionId (a ⌘K hit) opens that decision in place", async () => {
    render(<DecisionsView decisionId="dec-2" />);
    const card = await screen.findByTestId("decision-detail");
    expect(card.textContent).toContain("Freeze the old ledger on Nov 5");
  });

  // Astra, #785 finding 2 (kept): a slow bus re-read for an older list must
  // not land over the new one. The list now changes with the work ref.
  it("drops a late answer for an older work ref", async () => {
    const alpha = { ...receipt, id: "receipt-alpha", decision_text: "Alpha decision" };
    const beta = { ...receipt, id: "receipt-beta", decision_text: "Beta decision" };
    let releaseAlpha: (rows: unknown[]) => void = () => undefined;
    let alphaReads = 0;
    apiFetch.mockImplementation((path: string) => {
      if (path.includes("/work/story/alpha")) {
        alphaReads += 1;
        return alphaReads === 1
          ? Promise.resolve([alpha])
          : new Promise((resolve) => { releaseAlpha = resolve; });
      }
      if (path.includes("/work/story/beta")) return Promise.resolve([beta]);
      return Promise.resolve({ decisions: [] });
    });

    vi.useFakeTimers();
    const step = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

    const view = render(<DecisionsView workRef="story:alpha" />);
    await step(50);
    expect(screen.getByText("Alpha decision")).toBeTruthy();

    act(() => bus.handlers.forEach((handler) => handler({ type: "desk_changed", data: {} })));
    await step(300);
    expect(alphaReads).toBe(2);

    view.rerender(<DecisionsView workRef="story:beta" />);
    await step(50);
    expect(screen.getByText("Beta decision")).toBeTruthy();

    await act(async () => { releaseAlpha([alpha]); });
    await step(50);
    expect(screen.getByText("Beta decision")).toBeTruthy();
    expect(screen.queryByText("Alpha decision")).toBeNull();
  });
});
