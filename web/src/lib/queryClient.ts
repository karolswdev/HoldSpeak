import { QueryClient } from "@tanstack/react-query";

/** How long an answer in the cache is current for a new reader. */
export const DESK_STALE_MS = 15_000;

/** Shared server-resource cache. Zustand owns workspace/UI state; this client
 * owns request deduplication, staleness, retries, and targeted invalidation. */
export const deskQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: DESK_STALE_MS,
      gcTime: 10 * 60_000,
      retry: 1,
      retryDelay: 250,
      refetchOnWindowFocus: true,
    },
    mutations: {
      retry: false,
    },
  },
});

export const deskResourceKey = (kind: string, id: string) =>
  ["desk-resource", kind, id] as const;

/** A write to a hub path drops the keyed reads of that path (`readKeyed`),
 *  so the next reader reads it again. Called by `apiRequest` for each write
 *  the hub accepted. */
export function forgetWrittenPath(path: string): void {
  const written = path.split("?")[0];
  void deskQueryClient.invalidateQueries({
    predicate: (query) => query.queryKey[0] === "desk-resource" &&
      typeof query.queryKey[2] === "string" && query.queryKey[2].split("?")[0] === written,
  });
}
