// The Agents app (the roster and the agent's lane) on the hub's OWN answers
// (the test diet, 2026-10-11). Every apiFetch answer here is a file under
// ./wire, captured on a real hub seeded by the browser test's own seed and
// fenced against the hub's shape on every run by
// tests/integration/test_desk_agents_wire.py. Only apiFetch / apiRequest are
// doubles; the components, stores and reducers are the real ones.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { hubWire } from "./wire/hubWire";

const api = vi.hoisted(() => ({ fetch: vi.fn(), request: vi.fn() }));
vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiFetch: api.fetch,
  apiRequest: api.request,
}));
vi.mock("../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});
vi.mock("../components/MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

import { CompanionCore } from "../../pages/cores/CompanionCore";
import { WingSlotContext } from "../surface/wings";
import { LaneWindow, __resetDraftEgress } from "../lane/LaneWindow";
import { __resetLane, useLane } from "../lane/laneStore";
import { fromWireFlight, useAgentFlights } from "../agentFlights";
import { useSteering } from "../steering";

const QUESTION = "The runbook needs a rollback owner. Jordan or Avery?";
const LONG_CMD = (() => {
  const base = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = ";
  return base + "7".repeat(198 - base.length - 1) + "'";
})();

type Routes = Record<string, unknown>;

/** apiFetch answers by path prefix (longest first), each a captured hub answer. */
function serve(routes: Routes) {
  const keys = Object.keys(routes).sort((a, b) => b.length - a.length);
  api.fetch.mockImplementation(async (url: string) => {
    const hit = keys.find((key) => String(url).startsWith(key));
    if (hit === undefined) throw new Error(`no captured hub answer for ${url}`);
    return routes[hit];
  });
}

beforeEach(() => {
  api.fetch.mockReset();
  api.request.mockReset();
  api.request.mockImplementation(async () => ({ ok: true, status: 200, json: async () => ({}) }) as unknown as Response);
  localStorage.clear();
  __resetLane();
  __resetDraftEgress();
  useAgentFlights.setState({ flights: [], sessions: [], loaded: true });
});
afterEach(() => {
  __resetLane();
  vi.useRealTimers();
});

describe("the roster (Agents) on the product seed", () => {
  /** replaces: tests/e2e/test_agents_roster_glass.py::test_roster_lists_the_floor_agents_and_no_blank_delivery_tab */
  it("lists every seeded agent the hub serves and withholds an empty Delivery wing", async () => {
    const recipes = hubWire<{ recipes: Array<{ name: string; deleted?: boolean }> }>("recipes.seed");
    serve({
      "/api/recipes": recipes.wire,
      "/api/coders/sessions": hubWire("coders-sessions.empty").wire,
      "/api/delivery/prs": hubWire("delivery-prs.empty").wire,
    });
    function Host({ children }: { children: ReactNode }) {
      const [slot, setSlot] = useState<ReactNode>(null);
      return (
        <WingSlotContext.Provider value={setSlot}>
          <div data-testid="window-head">{slot}</div>
          {children}
        </WingSlotContext.Provider>
      );
    }
    const { container } = render(<Host><CompanionCore /></Host>);
    const floor = [...new Set(recipes.wire.recipes.filter((r) => !r.deleted).map((r) => String(r.name)))].sort();
    expect(floor).toEqual(expect.arrayContaining(["Chase", "Desk", "Draft"]));
    await screen.findByText("Chase");
    const crew = [...container.querySelectorAll(".surface-ledger-rows")].at(-1)!;
    const shown = [...new Set([...crew.querySelectorAll(".surface-primary, .surface-ledger-primary")]
      .map((el) => (el.textContent ?? "").trim()).filter(Boolean))].sort();
    expect(shown).toEqual(floor);
    // No repository work and no pull request receipts: the wing is withheld.
    expect(screen.queryByRole("tab", { name: "Delivery" })).toBeNull();
    expect(screen.getAllByRole("tab", { name: "Roster" })).toHaveLength(1);
  });
});

/* ── the lane (PHILO-14 C2 seed) ─────────────────────────────────────── */

const LANE = hubWire("lane.c2");
const LANE_CUT = hubWire("lane.c2-cut");
const FLIGHTS_C2 = hubWire<{ flights: Array<Record<string, unknown>> }>("coders-sessions.c2");
const ASSIGNMENTS = hubWire("inference-assignments.empty");

function steering() {
  act(() => {
    useSteering.setState({
      openKey: null, session: null, paneStatus: "no_pane", armed: false, postureAuthorized: false,
      steerState: "idle", steerDetail: "", answerSeq: 0, answerOpen: false,
      openSession: vi.fn(), closeSession: vi.fn(),
    } as never);
  });
}

async function openLane(lane: unknown, extra: Routes = {}) {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(LANE.captured_at));
  serve({
    "/api/agent/launches/": lane,
    "/api/inference/assignments": ASSIGNMENTS.wire,
    "/api/gate/proposals": { proposals: [] },
    ...extra,
  });
  steering();
  useAgentFlights.setState({ flights: FLIGHTS_C2.wire.flights.map((f) => fromWireFlight(f as never)), sessions: [], loaded: true });
  const key = (lane as { launch: { session_key: string } }).launch.session_key;
  render(<LaneWindow />);
  await act(async () => {
    await useLane.getState().open("launch_c2_runbook", { sessionKey: key });
  });
  await screen.findByTestId("lane-track");
}

describe("the agent's lane on the hub's lane answer", () => {
  /** replaces: tests/e2e/test_philo14_c2_lane_glass.py::test_the_agents_lane_window_at_1440_and_393 */
  it("reads the launch: title, station track, the ask and its draft, the rail, the PR, the files", async () => {
    await openLane(LANE.wire);
    expect(screen.getAllByText("Claude Code: Write the rollback runbook").length).toBeGreaterThan(0);
    const track = screen.getByTestId("lane-track").textContent ?? "";
    for (const word of ["BRIEF", "WORK", "COMMIT", "PR", "HELD", "ASKS", "MERGE"]) expect(track).toContain(word);
    expect(track).toContain("#413");
    expect(track).toContain("1 HELD · 1 WAITING");
    expect(track).toContain("now");
    expect(screen.getByTestId("lane-ask").querySelector(".ask-well-question")?.textContent).toBe(QUESTION);
    expect(screen.getByTestId("lane-ask").querySelector(".ask-well-draft")?.textContent).toContain("Jordan owns it. Avery reviews.");
    const rail = screen.getByTestId("lane-rail").textContent ?? "";
    for (const word of ["BRIEF", "READ", "SAYS", "WRITE", "RUN", "COMMIT", "PR", "HELD", "ASKS", "MERGE"]) expect(rail).toContain(word);
    expect(rail).toContain("Draft the ledger rollback runbook");
    expect(rail).toContain("psql -h staging-ledger");
    expect(rail).toContain("Your press in GitHub");
    const pr = screen.getByTestId("lane-pr").textContent ?? "";
    expect(pr).toContain("#413");
    expect(pr).toContain("CHECKS 6 OF 7");
    expect(pr).toContain("1 RUNNING");
    const files = screen.getByTestId("lane-files").textContent ?? "";
    expect(files).toContain("docs/ledger-rollback.md");
    expect(files).toContain("freeze.py");
    expect(screen.getAllByText("GITHUB.COM").length).toBeGreaterThan(0);
    expect(screen.getByTestId("lane-open-pr")).toBeTruthy();
    expect(screen.getByTestId("lane-stop")).toBeTruthy();
  });

  /** replaces: tests/e2e/test_philo14_c2_lane_glass.py::test_the_agents_lane_window_at_1440_and_393 (Raw) */
  it("Raw puts the terminal pane in place of the lane, and back", async () => {
    await openLane(LANE.wire);
    fireEvent.click(screen.getByTestId("lane-raw"));
    expect(screen.getByTestId("lane-raw-pane")).toBeTruthy();
    expect(screen.queryByTestId("lane-rail")).toBeNull();
    fireEvent.click(screen.getByTestId("lane-raw"));
    expect(screen.getByTestId("lane-rail")).toBeTruthy();
  });

  /** replaces: tests/e2e/test_philo14_c2_lane_glass.py::test_the_agents_lane_window_at_1440_and_393 (approve from the rail) */
  it("Approve on the rail's held call decides it through the gate route; the next read has no Approve", async () => {
    await openLane(LANE.wire, { "/api/gate/proposals/toolu_psql/decide": { state: "approved" } });
    const held = [...screen.getByTestId("lane-rail").querySelectorAll<HTMLElement>(".lane-rail-entry")]
      .find((el) => (el.textContent ?? "").includes("psql -h staging-ledger"))!;
    fireEvent.click(within(held).getByTestId("lane-approve"));
    await waitFor(() =>
      expect(api.fetch).toHaveBeenCalledWith("/api/gate/proposals/toolu_psql/decide", expect.objectContaining({
        method: "POST", json: expect.objectContaining({ decision: "approved" }),
      })),
    );
    // The hub's next lane answer (the call approved, a cut one held).
    serve({ "/api/agent/launches/": LANE_CUT.wire, "/api/inference/assignments": ASSIGNMENTS.wire, "/api/gate/proposals": { proposals: [] } });
    await act(async () => {
      await useLane.getState().load();
    });
    const after = [...screen.getByTestId("lane-rail").querySelectorAll<HTMLElement>(".lane-rail-entry")]
      .filter((el) => (el.textContent ?? "").includes("psql -h staging-ledger -c"));
    expect(after.length).toBeGreaterThan(0);
    for (const entry of after) expect(within(entry).queryByTestId("lane-approve")).toBeNull();
  });

  /** replaces: tests/e2e/test_philo14_c2_lane_glass.py::test_the_agents_lane_window_at_1440_and_393 (the 198-char cut call) */
  it("a call the hook cut reads `… +90 CHARS` with Deny and Raw, never Approve", async () => {
    await openLane(LANE_CUT.wire);
    const cut = [...screen.getByTestId("lane-rail").querySelectorAll<HTMLElement>(".lane-rail-entry")]
      .find((el) => (el.textContent ?? "").includes("+90 CHARS"))!;
    expect(cut).toBeTruthy();
    expect(cut.textContent).toContain(LONG_CMD.slice(0, 100));
    expect(cut.textContent).toContain("… +90 CHARS");
    expect(within(cut).queryByTestId("lane-approve")).toBeNull();
    expect(within(cut).getByTestId("lane-deny")).toBeTruthy();
    expect(within(cut).getByTestId("lane-raw-cut")).toBeTruthy();
  });
});

describe("Raw reads a cut call whole (PHILO-15 20)", () => {
  /** replaces: tests/e2e/test_philo15_20_raw_approve_glass.py::test_raw_shows_a_cut_call_whole_and_approves_it_at_1440_and_393 */
  it("Raw shows the hub's whole command with Deny and Approve; Approve decides it and leaves a receipt", async () => {
    const whole = hubWire<{ command: string }>("gate-command.whole").wire;
    await openLane(LANE_CUT.wire, {
      "/api/gate/proposals/toolu_cut/command": whole,
      "/api/gate/proposals/toolu_cut/decide": { state: "approved" },
    });
    const cut = [...screen.getByTestId("lane-rail").querySelectorAll<HTMLElement>(".lane-rail-entry")]
      .find((el) => (el.textContent ?? "").includes("+90 CHARS"))!;
    fireEvent.click(within(cut).getByTestId("lane-raw-cut"));
    const held = await screen.findByTestId("lane-raw-held");
    await waitFor(() => expect(within(held).getByTestId("lane-raw-command").textContent).toBe(whole.command));
    expect(held.querySelector(".lw-caption")?.textContent).toMatch(/^HELD · OUTSIDE THE WORKTREE/);
    expect(within(held).getByTestId("lane-raw-deny")).toBeTruthy();
    fireEvent.click(within(held).getByTestId("lane-raw-approve"));
    await waitFor(() =>
      expect(api.fetch).toHaveBeenCalledWith("/api/gate/proposals/toolu_cut/decide", expect.objectContaining({
        json: expect.objectContaining({ decision: "approved" }),
      })),
    );
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^APPROVED · \d\d:\d\d$/));
    expect(screen.getByTestId("lane-raw-pane")).toBeTruthy();
  });

  /** replaces: tests/e2e/test_philo15_20_raw_approve_glass.py::test_raw_shows_a_cut_call_whole_and_approves_it_at_1440_and_393 (the oversized call) */
  it("an oversized call kept as a part says CUT · n OF m CHARS and offers Deny only", async () => {
    const part = hubWire<{ shown_chars: number; declared_chars: number }>("gate-command.part").wire;
    expect(part.shown_chars).toBeLessThan(part.declared_chars);
    await openLane(LANE_CUT.wire, { "/api/gate/proposals/toolu_cut/command": part });
    act(() => useLane.getState().setRaw(true));
    const held = await screen.findByTestId("lane-raw-held");
    await waitFor(() =>
      expect(held.querySelector(".lw-caption")?.textContent).toContain(`CUT · ${part.shown_chars} OF ${part.declared_chars} CHARS`));
    expect(within(held).queryByTestId("lane-raw-approve")).toBeNull();
    expect(within(held).getByTestId("lane-raw-deny")).toBeTruthy();
  });
});
