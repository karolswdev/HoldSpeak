/* First run — the Skip on the optional cards (owner ruling 2026-10-06:
 * "Just on the setup, allow to press 'skip' and we good"). Calendar and
 * Connections each have one Skip; Local AI, You and First words do not.
 *
 * Stored in `config.first_run.skipped` through the settings API (`GET/PUT
 * /api/settings`, the same place the You card keeps his name), so a reload
 * does not bring a skipped step back. Settings still sets the step up later. */
import { useCallback, useEffect, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";

export type SkippableStep = "calendar" | "connections";

export function useSkips() {
  const [skipped, setSkipped] = useState<SkippableStep[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState<SkippableStep | null>(null);
  const [error, setError] = useState<{ step: SkippableStep; reason: string } | null>(null);

  useEffect(() => {
    let live = true;
    void apiFetch<{ first_run?: { skipped?: unknown } }>("/api/settings")
      .then((settings) => {
        if (!live) return;
        const list = settings?.first_run?.skipped;
        if (Array.isArray(list)) {
          setSkipped(list.filter((s): s is SkippableStep => s === "calendar" || s === "connections"));
        }
      })
      .catch(() => undefined)
      .finally(() => {
        if (live) setLoaded(true);
      });
    return () => {
      live = false;
    };
  }, []);

  const skip = useCallback(
    async (step: SkippableStep) => {
      const next = [...new Set([...skipped, step])];
      setBusy(step);
      setError(null);
      try {
        await apiFetch("/api/settings", { method: "PUT", json: { first_run: { skipped: next } } });
        setSkipped(next);
      } catch (caught) {
        setError({ step, reason: readableError(caught) });
      } finally {
        setBusy(null);
      }
    },
    [skipped],
  );

  return {
    loaded,
    calendar: skipped.includes("calendar"),
    connections: skipped.includes("connections"),
    busy,
    error,
    skip,
  };
}

export type Skips = ReturnType<typeof useSkips>;
