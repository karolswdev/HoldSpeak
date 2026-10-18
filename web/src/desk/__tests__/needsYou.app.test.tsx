// Needs you (the Chair's arrival app): the faces' half of the Needs-you browser
// tests (the test diet, 2026-10-11). The hub's half is
// tests/unit/test_desk_needs_you.py. Each test renders the real component with
// its real store; only `apiFetch` is mocked, with the hub's own answer shape
// (the producer's cards, the oracle week minted by the real producers).
// Every test names the browser test it replaces (`replaces:`).
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { asHub } from "../../test/hubNeedsYou";
import { ChairHome } from "../chair/ChairHome";
import { openChairWindows } from "../chair/__tests__/fixtures/openChairWindows";
import { openIntelligence } from "../intelligenceNavigation";
import { __resetSurfaces } from "../shell";
import { SurfaceWindows } from "../components/SurfaceWindows";
import { recordedGet } from "../../test/recordedHub";
import RECORDED from "./fixtures/needsYou.recorded.json";
import { useDesk } from "../store";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const ROSTER = { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  __resetSurfaces();
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  openChairWindows();
});

const needsRows = () => [...document.querySelectorAll<HTMLElement>('[data-testid="needs-drawer"] [data-testid="needs-row"]')];
const rowNamed = (text: string) => needsRows().find((r) => r.querySelector(".needs-row-name")?.textContent === text);
const lampOf = (r: HTMLElement) => r.querySelector(".gadget-lamp")?.textContent ?? "";
const head = () => screen.getByTestId("arrival-display").textContent ?? "";

/** The REAL producer's Door/Follow-through card (`DoorService._follow_through_card`,
 *  the same card shape arrivalAttention.test.tsx draws). */
const producerCard = (id: string, text: string, owner: string | null) => ({
  id, text, owner, due: null, status: "pending", meeting_id: "m-owner-verb", decision_id: null,
  stale_score: null, source: "action_item", lane: "unassigned", provenance: null,
  delegated_at: null, created_at: "2026-10-03T09:00:00",
  target_ref: `action_item:${id}`,
  lawful_verbs: [
    { name: "done", arguments: { card_id: id, verb: "done" }, required_arguments: [] },
    { name: "delegate", arguments: { card_id: id, verb: "delegate" }, required_arguments: ["to"] },
  ],
});

describe("Needs you: Name an owner and Review on a meeting's action items", () => {
  const OWNED = "Draft the migration runbook";
  const UNOWNED = "Book the dry run";

  it("the owner well saves; the row stays, reads TO REVIEW and drops Name an owner", async () => {
    // replaces: tests/e2e/test_chair_owner_verb_glass.py::test_owner_verb_only_where_no_owner_exists
    let avery: string | null = null;
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value === "/api/inference/assignments") return ROSTER;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, projects: [], items: [], next: null, coverage: [], complete: true };
      if (value === "/api/follow-through/complete") {
        const body = (init as { json?: { card_id?: string; verb?: string; payload?: { to?: string } } }).json;
        if (body?.card_id === "ai-unowned" && body.verb === "delegate") avery = body.payload?.to ?? null;
        return { card_id: body?.card_id, verb: body?.verb };
      }
      if (value.startsWith("/api/door")) {
        // Not reviewed yet: the item stays in `unassigned`, now with its owner
        // (tests/unit/test_desk_needs_you.py proves the hub does this).
        return { board: { unassigned: [producerCard("ai-owned", OWNED, "Priya"), producerCard("ai-unowned", UNOWNED, avery)] },
          counts: {}, upcoming: [], calendar_configured: false };
      }
      return null;
    }));
    render(<ChairHome />);
    await waitFor(() => expect(rowNamed(UNOWNED)).toBeTruthy());
    const owned = rowNamed(OWNED)!;
    expect(lampOf(owned)).toBe("TO REVIEW");
    expect(owned.querySelector('[data-verb="name-owner"]')).toBeNull();
    expect(lampOf(rowNamed(UNOWNED)!)).toBe("UNASSIGNED");

    fireEvent.click(rowNamed(UNOWNED)!.querySelector('[data-verb="name-owner"]') as HTMLElement);
    const well = await screen.findByTestId("needs-well");
    fireEvent.change(within(well).getByRole("textbox", { name: "Owner" }), { target: { value: "Avery" } });
    fireEvent.click(within(well).getByRole("button", { name: /Save owner/ }));
    await waitFor(() => expect(screen.queryByTestId("needs-well")).toBeNull());

    // The hub's board is the truth the row settles on.
    await waitFor(() => expect(lampOf(rowNamed(UNOWNED)!)).toBe("TO REVIEW"));
    expect(needsRows().filter((r) => r.querySelector(".needs-row-name")?.textContent === UNOWNED)).toHaveLength(1);
    expect(document.querySelector('[data-testid="needs-drawer"] [data-verb="name-owner"]')).toBeNull();
    expect(rowNamed(UNOWNED)!.textContent).not.toContain("UNASSIGNED");
  });

  it("Review's destination: the Needs-you window (Betterment D4: Follow-through is parked)", async () => {
    // The Follow-through wing is parked (Today is one page); a follow-through
    // drill opens the Needs-you window, where the card's row and verbs are.
    // The wing's case is parked in _parked/needsYouFollowThroughWing.app.test.tsx.
    const { isChairWindowOpen, useChairWindows } = await import("../chair/chairWindows");
    useChairWindows.setState((s) => ({ closed: { ...s.closed, "chair:needs": true } }));
    const openPullout = vi.fn();
    const realOpen = useDesk.getState().openPullout;
    useDesk.setState({ openPullout } as never);
    try {
      act(() => openIntelligence({ view: "follow-through", followThroughId: "ai-owned" }));
      await waitFor(() => expect(isChairWindowOpen("chair:needs")).toBe(true));
      expect(openPullout).not.toHaveBeenCalled();
    } finally {
      useDesk.setState({ openPullout: realOpen } as never);
    }
  });

});

// ── The oracle week, minted by the real producers ─────────────────────────
// scripts/philo13_needs_you_fixture.py (as chair/__tests__/oneNeedsYou.philo1303.test.tsx):
// six members; A3 names another owner (Priya) and waits; one Desk decision
// waits for review.
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../..");
type Wire = Record<string, any>;
let home = "";
let week: Wire;

describe("Needs you: the head counts what needs him; Waiting lists the rest", () => {
  beforeAll(() => {
    home = mkdtempSync(join(tmpdir(), "needs-you-app-"));
    const db = join(home, ".local", "share", "holdspeak", "holdspeak.db");
    const run = (mode: string) => JSON.parse(execFileSync(resolve(REPO_ROOT, ".venv/bin/python"),
      [resolve(REPO_ROOT, "scripts/philo13_needs_you_fixture.py"), mode, "--db", db, "--home", home],
      { cwd: REPO_ROOT, env: { ...process.env, HOME: home }, encoding: "utf8", maxBuffer: 32 * 1024 * 1024 }));
    run("seed");
    week = run("export");
  }, 60_000);
  afterAll(() => { if (home) rmSync(home, { recursive: true, force: true }); });

  function installWeek() {
    const wire = week.before as Wire;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value === "/api/door") return wire.door as never;
      if (value.startsWith("/api/desk/needs-you")) return wire.needsYou as never;
      if (value === "/api/inference/assignments") return wire.assignments as never;
      if (value === "/api/settings/heartbeat") return wire.heartbeat as never;
      if (value.startsWith("/api/meetings?summary_attention=true")) {
        const rows = (wire.meetingsWire.meetings as Wire[]).filter((row) => row.id === "philo13-a2-failed-meeting");
        return { meetings: rows, total: rows.length } as never;
      }
      // GET /api/decisions/{id}: a Desk decision (PrimitiveService.decision.read;
      // a Desk decision has no source meeting).
      if (value === "/api/decisions/philo13-a2-decision")
        return { decision: { id: "philo13-a2-decision", title: "R1 adopt the release checklist", status: "proposed" } } as never;
      return null as never;
    });
  }

  it("6 with A3 not among the rows; Waiting lists A3 waiting on Priya; Review opens the decision", async () => {
    // replaces: tests/e2e/test_needs_you_means_you_glass.py::TestNeedsYouMeansYou::test_the_head_counts_what_needs_him_and_waiting_lists_the_rest
    // (the A4-named -> 5 and decision-accepted -> 4 legs are the hub's: tests/unit/test_desk_needs_you.py)
    installWeek();
    useDesk.setState({ items: { ...useDesk.getState().items, meeting: [] } } as never);
    render(<ChairHome />);
    await waitFor(() => expect(head()).toMatch(/^6 need you/), { timeout: 3000 });
    // Betterment D2: one list. The six counted rows, then A3 (Priya owes it):
    // listed, not counted.
    const counted = needsRows().filter((r) => r.getAttribute("data-counted") === "true").map((r) => r.textContent ?? "");
    expect(counted).toHaveLength(6);
    expect(counted.some((t) => t.includes("A3 wait for Priya's review") || t.includes("WAITING ON"))).toBe(false);

    fireEvent.click(within(screen.getByTestId("needs-filter")).getByTestId("needs-chip-theirs"));
    await waitFor(() => expect(needsRows().every((r) => r.getAttribute("data-direction") === "theirs")).toBe(true));
    const waitingRows = needsRows().map((r) => r.textContent ?? "");
    expect(waitingRows.some((t) => t.includes("A3 wait for Priya's review") && t.includes("WAITING ON PRIYA"))).toBe(true);
    expect(waitingRows.some((t) => t.includes("A4 assign the owner"))).toBe(false);
    expect(head()).toMatch(/^6 need you/);

    fireEvent.click(within(screen.getByTestId("needs-filter")).getByTestId("needs-chip-theirs"));
    await waitFor(() => expect(rowNamed("R1 adopt the release checklist")).toBeTruthy());
    const decision = rowNamed("R1 adopt the release checklist")!;
    fireEvent.click(within(decision).getByRole("button", { name: "Decide: R1 adopt the release checklist" }));
    // The real opener (shell.ts openPrimitive) runs against the real desk store:
    // the decision's own window opens, in front.
    await waitFor(() =>
      expect(useDesk.getState().pullouts.map((p) => p.id)).toContain("decision:philo13-a2-decision"),
      { timeout: 3000 });
  });
});

// ── Arrival: proposal rows (HS-172) ───────────────────────────────────────
// The row fields are the hub's (`needs_you_aggregate._proposal_fields`), the
// values the browser test's seed gives (tests/unit/test_desk_needs_you.py
// reads the same seed through the real route).
describe("Needs you: proposal rows on arrival", () => {
  // The hub's own answers on the browser test's seed (a Room's ran Standup with
  // an action and a decision proposal), from ONE hub boot: the read before
  // Confirm, Confirm on the action, the read after
  // (scripts/record_needs_you_fixture.py `arrival`).
  it("each proposal names its meeting and act, has one Confirm; Confirm turns exactly that row into a commitment", async () => {
    // replaces: tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_proposals
    // replaces: tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_confirm_fires (the face half)
    const { action, steps } = RECORDED.arrival;
    const decision = "cut-over on the 12th";
    let at = 0;
    const posted: string[] = [];
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
    render(<ChairHome />);
    await waitFor(() => expect(head()).toMatch(/^4 need you/), { timeout: 3000 });
    const proposalRows = () => needsRows().filter((r) => r.getAttribute("data-object-id")?.startsWith("proposal:"));
    expect(proposalRows()).toHaveLength(2);
    for (const r of proposalRows()) {
      expect(r.querySelector(".needs-row-fact")?.textContent).toMatch(/^from Standup/);
      // Betterment D2: an action asks for Confirm; a decision for Decide.
      expect(r.querySelectorAll('[data-verb="confirm"], [data-verb="decide"]')).toHaveLength(1);
      expect(r.getAttribute("data-opens")).toBe("true");
    }
    expect(rowNamed(decision)!.querySelectorAll('[data-verb="decide"]')).toHaveLength(1);
    expect(proposalRows().map(lampOf).sort()).toEqual(["TO CONFIRM", "TO DECIDE"]);
    const face = document.querySelector('[data-testid="needs-drawer"]')?.textContent ?? "";
    expect(face).not.toContain("LOCAL");
    expect(face).not.toContain("0 NEEDS");

    fireEvent.click(screen.getByRole("button", { name: `Confirm: ${action}` }));
    expect(posted).toEqual([steps[1].post]);
    // The hub files the action as a commitment: the proposal row leaves, a
    // commitment row with the same words takes its place, with no Confirm.
    await waitFor(() => expect(proposalRows().map((r) => r.querySelector(".needs-row-name")?.textContent)).toEqual([decision]));
    const filed = rowNamed(action);
    expect(filed, "the confirmed action is drawn as the hub's commitment row").toBeTruthy();
    expect(filed!.getAttribute("data-object-id")).not.toMatch(/^proposal:/);
    expect(filed!.querySelectorAll('[data-verb="confirm"]')).toHaveLength(0);
    // The hub still counts 4: the obligation is still his, now filed.
    expect(head()).toMatch(/^4 need you/);
  });
});

// ── PHILO-15 08: Confirm and Defer on an unfiled meeting's rows ───────────
// The hub's own answers before and after each press, from ONE hub boot
// (scripts/record_needs_you_fixture.py `unfiled`: confirm the action, then
// defer the decision). The face re-reads after each press; the test serves
// what the hub answered at that moment.
describe("Needs you: Confirm and Defer on a meeting in no Project", () => {
  it("Confirm turns the action into a waiting row; Defer takes the decision off the face", async () => {
    // replaces: tests/e2e/test_philo15_08_confirm_unfiled_glass.py::TestConfirmFromAnUnfiledMeeting::test_confirm_an_action_item_from_its_needs_row (the face half)
    // replaces: tests/e2e/test_philo15_08_confirm_unfiled_glass.py::TestConfirmFromAnUnfiledMeeting::test_defer_holds_back_the_whole_obligation (the face half)
    const { action, decision, steps } = RECORDED.unfiled;
    let at = 0;
    const posted: string[] = [];
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
    render(<ChairHome />);
    await waitFor(() => expect(rowNamed(action)).toBeTruthy(), { timeout: 3000 });
    const counted = () => needsRows().map((r) => r.querySelector(".needs-row-name")?.textContent);
    expect(lampOf(rowNamed(action)!)).toBe("TO CONFIRM");
    expect(counted()).toContain(decision);

    // Confirm: the hub accepts the action; it now waits on its owner, Priya
    // Shah: listed (They owe me), not counted, with Nudge (Betterment D2).
    fireEvent.click(screen.getByRole("button", { name: `Confirm: ${action}` }));
    await waitFor(() => expect(rowNamed(action)?.getAttribute("data-counted")).toBe("false"));
    expect(posted).toEqual([steps[1].post]);
    const held = rowNamed(action)!;
    expect(held.textContent).toMatch(/WAITING ON PRIYA/i);
    expect(held.querySelector('[data-verb="nudge"]')).toBeTruthy();

    // Decide ▸ Not now: the decision leaves the face.
    await waitFor(() => expect(rowNamed(decision)).toBeTruthy());
    fireEvent.click(within(rowNamed(decision)!).getByRole("button", { name: `Decide: ${decision}` }));
    fireEvent.click(await screen.findByRole("button", { name: `Not now: ${decision}` }));
    await waitFor(() => expect(rowNamed(decision)).toBeUndefined());
    expect(posted).toEqual([steps[1].post, steps[2].post]);
  });
});

// ── PHILO-17: Reconnect lands on Settings, GitHub focused ─────────────────
describe("Needs you: Reconnect opens Settings on the GitHub row", () => {
  it("the real opener opens the Settings window scoped to GitHub, and focus is in the GitHub row", async () => {
    // replaces: tests/e2e/test_philo17_needs_you_grouped_glass.py::test_one_row_per_cause_and_repair_on_the_real_hub (the Reconnect leg)
    // The hub's answers on the browser test's seed (30 signed-out GitHub sources),
    // and the Settings window's own reads, recorded (`grouped`). Nothing mocks the
    // opener: NeedsDrawer's Reconnect -> shell.ts openSurfaceOr -> the surface
    // SurfaceWindows registered -> SettingsCore (scope integration:github, its
    // focusProvider at SettingsCore.tsx:2388) -> ConnectionsPane's focus.
    const misses: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      recordedGet(RECORDED.grouped.gets, path, misses) as never);
    useDesk.setState({ windowsById: {} } as never);
    render(<><SurfaceWindows /><ChairHome /></>);
    const reconnect = await screen.findByRole("button", { name: /^Reconnect: GitHub · 30 sources$/ }, { timeout: 3000 });
    fireEvent.click(reconnect);
    await waitFor(() => expect(useDesk.getState().windowsById["surface-settings"]?.scope).toBe("integration:github"));
    const row = await screen.findByTestId("connections-github", undefined, { timeout: 5000 });
    await waitFor(() => expect(row.contains(document.activeElement)).toBe(true), { timeout: 3000 });
  });
});

// ── HS-145: no calendar offers Connect; a quiet calendar asks nothing ─────
// The hub's own answers on the browser test's seed (the meeting path pinned;
// then one calendar source whose only event is two hours ago, applied by the
// real ingest conductor), recorded by scripts/record_needs_you_fixture.py
// (`calendar`). The hub half is tests/unit/test_desk_calendar.py.
describe("Needs you: the calendar offer and the quiet calendar", () => {
  it("no calendar: the foot offers NO CALENDAR · Connect calendar; the press opens Settings on Meetings, at its Connect row", async () => {
    // replaces: tests/e2e/test_hs145_door_polish_glass.py::test_hs145_connect_calendar_affordance_and_quiet_state (the no-calendar leg)
    const misses: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      recordedGet(RECORDED.calendar.none.gets, path, misses) as never);
    useDesk.setState({ windowsById: {} } as never);
    render(<><SurfaceWindows /><ChairHome /></>);
    const offer = await screen.findByTestId("needs-no-calendar", undefined, { timeout: 3000 });
    expect(offer.textContent).toContain("NO CALENDAR");
    expect(head()).toBe("Nothing needs you");
    fireEvent.click(within(offer).getByRole("button", { name: "Connect calendar" }));
    await waitFor(() => expect(useDesk.getState().windowsById["surface-settings"]?.scope).toBe("meetings"));
    await screen.findByTestId("calendar-connect-row", undefined, { timeout: 5000 });
  });

  it("a configured calendar with only a past event: Nothing needs you, no offer, no NEXT line", async () => {
    // replaces: tests/e2e/test_hs145_door_polish_glass.py::test_hs145_connect_calendar_affordance_and_quiet_state (the quiet leg)
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      recordedGet(RECORDED.calendar.quiet.gets, path) as never);
    expect(RECORDED.calendar.quiet.gets["/api/door"].calendar_configured).toBe(true);
    render(<ChairHome />);
    await waitFor(() => expect(head()).toBe("Nothing needs you"), { timeout: 3000 });
    // The drawer read the configured Door (the no-calendar test proves the
    // same read draws the offer when the Door says false).
    await waitFor(() => expect(vi.mocked(apiFetch).mock.calls.some(([p]) => String(p) === "/api/door")).toBe(true));
    await act(async () => { await new Promise((r) => setTimeout(r, 50)); });
    expect(screen.queryByTestId("needs-no-calendar")).toBeNull();
    expect(document.querySelector('[data-verb="connect-calendar"]')).toBeNull();
    expect(screen.queryByTestId("needs-next")).toBeNull();
  });
});

// ── PHILO-17 (evalerror): a failed Evaluate reaches Needs you ─────────────
// The hub's own answers after the owner's Evaluate (route) and an agent's
// (MCP) on two live GitHub Watches with gh signed out, its stderr carrying
// synthetic credentials (scripts/record_needs_you_fixture.py `evalError`).
// The hub half is tests/unit/test_desk_needs_you.py::test_a_failed_evaluate_is_stored_and_reaches_needs_you_without_a_secret.
describe("Needs you: a failed Evaluate is one grouped GitHub row", () => {
  it("GitHub · 2 sources reads Not signed in with one Reconnect; Details lists both; no secret, no gh auth login", async () => {
    // replaces: tests/e2e/test_philo17_evaluate_error_glass.py::test_a_failed_evaluate_reaches_needs_you_as_its_grouped_row (the face half)
    const { secrets, steps } = RECORDED.evalError;
    const before = steps[0].gets["/api/desk/needs-you?fresh=1"];
    expect(before.coverage.filter((c: { state: string }) => c.state === "failed")).toEqual([]);
    vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(steps[1].gets, path) as never);
    render(<ChairHome />);
    const reconnect = await screen.findByRole("button", { name: "Reconnect: GitHub · 2 sources" }, { timeout: 3000 });
    const sources = [...document.querySelectorAll<HTMLElement>('[data-testid="needs-source-row"]')];
    expect(sources.map((r) => r.querySelector(".needs-row-name")?.textContent?.trim())).toEqual(["GitHub · 2 sources"]);
    const group = sources[0];
    expect(group.contains(reconnect)).toBe(true);
    expect(group.querySelector(".needs-row-fact")?.textContent?.trim()).toBe("Not signed in");
    expect(within(group).getAllByRole("button", { name: "Reconnect: GitHub · 2 sources" })).toHaveLength(1);
    expect(screen.getByTestId("needs-list").textContent).not.toContain("gh auth login");

    fireEvent.click(within(group).getByRole("button", { name: "Details: GitHub · 2 sources" }));
    const detail = await screen.findByTestId("needs-detail");
    expect(detail.querySelectorAll("li")).toHaveLength(2);
    const shown = screen.getByTestId("needs-drawer").textContent ?? "";
    expect(secrets.filter((x: string) => shown.includes(x))).toEqual([]);
  });
});

// ── HS-144: a failed Door read never throws and never draws a row ─────────
// The recorded quiet desk (scripts/record_needs_you_fixture.py `calendar`),
// with the one Door read refused by the hub (a 500, as DoorService.get raising
// answers it).
describe("Needs you: the Door read fails", () => {
  it("the Door answers 500: the head still reads Nothing needs you; the drawer draws, with no row", async () => {
    // replaces: tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots (the Door 500 leg)
    const errors: unknown[] = [];
    const onError: EventListener = (event) => { errors.push(event); };
    window.addEventListener("unhandledrejection", onError as EventListener);
    window.addEventListener("error", onError as EventListener);
    try {
      vi.mocked(apiFetch).mockImplementation(async (path: string) => {
        if (String(path) === "/api/door") throw new ApiError(500, "controlled Door refusal", { error: "controlled Door refusal" });
        return recordedGet(RECORDED.calendar.quiet.gets, path) as never;
      });
      render(<ChairHome />);
      await waitFor(() => expect(vi.mocked(apiFetch).mock.calls.some(([p]) => String(p) === "/api/door")).toBe(true));
      await waitFor(() => expect(head()).toBe("Nothing needs you"), { timeout: 3000 });
      await screen.findByTestId("needs-drawer", undefined, { timeout: 3000 });
      await act(async () => { await new Promise((r) => setTimeout(r, 50)); });
      expect(needsRows()).toEqual([]);
      expect(head()).toBe("Nothing needs you");
      expect(errors).toEqual([]);
    } finally {
      window.removeEventListener("unhandledrejection", onError as EventListener);
      window.removeEventListener("error", onError as EventListener);
    }
  });
});
