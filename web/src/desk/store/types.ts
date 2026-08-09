/** Shared types for the desk store slices (HS-117-02). */
import type { PrimitiveKind } from "../../lib/primitives";
import type {
  InferenceTarget,
  Items,
  ProjectSummary,
  Status,
} from "../api";
import type { SetupStatus } from "../setup";

export interface UnitPos {
  x: number;
  y: number;
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

/** HS-93-08 -- the semantic list mode is the SAME Desk, keyboard-first. */
export type DeskView = "spatial" | "list";

/** HS-105-03 -- a zone window's remembered expression. */
export interface ZoneViewPref {
  view: "icons" | "list";
  sort: "name" | "kind" | "modified";
  dir: "asc" | "desc";
}

/** HS-112-03 -- every localStorage key that layouts the desk by object
 * id; a reset sweeps them all (the pre-charter survey's ghost list). */
export const GHOST_LAYOUT_KEYS = [
  "hs.diorama.pos",
  "hs.desk.panels",
  "hs.desk.zonew",
  "hs.desk.zone-views",
  "hs.desk.zone-windows",
  "hs.desk.open-windows",
] as const;

/** HS-105-01 -- the phone's density altitude: above this count, a compact
 * desk with NO saved choice leads with the list; an explicit user choice
 * (URL or saved key) always wins. */
export const COMPACT_LIST_THRESHOLD = 16;

/** Resolve an unset view choice against the loaded desk's density. */
export function defaultViewFor(
  mode: DeskView | "unset",
  objectCount: number,
  compact: boolean,
): DeskView {
  if (mode === "list" || mode === "spatial") return mode;
  return compact && objectCount > COMPACT_LIST_THRESHOLD ? "list" : "spatial";
}

/** The full desk state interface -- the union of every slice. */
export interface DeskState {
  items: Items;
  profiles: Array<Record<string, unknown>>;
  projects: ProjectSummary[];
  inferenceTargets: InferenceTarget[];
  /** HS-83-03 -- the hub's runnable models (the ask allow-list).
   * HS-130-06: one entry per destination, keyed by `id` (name may repeat). */
  models: Array<{
    id: string;
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
  /** The client point that invoked the editor's separate window path. */
  editorOrigin: { x: number; y: number } | null;
  /** Open object cards (HS-101 round 9): real windows -- they COEXIST,
   * each remembering the tap point it opened from (the origin its
   * open/close motion flies to). Order is open order; the panel order
   * decides stacking. */
  pullouts: { id: string; origin: { x: number; y: number } | null }[];
  /** HS-105-03 -- open zone windows (drawers opened into real desk
   * windows). They coexist like pullouts and persist across reload
   * (`hs.desk.zone-windows`, the HS-103-01 restoration rule). */
  zoneWindows: { id: string; origin: { x: number; y: number } | null }[];
  /** Per-zone remembered expression: view + sort (`hs.desk.zone-views`).
   * The window remembers -- that is what makes it a window. */
  zoneViewPrefs: Record<string, ZoneViewPref>;
  /** HS-105-04 -- open Info cards (transient inspection windows; they
   * coexist but do not persist across reload). Ref is `kind:id`, bare
   * id, or `zone:<id>`. */
  infoWindows: { ref: string; origin: { x: number; y: number } | null }[];
  /** Delivery Workbench projects open as their own Desk application window. */
  roadmapWindows: { slug: string; origin: { x: number; y: number } | null }[];
  /** Registered git sources open as physical desk drawers. */
  repositoryWindows: { id: string; origin: { x: number; y: number } | null }[];
  /** Agent workbenches open as their own desk windows. */
  workbenchWindows: { id: string; origin: { x: number; y: number } | null }[];
  /** The pre-persistence "new workbench" chooser (HS-130-09): open before
   * any record exists so exactly one Workbench is persisted per creation
   * gesture. Null when closed. */
  newWorkbenchChooser: { origin: { x: number; y: number } | null } | null;
  /** The zone a live drag is hovering (the drop affordance, HS-73-05). */
  hoverZoneId: string | null;
  /** The freshly-created zone whose rename is focused. */
  renamingZoneId: string | null;
  /** Inline error shown during zone rename (409 name taken). */
  zoneRenameError: string | null;
  /** The lasso'd/selected objects -- the Ask atom's context (HSM-16-04). */
  selectedIds: string[];
  /** The Ask composer is open (in-world, desk visible -- never a modal). */
  askOpen: boolean;
  /** HS-83-02 -- the persona whose CONVERSATION is open (null = none). */
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
  /** Panel ids whose rect the user arranged -- the persisted subset. */
  panelSaved: string[];
  /** Window focus order; the last id renders in front. Persisted
   * (HS-97-03: the arrangement is sacred, stacking included). */
  panelOrder: string[];
  /** Minimized windows (parked in the tray/dock), session-scoped. */
  panelMin: string[];
  /** Maximized windows (full stage; the saved rect is kept), persisted. */
  panelMax: string[];
  /** HS-93-08 -- which expression of the Desk renders (spatial or list). */
  viewMode: DeskView | "unset";

  refresh(): Promise<void>;
  /** Switch Desk expression; persists and mirrors `?view=list` in the URL. */
  setViewMode(mode: DeskView): void;
  /** Create in-world (HS-73-03): instant POST, spawn at center, NEW beat,
   * editor open. The object IS the editor -- no modal, ever. */
  createPrimitive(
    kind: "note" | "decision" | "kb" | "recipe" | "zone" | "workflow" | "workbench",
    overrides?: Record<string, unknown>,
  ): Promise<void>;
  /** Register a Delivery source (or local worktree) as a repository drawer. */
  registerRepository(input: { sourceId?: string; path?: string; label?: string }): Promise<void>;
  markNew(id: string): void;
  openEditor(id: string, origin?: { x: number; y: number }): void;
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
  clearZoneRenameError(): void;
  /** Open an object card. A second object opens a SECOND card (windows
   * coexist); reopening an open object focuses its card. `origin` is
   * the client point the open gesture happened at (the card flies out
   * of it and back into it on close). */
  openPullout(id: string, origin?: { x: number; y: number }): void;
  /** Close one card by object id; with no id, the front-most card. */
  closePullout(id?: string): void;
  /** HS-105-03 -- open a drawer as a real desk window (the OPEN grammar;
   * dive survives only as the Focus verb). Reopening focuses. */
  openZoneWindow(id: string, origin?: { x: number; y: number }): void;
  closeZoneWindow(id: string): void;
  /** Remember a zone window's expression (view/sort), persisted. */
  setZoneViewPref(id: string, pref: Partial<ZoneViewPref>): void;
  /** HS-105-04 -- Info on everything (right-click -> Info). */
  openInfoWindow(ref: string, origin?: { x: number; y: number }): void;
  closeInfoWindow(ref: string): void;
  openRoadmapWindow(slug: string, origin?: { x: number; y: number }): void;
  closeRoadmapWindow(slug: string): void;
  openRepositoryWindow(id: string, origin?: { x: number; y: number }): void;
  closeRepositoryWindow(id: string): void;
  openWorkbenchWindow(id: string, origin?: { x: number; y: number }): void;
  closeWorkbenchWindow(id: string): void;
  /** Open the pre-persistence workbench chooser (no record created yet). */
  openNewWorkbenchChooser(origin?: { x: number; y: number }): void;
  /** Dismiss the pre-persistence workbench chooser. */
  closeNewWorkbenchChooser(): void;
  setHoverZone(id: string | null): void;
  setRenamingZone(id: string | null): void;
  diveInto(zoneId: string): void;
  surface(): void;
  /** File a primitive into a directory (the real add-only PUT). */
  fileIntoDir(pid: string, dirId: string, kind?: string): Promise<void>;
  /** The toggle-off half (the legacy toggleFile parity). */
  removeFromDir(pid: string, dirId: string, kind?: string): Promise<void>;
  /** HS-105-02 -- the drop matrix's Add-to-Knowledge verb (the same
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
  /** HS-112-03 -- apply the packaged architect's-desk seed (idempotent;
   * additive by id, never destructive). */
  seedDesk(): Promise<boolean>;
  /** HS-112-03 -- the desk's first destructive verb: tombstone every desk
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

/** Zustand slice creator signature. */
export type SliceCreator<T> = (
  set: (partial: Partial<DeskState> | ((state: DeskState) => Partial<DeskState>)) => void,
  get: () => DeskState,
  api: { setState: (partial: Partial<DeskState>) => void; getState: () => DeskState },
) => T;
