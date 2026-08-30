/** Generic detail-loading hook (HS-117-13).
 *
 * Replaces the 3-5 useState calls every bespoke window duplicates. Server
 * resources share the Desk query client, so duplicate windows agree on
 * caching, retries, cancellation, staleness, and focus refetch. */
import { useQuery } from "@tanstack/react-query";
import { useCallback, useRef } from "react";
import { deskQueryClient, deskResourceKey } from "../../lib/queryClient";

export interface PrimitiveDetailState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function usePrimitiveDetail<T>(
  kind: string,
  id: string | null,
  fetchFn: (id: string) => Promise<T>,
): PrimitiveDetailState<T> {
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;
  const enabled = Boolean(id);
  const query = useQuery<T | null, Error>(
    {
      queryKey: id ? deskResourceKey(kind, id) : ["desk-resource", kind, "disabled"],
      // Several optional detail endpoints legitimately answer with no body.
      // TanStack Query rejects `undefined`, so normalize absence at this
      // boundary instead of forcing every window to special-case it.
      queryFn: async () => (await fetchRef.current(id as string)) ?? null,
      enabled,
    },
    deskQueryClient,
  );
  const refetchRef = useRef(query.refetch);
  refetchRef.current = query.refetch;

  const refresh = useCallback(() => {
    if (id) void refetchRef.current();
  }, [id]);

  return {
    data: query.data ?? null,
    loading: enabled && query.isFetching,
    error: query.error
      ? query.error.message || `${kind} unavailable`
      : null,
    refresh,
  };
}
