// HS-130-07 — one honest settings writer. Every persistent `/api/settings`
// PUT must carry the `_revision` it last read so the server can reject a
// stale, clobbering partial-tree write (optimistic concurrency) instead of
// silently merging two surfaces' edits into data loss.
import type { JsonRecord } from "./api";

/** Ride the last-read `_revision` on a settings patch. `data` is the resource
 * the caller loaded (its `_revision` token is threaded through). A missing
 * token degrades to the legacy last-writer-wins path. */
export function withRevision(
  patch: JsonRecord,
  data: { _revision?: string } | null | undefined,
): JsonRecord {
  const revision = data?._revision;
  return revision ? { ...patch, _revision: revision } : { ...patch };
}
