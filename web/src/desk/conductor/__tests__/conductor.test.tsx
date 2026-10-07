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
import { ConductorWindow } from "../ConductorWindow";
import { ConductorInfoWindow } from "../ConductorInfoWindow";
import { closeReceipt, conductorHead, conductorMembers, headWords } from "../members";
import { __resetConductor, useConductor } from "../store";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
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
const FLIGHT_OLD = {
  ...FLIGHT_RUNBOOK, origin_ref: "action:ai-old", id: "ai-old", title: "Write last week's note",
  state: "ended", session_key: "claude:old", launch_id: "l-old", launched_at: ago(60 * 30),
};

const SESSIONS = {
  sessions: [
    { session: { agent: "claude", session_id: "c1", state: "waiting", question: QUESTION, hook_event_name: "Notification",
      repo_root: "/h/dev/payments-ledger-runbook", updated_at: ago(2) }, flight: FLIGHT_RUNBOOK },
    { session: { agent: "codex", session_id: "x1", state: "working", repo_root: "/h/dev/payments-ledger-recon", updated_at: ago(1) }, flight: FLIGHT_RECON },
    { session: { agent: "claude", session_id: "solo", state: "working", repo_root: "/h/dev/scratch", updated_at: ago(5) } },
  ],
  flights: [FLIGHT_RUNBOOK, FLIGHT_RECON, FLIGHT_FLAG, FLIGHT_DONE, FLIGHT_OLD],
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
  apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
    const body = route(url, init);
    if (body instanceof Error) throw body;
    return body;
  });
  __resetConductor();
  useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  useDesk.setState({ items: { ...EMPTY_ITEMS }, zoneViewPrefs: {}, panelRects: {}, panelOrder: [], panelMin: [] });
});

function fixtureMembers() {
  return conductorMembers({
    detect: DETECT.agents as never,
    sessions: SESSIONS.sessions.map(fromWireSessionRow),
    flights: SESSIONS.flights.map(fromWireFlight),
    launchedAt: Object.fromEntries(SESSIONS.flights.map((f) => [f.launch_id, f.launched_at])),
    now: NOW,
  });
}

const icon = (name: RegExp) => screen.getByRole("button", { name });

describe("PHILO-14 C4 the Conductor members", () => {
  it("ready, then live, then stale: once each, with the screen's names and lamps", () => {
    const members = fixtureMembers();
    expect(members.map((m) => [m.role, m.name, m.lamp?.label ?? null, m.ref])).toEqual([
      ["ready", "Claude Code", null, "agent:claude"],
      ["ready", "Codex", "NOT INSTALLED", "agent:codex"],
      ["live", "Claude Code: rollback runbook", "ASKS", "launch:l-runbook"],
      ["live", "Codex: reconciliation job", "WORKS", "launch:l-recon"],
      // A session no launch holds opens its session window.
      ["live", "Claude Code: scratch", "WORKS", "coder:claude:solo"],
      // In flight with no live session: its PR is the fact.
      ["live", "Claude Code: ledger freeze flag", "PR #412", "launch:l-flag"],
      // Ended in the last 24 h: stale, its close receipt; the 30 h one is gone.
      ["stale", "Claude Code: cutover checklist", null, "launch:l-done"],
    ]);
    const stale = members.find((m) => m.role === "stale")!;
    expect(stale.receipt).toBe("PR #413 MERGED · ITEM CLOSED · SESSION STOPPED");
    expect(stale.sprite).toMatch(/agent-claude-code_stale\.png$/);
    expect(members.find((m) => m.agent === "codex" && m.role === "live")!.sprite).toMatch(/agent-codex\.png$/);
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

  it("the head omits zeros and names the cap only at it", () => {
    const flights = SESSIONS.flights.map(fromWireFlight);
    const head = conductorHead(fixtureMembers(), flights);
    // runbook asks; recon, scratch and the flag's PR are at work; 3 launches in flight.
    expect(head).toEqual({ atWork: 3, ask: 1, launched: 3 });
    expect(headWords(head)).toEqual(["3 AT WORK", "1 ASK", "3 OF 3"]);
    expect(headWords({ atWork: 2, ask: 0, launched: 2 })).toEqual(["2 AT WORK"]);
    expect(headWords({ atWork: 0, ask: 0, launched: 0 })).toEqual([]);
  });
});

describe("PHILO-14 C4 the Conductor window", () => {
  it("lists every member as an icon; the head says 3 AT WORK · 1 ASK · 3 OF 3", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: /^Claude Code: rollback runbook, AGENT, ASKS/ });
    expect(icon(/^Codex: reconciliation job, AGENT, WORKS/)).toBeTruthy();
    expect(icon(/^Claude Code: scratch, AGENT, WORKS/)).toBeTruthy();
    expect(icon(/^Claude Code: ledger freeze flag, AGENT, PR #412/)).toBeTruthy();
    expect(icon(/^Claude Code: cutover checklist, AGENT, PR #413 MERGED/)).toBeTruthy();
    await screen.findByRole("button", { name: /^Codex, AGENT, NOT INSTALLED/ });
    const head = screen.getByTestId("conductor-head").textContent ?? "";
    expect(head).toContain("3 AT WORK");
    expect(head).toContain("1 ASK");
    expect(head).toContain("3 OF 3");
    expect(head).not.toMatch(/\b0 /);
    expect(document.body.textContent).not.toMatch(/personas?/i);
  });

  it("Open on a live agent opens its lane; a plain session its window; a ready agent its Get Info", async () => {
    render(<ConductorWindow />);
    const runbook = await screen.findByRole("button", { name: /^Claude Code: rollback runbook/ });
    fireEvent.keyDown(runbook, { key: "Enter" });
    expect(shell.lanes).toEqual([["l-runbook"]]);
    fireEvent.keyDown(icon(/^Claude Code: scratch/), { key: "Enter" });
    expect(shell.sessions).toEqual([["claude:solo"]]);
    fireEvent.keyDown(await screen.findByRole("button", { name: /^Claude Code, AGENT$/ }), { key: "Enter" });
    expect(useConductor.getState().infos.map((m) => m.ref)).toEqual(["agent:claude"]);
  });

  it("the asking agent has Answer (the ask well); a working one has none; Stop is two presses", async () => {
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByRole("button", { name: /^Claude Code: rollback runbook/ }));
    fireEvent.click(screen.getByRole("button", { name: "Answer" }));
    expect(shell.lanes).toEqual([["l-runbook", { sessionKey: "claude:c1", answer: true }]]);
    fireEvent.click(screen.getByTestId("conductor-stop"));
    expect(screen.getByTestId("conductor-stop-confirm").textContent).toContain("ends the agent's session");
    fireEvent.click(icon(/^Codex: reconciliation job/));
    expect(screen.queryByRole("button", { name: "Answer" })).toBeNull();
    expect(screen.getByTestId("conductor-stop")).toBeTruthy();
    // A stale launch shows its receipt and opens its lane; no Stop.
    fireEvent.click(icon(/^Claude Code: cutover checklist/));
    expect(screen.getByTestId("conductor-receipt").textContent).toBe("PR #413 MERGED · ITEM CLOSED · SESSION STOPPED");
    expect(screen.queryByTestId("conductor-stop")).toBeNull();
  });

  it("an agent not installed reads NOT INSTALLED with Copy install; missing hooks offer Install hooks", async () => {
    const missing = { ...DETECT, agents: [{ ...DETECT.agents[0], hooks: "missing" }, DETECT.agents[1]] };
    detectReply = () => missing;
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByRole("button", { name: /^Codex, AGENT, NOT INSTALLED/ }));
    expect(screen.getByRole("button", { name: "Copy install: Codex" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /^Claude Code, AGENT, NO HOOKS/ }));
    detectReply = () => DETECT;
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Install hooks" }));
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/onboarding/agents/use", { method: "POST", json: { agent: "claude" } });
    await waitFor(() => expect(screen.queryByRole("button", { name: "Install hooks" })).toBeNull());
  });

  it("a failed sessions read is NOT READ with Retry, never an empty drawer", async () => {
    sessionsReply = () => new Error("hub down");
    render(<ConductorWindow />);
    const notRead = await screen.findByText(/SESSIONS ·/);
    expect(notRead.textContent).toContain("NOT READ");
    expect(screen.queryByText("No agent found")).toBeNull();
    expect(screen.queryByText(/No sessions/i)).toBeNull();
    // The ready agents still show; no live agent is claimed gone.
    expect(await screen.findByRole("button", { name: /^Claude Code, AGENT$/ })).toBeTruthy();
    sessionsReply = () => SESSIONS;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByRole("button", { name: /^Claude Code: rollback runbook/ });
    expect(screen.queryByTestId("conductor-not-read")).toBeNull();
  });

  it("re-reads on a coder frame: WORKING becomes ASKS; a cleaned-up session leaves the live set", async () => {
    const working = { ...SESSIONS, sessions: [{ ...SESSIONS.sessions[0], session: { ...SESSIONS.sessions[0].session, question: "" },
      flight: { ...FLIGHT_RUNBOOK, state: "working" } }, ...SESSIONS.sessions.slice(1)],
    flights: [{ ...FLIGHT_RUNBOOK, state: "working" }, ...SESSIONS.flights.slice(1)] };
    sessionsReply = () => working;
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: /^Claude Code: rollback runbook, AGENT, WORKS/ });
    sessionsReply = () => SESSIONS;
    act(() => {
      for (const h of bus.handlers.get("intel_status") ?? []) h({ type: "intel_status", data: { state: "ready", scope: "coder" } });
    });
    await screen.findByRole("button", { name: /^Claude Code: rollback runbook, AGENT, ASKS/ });
  });

  it("a ready agent's Get Info: version, hooks, sign-in", async () => {
    const [claude] = fixtureMembers();
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
