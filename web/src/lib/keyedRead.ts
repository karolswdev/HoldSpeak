/* One hub read per resource (2026-11-08, desk open): every reader of one
 * GET path reads it through the desk's query cache under
 * `deskResourceKey(kind, path)`: one copy, one request in flight, as HS-S14
 * did for a Program. A plain read takes an answer under `DESK_STALE_MS` old;
 * a re-read after a change frame (`fresh`) takes no kept answer, and joins a
 * read that is already out. A write to the path drops the key
 * (`forgetWrittenPath`, called by `apiRequest`). */
import { apiFetch } from "./api";
import { DESK_STALE_MS, deskQueryClient, deskResourceKey } from "./queryClient";

export function readKeyed<T>(kind: string, path: string, options: { fresh?: boolean } = {}): Promise<T> {
  return deskQueryClient.fetchQuery<T>({
    queryKey: deskResourceKey(kind, path),
    queryFn: () => apiFetch<T>(path),
    staleTime: options.fresh ? 0 : DESK_STALE_MS,
    retry: false,
  });
}

/** The hub's settings (`GET /api/settings`), read once for every reader. */
export function readHubSettings<T = Record<string, unknown>>(options: { fresh?: boolean } = {}): Promise<T> {
  return readKeyed<T>("settings", "/api/settings", options);
}

/** The People store's readiness (`GET /api/people/readiness`). */
export function readPeopleReadiness<T = unknown>(options: { fresh?: boolean } = {}): Promise<T> {
  return readKeyed<T>("people", "/api/people/readiness", options);
}

/** The People relationships (`GET /api/people/relationships`). */
export function readPeopleRelationships<T = unknown>(options: { fresh?: boolean } = {}): Promise<T> {
  return readKeyed<T>("people", "/api/people/relationships", options);
}
