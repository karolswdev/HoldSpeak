import { QueryClient } from "@tanstack/react-query";

/** Shared server-resource cache. Zustand owns workspace/UI state; this client
 * owns request deduplication, staleness, retries, and targeted invalidation. */
export const deskQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
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
