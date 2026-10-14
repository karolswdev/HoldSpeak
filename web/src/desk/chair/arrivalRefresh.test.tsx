/** HS-201-01 (counsel fix round, 2026-09-19) — the row clears without a
 *  navigation.
 *
 *  Astra finding 1: the Chair read the assignment roster once, on mount.
 *  The owner repaired the meeting path in Models, came back to the same
 *  open Desk, and the row still asked for an engine until something made
 *  the Chair mount again. So the Chair re-reads the roster on the hub's
 *  `desk_changed` frame and when the window takes focus again.
 */
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { EMPTY_ITEMS, fromWireMeeting } from "../api";
import { useDesk } from "../store";
import { ChairHome } from "./ChairHome";
import { asHub } from "../../test/hubNeedsYou";
import { openChairWindows } from "./__tests__/fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));

const frameListeners = new Map<string, Set<(frame: { data: unknown }) => void>>();
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: { data: unknown }) => void) => {
      const set = frameListeners.get(type) ?? new Set();
      set.add(listener);
      frameListeners.set(type, set);
      return () => set.delete(listener);
    },
  }),
  useRuntimeFrame: () => null,
}));

const CAPABILITY = "meeting.deferred_analysis";
const NO_ENGINE = {
  id: CAPABILITY,
  label: "Deferred meeting analysis",
  group: { id: "meetings", label: "Meetings" },
  has_override: false,
  effective: { status: "no_assignment", inherited_from: null, assignment: null, repair: "Choose default" },
  issues: [],
};
const ASSIGNED = {
  ...NO_ENGINE,
  has_override: true,
  effective: { status: "assigned", inherited_from: "capability", assignment: null, repair: null },
};

/** The roster the hub would answer right now; the repair flips it. */
let roster = [NO_ENGINE as Record<string, unknown>];

function wire() {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
    if (String(path) === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: roster, issue_count: 0 } as never;
    if (String(path).startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    return null as never;
  }));
}

function emitDeskChanged() {
  for (const listener of frameListeners.get("desk_changed") ?? []) {
    listener({ data: { kind: "note", id: "n1", op: "update", origin: "agent" } });
  }
}


// PHILO-14 A5: the Needs-you window body is the smart drawer; the SETUP rows
// are its rows (the object, one lamp, one verb) and the head is its display.
const setupRows = () => [...document.querySelectorAll<HTMLElement>(
  '[data-testid="needs-drawer"] .needs-row[data-object-id^="blocker:"]',
)];
const setupRow = () => setupRows()[0] ?? null;

function meetingListWire(id: string, startedAt: string) {
  return {
    id,
    title: `Refresh ${id}`,
    started_at: startedAt,
    ended_at: "2026-10-13T10:30:00Z",
    duration_seconds: 1800,
    segment_count: 1,
    transcriptWords: 17,
    intel_status: "completed",
    has_summary: true,
  };
}

function meetingDetailWire(id: string, startedAt: string) {
  return {
    ...meetingListWire(id, startedAt),
    intel: { summary: `Summary for ${id}`, topics: ["refresh"] },
    segments: [{ text: `Transcript for ${id}.`, speaker: "Me", start_time: 1 }],
  };
}

describe("HS-201-01 the row clears on the OPEN desk", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [] }, updatedAt: null } as never);
    frameListeners.clear();
    roster = [NO_ENGINE as Record<string, unknown>];
    wire();
  });

  it("re-reads the roster when the window takes focus again", async () => {
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");

    // The owner assigns the engine elsewhere (Models, the CLI, an agent),
    // then comes back to this same, never-navigated Desk.
    roster = [ASSIGNED as Record<string, unknown>];
    act(() => { window.dispatchEvent(new Event("focus")); });

    await waitFor(() => expect(setupRow()).toBeNull());
    expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you");
  });

  // Counsel round 2 (condition 1): the product's own return signal, the
  // one Models fires after it applies a set
  // (`features/concierge/useConciergeController.ts:507` ->
  // `desk/returnToTask.ts:113`, event `holdspeak:settings-updated`).
  it("re-reads the roster on the product's settings-updated signal", async () => {
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");

    roster = [ASSIGNED as Record<string, unknown>];
    act(() => { window.dispatchEvent(new Event("holdspeak:settings-updated")); });

    await waitFor(() => expect(setupRow()).toBeNull());
    expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you");
  });

  it("re-reads the roster on the hub's desk_changed frame", async () => {
    render(<ChairHome />);
    await screen.findByText("No engine for summaries");
    expect(frameListeners.get("desk_changed")?.size).toBeGreaterThan(0);

    roster = [ASSIGNED as Record<string, unknown>];
    act(() => { emitDeskChanged(); });

    await waitFor(() => expect(setupRow()).toBeNull(), {
      timeout: 5000,
    });
  });

  it("holds the Week marker through a retained detail refresh and ignores an old generation", async () => {
    const ids = ["m-refresh-a", "m-refresh-b"];
    const starts = ["2026-10-13T10:00:00Z", "2026-10-13T09:00:00Z"];
    const details = Object.fromEntries(ids.map((id, index) => [id, meetingDetailWire(id, starts[index])]));
    let detailCalls = 0;
    const deferred: Array<() => void> = [];
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      const value = String(path);
      const detailId = value.match(/^\/api\/meetings\/([^/?]+)$/)?.[1];
      if (detailId) {
        const detail = details[decodeURIComponent(detailId)];
        detailCalls += 1;
        if (detailCalls <= ids.length) return detail as never;
        return new Promise((resolve) => {
          deferred.push(() => resolve(detail));
        }) as never;
      }
      if (value === "/api/door") return { board: {}, upcoming: [], calendar_configured: true } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      return null as never;
    }));
    const meetings = ids
      .map((id, index) => fromWireMeeting(meetingListWire(id, starts[index])))
      .filter((meeting): meeting is NonNullable<typeof meeting> => meeting !== null);
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: meetings }, updatedAt: 1 } as never);
    render(<ChairHome />);

    const line = await screen.findAllByTestId("arrival-meeting-row").then((rows) => rows[0]);
    const row = line.parentElement!;
    await waitFor(() => expect(line).toHaveTextContent("Summary for m-refresh-a"));
    const open = within(row).getByRole("button", { name: "Open" });
    expect(row).not.toHaveAttribute("data-open");
    expect(within(row).queryByRole("button", { name: /Transcript/ })).toBeNull();
    await waitFor(() => expect(screen.queryByTestId("arrival-week-reading")).toBeNull());

    // A desk refresh starts two replacement reads, but the last details stay
    // visible while those reads are pending.
    act(() => { useDesk.setState({ updatedAt: 2 }); });
    await waitFor(() => expect(detailCalls).toBe(4));
    expect(screen.getByTestId("arrival-week-reading")).toBeInTheDocument();
    expect(screen.getAllByTestId("arrival-meeting-row")[0]).toBe(line);
    expect(within(row).getByRole("button", { name: "Open" })).toBe(open);
    expect(line).toHaveTextContent("Summary for m-refresh-a");
    expect(row).not.toHaveAttribute("data-open");

    // Replace that generation before it answers. Completing the stale reads
    // must not lower the pending count for the current generation.
    act(() => { useDesk.setState({ updatedAt: 3 }); });
    await waitFor(() => expect(detailCalls).toBe(6));
    const stale = deferred.splice(0, ids.length);
    const current = deferred.splice(0, ids.length);
    await act(async () => { stale.forEach((release) => release()); });
    expect(screen.getByTestId("arrival-week-reading")).toBeInTheDocument();
    await act(async () => { current[0](); });
    expect(screen.getByTestId("arrival-week-reading")).toBeInTheDocument();
    await act(async () => { current[1](); });
    await waitFor(() => expect(screen.queryByTestId("arrival-week-reading")).toBeNull());
  });
});
