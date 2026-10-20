import { apiFetch } from "../lib/api";
import type { WindowUndo, WindowUndoEntry, WindowUndoState } from "./used";

interface HubWindow {
  id: string;
  object_ref?: string | null;
  x?: string | number | null;
  y?: string | number | null;
  w?: string | number | null;
  h?: string | number | null;
  minimized?: boolean;
  room?: string | null;
  revision: number;
}

interface WindowList {
  windows: HubWindow[];
}

export class WindowUndoStale extends Error {
  constructor() {
    super("A window changed after Ask arranged it. The later change was kept.");
    this.name = "WindowUndoStale";
  }
}

const geometryOf = (row: WindowUndoState | HubWindow): Record<string, string | number> | null => {
  if ("geometry" in row && row.geometry) return row.geometry;
  const value = row as HubWindow;
  if (value.x == null || value.y == null || value.w == null || value.h == null) return null;
  return { x: value.x, y: value.y, w: value.w, h: value.h };
};

const same = (a: unknown, b: unknown): boolean => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);

const refresh = async (): Promise<Map<string, HubWindow>> => {
  const answer = await apiFetch<WindowList>("/api/desk/windows");
  return new Map((answer.windows ?? []).map((row) => [row.id, row]));
};

const expectedRevision = (row: HubWindow | undefined): number => {
  if (!row) throw new WindowUndoStale();
  return row.revision;
};

/** Restore the exact window state captured for one Ask trace.
 *
 * Every write carries the revision observed after the model's write.  If the
 * owner moved a window in the meantime, the hub refuses the write and this
 * function leaves that newer placement alone.
 */
export async function restoreWindowUndo(undo: WindowUndo): Promise<void> {
  const current = await refresh();
  for (const item of undo.windows) {
    const row = current.get(item.id);
    if (item.after) {
      if (!row || row.revision !== item.after.revision) throw new WindowUndoStale();
    } else if (item.before && row) {
      throw new WindowUndoStale();
    }
  }

  // Windows opened by the model leave on their exact post-write revision.
  for (const item of undo.windows) {
    if (item.before || !item.after) continue;
    await apiFetch(`/api/desk/windows/${encodeURIComponent(item.id)}/close`, {
      method: "POST", json: { expected_revision: item.after.revision },
    });
    current.delete(item.id);
  }

  // A model close is undone by reopening the same registry window and scope.
  for (const item of undo.windows) {
    if (!item.before || item.after || current.has(item.id)) continue;
    const geometry = geometryOf(item.before);
    const answer = await apiFetch<HubWindow>(`/api/desk/windows/${encodeURIComponent(item.id)}/open`, {
      method: "POST",
      json: {
        ...(item.before.object_ref ? { object_ref: item.before.object_ref } : {}),
        ...(geometry ? { geometry } : {}),
        ...(item.before.room ? { room: item.before.room } : {}),
      },
    });
    current.set(item.id, answer);
  }

  const geometry = new Map<string, Record<string, string | number>>();
  const expected: Record<string, number> = {};
  const clearGeometry: WindowUndoEntry[] = [];
  for (const item of undo.windows) {
    if (!item.before || !item.after) continue;
    const row = current.get(item.id);
    if (!row) throw new WindowUndoStale();
    const beforeRect = geometryOf(item.before);
    const afterRect = geometryOf(item.after);
    if (beforeRect && !same(beforeRect, afterRect)) {
      geometry.set(item.id, beforeRect);
      expected[item.id] = row.revision;
    } else if (!beforeRect && afterRect) {
      clearGeometry.push(item);
    }
  }
  if (geometry.size) {
    const answer = await apiFetch<WindowList>("/api/desk/windows/arrange", {
      method: "POST", json: { rects: Object.fromEntries(geometry), expected_revisions: expected },
    });
    for (const row of answer.windows ?? []) current.set(row.id, row);
  }
  for (const item of clearGeometry) {
    const row = current.get(item.id);
    const answer = await apiFetch<HubWindow>(`/api/desk/windows/${encodeURIComponent(item.id)}/set_geometry`, {
      method: "POST", json: { rect: null, expected_revision: expectedRevision(row) },
    });
    current.set(item.id, answer);
  }

  for (const item of undo.windows) {
    if (!item.before || !item.after) continue;
    const row = current.get(item.id);
    if (!row) throw new WindowUndoStale();
    if (item.before.object_ref !== item.after.object_ref) {
      const answer = await apiFetch<HubWindow>(`/api/desk/windows/${encodeURIComponent(item.id)}/open`, {
        method: "POST", json: { object_ref: item.before.object_ref ?? null, expected_revision: row.revision },
      });
      current.set(item.id, answer);
    }
    const latest = current.get(item.id);
    if (item.before.minimized !== item.after.minimized) {
      const answer = await apiFetch<HubWindow>(`/api/desk/windows/${encodeURIComponent(item.id)}/seat`, {
        method: "POST", json: { seated: Boolean(item.before.minimized), expected_revision: expectedRevision(latest) },
      });
      current.set(item.id, answer);
    }
  }
}

