import type {
  DeskState,
  PanelRect,
  WindowInstance,
  ZoneViewPref,
} from "./types";

/** A hard-cut workspace contract. Older Desk window keys are intentionally
 * ignored: this is the sole persisted document for window lifecycle state.
 *
 * PHILO-13-07 (B2, "the Desk remembers") adds optional sections to the same
 * v1 document; a document written before B2 reads as "none open" for each.
 * No version bump: every new field is optional and additive. */
export const DESK_WORKSPACE_STORAGE_KEY = "hs.desk.workspace.v1";
export const DESK_WORKSPACE_VERSION = 1 as const;

const PANEL_ORDER_LIMIT = 100;

export interface DeskWorkspaceDocumentV1 {
  version: typeof DESK_WORKSPACE_VERSION;
  windowsById: Record<string, WindowInstance>;
  panel: {
    rects: Record<string, PanelRect>;
    order: string[];
    max: string[];
    /** PHILO-13-12 (C2) — zoom's remembered rect per window (optional:
     * a document written before C2 reads as "fills the work band"). */
    zoom?: Record<string, PanelRect>;
    /** PHILO-13-07 (B2) — minimized windows come back minimized. */
    min?: string[];
  };
  zoneWindows: string[];
  zoneViewPrefs: Record<string, ZoneViewPref>;
  /** PHILO-13-07 (B2) — the open object windows, each by its key, in open
   * order. A closed window leaves its list (close means gone). */
  windows?: DeskWorkspaceWindows;
  /** PHILO-13-07 (B2) — the Chair's four windows (written by
   * `chair/chairWindows.ts`): the closed ones and the phone's one window. */
  chair?: { closed: string[]; phone: string };
  /** PHILO-13-07 (B2) — the screen he was on (written by `chairState.ts`). */
  screen?: "chair" | "floor";
  /** PHILO-13-07 (B2) — unsent text, keyed by its field AND its object
   * (`people/1on1/<person>`), so a draft never follows to another object.
   * A draft clears when its write lands; restore never saves or sends. */
  drafts?: Record<string, string>;
  /** PHILO-13-07 (B2) — a window's place (the person and tab, the Room's
   * update), keyed like a draft. */
  places?: Record<string, string>;
}

export interface DeskWorkspaceWindows {
  pullouts: string[];
  info: string[];
  roadmap: string[];
  repository: string[];
  workbench: string[];
}

const DRAFT_KEY_LIMIT = 200;
const DRAFT_VALUE_LIMIT = 50_000;
const DRAFT_COUNT_LIMIT = 100;

const emptyWorkspace = (): DeskWorkspaceDocumentV1 => ({
  version: DESK_WORKSPACE_VERSION,
  windowsById: {},
  panel: { rects: {}, order: [], max: [] },
  zoneWindows: [],
  zoneViewPrefs: {},
});

const isPanelId = (value: unknown): value is string =>
  typeof value === "string" && /^[A-Za-z0-9:_-]+$/.test(value);

const isPanelRect = (value: unknown): value is PanelRect => {
  if (!value || typeof value !== "object") return false;
  const rect = value as PanelRect;
  return [rect.x, rect.y, rect.w, rect.h].every(Number.isFinite) &&
    rect.w > 0 && rect.h > 0;
};

const compactIds = (values: unknown, limit = PANEL_ORDER_LIMIT): string[] => {
  if (!Array.isArray(values)) return [];
  const unique = Array.from(new Set(values.filter(isPanelId)));
  return unique.length > limit ? unique.slice(-limit) : unique;
};

/** Object refs as the openers give them (`decision:d1`, `zone:z1`, a slug). */
const compactRefs = (values: unknown, limit = PANEL_ORDER_LIMIT): string[] => {
  if (!Array.isArray(values)) return [];
  const refs = values.filter(
    (value): value is string =>
      typeof value === "string" && value.length > 0 && value.length <= DRAFT_KEY_LIMIT,
  );
  const unique = Array.from(new Set(refs));
  return unique.length > limit ? unique.slice(-limit) : unique;
};

const parseWindowLists = (value: unknown): DeskWorkspaceWindows => {
  const raw = value && typeof value === "object" ? value as Partial<DeskWorkspaceWindows> : {};
  return {
    pullouts: compactRefs(raw.pullouts),
    info: compactRefs(raw.info),
    roadmap: compactRefs(raw.roadmap),
    repository: compactRefs(raw.repository),
    workbench: compactRefs(raw.workbench),
  };
};

const parseTextMap = (value: unknown): Record<string, string> => {
  if (!value || typeof value !== "object") return {};
  const entries = Object.entries(value).filter(
    ([key, text]) =>
      key.length > 0 && key.length <= DRAFT_KEY_LIMIT &&
      typeof text === "string" && text.length > 0 && text.length <= DRAFT_VALUE_LIMIT,
  ) as [string, string][];
  return Object.fromEntries(entries.slice(-DRAFT_COUNT_LIMIT));
};

const parseChair = (value: unknown): { closed: string[]; phone: string } | undefined => {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as { closed?: unknown; phone?: unknown };
  return {
    closed: compactIds(raw.closed),
    phone: typeof raw.phone === "string" && (raw.phone === "" || isPanelId(raw.phone)) ? raw.phone : "chair:needs",
  };
};

const isZoneViewPref = (value: unknown): value is ZoneViewPref => {
  if (!value || typeof value !== "object") return false;
  const pref = value as ZoneViewPref;
  return (
    (pref.view === "icons" || pref.view === "list") &&
    (pref.sort === "name" || pref.sort === "kind" || pref.sort === "modified") &&
    (pref.dir === "asc" || pref.dir === "desc")
  );
};

function parseWindows(value: unknown): Record<string, WindowInstance> {
  if (!value || typeof value !== "object") return {};
  const windows: Record<string, WindowInstance> = {};
  for (const [id, raw] of Object.entries(value)) {
    if (!isPanelId(id) || !raw || typeof raw !== "object") continue;
    const candidate = raw as Partial<WindowInstance>;
    if (
      candidate.id !== id ||
      candidate.kind !== "surface" ||
      typeof candidate.applicationKey !== "string" ||
      (candidate.scope !== null && typeof candidate.scope !== "string") ||
      candidate.persistence !== "workspace"
    ) continue;
    windows[id] = candidate as WindowInstance;
  }
  return windows;
}

export function loadDeskWorkspace(): DeskWorkspaceDocumentV1 {
  try {
    const raw: unknown = JSON.parse(
      localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "null",
    );
    if (!raw || typeof raw !== "object") return emptyWorkspace();
    const candidate = raw as Partial<DeskWorkspaceDocumentV1>;
    if (candidate.version !== DESK_WORKSPACE_VERSION)
      return emptyWorkspace();

    const panel = candidate.panel && typeof candidate.panel === "object"
      ? candidate.panel
      : { rects: {}, order: [], max: [] };
    const rects = Object.fromEntries(
      Object.entries(panel.rects && typeof panel.rects === "object" ? panel.rects : {})
        .filter(([id, rect]) => isPanelId(id) && isPanelRect(rect)),
    ) as Record<string, PanelRect>;
    const zoom = Object.fromEntries(
      Object.entries(panel.zoom && typeof panel.zoom === "object" ? panel.zoom : {})
        .filter(([id, rect]) => isPanelId(id) && isPanelRect(rect)),
    ) as Record<string, PanelRect>;
    const zoneViewPrefs = Object.fromEntries(
      Object.entries(
        candidate.zoneViewPrefs && typeof candidate.zoneViewPrefs === "object"
          ? candidate.zoneViewPrefs
          : {},
      ).filter(([id, pref]) => isPanelId(id) && isZoneViewPref(pref)),
    ) as Record<string, ZoneViewPref>;

    const chair = parseChair(candidate.chair);
    return {
      version: DESK_WORKSPACE_VERSION,
      windowsById: parseWindows(candidate.windowsById),
      panel: {
        rects,
        order: compactIds(panel.order),
        max: compactIds(panel.max),
        ...(Object.keys(zoom).length ? { zoom } : {}),
        min: compactIds(panel.min),
      },
      zoneWindows: compactIds(candidate.zoneWindows),
      zoneViewPrefs,
      windows: parseWindowLists(candidate.windows),
      ...(chair ? { chair } : {}),
      ...(candidate.screen === "chair" || candidate.screen === "floor"
        ? { screen: candidate.screen }
        : {}),
      drafts: parseTextMap(candidate.drafts),
      places: parseTextMap(candidate.places),
    };
  } catch {
    return emptyWorkspace();
  }
}

type WorkspaceState = Pick<
  DeskState,
  | "windowsById"
  | "panelRects"
  | "panelSaved"
  | "panelOrder"
  | "panelMax"
  | "zoneWindows"
  | "zoneViewPrefs"
> & {
  panelZoom?: Record<string, PanelRect>;
  panelMin?: string[];
  pullouts?: DeskState["pullouts"];
  infoWindows?: DeskState["infoWindows"];
  roadmapWindows?: DeskState["roadmapWindows"];
  repositoryWindows?: DeskState["repositoryWindows"];
  workbenchWindows?: DeskState["workbenchWindows"];
  drafts?: Record<string, string>;
  places?: Record<string, string>;
};

/** The sections other stores own (the Chair's windows, the screen): the
 * desk compositor's save keeps them as they are in the stored document. */
function storedSections(): Pick<DeskWorkspaceDocumentV1, "chair" | "screen"> {
  const stored = loadDeskWorkspace();
  return {
    ...(stored.chair ? { chair: stored.chair } : {}),
    ...(stored.screen ? { screen: stored.screen } : {}),
  };
}

/** PHILO-13-07 (B2) — a store outside the desk compositor writes its own
 * section of the one document (read, replace that section, write). */
export function saveDeskWorkspaceSection(
  section: Pick<DeskWorkspaceDocumentV1, "chair" | "screen">,
): void {
  try {
    const raw: unknown = JSON.parse(
      localStorage.getItem(DESK_WORKSPACE_STORAGE_KEY) || "null",
    );
    const base = raw && typeof raw === "object" &&
      (raw as { version?: unknown }).version === DESK_WORKSPACE_VERSION
      ? raw as DeskWorkspaceDocumentV1
      : emptyWorkspace();
    localStorage.setItem(
      DESK_WORKSPACE_STORAGE_KEY,
      JSON.stringify({ ...base, ...section }),
    );
  } catch {
    /* storage may be unavailable; the live store remains authoritative */
  }
}

export function saveDeskWorkspace(state: WorkspaceState): void {
  const rects: Record<string, PanelRect> = {};
  for (const id of state.panelSaved) {
    const rect = state.panelRects[id];
    if (rect && isPanelId(id) && isPanelRect(rect)) rects[id] = rect;
  }
  const zoom: Record<string, PanelRect> = {};
  for (const [id, rect] of Object.entries(state.panelZoom ?? {})) {
    if (isPanelId(id) && isPanelRect(rect)) zoom[id] = rect;
  }
  const document: DeskWorkspaceDocumentV1 = {
    version: DESK_WORKSPACE_VERSION,
    windowsById: state.windowsById,
    panel: {
      rects,
      order: compactIds(state.panelOrder),
      max: compactIds(state.panelMax),
      ...(Object.keys(zoom).length ? { zoom } : {}),
      min: compactIds(state.panelMin ?? []),
    },
    zoneWindows: state.zoneWindows.map((window) => window.id),
    zoneViewPrefs: state.zoneViewPrefs,
    windows: {
      pullouts: compactRefs((state.pullouts ?? []).map((w) => w.id)),
      info: compactRefs((state.infoWindows ?? []).map((w) => w.ref)),
      roadmap: compactRefs((state.roadmapWindows ?? []).map((w) => w.slug)),
      repository: compactRefs((state.repositoryWindows ?? []).map((w) => w.id)),
      workbench: compactRefs((state.workbenchWindows ?? []).map((w) => w.id)),
    },
    ...storedSections(),
    drafts: parseTextMap(state.drafts ?? {}),
    places: parseTextMap(state.places ?? {}),
  };
  try {
    localStorage.setItem(DESK_WORKSPACE_STORAGE_KEY, JSON.stringify(document));
  } catch {
    /* storage may be unavailable; the live compositor remains authoritative */
  }
}
