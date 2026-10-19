// PHILO-14 C4 — the Conductor drawer: where agents live (ratified boards
// A-1, A-4). The members (ready, live, stale), their lamps, the head (no
// zero said; `3 OF 3` only at the cap), what Open does, Answer, Install
// hooks, Copy install, NOT READ + Retry, and Get Info from the lane route.
// It also carries what the Agents application (`agents.test.tsx`) and the
// Arrival's AGENTS section (`conductorF2.test.tsx` K4c) proved: every live
// session is listed, the asking one with Answer; a handed one names its item.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { fromWireFlight, fromWireSessionRow, useAgentFlights } from "../../agentFlights";
import { ConductorWindow, HOOKS_LINE, headFact } from "../ConductorWindow";
import { ConductorInfoWindow } from "../ConductorInfoWindow";
import { canRun, closeReceipt, conductorHead, conductorMembers, headWords, readyMember } from "../members";
import { __resetConductor, useConductor } from "../store";
import { laneSessionKey as laneSessionKeyOf } from "../../lane/laneStore";
import { ApiError } from "../../../lib/api";
import { useGate } from "../../gate";



const apiFetch = vi.fn();
const apiRequest = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return {
    ...actual,
    apiFetch: (...args: unknown[]) => apiFetch(...args),
    apiRequest: (...args: unknown[]) => apiRequest(...args),
  };
});
const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});
const shell = vi.hoisted(() => ({ lanes: [] as unknown[][], sessions: [] as unknown[][] }));
vi.mock("../../shell", async () => {
  const actual = await vi.importActual<typeof import("../../shell")>("../../shell");
  return {
    ...actual,
    openAgentLane: (...args: unknown[]) => shell.lanes.push(args),
    openCoderSession: (...args: unknown[]) => shell.sessions.push(args),
  };
});

const NOW = new Date();
const ago = (minutes: number) => new Date(NOW.getTime() - minutes * 60_000).toISOString();
const QUESTION = "The runbook needs a rollback owner. Jordan or Avery?";

const FLIGHT_RUNBOOK = {
  origin_ref: "action:ai-runbook", kind: "action", id: "ai-runbook", title: "Write the rollback runbook",
  project_id: "p-ledger", project_name: "Payments ledger cutover", agent: "claude", state: "waiting",
  session_key: "claude:c1", pr: null, close: null, merged_at: null, launch_id: "l-runbook", launched_at: ago(30),
};
const FLIGHT_RECON = {
  ...FLIGHT_RUNBOOK, origin_ref: "action:ai-recon", id: "ai-recon", title: "Shard the reconciliation job",
  agent: "codex", state: "working", session_key: "codex:x1", launch_id: "l-recon",
};
const FLIGHT_FLAG = {
  ...FLIGHT_RUNBOOK, origin_ref: "action:ai-flag", id: "ai-flag", title: "Add the ledger freeze flag",
  state: "pr_open", session_key: null, launch_id: "l-flag",
  pr: { number: 412, url: "https://github.com/acme/payments-ledger/pull/412", state: "open" },
};
const FLIGHT_DONE = {
  ...FLIGHT_RUNBOOK, origin_ref: "action:ai-done", id: "ai-done", title: "Write the cutover checklist",
  state: "merged", session_key: "claude:gone", launch_id: "l-done", close: "closed", session_cleanup: "killed",
  merged_at: ago(120), pr: { number: 413, url: "https://github.com/acme/payments-ledger/pull/413", state: "merged" },
};
const FLIGHT_DONE_ENDED = { ...FLIGHT_DONE, ended_at: FLIGHT_DONE.merged_at };
// Started 30 h ago, ended 2 min ago: in the last 24 h (the cut is the END).
const FLIGHT_OLD = {
  ...FLIGHT_RUNBOOK, origin_ref: "action:ai-old", id: "ai-old", title: "Write last week's note",
  state: "ended", session_key: "claude:old", launch_id: "l-old", launched_at: ago(60 * 30), ended_at: ago(2),
};
// Ended 25 h ago: gone.
const FLIGHT_GONE = { ...FLIGHT_OLD, origin_ref: "action:ai-gone", id: "ai-gone", title: "Write the gone note", launch_id: "l-gone", ended_at: ago(60 * 25) };

const SESSIONS = {
  sessions: [
    { session: { agent: "claude", session_id: "c1", state: "waiting", question: QUESTION, hook_event_name: "Notification",
      repo_root: "/h/dev/payments-ledger-runbook", updated_at: ago(2) }, flight: FLIGHT_RUNBOOK },
    { session: { agent: "codex", session_id: "x1", state: "working", repo_root: "/h/dev/payments-ledger-recon", updated_at: ago(1) }, flight: FLIGHT_RECON },
    { session: { agent: "claude", session_id: "solo", state: "working", repo_root: "/h/dev/scratch", updated_at: ago(5) } },
  ],
  flights: [FLIGHT_RUNBOOK, FLIGHT_RECON, FLIGHT_FLAG, FLIGHT_DONE_ENDED, FLIGHT_OLD],
  history: [FLIGHT_OLD, FLIGHT_DONE_ENDED, FLIGHT_GONE],
  launches: { live: 3, cap: 3 },
};

const DETECT = {
  agents: [
    { id: "claude", label: "Claude Code", installed: true, path: "/bin/claude", version: "2.1.0", hooks: "installed", signed_in: "yes", ready: true, verb: null },
    { id: "codex", label: "Codex", installed: false, path: null, version: null, hooks: "missing", signed_in: "unknown", ready: false, verb: null },
  ],
  tmux: { installed: true, path: "/bin/tmux", version: "3.4", install_hint: null },
};

let sessionsReply: () => unknown = () => SESSIONS;
let detectReply: () => unknown = () => DETECT;

function route(url: string, init?: { method?: string }): unknown {
  if (url.startsWith("/api/coders/sessions")) return sessionsReply();
  if (url === "/api/onboarding/agents") return detectReply();
  if (url === "/api/onboarding/agents/use" && init?.method === "POST") return { status: "installed" };
  if (url.startsWith("/api/agent/launches/l-runbook/lane"))
    return { launch: { branch: "hs/write-the-rollback-runbook", launched_at: FLIGHT_RUNBOOK.launched_at, control_mode: "normal" } };
  return null;
}

beforeEach(() => {
  localStorage.clear();
  bus.handlers.clear();
  shell.lanes = [];
  shell.sessions = [];
  sessionsReply = () => SESSIONS;
  detectReply = () => DETECT;
  apiFetch.mockReset();
  apiRequest.mockReset();
  apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
    const body = route(url, init);
    if (body instanceof Error) throw body;
    return body;
  });
  __resetConductor();
  useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  useGate.setState({ held: [], loaded: false, error: null });
  useDesk.setState({ items: { ...EMPTY_ITEMS }, zoneViewPrefs: {}, panelRects: {}, panelOrder: [], panelMin: [] });
});

function fixtureMembers() {
  return conductorMembers({
    detect: DETECT.agents as never,
    sessions: SESSIONS.sessions.map(fromWireSessionRow),
    flights: SESSIONS.flights.map(fromWireFlight),
    launchedAt: Object.fromEntries(SESSIONS.flights.map((f) => [f.launch_id, f.launched_at])),
    history: SESSIONS.history.map(fromWireFlight),
    endedAt: Object.fromEntries(SESSIONS.history.map((f) => [f.launch_id, f.ended_at])),
    now: NOW,
  });
}

/** A row's name (a press selects it). PHILO-17 THE REFIT: the Conductor
 *  lists its coders as rows; the name is the item the coder works on. */
const icon = (name: RegExp | string) => screen.getByRole("button", { name });
const rowOf = (name: string) => screen.getByRole("button", { name }).closest("[data-object-id]") as HTMLElement;
const pillOf = (name: string) => within(rowOf(name)).getByTestId("conductor-pill").textContent;
/* Betterment AG8: "On this Mac" shows only when something is missing (no
 * fold to open). */

describe("PHILO-14 C4 the Conductor members", () => {
  it("asking first, then at work, ready, stale: once each, with the screen's names and lamps", () => {
    const members = fixtureMembers();
    expect(members.map((m) => [m.role, m.name, m.lamp?.label ?? null, m.id, m.group])).toEqual([
      ["live", "Claude Code: rollback runbook", "ASKS", "launch:l-runbook", 0],
      ["live", "Codex: reconciliation job", "WORKS", "launch:l-recon", 1],
      // A session no launch holds is its session.
      ["live", "Claude Code: scratch", "WORKS", "coder:claude:solo", 1],
      // In flight with no live session: its PR is the fact.
      ["live", "Claude Code: ledger freeze flag", "PR #412", "launch:l-flag", 1],
      ["ready", "Claude Code", null, "agent:claude", 2],
      ["ready", "Codex", "NOT INSTALLED", "agent:codex", 2],
      // Ended in the last 24 h, newest end first, cut on the END (l-old
      // started 30 h ago, ended 2 min ago); the one that ended 25 h ago is gone.
      ["stale", "Claude Code: last week's note", null, "launch:l-old", 3],
      ["stale", "Claude Code: cutover checklist", null, "launch:l-done", 3],
    ]);
    const stale = members.find((m) => m.id === "launch:l-done")!;
    expect(stale.receipt).toBe("PR #413 MERGED · ITEM CLOSED · SESSION STOPPED");
    expect(stale.sprite).toMatch(/agent-claude-code_stale\.png$/);
    expect(members.find((m) => m.agent === "codex" && m.role === "live")!.sprite).toMatch(/agent-codex\.png$/);
  });

  it("a launched agent keeps its launch identity when its session binds (Astra r1 P2)", () => {
    const starting = { ...FLIGHT_RECON, state: "starting", session_key: null };
    const before = conductorMembers({ detect: null, sessions: [], flights: [fromWireFlight(starting)], launchedAt: {}, now: NOW });
    const after = conductorMembers({
      detect: null, sessions: [fromWireSessionRow(SESSIONS.sessions[1])], flights: [fromWireFlight(FLIGHT_RECON)], launchedAt: {}, now: NOW,
    });
    expect(before.map((m) => [m.id, m.lamp?.label])).toEqual([["launch:l-recon", "STARTS"]]);
    expect(after.map((m) => [m.id, m.lamp?.label, m.sessionKey])).toEqual([["launch:l-recon", "WORKS", "codex:x1"]]);
  });

  it("PHILO-15 15: an agent whose turn ended in a done report reads DONE, not ASKS", () => {
    const row = SESSIONS.sessions[0] as Record<string, unknown>;
    const flight = { ...(row.flight as Record<string, unknown>), turn_end: "done" };
    const members = conductorMembers({
      detect: null, sessions: [fromWireSessionRow({ ...row, flight })], flights: [fromWireFlight(flight)], launchedAt: {}, now: NOW,
    });
    const [live] = members.filter((m) => m.role === "live");
    expect([live.lamp?.label, live.lamp?.tone, live.live]).toEqual(["DONE", "ok", "done"]);
    expect(conductorHead(members, { live: 1, cap: 3 }).ask).toBe(0);
  });

  it("a permission prompt is HELD; the ended receipt words", () => {
    const held = conductorMembers({
      detect: null,
      sessions: [fromWireSessionRow({ session: { agent: "claude", session_id: "p1", state: "waiting", question: "Run psql?",
        hook_event_name: "Notification", notification_type: "permission_prompt" } })],
      flights: [], launchedAt: {}, now: NOW,
    });
    expect(held.map((m) => [m.lamp?.label, m.live])).toEqual([["HELD", "held"]]);
    expect(closeReceipt(fromWireFlight({ ...FLIGHT_OLD, close: null }))).toBe("ENDED");
    expect(closeReceipt(fromWireFlight({ ...FLIGHT_OLD, state: "expired" }))).toBe("SESSION GONE");
  });

  it("the head omits zeros; N OF M is the hub's own count, only at its cap (Astra r1 P2)", () => {
    const head = conductorHead(fixtureMembers(), { live: 3, cap: 3 });
    expect(head.atWork).toBe(3);
    expect(head.ask).toBe(1);
    expect(headWords(head)).toEqual(["3 AT WORK", "1 ASK", "3 OF 3"]);
    // Three PR flights whose agents left: the hub counts 0 running; no cap word.
    expect(headWords(conductorHead(fixtureMembers(), { live: 0, cap: 3 }))).toEqual(["3 AT WORK", "1 ASK"]);
    // Not served: never guessed.
    expect(headWords(conductorHead(fixtureMembers(), null))).toEqual(["3 AT WORK", "1 ASK"]);
    expect(headWords({ atWork: 0, ask: 0, launches: null })).toEqual([]);
  });
});

describe("PHILO-14 C4 the Conductor window", () => {
  it("lists every live member as a row with a plain pill; the head says 1 needs you · 3 working · 3 OF 3", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    expect(pillOf("Shard the reconciliation job")).toBe("Working");
    expect(pillOf("scratch")).toBe("Working");
    expect(pillOf("Add the ledger freeze flag")).toBe("PR #412 open");
    expect(pillOf("Write the cutover checklist")).toBe("PR #413 merged · item closed · session stopped");
    // Betterment AG8: Claude Code can run and Codex is not wanted here:
    // nothing is missing, so no "On this Mac".
    expect(screen.queryByTestId("conductor-coders")).toBeNull();
    const head = screen.getByTestId("conductor-head").textContent ?? "";
    // Betterment AG8: the fact counts only what is there; the strip keeps
    // the limit when he is at it.
    expect(screen.getByTestId("conductor-head").querySelector(".kit-disp")?.textContent).toBe("1 needs you · 3 working");
    expect(head).not.toContain("1 ASK");
    expect(head).toContain("3 OF 3");
    expect(head).not.toMatch(/\b0 /);
    expect(document.body.textContent).not.toMatch(/personas?/i);
  });

  it("keeps an asking helper's Answer row nested under a working parent", async () => {
    const parent = {
      ...FLIGHT_RECON,
      origin_ref: "action:ai-parent",
      id: "ai-parent",
      title: "Build the parent result",
      launch_id: "l-parent",
      session_key: "codex:p1",
      state: "working",
    };
    const helper = {
      ...FLIGHT_RUNBOOK,
      origin_ref: "action:ai-helper",
      id: "ai-helper",
      title: "Review the parent result",
      agent: "claude",
      launch_id: "l-helper",
      session_key: "claude:h1",
      state: "waiting",
      helper_of: "l-parent",
    };
    sessionsReply = () => ({
      sessions: [
        { session: { agent: "codex", session_id: "p1", state: "working", question: "" }, flight: parent },
        { session: { agent: "claude", session_id: "h1", state: "waiting", question: "Is the parent result ready?", hook_event_name: "Notification" }, flight: helper },
      ],
      flights: [parent, helper],
      history: [],
      launches: { live: 2, cap: 3 },
    });

    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Build the parent result" });
    const helperRow = document.querySelector("[data-object-id='launch:l-helper']") as HTMLElement;
    expect(helperRow).toBeTruthy();
    expect(helperRow.closest("[data-testid='conductor-helpers']")).toBeTruthy();
    expect(within(helperRow).getByRole("button", { name: "Answer" })).toBeTruthy();
  });

  it("Open on a live agent opens its lane; a plain session its window; a ready agent's Get Info is in the foot", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Shard the reconciliation job" });
    fireEvent.click(within(rowOf("Shard the reconciliation job")).getByRole("button", { name: "Open" }));
    expect(shell.lanes).toEqual([["l-recon"]]);
    fireEvent.click(within(rowOf("scratch")).getByRole("button", { name: "Open" }));
    expect(shell.sessions).toEqual([["claude:solo"]]);
    fireEvent.click(icon("Shard the reconciliation job"));
    fireEvent.click(screen.getByRole("button", { name: "Get Info" }));
    expect(useConductor.getState().infos.map((m) => m.ref)).toEqual(["launch:l-recon"]);
  });

  it("the asking agent has Answer (the ask well); a working one has none; Stop is two presses", async () => {
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByRole("button", { name: "Write the rollback runbook" }));
    // The ask plate carries the ONE primary of the window.
    expect(screen.getByRole("button", { name: "Answer" }).className).toContain("btn--primary");
    expect(document.querySelectorAll(".conductor-window .btn--primary")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Answer" }));
    expect(shell.lanes).toEqual([["l-runbook", { sessionKey: "claude:c1", answer: true }]]);
    fireEvent.click(screen.getByTestId("conductor-stop"));
    expect(screen.getByTestId("conductor-stop-confirm").textContent).toContain("ends the agent's session");
    // The confirmation REPLACES the foot's verbs: only Back and the confirm.
    const foot = document.querySelector(".cw-footer") as HTMLElement;
    expect(within(foot).queryByRole("button", { name: "Get Info" })).toBeNull();
    expect(within(foot).getByRole("button", { name: "Back" })).toBeTruthy();
    fireEvent.click(icon("Shard the reconciliation job"));
    expect(within(foot).queryByRole("button", { name: "Answer" })).toBeNull();
    expect(screen.getByTestId("conductor-stop")).toBeTruthy();
    // A stale launch shows its receipt and opens its lane; no Stop.
    fireEvent.click(icon("Write the cutover checklist"));
    expect(screen.getByTestId("conductor-receipt").textContent).toBe("PR #413 MERGED · ITEM CLOSED · SESSION STOPPED");
    expect(screen.queryByTestId("conductor-stop")).toBeNull();
  });

  it("Stop is bound to the agent pressed: confirm Stop on A, open B before A's read resolves; the kill names A (Astra r1 P1)", async () => {
    const { useLane, __resetLane } = await import("../../lane/laneStore");
    __resetLane();
    let releaseA: (body: unknown) => void = () => undefined;
    const base = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url.startsWith("/api/agent/launches/l-runbook/lane")) return new Promise((resolve) => { releaseA = resolve; });
      if (url.startsWith("/api/agent/launches/l-recon/lane"))
        return { launch: { launch_id: "l-recon", session_key: "codex:x1" }, control: { mode: "yolo", armed: true, direct: true } };
      return base(url, init);
    });
    apiRequest.mockImplementation(async () => ({ ok: true, status: 200, json: async () => ({ status: "killed" }) }));
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByRole("button", { name: "Write the rollback runbook" }));
    fireEvent.click(screen.getByTestId("conductor-stop"));
    fireEvent.click(screen.getByTestId("conductor-stop-confirm"));
    // B opens (its lane is the open one) while A's read is out.
    await act(async () => {
      useLane.getState().open("l-recon");
      await useLane.getState().load();
    });
    expect(laneSessionKeyOf(useLane.getState().lane)).toBe("codex:x1");
    await act(async () => {
      releaseA({ launch: { launch_id: "l-runbook", session_key: "claude:c1" }, control: { mode: "yolo", armed: true, direct: true } });
    });
    await waitFor(() => expect(apiRequest).toHaveBeenCalled());
    const kills = apiRequest.mock.calls.map(([url]) => String(url)).filter((url) => url.endsWith("/kill"));
    expect(kills).toEqual(["/api/coders/claude%3Ac1/kill"]);
    // The receipt lands on A (pressed), never on B's lane.
    await waitFor(() => expect(useConductor.getState().stops["launch:l-runbook"]?.word).toBe("STOPPED"));
    expect(useLane.getState().receipt).toBeNull();
    // Rendered: A (still selected) wears STOPPED · BY YOU; B wears none.
    expect((await screen.findByTestId("conductor-stop-receipt")).textContent).toBe("STOPPED · BY YOU");
    fireEvent.click(icon("Shard the reconciliation job"));
    expect(screen.queryByTestId("conductor-stop-receipt")).toBeNull();
    fireEvent.click(icon("Write the rollback runbook"));
    expect(screen.getByTestId("conductor-stop-receipt").textContent).toBe("STOPPED · BY YOU");
  });

  it("the asking agent comes first, then the working ones, and the stopped ones", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    const names = [...document.querySelectorAll(".conductor-window [data-object-id]")].map((el) => el.getAttribute("data-object-id"));
    expect(names[0]).toBe("launch:l-runbook");
    expect(names).not.toContain("agent:claude");
    // The ended launches close the list, folded (in the hub's history order).
    expect(names.slice(-2)).toEqual(["launch:l-old", "launch:l-done"]);
  });

  it("a hooks install the hub refuses is named in the Get Info that pressed it, with Retry (Astra r1 P2)", async () => {
    const missing = { ...DETECT, agents: [{ ...DETECT.agents[0], hooks: "missing" }, DETECT.agents[1]] };
    detectReply = () => missing;
    await useConductor.getState().readDetect();
    const base = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url === "/api/onboarding/agents/use") throw new TypeError("Failed to fetch");
      return base(url, init);
    });
    const [claude] = conductorMembers({ detect: missing.agents as never, sessions: [], flights: [], launchedAt: {}, now: NOW });
    render(<ConductorInfoWindow member={claude} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Connect Claude Code" }));
    });
    const failed = await screen.findByTestId("conductor-install-failed");
    expect(failed.textContent).toContain("NOT CONNECTED · HUB OFFLINE");
    apiFetch.mockImplementation(base);
    detectReply = () => DETECT;
    await act(async () => {
      fireEvent.click(within(failed).getByRole("button", { name: "Retry" }));
    });
    await waitFor(() => expect(screen.queryByTestId("conductor-install-failed")).toBeNull());
  });

  it("an agent not installed reads NOT INSTALLED with Copy install; missing hooks offer Install hooks", async () => {
    const missing = { ...DETECT, agents: [{ ...DETECT.agents[0], hooks: "missing" }, DETECT.agents[1]] };
    detectReply = () => missing;
    render(<ConductorWindow />);
    // Betterment AG8: "On this Mac" lists only what is missing: Claude Code
    // is not connected; Codex (not installed) is not his agent here.
    await screen.findByRole("button", { name: "Claude Code" });
    expect(screen.queryByRole("button", { name: "Codex" })).toBeNull();
    expect(pillOf("Claude Code")).toBe("Not connected");
    detectReply = () => DETECT;
    await act(async () => {
      fireEvent.click(within(rowOf("Claude Code")).getByRole("button", { name: "Connect Claude Code" }));
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/onboarding/agents/use", { method: "POST", json: { agent: "claude" } });
    await waitFor(() => expect(screen.queryByRole("button", { name: "Connect Claude Code" })).toBeNull());
  });

  it("PHILO-15 B34/B35: every ready agent without hooks has its own Install hooks; a success has a receipt", async () => {
    const both = {
      ...DETECT,
      agents: [
        { ...DETECT.agents[0], hooks: "missing" },
        { ...DETECT.agents[0], id: "codex", label: "Codex", path: "/bin/codex", hooks: "missing" },
      ],
    };
    detectReply = () => both;
    // No coder asks: the first fix is the window's one primary.
    sessionsReply = () => ({ sessions: [], flights: [], history: [], launches: { live: 0, cap: 3 } });
    render(<ConductorWindow />);
    // Nothing selected: one verb per agent (it was hidden until a selection).
    const claude = await screen.findByRole("button", { name: "Connect Claude Code" });
    expect(screen.getByRole("button", { name: "Connect Codex" })).toBeTruthy();
    // Astra r1 (#1084): one primary per face; the next Install hooks is secondary.
    expect(claude.className).toContain("btn--primary");
    expect(screen.getByRole("button", { name: "Connect Codex" }).className).toContain("btn--secondary");
    detectReply = () => ({ ...both, agents: [{ ...both.agents[0], hooks: "installed" }, both.agents[1]] });
    await act(async () => {
      fireEvent.click(claude);
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/onboarding/agents/use", { method: "POST", json: { agent: "claude" } });
    const done = await screen.findByTestId("conductor-install-done");
    expect(done.textContent).toMatch(/^CONNECTED · CLAUDE CODE · \d\d:\d\d$/);
    await waitFor(() => expect(screen.queryByRole("button", { name: "Connect Claude Code" })).toBeNull());
    expect(screen.getByRole("button", { name: "Connect Codex" })).toBeTruthy();
  });

  // PHILO-17 U32 (walk D 8): "3 ready · 3 HARNESSES" beside NO HOOKS · SIGN-IN UNKNOWN.
  it("ready counts only coders that can run; the strip says CODERS; hooks are said in one line", async () => {
    const claude = DETECT.agents[0];
    const rows = [
      { ...claude },
      { ...claude, id: "codex", label: "Codex", hooks: "missing" },
      // The owner's Claude Code: the Keychain sign-in is not read; it does not block.
      { ...claude, id: "pi", label: "pi", signed_in: "unknown" },
    ] as never[];
    expect(rows.map((r) => canRun(r))).toEqual([true, false, true]);
    expect(canRun({ ...claude, signed_in: "no" } as never)).toBe(false);
    expect(readyMember(rows[2]).facts.more?.find((f) => f.key === "signin")?.value).toBe("NOT CHECKED");
    expect(headFact({ atWork: 0, ask: 0 }, rows.map((r) => readyMember(r)))).toBe("2 ready");
    expect(headFact({ atWork: 0, ask: 0 }, rows.slice(1, 2).map((r) => readyMember(r)))).toBe("No agent ready");
    expect(headFact({ atWork: 0, ask: 0 }, [])).toBe("No agent");

    sessionsReply = () => ({ sessions: [], flights: [], history: [], launches: { live: 0, cap: 3 } });
    detectReply = () => ({ ...DETECT, agents: rows });
    render(<ConductorWindow />);
    const head = await screen.findByTestId("conductor-head");
    await waitFor(() => expect(head.textContent).toContain("2 ready"));
    expect(head.textContent).not.toMatch(/harness/i);
    // Nothing selected, Codex lacks hooks: Connect with its one line.
    expect(screen.getByRole("button", { name: "Connect Codex" })).toBeTruthy();
    expect(screen.getByTestId("conductor-hooks-line").textContent).toBe(HOOKS_LINE);
    // Betterment AG8: "On this Mac" lists only what is missing: Codex.
    expect(screen.queryByRole("button", { name: "Claude Code" })).toBeNull();
  });

  it("a failed sessions read is NOT READ with Retry, never an empty drawer", async () => {
    sessionsReply = () => new Error("hub down");
    render(<ConductorWindow />);
    const notRead = await screen.findByText(/SESSIONS ·/);
    expect(notRead.textContent).toContain("NOT READ");
    expect(screen.queryByText("No agent found")).toBeNull();
    expect(screen.queryByText(/No sessions/i)).toBeNull();
    // No live agent is claimed gone.
    expect(screen.queryByTestId("conductor-empty")).toBeNull();
    sessionsReply = () => SESSIONS;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    expect(screen.queryByTestId("conductor-not-read")).toBeNull();
  });

  it("re-reads on a coder frame: WORKING becomes ASKS; a cleaned-up session leaves the live set", async () => {
    const working = { ...SESSIONS, sessions: [{ ...SESSIONS.sessions[0], session: { ...SESSIONS.sessions[0].session, question: "" },
      flight: { ...FLIGHT_RUNBOOK, state: "working" } }, ...SESSIONS.sessions.slice(1)],
    flights: [{ ...FLIGHT_RUNBOOK, state: "working" }, ...SESSIONS.flights.slice(1)] };
    sessionsReply = () => working;
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    expect(pillOf("Write the rollback runbook")).toBe("Working");
    sessionsReply = () => SESSIONS;
    act(() => {
      for (const h of bus.handlers.get("intel_status") ?? []) h({ type: "intel_status", data: { state: "ready", scope: "coder" } });
    });
    await waitFor(() => expect(rowOf("Write the rollback runbook").querySelector(".cw-ask-label")?.textContent).toBe("Asks you"));
  });

  it("a ready agent's Get Info: version, hooks, sign-in", async () => {
    const claude = fixtureMembers().find((m) => m.id === "agent:claude")!;
    render(<ConductorInfoWindow member={claude} />);
    const info = await screen.findByTestId("conductor-info");
    expect(within(info).getByText("Version").nextSibling?.textContent).toBe("2.1.0");
    expect(within(info).getByText("Hooks").nextSibling?.textContent).toBe("IN");
    expect(within(info).getByText("Sign-in").nextSibling?.textContent).toBe("SIGNED IN");
  });

  it("a launched agent's Get Info: the item, Project, branch, launched, control from the lane route", async () => {
    const runbook = fixtureMembers().find((m) => m.ref === "launch:l-runbook")!;
    render(<ConductorInfoWindow member={runbook} />);
    const info = await screen.findByTestId("conductor-info");
    await waitFor(() => expect(within(info).getByText("Control").nextSibling?.textContent).toBe("NORMAL"));
    expect(within(info).getByText("Branch").nextSibling?.textContent).toBe("hs/write-the-rollback-runbook");
    expect(within(info).getByText("From").nextSibling?.textContent).toBe("Write the rollback runbook");
    expect(within(info).getByText("Where").nextSibling?.textContent).toBe("Payments ledger cutover");
    expect(within(info).getByText("Launched").nextSibling?.textContent).toMatch(/^(TODAY|[A-Z]{3} \d+) \d\d:\d\d$/);
    expect(screen.getByRole("button", { name: "Answer" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open" })).toBeTruthy();
  });
});

// PHILO-17 THE REFIT: the ask is a raised plate with a title bar, the
// question in full and ONE verb (Answer).
describe("PHILO-17 the Conductor reads like Today", () => {
  it("the ask is a plate: ASKS YOU, ASKED <age>, the agent, the question, Answer", async () => {
    render(<ConductorWindow />);
    const asks = await screen.findByTestId("conductor-asks");
    const rows = within(asks).getAllByTestId("conductor-ask-row");
    expect(rows).toHaveLength(1);
    expect(rows[0].querySelector(".cw-ask-label")?.textContent).toBe("Asks you");
    expect(rows[0].querySelector(".cw-ask-age")?.textContent).toMatch(/^Ask/);
    expect(rows[0].textContent).toContain("Claude Code");
    expect(rows[0].textContent).toContain(QUESTION.slice(0, 20));
    // No wait id in this read: Answer opens the agent's ask well (Betterment AG2 fallback).
    expect(within(rows[0]).getAllByRole("button").map((b) => b.textContent)).toEqual(["Write the rollback runbook", "Answer", "Open"]);
    expect(document.querySelectorAll(".kit-disp")).toHaveLength(1);
  });

  it("Answer on the plate opens the ask well in one press", async () => {
    render(<ConductorWindow />);
    const row = await screen.findByTestId("conductor-ask-row");
    fireEvent.click(within(row).getByRole("button", { name: "Answer" }));
    expect(shell.lanes).toEqual([["l-runbook", { sessionKey: "claude:c1", answer: true }]]);
  });

  it("a held call the hub shows whole is approved on the plate in one press", async () => {
    const base = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url.startsWith("/api/agent/launches/l-runbook/lane"))
        return { launch: { launch_id: "l-runbook" }, gated: [{ id: "toolu_psql", tool: "Bash", args_shown: "psql -h staging-ledger", args_cut: false, state: "held", hold_reason: "OUTSIDE THE WORKTREE" }] };
      return base(url, init);
    });
    render(<ConductorWindow />);
    const call = await screen.findByTestId("conductor-held-call");
    expect(call.textContent).toContain("psql -h staging-ledger");
    const plate = screen.getByTestId("conductor-ask-row");
    expect(plate.querySelector(".cw-ask-label")?.textContent).toBe("Wants to run");
    expect(within(plate).getByRole("button", { name: "Allow" }).className).toContain("btn--primary");
    expect(within(plate).getByRole("button", { name: "Deny" }).className).toContain("btn--secondary");
    await act(async () => {
      fireEvent.click(within(plate).getByRole("button", { name: "Allow" }));
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/gate/proposals/toolu_psql/decide", expect.objectContaining({
      method: "POST", json: expect.objectContaining({ decision: "approved" }),
    }));
  });

  it("names a refused approval, blocks repeated presses and retries the same call", async () => {
    const base = apiFetch.getMockImplementation()!;
    let release!: () => void;
    let accepted = false;
    let attempts = 0;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url.endsWith("/decide")) {
        attempts++;
        if (attempts === 1) {
          await new Promise<void>((resolve) => { release = resolve; });
          throw new ApiError(403, "Approval refused", { error: "Approval refused" });
        }
        accepted = true;
        return { state: "approved" };
      }
      if (url.startsWith("/api/agent/launches/l-runbook/lane")) return { gated: accepted ? [] : [{ id: "call-refused", tool: "Bash", args_shown: "git status", args_cut: false, state: "held" }] };
      if (url.startsWith("/api/gate/proposals?")) return { proposals: [] };
      return base(url, init);
    });
    render(<ConductorWindow />);
    const approve = await screen.findByRole("button", { name: "Allow" });
    fireEvent.click(approve);
    fireEvent.click(approve);
    expect(approve).toBeDisabled();
    expect(attempts).toBe(1);
    await act(async () => { release(); });
    expect(await screen.findByRole("alert")).toHaveTextContent("Allow failed · Approval refused");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    const posts = apiFetch.mock.calls.filter(([url]) => String(url).endsWith("/decide"));
    expect(posts).toHaveLength(2);
    expect(posts[1]).toEqual(posts[0]);
    expect(screen.queryByRole("button", { name: "Allow" })).toBeNull();
  });

  it.each([false, true])("retries reads only after a settled approval with unavailable truth, race=%s", async (race) => {
    const base = apiFetch.getMockImplementation()!;
    let settled = false;
    let unavailable = true;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url.endsWith("/decide")) {
        settled = true;
        if (race) throw new ApiError(409, "already_decided", { error: "already_decided", state: "denied" });
        return { state: "approved" };
      }
      if (url.startsWith("/api/agent/launches/l-runbook/lane")) {
        if (settled && unavailable) throw new Error("Lane read unavailable");
        return { gated: settled ? [] : [{ id: "call-read", tool: "Bash", args_shown: "git status", args_cut: false, state: "held" }] };
      }
      if (url.startsWith("/api/gate/proposals?")) {
        if (unavailable) throw new Error("Gate read unavailable");
        return { proposals: [] };
      }
      return base(url, init);
    });
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByRole("button", { name: "Allow" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Decision saved · Gate read failed · Retry · Gate read unavailable");
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled());
    expect(screen.queryByRole("button", { name: "Allow" })).toBeNull();
    unavailable = false;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(apiFetch.mock.calls.filter(([url]) => String(url).endsWith("/decide"))).toHaveLength(1);
    expect(screen.queryByTestId("conductor-held-call")).toBeNull();
  });

  it("names a failed held-call read and retries that read", async () => {
    const base = apiFetch.getMockImplementation()!;
    let unavailable = true;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url.startsWith("/api/agent/launches/l-runbook/lane")) {
        if (unavailable) throw new Error("Call unavailable");
        return { gated: [{ id: "call-recovered", tool: "Bash", args_shown: "git status", args_cut: false, state: "held" }] };
      }
      return base(url, init);
    });
    render(<ConductorWindow />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Call read failed · Calls unchanged · Retry · Call unavailable");
    unavailable = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("button", { name: "Allow" })).toBeEnabled();
    expect(apiFetch.mock.calls.filter(([url]) => String(url).endsWith("/decide"))).toHaveLength(0);
  });

  it("a cut call is never allowed on the plate: Terminal opens the lane on its screen", async () => {
    const base = apiFetch.getMockImplementation()!;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url.startsWith("/api/agent/launches/l-runbook/lane"))
        return { launch: { launch_id: "l-runbook" }, gated: [{ id: "toolu_cut", tool: "Bash", args_shown: "rm -rf", args_cut: true, state: "held" }] };
      return base(url, init);
    });
    render(<ConductorWindow />);
    await screen.findByTestId("conductor-held-call");
    expect(screen.queryByRole("button", { name: "Allow" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Terminal" }));
    expect(shell.lanes).toEqual([["l-runbook", { sessionKey: "claude:c1", raw: true }]]);
  });

  it("On this Mac shows only when something is missing; stopped launches fold", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    expect(screen.queryByTestId("conductor-coders")).toBeNull();
    expect(screen.getByText("Stopped today")).toBeTruthy();
  });
});

// PHILO-17 (mainreds3): a seat remembered from another view (the workspace
// keeps `min`) must not swallow a deliberate open: the Conductor opens on
// glass, in front of the other windows.
describe("opening the Conductor shows it", () => {
  const front = () => {
    const d = useDesk.getState().panelDepth;
    return Object.keys(d).sort((a, b) => d[a] - d[b]).at(-1);
  };

  it("a fresh open clears a remembered seat and fronts the window", async () => {
    __resetConductor();
    useDesk.setState({ panelMin: ["conductor"], panelDepth: { conductor: 1, "surface-meetings": 2 } });
    useConductor.getState().openWindow();
    expect(useConductor.getState().open).toBe(true);
    await waitFor(() => expect(useDesk.getState().panelMin).not.toContain("conductor"));
    expect(front()).toBe("conductor");
  });

  it("an open Conductor that is seated comes back in front", async () => {
    __resetConductor();
    useDesk.setState({ panelMin: [], panelDepth: { "surface-meetings": 1 } });
    useConductor.getState().openWindow();
    // The first open's restore has landed before the seat is set.
    await waitFor(() => expect(front()).toBe("conductor"));
    useDesk.setState({ panelMin: ["conductor"], panelDepth: { conductor: 1, "surface-meetings": 2 } });
    useConductor.getState().openWindow();
    await waitFor(() => expect(useDesk.getState().panelMin).not.toContain("conductor"));
    expect(front()).toBe("conductor");
  });

  it("a hub open (showFromHub) keeps the seat and does not raise", async () => {
    __resetConductor();
    useDesk.setState({ panelMin: ["conductor"], panelDepth: { conductor: 1, "surface-meetings": 2 } });
    useConductor.getState().showFromHub();
    await new Promise((r) => setTimeout(r, 0));
    expect(useConductor.getState().open).toBe(true);
    expect(useDesk.getState().panelMin).toContain("conductor");
    expect(front()).toBe("surface-meetings");
  });
});
