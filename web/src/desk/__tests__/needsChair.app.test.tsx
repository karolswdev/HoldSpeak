// The Chair app (test diet, 2026-10-11): the fresh arrival, moved off the
// browser. The real ChairHome, its real window store and the real menu bar;
// only `apiFetch` is mocked, with the hub's answers (the cold roster shape of
// `/api/inference/assignments`, as the Chair window fence uses it).
//
// replaces: tests/e2e/test_philo14_a1_fresh_arrival_glass.py::TestFreshArrival::test_the_fresh_desk_reaches_every_chair_window
// Facts that already have a successor elsewhere (cited, not repeated):
//  - the People drawer opens the People window on the desk (Enter):
//    web/src/desk/screen/__tests__/Screen.test.tsx:254-255
//  - Needs you from its drawer (Enter): chairWindows.philo1311.test.tsx:175-179
//  - 393 Go lists Needs you, Brief, The week, Capture first:
//    web/src/desk/components/window/phoneRing.test.tsx:198-206
//  - 393 the Dock's Speak opens Capture: chairWindows.philo1311.test.tsx:221-223
//  - TALK is one press on the screen: Screen.test.tsx:351
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { recordedGet } from "../../test/recordedHub";
import RECORDED from "./fixtures/needsYou.recorded.json";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

/** A cold HOME: the hub's own answers on a fresh HOME and database, recorded by
 *  scripts/record_needs_you_fixture.py (`cold`). The roster's summary row carries
 *  the producer's `effective.status: "no_assignment"` and its `queue` projection
 *  (inference_assignment_service.py `_queue_projection`), so the Chair's row reads
 *  the queue branch of meetingPathBlocker.ts. */
function coldHub() {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(RECORDED.cold.gets, path) as never);
}

const region = (name: string) => screen.queryByRole("region", { name });

beforeEach(() => {
  localStorage.clear();
  vi.mocked(apiFetch).mockReset();
  coldHub();
});

describe("Chair app: the fresh arrival", () => {
  it("a desk that remembers nothing opens with no Chair window", async () => {
    vi.resetModules();
    const fresh = await import("../chair/chairWindows");
    for (const id of ["chair:needs", "chair:brief", "chair:week", "chair:capture"])
      expect(fresh.isChairWindowOpen(id), id).toBe(false);
    const { ChairHome } = await import("../chair/ChairHome");
    render(<ChairHome />);
    expect(document.querySelectorAll(".desk-window-shell.chair-window")).toHaveLength(0);
    expect(screen.getByTestId("desk-screen")).toBeTruthy();
  });

  it("1440: with a window open, Window ▸ Desk reaches Today, Needs you and Capture (no Brief, no The week); Needs you names the No engine SETUP row", async () => {
    vi.resetModules();
    const { ChairHome } = await import("../chair/ChairHome");
    const { DeskMenuBar } = await import("../components/DeskMenuBar");
    const { isChairWindowOpen } = await import("../chair/chairWindows");
    const { useDesk } = await import("../store");
    render(<><DeskMenuBar /><ChairHome /></>);
    expect(document.querySelectorAll(".desk-window-shell.chair-window")).toHaveLength(0);

    const pick = async (name: string, opened: () => unknown = () => region(name)) => {
      fireEvent.click(screen.getByRole("button", { name: "Window" }), { detail: 0 });
      const menu = screen.getByRole("menu", { name: "Window menu" });
      const chair = within(menu).getAllByRole("menuitem")
        .find((h) => h.getAttribute("aria-haspopup") === "menu" && /^Desk/.test(h.textContent ?? ""));
      expect(chair, "Window holds the Desk submenu").toBeTruthy();
      fireEvent.click(chair!);
      const rows = within(menu).getAllByRole("menuitemcheckbox")
        .map((h) => h.querySelector(".desk-menu-label")?.textContent?.trim());
      // Betterment daily D5: Today, Needs you, Capture; never Brief or The week.
      expect(rows.filter((label) => ["Today", "Needs you", "Brief", "The week", "Capture"].includes(label ?? "")))
        .toEqual(["Today", "Needs you", "Capture"]);
      const row = within(menu).getAllByRole("menuitemcheckbox")
        .find((h) => h.querySelector(".desk-menu-label")?.textContent?.trim() === name)!;
      act(() => void fireEvent.click(row));
      await waitFor(() => expect(opened(), name).toBeTruthy());
    };

    // Betterment shell S0: with no window open, the Window menu is one line.
    fireEvent.click(screen.getByRole("button", { name: "Window" }), { detail: 0 });
    const empty = screen.getByRole("menu", { name: "Window menu" });
    expect(empty.textContent).toBe("No windows open");
    expect(within(empty).queryAllByRole("menuitem")).toHaveLength(0);
    fireEvent.keyDown(document.body, { key: "Escape" });
    // Needs you opens from its registry verb (the bell's and Go's door) ...
    const { verbById } = await import("../verbRegistry");
    act(() => verbById("chair.window.needs")!.run({ selectedRef: null }));
    await waitFor(() => expect(region("Needs you"), "Needs you").toBeTruthy());
    // ... and with a window open, Window ▸ Desk reaches the three.
    await pick("Needs you");
    expect(isChairWindowOpen("chair:needs")).toBe(true);
    const setup = await waitFor(() => {
      const row = region("Needs you")!.querySelector('[data-testid="needs-row"][data-object-id^="blocker:"]');
      expect(row, "the SETUP row of the cold HOME").toBeTruthy();
      return row as HTMLElement;
    });
    // The recorded roster: speech has an engine, the summary queue has none.
    expect(setup.textContent).toContain("No engine for summaries");
    expect(setup.textContent).toContain("Choose an engine");

    await pick("Today", () => useDesk.getState().pullouts.some((w) => w.id === "intelligence:desk"));
    await pick("Capture");
    expect(within(region("Capture")!).getByTestId("arrival-capture-bar")).toBeTruthy();
  });
});

// Astra r2 (#1101) MUST 4: the roster shape is the producer's. On the desk the
// Chair draws the hub's own `blockers` (needsYou.ts reads them from
// GET /api/desk/needs-you; the hub computes them in
// holdspeak/services/needs_you_membership.py `meeting_path_blockers`), so the
// replay above covers the production row. The browser statement of the same
// rule, meetingPathBlocker.ts, runs where the desk composes needs-you from its
// sources (`computeNeedsYou`); here it reads the SAME recorded roster, and its
// queue branch decides.
describe("Chair app: the cold roster through meetingPathBlockers", () => {
  it("the recorded cold roster (effective no_assignment, queue no_assignment) blocks summaries only", async () => {
    const { meetingPathBlockers, SUMMARY_CAPABILITY } = await import("../chair/meetingPathBlocker");
    const roster = RECORDED.cold.gets["/api/inference/assignments"];
    const summary = roster.task_overrides.find((t: { id: string }) => t.id === SUMMARY_CAPABILITY);
    expect(summary?.effective.status).toBe("no_assignment");
    expect(summary?.queue?.status).toBe("no_assignment");
    expect(meetingPathBlockers(roster as never)).toEqual([
      { key: "summary", label: "No engine for summaries", verb: "Choose an engine" },
    ]);
    // The hub's own answer on the same HOME says the same.
    // (The hub's rows also name their direction, Betterment D0.)
    const hubRows = RECORDED.cold.gets["/api/desk/needs-you?fresh=1"].blockers as Array<Record<string, string>>;
    expect(hubRows.map(({ key, label, verb }) => ({ key, label, verb }))).toEqual(meetingPathBlockers(roster as never));
  });
});

// ── PHILO-15 01: a Default for AI work clears "No engine for summaries" ──
// The hub's own answers (scripts/record_needs_you_fixture.py `lanDefault` and
// `summariesOff`, the browser test's seeds: the LAN model as the GLOBAL
// default; for OFF, an imported meeting and summaries turned off). One hub
// boot each: the reads before Generate, Generate, the reads after. The hub
// half is tests/unit/test_desk_brief.py.
const FALSE_ROW = "No engine for summaries";

type Step = { name: string; gets: Record<string, unknown>; post?: string; answer?: unknown };

function replay(steps: Step[], posted: string[]) {
  let at = 0;
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string }) => {
    const value = String(path);
    if (init?.method === "POST") {
      posted.push(value);
      const next = steps.findIndex((step, i) => i > at && step.post === value);
      if (next < 0) throw new Error(`unrecorded POST ${value}`);
      at = next;
      return structuredClone(steps[next].answer) as never;
    }
    return recordedGet(steps[at].gets, value) as never;
  });
}

describe("Chair app: a Default for AI work asks nothing about summaries", () => {
  // Betterment daily D5: the Brief window's half (Generate draws the brief
  // with no false row) is parked in __tests__/_parked/needsChairBrief.d5.app.test.tsx.
  it.each([
    ["the LAN model is the global default", "lanDefault"],
    ["summaries are off over an imported meeting", "summariesOff"],
  ] as const)("%s: Needs you draws no SETUP row", async (_name, key) => {
    // replaces: tests/e2e/test_philo15_01_default_clears_summaries_glass.py::TestDefaultClearsSummaries::test_needs_you_and_brief_draw_no_false_row (the face half)
    // replaces: tests/e2e/test_philo15_01_default_clears_summaries_glass.py::TestSummariesOff::test_off_reads_off_and_asks_nothing (the face half; the Meetings headline is meetingsHeadlineDefault.philo1501.test.ts)
    const steps = (RECORDED as unknown as Record<string, { steps: Step[] }>)[key].steps;
    const posted: string[] = [];
    replay(steps, posted);
    vi.resetModules();
    const { openChairWindows } = await import("../chair/__tests__/fixtures/openChairWindows");
    openChairWindows();
    const { ChairHome } = await import("../chair/ChairHome");
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"), { timeout: 3000 });
    const needs = region("Needs you")!;
    expect(needs.querySelectorAll('[data-object-id^="blocker:"]')).toHaveLength(0);
    expect(needs.textContent).not.toContain(FALSE_ROW);
    expect(needs.textContent).not.toContain("Summary failed");
    expect(posted).toEqual([]);
  });
});

// ── HS-201-01: the SETUP row's verb opens Runs on at its job ──────────────
describe("Chair app: the SETUP verb on the cold row", () => {
  it("Choose an engine on the recorded cold row opens Engines scoped to the row's key", async () => {
    // replaces: tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_chair_names_the_blocker (the Button opens Runs on)
    const blockers = RECORDED.cold.gets["/api/desk/needs-you?fresh=1"].blockers as Array<{ key: string; verb: string }>;
    expect(blockers.map((b) => b.key)).toEqual(["summary"]);
    vi.resetModules();
    const { openChairWindows } = await import("../chair/__tests__/fixtures/openChairWindows");
    openChairWindows();
    const { ChairHome } = await import("../chair/ChairHome");
    const { SurfaceWindows } = await import("../components/SurfaceWindows");
    const { useDesk } = await import("../store");
    useDesk.setState({ windowsById: {} } as never);
    render(<><SurfaceWindows /><ChairHome /></>);
    const row = await waitFor(() => {
      const found = region("Needs you")!.querySelector<HTMLElement>('[data-testid="needs-row"][data-object-id="blocker:summary"]');
      expect(found).toBeTruthy();
      return found!;
    }, { timeout: 3000 });
    const verbs = within(row).getAllByRole("button");
    expect(verbs).toHaveLength(1);
    expect(verbs[0].getAttribute("data-verb")).toBe("setup");
    expect(verbs[0].textContent).toBe(blockers[0].verb);
    fireEvent.click(verbs[0]);
    // ST7: Engines receives the job scope directly in its own window.
    await waitFor(() => expect(useDesk.getState().windowsById["surface-engines"]?.scope).toBe("summary"));
  });
});
