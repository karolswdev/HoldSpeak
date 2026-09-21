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

export function useRecallController(initialQuery = "") {
  // A `q:` scope (HS-200-11, `Find support`) outranks the resumed query:
  // the sentence is prefilled and searched under `all`; otherwise the
  // query and filter that were in the well when the tab closed resume.
  const resumed = useRef(readResume());
  const opened = useRef(initialQuery.trim());
  const [query, setQuery] = useState(opened.current || (resumed.current?.query ?? ""));
  const [filter, setFilterState] = useState<RecallFilter>(
    opened.current ? "all" : (resumed.current?.filter ?? "all"),
  );
  const [result, setResult] = useState<RecallResult>(EMPTY_RESULT);
  const [status, setStatus] = useState<RecallStatus>("empty");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  /** The last good result, restored by Escape. */
  const previous = useRef<RecallResult>(EMPTY_RESULT);
  const searchedOnce = useRef(false);
  const generation = useRef(0);

  /* HS-202-02 — `recent` is the zero-query read. A window named "Desk
     memory" showed a blank body on a desk that held a meeting, two
     decision records and a brief, because the only read it had needed a
     query and nobody had typed one yet (03-interaction-walk.md finding
     7). A search still needs words; this does not. */
  const run = useCallback(
    async (q: string, f: RecallFilter, { recent = false } = {}) => {
      const trimmed = q.trim();
      if (!trimmed && !recent) return;
      const mine = ++generation.current;
      // The recent read is QUIET: it must not put the face in the
      // searching state, or the Search verb (which goes `loading` there)
      // is inert while the desk's own memory is arriving.
      if (trimmed) setStatus("searching");
      setError("");
      try {
        const params = trimmed
          ? new URLSearchParams({ query: trimmed, filter: f })
          : new URLSearchParams({ recent: "1", filter: f });
        const raw = await apiFetch<Record<string, unknown>>(
          `/api/memory/recall?${params}`,
        );
        if (mine !== generation.current) return;
        const decoded = decodeRecall(raw);
        previous.current = decoded;
        setResult(decoded);
        setStatus("ready");
        searchedOnce.current = Boolean(trimmed);
        if (trimmed) writeResume(trimmed, f);
      } catch (reason) {
        if (mine !== generation.current) return;
        setError(readableError(reason));
        setStatus("failed");
      }
    },
    [],
  );

  const search = useCallback(() => run(query, filter), [run, query, filter]);

  const setFilter = useCallback(
    (next: RecallFilter) => {
      setFilterState(next);
      if (searchedOnce.current && query.trim()) void run(query, next);
      else {
        writeResume(query, next);
        // The recent read is filtered too: the chips were inert before
        // any search had run (03-interaction-walk.md rows 67-71).
        if (!query.trim()) void run("", next, { recent: true });
      }
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

  // Opened with a sentence (`q:` scope), else resumed: the query that was in
  // the well when the tab closed runs again.
  useEffect(() => {
    if (opened.current) {
      void run(opened.current, "all");
      return;
    }
    const saved = resumed.current;
    if (saved?.query?.trim()) {
      void run(saved.query, saved.filter);
      return;
    }
    // Nothing asked for and nothing resumed: show what the desk holds.
    void run("", saved?.filter ?? "all", { recent: true });
  }, [run]);
  // A later `Find support` on the same open window re-points the well.
  useEffect(() => {
    const next = initialQuery.trim();
    if (!next || next === opened.current) return;
    opened.current = next;
    setQuery(next);
    setFilterState("all");
    void run(next, "all");
  }, [initialQuery, run]);

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
