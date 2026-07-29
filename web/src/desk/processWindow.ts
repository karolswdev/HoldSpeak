/** HS-109-06 — cursor-aware, read-only kernel process watcher. */
import { create } from "zustand";
import { apiRequest } from "../lib/api";
import {
  foldProcessWindow,
  mergeProcessEvents,
  operationIdsInSections,
  type KernelProcessEvent,
  type KernelProcessObject,
  type ProcessSection,
} from "./processWindowReducer";

export const PROCESS_POLL_MS = 1_500;
export const PROCESS_EVENT_BATCH = 500;
export const PROCESS_READ_BATCH = 100;
export const PROCESS_CHECKPOINT_KEY = "hs.process-window.v1";

export interface ProcessCheckpoint {
  cursor: number;
  events: KernelProcessEvent[];
  objects: KernelProcessObject[];
}

interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

const EMPTY_CHECKPOINT: ProcessCheckpoint = { cursor: 0, events: [], objects: [] };

function browserStorage(): StorageLike | undefined {
  try {
    return typeof localStorage === "undefined" ? undefined : localStorage;
  } catch {
    return undefined;
  }
}

export function loadProcessCheckpoint(
  storage: StorageLike | undefined = browserStorage(),
): ProcessCheckpoint {
  try {
    const value = JSON.parse(storage?.getItem(PROCESS_CHECKPOINT_KEY) || "null");
    if (!value || typeof value !== "object") return { ...EMPTY_CHECKPOINT };
    return {
      cursor: Math.max(0, Number(value.cursor || 0)),
      events: Array.isArray(value.events) ? mergeProcessEvents([], value.events) : [],
      objects: Array.isArray(value.objects) ? value.objects : [],
    };
  } catch {
    return { ...EMPTY_CHECKPOINT };
  }
}

export function saveProcessCheckpoint(
  checkpoint: ProcessCheckpoint,
  storage: StorageLike | undefined = browserStorage(),
): void {
  try {
    storage?.setItem(PROCESS_CHECKPOINT_KEY, JSON.stringify(checkpoint));
  } catch {
    /* Storage is an optimization. The authenticated journal remains truth. */
  }
}

interface ProcessWindowState extends ProcessCheckpoint {
  sections: ProcessSection[];
  loading: boolean;
  inflight: boolean;
  error: string;
  started: boolean;
  start(): void;
  stop(): void;
  poll(): Promise<void>;
}

function operationId(object: KernelProcessObject): string {
  const operation = object.operation ?? {};
  return String(operation.operation_id || object.ref || "").replace(/^operation:/, "");
}

function mergeObjects(
  standing: KernelProcessObject[],
  incoming: KernelProcessObject[],
): KernelProcessObject[] {
  const values = new Map<string, KernelProcessObject>();
  for (const object of [...standing, ...incoming]) {
    const id = operationId(object);
    if (id) values.set(id, object);
  }
  return [...values.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, object]) => object);
}

async function jsonRequest<T>(url: string): Promise<T> {
  const response = await apiRequest(url, { headers: { Accept: "application/json" } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.error || body?.detail || `HTTP ${response.status}`;
    throw new Error(String(detail));
  }
  return body as T;
}

function eventsUrl(cursor: number): string {
  const query = new URLSearchParams({
    after_cursor: String(cursor),
    stream: "operations",
    limit: String(PROCESS_EVENT_BATCH),
  });
  return `/api/kernel/events?${query}`;
}

function readUrl(ids: string[]): string {
  const query = new URLSearchParams({ view: "process" });
  ids.forEach((id) => query.append("refs", `operation:${id}`));
  return `/api/kernel/read?${query}`;
}

export function createProcessWindowStore(
  storage: StorageLike | undefined = browserStorage(),
) {
  const checkpoint = loadProcessCheckpoint(storage);
  let timer: ReturnType<typeof setInterval> | null = null;

  return create<ProcessWindowState>((set, get) => ({
    ...checkpoint,
    sections: foldProcessWindow(checkpoint.events, checkpoint.objects),
    loading: checkpoint.events.length === 0,
    inflight: false,
    error: "",
    started: false,

    start() {
      if (get().started) return;
      set({ started: true });
      void get().poll();
      timer = setInterval(() => void get().poll(), PROCESS_POLL_MS);
    },

    stop() {
      if (timer !== null) {
        clearInterval(timer);
        timer = null;
      }
      set({ started: false });
    },

    async poll() {
      if (get().inflight) return;
      set({ inflight: true, error: "" });
      try {
        let cursor = get().cursor;
        let events = get().events;

        // The route currently returns its journal default (100), despite the
        // requested 500 cap. Continue to an empty page rather than treating a
        // short page as end-of-journal.
        for (;;) {
          const page = await jsonRequest<{
            cursor?: number;
            events?: KernelProcessEvent[];
          }>(eventsUrl(cursor));
          const batch = Array.isArray(page.events) ? page.events : [];
          const nextCursor = Math.max(cursor, Number(page.cursor || cursor));
          if (batch.length === 0 || nextCursor === cursor) break;
          events = mergeProcessEvents(events, batch);
          cursor = nextCursor;
          // A hard restart after any journal page resumes at the exact page
          // boundary, with the fold summaries required to reconstruct rows.
          saveProcessCheckpoint({ cursor, events, objects: get().objects }, storage);
        }

        const ids = events.map((event) => event.operation_id).filter(Boolean);
        let objects = get().objects;
        for (let offset = 0; offset < ids.length; offset += PROCESS_READ_BATCH) {
          const body = await jsonRequest<{ objects?: KernelProcessObject[] }>(
            readUrl(ids.slice(offset, offset + PROCESS_READ_BATCH)),
          );
          objects = mergeObjects(objects, Array.isArray(body.objects) ? body.objects : []);
        }

        const sections = foldProcessWindow(events, objects);
        const retained = operationIdsInSections(sections);
        events = events.filter((event) => retained.has(event.operation_id));
        objects = objects.filter((object) => retained.has(operationId(object)));
        const next = { cursor, events, objects };
        saveProcessCheckpoint(next, storage);
        set({ ...next, sections, loading: false, error: "" });
      } catch (reason) {
        set({
          loading: false,
          error: reason instanceof Error ? reason.message : "Kernel unavailable",
        });
      } finally {
        set({ inflight: false });
      }
    },
  }));
}

export const useProcessWindow = createProcessWindowStore();
