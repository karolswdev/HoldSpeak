import {
  type ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { apiFetch, readableError } from "../lib/api";
import { SurfaceState } from "../desk/surface/Surface";
import {
  controlModeDescription,
  controlModeLabel,
} from "../lib/productLanguage";


export function PostureNote({
  mode,
  describe = false,
}: {
  mode: string;
  describe?: boolean;
}) {
  return (
    <span className="posture-note">
      <strong>{controlModeLabel(mode)}</strong>
      {describe ? <> · {controlModeDescription(mode)}</> : null}
    </span>
  );
}

export function useResource<T>(url: string, initial: T) {
  const [data, setData] = useState<T>(initial);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const mounted = useRef(true);

  useEffect(
    () => () => {
      mounted.current = false;
    },
    [],
  );
  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await apiFetch<T>(url);
      if (mounted.current) setData(result);
      return result;
    } catch (reason) {
      if (mounted.current) setError(readableError(reason));
      return null;
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, [url]);
  useEffect(() => {
    void reload();
  }, [reload]);
  return { data, setData, loading, error, setError, reload };
}

/** HS-111-08 — the ONE chokepoint (audit §3.5): every useResource
 * consumer's loading/empty/error faces render as the kit's
 * SurfaceState axes — never Skeleton/EmptyState/InlineMessage. */
export function ResourceState({
  loading,
  error,
  empty,
  onRetry,
  children,
}: {
  loading: boolean;
  error: string;
  empty?: boolean;
  onRetry(): void;
  children: ReactNode;
}) {
  return (
    <SurfaceState
      loading={loading}
      error={error}
      empty={empty}
      emptyLabel="Nothing yet"
      onRetry={onRetry}
    >
      {children}
    </SurfaceState>
  );
}

export function valueAt(record: unknown, path: string, fallback = ""): string {
  let value: unknown = record;
  for (const key of path.split(".")) {
    if (!value || typeof value !== "object") return fallback;
    value = (value as Record<string, unknown>)[key];
  }
  return value === null || value === undefined ? fallback : String(value);
}

export function asRows(
  value: unknown,
  keys: string[],
): Array<Record<string, unknown>> {
  if (Array.isArray(value))
    return value.filter(
      (row): row is Record<string, unknown> =>
        Boolean(row) && typeof row === "object",
    );
  if (value && typeof value === "object") {
    for (const key of keys) {
      const rows = (value as Record<string, unknown>)[key];
      if (Array.isArray(rows)) return asRows(rows, []);
    }
  }
  return [];
}

export function rowId(row: Record<string, unknown>, index: number): string {
  return String(row.id ?? row.key ?? row.name ?? row.session_id ?? index);
}
