// PHILO-13-11 (C1, slice two) — THE CHAIR AS WINDOWS, to the owner-ratified
// canvas (2026-10-02: "Ratify, build it"; Capture "Yes"). Red on bbf7e9a4
// (the Chair was one scrolling page), green after.
//
//   1. Four DeskWindowFrame windows — Needs you, Brief, The week, Capture —
//      each holding its sections; registered (front window, screen title)
//      with no Dock chip; Needs you is the front Chair window.
//   2. The work first (R3): the Needs-you window leads with the headline and
//      the actions; SETUP is below the actions.
//   3. R1: Close closes; the closed window leaves a reopen Button in its
//      place; Window ▸ Chair lists the four with a check on the open ones.
//   4. R2 (393): one window at a time, Needs you first; the Speak AppIcon's
//      key ("dictate") opens Capture on demand.
//   5. The A3-W ledger: no `Run summary` beside SUMMARY STORED.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { useDesk } from "../../store";
import { ChairHome } from "../ChairHome";
import { DeskMenuBar } from "../../components/DeskMenuBar";
import {
  frontWindowId,
  registrySnapshot,
  dockSnapshot,
} from "../../components/window/windowRegistry";
import { verbById } from "../../verbRegistry";
import { openSurfaceOr } from "../../shell";
import { useChairWindows } from "../chairWindows";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const ROUTE = {
  status: "ready",
  reason_code: null,
  selection_hash: "sha256:chair",
  legs: [{ ordinal: 1, host: "192.168.1.43", boundary: "lan" }],
};

const NEEDS = {
  count: 1,
  items: [{
    id: "item-1", projectId: "p1", projectName: "Q4 Platform", ref: "item-1",
    title: "Sam: send the status by Thursday", why: "DUE TODAY", ageToken: "",
    since: "2026-09-04T09:00:00", source: "github", verbHref: "https://x/1",
    severity: "warning", rankClass: "due_today",
  }],
  coverage: [],
};

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    const p = String(path);
    // a cold roster: the meeting path names its SETUP row
    if (p === "/api/inference/assignments")
      return {
        schema: "InferenceAssignmentSummary@1", rows: [], issue_count: 0,
        task_overrides: [{ id: "meeting.deferred_analysis", has_override: false, effective: { status: "unassigned" } }],
      };
    if (p.startsWith("/api/desk/needs-you")) return NEEDS;
    if (p.startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
    return null;
  });
}

function setCompact(on: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: on && query.includes("max-width: 720px"),
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

const region = (name: string) => screen.queryByRole("region", { name });
const realMatchMedia = window.matchMedia;

beforeEach(() => {
  setCompact(false);
  localStorage.clear();
  useChairWindows.setState({ closed: {}, phone: "chair:needs" });
  useDesk.setState({
    panelRects: {}, panelSaved: [], panelOrder: [], panelMin: [], panelMax: [],
    items: { meeting: [] } as never,
  });
  vi.mocked(apiFetch).mockReset();
  wire();
});
afterEach(() => {
  window.matchMedia = realMatchMedia;
});

describe("PHILO-13-11 slice two — the Chair as windows", () => {
  it("renders four windows, each holding its sections", async () => {
    render(<ChairHome />);
    for (const name of ["Needs you", "Brief", "The week", "Capture"]) {
      const win = region(name);
      expect(win, name).toBeTruthy();
      expect(win!.classList.contains("desk-window-shell")).toBe(true);
      expect(within(win!).getByRole("button", { name: `Close ${name}` })).toBeTruthy();
      expect(within(win!).getByRole("button", { name: `Zoom ${name}` })).toBeTruthy();
      // design §3: every window carries the full set (depth withheld until C2)
      expect(within(win!).getByRole("button", { name: `Iconify ${name}` })).toBeTruthy();
    }
    expect(within(region("Needs you")!).getByTestId("arrival-headline")).toBeTruthy();
    expect(within(region("Brief")!).getByTestId("arrival-brief")).toBeTruthy();
    expect(within(region("Capture")!).getByTestId("arrival-capture-bar")).toBeTruthy();
    expect(within(region("Capture")!).getByRole("button", { name: "Write a thought" })).toBeTruthy();
    expect(within(region("Capture")!).getByRole("button", { name: "Record meeting" })).toBeTruthy();
    expect(within(region("Capture")!).getByRole("button", { name: "Schedule" })).toBeTruthy();
    // registered for the front and the screen title; no Dock chip until iconified
    const ids = registrySnapshot.map((w) => w.id);
    for (const id of ["chair:needs", "chair:brief", "chair:week", "chair:capture"]) {
      expect(ids).toContain(id);
      expect(dockSnapshot.map((w) => w.id)).not.toContain(id);
    }
    expect(frontWindowId()).toBe("chair:needs");
    expect(region("Needs you")!.classList.contains("is-front")).toBe(true);
    expect(document.querySelectorAll(".desk-window-shell.is-front")).toHaveLength(1);
  });

  it("the work first: the headline and the actions lead; SETUP is below the actions", async () => {
    render(<ChairHome />);
    const needs = region("Needs you")!;
    await waitFor(() => expect(within(needs).getByTestId("arrival-needs-you")).toBeTruthy());
    await waitFor(() => expect(within(needs).getByTestId("arrival-blocker")).toBeTruthy());
    const body = within(needs).getByTestId("chair-window-body-needs");
    expect(body.firstElementChild?.getAttribute("data-testid")).toBe("arrival-headline");
    const actions = within(needs).getByTestId("arrival-needs-you");
    const setup = within(needs).getByTestId("arrival-blocker");
    expect(actions.compareDocumentPosition(setup) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("Close closes; a reopen Button stands in its place; Window ▸ Chair checks the open ones", async () => {
    render(<><DeskMenuBar /><ChairHome /></>);
    fireEvent.click(within(region("Brief")!).getByRole("button", { name: "Close Brief" }));
    await waitFor(() => expect(region("Brief")).toBeNull());
    expect(registrySnapshot.map((w) => w.id)).not.toContain("chair:brief");
    const reopen = screen.getByTestId("chair-reopen-brief");
    expect(within(reopen).getByRole("button", { name: "Open Brief" })).toBeTruthy();

    // the verbs behind Window ▸ Chair
    expect(verbById("chair.window.brief")!.checked!({ selectedRef: null })).toBe(false);
    expect(verbById("chair.window.needs")!.checked!({ selectedRef: null })).toBe(true);
    // the menu face: Window holds ONE Chair submenu
    const title = screen.getByRole("button", { name: "Window" });
    fireEvent.click(title, { detail: 0 });
    const labels = screen.getAllByRole("menuitem").map((el) => el.textContent ?? "");
    expect(labels.filter((t) => t.includes("Chair"))).toHaveLength(1);
    fireEvent.keyDown(document, { key: "Escape" });

    act(() => verbById("chair.window.brief")!.run({ selectedRef: null }));
    await waitFor(() => expect(region("Brief")).toBeTruthy());
    expect(frontWindowId()).toBe("chair:brief");
    expect(screen.queryByTestId("chair-reopen-brief")).toBeNull();

    // the reopen Button reopens too
    fireEvent.click(within(region("The week")!).getByRole("button", { name: "Close The week" }));
    await waitFor(() => expect(region("The week")).toBeNull());
    fireEvent.click(within(screen.getByTestId("chair-reopen-week")).getByRole("button", { name: "Open The week" }));
    await waitFor(() => expect(region("The week")).toBeTruthy());
  });

  it("Iconify falls to a Dock chip; Window ▸ Chair brings it back", async () => {
    render(<ChairHome />);
    fireEvent.click(within(region("Brief")!).getByRole("button", { name: "Iconify Brief" }));
    await waitFor(() => expect(useDesk.getState().panelMin).toContain("chair:brief"));
    expect(dockSnapshot.map((w) => w.id)).toContain("chair:brief");
    expect(dockSnapshot.map((w) => w.id)).not.toContain("chair:needs");
    // iconified is still open: checked in Window ▸ Chair, no reopen Button
    expect(verbById("chair.window.brief")!.checked!({ selectedRef: null })).toBe(true);
    expect(screen.queryByTestId("chair-reopen-brief")).toBeNull();
    act(() => verbById("chair.window.brief")!.run({ selectedRef: null }));
    await waitFor(() => expect(useDesk.getState().panelMin).not.toContain("chair:brief"));
    expect(dockSnapshot.map((w) => w.id)).not.toContain("chair:brief");
    expect(frontWindowId()).toBe("chair:brief");
  });

  it("393: one window at a time, Needs you first; the Dock's Speak opens Capture, Go ▸ Speak does not", async () => {
    setCompact(true);
    render(<ChairHome />);
    expect(region("Needs you")).toBeTruthy();
    for (const name of ["Brief", "The week", "Capture"]) expect(region(name)).toBeNull();
    // Go ▸ Speak, the verb and ⌘1 ask the shell for "dictate" with no Dock
    // press: Capture stays closed (the Speak window keeps its door).
    act(() => openSurfaceOr("dictate", "/dictation"));
    expect(region("Capture")).toBeNull();
    expect(region("Needs you")).toBeTruthy();
    // PHILO-13-13 C3-W: a click on a Speak-labelled Dock element is no
    // longer a signal (the 1.5 s press window is retired) ...
    const dock = document.createElement("div");
    dock.className = "desk-dock";
    const speak = document.createElement("button");
    speak.setAttribute("aria-label", "Speak");
    dock.appendChild(speak);
    document.body.appendChild(dock);
    fireEvent.click(speak);
    act(() => openSurfaceOr("dictate", "/dictation"));
    dock.remove();
    expect(region("Capture")).toBeNull();
    // ... the Dock's explicit launch origin (#744) is the one signal.
    act(() => openSurfaceOr("dictate", "/dictation", undefined, { origin: "dock" }));
    await waitFor(() => expect(region("Capture")).toBeTruthy());
    expect(region("Needs you")).toBeNull();
    // closing Capture gives the work area back to the next Chair window
    fireEvent.click(within(region("Capture")!).getByRole("button", { name: "Close Capture" }));
    await waitFor(() => expect(region("Needs you")).toBeTruthy());
    // Window ▸ Chair at 393 has no Capture row (Speak opens it)
    expect(verbById("chair.window.capture")!.wide).toBe(true);
    // with every Chair window closed, a reopen Button for each
    fireEvent.click(within(region("Needs you")!).getByRole("button", { name: "Close Needs you" }));
    await waitFor(() => expect(region("Brief")).toBeTruthy());
    fireEvent.click(within(region("Brief")!).getByRole("button", { name: "Close Brief" }));
    await waitFor(() => expect(region("The week")).toBeTruthy());
    fireEvent.click(within(region("The week")!).getByRole("button", { name: "Close The week" }));
    const list = await screen.findByTestId("chair-reopen-list");
    expect(within(list).getAllByRole("button").map((b) => b.textContent)).toEqual(["Needs you", "Brief", "The week"]);
  });

  it("no Run summary beside SUMMARY STORED (the stored fact drives the verb)", async () => {
    useDesk.setState({
      items: {
        meeting: [{
          kind: "meeting", id: "m-1", title: "Census standup",
          startedAt: "2026-09-19T09:00:00Z", endedAt: "2026-09-19T09:30:00Z",
          durationSeconds: 1800, intelStatus: "disabled", transcriptWords: 1204,
          hasSummary: true, plannedRoute: ROUTE, runReceipt: null,
        }],
      } as never,
    });
    render(<ChairHome />);
    const row = await screen.findByTestId("arrival-meeting-row");
    expect(within(row).getByTestId("arrival-meeting-badge").textContent).toBe("SUMMARY STORED");
    expect(within(row).queryByTestId("arrival-run-intel")).toBeNull();
    expect(within(row).getByRole("button", { name: "Open" })).toBeTruthy();
  });

  it("the ledger row: SUMMARY STORED from the detail read had a Run summary beside it", async () => {
    useDesk.setState({
      items: {
        meeting: [{
          kind: "meeting", id: "m-2", title: "Ledger cutover sync",
          startedAt: "2026-09-19T09:00:00Z", endedAt: "2026-09-19T09:30:00Z",
          durationSeconds: 1800, intelStatus: "disabled", transcriptWords: 40,
          plannedRoute: ROUTE, runReceipt: null,
        }],
      } as never,
    });
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      if (String(path) === "/api/meetings/m-2")
        return {
          id: "m-2", title: "Ledger cutover sync", started_at: "2026-09-19T09:00:00Z",
          ended_at: "2026-09-19T09:30:00Z", duration_seconds: 1800, intel_status: "disabled",
          transcriptWords: 40, planned_route: ROUTE,
          intel: { summary: "Dual-write is stable.", topics: [] },
          segments: [{ text: "Dual-write is stable.", speaker: "Me", start_time: 1 }],
        };
      return (base as (p: string, i?: unknown) => Promise<unknown>)(path, init);
    });
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge").textContent).toBe("SUMMARY STORED"));
    const row = screen.getByTestId("arrival-meeting-row");
    expect(within(row).queryByTestId("arrival-run-intel")).toBeNull();
    expect(within(row).getByRole("button", { name: "Open" })).toBeTruthy();
  });
});
