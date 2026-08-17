/** Generic window factory for the five structurally identical window types
 * (HS-117-02). Each config produces open/close methods and the initial
 * state array. Pullouts stay hand-written (custom close with optional id,
 * dispatch routing). */
import type { DeskState, PanelRect } from "./types";
import { play as sfx } from "../../lib/sfx";

/** Configuration for one window type. */
export interface WindowTypeConfig<K extends string> {
  /** State field name: "zoneWindows" | "infoWindows" | ... */
  field: keyof DeskState;
  /** The key field on each window entry: "id" | "slug" | "ref" */
  key: K;
  /** Panel id prefix: "zone:" | "info:" | ... */
  panelPrefix: string;
  /** localStorage key for persistence (null = transient). */
  persistKey: string | null;
  /** Extra logic on open (e.g. workbench default sizing). */
  onOpen?: (
    value: string,
    get: () => DeskState,
    set: (partial: Partial<DeskState>) => void,
  ) => void;
}

type WindowEntry<K extends string> = Record<K, string> & {
  origin: { x: number; y: number } | null;
};

// ---- persistence helpers ------------------------------------------------

function loadPersistedWindows<K extends string>(
  persistKey: string | null,
  key: K,
): WindowEntry<K>[] {
  if (!persistKey) return [];
  try {
    const raw = localStorage.getItem(persistKey);
    const ids = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(ids)
      ? ids
          .filter((v) => typeof v === "string")
          .map((id) => ({ [key]: id, origin: null }) as unknown as WindowEntry<K>)
      : [];
  } catch {
    return [];
  }
}

function persistWindows<K extends string>(
  persistKey: string | null,
  open: WindowEntry<K>[],
  key: K,
): void {
  if (!persistKey) return;
  try {
    localStorage.setItem(
      persistKey,
      JSON.stringify(open.map((w) => w[key])),
    );
  } catch {
    /* storage may be unavailable */
  }
}

// ---- factory ------------------------------------------------------------

/** Build the initial state value for one window type. */
export function windowInitialState<K extends string>(
  config: WindowTypeConfig<K>,
): WindowEntry<K>[] {
  return loadPersistedWindows(config.persistKey, config.key);
}

/** Build the open method for one window type. */
export function makeOpenWindow<K extends string>(
  config: WindowTypeConfig<K>,
) {
  return function openWindow(
    this: void,
    value: string,
    origin: { x: number; y: number } | undefined,
    set: (partial: Partial<DeskState>) => void,
    get: () => DeskState,
  ): void {
    const open = get()[config.field] as unknown as WindowEntry<K>[];
    const panelId = `${config.panelPrefix}${value}`;
    if (!open.some((w) => w[config.key] === value)) {
      const entry = { [config.key]: value, origin: origin ?? null } as unknown as WindowEntry<K>;
      const next = [...open, entry];
      set({ [config.field]: next } as unknown as Partial<DeskState>);
      if (config.persistKey) persistWindows(config.persistKey, next, config.key);
      if (config.onOpen) config.onOpen(value, get, set);
      sfx("latch");
    }
    get().focusPanel(panelId);
  };
}

/** Build the close method for one window type. */
export function makeCloseWindow<K extends string>(
  config: WindowTypeConfig<K>,
) {
  return function closeWindow(
    this: void,
    value: string,
    set: (partial: Partial<DeskState>) => void,
    get: () => DeskState,
  ): void {
    const prev = get()[config.field] as unknown as WindowEntry<K>[];
    const next = prev.filter((w) => w[config.key] !== value);
    if (next.length < prev.length) sfx("latch");
    set({ [config.field]: next } as unknown as Partial<DeskState>);
    if (config.persistKey) persistWindows(config.persistKey, next, config.key);
  };
}

// ---- the five window configs --------------------------------------------

export const ZONE_WINDOW_CONFIG: WindowTypeConfig<"id"> = {
  field: "zoneWindows",
  key: "id",
  panelPrefix: "zone:",
  persistKey: "hs.desk.zone-windows",
};

export const INFO_WINDOW_CONFIG: WindowTypeConfig<"ref"> = {
  field: "infoWindows",
  key: "ref",
  panelPrefix: "info:",
  persistKey: null,
};

export const ROADMAP_WINDOW_CONFIG: WindowTypeConfig<"slug"> = {
  field: "roadmapWindows",
  key: "slug",
  panelPrefix: "roadmap:",
  persistKey: null,
};

export const REPOSITORY_WINDOW_CONFIG: WindowTypeConfig<"id"> = {
  field: "repositoryWindows",
  key: "id",
  panelPrefix: "repository:",
  persistKey: null,
};

export const WORKBENCH_WINDOW_CONFIG: WindowTypeConfig<"id"> = {
  field: "workbenchWindows",
  key: "id",
  panelPrefix: "workbench:",
  persistKey: null,
  onOpen(value: string, get: () => DeskState, set: (partial: Partial<DeskState>) => void) {
    const panelId = `workbench:${value}`;
    if (!get().panelRects[panelId]) {
      const vw = window.innerWidth || 1280;
      const vh = window.innerHeight || 800;
      const w = Math.min(640, vw - 40);
      const h = Math.min(520, vh - 100);
      const rect: PanelRect = {
        x: Math.round((vw - w) / 2),
        y: Math.round((vh - h) * 0.3),
        w,
        h,
      };
      get().setPanelRect(panelId, rect);
    }
  },
};
