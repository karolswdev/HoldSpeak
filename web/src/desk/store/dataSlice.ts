/** Data slice (HS-117-02): items, profiles, projects, inferenceTargets,
 * models, status, error, loading, updatedAt, setup + refresh,
 * createPrimitive, updatePrimitive, deletePrimitive, renameZone,
 * fileIntoDir, removeFromDir, fileIntoKnowledge, seedDesk, resetDesk,
 * registerRepository, answerCoder, speakToCoder, runCapability. */
import { apiFetch, apiRequest, newDeliveryId } from "../../lib/api";
import {
  clearWriteFailure,
  currentWriteFailure,
  reportWriteFailure,
  writeFailureReason,
} from "../hooks/useWriteReceipt";
import { PRIMITIVES, type PrimitiveKind } from "../../lib/primitives";
import {
  EMPTY_ITEMS,
  fromWireCreated,
  loadAll,
  qualifiedRef,
  type Items,
} from "../api";
import { buildLinearGraph } from "../graph";
import { loadSetup } from "../setup";
import { registerRepository as registerRepositoryApi } from "../repository";
import { faceChangeCount, nextFreeZoneName } from "../zoneName";
import { useNamePrompt } from "../chromeState";
import type { DeskState, SliceCreator, ZoneRenameError } from "./types";
import { GHOST_LAYOUT_KEYS } from "./types";

/** PHILO-8-01 — default zone names posted whose refresh has not landed. */
const zoneNamesInFlight = new Set<string>();

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
    // HS-151-05 — thread rename via PATCH.
    thread: `/api/threads/${encodeURIComponent(id)}`,
  } satisfies Partial<Record<PrimitiveKind, string>>;
  return (urls as Partial<Record<string, string>>)[kind] ?? null;
}

/** Meetings on the desk when a local recording started (NEW-beat diff). */
let meetingsBeforeRecording = new Set<string>();

type PrimitiveWriteState = {
  version: number;
  pending: boolean;
  rollback?: { token: number };
};

type RollbackProtection = {
  kind: string;
  id: string;
  version: number;
  token: number;
};

type IdentifiedItem = { id: string };

function writeKey(kind: string, id: string): string {
  return `${kind}:${id}`;
}

function replaceItemsBucket<K extends keyof Items>(
  items: Items,
  kind: K,
  bucket: Items[K],
): void {
  items[kind] = bucket;
}

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
  | "adoptCreated"
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

export const createDataSlice: SliceCreator<DataSlice> = (set, get) => {
  const primitiveWrites = new Map<string, PrimitiveWriteState>();
  let rollbackToken = 0;

  const mergeRefreshItems = (
    incoming: Items,
    current: Items,
    snapshot: ReadonlyMap<string, PrimitiveWriteState>,
    status: DeskState["status"],
    rollbackProtection?: RollbackProtection,
  ): Items => {
    const merged = { ...incoming } as Items;
    for (const kind of Object.keys(incoming) as Array<keyof Items>) {
      const incomingBucket = (incoming[kind] ?? []) as unknown as IdentifiedItem[];
      // A kind the store has not loaded yet has no current bucket: nothing
      // there is protected, and the incoming bucket stands as read.
      const currentBucket = (current[kind] ?? []) as unknown as IdentifiedItem[];
      const protectedItems = new Map<string, IdentifiedItem>();
      const kindName = String(kind);
      for (const item of currentBucket) {
        const id = item.id;
        const key = writeKey(kindName, id);
        const before = snapshot.get(key);
        const after = primitiveWrites.get(key);
        const protectedByWrite = Boolean(
          after &&
            (after.version > (before?.version || 0) ||
              (before?.pending && after.version === before.version)),
        );
        const protectedByRollback = Boolean(
          rollbackProtection &&
            rollbackProtection.kind === kindName &&
            rollbackProtection.id === id &&
            rollbackProtection.version === after?.version &&
            rollbackProtection.token === after?.rollback?.token &&
            status[kind] === "unreachable",
        );
        if (protectedByWrite || protectedByRollback) {
          protectedItems.set(id, item);
        }
      }
      if (!protectedItems.size) continue;
      const incomingIds = new Set(incomingBucket.map((item) => item.id));
      const bucket = incomingBucket.map((item) => {
        return protectedItems.get(item.id) || item;
      });
      for (const [id, item] of protectedItems) {
        if (!incomingIds.has(id)) bucket.push(item);
      }
      replaceItemsBucket(merged, kind, bucket as Items[typeof kind]);
    }
    return merged;
  };

  const runRefresh = async (rollbackProtection?: RollbackProtection) => {
    const refreshSnapshot = new Map(
      [...primitiveWrites].map(([key, state]) => [key, { ...state }]),
    );
    set({ loading: true, error: "" });
    let setupCause: unknown = null;
    const [
      { items, profiles, projects, inferenceTargets, models, status, error, failed: collectionFailed },
      setup,
    ] = await Promise.all([loadAll(), loadSetup((cause) => { setupCause = cause; })]);
    // PHILO-13-13 C3-W: a Desk that keeps its frame through a lost setup read
    // (DeskApp) names that read here, like any collection read.
    const failed = collectionFailed ??
      (setup === null && setupCause !== null ? { label: "Setup", cause: setupCause } : null);
    // PHILO-3-01 — a failed collection read is named on the face (the desk
    // receipt line), with Retry; a pending write (CREATE, SAVE, ...) keeps its
    // receipt and its Retry: a read failure never replaces it.
    const standing = currentWriteFailure();
    const readReceipt = !standing || standing.verb.startsWith("READ ");
    if (failed) {
      if (readReceipt)
        reportWriteFailure(`READ ${failed.label}`, failed.cause, () => void get().refresh());
    } else if (standing && standing.verb.startsWith("READ ")) {
      clearWriteFailure();
    }
    const mergedItems = mergeRefreshItems(
      items,
      get().items,
      refreshSnapshot,
      status,
      rollbackProtection,
    );
    set({
      items: mergedItems,
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
    if (rollbackProtection) {
      const key = writeKey(rollbackProtection.kind, rollbackProtection.id);
      const state = primitiveWrites.get(key);
      if (
        state?.version === rollbackProtection.version &&
        state.rollback?.token === rollbackProtection.token
      ) {
        primitiveWrites.set(key, { ...state, rollback: undefined });
      }
    }
  };

  /** One press, one record: the creates in flight, and the object each New
   * verb made last (see createPrimitive). */
  const createsInFlight = new Map<string, Promise<void>>();
  const freshCreates = new Map<string, string>();
  const createKey = (kind: string, overrides: Record<string, unknown>) =>
    `${kind}:${JSON.stringify(overrides)}`;

  const createNow = async (
    kind: Parameters<DeskState["createPrimitive"]>[0],
    overrides: Record<string, unknown> = {},
    /** The hub has answered the create (its window is open, or its refusal
     * is about to be named): the press is no longer in flight. */
    answered: () => void = () => undefined,
  ): Promise<void> => {
    // HS-130-09 — a Workbench is chosen BEFORE it is persisted. The create
    // gesture opens the pre-persistence chooser; exactly one of its exits
    // persists exactly one Workbench (no orphaned blank record).
    if (kind === "workbench") {
      get().openNewWorkbenchChooser();
      return;
    }
    // PHILO-13-08 (B3) — a decision is named BEFORE it is persisted. With no
    // title from the caller the palette asks it inline; closing the palette
    // writes nothing, so no `New decision` placeholder is ever born (F9).
    if (kind === "decision" && !String(overrides.title ?? "").trim()) {
      useNamePrompt.getState().ask({
        label: "Decision title",
        submit: (title) => void get().createPrimitive("decision", { ...overrides, title }),
      });
      return;
    }
    const posts = {
      note: ["/api/notes", "note", { title: "New note", body_markdown: "" }],
      decision: [
        "/api/decisions",
        "decision",
        {
          // PHILO-15-09 (B12): the owner's own decision is DECIDED; it is
          // not a Needs row and not "to review".
          status: "accepted",
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
    const [url, wireKey, defaults] = posts[kind];
    // PHILO-8-01 — a zone with no name from the caller takes the first free
    // default name ("New zone", "New zone 2", …) by the hub's rule; a name
    // the caller passed is never replaced. A name already posted but not yet
    // in the store (its refresh is still running) counts as taken, so two
    // quick presses never post the same name.
    const picked =
      kind === "zone" && overrides.name === undefined
        ? nextFreeZoneName([
            ...(get().items.directory ?? []),
            ...[...zoneNamesInFlight].map((name) => ({ name })),
          ])
        : null;
    if (picked) zoneNamesInFlight.add(picked);
    const release = () => {
      if (picked) zoneNamesInFlight.delete(picked);
    };
    const body: Record<string, unknown> = picked ? { ...defaults, name: picked } : defaults;
    const faceAtPress = faceChangeCount();
    let createdId: string | null = null;
    let created: unknown = null;
    // HS-132-06 — a refused create is named, not swallowed; RETRY re-issues
    // the same create. PHILO-8-01 — RETRY refreshes the store first, so a
    // zone made elsewhere (MCP, another tab) is seen and the free name is
    // picked again; a second refusal is still named.
    const retry = () =>
      void get()
        .refresh()
        .catch(() => undefined)
        .then(() => get().createPrimitive(kind, overrides));
    try {
      const res = await apiRequest(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, ...overrides }),
      });
      if (!res.ok) {
        release();
        answered();
        await reportCreateFailure(kind, res, retry, get);
        return;
      }
      const data = await res.json().catch(() => ({}));
      created = data?.[wireKey] ?? null;
      createdId = data?.[wireKey]?.id || null;
      clearWriteFailure();
    } catch (cause) {
      release();
      answered();
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
    const open = (id: string) => {
      freshCreates.set(createKey(kind, overrides), id);
      get().markNew(id);
      // "workbench" never reaches here — it returns early to the
      // pre-persistence chooser (HS-130-09).
      if (kind === "zone") {
        // PHILO-8-01 — only on the face where New Zone was pressed.
        if (faceChangeCount() === faceAtPress) get().setRenamingZone(id);
      }
      // PHILO-3-01 — a decision has no inline editor; its face is the
      // DecisionPullout, which opens in Edit for a new decision.
      else if (kind === "decision") get().openPullout(id);
      else get().openEditor(id);
    };
    // The window opens at once, from the create answer. Before, it waited
    // for a full desk read (every collection; 2 to 5 s on a desk with a
    // roadmap), so the press showed nothing and the record was made unseen.
    // A zone is not a window: its name field waits for the read, by the
    // PHILO-8-01 face rule above.
    const opened =
      createdId !== null &&
      kind !== "zone" &&
      get().adoptCreated(kind, created) !== null;
    if (opened && createdId) {
      open(createdId);
      answered();
    }
    try {
      await get().refresh();
    } finally {
      release();
    }
    if (createdId && !opened) open(createdId);
  };

  return {
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

  refresh() {
    return runRefresh();
  },

  adoptCreated(kind, wire) {
    const made = fromWireCreated(kind, wire);
    if (!made) return null;
    const bucket = (get().items[kind] ?? []) as unknown as IdentifiedItem[];
    const next = bucket.some((item) => item.id === made.id)
      ? bucket.map((item) => (item.id === made.id ? made : item))
      : [...bucket, made];
    // A desk read that started before this create does not hold the new
    // record: the write version keeps the object through that read
    // (mergeRefreshItems), so its window does not close under the owner.
    const key = writeKey(kind, made.id);
    primitiveWrites.set(key, {
      version: (primitiveWrites.get(key)?.version || 0) + 1,
      pending: false,
    });
    set({ items: { ...get().items, [kind]: next } as Items });
    return made.id;
  },

  async createPrimitive(kind, overrides = {}) {
    // One press, one record. A second press of the same New verb while its
    // create is in flight, or while the window it just opened is still new
    // (the NEW beat) and open, makes nothing: it puts that window in front.
    // Before, two quick presses made two records and showed one editor.
    // A zone is not a window and keeps its own rule (PHILO-8-01); a
    // workbench and an unnamed decision write nothing here.
    const writes =
      kind !== "zone" &&
      kind !== "workbench" &&
      !(kind === "decision" && !String(overrides.title ?? "").trim());
    if (!writes) return createNow(kind, overrides);
    const key = createKey(kind, overrides);
    const fresh = freshCreates.get(key);
    if (fresh && get().newIds.includes(fresh)) {
      if (kind === "decision") {
        if (get().pullouts.some((p) => p.id === fresh)) {
          get().openPullout(fresh);
          return;
        }
      } else if (get().editingId === fresh) {
        get().restorePanel(`editor:${kind}:${fresh}`);
        return;
      }
    }
    const flying = createsInFlight.get(key);
    if (flying) return flying;
    const landed = () => createsInFlight.delete(key);
    const run = createNow(kind, overrides, landed).finally(landed);
    createsInFlight.set(key, run);
    return run;
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
      reportWriteFailure(verb, `NO UPDATE PATH FOR ${kind.toUpperCase()}`, undefined, qualifiedRef(kind, id));
      return false;
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
      avatar: "avatar",
    };
    const itemsKind =
      kind === "directory" ? "directory" : (kind as keyof Items);
    const items = get().items;
    const writeKind = String(itemsKind);
    const key = writeKey(writeKind, id);
    const currentItem = items[itemsKind]?.find((item) => item.id === id);
    const previousItem = currentItem ? { ...currentItem } : undefined;
    const previousState = primitiveWrites.get(key);
    const writeVersion = (previousState?.version || 0) + 1;
    primitiveWrites.set(key, { version: writeVersion, pending: true });
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
      const state = primitiveWrites.get(key);
      // A refusal from an older request is superseded. It must not restore its
      // prior value, publish a stale Retry, or start a refresh over a newer
      // write.
      if (!state || state.version !== writeVersion) return;
      const token = ++rollbackToken;
      const rollback = previousItem
        ? { token }
        : undefined;
      primitiveWrites.set(key, {
        version: writeVersion,
        pending: false,
        rollback,
      });
      if (previousItem) {
        const latestItems = get().items;
        const latestBucket = latestItems[itemsKind];
        if (latestBucket) {
          set({
            items: {
              ...latestItems,
              [itemsKind]: latestBucket.map((item) =>
                item.id === id ? previousItem : item,
              ),
            },
          });
        }
      }
      reportWriteFailure(
        verb,
        cause,
        () => void get().updatePrimitive(kind, id, patch, verb),
        qualifiedRef(kind, id),
      );
      await runRefresh(
        rollback
          ? { kind: writeKind, id, version: writeVersion, token }
          : undefined,
      );
    };
    try {
      const res = await apiRequest(url, {
        // The project and thread routes take PATCH; a PUT to a thread is a 405.
        method: kind === "project" || kind === "thread" ? "PATCH" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) {
        await refused(res);
        return false;
      }
      const state = primitiveWrites.get(key);
      if (!state || state.version !== writeVersion) return true; // it landed; a newer write owns the receipt
      primitiveWrites.set(key, { ...state, pending: false });
      clearWriteFailure(qualifiedRef(kind, id));
      // HS-202-02 — the hub answered ok: the object is KEPT, and the
      // editor's foot may say so (04-sober-eye.md, rank 5).
      set({ keptAt: { ...get().keptAt, [id]: Date.now() } });
      return true;
    } catch (cause) {
      await refused(cause);
      return false;
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
    if (!path) return false;
    try {
      // apiFetch, not apiRequest: a refusal (4xx/5xx) throws with its named
      // reason; apiRequest answered the Response and the refusal went unseen.
      await apiFetch(`/api/${path}/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
    } catch (cause) {
      // PHILO-8-02 round three — a refused delete is named on the desk's
      // receipt line with Retry; the object stays and so does its card.
      reportWriteFailure(
        "DELETE",
        cause,
        () => void get().deletePrimitive(id, kind),
        qualifiedRef(kind, id),
      );
      void get().refresh();
      return false;
    }
    // Round four/seven: a landed delete clears only a failure about its own
    // object (the channel's subject rule), never an unrelated one.
    clearWriteFailure(qualifiedRef(kind, id));
    get().clearPosition(id);
    set({
      editingId: get().editingId === id ? null : get().editingId,
      pullouts: get().pullouts.filter(
        (pullout) => pullout.id !== id && pullout.id !== qualifiedRef(kind, id),
      ),
      infoWindows: get().infoWindows.filter(
        (window) => window.ref !== qualifiedRef(kind, id) && window.ref !== id,
      ),
      selectedIds: get().selectedIds.filter(
        (ref) => ref !== qualifiedRef(kind, id) && ref !== id,
      ),
    });
    await get().refresh();
    return true;
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
    const trimmed = name.trim();
    // PHILO-8-01 (the owner's ratified canvas, 2026-09-26) — a refused rename
    // is never silent. While the zone's field is open the refusal is its chip;
    // when the field has closed (he left the face) it is the desk's write
    // receipt, `RENAME ZONE`, with Retry.
    const refuse = (error: Omit<ZoneRenameError, "zoneId" | "name">) => {
      set({
        items: {
          ...get().items,
          directory: get().items.directory.map((d) =>
            d.id === id ? { ...d, name: oldName, title: oldName } : d,
          ),
        },
      });
      if (get().renamingZoneId === id) {
        set({ zoneRenameError: { ...error, zoneId: id, name: trimmed } });
      } else {
        reportWriteFailure(
          "RENAME ZONE",
          error.label,
          () => void get().renameZone(id, trimmed),
          qualifiedRef("directory", id),
        );
      }
    };
    try {
      const res = await apiRequest(
        `/api/directories/${encodeURIComponent(id)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: trimmed }),
        },
      );
      if (res.ok) {
        // Round seven: a landed rename answers its own earlier refusal.
        clearWriteFailure(qualifiedRef("directory", id));
        return;
      }
      const body = await res.json().catch(() => ({}));
      if (res.status === 409) {
        const existingName = body?.existing_name || trimmed;
        refuse({
          code: "zone_name_taken",
          label: "NAME TAKEN",
          detail: `A zone named "${existingName}" already exists`,
        });
      } else {
        refuse({
          code: res.status === 422 ? "invalid_arguments" : `http_${res.status}`,
          label: "NOT SAVED",
          detail: String(body?.error || writeFailureReason(res)),
        });
      }
    } catch (cause) {
      refuse({ code: "not_saved", label: "NOT SAVED", detail: writeFailureReason(cause) });
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
      windowsById: {},
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
  };
};
