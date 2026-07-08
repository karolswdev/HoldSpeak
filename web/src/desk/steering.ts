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

/** `m:ss` for the countdown chip — the grant's honest remainder. */
export function mmss(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

interface SteeringState {
  openKey: string | null;
  session: SteeringSession | null;
  paneStatus: PaneStatus;
  paneDetail: string;
  paneLines: string[];
  paneHash: string | null;
  inflight: boolean;
  /** The OPEN session's grant (HS-87-02): armed + a client-side
   * countdown anchor (epoch ms), re-synced by every peek. */
  armed: boolean;
  armedUntil: number | null;
  armError: string;
  /** Armed state for every pin on the desk: key → epoch ms expiry. */
  armedKeys: Record<string, number>;
  /** The last steer's fate (HS-87-03), rendered in place. */
  steerState: "idle" | "sending" | "sent" | "refused";
  steerDetail: string;
  /** Classify (HS-87-05): manual session→story pins, desk-side only.
   * A view preference over receipts — never the correlator's verdict;
   * persisted to localStorage, re-asserted if the registry changes. */
  manualPins: Record<string, string>;
  classifyState: "idle" | "kept" | "failed";
  openSession(key: string): void;
  closeSession(): void;
  poll(): Promise<void>;
  arm(): Promise<void>;
  disarm(): Promise<void>;
  refreshGrants(): Promise<void>;
  steer(
    text: string,
    submit: boolean,
    grounding?: { meeting_ids: string[]; artifact_ids: string[]; expand: string } | null,
  ): Promise<boolean>;
  keepAsNote(title?: string): Promise<boolean>;
  pinToStory(key: string, storyId: string): void;
  clearPin(key: string): void;
}

let timer: ReturnType<typeof setInterval> | null = null;

const PIN_KEY = "hs.steering.pins";

function loadPins(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(PIN_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function savePins(pins: Record<string, string>) {
  try {
    localStorage.setItem(PIN_KEY, JSON.stringify(pins));
  } catch {
    /* storage unavailable — the pin won't persist, honestly */
  }
}

/** The grant riding the peek envelope → the store's armed shape. */
function grantPatch(key: string, grant: any, armedKeys: Record<string, number>) {
  const armed = Boolean(grant && grant.armed);
  const expiresIn = armed ? Number(grant.expires_in_seconds || 0) : 0;
  const nextKeys = { ...armedKeys };
  if (armed) nextKeys[key] = Date.now() + expiresIn * 1000;
  else delete nextKeys[key];
  return {
    armed,
    armedUntil: armed ? Date.now() + expiresIn * 1000 : null,
    armedKeys: nextKeys,
  };
}

export const useSteering = create<SteeringState>((set, get) => ({
  openKey: null,
  session: null,
  paneStatus: "idle",
  paneDetail: "",
  paneLines: [],
  paneHash: null,
  inflight: false,
  armed: false,
  armedUntil: null,
  armError: "",
  armedKeys: {},
  steerState: "idle",
  steerDetail: "",
  manualPins: loadPins(),
  classifyState: "idle",

  openSession(key) {
    if (timer !== null) clearInterval(timer);
    set({
      openKey: key,
      session: null,
      paneStatus: "idle",
      paneDetail: "",
      paneLines: [],
      paneHash: null,
      armed: false,
      armedUntil: null,
      armError: "",
      steerState: "idle",
      steerDetail: "",
      classifyState: "idle",
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
      armed: false,
      armedUntil: null,
      armError: "",
      steerState: "idle",
      steerDetail: "",
      classifyState: "idle",
    });
  },

  async arm() {
    const key = get().openKey;
    if (!key) return;
    set({ armError: "" });
    try {
      const res = await fetch(`/api/coders/${encodeURIComponent(key)}/arm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const body = await res.json().catch(() => ({}));
      if (get().openKey !== key) return;
      if (res.ok && body.status === "armed") {
        set(
          grantPatch(
            key,
            { armed: true, expires_in_seconds: body.expires_in_seconds },
            get().armedKeys,
          ),
        );
        return;
      }
      // The refusal, typed and in place — staleness named, pane named.
      set({ armError: body.detail || body.status || `HTTP ${res.status}` });
    } catch {
      if (get().openKey === key) set({ armError: "hub unreachable" });
    }
  },

  async disarm() {
    const key = get().openKey;
    if (!key) return;
    try {
      await fetch(`/api/coders/${encodeURIComponent(key)}/disarm`, {
        method: "POST",
      });
    } catch {
      /* the grant state re-syncs on the next peek either way */
    }
    if (get().openKey === key) {
      set(grantPatch(key, { armed: false }, get().armedKeys));
    }
  },

  async steer(text, submit, grounding) {
    const key = get().openKey;
    if (!key || !text.trim()) return false;
    set({ steerState: "sending", steerDetail: "" });
    try {
      const res = await fetch(`/api/coders/${encodeURIComponent(key)}/steer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          grounding ? { text, submit, grounding } : { text, submit },
        ),
      });
      const body = await res.json().catch(() => ({}));
      if (get().openKey !== key) return false;
      if (res.ok && body.status === "delivered") {
        set({ steerState: "sent", steerDetail: "" });
        return true;
      }
      // A refusal that revoked (expiry, recycled pane) re-offers ARM:
      // the armed flag drops here and the header chip is the answer.
      // A grounding-over-cap or unknown-ref refusal keeps the grant —
      // it is a composition problem, not a consent one.
      const refusal = body.detail || body.error || body.status || `HTTP ${res.status}`;
      const revoking = ["unarmed", "expired", "pane_mismatch", "pane_gone"].includes(
        body.status,
      );
      set({
        steerState: "refused",
        steerDetail: body.detail || refusal,
        ...(revoking ? grantPatch(key, { armed: false }, get().armedKeys) : {}),
      });
      return false;
    } catch {
      if (get().openKey === key)
        set({ steerState: "refused", steerDetail: "hub unreachable" });
      return false;
    }
  },

  async keepAsNote(title) {
    const key = get().openKey;
    if (!key) return false;
    try {
      const res = await fetch(`/api/coders/${encodeURIComponent(key)}/keep-note`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(title ? { title } : {}),
      });
      const ok = res.status === 201;
      if (get().openKey === key) set({ classifyState: ok ? "kept" : "failed" });
      return ok;
    } catch {
      if (get().openKey === key) set({ classifyState: "failed" });
      return false;
    }
  },

  pinToStory(key, storyId) {
    const pins = { ...get().manualPins, [key]: storyId };
    set({ manualPins: pins });
    savePins(pins);
  },

  clearPin(key) {
    const { [key]: _dropped, ...rest } = get().manualPins;
    set({ manualPins: rest });
    savePins(rest);
  },

  async refreshGrants() {
    try {
      const res = await fetch("/api/coders/steering/grants");
      if (!res.ok) return;
      const body = await res.json().catch(() => ({}));
      const now = Date.now();
      const armedKeys: Record<string, number> = {};
      for (const [key, grant] of Object.entries(body.grants || {})) {
        armedKeys[key] = now + Number((grant as any).expires_in_seconds || 0) * 1000;
      }
      set({ armedKeys });
    } catch {
      /* pins keep their last honest state; the next tick retries */
    }
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
      const grant = grantPatch(key, body.grant, get().armedKeys);
      if (peek.status === "not_modified") {
        set({ session, paneStatus: "live", ...grant }); // the view stays; the gate held
        return;
      }
      if (peek.status === "live") {
        set({
          session,
          paneStatus: "live",
          paneLines: peek.lines || [],
          paneHash: peek.hash || null,
          paneDetail: "",
          ...grant,
        });
        return;
      }
      set({
        session,
        paneStatus: (peek.status as PaneStatus) || "error",
        paneDetail: peek.detail || "",
        paneLines: [],
        paneHash: null,
        ...grant,
      });
    } catch {
      if (get().openKey === key) set({ paneStatus: "unreachable", paneDetail: "" });
    } finally {
      set({ inflight: false });
    }
  },
}));
