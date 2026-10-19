// PHILO-3-02 — Arrival reads the durable meeting detail on desk refresh.
// These fences consume the summary_detail service producer wire directly.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import summaryWire from "../../../../tests/fixtures/philo3_summary_wire.json";
import { apiFetch } from "../../lib/api";
import { EMPTY_ITEMS, fromWireMeeting } from "../api";
import { useDesk } from "../store";
import { DeskChangedRefresh } from "../useDeskChangedRefresh";
import { ChairHome } from "./ChairHome";
import { MeetingRecord } from "../../pages/cores/history/MeetingRecord";
import { asHub } from "../../test/hubNeedsYou";
import { openChairWindows } from "./__tests__/fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

const runtime = vi.hoisted(() => ({
  handlers: {} as Record<string, Array<() => void>>,
}));

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: () => void) => {
      const handlers = runtime.handlers[type] ?? [];
      handlers.push(handler);
      runtime.handlers[type] = handlers;
      return () => {
        runtime.handlers[type] = (runtime.handlers[type] ?? []).filter((entry) => entry !== handler);
      };
    },
  }),
  useRuntimeFrame: () => null,
}));

const mockedApiFetch = vi.mocked(apiFetch);
type SummaryCase = (typeof summaryWire.cases)[number];

function caseFor(state: SummaryCase["state"]): SummaryCase {
  const found = summaryWire.cases.find((candidate) => candidate.state === state);
  if (!found) throw new Error(`Missing summary wire case: ${state}`);
  return found;
}

/**
 * The producer fixture records five lifecycle snapshots for one real meeting,
 * so all snapshots intentionally share one wire id. These fences sometimes
 * need several simultaneous rows or an identity change. Normalize only the
 * id for those test arrangements; producer state, cause, receipt, and content
 * remain byte-for-byte from the fixture.
 */
function withTestIdentity(candidate: SummaryCase, id: string): SummaryCase {
  return {
    ...candidate,
    list: { ...candidate.list, id },
    detail: { ...candidate.detail, id },
    recovery: { ...candidate.recovery, meeting_id: id },
  } as SummaryCase;
}

function meetingFor(candidate: SummaryCase) {
  const meeting = fromWireMeeting(candidate.list);
  if (!meeting) throw new Error(`Invalid summary wire list: ${candidate.state}`);
  return meeting;
}

function detailsFor(...candidates: SummaryCase[]) {
  return Object.fromEntries(candidates.map((candidate) => [candidate.detail.id, candidate.detail]));
}

function commonWire(candidates: SummaryCase[]) {
  const details = detailsFor(...candidates);
  mockedApiFetch.mockImplementation(asHub(async (path: string) => {
    const value = String(path);
    const recoveryId = value.match(/^\/api\/meetings\/([^/?]+)\/intel-recovery$/)?.[1];
    if (recoveryId) return candidates.find((candidate) => candidate.detail.id === decodeURIComponent(recoveryId))?.recovery as never;
    const detailId = value.match(/^\/api\/meetings\/([^/?]+)(?:\?include_parked=true)?$/)?.[1];
    if (detailId) return details[decodeURIComponent(detailId)] as never;
    if (value.startsWith("/api/meetings?")) {
      return { meetings: candidates.map((candidate) => candidate.list) } as never;
    }
    if (value === "/api/inference/assignments") {
      return { rows: [], task_overrides: [], issue_count: 0 } as never;
    }
    if (value.startsWith("/api/desk/needs-you")) {
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    }
    if (value === "/api/door") return { board: {}, upcoming: [] } as never;
    return null as never;
  }));
}

function seat(...candidates: SummaryCase[]) {
  useDesk.setState({
    items: { ...EMPTY_ITEMS, meeting: candidates.map(meetingFor) },
    updatedAt: Date.now(),
  } as never);
}

function detailCalls() {
  return mockedApiFetch.mock.calls
    .map(([path]) => String(path))
    .filter((path) => /^\/api\/meetings\/[^/?]+$/.test(path));
}

function expectProducerCause(candidate: SummaryCase) {
  const cause = String(candidate.detail.intel_job?.last_error ?? "").trim();
  const status = screen.getByTestId("arrival-meeting-row");
  expect(status).toHaveTextContent("PROVIDER FAILED");
  expect(status.parentElement).not.toHaveAttribute("data-open");
  expect(screen.getByTestId("arrival-attempts")).toBeInTheDocument();
  expect(cause).toBe("PROVIDER FAILED");
  expect(status.textContent ?? "").not.toMatch(/ATTEMPT\(S\)|DEFERRED INTEL|BOUND ANALYSIS|PUBLISH/i);
}

function emitRuntime(type: string) {
  for (const handler of [...(runtime.handlers[type] ?? [])]) handler();
}

describe("PHILO-3-02 Arrival summary completion", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
    runtime.handlers = {};
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [] }, updatedAt: null } as never);
  });

  it("the actual Meeting record owns the full producer summary, topics and user-open transcript", async () => {
    const ready = caseFor("success");
    commonWire([ready]);
    render(<MeetingRecord meetingId={ready.detail.id} onClose={() => undefined} />);
    expect(await screen.findByTestId("meeting-summary-text")).toHaveTextContent("The team reviewed the budget.");
    expect(screen.getByTestId("meeting-summary-topics")).toHaveTextContent("BUDGET");
    expect(screen.getAllByTestId("meeting-summary-text")).toHaveLength(1);
    expect(screen.getAllByText("The team reviewed the budget.")).toHaveLength(1);
    expect(screen.getByTestId("summary-record-attempts")).not.toHaveTextContent("THIS DEVICE");
    const transcript = await screen.findByRole("button", { name: /Transcript/ });
    expect(transcript).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(transcript);
    expect(screen.getAllByText("We will ship the boundary change on Tuesday.")).toHaveLength(2);
    expect(transcript).toHaveAttribute("aria-expanded", "true");
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
  });

  it.each(["retry", "terminal_failure"] as const)("the actual Meeting record retains %s producer cause, recovery and run receipt", async (state) => {
    const snapshot = caseFor(state);
    commonWire([snapshot]);
    render(<MeetingRecord meetingId={snapshot.detail.id} onClose={() => undefined} />);
    if (state === "retry") {
      expect(await screen.findByTestId("meeting-summary-state")).toHaveTextContent("SUMMARY QUEUED");
      expect(await screen.findByTestId("meetings-run-receipt")).toHaveTextContent(/^QUEUED \d/);
      expect(screen.queryByRole("region", { name: "Meeting intelligence recovery" })).toBeNull();
      expect(snapshot.recovery.remaining.detail).toBe("PROVIDER FAILED");
      return;
    }
    const cause = await screen.findByTitle("PROVIDER FAILED");
    expect(cause).toHaveTextContent("NOT DONE");
    const recovery = screen.getByRole("region", { name: "Meeting intelligence recovery" });
    expect(recovery).toHaveTextContent("KEPT 2 SEGMENTS");
    expect(within(recovery).getByTestId("recovery-attempts")).not.toHaveTextContent("THIS DEVICE");
    expect(within(recovery).getByRole("button", { name: "Retry" })).toBeEnabled();
    expect(within(recovery).getByRole("button", { name: "Skip" })).toBeEnabled();
  });

  it("the actual Meeting record keeps the user's transcript open while a producer refresh is pending", async () => {
    const ready = caseFor("success");
    const refreshed = { ...ready.detail, intel: { ...ready.detail.intel, summary: "The team reviewed the launch." } };
    commonWire([ready]);
    const base = mockedApiFetch.getMockImplementation()!;
    let pending = false;
    let release!: (value: unknown) => void;
    const refresh = new Promise((resolve) => { release = resolve; });
    mockedApiFetch.mockImplementation(async (path, init) => {
      if (pending && new RegExp(`^/api/meetings/${ready.detail.id}(?:\\?|$)`).test(String(path))) return refresh as never;
      return base(path, init);
    });
    render(<MeetingRecord meetingId={ready.detail.id} onClose={() => undefined} />);
    expect(await screen.findByTestId("meeting-summary-text")).toHaveTextContent("The team reviewed the budget.");
    fireEvent.click(await screen.findByRole("button", { name: /Transcript/ }));
    expect(screen.getByRole("button", { name: /Transcript/ })).toHaveAttribute("aria-expanded", "true");
    pending = true;
    window.dispatchEvent(new Event("focus"));
    await waitFor(() => expect(mockedApiFetch.mock.calls.filter(([path]) => String(path).includes("include_parked=true")).length).toBeGreaterThan(1));
    expect(screen.getByTestId("meeting-summary-text")).toHaveTextContent("The team reviewed the budget.");
    expect(screen.getByRole("button", { name: /Transcript/ })).toHaveAttribute("aria-expanded", "true");
    release(refreshed);
    await waitFor(() => expect(screen.getByTestId("meeting-summary-text")).toHaveTextContent("The team reviewed the launch."));
    expect(screen.getByRole("button", { name: /Transcript/ })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getAllByText("We will ship the boundary change on Tuesday.")).toHaveLength(2);
  });

});
