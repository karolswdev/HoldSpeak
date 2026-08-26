/** Data slice (HS-117-02): items, profiles, projects, inferenceTargets,
 * models, status, error, loading, updatedAt, setup + refresh,
 * createPrimitive, updatePrimitive, deletePrimitive, renameZone,
 * fileIntoDir, removeFromDir, fileIntoKnowledge, seedDesk, resetDesk,
 * registerRepository, answerCoder, speakToCoder, runCapability. */
import { apiRequest, newDeliveryId } from "../../lib/api";
import {
  clearWriteFailure,
  reportWriteFailure,
} from "../hooks/useWriteReceipt";
import { PRIMITIVES, type PrimitiveKind } from "../../lib/primitives";
import {
  EMPTY_ITEMS,
  loadAll,
  qualifiedRef,
  type Items,
} from "../api";
import { buildLinearGraph } from "../graph";
import { loadSetup } from "../setup";
import { registerRepository as registerRepositoryApi } from "../repository";
import type { DeskState, SliceCreator } from "./types";
import { GHOST_LAYOUT_KEYS } from "./types";

// ---- localStorage helpers (positions, zone widths) ----------------------

const POS_KEY = "hs.diorama.pos";
const ZONE_W_KEY = "hs.desk.zonew";

function loadPositions(): Record<string, { x: number; y: number }> {
  try {
    return JSON.parse(localStorage.getItem(POS_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function savePositions(positions: Record<string, { x: number; y: number }>) {
  try {
    localStorage.setItem(POS_KEY, JSON.stringify(positions));
  } catch {
    /* storage may be unavailable; arranging just won't persist */
  }
}

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

/**
 * HS-132-06 — one named refusal for a create the hub would not take. It
 * reaches the desk write channel, which every desk surface renders in flow
 * (the system bar backstops the floor), so the press is never swallowed.
 */
async function reportCreateFailure(
  kind: string,
  cause: unknown,
  retry: () => void,
  get: () => DeskState,
) {
  reportWriteFailure(`CREATE ${kind}`, cause, retry);
  await get().refresh();
}

/** HS-132-07 — the ONE table of real update paths.
 *
 * Get Info offered Rename for every kind while this map covered seven, so
 * meeting/chain/workbench renames fell through `if (!url) return;` and did
 * nothing. The map is the honesty gate now: a kind is listed here only when
 * a hub route really takes the write, and the Info card asks this table
 * before it offers the affordance (`renameLock`).
 */
export function primitiveUpdateUrl(kind: string, id: string): string | null {
  const urls = {
    note: `/api/notes/${encodeURIComponent(id)}`,
    decision: `/api/decisions/${encodeURIComponent(id)}`,
    kb: `/api/kbs/${encodeURIComponent(id)}`,
    recipe: `/api/recipes/${encodeURIComponent(id)}`,
    directory: `/api/directories/${encodeURIComponent(id)}`,
    workflow: `/api/workflows/${encodeURIComponent(id)}`,
    project: `/api/projects/${encodeURIComponent(id)}`,
    // HS-132-07 — routes that existed on the hub but not in this map.
    chain: `/api/chains/${encodeURIComponent(id)}`,
    workbench: `/api/workbenches/${encodeURIComponent(id)}`,
    // HS-132-07 — the rename route this story added to the hub.
    meeting: `/api/meetings/${encodeURIComponent(id)}`,
  } satisfies Partial<Record<PrimitiveKind, string>>;
  return (urls as Partial<Record<string, string>>)[kind] ?? null;
}

/** Meetings on the desk when a local recording started (NEW-beat diff). */
let meetingsBeforeRecording = new Set<string>();

// ---- the slice ----------------------------------------------------------

export type DataSlice = Pick<
  DeskState,
  | "items"
  | "profiles"
  | "projects"
  | "inferenceTargets"
  | "models"
  | "status"
  | "error"
  | "loading"
  | "updatedAt"
  | "setup"
  | "positions"
  | "zoneWidths"
  | "refresh"
  | "createPrimitive"
  | "registerRepository"
  | "updatePrimitive"
  | "deletePrimitive"
  | "renameZone"
  | "clearZoneRenameError"
  | "zoneRenameError"
  | "fileIntoDir"
  | "removeFromDir"
  | "fileIntoKnowledge"
  | "answerCoder"
  | "speakToCoder"
  | "runCapability"
  | "seedDesk"
  | "resetDesk"
  | "setPosition"
  | "persistPositions"
  | "clearPosition"
  | "tidyDesk"
  | "setZoneWidth"
>;

export const createDataSlice: SliceCreator<DataSlice> = (set, get) => ({
  items: { ...EMPTY_ITEMS },
  profiles: [],
  projects: [],
  inferenceTargets: [],
  models: [],
  status: {},
  error: "",
  loading: false,
  updatedAt: null,
  setup: null,
  positions: loadPositions(),
  zoneWidths: loadZoneWidths(),
  zoneRenameError: null,

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

  async createPrimitive(kind, overrides = {}) {
    // HS-130-09 — a Workbench is chosen BEFORE it is persisted. The create
    // gesture opens the pre-persistence chooser; exactly one of its exits
    // persists exactly one Workbench (no orphaned blank record).
    if (kind === "workbench") {
      get().openNewWorkbenchChooser();
      return;
    }
    const posts = {
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
      recipe: ["/api/recipes", "recipe", { name: "New Agent", avatar: "" }],
      zone: ["/api/directories", "directory", { name: "New zone" }],
      workbench: ["/api/workbenches", "workbench", { name: "New Workbench" }],
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
    } satisfies Record<string, [string, string, Record<string, unknown>]>;
    const [url, wireKey, body] = posts[kind];
    let createdId: string | null = null;
    // HS-132-06 — a refused create is named, not swallowed; RETRY re-issues
    // the exact same create.
    const retry = () => void get().createPrimitive(kind, overrides);
    try {
      const res = await apiRequest(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, ...overrides }),
      });
      if (!res.ok) {
        await reportCreateFailure(kind, res, retry, get);
        return;
      }
      const data = await res.json().catch(() => ({}));
      createdId = data?.[wireKey]?.id || null;
      clearWriteFailure();
    } catch (cause) {
      await reportCreateFailure(kind, cause, retry, get);
      return;
    }
    if (createdId && kind !== "zone") {
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
      // "workbench" never reaches here — it returns early to the
      // pre-persistence chooser (HS-130-09).
      if (kind === "zone") get().setRenamingZone(createdId);
      else get().openEditor(createdId);
    }
  },

  async registerRepository(input) {
    try {
      const { repository } = await registerRepositoryApi(input);
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

  async updatePrimitive(kind, id, patch, verb = "SAVE") {
    const url = primitiveUpdateUrl(kind, id);
    if (!url) {
      // HS-132-07 — a kind with no update path is never offered an edit
      // (see `renameLock` in infoContract). Reaching here anyway is a wiring
      // fault, and it is named instead of swallowed.
      reportWriteFailure(verb, `NO UPDATE PATH FOR ${kind.toUpperCase()}`);
      return;
    }
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
              if (camel[w]) (next as Record<string, unknown>)[camel[w]] = v;
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
    // HS-132-07 — the optimistic patch above is a PROMISE about the hub. A
    // refused write names itself in the desk's one receipt channel and the
    // desk re-reads, so the surface never keeps a name the hub rejected.
    const refused = async (cause: unknown) => {
      reportWriteFailure(verb, cause, () =>
        void get().updatePrimitive(kind, id, patch, verb),
      );
      await get().refresh();
    };
    try {
      const res = await apiRequest(url, {
        method: kind === "project" ? "PATCH" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) {
        await refused(res);
        return;
      }
      clearWriteFailure();
    } catch (cause) {
      await refused(cause);
    }
  },

  async deletePrimitive(id, kind) {
    const paths = {
      note: "notes",
      decision: "decisions",
      kb: "kbs",
      recipe: "recipes",
      directory: "directories",
      chain: "chains",
      workflow: "workflows",
    } satisfies Partial<Record<PrimitiveKind, string>>;
    const path = (paths as Partial<Record<string, string>>)[kind];
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

  async renameZone(id, name) {
    // Clear any prior rename error.
    set({ zoneRenameError: null });
    // Optimistic local rename; the PUT persists it.
    const items = get().items;
    const oldZone = items.directory.find((d) => d.id === id);
    const oldName = oldZone?.name ?? name;
    set({
      items: {
        ...items,
        directory: items.directory.map((d) =>
          d.id === id ? { ...d, name, title: name } : d,
        ),
      },
    });
    try {
      const trimmed = name.trim();
      const res = await apiRequest(
        `/api/directories/${encodeURIComponent(id)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: trimmed }),
        },
      );
      if (res.status === 409) {
        // Name taken -- revert optimistic update and show error.
        const body = await res.json();
        const existingName = body.existing_name || trimmed;
        set({
          zoneRenameError: `A zone named "${existingName}" already exists`,
          items: {
            ...get().items,
            directory: get().items.directory.map((d) =>
              d.id === id ? { ...d, name: oldName, title: oldName } : d,
            ),
          },
        });
      } else if (res.status === 422) {
        // Validation error -- revert.
        set({
          items: {
            ...get().items,
            directory: get().items.directory.map((d) =>
              d.id === id ? { ...d, name: oldName, title: oldName } : d,
            ),
          },
        });
      }
    } catch {
      // Network error -- revert silently.
      set({
        items: {
          ...get().items,
          directory: get().items.directory.map((d) =>
            d.id === id ? { ...d, name: oldName, title: oldName } : d,
          ),
        },
      });
    }
  },
  clearZoneRenameError() {
    set({ zoneRenameError: null });
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
    get().clearPosition(pid);
    await get().refresh();
  },

  async fileIntoKnowledge(ref, kbId) {
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
        body: JSON.stringify({
          text,
          target_mode: "agent",
          delivery_id: newDeliveryId(),
        }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async runCapability(kind, id, input) {
    const routes = {
      recipe: `/api/recipes/${encodeURIComponent(id)}/run`,
      chain: `/api/chains/${encodeURIComponent(id)}/run`,
      workflow: `/api/workflows/${encodeURIComponent(id)}/run`,
    };
    try {
      const res = await apiRequest(routes[kind], {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input }),
      });
      const data = await res.json().catch(() => ({}));
      const output = String(data.output || data.error || `HTTP ${res.status}`);
      const artifactId = res.ok ? String(data.artifact_id || "") || null : null;
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
  setZoneWidth(id, width, persist = false) {
    const zoneWidths = { ...get().zoneWidths, [id]: width };
    set({ zoneWidths });
    if (persist) saveZoneWidths(zoneWidths);
  },

  async seedDesk() {
    // HS-132-06 — the seed's refusal reaches the desk's write channel, so
    // the empty floor never swallows the press.
    const retry = () => void get().seedDesk();
    try {
      const res = await apiRequest("/api/desk/seed", { method: "POST" });
      if (!res.ok) {
        reportWriteFailure("SEED DESK", res, retry);
        return false;
      }
    } catch (cause) {
      reportWriteFailure("SEED DESK", cause, retry);
      return false;
    }
    clearWriteFailure();
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
});
