// The Conductor app on the hub's OWN answers (the test diet, 2026-10-11).
// The answers under ./wire were captured on a real hub seeded by the
// Conductor glass's own seed (tests/e2e/conductor_rig.py: three launches,
// Claude Code asking, Codex working, PR #412 on the flag) and are fenced
// against the hub's shape on every run by
// tests/integration/test_desk_agents_wire.py. Only apiFetch is a double; the
// window, its store and the members reducer are the real ones.
import { fireEvent, render, screen, within } from "@testing-library/react";
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
const shell = vi.hoisted(() => ({ lanes: [] as unknown[][], sessions: [] as unknown[][] }));
vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openAgentLane: (...args: unknown[]) => shell.lanes.push(args),
  openCoderSession: (...args: unknown[]) => shell.sessions.push(args),
}));

import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { useAgentFlights } from "../agentFlights";
import { ConductorWindow } from "../conductor/ConductorWindow";
import { __resetConductor } from "../conductor/store";

const SESSIONS = hubWire("coders-sessions.c4");
const DETECT = hubWire("onboarding-agents.isolated");
const LANE = hubWire("lane.c4-runbook");

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(SESSIONS.captured_at));
  localStorage.clear();
  shell.lanes = [];
  shell.sessions = [];
  api.fetch.mockReset();
  api.fetch.mockImplementation(async (url: string) => {
    if (String(url).startsWith("/api/coders/sessions")) return SESSIONS.wire;
    if (url === "/api/onboarding/agents") return DETECT.wire;
    if (String(url).startsWith("/api/agent/launches/launch_c4_runbook/lane")) return LANE.wire;
    throw new Error(`no captured hub answer for ${url}`);
  });
  __resetConductor();
  useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  useDesk.setState({ items: { ...EMPTY_ITEMS }, zoneViewPrefs: {}, panelRects: {}, panelOrder: [], panelMin: [] });
});
afterEach(() => {
  vi.useRealTimers();
});

const member = (id: string) => document.querySelector<HTMLElement>(`[data-object-id='${id}']`);

describe("the Conductor on the C4 seed", () => {
  /** replaces: tests/e2e/test_philo14_c4_conductor_glass.py::test_the_conductor_drawer_at_1440_and_393
   *  PHILO-17 refit (conductor): the drawer reads like Today. The ask is a
   *  raised plate first; the coders at work are quiet rows; the coders on
   *  this Mac follow. */
  it("lists the ready agents and the three launches with their lamps, asking first; the head says 2 at work, 1 ASK", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    for (const name of ["Write the rollback runbook", "Shard the reconciliation job", "Add the ledger freeze flag"]) {
      expect(screen.getByRole("button", { name }), name).toBeTruthy();
    }
    // The ready agents: whatever the hub's own detect read served.
    await screen.findByRole("button", { name: "Codex" });
    expect(document.querySelectorAll("[data-object-id='agent:claude']")).toHaveLength(1);
    expect(document.querySelectorAll("[data-object-id='agent:codex']")).toHaveLength(1);
    const lamps: Record<string, string> = {
      "launch:launch_c4_runbook": "Asks you",
      "launch:launch_c4_recon": "Working",
      "launch:launch_c4_flag": "PR #412 open",
    };
    for (const [id, lamp] of Object.entries(lamps)) {
      const el = member(id);
      expect(el, id).toBeTruthy();
      expect(el!.textContent ?? "").toContain(lamp);
    }
    const head = screen.getByTestId("conductor-head");
    expect(head.querySelector(".kit-disp")?.textContent).toBe("2 at work");
    expect(head.textContent).toContain("1 ASK");
    // The cap is the hub's count (no tmux session runs): no `N OF M`.
    expect(head.textContent).not.toContain(" OF ");
    expect(head.textContent).not.toContain("NOT READ");
    expect((head.textContent ?? "").toUpperCase()).not.toContain("HARNESS");
    // Asking first.
    expect(document.querySelector("[data-object-id]")?.getAttribute("data-object-id")).toBe("launch:launch_c4_runbook");
  });

  /** replaces: tests/e2e/test_philo14_c4_conductor_glass.py::test_the_conductor_drawer_at_1440_and_393 (Open, Stop confirm)
   *  PHILO-17 refit: Answer stays on the ask plate, Open on the row; the foot
   *  keeps the quiet verbs (Get Info, Stop). */
  /** The desk sweep's flake (conductor at 393: still … moved 220 px): the
   *  detect read answered first and drew the ready rows; the late sessions
   *  read then put Needs you and At work above them. The window now reads
   *  until the sessions answer, and draws its rows once, in their places. */
  it("draws no agent row until the sessions read answers, then draws the asks above the ready agents", async () => {
    let answerSessions: (value: unknown) => void = () => undefined;
    const sessions = new Promise((resolve) => { answerSessions = resolve; });
    api.fetch.mockImplementation(async (url: string) => {
      if (String(url).startsWith("/api/coders/sessions")) return sessions;
      if (url === "/api/onboarding/agents") return DETECT.wire;
      throw new Error(`no captured hub answer for ${url}`);
    });
    render(<ConductorWindow />);
    await vi.waitFor(() => expect(api.fetch).toHaveBeenCalledWith("/api/onboarding/agents"));
    await Promise.resolve();
    await Promise.resolve();
    expect(document.querySelector("[data-object-id='agent:codex']")).toBeNull();
    expect(screen.getByTestId("conductor-window").querySelector("[aria-busy='true']")).toBeTruthy();
    answerSessions(SESSIONS.wire);
    await screen.findByRole("button", { name: "Write the rollback runbook" });
    const ask = member("launch:launch_c4_runbook");
    expect(ask).toBeTruthy();
    expect(screen.getByTestId("conductor-window").querySelector("[aria-busy='true']")).toBeNull();
    const codex = member("agent:codex");
    if (codex) expect(ask!.compareDocumentPosition(codex) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("the asking agent's verbs are Get Info, Stop, Answer, Open; Stop confirms in place; Open opens its lane", async () => {
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByRole("button", { name: "Write the rollback runbook" }));
    const plate = member("launch:launch_c4_runbook")!;
    expect(within(plate).getByRole("button", { name: "Answer" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Get Info" })).toBeTruthy();
    expect(screen.getByTestId("conductor-stop")).toBeTruthy();
    fireEvent.click(screen.getByTestId("conductor-stop"));
    expect(screen.getByTestId("conductor-stop-confirm")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Stop · sure? (ends the agent's session)" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Get Info" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByRole("button", { name: "Get Info" })).toBeTruthy();
    fireEvent.click(within(member("launch:launch_c4_recon")!).getByRole("button", { name: "Open" }));
    expect(shell.lanes.at(-1)?.[0]).toBe("launch_c4_recon");
  });

  /** replaces: tests/e2e/test_philo14_a0c_list_sprites_glass.py::test_the_list_species_wear_the_32px_set (the Conductor's list)
   *  PHILO-17 refit: one row species (no Icons | List); each row wears the
   *  sprite of ITS agent. */
  it("every row wears the sprite of ITS agent", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: "Shard the reconciliation job" });
    const sprite = (id: string) => member(id)!.querySelector("img")?.getAttribute("src") ?? "";
    expect(sprite("launch:launch_c4_recon")).toMatch(/\/desk\/sprites\/agent-codex(_sel)?\.png$/);
    expect(sprite("launch:launch_c4_runbook")).toMatch(/\/desk\/sprites\/agent-claude-code(_sel)?\.png$/);
    expect(sprite("launch:launch_c4_flag")).toMatch(/\/desk\/sprites\/agent-claude-code(_sel)?\.png$/);
    expect(sprite("agent:codex")).toMatch(/\/desk\/sprites\/agent-codex(_sel)?\.png$/);
    expect(screen.queryByRole("group", { name: "Conductor view" })).toBeNull();
  });
});
