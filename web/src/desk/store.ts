/** The desk's one state store (HS-73-01). Zustand, no persist middleware:
 * positions keep the EXACT legacy localStorage contract —
 * `localStorage["hs.diorama.pos"]` holding a bare `{id: {x, y}}` map,
 * local-only, never synced (the Primitive Framework layout rule) — so a
 * hand-arranged desk survives the Alpine→React cutover byte-for-byte. */
import { create } from "zustand";
import {
  EMPTY_ITEMS, loadAll,
  type Items, type Status,
} from "./api";
import { loadSetup, type SetupStatus } from "./setup";

export interface UnitPos { x: number; y: number }

const POS_KEY = "hs.diorama.pos";

function loadPositions(): Record<string, UnitPos> {
  try {
    return JSON.parse(localStorage.getItem(POS_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function savePositions(positions: Record<string, UnitPos>) {
  try {
    localStorage.setItem(POS_KEY, JSON.stringify(positions));
  } catch {
    /* storage may be unavailable; arranging just won't persist */
  }
}

interface DeskState {
  items: Items;
  profiles: Array<Record<string, unknown>>;
  status: Status;
  error: string;
  loading: boolean;
  updatedAt: number | null;
  positions: Record<string, UnitPos>;
  divedZone: string | null;
  /** id of the object being dragged (render z-lift; float pauses). */
  draggingId: string | null;
  setup: SetupStatus | null;

  refresh(): Promise<void>;
  /** Instant create (HS-73-02; HS-73-03 adds the in-world editor + beat). */
  createPrimitive(kind: "note" | "kb" | "agent" | "zone"): Promise<void>;
  setPosition(id: string, pos: UnitPos): void;
  persistPositions(): void;
  clearPosition(id: string): void;
  tidyDesk(): void;
  setDragging(id: string | null): void;
}

export const useDesk = create<DeskState>((set, get) => ({
  items: { ...EMPTY_ITEMS },
  profiles: [],
  status: {},
  error: "",
  loading: false,
  updatedAt: null,
  positions: loadPositions(),
  divedZone: null,
  draggingId: null,
  setup: null,

  async refresh() {
    set({ loading: true, error: "" });
    const [{ items, profiles, status, error }, setup] = await Promise.all([
      loadAll(),
      loadSetup(),
    ]);
    set({ items, profiles, status, error, setup, loading: false, updatedAt: Date.now() });
  },

  async createPrimitive(kind) {
    const posts: Record<string, [string, Record<string, unknown>]> = {
      note: ["/api/notes", { title: "New note", body_markdown: "" }],
      kb: ["/api/kbs", { name: "New KB" }],
      agent: ["/api/agents", { name: "New agent", avatar: "🤖" }],
      zone: ["/api/directories", { name: "New zone" }],
    };
    const [url, body] = posts[kind];
    try {
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch {
      /* the refresh below reports reachability honestly */
    }
    await get().refresh();
  },

  setPosition(id, pos) {
    set({ positions: { ...get().positions, [id]: pos } });
  },
  persistPositions() {
    savePositions(get().positions);
  },
  clearPosition(id) {
    const { [id]: _dropped, ...rest } = get().positions;
    set({ positions: rest });
    savePositions(rest);
  },
  tidyDesk() {
    set({ positions: {} });
    savePositions({});
  },
  setDragging(id) {
    set({ draggingId: id });
  },
}));
