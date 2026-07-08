/** The steering desk (HS-87-01) — attach: the typed data layer.
 *
 * One session pull-out at a time; the peek poll runs ONLY while it
 * is open (1.5 s, single-flight, hash-gated server-side so an idle
 * pane costs a stat, not a body). Wire is snake_case; these are the
 * camelCase view shapes. Statuses are typed and honest: a dead pane,
 * a missing tmux, a stale record each render as themselves.
 */

import { create } from "zustand";

export type PaneStatus =
  | "live"
  | "not_modified"
  | "pane_gone"
  | "tmux_absent"
  | "no_pane"
  | "error"
  | "unknown_session"
  | "unreachable"
  | "idle";

export interface SteeringSession {
  key: string;
  agent: string;
  stale: boolean;
  awaitingResponse: boolean;
  question: string;
  updatedAt: string;
}

export const fromWireSteeringSession = (body: any): SteeringSession => ({
  key: body.key || "",
  agent: body.agent || "",
  stale: Boolean(body.stale),
  awaitingResponse: Boolean(body.awaiting_response),
  question: body.question || "",
  updatedAt: body.updated_at || "",
});

/** A `scope:"coder"` frame on the one bus — an awaiting-response
 * transition somewhere on the board; listeners refresh on sight. */
export function isCoderFrame(frame: any): boolean {
  return Boolean(
    frame &&
      frame.type === "intel_status" &&
      frame.data &&
      frame.data.scope === "coder",
  );
}

export const PEEK_POLL_MS = 1_500;
export const PEEK_LINES = 200;

interface SteeringState {
  openKey: string | null;
  session: SteeringSession | null;
  paneStatus: PaneStatus;
  paneDetail: string;
  paneLines: string[];
  paneHash: string | null;
  inflight: boolean;
  openSession(key: string): void;
  closeSession(): void;
  poll(): Promise<void>;
}

let timer: ReturnType<typeof setInterval> | null = null;

export const useSteering = create<SteeringState>((set, get) => ({
  openKey: null,
  session: null,
  paneStatus: "idle",
  paneDetail: "",
  paneLines: [],
  paneHash: null,
  inflight: false,

  openSession(key) {
    if (timer !== null) clearInterval(timer);
    set({
      openKey: key,
      session: null,
      paneStatus: "idle",
      paneDetail: "",
      paneLines: [],
      paneHash: null,
    });
    void get().poll();
    timer = setInterval(() => void get().poll(), PEEK_POLL_MS);
  },

  closeSession() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
    set({
      openKey: null,
      session: null,
      paneStatus: "idle",
      paneDetail: "",
      paneLines: [],
      paneHash: null,
    });
  },

  async poll() {
    const key = get().openKey;
    if (!key || get().inflight) return; // single-flight: a slow peek skips ticks
    set({ inflight: true });
    try {
      const hash = get().paneHash;
      const url =
        `/api/coders/${encodeURIComponent(key)}/peek?lines=${PEEK_LINES}` +
        (hash ? `&last_hash=${encodeURIComponent(hash)}` : "");
      const res = await fetch(url);
      const body = await res.json().catch(() => ({}));
      if (get().openKey !== key) return; // closed mid-flight
      if (res.status === 404) {
        set({ paneStatus: "unknown_session", paneDetail: key });
        return;
      }
      if (!res.ok) {
        set({ paneStatus: "error", paneDetail: body.error || `HTTP ${res.status}` });
        return;
      }
      const peek = body.peek || {};
      const session = fromWireSteeringSession(body);
      if (peek.status === "not_modified") {
        set({ session, paneStatus: "live" }); // the view stays; the gate held
        return;
      }
      if (peek.status === "live") {
        set({
          session,
          paneStatus: "live",
          paneLines: peek.lines || [],
          paneHash: peek.hash || null,
          paneDetail: "",
        });
        return;
      }
      set({
        session,
        paneStatus: (peek.status as PaneStatus) || "error",
        paneDetail: peek.detail || "",
        paneLines: [],
        paneHash: null,
      });
    } catch {
      if (get().openKey === key) set({ paneStatus: "unreachable", paneDetail: "" });
    } finally {
      set({ inflight: false });
    }
  },
}));
