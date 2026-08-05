/** The desk's one state store (HS-73-01). Zustand, no persist middleware:
 * positions keep the EXACT legacy localStorage contract —
 * `localStorage["hs.diorama.pos"]` holding a bare `{id: {x, y}}` map,
 * local-only, never synced (the Primitive Framework layout rule) — so a
 * hand-arranged desk survives the React unification byte-for-byte. */
import { create } from "zustand";
import { apiRequest } from "../lib/api";
import {
  EMPTY_ITEMS,
  loadAll,
  qualifiedRef,
  type InferenceTarget,
  type Items,
  type ProjectSummary,
  type Status,
} from "./api";
import { buildLinearGraph } from "./graph";
import { loadSetup, type SetupStatus } from "./setup";
import { registerRepository } from "./repository";

export interface UnitPos {
  x: number;
  y: number;
}

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

/** A desk-window rect in viewport px (the panel counterpart of UnitPos).
 * Panels the user has arranged persist under their own key, exactly like
 * hand-arranged objects do; untouched panels keep their CSS default corner. */
export interface PanelRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

const PANEL_KEY = "hs.desk.panels";
const PANEL_ORDER_LIMIT = 100;

// A panel id is local storage data, not an executable identifier. Retain
// legacy panel names while rejecting empty and malformed keys; live panels
// subsequently present themselves through the compositor registry.
const isPanelId = (value: unknown): value is string =>
  typeof value === "string" && /^[A-Za-z0-9:_-]+$/.test(value);

const isPanelRect = (value: unknown): value is PanelRect => {
  if (!value || typeof value !== "object") return false;
  const rect = value as PanelRect;
  return [rect.x, rect.y, rect.w, rect.h].every(Number.isFinite) &&
    rect.w > 0 && rect.h > 0;
};

/** Keep z positions inside the window band. `panelOrder` is the store's
 * z-index source, so retaining its newest 100 ids is equivalent to
 * renumbering the ladder from its base while preserving relative order. */
function compactPanelOrder(order: string[]): string[] {
  const unique = Array.from(new Set(order));
  return unique.length > PANEL_ORDER_LIMIT
    ? unique.slice(-PANEL_ORDER_LIMIT)
    : unique;
}

/** The persisted window layout (HS-95-02; order since HS-97-03):
 * arranged rects, the stacking order, and maximize. Minimize is
 * session-scoped by design and is NOT persisted (a legacy `min` key is
 * tolerated and dropped). The loader also accepts the Phase 93 flat
 * `{id: rect}` shape so an arranged desk survives the upgrade. */
interface PanelLayout {
  rects: Record<string, PanelRect>;
  order: string[];
  max: string[];
}

export function loadPanelLayout(): PanelLayout {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(PANEL_KEY) || "{}") || {};
    const layout = raw as { rects?: unknown; order?: unknown; max?: unknown };
    const source = raw && typeof raw === "object" && layout.rects ? layout.rects : raw;
    const rects = Object.fromEntries(
      Object.entries(source && typeof source === "object" ? source : {}).filter(
        ([id, rect]) => isPanelId(id) && isPanelRect(rect),
      ),
    ) as Record<string, PanelRect>;
    const order = compactPanelOrder(
      (Array.isArray(layout.order) ? layout.order : []).filter(
        (value): value is string => isPanelId(value),
      ),
    );
    const max = Array.from(
      new Set(
        (Array.isArray(layout.max) ? layout.max : []).filter(
          (value): value is string => isPanelId(value),
        ),
      ),
    );
    return { rects, order, max };
  } catch {
    return { rects: {}, order: [], max: [] };
  }
}

function savePanelLayout(
  rects: Record<string, PanelRect>,
  keep: string[],
  order: string[],
  max: string[],
) {
  try {
    const out: Record<string, PanelRect> = {};
    for (const id of keep) if (rects[id]) out[id] = rects[id];
    localStorage.setItem(PANEL_KEY, JSON.stringify({ rects: out, order, max }));
  } catch {
    /* storage may be unavailable; arranging just won't persist */
  }
}

const initialPanelLayout = loadPanelLayout();
const initialPanelRects = initialPanelLayout.rects;

/** Zone tray widths in px (`hs.desk.zonew`) — zones move via the shared
 * positions map (keyed `zone:<id>`) and resize via this sibling map. */
const ZONE_W_KEY = "hs.desk.zonew";

function loadZoneWidths(): Record<string, number> {
  try {
    return JSON.parse(localStorage.getItem(ZONE_W_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function saveZoneWidths(widths: Record<string, number>) {
  try {
    localStorage.setItem(ZONE_W_KEY, JSON.stringify(widths));
  } catch {
    /* storage may be unavailable; arranging just won't persist */
  }
}

/** HS-93-08 — the semantic list mode is the SAME Desk, keyboard-first.
 * The choice persists (`hs.desk.view`) and mirrors into the URL as
 * `?view=list` so a bookmarked or shared address opens the same expression. */
export type DeskView = "spatial" | "list";

/** HS-105-03 — a zone window's remembered expression. */
export interface ZoneViewPref {
  view: "icons" | "list";
  sort: "name" | "kind" | "modified";
  dir: "asc" | "desc";
}
const ZONE_VIEWS_KEY = "hs.desk.zone-views";
const ZONE_WINDOWS_KEY = "hs.desk.zone-windows";

function loadZoneViewPrefs(): Record<string, ZoneViewPref> {
  try {
    const raw = localStorage.getItem(ZONE_VIEWS_KEY);
    return raw ? (JSON.parse(raw) as Record<string, ZoneViewPref>) : {};
  } catch {
    return {};
  }
}

function loadZoneWindows(): { id: string; origin: null }[] {
  try {
    const raw = localStorage.getItem(ZONE_WINDOWS_KEY);
    const ids = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(ids)
      ? ids
          .filter((v) => typeof v === "string")
          .map((id) => ({ id, origin: null }))
      : [];
  } catch {
    return [];
  }
}

function persistZoneWindows(open: { id: string }[]) {
  try {
    localStorage.setItem(
      ZONE_WINDOWS_KEY,
      JSON.stringify(open.map((w) => w.id)),
    );
  } catch {
    /* storage may be unavailable */
  }
}

const VIEW_KEY = "hs.desk.view";

/** HS-105-01 — the phone's density altitude: a 104px cell cannot grid a
 * dense desk inside a 393px world (measured, not guessed — the density
 * walk showed the soup). Above this count, a compact desk with NO saved
 * choice leads with the list; an explicit user choice (URL or saved key)
 * always wins — the arrangement stays the user's. */
export const COMPACT_LIST_THRESHOLD = 16;

function loadViewMode(): DeskView | "unset" {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get("view");
    if (fromUrl === "list") return "list";
    if (fromUrl === "spatial") return "spatial";
    const saved = localStorage.getItem(VIEW_KEY);
    if (saved === "list") return "list";
    if (saved === "spatial") return "spatial";
    return "unset"; // resolved against density by defaultViewFor
  } catch {
    return "spatial";
  }
}

/** Resolve an unset view choice against the loaded desk's density. */
export function defaultViewFor(
  mode: DeskView | "unset",
  objectCount: number,
  compact: boolean,
): DeskView {
  if (mode === "list" || mode === "spatial") return mode;
  return compact && objectCount > COMPACT_LIST_THRESHOLD ? "list" : "spatial";
}

function persistViewMode(mode: DeskView) {
  try {
    localStorage.setItem(VIEW_KEY, mode);
  } catch {
    /* storage may be unavailable; the choice just won't persist */
  }
  try {
    const url = new URL(window.location.href);
    if (mode === "list") url.searchParams.set("view", "list");
    else url.searchParams.delete("view");
    window.history.replaceState(null, "", url);
  } catch {
    /* environments without history keep the in-memory choice */
  }
}

/** Meetings on the desk when a local recording started (NEW-beat diff). */
let meetingsBeforeRecording = new Set<string>();

interface DeskState {
  items: Items;
  profiles: Array<Record<string, unknown>>;
  projects: ProjectSummary[];
  inferenceTargets: InferenceTarget[];
  /** HS-83-03 — the hub's runnable models (the ask allow-list). */
  models: Array<{
    name: string;
    source: "hub" | "profile";
    profile_id: string | null;
  }>;
  status: Status;
  error: string;
  loading: boolean;
  updatedAt: number | null;
  positions: Record<string, UnitPos>;
  divedZone: string | null;
  /** id of the object being dragged (render z-lift; float pauses). */
  draggingId: string | null;
  setup: SetupStatus | null;
  /** Freshly-created ids wearing the NEW beat (settles after ~4.5s). */
  newIds: string[];
  /** The world object id whose in-world editor is open (one at a time). */
  editingId: string | null;
  /** Open object cards (HS-101 round 9): real windows — they COEXIST,
   * each remembering the tap point it opened from (the origin its
   * open/close motion flies to). Order is open order; the panel order
   * decides stacking. */
  pullouts: { id: string; origin: { x: number; y: number } | null }[];
  /** HS-105-03 — open zone windows (drawers opened into real desk
   * windows). They coexist like pullouts and persist across reload
   * (`hs.desk.zone-windows`, the HS-103-01 restoration rule). */
  zoneWindows: { id: string; origin: { x: number; y: number } | null }[];
  /** Per-zone remembered expression: view + sort (`hs.desk.zone-views`).
   * The window remembers — that is what makes it a window. */
  zoneViewPrefs: Record<string, ZoneViewPref>;
  /** HS-105-04 — open Info cards (transient inspection windows; they
   * coexist but do not persist across reload). Ref is `kind:id`, bare
   * id, or `zone:<id>`. */
  infoWindows: { ref: string; origin: { x: number; y: number } | null }[];
  /** Delivery Workbench projects open as their own Desk application window. */
  roadmapWindows: { slug: string; origin: { x: number; y: number } | null }[];
  /** Registered git sources open as physical desk drawers. */
  repositoryWindows: { id: string; origin: { x: number; y: number } | null }[];
  /** Agent workbenches open as their own desk windows. */
  workbenchWindows: { id: string; origin: { x: number; y: number } | null }[];
  /** The zone a live drag is hovering (the drop affordance, HS-73-05). */
  hoverZoneId: string | null;
  /** The freshly-created zone whose rename is focused. */
  renamingZoneId: string | null;
  /** The lasso'd/selected objects — the Ask atom's context (HSM-16-04). */
  selectedIds: string[];
  /** The Ask composer is open (in-world, desk visible — never a modal). */
  askOpen: boolean;
  /** HS-83-02 — the persona whose CONVERSATION is open (null = none). */
  chatPersonaId: string | null;
  /** Non-document Desk tool/resource shown in the shared inspector. */
  toolInspector: {
    kind: "project" | "integration" | "target";
    id: string;
  } | null;
  /** One recording verb (UX remediation): the chrome Record chip and the
   * orb drive the SAME hub recorder and mirror the same state. */
  recording: "idle" | "recording" | "busy";
  recordingExternal: boolean;
  recordingStartedAt: number | null;
  /** Zone tray widths in px (resized zones only). */
  zoneWidths: Record<string, number>;
  /** Desk-window geometry per panel id (moved/resized panels only). */
  panelRects: Record<string, PanelRect>;
  /** Panel ids whose rect the user arranged — the persisted subset. */
  panelSaved: string[];
  /** Window focus order; the last id renders in front. Persisted
   * (HS-97-03: the arrangement is sacred, stacking included). */
  panelOrder: string[];
  /** Minimized windows (parked in the tray/dock), session-scoped. */
  panelMin: string[];
  /** Maximized windows (full stage; the saved rect is kept), persisted. */
  panelMax: string[];
  /** HS-93-08 — which expression of the Desk renders (spatial or list). */
  viewMode: DeskView | "unset";

  refresh(): Promise<void>;
  /** Switch Desk expression; persists and mirrors `?view=list` in the URL. */
  setViewMode(mode: DeskView): void;
  /** Create in-world (HS-73-03): instant POST, spawn at center, NEW beat,
   * editor open. The object IS the editor — no modal, ever. */
  createPrimitive(
    kind: "note" | "decision" | "kb" | "recipe" | "zone" | "workflow" | "workbench",
  ): Promise<void>;
  /** Register a Delivery source (or local worktree) as a repository drawer. */
  registerRepository(input: { sourceId?: string; path?: string; label?: string }): Promise<void>;
  markNew(id: string): void;
  openEditor(id: string): void;
  closeEditor(): void;
  /** Autosaving field update through the real PUT routes. */
  updatePrimitive(
    kind: string,
    id: string,
    patch: Record<string, unknown>,
  ): Promise<void>;
  /** Tombstone a deletable primitive, then settle all local desk faces. */
  deletePrimitive(id: string, kind: string): Promise<void>;
  renameZone(id: string, name: string): Promise<void>;
  /** Open an object card. A second object opens a SECOND card (windows
   * coexist); reopening an open object focuses its card. `origin` is
   * the client point the open gesture happened at (the card flies out
   * of it and back into it on close). */
  openPullout(id: string, origin?: { x: number; y: number }): void;
  /** Close one card by object id; with no id, the front-most card. */
  closePullout(id?: string): void;
  /** HS-105-03 — open a drawer as a real desk window (the OPEN grammar;
   * dive survives only as the Focus verb). Reopening focuses. */
  openZoneWindow(id: string, origin?: { x: number; y: number }): void;
  closeZoneWindow(id: string): void;
  /** Remember a zone window's expression (view/sort), persisted. */
  setZoneViewPref(id: string, pref: Partial<ZoneViewPref>): void;
  /** HS-105-04 — Info on everything (right-click → Info). */
  openInfoWindow(ref: string, origin?: { x: number; y: number }): void;
  closeInfoWindow(ref: string): void;
  openRoadmapWindow(slug: string, origin?: { x: number; y: number }): void;
  closeRoadmapWindow(slug: string): void;
  openRepositoryWindow(id: string, origin?: { x: number; y: number }): void;
  closeRepositoryWindow(id: string): void;
  openWorkbenchWindow(id: string, origin?: { x: number; y: number }): void;
  closeWorkbenchWindow(id: string): void;
  setHoverZone(id: string | null): void;
  setRenamingZone(id: string | null): void;
  diveInto(zoneId: string): void;
  surface(): void;
  /** File a primitive into a directory (the real add-only PUT). */
  fileIntoDir(pid: string, dirId: string, kind?: string): Promise<void>;
  /** The toggle-off half (the legacy toggleFile parity). */
  removeFromDir(pid: string, dirId: string, kind?: string): Promise<void>;
  /** HS-105-02 — the drop matrix's Add-to-Knowledge verb (the same
   * membership PUT the card's Filed strip toggles). */
  fileIntoKnowledge(ref: string, kbId: string): Promise<void>;
  /** Select a coder session as the dictation target (answerCoder parity). */
  answerCoder(agent: string, sessionId: string): Promise<boolean>;
  /** Speak straight into the waiting coder (HS-78-03): select the
   * session, then inject the transcript through the remote seam. */
  speakToCoder(
    agent: string,
    sessionId: string,
    text: string,
  ): Promise<boolean>;
  /** Run a capability through the real route; the persisted result
   * MATERIALIZES on the desk (HS-74-03: refresh + the NEW beat). */
  runCapability(
    kind: "recipe" | "chain" | "workflow",
    id: string,
    input: string,
    inferenceTargetId: string,
  ): Promise<{
    ok: boolean;
    output: string;
    artifactId: string | null;
    warning: string | null;
    invocationId: string | null;
    resultRef: string | null;
    state: string;
    actualPlacement: Record<string, unknown> | null;
  }>;
  toggleSelected(id: string): void;
  setSelected(ids: string[]): void;
  clearSelection(): void;
  openAsk(): void;
  openChat(personaId: string): void;
  closeChat(): void;
  openToolInspector(
    kind: "project" | "integration" | "target",
    id: string,
  ): void;
  closeToolInspector(): void;
  closeAsk(): void;
  setPosition(id: string, pos: UnitPos): void;
  persistPositions(): void;
  clearPosition(id: string): void;
  tidyDesk(): void;
  setDragging(id: string | null): void;
  /** Reduce a runtime_activity frame (or /api/state seed) into orb state. */
  applyRecordingActivity(activity: unknown): void;
  /** Start the hub recorder in place (never a browser mic). */
  startRecording(): Promise<void>;
  /** Stop the hub recorder; the finished meeting materializes NEW. */
  stopRecording(): Promise<void>;
  /** Resize a zone tray; persist=true saves the width. */
  setZoneWidth(id: string, width: number, persist?: boolean): void;
  /** Move/resize a desk window; persist=true marks it user-arranged. */
  setPanelRect(id: string, rect: PanelRect, persist?: boolean): void;
  minimizePanel(id: string): void;
  restorePanel(id: string): void;
  toggleMaximizePanel(id: string): void;
  /** Forget every arranged rect and lifecycle mark (the reset verb). */
  resetLayout(): void;
  /** HS-112-03 — apply the packaged architect's-desk seed (idempotent;
   * additive by id, never destructive). */
  seedDesk(): Promise<boolean>;
  /** HS-112-03 — the desk's first destructive verb: tombstone every desk
   * primitive on the hub, re-seed, then sweep the ghost layout keys the
   * dead desk left behind. Confirmed in-world (Prefs) BEFORE this runs.
   * Returns the hub's counts, or null on refusal/unreachable. */
  resetDesk(): Promise<{ tombstoned: number; seeded: number } | null>;
  /** Forget a window's arranged rect (back to its CSS default corner). */
  resetPanelRect(id: string): void;
  /** Bring a desk window to the front of the focus order. */
  focusPanel(id: string): void;
  /** Present a window on open: a window with a remembered place in the
   * stacking order keeps it (reload-rehydrate); a new one goes on top. */
  presentPanel(id: string): void;
  /** A closed window leaves the stacking order (so reopening presents). */
  retirePanel(id: string): void;
}

export const useDesk = create<DeskState>((set, get) => ({
  items: { ...EMPTY_ITEMS },
  profiles: [],
  projects: [],
  inferenceTargets: [],
  models: [],
  status: {},
  error: "",
  loading: false,
  updatedAt: null,
  positions: loadPositions(),
  zoneWidths: loadZoneWidths(),
  recording: "idle",
  recordingExternal: false,
  recordingStartedAt: null,
  panelRects: initialPanelRects,
  panelSaved: Object.keys(initialPanelRects),
  panelOrder: initialPanelLayout.order,
  panelMin: [],
  panelMax: initialPanelLayout.max,
  divedZone: null,
  draggingId: null,
  setup: null,
  newIds: [],
  editingId: null,
  pullouts: [],
  zoneWindows: loadZoneWindows(),
  zoneViewPrefs: loadZoneViewPrefs(),
  infoWindows: [],
  roadmapWindows: [],
  repositoryWindows: [],
  workbenchWindows: [],
  hoverZoneId: null,
  renamingZoneId: null,
  selectedIds: [],
  askOpen: false,
  chatPersonaId: null,
  toolInspector: null,
  viewMode: loadViewMode(),

  setViewMode(mode) {
    set({ viewMode: mode });
    persistViewMode(mode);
  },

  async refresh() {
    set({ loading: true, error: "" });
    const [
      { items, profiles, projects, inferenceTargets, models, status, error },
      setup,
    ] = await Promise.all([loadAll(), loadSetup()]);
    set({
      items,
      profiles,
      projects,
      inferenceTargets,
      models,
      status,
      error,
      setup,
      loading: false,
      updatedAt: Date.now(),
    });
  },

  async createPrimitive(kind) {
    const posts: Record<string, [string, string, Record<string, unknown>]> = {
      note: ["/api/notes", "note", { title: "New note", body_markdown: "" }],
      decision: [
        "/api/decisions",
        "decision",
        {
          title: "New decision",
          status: "proposed",
          context_markdown: "",
          decision_markdown: "",
          consequences_markdown: "",
          alternatives: [],
        },
      ],
      kb: ["/api/kbs", "kb", { name: "New Knowledge" }],
      // HS-111-09 — born without an emoji: the empty avatar means "wear
      // the automaton sprite" (the server's own default is "" too).
      recipe: ["/api/recipes", "recipe", { name: "New Agent", avatar: "" }],
      zone: ["/api/directories", "directory", { name: "New zone" }],
      workbench: ["/api/workbenches", "workbench", { name: "New Workbench" }],
      // HSM-22-03 — a workflow is born with a real one-step linear graph in
      // the canonical wire shape (never an empty {} the run route must refuse).
      workflow: [
        "/api/workflows",
        "workflow",
        {
          name: "New workflow",
          graph_json: buildLinearGraph(crypto.randomUUID(), "New workflow", [
            { kind: "summarize" },
          ]) as unknown as Record<string, unknown>,
        },
      ],
    };
    const [url, wireKey, body] = posts[kind];
    let createdId: string | null = null;
    try {
      const res = await apiRequest(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      createdId = data?.[wireKey]?.id || null;
    } catch {
      /* the refresh below reports reachability honestly */
    }
    if (createdId && kind !== "zone") {
      // Spawn at stage center (the iPad grammar): the new object appears in
      // front of you and you drag it away.
      const positions = {
        ...get().positions,
        [createdId]: { x: 0.5, y: 0.55 },
      };
      set({ positions });
      savePositions(positions);
    }
    await get().refresh();
    if (createdId) {
      get().markNew(createdId);
      if (kind === "zone") get().setRenamingZone(createdId);
      else if (kind === "workbench") get().openWorkbenchWindow(createdId);
      else get().openEditor(createdId);
    }
  },

  async registerRepository(input) {
    try {
      const { repository } = await registerRepository(input);
      await get().refresh();
      const positions = { ...get().positions, [repository.id]: { x: 0.5, y: 0.55 } };
      set({ positions });
      savePositions(positions);
      get().markNew(repository.id);
      get().openRepositoryWindow(repository.id);
    } catch {
      await get().refresh();
    }
  },

  markNew(id) {
    set({ newIds: [...get().newIds, id] });
    // The beat settles (glow + ring + badge fade) — the HS-71-06 timing.
    setTimeout(() => {
      set({ newIds: get().newIds.filter((x) => x !== id) });
    }, 4500);
  },

  openEditor(id) {
    // The object's own card yields to its editor; other cards keep
    // their seats (windows coexist).
    set({
      editingId: id,
      pullouts: get().pullouts.filter((p) => p.id !== id),
      toolInspector: null,
    });
  },
  closeEditor() {
    set({ editingId: null });
    void get().refresh(); // settle the world to the saved truth
  },

  async updatePrimitive(kind, id, patch) {
    const urls: Record<string, string> = {
      note: `/api/notes/${encodeURIComponent(id)}`,
      decision: `/api/decisions/${encodeURIComponent(id)}`,
      kb: `/api/kbs/${encodeURIComponent(id)}`,
      recipe: `/api/recipes/${encodeURIComponent(id)}`,
      directory: `/api/directories/${encodeURIComponent(id)}`,
      workflow: `/api/workflows/${encodeURIComponent(id)}`,
      project: `/api/projects/${encodeURIComponent(id)}`,
    };
    const url = urls[kind];
    if (!url) return;
    // Optimistic local merge so the world's labels track typing.
    const camel: Record<string, string> = {
      title: "title",
      name: "name",
      body_markdown: "bodyMarkdown",
      context_markdown: "contextMarkdown",
      decision_markdown: "decisionMarkdown",
      consequences_markdown: "consequencesMarkdown",
      decided_at: "decidedAt",
      superseded_by: "supersededBy",
      alternatives: "alternatives",
      status: "status",
      deciders: "deciders",
      tags: "tags",
      role: "role",
      system_prompt: "systemPrompt",
      user_template: "userTemplate",
      tools: "tools",
      kb_id: "kbId",
      profile_id: "profileId",
      avatar: "avatar",
    };
    const itemsKind =
      kind === "directory" ? "directory" : (kind as keyof Items);
    const items = get().items;
    if (items[itemsKind]) {
      set({
        items: {
          ...items,
          [itemsKind]: items[itemsKind].map((it) => {
            if (it.id !== id) return it;
            const next = { ...it };
            for (const [w, v] of Object.entries(patch)) {
              if (camel[w]) (next as any)[camel[w]] = v;
            }
            return next;
          }),
        },
      });
    }
    if (kind === "project" && "name" in patch) {
      set({
        projects: get().projects.map((project) =>
          project.id === id
            ? { ...project, name: String(patch.name) }
            : project,
        ),
      });
    }
    try {
      await apiRequest(url, {
        method: kind === "project" ? "PATCH" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
    } catch {
      /* saves are on-change; the next one retries — the hub dot reports */
    }
  },

  async deletePrimitive(id, kind) {
    const paths: Record<string, string> = {
      note: "notes",
      decision: "decisions",
      kb: "kbs",
      recipe: "recipes",
      directory: "directories",
      chain: "chains",
      workflow: "workflows",
    };
    const path = paths[kind];
    if (!path) return;
    try {
      await apiRequest(`/api/${path}/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
    } catch {
      /* refresh reports reachability and preserves the object on failure */
    }
    get().clearPosition(id);
    set({
      editingId: get().editingId === id ? null : get().editingId,
      pullouts: get().pullouts.filter((pullout) => pullout.id !== id),
      infoWindows: get().infoWindows.filter(
        (window) => window.ref !== qualifiedRef(kind, id) && window.ref !== id,
      ),
      selectedIds: get().selectedIds.filter(
        (ref) => ref !== qualifiedRef(kind, id) && ref !== id,
      ),
    });
    await get().refresh();
  },

  setHoverZone(id) {
    if (get().hoverZoneId !== id) set({ hoverZoneId: id });
  },
  setRenamingZone(id) {
    set({ renamingZoneId: id });
  },
  diveInto(zoneId) {
    set({
      divedZone: zoneId,
      pullouts: [],
      editingId: null,
      toolInspector: null,
    });
  },
  surface() {
    set({ divedZone: null });
  },

  openPullout(id, origin) {
    if (id.startsWith("roadmap:")) {
      get().openRoadmapWindow(id.slice("roadmap:".length), origin);
      return;
    }
    if ((get().items.repository || []).some((repository) => repository.id === id)) {
      get().openRepositoryWindow(id, origin);
      return;
    }
    if ((get().items.workbench || []).some((wb) => wb.id === id)) {
      get().openWorkbenchWindow(id, origin);
      return;
    }
    const projectId = id.startsWith("project:")
      ? id.slice("project:".length)
      : (get().items.project || []).some((project) => project.id === id)
        ? id
        : "";
    if (projectId) {
      void import("./shell").then(({ openSurfaceWhenReady }) =>
        openSurfaceWhenReady("open-project-memory", `project:${projectId}`),
      );
      set({ editingId: null });
      return;
    }
    const open = get().pullouts;
    if (!open.some((p) => p.id === id))
      set({ pullouts: [...open, { id, origin: origin ?? null }] });
    set({ editingId: null });
    get().focusPanel(`pullout:${id}`);
  },
  closePullout(id) {
    const open = get().pullouts;
    if (open.length === 0) return;
    const victim =
      id ??
      // Front-most card: the last pullout panel in the stacking order
      // (cards never focused yet fall back to open order).
      [...open]
        .sort(
          (a, b) =>
            get().panelOrder.indexOf(`pullout:${a.id}`) -
            get().panelOrder.indexOf(`pullout:${b.id}`),
        )
        .pop()?.id;
    set({ pullouts: open.filter((p) => p.id !== victim) });
  },

  openZoneWindow(id, origin) {
    const open = get().zoneWindows;
    if (!open.some((w) => w.id === id)) {
      const next = [...open, { id, origin: origin ?? null }];
      set({ zoneWindows: next });
      persistZoneWindows(next);
    }
    get().focusPanel(`zone:${id}`);
  },
  closeZoneWindow(id) {
    const next = get().zoneWindows.filter((w) => w.id !== id);
    set({ zoneWindows: next });
    persistZoneWindows(next);
  },
  openInfoWindow(ref, origin) {
    const open = get().infoWindows;
    if (!open.some((w) => w.ref === ref))
      set({ infoWindows: [...open, { ref, origin: origin ?? null }] });
    get().focusPanel(`info:${ref}`);
  },
  closeInfoWindow(ref) {
    set({ infoWindows: get().infoWindows.filter((w) => w.ref !== ref) });
  },
  openRoadmapWindow(slug, origin) {
    const open = get().roadmapWindows;
    if (!open.some((window) => window.slug === slug))
      set({ roadmapWindows: [...open, { slug, origin: origin ?? null }] });
    get().focusPanel(`roadmap:${slug}`);
  },
  closeRoadmapWindow(slug) {
    set({ roadmapWindows: get().roadmapWindows.filter((window) => window.slug !== slug) });
  },
  openRepositoryWindow(id, origin) {
    const open = get().repositoryWindows;
    if (!open.some((window) => window.id === id))
      set({ repositoryWindows: [...open, { id, origin: origin ?? null }] });
    get().focusPanel(`repository:${id}`);
  },
  closeRepositoryWindow(id) {
    set({ repositoryWindows: get().repositoryWindows.filter((window) => window.id !== id) });
  },
  openWorkbenchWindow(id, origin) {
    const open = get().workbenchWindows;
    const panelId = `workbench:${id}`;
    if (!open.some((window) => window.id === id)) {
      set({ workbenchWindows: [...open, { id, origin: origin ?? null }] });
      if (!get().panelRects[panelId]) {
        const vw = window.innerWidth || 1280;
        const vh = window.innerHeight || 800;
        const w = Math.min(640, vw - 40);
        const h = Math.min(520, vh - 100);
        get().setPanelRect(panelId, {
          x: Math.round((vw - w) / 2),
          y: Math.round((vh - h) * 0.3),
          w,
          h,
        });
      }
    }
    get().focusPanel(panelId);
  },
  closeWorkbenchWindow(id) {
    set({ workbenchWindows: get().workbenchWindows.filter((window) => window.id !== id) });
  },
  setZoneViewPref(id, pref) {
    const current = get().zoneViewPrefs[id] || {
      view: "icons",
      sort: "name",
      dir: "asc",
    };
    const next = { ...get().zoneViewPrefs, [id]: { ...current, ...pref } };
    set({ zoneViewPrefs: next });
    try {
      localStorage.setItem(ZONE_VIEWS_KEY, JSON.stringify(next));
    } catch {
      /* storage may be unavailable */
    }
  },

  async fileIntoDir(pid, dirId, kind = "note") {
    const ref = pid.includes(":") ? pid : qualifiedRef(kind, pid);
    try {
      await apiRequest(
        `/api/directories/${encodeURIComponent(dirId)}/members/${encodeURIComponent(ref)}`,
        { method: "PUT" },
      );
    } catch {
      /* the refresh reports reachability */
    }
    // Filing forgets a free position (the object lives on the shelf now).
    get().clearPosition(pid);
    await get().refresh();
  },

  async fileIntoKnowledge(ref, kbId) {
    // HS-105-02 — the drop matrix's Add-to-Knowledge verb: the SAME
    // membership PUT the card's Filed strip uses, reversible there.
    try {
      await apiRequest(
        `/api/kbs/${encodeURIComponent(kbId)}/members/${encodeURIComponent(ref)}`,
        { method: "PUT" },
      );
    } catch {
      /* the refresh reports reachability */
    }
    await get().refresh();
  },

  async removeFromDir(pid, dirId, kind = "note") {
    const ref = pid.includes(":") ? pid : qualifiedRef(kind, pid);
    try {
      await apiRequest(
        `/api/directories/${encodeURIComponent(dirId)}/members/${encodeURIComponent(ref)}`,
        { method: "DELETE" },
      );
    } catch {
      /* the refresh reports reachability */
    }
    await get().refresh();
  },

  async answerCoder(agent, sessionId) {
    try {
      const res = await apiRequest("/api/coders/select", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ agent, session_id: sessionId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async runCapability(kind, id, input, inferenceTargetId) {
    const routes = {
      recipe: `/api/recipes/${encodeURIComponent(id)}/run`,
      chain: `/api/chains/${encodeURIComponent(id)}/run`,
      workflow: `/api/workflows/${encodeURIComponent(id)}/run`,
    };
    try {
      const res = await apiRequest(routes[kind], {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input, inference_target_id: inferenceTargetId }),
      });
      const data = await res.json().catch(() => ({}));
      const output = String(data.output || data.error || `HTTP ${res.status}`);
      const artifactId = res.ok ? String(data.artifact_id || "") || null : null;
      // Preserve warnings from older hubs; current hubs refuse unsupported graphs.
      const warning = data.warning ? String(data.warning) : null;
      const invocationId = String(data.invocation_id || "") || null;
      const resultRef =
        String(data.result_ref || data.invocation?.result_ref || "") || null;
      const state = String(
        data.invocation?.state || (res.ok ? "succeeded" : "failed"),
      );
      const actualPlacement =
        data.actual_placement && typeof data.actual_placement === "object"
          ? (data.actual_placement as Record<string, unknown>)
          : data.invocation?.attempts?.at(-1)?.actual_placement || null;
      if (artifactId) {
        // The result is a REAL artifact now — it lands on the desk in
        // front of you, wearing the beat (the HS-73-06 grammar).
        await get().refresh();
        const source = get().positions[id];
        if (source) {
          const positions = {
            ...get().positions,
            [artifactId]: {
              x: Math.min(0.94, source.x + 0.08),
              y: Math.min(0.94, source.y + 0.06),
            },
          };
          set({ positions });
          savePositions(positions);
        }
        get().markNew(artifactId);
      }
      return {
        ok: res.ok,
        output,
        artifactId,
        warning,
        invocationId,
        resultRef,
        state,
        actualPlacement,
      };
    } catch (e) {
      return {
        ok: false,
        output: String(e),
        artifactId: null,
        warning: null,
        invocationId: null,
        resultRef: null,
        state: "failed",
        actualPlacement: null,
      };
    }
  },

  async speakToCoder(agent, sessionId, text) {
    if (!text.trim()) return false;
    try {
      await apiRequest("/api/coders/select", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ agent, session_id: sessionId }),
      });
      const res = await apiRequest("/api/dictation/remote", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text, target_mode: "agent" }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async renameZone(id, name) {
    // Optimistic local rename; the PUT persists it.
    const items = get().items;
    set({
      items: {
        ...items,
        directory: items.directory.map((d) =>
          d.id === id ? { ...d, name, title: name } : d,
        ),
      },
    });
    await get().updatePrimitive("directory", id, { name });
  },

  toggleSelected(id) {
    const cur = get().selectedIds;
    set({
      selectedIds: cur.includes(id)
        ? cur.filter((x) => x !== id)
        : [...cur, id],
    });
  },
  setSelected(ids) {
    set({ selectedIds: ids });
  },
  clearSelection() {
    set({ selectedIds: [], askOpen: false });
  },
  openAsk() {
    // Desk windows coexist (focus, don't destroy): opening the composer
    // settles the in-world editor but leaves sibling windows arranged as
    // the user left them. The Ask composer is the one deliberate carve-out
    // (HSM-16-04): it holds its selection rope, unlike card-open, which
    // now clears the mark on open.
    set({ askOpen: true, editingId: null });
    get().focusPanel("ask");
  },
  closeAsk() {
    set({ askOpen: false });
  },
  openChat(personaId) {
    set({ chatPersonaId: personaId, editingId: null });
    get().focusPanel("chat");
  },
  closeChat() {
    set({ chatPersonaId: null });
  },
  openToolInspector(kind, id) {
    set({ toolInspector: { kind, id }, editingId: null });
    get().focusPanel("inspector");
  },
  closeToolInspector() {
    set({ toolInspector: null });
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
  applyRecordingActivity(activity) {
    if (!activity || typeof activity !== "object") return;
    const s = String((activity as any).state || "").toLowerCase();
    if (s === "meeting_live") {
      const started = get().recording === "recording";
      set({
        recording: "recording",
        // A start this desk initiated is not "live elsewhere": the local
        // start stamps recordingStartedAt just before the frame lands.
        recordingExternal: started
          ? get().recordingExternal
          : get().recordingStartedAt == null,
        recordingStartedAt: get().recordingStartedAt ?? Date.now(),
      });
    } else if (s === "idle" || s === "complete") {
      if (get().recording === "recording")
        set({
          recording: "idle",
          recordingExternal: false,
          recordingStartedAt: null,
        });
    }
  },
  async startRecording() {
    if (get().recording !== "idle") return;
    // The stamp lands before the POST so an early runtime frame still
    // reads this start as local, not "live elsewhere".
    set({ recording: "busy", recordingStartedAt: Date.now() });
    meetingsBeforeRecording = new Set(
      get().items.meeting.map((m: any) => String(m.id)),
    );
    try {
      // /live's exact call — the hub's recorder, never a browser mic.
      await apiRequest("/api/meeting/start", { method: "POST" });
      set({ recording: "recording", recordingExternal: false });
    } catch {
      set({ recording: "idle", recordingStartedAt: null });
    }
  },
  async stopRecording() {
    if (get().recording !== "recording") return;
    set({ recording: "busy" });
    try {
      await apiRequest("/api/meeting/stop", { method: "POST" });
    } catch {
      /* the state frame settles the orb either way */
    }
    set({
      recording: "idle",
      recordingExternal: false,
      recordingStartedAt: null,
    });
    // The finished meeting materializes as an object in front of you.
    await get().refresh();
    const after = get().items.meeting.map((m: any) => String(m.id));
    const fresh = after.find((id: string) => !meetingsBeforeRecording.has(id));
    if (fresh) get().markNew(fresh);
  },
  setZoneWidth(id, width, persist = false) {
    const zoneWidths = { ...get().zoneWidths, [id]: width };
    set({ zoneWidths });
    if (persist) saveZoneWidths(zoneWidths);
  },
  setPanelRect(id, rect, persist = false) {
    const panelRects = { ...get().panelRects, [id]: rect };
    const panelSaved =
      persist && !get().panelSaved.includes(id)
        ? [...get().panelSaved, id]
        : get().panelSaved;
    set({ panelRects, panelSaved });
    if (persist)
      savePanelLayout(panelRects, panelSaved, get().panelOrder, get().panelMax);
  },
  resetPanelRect(id) {
    const { [id]: _dropped, ...rest } = get().panelRects;
    const panelSaved = get().panelSaved.filter((x) => x !== id);
    set({ panelRects: rest, panelSaved });
    savePanelLayout(rest, panelSaved, get().panelOrder, get().panelMax);
  },
  focusPanel(id) {
    const order = compactPanelOrder([
      ...get().panelOrder.filter((x) => x !== id),
      id,
    ]);
    set({ panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, get().panelMax);
  },
  presentPanel(id) {
    if (get().panelOrder.includes(id)) return;
    get().focusPanel(id);
  },
  retirePanel(id) {
    if (!get().panelOrder.includes(id)) return;
    const order = get().panelOrder.filter((x) => x !== id);
    set({ panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, get().panelMax);
  },
  minimizePanel(id) {
    if (get().panelMin.includes(id)) return;
    // Session-scoped by design (HS-97-03): never persisted.
    set({ panelMin: [...get().panelMin, id] });
  },
  restorePanel(id) {
    const panelMin = get().panelMin.filter((x) => x !== id);
    const order = compactPanelOrder([
      ...get().panelOrder.filter((x) => x !== id),
      id,
    ]);
    set({ panelMin, panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, get().panelMax);
  },
  toggleMaximizePanel(id) {
    const has = get().panelMax.includes(id);
    const panelMax = has
      ? get().panelMax.filter((x) => x !== id)
      : [...get().panelMax, id];
    const order = compactPanelOrder([
      ...get().panelOrder.filter((x) => x !== id),
      id,
    ]);
    set({ panelMax, panelOrder: order });
    savePanelLayout(get().panelRects, get().panelSaved, order, panelMax);
  },
  resetLayout() {
    set({
      panelRects: {},
      panelSaved: [],
      panelOrder: [],
      panelMin: [],
      panelMax: [],
    });
    savePanelLayout({}, [], [], []);
  },

  async seedDesk() {
    try {
      const res = await apiRequest("/api/desk/seed", { method: "POST" });
      if (!res.ok) return false;
    } catch {
      return false;
    }
    await get().refresh();
    return true;
  },

  async resetDesk() {
    let counts: { tombstoned: number; seeded: number };
    try {
      const res = await apiRequest("/api/desk/reset", { method: "POST" });
      if (!res.ok) return null;
      const data = await res.json().catch(() => ({}));
      counts = {
        tombstoned: Number(data?.tombstoned_total ?? 0),
        seeded: Number(data?.seeded_total ?? 0),
      };
    } catch {
      return null;
    }
    // The dead desk's ghost layout: positions, rects, widths, and open
    // sets keyed by ids that no longer live. Sweep the persisted keys
    // (resetLayout covers only the panel layout) and the in-memory
    // mirrors, then settle to the seeded truth.
    for (const key of GHOST_LAYOUT_KEYS) {
      try {
        localStorage.removeItem(key);
      } catch {
        /* storage may be unavailable; the ghost just lingers until it is */
      }
    }
    set({
      positions: {},
      zoneWidths: {},
      panelRects: {},
      panelSaved: [],
      panelOrder: [],
      panelMin: [],
      panelMax: [],
      pullouts: [],
      zoneWindows: [],
      zoneViewPrefs: {},
      infoWindows: [],
      roadmapWindows: [],
      repositoryWindows: [],
  workbenchWindows: [],
      divedZone: null,
      editingId: null,
      selectedIds: [],
    });
    await get().refresh();
    return counts;
  },
}));

/** HS-112-03 — every localStorage key that layouts the desk by object
 * id; a reset sweeps them all (the pre-charter survey's ghost list). */
export const GHOST_LAYOUT_KEYS = [
  "hs.diorama.pos",
  "hs.desk.panels",
  "hs.desk.zonew",
  "hs.desk.zone-views",
  "hs.desk.zone-windows",
  "hs.desk.open-windows",
] as const;
