// PHILO-15-07 (Astra r1 on #982): rendered fences. B15: the footer receipt
// is bound to its run (meeting id + job id) and renders QUEUED → RAN;
// another meeting's completion never touches it. B01: the record header's
// unclear lamp reads ONE source, and a fresh detail's zero is authoritative.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
