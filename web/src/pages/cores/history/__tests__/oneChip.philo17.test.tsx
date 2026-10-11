// PHILO-17 (U16, Astra r1 M3): the meeting names its summary engine ONCE.
// A rendered fence over the composed Meetings face: list → open meeting →
// Review. The window foot names the host; the row, the record's strip and
// its summary slab do not repeat a succeeded run on that host. A failed
// attempt and a different host stay. Under Review the window foot is not
// mounted, so nothing is suppressed against it.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { HistoryCore } from "../../HistoryCore";
import { apiFetch } from "../../../../lib/api";
import { forgetExecutedReceipts } from "../../../../meetings/summaryRoute";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<Record<string, unknown>>()),
  apiFetch: vi.fn(),
}));
const subscribe = () => () => undefined;
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  forgetExecutedReceipts();
});
afterEach(() => {
  vi.restoreAllMocks();
});

const LOOPBACK_ROUTE = {
  status: "ready", selection_hash: "sha256:ready", reason_code: null,
  legs: [{ ordinal: 1, host: "127.0.0.1", boundary: "local" }],
};

type Attempt = { leg_ordinal: number; host: string; outcome: string; operation_id: string };

function meeting(attempts: Attempt[], intelHost: string) {
  return {
    id: "a", title: "Standup", started_at: "2026-10-10T10:00:00",
    capture_status: "finalized", intel_status: { state: "ready" }, intel_model_host: intelHost,
    duration_seconds: 24, transcriptWords: 38, unclearSpans: 0,
    planned_route: LOOPBACK_ROUTE,
    run_receipt: { receipt_id: "rr_1", job_id: "job-a", meeting_id: "a", selection_hash: "sha256:ready", outcome: "succeeded", attempts },
    intel: { summary: "The team agreed to ship on Friday.", topics: ["release"] },
    segments: [{ text: "Ship it Friday.", start_time: 0, end_time: 4 }],
  };
}

function hub(row: Record<string, unknown>) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path.startsWith("/api/meetings?")) return { meetings: [row] } as never;
    if (path === "/api/meetings/a") return row as never;
    if (path.endsWith("/outcome-review")) {
      return {
        meeting_id: "a", title: "Standup", started_at: "2026-10-10T10:00:00", project: null,
        job: { job_id: "job-a", status: "succeeded", attempt: 1, same_job: false, last_error: null, model_host: "127.0.0.1", extraction_model: "walk", updated_at: "2026-10-10T10:00:00" },
        coverage: { turns: 1, read: 1, state: "available" }, extracted_at: null, proposals: [],
      } as never;
    }
    return {} as never;
  });
}

function Shell() {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setWings}>
      {wings}
      <HistoryCore />
    </WingSlotContext.Provider>
  );
}

/** Every egress chip on the face, by its label. */
function chips(): string[] {
  return Array.from(document.querySelectorAll(".gadget-chip-egress")).map((el) => (el.textContent ?? "").trim());
}

it("list and open meeting: a succeeded loopback run is one THIS DEVICE chip, never 127.0.0.1", async () => {
  hub(meeting([{ leg_ordinal: 1, host: "127.0.0.1", outcome: "succeeded", operation_id: "op_1" }], "127.0.0.1"));
  render(<Shell />);
  await screen.findByTestId("meeting-row-a");
  await waitFor(() => expect(chips().filter((c) => c.includes("THIS DEVICE"))).toHaveLength(1));
  expect(chips().join(" ")).not.toContain("127.0.0.1");
  expect(screen.queryByTestId("row-attempts")).toBeNull();

  // Open the meeting: its strip and summary slab do not say it again.
  fireEvent.click(within(screen.getByTestId("meeting-row-a")).getByRole("button", { name: /Standup/ }));
  await screen.findByTestId("meeting-summary-text");
  expect(chips().filter((c) => c.includes("THIS DEVICE"))).toHaveLength(1);
  expect(screen.queryByTestId("summary-record-attempts")).toBeNull();
  expect(chips().join(" ")).not.toContain("127.0.0.1");
});

it("a failed leg and a different host stay on the open meeting", async () => {
  hub(meeting([
    { leg_ordinal: 1, host: "127.0.0.1", outcome: "failed", operation_id: "op_1" },
    { leg_ordinal: 2, host: "api.example.com", outcome: "succeeded", operation_id: "op_2" },
  ], "api.example.com"));
  render(<Shell />);
  await screen.findByTestId("meeting-row-a");
  fireEvent.click(within(screen.getByTestId("meeting-row-a")).getByRole("button", { name: /Standup/ }));
  await screen.findByTestId("meeting-summary-text");
  const slab = screen.getByTestId("summary-record-attempts").textContent ?? "";
  expect(slab).toContain("THIS DEVICE");
  expect(slab).toContain("FAILED");
  expect(slab).toContain("api.example.com");
  // The strip names the other host too: it is not the foot's.
  expect(chips().filter((c) => c === "api.example.com").length).toBeGreaterThanOrEqual(2);
});

it("Review: the window foot is not mounted, so nothing is suppressed against it", async () => {
  hub(meeting([{ leg_ordinal: 1, host: "127.0.0.1", outcome: "succeeded", operation_id: "op_1" }], "127.0.0.1"));
  render(<Shell />);
  await screen.findByTestId("meeting-row-a");
  fireEvent.click(within(screen.getByTestId("meeting-row-a")).getByRole("button", { name: /Standup/ }));
  await screen.findByTestId("meeting-summary-text");
  fireEvent.click(screen.getByRole("tab", { name: /Review/i }));
  await screen.findByTestId("review-receipt");
  // Review's own foot names the host; the strip keeps its own chip because
  // the foot it was checked against is gone. Never the raw IP.
  const strip = document.querySelector(".meetings-detail-facts");
  expect(strip?.querySelector(".gadget-chip-egress")?.textContent).toContain("THIS DEVICE");
  expect(chips().join(" ")).not.toContain("127.0.0.1");
});
