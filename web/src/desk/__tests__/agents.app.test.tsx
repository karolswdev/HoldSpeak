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
import { ApiError } from "../../lib/api";

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
import { branchFace } from "../lane/laneWire";
import { questionChoices } from "../agents/choices";
import { WhyThisStateBody, type ExplainWire } from "../agents/WhyThisState";
import { fromWireFlight, fromWireSessionRow, useAgentFlights } from "../agentFlights";
import { ConductorWindow } from "../conductor/ConductorWindow";
import { __resetConductor } from "../conductor/store";
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
    for (const word of ["BRIEF", "WORK", "COMMIT", "PR", "HELD", "ASKS"]) expect(track).toContain(word);
    expect(track).not.toContain("MERGE");
    expect(track).toContain("#413");
    expect(track).toContain("1 HELD · 1 WAITING");
    expect(track).toContain("now");
    expect(screen.getByTestId("lane-ask").querySelector(".ask-well-question")?.textContent).toBe(QUESTION);
    expect(screen.getByTestId("lane-ask").querySelector(".ask-well-draft")?.textContent).toContain("Jordan owns it. Avery reviews.");
    const rail = screen.getByTestId("lane-rail").textContent ?? "";
    for (const word of ["BRIEF", "READ", "SAYS", "WRITE", "RUN", "COMMIT", "PR", "HELD"]) expect(rail).toContain(word);
    expect(rail).toContain("Draft the ledger rollback runbook");
    expect(rail).toContain("psql -h staging-ledger");
    expect(rail).not.toContain("Your press in GitHub");
    expect(rail).not.toContain(QUESTION);
    const pr = screen.getByTestId("lane-pr").textContent ?? "";
    expect(pr).toContain("#413");
    expect(pr).toContain("CHECKS 6 OF 7");
    expect(pr).toContain("1 RUNNING");
    const files = screen.getByTestId("lane-files").textContent ?? "";
    expect(files).toContain("docs/ledger-rollback.md");
    expect(files).toContain("freeze.py");
    expect(screen.getAllByText("GITHUB.COM").length).toBeGreaterThan(0);
    expect(screen.getByTestId("lane-open-pr")).toBeTruthy();
    expect(screen.queryByTestId("lane-stop")).toBeNull(); // this recorded hub answer has no pane
  });

  /** replaces: tests/e2e/test_philo14_c2_lane_glass.py::test_the_agents_lane_window_at_1440_and_393 (Raw) */
  it("Raw puts the terminal pane in place of the lane, and back", async () => {
    await openLane(LANE.wire);
    fireEvent.click(screen.getByTestId("lane-raw"));
    expect(screen.getByTestId("lane-raw-pane")).toBeTruthy();
    expect(screen.getByTestId("lane-rail")).toBeTruthy();
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

/* ── Betterment AG0: tell the truth about state ───────────────────────
 * Recorded on a real hub by tests/integration/test_desk_agents_wire.py::
 * test_the_agents_read_says_done_new_quiet_and_stopped_by_restart
 * (fixtures/agents-ag0): one agent finished its turn with no PR, one asked
 * and then a restart took its tmux session. */
function ag0<T = unknown>(name: string): { captured_at: string; wire: T } {
  return hubWire<T>(`../fixtures/agents-ag0/${name}`);
}
const AG0 = ag0<{ sessions: unknown[]; flights: Array<Record<string, unknown>> }>("coders-sessions");
const AG0_SEEN = ag0("coders-sessions.seen");
const DETECT = hubWire("onboarding-agents.isolated");
const conductorMember = (id: string) => document.querySelector<HTMLElement>(`[data-object-id='${id}']`);

function pillOf(id: string): string {
  return conductorMember(id)?.querySelector("[data-testid='conductor-pill']")?.textContent ?? "";
}

describe("the Agents list tells the truth about state (Betterment AG0)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(AG0.captured_at));
    __resetConductor();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  });

  it("a finished turn with no PR reads Done · New; an agent a restart took reads Stopped by restart and never asks", async () => {
    serve({ "/api/coders/sessions": AG0.wire, "/api/onboarding/agents": DETECT.wire });
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Draft test scaffolding for flags" });
    expect(pillOf("launch:launch_ag0_done")).toBe("Done · New");
    // Nothing asks: no NEEDS YOU plate, no ASK in the head, and Done is not "at work".
    expect(screen.queryByTestId("conductor-asks")).toBeNull();
    const head = screen.getByTestId("conductor-head");
    expect(head.textContent).not.toContain("ASK");
    expect(head.querySelector(".kit-disp")?.textContent).not.toMatch(/at work/);
    // The ghost stands under STOPPED BY RESTART, in words, with Resume (AG6).
    const stopped = screen.getByTestId("conductor-stopped");
    expect(within(stopped).getByRole("button", { name: "Write the on-call note" })).toBeTruthy();
    expect(pillOf("launch:launch_ag0_ghost")).toBe("Stopped by restart");
    expect(within(stopped).getByRole("button", { name: "Resume" })).toBeTruthy();
    expect(document.body.textContent).not.toContain("Working");
  });

  it("after the seen mark the same agent reads Quiet", async () => {
    serve({ "/api/coders/sessions": AG0_SEEN.wire, "/api/onboarding/agents": DETECT.wire });
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Draft test scaffolding for flags" });
    expect(pillOf("launch:launch_ag0_done")).toBe("Quiet");
  });

  it("opening the agent's window marks its done turn seen (the hub's seen route, then Quiet)", async () => {
    const lane = ag0<{ launch: { session_key: string } }>("lane.done");
    const seen = ag0<{ seen: string }>("seen");
    serve({
      "/api/agent/launches/launch_ag0_done/seen": seen.wire,
      "/api/agent/launches/": lane.wire,
      "/api/coders/sessions": AG0.wire,
      "/api/inference/assignments": ASSIGNMENTS.wire,
      "/api/gate/proposals": { proposals: [] },
    });
    steering();
    useAgentFlights.setState({
      flights: AG0.wire.flights.map((f) => fromWireFlight(f as never)),
      sessions: AG0.wire.sessions.map(fromWireSessionRow),
      loaded: true,
    });
    const [done] = useAgentFlights.getState().flights.filter((f) => f.launchId === "launch_ag0_done");
    expect(done.isNew).toBe(true);
    render(<LaneWindow />);
    await act(async () => {
      await useLane.getState().open("launch_ag0_done", { sessionKey: lane.wire.launch.session_key });
    });
    // On open the lane asks the hub to mark its current done turn; the hub's
    // answer names that turn.
    await waitFor(() =>
      expect(api.fetch).toHaveBeenCalledWith("/api/agent/launches/launch_ag0_done/seen", { method: "POST", json: {} }),
    );
    expect(seen.wire.seen).toBe(done.turnId);
    expect(useAgentFlights.getState().flights.find((f) => f.launchId === "launch_ag0_done")?.isNew).toBe(false);
  });

  it("an Answer to an agent whose terminal is gone says so; no ARM step (Betterment AG2)", async () => {
    const lane = ag0<{ launch: { session_key: string }; wait: { wait_id: string } }>("lane.ghost");
    // The hub's refusal when the pane is gone (recorded for the ARM; the
    // steer route refuses with the same status).
    const refused = ag0("arm.refused");
    serve({
      "/api/agent/launches/": lane.wire,
      "/api/coders/sessions": AG0.wire,
      "/api/inference/assignments": ASSIGNMENTS.wire,
      "/api/gate/proposals": { proposals: [] },
    });
    const posted: Array<[string, unknown]> = [];
    api.request.mockImplementation(async (url: string, init?: RequestInit) => {
      posted.push([String(url), init?.body ? JSON.parse(String(init.body)) : null]);
      return String(url).endsWith("/steer")
        ? ({ ok: false, status: 409, json: async () => refused.wire } as unknown as Response)
        : ({ ok: true, status: 200, json: async () => ({}) } as unknown as Response);
    });
    steering();
    render(<LaneWindow />);
    await act(async () => {
      await useLane.getState().open("launch_ag0_ghost", { sessionKey: lane.wire.launch.session_key });
    });
    const well = await screen.findByTestId("lane-ask");
    // Normal mode, not armed: no ARM on the face.
    expect(screen.queryByTestId("lane-arm")).toBeNull();
    expect(document.body.textContent).not.toContain("ARM FIRST");
    fireEvent.change(within(well).getByRole("textbox", { name: "Answer" }), { target: { value: "1" } });
    await act(async () => {
      fireEvent.click(within(well).getByRole("button", { name: "Answer" }));
    });
    await waitFor(() => expect(screen.getByTestId("lane-terminal-gone").textContent).toBe("This agent's terminal is gone"));
    const steer = posted.find(([url]) => url.endsWith("/steer"));
    expect(steer?.[1]).toMatchObject({ text: "1", kind: "answer", wait_id: lane.wire.wait.wait_id });
  });
});

/* ── Betterment AG1: one name, Agents ─────────────────────────────── */

/** The words the agent faces no longer say (DESIGN.md §4, "The words"). */
const OLD_WORDS = /Conductor|\bcoders?\b|\bCODERS?\b|Re-brief|RE-BRIEF|Install hooks|ASKS YOU|WANTS APPROVAL|Wants approval|\brider\b|\bNODE\b|\bTARGET\b|INCOMPATIBLE|stopped_by_owner|\bRaw\b/;

describe("the agent faces say Agents and agent (Betterment AG1)", () => {
  beforeEach(() => {
    __resetConductor();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  });

  it("the Agents window on the hub's C4 and AG0 answers: its title is Agents, no old word, Connect for hooks", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    const c4 = hubWire("coders-sessions.c4");
    vi.setSystemTime(new Date(c4.captured_at));
    serve({ "/api/coders/sessions": c4.wire, "/api/onboarding/agents": DETECT.wire,
      "/api/agent/launches/": hubWire("lane.c4-runbook").wire });
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    expect(screen.getAllByText("Agents").length).toBeGreaterThan(0);
    const plate = screen.getByTestId("conductor-ask-row");
    expect(plate.querySelector(".cw-ask-label")?.textContent).toBe("Asks you");
    expect(document.body.textContent).not.toMatch(OLD_WORDS);
    // Stop confirms in the agent's words.
    fireEvent.click(within(conductorMember("launch:launch_c4_runbook")!).getByRole("button", { name: "Write the rollback runbook" }));
    fireEvent.click(await screen.findByTestId("conductor-stop"));
    expect(screen.getByTestId("conductor-stop-confirm").textContent).toBe("Stop · sure? (ends the agent's session)");
    expect(document.body.textContent).not.toMatch(OLD_WORDS);
  });

  it("the agent's window: Terminal and Story, a held call says Wants to run, no old word", async () => {
    await openLane(LANE_CUT.wire);
    expect(screen.getByTestId("lane-raw").textContent).toBe("Terminal");
    expect(screen.getByTestId("lane-approve-well").querySelector(".lw-plate-label")?.textContent).toBe("Wants to run");
    expect(screen.getByTestId("lane-raw-cut").textContent).toBe("Terminal");
    // Tell it (was Re-brief) needs a live pane; laneWindow.c2.test.tsx drives it.
    expect(document.body.textContent).not.toMatch(OLD_WORDS);
    fireEvent.click(screen.getByTestId("lane-raw"));
    expect(screen.getByTestId("lane-raw").textContent).toBe("Story");
  });

  it("branchFace: the hub's id branch reads new branch; a branch with words shows as it is", () => {
    expect(branchFace("hs/action-action_5f5e1a2b")).toBe("new branch");
    expect(branchFace("hs/note-0123456789abcdef")).toBe("new branch");
    expect(branchFace("hs/action-ai_1")).toBe("new branch");
    expect(branchFace("hs/write-the-rollback-runbook")).toBe("hs/write-the-rollback-runbook");
    expect(branchFace("feature/flags")).toBe("feature/flags");
    expect(branchFace(null)).toBe("");
  });
});

/* ── Betterment AG2: one press to answer and to allow ─────────────────
 * Recorded on a real hub by tests/integration/test_desk_agents_wire.py::
 * test_the_agents_read_asks_with_choices_and_answers_without_an_arm
 * (fixtures/agents-ag2: one agent asks "Answer 1 for config, 2 for env.",
 * one waits at a permission prompt; Normal mode, nothing armed). Betterment
 * AG7: the command and the agent's own menu come from the hub's screen rules
 * (fixtures/agents-ag7), no longer from the row's own read of the pane. */
function ag2<T = unknown>(name: string): { captured_at: string; wire: T } {
  return hubWire<T>(`../fixtures/agents-ag2/${name}`);
}

describe("one press to answer and to allow (Betterment AG2)", () => {
  const SESSIONS = ag2<{ sessions: Array<{ session: Record<string, unknown> }> }>("coders-sessions");
  const LANE_ASKS = ag2<{ wait: { wait_id: string; question: string } }>("lane.asks");
  const waitOf = (sid: string) => String(SESSIONS.wire.sessions.find((r) => r.session.session_id === sid)?.session.wait_id ?? "");
  const posts = () => api.fetch.mock.calls
    .filter(([, init]) => (init as { method?: string } | undefined)?.method === "POST")
    .map(([url, init]) => [String(url), (init as { json?: unknown }).json] as const);

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(SESSIONS.captured_at));
    __resetConductor();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
    serve({
      "/api/coders/sessions": SESSIONS.wire,
      "/api/onboarding/agents": DETECT.wire,
      "/api/agent/launches/launch_ag0_ghost/lane": LANE_ASKS.wire,
      "/api/agent/launches/": { gated: [], wait: null },
      "/api/coders/claude%3Aag0-ghost/steer": { status: "delivered", pane_id: "%4242" },
      "/api/coders/claude%3Aag2-held/keys": { status: "delivered", pane_id: "%4243" },
    });
  });

  async function rows() {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the on-call note" });
    const asks = within(screen.getByTestId("conductor-asks")).getAllByTestId("conductor-ask-row");
    const asking = asks.find((row) => row.dataset.objectId === "launch:launch_ag0_ghost")!;
    const held = asks.find((row) => row.dataset.objectId === "coder:claude:ag2-held")!;
    return { asking, held };
  }

  it("the row shows the whole question and 1 · config / 2 · env; one press sends 1 with the wait", async () => {
    const { asking } = await rows();
    expect(asking.querySelector(".cw-ask-label")?.textContent).toBe("Asks you");
    expect(asking.textContent).toContain(LANE_ASKS.wire.wait.question);
    await waitFor(() => expect(within(asking).getAllByTestId("agent-row-choice").map((b) => b.textContent))
      .toEqual(["1 · config", "2 · env"]));
    expect(document.body.textContent).not.toMatch(/ARM/);
    await act(async () => {
      fireEvent.click(within(asking).getByRole("button", { name: "1 · config" }));
    });
    expect(posts()).toEqual([["/api/coders/claude%3Aag0-ghost/steer",
      { text: "1", submit: true, kind: "answer", wait_id: waitOf("ag0-ghost") }]]);
    expect(LANE_ASKS.wire.wait.wait_id).toBe(waitOf("ag0-ghost"));
    await waitFor(() => expect(within(asking).getByTestId("agent-row-receipt").textContent).toBe("Sent · 1 · config"));
  });

  it("a typed answer goes in one press too (Answer)", async () => {
    const { asking } = await rows();
    const field = within(asking).getByTestId("agent-row-answer-field") as HTMLInputElement;
    fireEvent.change(field, { target: { value: "Use config, and add a test" } });
    await act(async () => {
      fireEvent.click(within(asking).getByRole("button", { name: "Answer" }));
    });
    expect(posts()).toEqual([["/api/coders/claude%3Aag0-ghost/steer",
      { text: "Use config, and add a test", submit: true, kind: "answer", wait_id: waitOf("ag0-ghost") }]]);
  });

  it("Wants to run: Allow sends Enter, Deny sends Escape", async () => {
    const { held } = await rows();
    expect(held.querySelector(".cw-ask-label")?.textContent).toBe("Wants to run");
    await act(async () => {
      fireEvent.click(within(held).getByRole("button", { name: "Allow" }));
    });
    expect(posts()).toEqual([["/api/coders/claude%3Aag2-held/keys",
      { keys: ["Enter"], kind: "answer", wait_id: waitOf("ag2-held") }]]);
    await waitFor(() => expect(within(held).getByTestId("agent-row-receipt").textContent).toBe("Sent · Allowed"));
    api.fetch.mockClear();
    await act(async () => {
      fireEvent.click(within(held).getByRole("button", { name: "Deny" }));
    });
    expect(posts()).toEqual([["/api/coders/claude%3Aag2-held/keys",
      { keys: ["Escape"], kind: "answer", wait_id: waitOf("ag2-held") }]]);
  });
});

describe("the choices a question offers (Betterment AG2)", () => {
  it("reads 'Answer 1 for …, 2 for …' in the question; a plain question has none", () => {
    expect(questionChoices("Ship it now? Answer 1 for yes, 2 for no, 3 for later.").map((c) => `${c.n} · ${c.label}`))
      .toEqual(["1 · yes", "2 · no", "3 · later"]);
    expect(questionChoices("Jordan or Avery?")).toEqual([]);
  });
});

/* ── Betterment AG7: screen rules (the herdr port) ─────────────────────
 * Recorded on a real hub by tests/integration/test_desk_agents_wire.py::
 * test_the_agents_read_states_from_the_screen_when_no_hook_speaks
 * (fixtures/agents-ag7): three agents with their hooks off; the hub's
 * watcher read their real tmux panes (the fake Claude Code's recorded
 * screens) with herdr's rules. */
function ag7<T = unknown>(name: string): { captured_at: string; wire: T } {
  return hubWire<T>(`../fixtures/agents-ag7/${name}`);
}

describe("the screen says the state when no hook speaks (Betterment AG7)", () => {
  const SESSIONS = ag7<{ flights: Array<Record<string, unknown>> }>("coders-sessions");
  const WHY = ag7<ExplainWire>("explain.held");

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(SESSIONS.captured_at));
    __resetConductor();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
    serve({
      "/api/coders/sessions": SESSIONS.wire,
      "/api/onboarding/agents": DETECT.wire,
      "/api/agent/launches/": { gated: [], wait: null },
    });
  });

  it("Wants to run shows the command the rules read; with no hook to answer, Terminal leads", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Release the rollback build" });
    const held = within(screen.getByTestId("conductor-asks")).getAllByTestId("conductor-ask-row")
      .find((row) => row.dataset.objectId === "launch:launch_ag7_held")!;
    expect(held.querySelector(".cw-ask-label")?.textContent).toBe("Wants to run");
    expect(within(held).getByTestId("agent-row-command").textContent).toMatch(/^rm -rf build\/ && make release/);
    expect(within(held).getByTestId("agent-row-terminal").textContent).toBe("Terminal");
    expect(within(held).queryByRole("button", { name: "Allow" })).toBeNull();
  });

  it("Asks you shows the agent's last words and their choices; Done is New", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Move the rollback flag" });
    const asks = within(screen.getByTestId("conductor-asks")).getAllByTestId("conductor-ask-row")
      .find((row) => row.dataset.objectId === "launch:launch_ag7_asks")!;
    expect(asks.querySelector(".cw-ask-label")?.textContent).toBe("Asks you");
    expect(within(asks).getByTestId("agent-row-question").textContent).toContain("Should it live in config/flags.yaml");
    expect(within(asks).getAllByTestId("agent-row-choice").map((b) => b.textContent)).toEqual(["1 · config", "2 · env"]);
    const done = screen.getAllByTestId("conductor-row").find((row) => row.dataset.objectId === "launch:launch_ag7_done")!;
    expect(within(done).getByTestId("conductor-pill").textContent).toBe("Done · New");
  });

  it("Why this state names the source, the rule, its file and the lines it matched", () => {
    render(<WhyThisStateBody explain={WHY.wire} />);
    expect(screen.getByTestId("lane-why-source").textContent).toBe("From: The agent's screen");
    expect(screen.getByTestId("lane-why-rule").textContent).toBe(
      "Rule: bash_permission_prompt · claude.toml 2026.10.11.1 (bundled)");
    expect(screen.getByTestId("lane-why-evidence").textContent).toContain("Do you want to proceed?");
    expect(screen.queryByTestId("lane-why-hook")).toBeNull();
  });
});

/* ── Betterment AG5: working at once, and a queue ─────────────────────
 * Recorded on a real hub by tests/integration/test_desk_agents_wire.py::
 * test_the_agents_read_counts_only_working_agents_and_shows_a_queued_hand
 * (fixtures/agents-ag5): the limit is 2; one agent is done, one asks, and a
 * third hand waits for a free agent. */
const AG5 = hubWire<{ flights: Array<Record<string, unknown>>; launches: { live: number; cap: number } }>(
  "../fixtures/agents-ag5/coders-sessions",
);

describe("working at once, and a queue (Betterment AG5)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(AG5.captured_at));
    __resetConductor();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  });

  it("a queued hand reads Waits for a free agent, has no Open, and is not at work", async () => {
    const queued = AG5.wire.flights.find((f) => f.state === "queued")!;
    serve({ "/api/coders/sessions": AG5.wire, "/api/onboarding/agents": DETECT.wire });
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Rotate the staging keys" });
    const id = `queue:${String(queued.queue_id)}`;
    expect(pillOf(id)).toBe("Waits for a free agent");
    expect(within(conductorMember(id)!).queryByTestId("conductor-open")).toBeNull();
    expect(pillOf("launch:launch_ag0_done")).toBe("Done · New");
    // The head: the done agent and the queued hand are not at work.
    expect(screen.getByTestId("conductor-head").querySelector(".kit-disp")?.textContent).not.toMatch(/at work/);
    // Selecting the queued row offers no Stop (nothing runs yet).
    fireEvent.click(within(conductorMember(id)!).getByRole("button", { name: "Rotate the staging keys" }));
    expect(screen.queryByTestId("conductor-stop")).toBeNull();
  });

  it("the flight wire carries the queued state and its queue id", () => {
    const flight = fromWireFlight(AG5.wire.flights.find((f) => f.state === "queued"));
    expect(flight.state).toBe("queued");
    expect(flight.queueId).toMatch(/^queue_/);
    expect(flight.launchId).toBeNull();
    expect(AG5.wire.launches.cap).toBe(2);
  });
});

/* ── Betterment AG6: Resume after a restart ───────────────────────────
 * Recorded on a real hub by tests/integration/test_desk_agents_wire.py::
 * test_the_agents_read_offers_resume_for_agents_a_restart_stopped
 * (fixtures/agents-ag6): a restart took both agents; this rig's launches
 * have no worktree, so the hub refuses the Resume by name. */
const AG6 = hubWire<{ history: Array<Record<string, unknown>> }>("../fixtures/agents-ag6/coders-sessions");
const AG6_REFUSED = hubWire<Record<string, unknown>>("../fixtures/agents-ag6/resume.refused");

describe("Resume after a restart (Betterment AG6)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(AG6.captured_at));
    __resetConductor();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  });

  it("each agent a restart stopped has Resume; two or more give Resume all in the head", async () => {
    serve({ "/api/coders/sessions": AG6.wire, "/api/onboarding/agents": DETECT.wire });
    render(<ConductorWindow />);
    const stopped = await screen.findByTestId("conductor-stopped");
    expect(within(stopped).getAllByRole("button", { name: "Resume" })).toHaveLength(2);
    expect(pillOf("launch:launch_ag0_done")).toBe("Stopped by restart");
    expect(pillOf("launch:launch_ag0_ghost")).toBe("Stopped by restart");
    expect(screen.getByTestId("conductor-resume-all").textContent).toBe("Resume all");
    expect(screen.queryByTestId("conductor-ended")).toBeNull();
  });

  it("one press posts the resume; the hub's refusal reads NOT RESUMED with its reason", async () => {
    serve({ "/api/coders/sessions": AG6.wire, "/api/onboarding/agents": DETECT.wire });
    const served = api.fetch.getMockImplementation()!;
    api.fetch.mockImplementation(async (url: string, init?: unknown) => {
      if (String(url).endsWith("/resume")) throw new ApiError(409, "refused", AG6_REFUSED.wire);
      return served(url, init);
    });
    render(<ConductorWindow />);
    const row = (await screen.findByTestId("conductor-stopped")).querySelector<HTMLElement>("[data-object-id='launch:launch_ag0_ghost']")!;
    fireEvent.click(within(row).getByRole("button", { name: "Resume" }));
    const receipt = await screen.findByTestId("conductor-stop-receipt");
    expect(receipt.textContent).toBe(`NOT RESUMED · ${String(AG6_REFUSED.wire.code).replace(/_/g, " ")}`);
    const posts = api.fetch.mock.calls.filter(([u, i]) => String(u).endsWith("/resume") && (i as { method?: string })?.method === "POST");
    expect(posts.map(([u]) => u)).toEqual(["/api/agent/launches/launch_ag0_ghost/resume"]);
  });

  it("Resume all posts every stopped agent in one press", async () => {
    serve({ "/api/coders/sessions": AG6.wire, "/api/onboarding/agents": DETECT.wire });
    const served = api.fetch.getMockImplementation()!;
    api.fetch.mockImplementation(async (url: string, init?: unknown) => {
      if (String(url).endsWith("/resume")) throw new ApiError(409, "refused", AG6_REFUSED.wire);
      return served(url, init);
    });
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByTestId("conductor-resume-all"));
    await waitFor(() => {
      const posts = api.fetch.mock.calls.filter(([u]) => String(u).endsWith("/resume")).map(([u]) => String(u)).sort();
      expect(posts).toEqual(["/api/agent/launches/launch_ag0_done/resume", "/api/agent/launches/launch_ag0_ghost/resume"]);
    });
  });
});

/* ── Betterment AG3: the desk's own answers are visible ───────────────
 * Recorded on a real hub by tests/integration/test_desk_agents_wire.py::
 * test_the_agents_read_shows_the_desks_own_answer (fixtures/agents-ag3):
 * under YOLO the real responder holds "Answer 1 for config, 2 for env.",
 * answers `1` from the Project's decision (the recorded LAN draft), and the
 * seen mark makes the answer old. */
function ag3<T = unknown>(name: string): { captured_at: string; wire: T } {
  return hubWire<T>(`../fixtures/agents-ag3/${name}`);
}

describe("the desk's own answers are visible (Betterment AG3)", () => {
  const DECISION = "The desk answered: 1, from your decision 'The rollback flag moves into config/flags.yaml.'";

  function serveAg3(sessions: string) {
    const read = ag3(sessions);
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(read.captured_at));
    __resetConductor();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
    serve({
      "/api/coders/sessions": read.wire,
      "/api/onboarding/agents": DETECT.wire,
      "/api/agent/launches/launch_ag0_ghost/lane": ag3("lane.drafting").wire,
      "/api/agent/launches/": { gated: [], wait: null },
      "/api/coders/claude%3Aag0-ghost/peek": hubWire("peek.ag2-asks").wire,
      "/api/coders/claude%3Aag0-done/peek": hubWire("peek.ag2-asks").wire,
    });
  }
  const ghost = () => document.querySelector<HTMLElement>('[data-object-id="launch:launch_ag0_ghost"]')!;

  it("while the desk drafts, the row says so and offers Answer it myself, then the answer box", async () => {
    serveAg3("coders-sessions.drafting");
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the on-call note" });
    const row = ghost();
    expect(within(row).getByTestId("agent-row-drafting").textContent).toContain("The desk is drafting an answer");
    expect(within(row).queryByTestId("agent-row-choices")).toBeNull();
    fireEvent.click(within(row).getByRole("button", { name: "Answer it myself" }));
    expect(within(row).queryByTestId("agent-row-drafting")).toBeNull();
    await waitFor(() => expect(within(row).getAllByTestId("agent-row-choice").map((b) => b.textContent))
      .toEqual(["1 · config", "2 · env"]));
  });

  it("after the desk answered: what it said and the decision it used, New until opened", async () => {
    serveAg3("coders-sessions.answered");
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the on-call note" });
    const line = within(ghost()).getByTestId("agent-row-desk-answer");
    expect(line.textContent).toBe(`${DECISION}New`);
    expect(line.textContent).not.toMatch(/Yes,/);
    expect(within(line).getByTestId("agent-row-desk-answer-new").textContent).toBe("New");
  });

  it("after the seen mark the answer stays, without New", async () => {
    serveAg3("coders-sessions.seen");
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the on-call note" });
    const line = within(ghost()).getByTestId("agent-row-desk-answer");
    expect(line.textContent).toBe(DECISION);
  });

  it("opening the agent marks the desk's answer seen at once", async () => {
    const { markLaunchSeen } = await import("../agentFlights");
    const answered = ag3<{ flights: unknown[] }>("coders-sessions.answered").wire;
    useAgentFlights.setState({ flights: answered.flights.map(fromWireFlight), sessions: [], loaded: true });
    api.fetch.mockResolvedValue({ launch_id: "launch_ag0_ghost", seen: null, answer_seen: "w" });
    await markLaunchSeen("launch_ag0_ghost", null);
    const flight = useAgentFlights.getState().flights.find((f) => f.launchId === "launch_ag0_ghost")!;
    expect(flight.deskAnswer).toMatchObject({ state: "answered", text: "1", isNew: false });
  });
});
