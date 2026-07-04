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
import { buildLinearGraph } from "./graph";
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

  refresh(): Promise<void>;
  /** Create in-world (HS-73-03): instant POST, spawn at center, NEW beat,
   * editor open. The object IS the editor — no modal, ever. */
  createPrimitive(kind: "note" | "kb" | "agent" | "zone" | "workflow"): Promise<void>;
  markNew(id: string): void;
  openEditor(id: string): void;
  closeEditor(): void;
  /** Autosaving field update through the real PUT routes. */
  updatePrimitive(kind: string, id: string, patch: Record<string, unknown>): Promise<void>;
  renameZone(id: string, name: string): Promise<void>;
  openPullout(id: string): void;
  closePullout(): void;
  setHoverZone(id: string | null): void;
  setRenamingZone(id: string | null): void;
  diveInto(zoneId: string): void;
  surface(): void;
  /** File a primitive into a directory (the real add-only PUT). */
  fileIntoDir(pid: string, dirId: string): Promise<void>;
  /** The toggle-off half (the legacy toggleFile parity). */
  removeFromDir(pid: string, dirId: string): Promise<void>;
  /** Select a coder session as the dictation target (answerCoder parity). */
  answerCoder(agent: string, sessionId: string): Promise<boolean>;
  /** Speak straight into the waiting coder (HS-78-03): select the
   * session, then inject the transcript through the remote seam. */
  speakToCoder(agent: string, sessionId: string, text: string): Promise<boolean>;
  /** Run a capability through the real route; the persisted result
   * MATERIALIZES on the desk (HS-74-03: refresh + the NEW beat). */
  runCapability(
    kind: "agent" | "chain" | "workflow",
    id: string,
    input: string,
  ): Promise<{ ok: boolean; output: string; artifactId: string | null; warning: string | null }>;
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
  newIds: [],
  editingId: null,
  pulloutId: null,
  pulloutBackId: null,
  hoverZoneId: null,
  renamingZoneId: null,

  async refresh() {
    set({ loading: true, error: "" });
    const [{ items, profiles, status, error }, setup] = await Promise.all([
      loadAll(),
      loadSetup(),
    ]);
    set({ items, profiles, status, error, setup, loading: false, updatedAt: Date.now() });
  },

  async createPrimitive(kind) {
    const posts: Record<string, [string, string, Record<string, unknown>]> = {
      note: ["/api/notes", "note", { title: "New note", body_markdown: "" }],
      kb: ["/api/kbs", "kb", { name: "New KB" }],
      agent: ["/api/agents", "agent", { name: "New agent", avatar: "🤖" }],
      zone: ["/api/directories", "directory", { name: "New zone" }],
      // HSM-22-03 — a workflow is born with a real one-step linear graph in
      // the canonical wire shape (never an empty {} the run route must refuse).
      workflow: ["/api/workflows", "workflow", {
        name: "New workflow",
        graph_json: buildLinearGraph(
          crypto.randomUUID(), "New workflow", [{ kind: "summarize" }],
        ) as unknown as Record<string, unknown>,
      }],
    };
    const [url, wireKey, body] = posts[kind];
    let createdId: string | null = null;
    try {
      const res = await fetch(url, {
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
      const positions = { ...get().positions, [createdId]: { x: 0.5, y: 0.55 } };
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
    set({ editingId: id, pulloutId: null, pulloutBackId: null });
  },
  closeEditor() {
    set({ editingId: null });
    void get().refresh(); // settle the world to the saved truth
  },

  async updatePrimitive(kind, id, patch) {
    const urls: Record<string, string> = {
      note: `/api/notes/${encodeURIComponent(id)}`,
      kb: `/api/kbs/${encodeURIComponent(id)}`,
      agent: `/api/agents/${encodeURIComponent(id)}`,
      directory: `/api/directories/${encodeURIComponent(id)}`,
      workflow: `/api/workflows/${encodeURIComponent(id)}`,
    };
    const url = urls[kind];
    if (!url) return;
    // Optimistic local merge so the world's labels track typing.
    const camel: Record<string, string> = {
      title: "title", name: "name", body_markdown: "bodyMarkdown", tags: "tags",
      role: "role", system_prompt: "systemPrompt", user_template: "userTemplate",
      tools: "tools", kb_id: "kbId", profile_id: "profileId",
    };
    const itemsKind = kind === "directory" ? "directory" : (kind as keyof Items);
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
      await fetch(url, {
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
    set({ divedZone: zoneId, pulloutId: null, pulloutBackId: null, editingId: null });
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
  },
  closePullout() {
    set({ pulloutId: null, pulloutBackId: null });
  },

  async fileIntoDir(pid, dirId) {
    try {
      await fetch(
        `/api/directories/${encodeURIComponent(dirId)}/members/${encodeURIComponent(pid)}`,
        { method: "PUT" },
      );
    } catch {
      /* the refresh reports reachability */
    }
    // Filing forgets a free position (the object lives on the shelf now).
    get().clearPosition(pid);
    await get().refresh();
  },

  async removeFromDir(pid, dirId) {
    try {
      await fetch(
        `/api/directories/${encodeURIComponent(dirId)}/members/${encodeURIComponent(pid)}`,
        { method: "DELETE" },
      );
    } catch {
      /* the refresh reports reachability */
    }
    await get().refresh();
  },

  async answerCoder(agent, sessionId) {
    try {
      const res = await fetch("/api/coders/select", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ agent, session_id: sessionId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async runCapability(kind, id, input) {
    const routes = {
      agent: `/api/agents/${encodeURIComponent(id)}/run`,
      chain: `/api/chains/${encodeURIComponent(id)}/run`,
      workflow: `/api/workflows/${encodeURIComponent(id)}/run`,
    };
    try {
      const res = await fetch(routes[kind], {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input }),
      });
      const data = await res.json().catch(() => ({}));
      const output = String(data.output || data.error || `HTTP ${res.status}`);
      const artifactId = res.ok ? String(data.artifact_id || "") || null : null;
      // HSM-22-03 — the hub's honest refusal (a graph it ran as the prompt
      // fallback) rides the response as `warning`; surface it, never drop it.
      const warning = data.warning ? String(data.warning) : null;
      if (artifactId) {
        // The result is a REAL artifact now — it lands on the desk in
        // front of you, wearing the beat (the HS-73-06 grammar).
        await get().refresh();
        get().markNew(artifactId);
      }
      return { ok: res.ok, output, artifactId, warning };
    } catch (e) {
      return { ok: false, output: String(e), artifactId: null, warning: null };
    }
  },

  async speakToCoder(agent, sessionId, text) {
    if (!text.trim()) return false;
    try {
      await fetch("/api/coders/select", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ agent, session_id: sessionId }),
      });
      const res = await fetch("/api/dictation/remote", {
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
