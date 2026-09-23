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
  mockedApiFetch.mockImplementation(async (path: string) => {
    const value = String(path);
    const detailId = value.match(/^\/api\/meetings\/([^/?]+)$/)?.[1];
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
  });
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

function emitRuntime(type: string) {
  for (const handler of [...(runtime.handlers[type] ?? [])]) handler();
}

describe("PHILO-3-02 Arrival summary completion", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
    runtime.handlers = {};
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [] }, updatedAt: null } as never);
  });

  it("renders imported duration and transcript from the producer detail", async () => {
    const imported = caseFor("imported_off");
    commonWire([imported]);
    seat(imported);
    render(<ChairHome />);

    expect(await screen.findByText("35 S")).toBeInTheDocument();
    expect(screen.getByText("16 WORDS")).toBeInTheDocument();
    expect((await screen.findAllByText("We will ship the boundary change on Tuesday.")).length).toBe(2);
    expect(screen.getByTestId("arrival-route")).toHaveTextContent("THIS DEVICE");
    expect(screen.getByTestId("arrival-run-intel")).toBeInTheDocument();
    expect(screen.queryByTestId("meeting-summary-text")).toBeNull();
  });

  it("renders the ready summary and transcript from the producer detail", async () => {
    const ready = caseFor("success");
    commonWire([ready]);
    seat(ready);
    render(<ChairHome />);

    expect(await screen.findByTestId("meeting-summary-text")).toHaveTextContent(
      "The team reviewed the budget.",
    );
    expect(screen.getByTestId("meeting-summary-topics")).toHaveTextContent("BUDGET");
    expect(screen.getByTestId("arrival-attempts")).toHaveTextContent("THIS DEVICE");
    expect(screen.queryByTestId("arrival-summary-status")).toBeNull();
    expect(screen.getByText("16 WORDS")).toBeInTheDocument();
    expect(screen.getAllByText("We will ship the boundary change on Tuesday.").length).toBe(2);
    expect(
      within(screen.getByTestId("arrival-meeting-row")).getByRole("button", {
        name: /^Open$/,
      }),
    ).toBeInTheDocument();
  });

  it("keeps a failed lineage as RETRYING after its scheduled time and names the producer cause", async () => {
    const retry = caseFor("retry");
    commonWire([retry]);
    seat(retry);
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RETRYING"));
    expect(screen.getByTestId("arrival-display")).toHaveTextContent("1 need you");
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent(
      "LAST ATTEMPT · THIS DEVICE",
    );
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent(
      "LAST ERROR · Deferred intel failed: bound analysis did not publish",
    );
    expect(screen.queryByText("Nothing needs you")).toBeNull();
  });

  it("renders the terminal producer failure and keeps the named cause", async () => {
    const failed = caseFor("terminal_failure");
    commonWire([failed]);
    seat(failed);
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("FAILED"));
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent(
      "LAST ATTEMPT · THIS DEVICE",
    );
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent(
      "LAST ERROR · Deferred intel failed after 1 attempt(s): Deferred intel failed: bound analysis did not publish",
    );
    expect(screen.getByTestId("arrival-display")).toHaveTextContent("1 need you");
    expect(screen.queryByText("Nothing needs you")).toBeNull();
  });

  it("keeps a persisted summary visible with a later producer failure", async () => {
    const ready = caseFor("success");
    const failed = caseFor("terminal_failure");
    const mixed = {
      ...failed,
      detail: { ...failed.detail, intel: ready.detail.intel },
      list: { ...failed.list, intel_status: "error" },
    } as SummaryCase;
    commonWire([mixed]);
    seat(mixed);
    render(<ChairHome />);

    expect(await screen.findByTestId("meeting-summary-text")).toHaveTextContent(
      "The team reviewed the budget.",
    );
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent("FAILED");
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent(
      "LAST ERROR · Deferred intel failed after 1 attempt(s): Deferred intel failed: bound analysis did not publish",
    );
    expect(screen.getByTestId("summary-record-attempts")).toHaveTextContent("THIS DEVICE");
  });

  it("reads only the top three visible meeting details per desk refresh", async () => {
    const candidates = summaryWire.cases
      .slice(0, 4)
      .map((candidate, index) =>
        withTestIdentity(candidate, `${candidate.detail.id}-${candidate.state}-${index}`),
      );
    commonWire(candidates);
    seat(...candidates);
    render(<ChairHome />);

    await waitFor(() => expect(detailCalls()).toHaveLength(3));
    expect(new Set(detailCalls()).size).toBe(3);
    const expected = [...candidates]
      .sort((a, b) => new Date(String(b.list.started_at)).getTime() - new Date(String(a.list.started_at)).getTime())
      .slice(0, 3)
      .map((candidate) => `/api/meetings/${candidate.detail.id}`);
    expect(new Set(detailCalls())).toEqual(new Set(expected));
  });

  it("drops a stale response when the visible meeting identity changes", async () => {
    const ready = withTestIdentity(caseFor("success"), "m-summary-ready");
    const running = withTestIdentity(caseFor("running"), "m-summary-running");
    let resolveFirst!: (value: unknown) => void;
    const first = new Promise((resolve) => { resolveFirst = resolve; });
    commonWire([ready, running]);
    mockedApiFetch.mockImplementation(async (path: string) => {
      const value = String(path);
      if (value === `/api/meetings/${ready.detail.id}`) return first as never;
      if (value === `/api/meetings/${running.detail.id}`) return running.detail as never;
      if (value.startsWith("/api/meetings?")) return { meetings: [] } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      if (value === "/api/door") return { board: {}, upcoming: [] } as never;
      return null as never;
    });
    seat(ready);
    render(<ChairHome />);
    seat(running);

    await waitFor(() => expect(screen.getAllByText("We will ship the boundary change on Tuesday.").length).toBe(2));
    resolveFirst(ready.detail);
    await waitFor(() => expect(screen.queryByText("The team reviewed the budget.")).toBeNull());
    expect(screen.queryByText("MEETING DETAIL IDENTITY CHANGED")).toBeNull();
  });

  it("names a response whose identity does not match the requested meeting", async () => {
    const ready = withTestIdentity(caseFor("success"), "m-summary-expected");
    const running = withTestIdentity(caseFor("running"), "m-summary-reply");
    commonWire([ready, running]);
    mockedApiFetch.mockImplementation(async (path: string) => {
      const value = String(path);
      if (value === `/api/meetings/${ready.detail.id}`) return running.detail as never;
      if (value.startsWith("/api/meetings?")) return { meetings: [] } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      if (value === "/api/door") return { board: {}, upcoming: [] } as never;
      return null as never;
    });
    seat(ready);
    render(<ChairHome />);

    expect(await screen.findByTestId("arrival-detail-error")).toHaveTextContent(
      `MEETING DETAIL IDENTITY CHANGED · EXPECTED ${ready.detail.id} · RECEIVED ${running.detail.id}`,
    );
    expect(screen.getByText("SUMMARY · READ FAILED")).toBeInTheDocument();
    expect(screen.getByTestId("arrival-detail-retained")).toHaveTextContent("MEETING KEPT");
    const retainedRow = screen.getByTestId("arrival-meeting-row");
    expect(retainedRow).toHaveTextContent(ready.detail.title);
    const open = within(retainedRow).getByRole("button", { name: /^Open$/ });
    expect(open).toBeEnabled();
    expect(open).toHaveClass("btn");
  });

  it("clicks Run once, then follows desk_changed to a ready summary and durable receipt", async () => {
    const snapshots = [
      withTestIdentity(caseFor("imported_off"), "m-run-success"),
      withTestIdentity(caseFor("running"), "m-run-success"),
      withTestIdentity(caseFor("success"), "m-run-success"),
    ];
    let currentSnapshot = 0;
    commonWire(snapshots);
    const defaultFetch = mockedApiFetch.getMockImplementation()!;
    mockedApiFetch.mockImplementation(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value === "/api/meetings/m-run-success") {
        return snapshots[currentSnapshot].detail as never;
      }
      if (value.endsWith("/intelligence/run")) {
        return {
          job_id: "ij-run-success",
          state: "queued",
          drainer: "running",
          run_receipt: null,
        } as never;
      }
      return defaultFetch(path, init as never) as never;
    });
    const refresh = vi.fn(async () => {
      currentSnapshot = Math.min(currentSnapshot + 1, snapshots.length - 1);
      const snapshot = snapshots[currentSnapshot];
      useDesk.setState({
        items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshot)] },
        updatedAt: Date.now(),
        refresh,
      } as never);
    });
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[0])] },
      updatedAt: Date.now(),
      refresh,
    } as never);
    render(
      <>
        <DeskChangedRefresh />
        <ChairHome />
      </>,
    );

    const run = await screen.findByTestId("arrival-run-intel");
    fireEvent.click(run);
    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/meetings/m-run-success/intelligence/run",
      { method: "POST", json: { expected_selection_hash: snapshots[0].list.planned_route.selection_hash } },
    ));
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RUNNING"));

    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByTestId("meeting-summary-text")).toHaveTextContent(
      "The team reviewed the budget.",
    ));
    expect(
      within(screen.getByTestId("arrival-meeting-row")).getByRole("button", {
        name: /^Open$/,
      }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("arrival-attempts")).toHaveTextContent("THIS DEVICE");
    expect(screen.queryAllByTestId("arrival-run-intel")).toHaveLength(0);
    expect(mockedApiFetch.mock.calls.filter(([path]) => String(path).endsWith("/intelligence/run"))).toHaveLength(1);
  });

  it("keeps the durable receipt and producer cause through retry to terminal failure", async () => {
    const snapshots = [
      withTestIdentity(caseFor("imported_off"), "m-run-failure"),
      withTestIdentity(caseFor("retry"), "m-run-failure"),
      withTestIdentity(caseFor("terminal_failure"), "m-run-failure"),
    ];
    let currentSnapshot = 0;
    commonWire(snapshots);
    const defaultFetch = mockedApiFetch.getMockImplementation()!;
    mockedApiFetch.mockImplementation(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value === "/api/meetings/m-run-failure") {
        return snapshots[currentSnapshot].detail as never;
      }
      if (value.endsWith("/intelligence/run")) {
        return {
          job_id: "ij-run-failure",
          state: "queued",
          drainer: "running",
          run_receipt: null,
        } as never;
      }
      return defaultFetch(path, init as never) as never;
    });
    const refresh = vi.fn(async () => {
      currentSnapshot = Math.min(currentSnapshot + 1, snapshots.length - 1);
      const snapshot = snapshots[currentSnapshot];
      useDesk.setState({
        items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshot)] },
        updatedAt: Date.now(),
        refresh,
      } as never);
    });
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[0])] },
      updatedAt: Date.now(),
      refresh,
    } as never);
    render(
      <>
        <DeskChangedRefresh />
        <ChairHome />
      </>,
    );

    fireEvent.click(await screen.findByTestId("arrival-run-intel"));
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RETRYING"));
    expect(screen.getByTestId("arrival-attempts")).toHaveTextContent("THIS DEVICE");
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent(
      "LAST ERROR · Deferred intel failed: bound analysis did not publish",
    );

    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("FAILED"));
    expect(screen.getByTestId("arrival-attempts")).toHaveTextContent("THIS DEVICE");
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent(
      "LAST ERROR · Deferred intel failed after 1 attempt(s): Deferred intel failed: bound analysis did not publish",
    );
    expect(screen.getByTestId("arrival-display")).toHaveTextContent("1 need you");
    expect(screen.queryAllByTestId("arrival-run-intel")).toHaveLength(0);
    expect(mockedApiFetch.mock.calls.filter(([path]) => String(path).endsWith("/intelligence/run"))).toHaveLength(1);
  });

  it("refreshes running to ready to retry to failed from desk_changed and keeps durable receipts", async () => {
    const snapshots = [
      caseFor("running"),
      caseFor("success"),
      caseFor("retry"),
      caseFor("terminal_failure"),
    ].map((candidate) => ({
      ...candidate,
      list: { ...candidate.list, id: "m-transition" },
      detail: { ...candidate.detail, id: "m-transition" },
    })) as SummaryCase[];
    let current = 0;
    const detailPaths: string[] = [];
    mockedApiFetch.mockImplementation(async (path: string) => {
      const value = String(path);
      if (value === "/api/meetings/m-transition") {
        detailPaths.push(value);
        return snapshots[current].detail as never;
      }
      if (value.startsWith("/api/meetings?")) return { meetings: [snapshots[current].list] } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      if (value === "/api/door") return { board: {}, upcoming: [] } as never;
      return null as never;
    });
    const refresh = vi.fn(async () => {
      useDesk.setState({
        items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[current])] },
        updatedAt: Date.now(),
      } as never);
    });
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[0])] },
      updatedAt: Date.now(),
      refresh,
    } as never);
    render(
      <>
        <DeskChangedRefresh />
        <ChairHome />
      </>,
    );
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RUNNING"));

    current = 1;
    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1), { timeout: 1000 });
    await waitFor(() => expect(screen.getByTestId("meeting-summary-text")).toHaveTextContent("The team reviewed the budget."));
    expect(screen.getByTestId("arrival-attempts")).toHaveTextContent("THIS DEVICE");

    current = 2;
    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(2), { timeout: 1000 });
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RETRYING"));
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent("LAST ATTEMPT · THIS DEVICE");

    current = 3;
    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(3), { timeout: 1000 });
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("FAILED"));
    expect(screen.getByTestId("arrival-summary-status")).toHaveTextContent("LAST ATTEMPT · THIS DEVICE");
    expect(detailPaths).toHaveLength(4);
  });
});
