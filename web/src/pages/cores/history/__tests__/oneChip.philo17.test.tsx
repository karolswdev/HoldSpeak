// PHILO-17 (U16, Astra r1 M3): the meeting names its summary engine ONCE.
// A rendered fence over the composed Meetings face: list → open meeting →
// Outcomes. The window foot names an external host; the row, the record's
// strip and its summary slab do not repeat a succeeded run on that host. A
// failed attempt and a different host stay. Same-device work has no badge.
//
// PHILO-17 meetingwin: the open meeting is its own window (MeetingRecord);
// its foot is the window foot. The list and the window are fenced apart.
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { HistoryCore } from "../../HistoryCore";
import { MeetingRecord } from "../MeetingRecord";
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
    if (path.split("?")[0] === "/api/meetings/a") return row as never;
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

function Shell({ open = false }: { open?: boolean }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setWings}>
      {wings}
      {open ? <MeetingRecord meetingId="a" onClose={() => undefined} /> : <HistoryCore />}
    </WingSlotContext.Provider>
  );
}

/** Every egress chip on the face, by its label. */
function chips(): string[] {
  return Array.from(document.querySelectorAll(".gadget-chip-egress")).map((el) => (el.textContent ?? "").trim());
}

it("list and open meeting: same-device work has no egress chip or loopback address", async () => {
  hub(meeting([{ leg_ordinal: 1, host: "127.0.0.1", outcome: "succeeded", operation_id: "op_1" }], "127.0.0.1"));
  render(<Shell />);
  await screen.findByTestId("meeting-row-a");
  await waitFor(() => expect(chips()).toHaveLength(0));
  expect(chips().join(" ")).not.toContain("127.0.0.1");
  expect(screen.queryByTestId("row-attempts")?.querySelector(".gadget-chip-egress")).toBeNull();
  cleanup();

  // The meeting's own window: its strip and summary slab do not say it again.
  render(<Shell open />);
  await screen.findByTestId("meeting-summary-text");
  expect(chips()).toHaveLength(0);
  expect(screen.queryByTestId("summary-record-attempts")?.querySelector(".gadget-chip-egress")).toBeNull();
  expect(chips().join(" ")).not.toContain("127.0.0.1");
});

it("a failed leg and a different host stay on the open meeting", async () => {
  hub(meeting([
    { leg_ordinal: 1, host: "127.0.0.1", outcome: "failed", operation_id: "op_1" },
    { leg_ordinal: 2, host: "api.example.com", outcome: "succeeded", operation_id: "op_2" },
  ], "api.example.com"));
  render(<Shell open />);
  await screen.findByTestId("meeting-summary-text");
  const slab = screen.getByTestId("summary-record-attempts").textContent ?? "";
  expect(slab).not.toContain("THIS DEVICE");
  expect(slab).toContain("FAILED");
  expect(slab).toContain("api.example.com");
  // The strip names the other host too: it is not the foot's.
  expect(chips().filter((c) => c === "api.example.com").length).toBeGreaterThanOrEqual(2);
});

it("Outcomes is the one review face and reads its own records", async () => {
  hub(meeting([{ leg_ordinal: 1, host: "127.0.0.1", outcome: "succeeded", operation_id: "op_1" }], "127.0.0.1"));
  render(<Shell open />);
  await screen.findByTestId("meeting-summary-text");
  expect(screen.getByRole("tab", { name: "Outcomes" })).toBeTruthy();
  expect(screen.queryByRole("tab", { name: /Review/i })).toBeNull();
  await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/meetings/a/outcome-review"));
  // The strip has no same-device chip. Never the raw IP.
  const strip = document.querySelector(".meetings-detail-facts");
  expect(strip?.querySelector(".gadget-chip-egress")).toBeNull();
  expect(chips().join(" ")).not.toContain("127.0.0.1");
});
