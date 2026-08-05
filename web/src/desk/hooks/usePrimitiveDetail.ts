/** Generic detail-loading hook (HS-117-13).
 *
 * Replaces the 3-5 useState calls every bespoke window duplicates for
 * loading/error/data/refresh. Does NOT handle WebSocket subscriptions,
 * caching, retries, or staleness — those stay component-side. */
import { useCallback, useEffect, useRef, useState } from "react";

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
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Keep fetchFn stable across renders without requiring the caller to
  // memoize it — we track the latest reference and call through it.
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;

  // Monotonic generation counter — only the most recent fetch may write state.
  const genRef = useRef(0);

  const doFetch = useCallback(
    (targetId: string, generation: number) => {
      setLoading(true);
      const controller = new AbortController();

      fetchRef
        .current(targetId)
        .then((result) => {
          if (generation !== genRef.current || controller.signal.aborted) return;
          setData(result);
          setError(null);
        })
        .catch((err) => {
          if (generation !== genRef.current || controller.signal.aborted) return;
          setError(
            err instanceof Error ? err.message : `${kind} unavailable`,
          );
        })
        .finally(() => {
          if (generation !== genRef.current || controller.signal.aborted) return;
          setLoading(false);
        });

      return controller;
    },
    [kind],
  );

  // Fetch on mount and when id changes.
  useEffect(() => {
    if (!id) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    const generation = ++genRef.current;
    const controller = doFetch(id, generation);

    return () => {
      controller?.abort();
    };
  }, [id, doFetch]);

  // Refetch on window refocus (visibilitychange).
  useEffect(() => {
    if (!id) return;

    const onVisible = () => {
      if (document.visibilityState !== "visible") return;
      const generation = ++genRef.current;
      doFetch(id, generation);
    };

    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [id, doFetch]);

  // Stable refresh callback — triggers a new fetch without clearing current data.
  const refresh = useCallback(() => {
    if (!id) return;
    const generation = ++genRef.current;
    doFetch(id, generation);
  }, [id, doFetch]);

  return { data, loading, error, refresh };
}
