// PHILO-15-07 (Astra r1 on #982): rendered fences. B15: the footer receipt
// is bound to its run (meeting id + job id) and renders QUEUED → RAN;
// another meeting's completion never touches it. B01: the record header's
// unclear lamp reads ONE source, and a fresh detail's zero is authoritative.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import summaryWire from "../../../../../../tests/fixtures/philo3_summary_wire.json";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { deskQueryClient } from "../../../../lib/queryClient";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { MeetingHeader } from "../MeetingHeader";
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

const route = {
  status: "ready", selection_hash: "sha256:ready", reason_code: null,
  legs: [{ ordinal: 1, host: "192.168.1.43", boundary: "lan" }],
};
function row(id: string, state: string) {
  return {
    id, title: `Meeting ${id}`, started_at: "2026-10-07T10:00:00",
    capture_status: "finalized", intel_status: { state }, duration_seconds: 40,
    transcriptWords: 12, unclearSpans: 0, planned_route: route, run_receipt: null,
  };
}
function hub(states: Record<string, string>, reads: { terminalA: boolean }) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path.startsWith("/api/meetings?")) {
      return { meetings: Object.keys(states).map((id) => row(id, states[id])) } as never;
    }
    const post = path.match(/^\/api\/meetings\/(\w+)\/intelligence\/run$/);
    if (post) {
      states[post[1]] = "queued";
      return { state: "queued", drainer: "running", jobId: `job-${post[1]}` } as never;
    }
    const get = path.match(/^\/api\/meetings\/(\w+)$/);
    if (get) {
      if (get[1] === "a" && states.a === "ready") reads.terminalA = true;
      return row(get[1], states[get[1]]) as never;
    }
    return {} as never;
  });
}

it("renders the footer receipt QUEUED → RAN for the run it names", async () => {
  const states: Record<string, string> = { a: "disabled" };
  hub(states, { terminalA: false });
  render(<HistoryCore />);
  fireEvent.click(within(await screen.findByTestId("meeting-row-a")).getByRole("button", { name: /Run summary/i }));
  await screen.findByText(/^QUEUED \d/);
  states.a = "ready";
  await screen.findByText(/^RAN · \d/, undefined, { timeout: 6000 });
  expect(screen.queryByText(/^QUEUED \d/)).toBeNull();
}, 10000);

it("a completion of meeting A cannot finish the receipt for queued meeting B", async () => {
  const states: Record<string, string> = { a: "disabled", b: "disabled" };
  const reads = { terminalA: false };
  hub(states, reads);
  render(<HistoryCore />);
  fireEvent.click(within(await screen.findByTestId("meeting-row-a")).getByRole("button", { name: /Run summary/i }));
  await screen.findByText(/^QUEUED \d/);
  fireEvent.click(within(await screen.findByTestId("meeting-row-b")).getByRole("button", { name: /Run summary/i }));
  await waitFor(() => expect(states.b).toBe("queued"));
  states.a = "ready";
  await waitFor(() => expect(reads.terminalA).toBe(true), { timeout: 5000 });
  await act(async () => { await new Promise((r) => setTimeout(r, 50)); });
  expect(screen.queryByText(/^RAN ·/)).toBeNull();
  expect(screen.getByText(/^QUEUED \d/)).toBeInTheDocument();
}, 10000);

it("a fresh detail's zero removes a stale list warning", () => {
  const meeting = { id: "m1", title: "Meeting", unclearSpans: 1, intel_status: "disabled" };
  const data = { detail: { ...meeting, unclearSpans: 0 }, startedAt: "2026-10-07T10:00:00", durationS: 30 };
  render(<MeetingHeader meeting={meeting} data={data as never} />);
  expect(screen.queryByTestId("unclear-lamp")).toBeNull();
});

// ── Astra iteration 2 ──────────────────────────────────────────────────

function Shell() {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setWings}>
      {wings}
      <HistoryCore scope="meeting:a" />
    </WingSlotContext.Provider>
  );
}

it("the full parent → Review transition shows QUEUED then RAN in Review, and Review reads again", async () => {
  const states: Record<string, string> = { a: "disabled" };
  let reviewReads = 0;
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path.startsWith("/api/meetings?")) return { meetings: [row("a", states.a)] } as never;
    if (path.endsWith("/intelligence/run")) {
      states.a = "queued";
      return { state: "queued", drainer: "running", jobId: "job-a" } as never;
    }
    if (path === "/api/meetings/a") {
      return { ...row("a", states.a), segments: [{ text: "Priya owns the migration.", start_time: 0, end_time: 8 }] } as never;
    }
    if (path.endsWith("/outcome-review")) {
      reviewReads += 1;
      const done = states.a === "ready";
      return {
        meeting_id: "a", title: "Meeting a", started_at: "2026-10-07T10:00:00", project: null,
        job: { job_id: "job-a", status: done ? "succeeded" : "failed", attempt: 1, same_job: false, last_error: null, model_host: "192.168.1.43", extraction_model: "test", updated_at: "2026-10-07T10:00:00" },
        coverage: { turns: 1, read: done ? 1 : 0, state: done ? "available" : "failed" },
        extracted_at: null, proposals: [],
      } as never;
    }
    return {} as never;
  });
  render(<Shell />);
  await screen.findByTestId("meeting-row-a");
  fireEvent.click(screen.getByRole("tab", { name: /Review/i }));
  fireEvent.click(await screen.findByRole("button", { name: "Re-read: Transcript" }));
  await waitFor(() => expect(screen.getByTestId("review-receipt")).toHaveTextContent(/^QUEUED /));
  const readsBefore = reviewReads;
  states.a = "ready";
  await waitFor(
    () => expect(screen.getByTestId("review-receipt")).toHaveTextContent(/^RAN · \d/),
    { timeout: 6000 },
  );
  await waitFor(() => expect(reviewReads).toBeGreaterThan(readsBefore));
}, 12000);

type WireCase = { state: string; list: Record<string, unknown>; detail: Record<string, unknown> };
const wires = Object.fromEntries(
  (summaryWire as { cases: WireCase[] }).cases.map((c) => [c.state, c]),
) as Record<string, WireCase>;

it("a reload during a run recovers its timed receipt from the real producer rows", async () => {
  let phase = "imported_off";
  const id = String(wires.success.detail.id);
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path.startsWith("/api/meetings?")) return { meetings: [wires[phase].list] } as never;
    if (path.endsWith("/intelligence/run")) {
      phase = "running";
      return { state: "queued", drainer: "running", jobId: "job-x" } as never;
    }
    if (path === `/api/meetings/${id}`) return wires[phase].detail as never;
    return {} as never;
  });
  const first = render(<HistoryCore />);
  fireEvent.click(within(await screen.findByTestId(`meeting-row-${id}`)).getByRole("button", { name: /Run summary/i }));
  await screen.findByText(/^QUEUED \d/);
  first.unmount();
  deskQueryClient.clear();
  render(<HistoryCore />);
  await screen.findByTestId(`meeting-row-${id}`);
  // The remount adopts the active run from the durable row, beside the count.
  const queued = await screen.findByTestId("meetings-run-receipt");
  expect(queued.textContent).toMatch(/^QUEUED \d/);
  expect(queued.closest("[role=status]")?.textContent).toMatch(/^1 RECORD · QUEUED/);
  phase = "success";
  await act(async () => {
    window.dispatchEvent(new Event("focus"));
  });
  await screen.findByText(/^RAN · \d/, undefined, { timeout: 6000 });
}, 12000);

function successRowAt(at: string): Record<string, unknown> {
  const list = wires.success.list;
  return { ...list, intel_job: { ...(list.intel_job as Record<string, unknown>), updated_at: at } };
}

function mountWithOnly(rowWire: Record<string, unknown>) {
  const id = String(rowWire.id);
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (path.startsWith("/api/meetings?")) return { meetings: [rowWire] } as never;
    if (path === `/api/meetings/${id}`) return wires.success.detail as never;
    return {} as never;
  });
  render(<HistoryCore />);
  return id;
}

it("a reload after today's run shows the record count first and the RAN receipt beside it", async () => {
  const id = mountWithOnly(successRowAt(new Date().toISOString()));
  await screen.findByTestId(`meeting-row-${id}`);
  const receipt = await screen.findByTestId("meetings-run-receipt");
  expect(receipt.textContent).toMatch(/^RAN · \d/);
  const line = receipt.closest("[role=status]");
  expect(line?.textContent).toMatch(/^1 RECORD · RAN · \d/);
});

it("a reload with only an old run shows the record count alone", async () => {
  const id = mountWithOnly(successRowAt("2020-01-01T09:00:00"));
  await screen.findByTestId(`meeting-row-${id}`);
  await screen.findByText("1 RECORD");
  expect(screen.queryByTestId("meetings-run-receipt")).toBeNull();
  expect(screen.queryByText(/^RAN · /)).toBeNull();
});
