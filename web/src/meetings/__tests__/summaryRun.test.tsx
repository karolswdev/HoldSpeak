// HS-201-04 — the fences for "ask for the summary and find it again".
//
// Every fence asserts the REQUEST (its path and its body), never the
// click, and the rendered disclosure, never a prop that happens to be
// passed. The five things under test:
//
//   1. every run verb sends `expected_selection_hash` from the route it
//      disclosed (the lane A interlock);
//   2. the ledger's `Retry` DISPATCHES (audit defect 2: zero requests);
//   3. a 409 is a refusal with its plain reason, and it does not erase
//      the receipt of an earlier successful run;
//   4. an `unavailable` route says its reason and withholds the verb;
//   5. the disclosure is `legs[0].host` (+ `FALLBACK` for each further
//      leg) before the click, and the receipt's attempts, in order,
//      after the run.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { MeetingIntelRecovery } from "../MeetingIntelRecovery";
import { MeetingSummarySlab, readMeetingIntel } from "../MeetingSummarySlab";
import { RouteDisclosure, RunAttempts } from "../RouteDisclosure";
import gadgetsCss from "../../desk/surface/gadgets.css?raw";
import {
  forgetExecutedReceipts,
  readPlannedRoute,
  readRunReceipt,
} from "../summaryRoute";
import { CatalogRail } from "../../pages/cores/history/CatalogRail";
import { NeedsYouTable } from "../../pages/cores/history/NeedsYouTable";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));

const mockedApiFetch = vi.mocked(apiFetch);

const READY_ROUTE = {
  status: "ready",
  reason_code: null,
  selection_hash: "sha256:abc123",
  legs: [
    {
      ordinal: 1,
      host: "192.168.1.43",
      boundary: "lan",
      profile_id: "summary-first",
      profile_revision: 2,
      deployment_revision_id: "dep-1",
    },
    {
      ordinal: 2,
      host: "api.example.com",
      boundary: "cloud",
      profile_id: "summary-fallback",
      profile_revision: 1,
      deployment_revision_id: "dep-2",
    },
  ],
};

const UNAVAILABLE_ROUTE = {
  status: "unavailable",
  reason_code: "no assignment",
  selection_hash: null,
  legs: [],
};

const SUCCEEDED_RECEIPT = {
  receipt_id: "rr_1",
  job_id: "ij_1",
  meeting_id: "meeting-1",
  selection_hash: "sha256:abc123",
  outcome: "succeeded",
  attempts: [
    { leg_ordinal: 1, host: "192.168.1.43", outcome: "failed", operation_id: "op_1" },
    { leg_ordinal: 2, host: "api.example.com", outcome: "succeeded", operation_id: "op_2" },
  ],
};

function recovery(overrides: Record<string, unknown> = {}) {
  return {
    meeting_id: "meeting-1",
    visible: true,
    state: "error",
    headline: "Meeting saved",
    completed: [{ label: "Transcript", detail: "3 saved segments" }],
    remaining: {
      label: "Remaining meeting intelligence",
      detail: "The producer returned nothing.",
    },
    job: {
      status: "failed",
      attempts: 1,
      requested_at: "2026-09-19T12:00:00",
      updated_at: "2026-09-19T12:01:00",
    },
    actions: { retry: true, skip: true },
    planned_route: READY_ROUTE,
    run_receipt: SUCCEEDED_RECEIPT,
    ...overrides,
  };
}

/** The receipt a route refusal writes: nothing was contacted, so it has no
 *  attempts, and the hub then serves THIS from every read
 *  (holdspeak/db/intel.py record_route_refusal — proven live in the glass
 *  rig: `RECEIPT AFTER REFUSAL outcome=refused attempts=[]`). */
const REFUSED_RECEIPT = {
  receipt_id: "rr_refused",
  job_id: "ij_1",
  meeting_id: "meeting-1",
  selection_hash: "sha256:abc123",
  outcome: "refused",
  attempts: [],
};

/** The 409 body the hub serves (holdspeak/web/routes/meetings/intel.py:47). */
function drift(): ApiError {
  return new ApiError(409, "The summary route changed. Check it, then try again.", {
    success: false,
    error: "The summary route changed. Check it, then try again.",
    plainReason: "The summary route changed. Check it, then try again.",
    code: "selection_drift",
    planned_route: { ...READY_ROUTE, selection_hash: "sha256:fresh" },
    current_planned_route: { ...READY_ROUTE, selection_hash: "sha256:fresh" },
    run_receipt: REFUSED_RECEIPT,
  });
}

describe("HS-201-04 the disclosure beside the verb", () => {
  it("shows legs[0].host and names every further leg a fallback", () => {
    render(<RouteDisclosure route={readPlannedRoute({ planned_route: READY_ROUTE })} />);
    const chips = screen.getByTestId("summary-route").textContent ?? "";
    expect(chips).toContain("192.168.1.43 · LAN");
    expect(chips).toContain("+ FALLBACK api.example.com");
    // Article III: the lead host is the FIRST thing said.
    expect(chips.indexOf("192.168.1.43")).toBeLessThan(chips.indexOf("FALLBACK"));
  });

  it("keeps the FULL fallback text: a route chip never truncates (PHILO-4-01 r4)", () => {
    // The disclosure is the only place the destination shows, so its chips
    // carry no truncate modifier and the whole host is in the text.
    const route = {
      ...READY_ROUTE,
      legs: [READY_ROUTE.legs[0], { ...READY_ROUTE.legs[1], host: "api.anthropic.com" }],
    };
    render(<RouteDisclosure route={readPlannedRoute({ planned_route: route })} />);
    const chips = [...screen.getByTestId("summary-route").querySelectorAll(".gadget-chip")];
    const fallback = chips.find((chip) => chip.textContent?.includes("FALLBACK"));
    expect(fallback?.textContent).toBe("+ FALLBACK api.anthropic.com");
    for (const chip of chips) {
      expect(chip.classList.contains("gadget-chip-truncate")).toBe(false);
    }
    // jsdom paints no CSS, so the species rule itself is the fence: the base
    // chip never clips; only the opt-in modifier does.
    const base = gadgetsCss.match(/\n\.gadget-chip \{[^}]*\}/)?.[0] ?? "";
    expect(base).toContain("white-space: nowrap");
    expect(base).not.toMatch(/text-overflow|max-width|overflow:/);
    expect(gadgetsCss).toMatch(/\.gadget-chip\.gadget-chip-truncate \{[^}]*text-overflow: ellipsis/);
  });

  it("says the reason in plain words when no route resolves", () => {
    render(
      <RouteDisclosure route={readPlannedRoute({ planned_route: UNAVAILABLE_ROUTE })} />,
    );
    expect(screen.getByTestId("summary-route-unavailable").textContent).toBe(
      "NO SUMMARY ROUTE · NO ASSIGNMENT",
    );
    // Never the word the old face invented for an unresolved route.
    expect(screen.queryByText(/local/i)).toBeNull();
  });

  it("lists the destinations contacted, in order, with failed attempts", () => {
    render(<RunAttempts receipt={readRunReceipt({ run_receipt: SUCCEEDED_RECEIPT })} />);
    const text = screen.getByTestId("summary-attempts").textContent ?? "";
    expect(text.indexOf("192.168.1.43")).toBeLessThan(text.indexOf("api.example.com"));
    expect(text).toContain("FAILED");
  });
});

describe("HS-201-04 the record's Retry", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
    forgetExecutedReceipts();
  });

  it("sends the disclosed selection hash with the run", async () => {
    mockedApiFetch
      .mockResolvedValueOnce(recovery())
      .mockResolvedValueOnce({ success: true, recovery: recovery({ state: "queued" }) });

    render(<MeetingIntelRecovery meetingId="meeting-1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }));

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenLastCalledWith(
        "/api/meetings/meeting-1/intel-recovery/retry",
        { method: "POST", json: { expected_selection_hash: "sha256:abc123" } },
      ),
    );
  });

  it("discloses the route before the click and the attempts after the run", async () => {
    mockedApiFetch.mockResolvedValue(recovery());
    render(<MeetingIntelRecovery meetingId="meeting-1" />);
    await screen.findByRole("button", { name: "Retry" });
    expect(screen.getByTestId("recovery-route").textContent).toContain("192.168.1.43");
    expect(screen.getByTestId("recovery-attempts").textContent).toContain(
      "api.example.com",
    );
  });

  it("shows a 409 as a refusal and keeps the EXECUTED receipt", async () => {
    // Astra's counsel finding 2: the old fixture returned the SUCCESSFUL
    // receipt from both the 409 and the reload after it, so it could not
    // catch the loss. The hub really serves the bare refusal receipt from
    // both, and the executed attempts must still be on the face.
    mockedApiFetch
      .mockResolvedValueOnce(recovery())
      .mockRejectedValueOnce(drift())
      .mockResolvedValueOnce(recovery({ run_receipt: REFUSED_RECEIPT, job: null }));

    render(<MeetingIntelRecovery meetingId="meeting-1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }));

    const refusal = await screen.findByTestId("recovery-refusal");
    // ONE short fact line, not the hub's two-sentence instruction.
    expect(refusal.textContent).toBe("REFUSED · ROUTE CHANGED");
    expect(refusal.getAttribute("title")).toContain(
      "The summary route changed. Check it, then try again.",
    );
    // The receipt of the earlier executed run is NOT erased by the refusal.
    expect(screen.getByTestId("recovery-attempts").textContent).toContain(
      "api.example.com",
    );
    // …and the refusal carries the FRESH route the hub disclosed with it.
    expect(screen.getByTestId("recovery-route").textContent).toContain(
      "192.168.1.43",
    );
    // A refusal is not an error surface (UX-CANON: honest states).
    expect(document.querySelector(".surface-state-error")).toBeNull();
  });

  it("renders the hub's EXECUTED receipt beside its durable last_refusal", async () => {
    // Lane A `a07d4bb5`: a refusal no longer replaces the executed receipt.
    // `run_receipt` is the run that really happened and `last_refusal` is
    // the no-call refusal beside it — both survive a reload and a restart,
    // so the face shows them together with NO 409 held in memory.
    mockedApiFetch.mockResolvedValue(
      recovery({ run_receipt: SUCCEEDED_RECEIPT, last_refusal: REFUSED_RECEIPT }),
    );
    render(<MeetingIntelRecovery meetingId="meeting-durable" />);
    const refusal = await screen.findByTestId("recovery-refusal");
    // No 409 in hand: the token says the state and invents no cause.
    expect(refusal.textContent).toBe("REFUSED");
    expect(refusal.getAttribute("title")).toContain("before any model was contacted");
    expect(screen.getByTestId("recovery-attempts").textContent).toContain(
      "api.example.com",
    );
  });

  it("withholds Retry and says why when no route resolves", async () => {
    mockedApiFetch.mockResolvedValue(
      recovery({ planned_route: UNAVAILABLE_ROUTE, run_receipt: null }),
    );
    render(<MeetingIntelRecovery meetingId="meeting-1" />);
    await screen.findByTestId("recovery-route-unavailable");
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
    expect(screen.getByTestId("recovery-route-unavailable").textContent).toContain(
      "NO ASSIGNMENT",
    );
  });
});

describe("HS-201-04 the ledger's Retry", () => {
  beforeEach(() => forgetExecutedReceipts());
  function rail(row: Record<string, unknown>, onRun = vi.fn()) {
    render(
      <CatalogRail
        meetingRows={[row]}
        meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
        selected={null}
        setSelected={vi.fn()}
        onRunIntelligence={onRun}
        runningId={null}
      />,
    );
    return onRun;
  }

  const FAILED_ROW = {
    id: "meeting-1",
    title: "Census standup",
    started_at: "2026-09-19T09:00:00Z",
    duration_seconds: 1800,
    capture_status: "finalized",
    intel_status: "error",
    transcriptWords: 1204,
    planned_route: READY_ROUTE,
  };

  it("dispatches the run with the route it DISPLAYED", () => {
    // The audit measured zero requests from this verb; the counsel then
    // measured a request whose hash came from a different object than the
    // chip beside it. Both are fenced here: the row hands the callback the
    // exact route it disclosed.
    const onRun = rail(FAILED_ROW);
    fireEvent.click(screen.getByTestId("retry-intelligence-btn"));
    expect(onRun).toHaveBeenCalledWith(
      "meeting-1",
      readPlannedRoute({ planned_route: READY_ROUTE }),
    );
  });

  it("discloses the route beside the verb before the click", () => {
    rail(FAILED_ROW);
    expect(screen.getByTestId("row-route").textContent).toContain("192.168.1.43");
  });

  it("withholds the verb when no route resolves", () => {
    rail({ ...FAILED_ROW, planned_route: UNAVAILABLE_ROUTE });
    expect(screen.queryByTestId("retry-intelligence-btn")).toBeNull();
    expect(screen.getByTestId("row-route-unavailable").textContent).toContain(
      "NO ASSIGNMENT",
    );
  });

  it("shows the destinations contacted after the run", () => {
    rail({ ...FAILED_ROW, run_receipt: SUCCEEDED_RECEIPT });
    expect(screen.getByTestId("row-attempts").textContent).toContain(
      "api.example.com",
    );
  });
});

describe("HS-201-04 the record's NEEDS YOU verbs", () => {
  it("discloses the route and withholds Run when none resolves", () => {
    const { rerender } = render(
      <NeedsYouTable
        needsRows={[]}
        needsCount={0}
        intelOff
        intelState="disabled"
        hasTranscript
        plannedRoute={readPlannedRoute({ planned_route: READY_ROUTE })}
        onRunIntelligence={vi.fn()}
      />,
    );
    expect(screen.getByTestId("detail-run-intelligence-btn")).toBeTruthy();
    expect(screen.getByTestId("detail-route").textContent).toContain("192.168.1.43");

    rerender(
      <NeedsYouTable
        needsRows={[]}
        needsCount={0}
        intelOff
        intelState="disabled"
        hasTranscript
        plannedRoute={readPlannedRoute({ planned_route: UNAVAILABLE_ROUTE })}
        onRunIntelligence={vi.fn()}
      />,
    );
    expect(screen.queryByTestId("detail-run-intelligence-btn")).toBeNull();
    expect(screen.getByTestId("detail-route-unavailable").textContent).toContain(
      "NO ASSIGNMENT",
    );
  });
});

describe("HS-201-04 the summary on the record", () => {
  it("renders the persisted summary text and its topics", () => {
    const intel = readMeetingIntel({
      intel: { summary: "The team reviewed the budget.", topics: ["Budget"] },
    });
    render(<MeetingSummarySlab intel={intel} receipt={readRunReceipt({ run_receipt: SUCCEEDED_RECEIPT })} />);
    expect(screen.getByTestId("meeting-summary-text").textContent).toBe(
      "The team reviewed the budget.",
    );
    expect(screen.getByTestId("meeting-summary-topics").textContent).toContain(
      "BUDGET",
    );
    // The destinations contacted ride the well's head.
    expect(screen.getByTestId("summary-record-attempts").textContent).toContain(
      "api.example.com",
    );
  });

  it("draws nothing at all when no summary was produced", () => {
    const { container } = render(
      <MeetingSummarySlab intel={readMeetingIntel({ intel: null })} receipt={null} />,
    );
    expect(container.textContent).toBe("");
  });
});
