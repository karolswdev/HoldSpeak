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
    const list = container.querySelector("[data-testid='agents-list']")!;
    const shown = [...new Set([...list.querySelectorAll(".ag-row-title")]
      .map((el) => (el.textContent ?? "").trim()).filter(Boolean))].sort();
    expect(shown).toEqual(floor);
    // No repository work and no pull request receipts: the wing is withheld,
    // and one wing is no choice (PHILO-17): no wing strip at all.
    await waitFor(() => expect(screen.queryByRole("tab", { name: "Delivery" })).toBeNull());
    expect(screen.queryAllByRole("tab")).toHaveLength(0);
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
  it("Approve on the held plate decides it through the gate route; the next read has no Approve", async () => {
    await openLane(LANE.wire, { "/api/gate/proposals/toolu_psql/decide": { state: "approved" } });
    // PHILO-17 THE REFIT: the held call is on the focus plate at the top of the lane.
    const held = screen.getByTestId("lane-approve-well");
    expect(held.textContent).toContain("psql -h staging-ledger");
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
    expect(screen.queryByTestId("lane-approve")).toBeNull();
  });

  /** replaces: tests/e2e/test_philo14_c2_lane_glass.py::test_the_agents_lane_window_at_1440_and_393 (the 198-char cut call) */
  it("a call the hook cut reads `… +90 CHARS` with Deny and Raw, never Approve", async () => {
    await openLane(LANE_CUT.wire);
    const cut = screen.getByTestId("lane-approve-well");
    expect(cut).toBeTruthy();
    expect(cut.textContent).toContain(LONG_CMD.slice(0, 100));
    expect(cut.textContent).toContain("… +90 CHARS");
    expect(within(cut).queryByTestId("lane-approve")).toBeNull();
    expect(within(cut).getByTestId("lane-deny")).toBeTruthy();
    expect(within(cut).getByTestId("lane-raw-cut")).toBeTruthy();
  });
});

describe("Raw reads a cut call whole (PHILO-15 20)", () => {
  // Astra r1 on #1100: every answer below is ONE hub boot's, each under its
  // own proposal id (tests/integration/test_desk_agents_wire.py::
  // test_raw_reads_a_cut_call_whole_and_approves_it): the lane holding three
  // cut calls, each call's own command read, the decide answer, and the lane
  // and held list the hub serves after the press.
  const HELD = hubWire("lane.raw-held");
  const AFTER = hubWire("lane.raw-approved");
  const WHOLE = hubWire<{ command: string; whole: boolean }>("gate-command.whole");
  const HEAD_ONLY = hubWire<{ command: string; whole: boolean }>("gate-command.head-only");
  const PART = hubWire<{ whole: boolean; shown_chars: number; declared_chars: number }>("gate-command.part");
  const DECIDED = hubWire<{ state: string; decided_at: number }>("gate-decide.approved");
  const HELD_AFTER = hubWire("gate-proposals.raw-approved");

  /** A fake hub with the recorded answers: the decide press flips it to the after reads. */
  async function openRaw() {
    let decided = false;
    await openLane(HELD.wire);
    api.fetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      const path = String(url);
      if (path === "/api/gate/proposals/toolu_cut_1440/decide" && init?.method === "POST") {
        decided = true;
        return DECIDED.wire;
      }
      if (path.startsWith("/api/agent/launches/")) return decided ? AFTER.wire : HELD.wire;
      if (path === "/api/gate/proposals/toolu_cut_1440/command") return WHOLE.wire;
      if (path === "/api/gate/proposals/toolu_cut/command") return HEAD_ONLY.wire;
      if (path === "/api/gate/proposals/toolu_cut_huge/command") return PART.wire;
      if (path.startsWith("/api/gate/proposals")) return decided ? HELD_AFTER.wire : { proposals: [] };
      if (path.startsWith("/api/inference/assignments")) return ASSIGNMENTS.wire;
      throw new Error(`no captured hub answer for ${path}`);
    });
    act(() => useLane.getState().setRaw(true));
    const cards = await screen.findAllByTestId("lane-raw-held");
    expect(cards).toHaveLength(3);
    await waitFor(() => expect(screen.getAllByTestId("lane-raw-command")).toHaveLength(3));
  }
  const cardFor = (text: string) =>
    screen.getAllByTestId("lane-raw-held").find((el) => (within(el).queryByTestId("lane-raw-command")?.textContent ?? "") === text);

  /** replaces: tests/e2e/test_philo15_20_raw_approve_glass.py::test_raw_shows_a_cut_call_whole_and_approves_it_at_1440_and_393 */
  it("Approve shows only on the call the hub reads whole; a head-only call and a part offer Deny only", async () => {
    expect(WHOLE.wire.whole).toBe(true);
    expect(HEAD_ONLY.wire.whole).toBe(false);
    expect(PART.wire.whole).toBe(false);
    await openRaw();
    const whole = cardFor(WHOLE.wire.command)!;
    expect(whole.querySelector(".lw-caption")?.textContent).toMatch(/^HELD · OUTSIDE THE WORKTREE/);
    expect(within(whole).getByTestId("lane-raw-approve")).toBeTruthy();
    expect(within(whole).getByTestId("lane-raw-deny")).toBeTruthy();
    const headOnly = cardFor(HEAD_ONLY.wire.command)!;
    expect(headOnly.querySelector(".lw-caption")?.textContent).toContain("CUT ·");
    expect(within(headOnly).queryByTestId("lane-raw-approve")).toBeNull();
    expect(within(headOnly).getByTestId("lane-raw-deny")).toBeTruthy();
    const part = screen.getAllByTestId("lane-raw-held")
      .find((el) => (el.querySelector(".lw-caption")?.textContent ?? "").includes(`CUT · ${PART.wire.shown_chars} OF ${PART.wire.declared_chars} CHARS`))!;
    expect(part).toBeTruthy();
    expect(within(part).queryByTestId("lane-raw-approve")).toBeNull();
    expect(within(part).getByTestId("lane-raw-deny")).toBeTruthy();
  });

  /** replaces: tests/e2e/test_philo15_20_raw_approve_glass.py::test_raw_shows_a_cut_call_whole_and_approves_it_at_1440_and_393 (Approve, then the next read) */
  it("Approve decides it: the held card leaves on the hub's next lane read and the receipt stays", async () => {
    await openRaw();
    fireEvent.click(within(cardFor(WHOLE.wire.command)!).getByTestId("lane-raw-approve"));
    await waitFor(() =>
      expect(api.fetch).toHaveBeenCalledWith("/api/gate/proposals/toolu_cut_1440/decide", expect.objectContaining({
        method: "POST", json: expect.objectContaining({ decision: "approved" }),
      })),
    );
    await waitFor(() => expect(screen.getAllByTestId("lane-raw-held")).toHaveLength(2));
    expect(cardFor(WHOLE.wire.command)).toBeUndefined();
    expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^APPROVED · \d\d:\d\d$/);
    expect(screen.getByTestId("lane-raw-pane")).toBeTruthy();
  });
});

/* ── PHILO-17 final lane A: the draft chip on the Default for AI work ──
 * Recorded on a real hub by tests/integration/test_desk_agents_wire.py::
 * test_the_lane_draft_inherits_the_default_for_ai_work (fixtures/agents-default). */
function fixtureWire<T = unknown>(name: string): { captured_at: string; wire: T } {
  return hubWire<T>(`../fixtures/agents-default/${name}`);
}

describe("the lane's draft chip names the Default for AI work (PHILO-15 05)", () => {
  /** replaces: tests/e2e/test_philo15_05_strong_defaults_glass.py::test_the_lane_draft_chip_names_the_default */
  it("Cadence drafts inherit the global default: the chip names its model, never NOT SET", async () => {
    const lane = fixtureWire("lane");
    const assignments = fixtureWire("inference-assignments");
    await openLane(lane.wire, { "/api/inference/assignments": assignments.wire });
    const draft = screen.getByTestId("lane-ask").querySelector(".ask-well-draft")!;
    await waitFor(() => expect(draft.textContent?.toUpperCase()).toContain("QWEN3 8 27B"));
    expect(draft.textContent).not.toContain("NOT SET");
  });

  it("with no default at all the draft has no egress chip", async () => {
    await openLane(fixtureWire("lane").wire);
    const draft = screen.getByTestId("lane-ask").querySelector(".ask-well-draft")!;
    await waitFor(() => expect(draft.querySelector(".gadget-chip-egress")).toBeNull());
    expect(draft.textContent).not.toContain("NOT SET");
  });
});
