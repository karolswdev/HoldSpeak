/** PHILO-16 (16b) — the `desk_changed` frames of kind `windows`.
 *
 * The hub sends ONE frame per window write (one change per window id; an
 * arrangement names every id). A frame that names only windows changed no
 * desk data: the data refresh skips it and the hub's windows follow it
 * (`hubWindows.ts`). Pure: no imports. */

export interface FrameChange {
  kind: string;
  id: string;
}

/** The changes a `desk_changed` frame's data names, or null when it names none. */
export function frameChanges(data: unknown): FrameChange[] | null {
  if (!data || typeof data !== "object") return null;
  const frame = data as { kind?: unknown; id?: unknown; changes?: unknown };
  const list =
    Array.isArray(frame.changes) && frame.changes.length
      ? frame.changes
      : frame.kind !== undefined
        ? [{ kind: frame.kind, id: frame.id }]
        : [];
  if (!list.length) return null;
  return list.map((c) => ({
    kind: String((c as { kind?: unknown }).kind ?? ""),
    id: String((c as { id?: unknown }).id ?? ""),
  }));
}

/** True for a frame that names only windows. */
export function isWindowsOnlyFrame(data: unknown): boolean {
  const changes = frameChanges(data);
  return changes !== null && changes.every((c) => c.kind === "windows");
}
