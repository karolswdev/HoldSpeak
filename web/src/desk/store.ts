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

function loadPanelRects(): Record<string, PanelRect> {
  try {
    return JSON.parse(localStorage.getItem(PANEL_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function savePanelRects(rects: Record<string, PanelRect>, keep: string[]) {
  try {
    const out: Record<string, PanelRect> = {};
    for (const id of keep) if (rects[id]) out[id] = rects[id];
    localStorage.setItem(PANEL_KEY, JSON.stringify(out));
  } catch {
    /* storage may be unavailable; arranging just won't persist */
  }
}

const initialPanelRects = loadPanelRects();

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
  /** The object whose pull-out is open, + one level of back (HS-73-04). */
  pulloutId: string | null;
  pulloutBackId: string | null;
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
  /** Window focus order; the last id renders in front. */
  panelOrder: string[];

  refresh(): Promise<void>;
  /** Create in-world (HS-73-03): instant POST, spawn at center, NEW beat,
   * editor open. The object IS the editor — no modal, ever. */
  createPrimitive(
    kind: "note" | "kb" | "recipe" | "zone" | "workflow",
  ): Promise<void>;
  markNew(id: string): void;
  openEditor(id: string): void;
  closeEditor(): void;
  /** Autosaving field update through the real PUT routes. */
  updatePrimitive(
    kind: string,
    id: string,
    patch: Record<string, unknown>,
  ): Promise<void>;
  renameZone(id: string, name: string): Promise<void>;
  openPullout(id: string): void;
  closePullout(): void;
  setHoverZone(id: string | null): void;
  setRenamingZone(id: string | null): void;
  diveInto(zoneId: string): void;
  surface(): void;
  /** File a primitive into a directory (the real add-only PUT). */
  fileIntoDir(pid: string, dirId: string, kind?: string): Promise<void>;
  /** The toggle-off half (the legacy toggleFile parity). */
  removeFromDir(pid: string, dirId: string, kind?: string): Promise<void>;
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
  /** Forget a window's arranged rect (back to its CSS default corner). */
  resetPanelRect(id: string): void;
  /** Bring a desk window to the front of the focus order. */
  focusPanel(id: string): void;
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
  panelOrder: [],
  divedZone: null,
  draggingId: null,
  setup: null,
  newIds: [],
  editingId: null,
  pulloutId: null,
  pulloutBackId: null,
  hoverZoneId: null,
  renamingZoneId: null,
  selectedIds: [],
  askOpen: false,
  chatPersonaId: null,
  toolInspector: null,

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
      kb: ["/api/kbs", "kb", { name: "New Knowledge" }],
      recipe: ["/api/recipes", "recipe", { name: "New Persona", avatar: "🤖" }],
      zone: ["/api/directories", "directory", { name: "New zone" }],
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
      else get().openEditor(createdId);
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
    set({
      editingId: id,
      pulloutId: null,
      pulloutBackId: null,
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
      kb: `/api/kbs/${encodeURIComponent(id)}`,
      recipe: `/api/recipes/${encodeURIComponent(id)}`,
      directory: `/api/directories/${encodeURIComponent(id)}`,
      workflow: `/api/workflows/${encodeURIComponent(id)}`,
    };
    const url = urls[kind];
    if (!url) return;
    // Optimistic local merge so the world's labels track typing.
    const camel: Record<string, string> = {
      title: "title",
      name: "name",
      body_markdown: "bodyMarkdown",
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
    try {
      await apiRequest(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
    } catch {
      /* saves are on-change; the next one retries — the hub dot reports */
    }
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
      pulloutId: null,
      pulloutBackId: null,
      editingId: null,
      toolInspector: null,
    });
  },
  surface() {
    set({ divedZone: null });
  },

  openPullout(id) {
    const current = get().pulloutId;
    set({
      pulloutId: id,
      // One-deep stack: opening from inside a pull-out remembers where to
      // go back to (an artifact row inside a meeting's drawer).
      pulloutBackId: current && current !== id ? current : null,
      editingId: null,
    });
    get().focusPanel("pullout");
  },
  closePullout() {
    set({ pulloutId: null, pulloutBackId: null });
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
    // the user left them; the selection stays visible behind the panel.
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
    if (persist) savePanelRects(panelRects, panelSaved);
  },
  resetPanelRect(id) {
    const { [id]: _dropped, ...rest } = get().panelRects;
    const panelSaved = get().panelSaved.filter((x) => x !== id);
    set({ panelRects: rest, panelSaved });
    savePanelRects(rest, panelSaved);
  },
  focusPanel(id) {
    const order = get().panelOrder.filter((x) => x !== id);
    order.push(id);
    set({ panelOrder: order });
  },
}));
