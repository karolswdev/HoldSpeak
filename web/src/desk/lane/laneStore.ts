/** PHILO-14 C2 — the agent's lane window: which launch is open, and its data.
 *
 * One lane window at a time (as one session window). A launch opens it by
 * id; a coder session that belongs to a launch opens it too (the session
 * window stays the face of a plain, non-launch session). The steering store
 * (`steering.ts`) keeps the launch's session open beside it: the Raw pane,
 * Answer (the steer route) and Stop (the kill route) are its verbs.
 *
 * The data is `GET /api/agent/launches/{id}/lane`. The first read starts at
 * event 0; every later read (a coder frame, the 5 s tick while the window is
 * in front, a scroll to the end) asks for the events after the last one it
 * holds and takes the rest of the lane whole. */
import { create } from "zustand";
import { apiFetch } from "../../lib/api";
import { useAgentFlights } from "../agentFlights";
import { useSteering } from "../steering";
import { isNotRead, type LaneEvent, type LaneWire } from "./laneWire";

/** Events one read asks for. */
export const LANE_PAGE = 200;

interface LaneState {
  launchId: string | null;
  /** The title-bar Raw gadget: the terminal pane in place of the timeline. */
  raw: boolean;
  /** Re-brief: the steer well, prefilled `Re-brief: `. */
  rebrief: boolean;
  lane: LaneWire | null;
  events: LaneEvent[];
  /** The id the next read starts after (the last event held). */
  lastId: number;
  /** True when the last read returned a full page: more events wait. */
  more: boolean;
  /** The events part could not be read (the reason), else null. */
  eventsNotRead: string | null;
  loading: boolean;
  /** The lane could not be read at all (the reason), else null. */
  error: string | null;
  open(launchId: string, opts?: { sessionKey?: string | null; answer?: boolean }): void;
  close(): void;
  setRaw(raw: boolean): void;
  setRebrief(open: boolean): void;
  load(): Promise<void>;
}

let inflight: Promise<void> | null = null;
let again = false;

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
};

export const useLane = create<LaneState>((set, get) => ({
  launchId: null,
  ...EMPTY,

  open(launchId, opts) {
    const same = get().launchId === launchId;
    if (!same) set({ launchId, ...EMPTY });
    const key = opts?.sessionKey ?? null;
    const steering = useSteering.getState();
    if (key && (steering.openKey !== key || opts?.answer)) steering.openSession(key, { answer: opts?.answer });
    void get().load();
  },

  close() {
    set({ launchId: null, ...EMPTY });
    useSteering.getState().closeSession();
  },

  setRaw(raw) {
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
        // The session the launch is bound to is the one the Raw pane, Answer
        // and Stop act on.
        const key = lane.launch?.session_key;
        const steering = useSteering.getState();
        if (key && steering.openKey !== key) steering.openSession(key);
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

/** Test seam. */
export function __resetLane(): void {
  inflight = null;
  again = false;
  useLane.setState({ launchId: null, ...EMPTY });
}
