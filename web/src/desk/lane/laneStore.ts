/** PHILO-14 C2 — the agent's lane window: which launch is open, its data,
 * and its actions.
 *
 * One lane window at a time. A launch opens it by id; a coder session that
 * belongs to a launch opens it too (the session window stays the face of a
 * plain, non-launch session).
 *
 * Every action of the lane (Answer, Use draft's send, Re-brief, ARM, Stop)
 * goes to the lane's OWN session: the launch's registered session key, read
 * from the lane JSON at the moment of the press. Never the shared steering
 * selection (Panes can point that at another pane while the lane is open).
 * The steering store is used only behind Raw (the pane, its keys), and Raw
 * binds it to the lane's session first.
 *
 * The data is `GET /api/agent/launches/{id}/lane`. The first read starts at
 * event 0; every later read (a coder frame, the 5 s tick while the window is
 * in front, a scroll to the end) asks for the events after the last one it
 * holds and takes the rest of the lane whole. */
import { create } from "zustand";
import { apiFetch, apiRequest } from "../../lib/api";
import { play as sfx } from "../../lib/sfx";
import { useAgentFlights } from "../agentFlights";
import { useSteering } from "../steering";
import { isNotRead, type LaneEvent, type LaneWire } from "./laneWire";

/** Events one read asks for. */
export const LANE_PAGE = 200;

/** The last thing the owner did on this lane, kept on the face when the
 * well that made it closes or the wait it answered clears. */
export interface LaneReceipt {
  word: "SENT" | "NOT SENT" | "ARMED" | "STOPPED" | "NOT STOPPED" | "ARM FIRST";
  at: number;
  text: string;
  tone: "ok" | "fail";
}

interface LaneState {
  launchId: string | null;
  raw: boolean;
  rebrief: boolean;
  lane: LaneWire | null;
  events: LaneEvent[];
  lastId: number;
  more: boolean;
  eventsNotRead: string | null;
  loading: boolean;
  error: string | null;
  /** Each Speak answer press: the ask well's mic starts once per value. */
  answerSeq: number;
  receipt: LaneReceipt | null;
  sending: boolean;
  open(launchId: string, opts?: { sessionKey?: string | null; answer?: boolean }): void;
  close(): void;
  setRaw(raw: boolean): void;
  setRebrief(open: boolean): void;
  load(): Promise<void>;
  /** Type `text` into the lane's session. `waitId` names the wait an answer
   * answers (the hub refuses it when that wait is not the current one). */
  send(text: string, opts?: { waitId?: string | null }): Promise<boolean>;
  arm(): Promise<boolean>;
  stop(): Promise<boolean>;
}

let inflight: Promise<void> | null = null;
let again = false;
let answerRequests = 0;

const EMPTY = {
  lane: null,
  events: [] as LaneEvent[],
  lastId: 0,
  more: false,
  eventsNotRead: null,
  loading: false,
  error: null,
  raw: false,
  rebrief: false,
  receipt: null,
  sending: false,
};

/** The lane's own session key, from the lane JSON (never the steering selection). */
export function laneSessionKey(lane: LaneWire | null | undefined): string | null {
  const key = lane?.launch?.session_key;
  return key ? String(key) : null;
}

function firstWords(text: string, max = 48): string {
  const line = text.replace(/\s+/g, " ").trim();
  return line.length <= max ? line : `${line.slice(0, max).trimEnd()}…`;
}

const REFUSAL_WORD: Record<string, string> = {
  unarmed: "ARM FIRST",
  expired: "ARM FIRST",
  wait_not_current: "QUESTION ANSWERED OR CHANGED",
  pane_gone: "PANE GONE",
  pane_mismatch: "PANE CHANGED",
  no_pane: "NO PANE",
  stale_session: "SESSION STALE",
};

async function post(url: string, body: unknown): Promise<{ ok: boolean; status: number; body: Record<string, unknown> }> {
  const res = await apiRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const json = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  return { ok: res.ok, status: res.status, body: json };
}

export const useLane = create<LaneState>((set, get) => ({
  launchId: null,
  answerSeq: 0,
  ...EMPTY,

  open(launchId, opts) {
    if (get().launchId !== launchId) set({ launchId, ...EMPTY });
    if (opts?.answer) set({ answerSeq: ++answerRequests });
    void get().load();
  },

  close() {
    const key = laneSessionKey(get().lane);
    set({ launchId: null, ...EMPTY });
    // Raw bound the steering store to the lane's session: let it go.
    const steering = useSteering.getState();
    if (key && steering.openKey === key) steering.closeSession();
  },

  setRaw(raw) {
    const key = laneSessionKey(get().lane);
    // Raw shows the lane's own pane: bind the steering store to it.
    if (raw && key && useSteering.getState().openKey !== key) useSteering.getState().openSession(key);
    set({ raw });
  },

  setRebrief(open) {
    set({ rebrief: open });
  },

  load() {
    if (inflight) {
      again = true;
      return inflight;
    }
    const launchId = get().launchId;
    if (!launchId) return Promise.resolve();
    const after = get().lastId;
    set({ loading: true });
    inflight = apiFetch<LaneWire>(
      `/api/agent/launches/${encodeURIComponent(launchId)}/lane?after=${after}&limit=${LANE_PAGE}`,
    )
      .then((lane) => {
        if (get().launchId !== launchId || !lane || typeof lane !== "object") return;
        const patch: Partial<LaneState> = { lane, error: null };
        if (isNotRead(lane.events)) {
          patch.eventsNotRead = lane.events.not_read;
        } else {
          const held = get().events;
          const seen = new Set(held.map((e) => e.id));
          const fresh = (lane.events ?? []).filter((e) => !seen.has(e.id));
          const events = fresh.length ? [...held, ...fresh] : held;
          patch.events = events;
          patch.eventsNotRead = null;
          patch.lastId = events.length ? events[events.length - 1].id : get().lastId;
          patch.more = lane.events_next_after != null;
        }
        set(patch);
      })
      .catch((err: unknown) => {
        if (get().launchId === launchId) set({ error: err instanceof Error ? err.message : String(err) });
      })
      .finally(() => {
        inflight = null;
        if (get().launchId === launchId) set({ loading: false });
        if (again) {
          again = false;
          void get().load();
        }
      });
    return inflight;
  },

  async send(text, opts) {
    const key = laneSessionKey(get().lane);
    const clean = text.trim();
    if (!key || !clean || get().sending) return false;
    const control = get().lane?.control;
    const needsArm = control && !isNotRead(control) && !control.direct && !control.armed;
    if (needsArm) {
      set({ receipt: { word: "ARM FIRST", at: Date.now(), text: firstWords(clean), tone: "fail" } });
      return false;
    }
    set({ sending: true });
    try {
      const body: Record<string, unknown> = { text: clean, submit: true };
      if (opts && "waitId" in opts) body.wait_id = opts.waitId ?? "";
      const res = await post(`/api/coders/${encodeURIComponent(key)}/steer`, body);
      if (res.ok && res.body.status === "delivered") {
        sfx("land");
        set({ receipt: { word: "SENT", at: Date.now(), text: firstWords(clean), tone: "ok" } });
        void get().load();
        return true;
      }
      sfx("error");
      const status = String(res.body.status ?? "");
      const word = REFUSAL_WORD[status];
      set({
        receipt: word === "ARM FIRST"
          ? { word: "ARM FIRST", at: Date.now(), text: firstWords(clean), tone: "fail" }
          : { word: "NOT SENT", at: Date.now(), text: word ?? String(res.body.detail ?? status ?? `HTTP ${res.status}`), tone: "fail" },
      });
      void get().load();
      return false;
    } catch {
      set({ receipt: { word: "NOT SENT", at: Date.now(), text: "HUB UNREACHABLE", tone: "fail" } });
      return false;
    } finally {
      set({ sending: false });
    }
  },

  async arm() {
    const key = laneSessionKey(get().lane);
    if (!key) return false;
    try {
      const res = await post(`/api/coders/${encodeURIComponent(key)}/arm`, {});
      if (res.ok && res.body.status === "armed") {
        set({ receipt: { word: "ARMED", at: Date.now(), text: String(res.body.pane_id ?? ""), tone: "ok" } });
        await get().load();
        return true;
      }
      const status = String(res.body.status ?? "");
      set({ receipt: { word: "NOT SENT", at: Date.now(), text: REFUSAL_WORD[status] ?? String(res.body.detail ?? status), tone: "fail" } });
      return false;
    } catch {
      set({ receipt: { word: "NOT SENT", at: Date.now(), text: "HUB UNREACHABLE", tone: "fail" } });
      return false;
    }
  },

  async stop() {
    const key = laneSessionKey(get().lane);
    if (!key) return false;
    const control = get().lane?.control;
    const known = control && !isNotRead(control) ? control : null;
    // YOLO arms per press (R6); Secure and Normal need the owner's own ARM.
    if (known && !known.armed) {
      if (String(known.mode) !== "yolo") {
        set({ receipt: { word: "ARM FIRST", at: Date.now(), text: "STOP", tone: "fail" } });
        return false;
      }
      if (!(await get().arm())) return false;
    }
    try {
      const res = await post(`/api/coders/${encodeURIComponent(key)}/kill`, { scope: "session" });
      if (res.ok && res.body.status === "killed") {
        set({ receipt: { word: "STOPPED", at: Date.now(), text: "BY YOU", tone: "ok" } });
        await get().load();
        return true;
      }
      const status = String(res.body.status ?? "");
      set({ receipt: { word: "NOT STOPPED", at: Date.now(), text: REFUSAL_WORD[status] ?? String(res.body.detail ?? status), tone: "fail" } });
      return false;
    } catch {
      set({ receipt: { word: "NOT STOPPED", at: Date.now(), text: "HUB UNREACHABLE", tone: "fail" } });
      return false;
    }
  },
}));

/** The launch a coder session belongs to (the Conductor's flights), or null. */
export function launchForSession(key: string | null | undefined): string | null {
  if (!key) return null;
  const flight = useAgentFlights.getState().flights.find((f) => f.sessionKey === key && f.launchId);
  return flight?.launchId ?? null;
}

/** The lane window's launch: the one opened by id, else the launch of the
 * open coder session. Null: no lane (a plain session keeps its window). */
export function useLaneLaunchId(): string | null {
  const explicit = useLane((s) => s.launchId);
  const openKey = useSteering((s) => s.openKey);
  const flights = useAgentFlights((s) => s.flights);
  if (explicit) return explicit;
  if (!openKey) return null;
  return flights.find((f) => f.sessionKey === openKey && f.launchId)?.launchId ?? null;
}

/** True when the open steering session is shown by the lane (a launch's
 * session, or the lane's own session behind Raw): the session window steps
 * aside. A plain pane opened from Panes keeps its own window. */
export function useLaneOwnsSteering(): boolean {
  const openKey = useSteering((s) => s.openKey);
  const laneKey = useLane((s) => laneSessionKey(s.lane));
  const launchId = useLane((s) => s.launchId);
  const flights = useAgentFlights((s) => s.flights);
  if (!openKey) return false;
  if (launchId && laneKey === openKey) return true;
  return flights.some((f) => f.sessionKey === openKey && f.launchId);
}

/** Test seam. */
export function __resetLane(): void {
  inflight = null;
  again = false;
  useLane.setState({ launchId: null, answerSeq: 0, ...EMPTY });
}
