// HS-200-13 — the recall controller: one query, one filter, one result,
// and the four writes the face makes (carry, name an owner, set a date,
// mark done).  The query and its filter survive a restart (design D2(e),
// "Resumed"): they are kept per viewer in localStorage and re-run on mount.
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../../lib/api";
import {
  decodeRecall,
  EMPTY_RESULT,
  RECALL_FILTERS,
  type RecallFilter,
  type RecallResult,
} from "./model";

const RESUME_KEY = "hs.desk-memory.recall.v1";

export type RecallStatus = "empty" | "searching" | "ready" | "failed";

function readResume(): { query: string; filter: RecallFilter } | null {
  try {
    const raw = localStorage.getItem(RESUME_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { query?: unknown; filter?: unknown };
    const query = typeof parsed.query === "string" ? parsed.query : "";
    const filter = RECALL_FILTERS.some((f) => f.value === parsed.filter)
      ? (parsed.filter as RecallFilter)
      : "all";
    return { query, filter };
  } catch {
    return null;
  }
}

function writeResume(query: string, filter: RecallFilter): void {
  try {
    localStorage.setItem(RESUME_KEY, JSON.stringify({ query, filter }));
  } catch {
    // Storage can be unavailable; the search still ran.
  }
}

function readableError(reason: unknown): string {
  if (reason instanceof Error) return reason.message || "search failed";
  return String(reason || "search failed");
}

export function useRecallController() {
  const resumed = useRef(readResume());
  const [query, setQuery] = useState(resumed.current?.query ?? "");
  const [filter, setFilterState] = useState<RecallFilter>(resumed.current?.filter ?? "all");
  const [result, setResult] = useState<RecallResult>(EMPTY_RESULT);
  const [status, setStatus] = useState<RecallStatus>("empty");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  /** The last good result, restored by Escape. */
  const previous = useRef<RecallResult>(EMPTY_RESULT);
  const searchedOnce = useRef(false);
  const generation = useRef(0);

  const run = useCallback(async (q: string, f: RecallFilter) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    const mine = ++generation.current;
    setStatus("searching");
    setError("");
    try {
      const raw = await apiFetch<Record<string, unknown>>(
        `/api/memory/recall?${new URLSearchParams({ query: trimmed, filter: f })}`,
      );
      if (mine !== generation.current) return;
      const decoded = decodeRecall(raw);
      previous.current = decoded;
      setResult(decoded);
      setStatus("ready");
      searchedOnce.current = true;
      writeResume(trimmed, f);
    } catch (reason) {
      if (mine !== generation.current) return;
      setError(readableError(reason));
      setStatus("failed");
    }
  }, []);

  const search = useCallback(() => run(query, filter), [run, query, filter]);

  const setFilter = useCallback(
    (next: RecallFilter) => {
      setFilterState(next);
      if (searchedOnce.current && query.trim()) void run(query, next);
      else writeResume(query, next);
    },
    [query, run],
  );

  /** Escape: clear the query and restore the previous results. */
  const clear = useCallback(() => {
    generation.current += 1;
    setQuery("");
    setError("");
    if (searchedOnce.current) {
      setResult(previous.current);
      setStatus("ready");
    } else {
      setResult(EMPTY_RESULT);
      setStatus("empty");
    }
  }, []);

  // Resumed: the query that was in the well when the tab closed runs again.
  useEffect(() => {
    const saved = resumed.current;
    if (saved?.query?.trim()) void run(saved.query, saved.filter);
  }, [run]);

  const refresh = useCallback(() => {
    if (searchedOnce.current && query.trim()) return run(query, filter);
    return Promise.resolve();
  }, [run, query, filter]);

  const carry = useCallback(
    async (recordId: string, projectId: string | null) => {
      setBusy(`carry:${recordId}`);
      try {
        await apiFetch(`/api/decision-records/${encodeURIComponent(recordId)}/carry`, {
          method: "POST",
          json: projectId ? { project_id: projectId } : {},
        });
        // The carry state is a stored fact; mark the card without a re-search
        // so focus stays on the verb (design: focus return).
        setResult((prev) => ({
          ...prev,
          current: prev.current.map((c) => (c.id === recordId ? { ...c, carried: true } : c)),
        }));
        previous.current = {
          ...previous.current,
          current: previous.current.current.map((c) => (c.id === recordId ? { ...c, carried: true } : c)),
        };
        return true;
      } catch (reason) {
        setError(readableError(reason));
        return false;
      } finally {
        setBusy("");
      }
    },
    [],
  );

  const commitmentVerb = useCallback(
    async (actionItemId: string, verb: "delegate" | "due" | "done", payload?: Record<string, unknown>) => {
      setBusy(`${verb}:${actionItemId}`);
      try {
        await apiFetch("/api/follow-through/complete", {
          method: "POST",
          json: { card_id: actionItemId, verb, payload: payload ?? {} },
        });
        await refresh();
        return true;
      } catch (reason) {
        setError(readableError(reason));
        return false;
      } finally {
        setBusy("");
      }
    },
    [refresh],
  );

  return {
    query,
    setQuery,
    filter,
    setFilter,
    result,
    status,
    error,
    busy,
    search,
    clear,
    refresh,
    carry,
    nameOwner: (actionItemId: string, owner: string) => commitmentVerb(actionItemId, "delegate", { to: owner }),
    setDate: (actionItemId: string, dueAt: string) => commitmentVerb(actionItemId, "due", { due_at: dueAt }),
    markDone: (actionItemId: string) => commitmentVerb(actionItemId, "done"),
  };
}

export type RecallController = ReturnType<typeof useRecallController>;
