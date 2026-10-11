// The Conductor app on the hub's OWN answers (the test diet, 2026-10-11).
// The answers under ./wire were captured on a real hub seeded by the
// Conductor glass's own seed (tests/e2e/conductor_rig.py: three launches,
// Claude Code asking, Codex working, PR #412 on the flag) and are fenced
// against the hub's shape on every run by
// tests/integration/test_desk_agents_wire.py. Only apiFetch is a double; the
// window, its store and the members reducer are the real ones.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
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
  /** replaces: tests/e2e/test_philo14_c4_conductor_glass.py::test_the_conductor_drawer_at_1440_and_393 */
  it("lists the ready agents and the three launches with their lamps, asking first; the head says 2 at work, 1 ASK", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("button", { name: /^Claude Code: rollback runbook/ });
    for (const name of ["Claude Code: rollback runbook", "Codex: reconciliation job", "Claude Code: ledger freeze flag"]) {
      expect(document.querySelector(`[title='${name}'], [aria-label^='${name}']`), name).toBeTruthy();
    }
    // The ready agents: whatever the hub's own detect read served.
    await screen.findByRole("button", { name: /^Codex, CODER/ });
    expect(document.querySelectorAll("[data-object-id='agent:claude']")).toHaveLength(1);
    expect(document.querySelectorAll("[data-object-id='agent:codex']")).toHaveLength(1);
    const lamps: Record<string, string> = {
      "launch:launch_c4_runbook": "ASKS",
      "launch:launch_c4_recon": "WORKS",
      "launch:launch_c4_flag": "PR #412",
    };
    for (const [id, lamp] of Object.entries(lamps)) {
      const el = member(id);
      expect(el, id).toBeTruthy();
      expect((el!.getAttribute("aria-label") ?? "") + (el!.textContent ?? "")).toContain(lamp);
    }
    const head = screen.getByTestId("conductor-head");
    expect(head.querySelector(".kit-disp")?.textContent).toBe("2 at work");
    expect(head.textContent).toContain("1 ASK");
    // The cap is the hub's count (no tmux session runs): no `N OF M`.
    expect(head.textContent).not.toContain(" OF ");
    expect(head.textContent).not.toContain("NOT READ");
    expect((head.textContent ?? "").toUpperCase()).not.toContain("HARNESS");
    // Asking first in every view.
    expect(document.querySelector("[data-object-id]")?.getAttribute("data-object-id")).toBe("launch:launch_c4_runbook");
  });

  /** replaces: tests/e2e/test_philo14_c4_conductor_glass.py::test_the_conductor_drawer_at_1440_and_393 (Open, Stop confirm) */
  it("the asking agent's verbs are Get Info, Stop, Answer, Open; Stop confirms in place; Open opens its lane", async () => {
    render(<ConductorWindow />);
    fireEvent.click(await screen.findByRole("button", { name: /^Claude Code: rollback runbook/ }));
    for (const verb of ["Get Info", "Answer", "Open"]) expect(screen.getByRole("button", { name: verb })).toBeTruthy();
    expect(screen.getByTestId("conductor-stop")).toBeTruthy();
    fireEvent.click(screen.getByTestId("conductor-stop"));
    expect(screen.getByTestId("conductor-stop-confirm")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Stop · sure? (ends the coder's session)" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Answer" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Open" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(shell.lanes.at(-1)?.[0]).toBe("launch_c4_runbook");
  });

  /** replaces: tests/e2e/test_philo14_a0c_list_sprites_glass.py::test_the_list_species_wear_the_32px_set (the Conductor's list) */
  it("in List view every row wears the 32 px sprite of ITS agent; the icon view keeps the 64", async () => {
    render(<ConductorWindow />);
    const iconImg = (await screen.findByRole("button", { name: /^Codex: reconciliation job/ })).querySelector("img");
    expect(iconImg?.getAttribute("src") ?? "").not.toContain("/desk/sprites/32/");
    fireEvent.click(within(screen.getByRole("group", { name: "Conductor view" })).getByRole("button", { name: "List" }));
    const row = (id: string) => document.querySelector<HTMLElement>(`.object-list-row[data-object-id='${id}']`)!;
    await waitFor(() => expect(document.querySelector(".object-list-row")).toBeTruthy());
    const sprites = [...document.querySelectorAll<HTMLImageElement>(".object-list-open img")].map((img) => img.getAttribute("src") ?? "");
    expect(sprites.length).toBeGreaterThan(0);
    for (const src of sprites) expect(src).toMatch(/\/desk\/sprites\/32\/[a-z-]+(_sel|_stale)?\.png$/);
    expect(row("launch:launch_c4_recon").querySelector(".object-list-open img")?.getAttribute("src")).toMatch(/\/32\/agent-codex(_sel)?\.png$/);
    expect(row("launch:launch_c4_runbook").querySelector(".object-list-open img")?.getAttribute("src")).toMatch(/\/32\/agent-claude-code(_sel)?\.png$/);
    // Shown 1:1: the list cell draws the sprite at 32 (objects.css).
    const css = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "../surface/objects/objects.css"), "utf8");
    expect(css).toMatch(/\.object-list-open img \{[^}]*width: 32px;[^}]*height: 32px;/);
  });
});
