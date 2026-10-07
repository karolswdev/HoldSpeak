/** PHILO-14 C4 — the Conductor drawer: is it open, its Get Info windows,
 *  and its two reads.
 *
 *  - The agents read (`GET /api/onboarding/agents`, K1's `agents_detect`):
 *    the ready agents, their version, hooks and sign-in.
 *  - The flights read (`GET /api/coders/sessions?include_ended=false`, the
 *    one agents read every face shares): the window reads it itself so a
 *    failed read is NOT READ (the shared store keeps its last answer
 *    silently), and hands every good answer to the shared store, so the
 *    screen and the Arrival see it too.
 *
 *  Install hooks is the first-run card's press: `POST
 *  /api/onboarding/agents/use` for the agent, then the agents read again.
 */
import { create } from "zustand";
import { ApiError, apiFetch } from "../../lib/api";
import { fromWireFlight, fromWireSessionRow, useAgentFlights, type AgentFlight } from "../agentFlights";
import type { LaneReceipt } from "../lane/laneStore";
import { AGENTS_PATH, AGENTS_USE_PATH, type AgentId, type AgentsDetect } from "../firstrun/agentsStep";
import type { ConductorMember } from "./members";

export const CONDUCTOR_WINDOW_ID = "conductor";
export const CONDUCTOR_KEY = "open-conductor";
export const FLIGHTS_PATH = "/api/coders/sessions?include_ended=false";

// The workspace keeps a window's place under an id of [A-Za-z0-9:_-] only.
export const conductorInfoId = (ref: string) => `conductor-info:${ref.replace(/[^A-Za-z0-9:_-]/g, "_")}`;

export type ReadState = "idle" | "loading" | "ok" | "failed";

interface ConductorState {
  open: boolean;
  origin: { x: number; y: number } | null;
  infos: ConductorMember[];
  detect: AgentsDetect | null;
  detectState: ReadState;
  /** The failed agents read as a token (`HTTP 500`, `HUB OFFLINE`). */
  detectFailure: string;
  flightsState: ReadState;
  launchedAt: Record<string, string>;
  /** `ended_at` per launch id (history and flights). */
  endedAt: Record<string, string>;
  /** Every launch that ended in the last 24 h (the route's `history`). */
  history: AgentFlight[];
  /** The hub's own launch count against its cap; null = not served. */
  launches: { live: number; cap: number } | null;
  /** Per member ref: the last Stop's receipt (it lands where it was pressed). */
  stops: Record<string, LaneReceipt>;
  /** The agent whose hooks are being installed. */
  installing: AgentId | null;
  /** The last install that the hub refused, as a token, and its agent. */
  installFailure: string;
  installFailedAgent: AgentId | null;
  openWindow(origin?: { x: number; y: number } | null): void;
  closeWindow(): void;
  openInfo(member: ConductorMember): void;
  closeInfo(ref: string): void;
  readDetect(): Promise<void>;
  readFlights(): Promise<void>;
  installHooks(agent: AgentId): Promise<boolean>;
  setStop(ref: string, receipt: LaneReceipt | null): void;
}

const failureToken = (error: unknown) => (error instanceof ApiError ? `HTTP ${error.status}` : "HUB OFFLINE");

export const useConductor = create<ConductorState>((set, get) => ({
  open: false,
  origin: null,
  infos: [],
  detect: null,
  detectState: "idle",
  detectFailure: "",
  flightsState: "idle",
  launchedAt: {},
  endedAt: {},
  history: [],
  launches: null,
  stops: {},
  installing: null,
  installFailure: "",
  installFailedAgent: null,
  setStop(ref, receipt) {
    const next = { ...get().stops };
    if (receipt) next[ref] = receipt;
    else delete next[ref];
    set({ stops: next });
  },
  openWindow(origin = null) {
    if (get().open) {
      // Already open: bring it forward (and back from the Dock).
      void import("../store").then((m) => {
        const desk = m.useDesk.getState();
        if (desk.panelMin.includes(CONDUCTOR_WINDOW_ID)) desk.restorePanel(CONDUCTOR_WINDOW_ID);
        desk.focusPanel(CONDUCTOR_WINDOW_ID);
      });
      return;
    }
    set({ open: true, origin });
  },
  closeWindow() {
    set({ open: false, infos: [] });
  },
  openInfo(member) {
    set({ infos: [...get().infos.filter((i) => i.ref !== member.ref), member] });
  },
  closeInfo(ref) {
    set({ infos: get().infos.filter((i) => i.ref !== ref) });
  },
  async readDetect() {
    set({ detectState: get().detect ? get().detectState : "loading" });
    try {
      const detect = await apiFetch<AgentsDetect>(AGENTS_PATH);
      if (!detect || !Array.isArray(detect.agents)) throw new Error("no agents");
      set({ detect, detectState: "ok", detectFailure: "" });
    } catch (error) {
      set({ detectState: "failed", detectFailure: failureToken(error) });
    }
  },
  async readFlights() {
    if (get().flightsState !== "ok") set({ flightsState: "loading" });
    try {
      const body = await apiFetch<{
        sessions?: unknown[];
        flights?: unknown[];
        history?: unknown[];
        launches?: { live?: unknown; cap?: unknown };
      }>(FLIGHTS_PATH);
      if (!body || typeof body !== "object" || !Array.isArray(body.sessions)) throw new Error("no sessions");
      const rawFlights = Array.isArray(body.flights) ? body.flights : [];
      const rawHistory = Array.isArray(body.history) ? body.history : [];
      const launchedAt: Record<string, string> = {};
      const endedAt: Record<string, string> = {};
      for (const raw of [...rawFlights, ...rawHistory] as Array<Record<string, unknown>>) {
        if (!raw?.launch_id) continue;
        if (raw.launched_at) launchedAt[String(raw.launch_id)] = String(raw.launched_at);
        if (raw.ended_at) endedAt[String(raw.launch_id)] = String(raw.ended_at);
      }
      const live = Number(body.launches?.live);
      const cap = Number(body.launches?.cap);
      const launches = Number.isFinite(live) && Number.isFinite(cap) && cap > 0 ? { live, cap } : null;
      useAgentFlights.setState({
        sessions: body.sessions.map(fromWireSessionRow),
        flights: rawFlights.map(fromWireFlight),
        loaded: true,
      });
      set({ flightsState: "ok", launchedAt, endedAt, history: rawHistory.map(fromWireFlight), launches });
    } catch {
      set({ flightsState: "failed" });
    }
  },
  async installHooks(agent) {
    if (get().installing) return false;
    set({ installing: agent, installFailure: "", installFailedAgent: null });
    try {
      await apiFetch(AGENTS_USE_PATH, { method: "POST", json: { agent } });
      await get().readDetect();
      return true;
    } catch (error) {
      const payload = error instanceof ApiError ? (error.payload as Record<string, unknown> | null) : null;
      set({
        installFailure: typeof payload?.code === "string" ? payload.code.replace(/_/g, " ").toUpperCase() : failureToken(error),
        installFailedAgent: agent,
      });
      return false;
    } finally {
      set({ installing: null });
    }
  },
}));

/** Open the Conductor drawer (the screen's icon, the Dock, Go, ⌘3). */
export function openConductor(origin?: { x: number; y: number } | null): void {
  useConductor.getState().openWindow(origin ?? null);
}

/** Test seam. */
export function __resetConductor(): void {
  useConductor.setState({
    open: false, origin: null, infos: [], detect: null, detectState: "idle", detectFailure: "",
    flightsState: "idle", launchedAt: {}, endedAt: {}, history: [], launches: null, stops: {},
    installing: null, installFailure: "", installFailedAgent: null,
  });
}
