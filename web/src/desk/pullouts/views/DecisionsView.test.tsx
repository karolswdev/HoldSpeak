import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DecisionsView } from "./DecisionsView";
import { useDesk } from "../../store";
import HONEST_DECISIONS from "../../../test/wire/decisions.honest-faces.wire.json";

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

const openRef = vi.hoisted(() => vi.fn());
vi.mock("../../openObject", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../openObject")>(),
  openRef,
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

// PHILO-17: the list is every decision on the desk (`/api/decisions?scope=all`,
// paged, searched and filtered by the hub), each row with its date and its
// meeting; a row opens its record, its Desk window, or the decision itself.
const ledger = [
  {
    source: "meeting", id: "dec-1", text: receipt.decision_text, rationale: receipt.rationale,
    decided_at: "2026-10-09T14:00:00", lifecycle: "active", meeting_id: "m-1",
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

const params = (path: string) => new URLSearchParams(path.split("?")[1] ?? "");

function hub(path: string): Promise<unknown> {
  if (path.includes("receipt-abcdef0123456789")) return Promise.resolve(detail);
  if (path.startsWith("/api/decisions?")) {
    const p = params(path);
    let rows = ledger.slice();
    const id = p.get("decision_id");
    if (id) rows = rows.filter((r) => r.id === id);
    if (p.get("current") === "true") rows = rows.filter((r) => ["recorded", "accepted", "active"].includes(r.lifecycle));
    const q = (p.get("q") ?? "").toLowerCase().split(/\s+/).filter(Boolean);
    rows = rows.filter((r) => q.every((w) => `${r.text} ${r.meeting_title ?? ""}`.toLowerCase().includes(w)));
    const offset = Number(p.get("offset") ?? 0);
    const limit = Number(p.get("limit") ?? 100);
    return Promise.resolve({ decisions: rows.slice(offset, offset + limit), page: { total: rows.length } });
  }
  return Promise.resolve([receipt]);
}

describe("Intelligence → Decisions (PHILO-17: every decision, its date and its meeting)", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  beforeEach(() => {
    apiFetch.mockReset();
    openRef.mockReset();
    apiFetch.mockImplementation(hub);
  });

  it("lists every decision with its date and meeting; no UNASSIGNED, no GOVERNING, no WHY", async () => {
    const { container } = render(<DecisionsView />);
    await screen.findByText("Freeze the old ledger on Nov 5");
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions?scope=all&limit=100&offset=0");
    const rows = container.querySelectorAll("[data-testid=decisions-row]");
    expect(rows).toHaveLength(4);
    const freeze = [...rows].find((r) => r.textContent?.includes("Freeze the old ledger"))!;
    expect(freeze.textContent).toContain("Ledger cutover sync");
    expect(freeze.textContent).toContain(new Date("2026-10-09T14:05:00").toLocaleDateString());
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/UNASSIGNED|GOVERNING|WHY/);
    expect([...rows].find((r) => r.textContent?.includes("Use OTel"))!.textContent).toContain("Desk");
    expect(screen.queryByTestId("decisions-more")).toBeNull();
  });

  it("the hub searches; Current only asks the hub for standing decisions", async () => {
    render(<DecisionsView />);
    await screen.findByText("Keep the old ledger");
    expect(screen.getByText("REPLACED")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Current only" }));
    await waitFor(() => expect(screen.queryByText("Keep the old ledger")).toBeNull());
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions?scope=all&limit=100&offset=0&current=true");

    fireEvent.change(screen.getByRole("searchbox", { name: "Search decisions" }), {
      target: { value: "cutover freeze" },
    });
    await waitFor(() => expect(screen.queryByText(receipt.decision_text)).toBeNull());
    expect(screen.getByText("Freeze the old ledger on Nov 5")).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions?scope=all&limit=100&offset=0&q=cutover+freeze&current=true");
  });

  it("a list longer than one page says so and shows more", async () => {
    const many = Array.from({ length: 130 }, (_, i) => ({
      source: "meeting", id: `dec-${i}`, text: `Decision ${i}`, rationale: null,
      decided_at: "2026-10-01", lifecycle: "recorded", meeting_id: "m-1", meeting_title: "Sync", record_id: null,
    }));
    apiFetch.mockImplementation((path: string) => {
      const p = params(path);
      const offset = Number(p.get("offset") ?? 0);
      return Promise.resolve({ decisions: many.slice(offset, offset + 100), page: { total: many.length } });
    });
    const { container } = render(<DecisionsView />);
    const more = await screen.findByTestId("decisions-more");
    expect(more.textContent).toBe("Show more (100 of 130)");
    expect(container.textContent).toContain("130");
    fireEvent.click(more);
    await waitFor(() => expect(container.querySelectorAll("[data-testid=decisions-row]")).toHaveLength(130));
    expect(screen.queryByTestId("decisions-more")).toBeNull();
  });

  it("a row with a record opens full receipt evidence in place and returns to the list", async () => {
    render(<DecisionsView />);
    const row = await screen.findByRole("button", { name: `Open decision ${receipt.decision_text}` });
    fireEvent.click(row);

    expect(await screen.findByText(receipt.rationale)).toBeInTheDocument();
    expect(screen.getByText(/Receipts must explain the decision/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Evidence", { selector: ".gadget-fold-title" }));
    expect(screen.getByRole("button", { name: "Open story · HS-128-04" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open meeting" }));
    expect(openRef).toHaveBeenCalledWith("meeting:meeting-1");
    fireEvent.click(screen.getByText("History", { selector: ".gadget-fold-title" }));
    expect(screen.getByRole("button", { name: "Previous decision" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next decision" })).toBeInTheDocument();
    expect(screen.getByText(/Old rationale/)).toBeInTheDocument();
    expect(screen.getByText("CURRENT")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Results" }));
    expect(screen.getByText(receipt.decision_text)).toBeInTheDocument();
  });

  it("a meeting-derived record opens its source decision and keeps meeting evidence identity", async () => {
    // DecisionRecordService.create_from_meeting: top-level source_id is the
    // decision id; sources[].meeting_id/source_ref names the actual meeting.
    const meetingRecord = { ...detail, source_type: "meeting", source_id: "decision-from-meeting" };
    apiFetch.mockImplementation((path: string) => path === `/api/decision-records/${receipt.id}`
      ? Promise.resolve(meetingRecord) : hub(path));
    render(<DecisionsView receiptId={receipt.id} />);
    await screen.findByText(receipt.rationale);
    fireEvent.click(screen.getByRole("button", { name: "Open decision" }));
    expect(openRef).toHaveBeenCalledWith("decision:decision-from-meeting");

    fireEvent.click(screen.getByText("Evidence", { selector: ".gadget-fold-title" }));
    fireEvent.click(screen.getByRole("button", { name: "Open meeting" }));
    expect(openRef).toHaveBeenCalledWith("meeting:meeting-1");
    expect(openRef).not.toHaveBeenCalledWith("meeting:decision-from-meeting");
  });

  it("a meeting's decision with no record opens itself; Open meeting goes through the loading opener", async () => {
    render(<DecisionsView />);
    fireEvent.click(await screen.findByRole("button", { name: "Open decision Freeze the old ledger on Nov 5" }));
    const card = await screen.findByTestId("decision-detail");
    expect(card.textContent).toContain("Freeze the old ledger on Nov 5");
    expect(card.textContent).toContain("Agreed in the meeting.");
    expect(card.textContent).toContain("Ledger cutover sync");
    fireEvent.click(screen.getByRole("button", { name: "Open meeting" }));
    expect(openRef).toHaveBeenCalledWith("meeting:m-1");
  });

  it("a Desk decision the Desk did not load is held, read, then opened", async () => {
    const refresh = vi.fn(() => Promise.resolve());
    useDesk.setState({ refresh } as never);
    render(<DecisionsView />);
    fireEvent.click(await screen.findByRole("button", { name: "Open decision Use OTel for tracing" }));
    await waitFor(() => expect(openRef).toHaveBeenCalledWith("desk_decision:d-adr"));
    expect(refresh).toHaveBeenCalled();
  });

  it("decisionId is read by its id (not found in the page), and the same id asked again opens again", async () => {
    const view = render(<DecisionsView decisionId="dec-2" decisionNonce={1} />);
    expect((await screen.findByTestId("decision-detail")).textContent).toContain("Freeze the old ledger on Nov 5");
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions?scope=all&decision_id=dec-2&limit=1");

    fireEvent.click(screen.getByRole("button", { name: "Results" }));
    await screen.findByText("Keep the old ledger");
    expect(screen.queryByTestId("decision-detail")).toBeNull();

    view.rerender(<DecisionsView decisionId="dec-2" decisionNonce={2} />);
    expect((await screen.findByTestId("decision-detail")).textContent).toContain("Freeze the old ledger on Nov 5");
  });

  it("a failed requested record shows its own failure, exact Retry and Results", async () => {
    render(<DecisionsView receiptId={receipt.id} />);
    await screen.findByText(receipt.rationale);
    apiFetch.mockImplementation((path: string) => path === "/api/decision-records/receipt-new"
      ? Promise.reject(new Error("Record did not load")) : hub(path));
    fireEvent.click(screen.getByText("History", { selector: ".gadget-fold-title" }));
    fireEvent.click(screen.getByRole("button", { name: "Next decision" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Record did not load");
    expect(screen.queryByText(receipt.decision_text)).not.toBeInTheDocument();
    apiFetch.mockImplementation((path: string) => path === "/api/decision-records/receipt-new"
      ? Promise.resolve({ ...detail, id: "receipt-new", decision_text: "Use the revised rollout" }) : hub(path));
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Use the revised rollout")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /RESULTS/i }));
    expect(await screen.findByRole("searchbox", { name: "Search decisions" })).toBeInTheDocument();
  });

  it("a late record response cannot replace a later destination or Results", async () => {
    let release!: (body: unknown) => void;
    apiFetch.mockImplementation((path: string) => path === "/api/decision-records/slow-record"
      ? new Promise((resolve) => { release = resolve; }) : hub(path));
    const view = render(<DecisionsView receiptId="slow-record" />);
    await waitFor(() => expect(release).toBeTypeOf("function"));
    view.rerender(<DecisionsView receiptId={receipt.id} />);
    await screen.findByText(receipt.rationale);
    await act(async () => release({ ...detail, decision_text: "Obsolete record" }));
    expect(screen.queryByText("Obsolete record")).not.toBeInTheDocument();

    view.rerender(<DecisionsView receiptId="slow-record" />);
    await waitFor(() => expect(screen.getByRole("button", { name: /RESULTS/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /RESULTS/i }));
    await act(async () => release({ ...detail, decision_text: "Returned after Back" }));
    expect(screen.queryByText("Returned after Back")).not.toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: "Search decisions" })).toBeInTheDocument();
  });

  // Astra, #785 finding 2 (kept): a slow bus re-read for an older search must
  // not land over the new one.
  it("drops a late answer for an older query", async () => {
    let releaseAlpha: (body: unknown) => void = () => undefined;
    let alphaReads = 0;
    const page = (text: string) => ({ decisions: [{ ...ledger[1], id: text, text }], page: { total: 1 } });
    apiFetch.mockImplementation((path: string) => {
      const q = params(path).get("q");
      if (q === "alpha") {
        alphaReads += 1;
        return alphaReads === 1
          ? Promise.resolve(page("Alpha decision"))
          : new Promise((resolve) => { releaseAlpha = resolve; });
      }
      if (q === "beta") return Promise.resolve(page("Beta decision"));
      return Promise.resolve({ decisions: [], page: { total: 0 } });
    });

    vi.useFakeTimers();
    const step = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

    render(<DecisionsView />);
    const field = screen.getByRole("searchbox", { name: "Search decisions" });
    fireEvent.change(field, { target: { value: "alpha" } });
    await step(200);
    expect(screen.getByText("Alpha decision")).toBeTruthy();
    expect(alphaReads).toBe(1);

    act(() => bus.handlers.forEach((handler) => handler({ type: "desk_changed", data: {} })));
    await step(300);
    expect(alphaReads).toBe(2);

    fireEvent.change(field, { target: { value: "beta" } });
    await step(200);
    expect(screen.getByText("Beta decision")).toBeTruthy();

    await act(async () => { releaseAlpha(page("Alpha decision")); });
    await step(50);
    expect(screen.getByText("Beta decision")).toBeTruthy();
    expect(screen.queryByText("Alpha decision")).toBeNull();
  });
});

// Honest faces (inventory 2026-10-03): a raw decision id once cut the
// decision's words on its row. The hub's own answer for the honest-faces seed
// (tests/integration/test_face_wire_fences.py): one meeting decision with a record.
describe("Decisions rows on the recorded hub", () => {
  beforeEach(() => apiFetch.mockReset());

  it("a row shows the decision's words and its meeting, never a D-hex id", async () => {
    // replaces: tests/e2e/test_honest_faces_glass.py::test_intelligence_lane_names_and_decision_rows (the Decisions leg)
    apiFetch.mockImplementation(async () => structuredClone(HONEST_DECISIONS.wire));
    const { container } = render(<DecisionsView />);
    await screen.findByText("Freeze the old ledger on Nov 5");
    const rows = container.querySelectorAll("[data-testid=decisions-row]");
    expect(rows).toHaveLength(1);
    const text = rows[0].textContent ?? "";
    expect(text).toContain("Ledger cutover sync");
    expect(text).not.toMatch(/D-[0-9a-f]{6,}/i);
    expect(text).not.toMatch(/dec-[0-9a-f]{6,}|record-[0-9a-f]{6,}/);
  });
});
