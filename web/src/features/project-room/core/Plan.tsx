import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../../lib/api";
import { pluralize } from "../steward/model";

type ItemRow = {
  id: string;
  item_type: string;
  title: string;
  lifecycle: string;
  severity: string | null;
  due_at: string | null;
  details_json: string | null;
  owner?: string;
  summary?: string;
  updated_at?: string;
};

function dayNumber(ymd: string): number {
  const [y, m, d] = ymd.slice(0, 10).split("-").map(Number);
  return Math.round(new Date(y, m - 1, d).getTime() / 86_400_000);
}
function todayNumber(): number {
  const n = new Date();
  return Math.round(
    new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime() / 86_400_000,
  );
}
/** Days late for a planned milestone past its date; 0 otherwise. */
function daysLate(item: ItemRow): number {
  if (
    item.item_type !== "milestone" ||
    item.lifecycle !== "planned" ||
    !item.due_at
  )
    return 0;
  return Math.max(0, todayNumber() - dayNumber(item.due_at));
}
function plainWord(word: string): string {
  if (word.length <= 2) return word.toUpperCase();
  const w = word.replace(/_/g, " ").toLowerCase();
  return w.charAt(0).toUpperCase() + w.slice(1);
}

export type ItemsRead = {
  items: ItemRow[] | null;
  failed: boolean;
  retry: () => void;
};

export function useRoomItems(projectId: string, revision: number): ItemsRead {
  const [items, setItems] = useState<ItemRow[] | null>(null);
  // A failed read is UNAVAILABLE, never empty (Codex Astra canvases r1 F7).
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!projectId) return;
    let live = true;
    apiFetch<{ items: ItemRow[] }>(
      `/api/projects/${encodeURIComponent(projectId)}/items?limit=200`,
    )
      .then((r) => {
        if (live) {
          setFailed(false);
          setItems(r.items ?? []);
        }
      })
      .catch(() => {
        if (live) {
          setFailed(true);
          setItems(null);
        }
      });
    return () => {
      live = false;
    };
  }, [projectId, revision, attempt]);
  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { items, failed, retry };
}

/** The plan carries the same late and closed states as its source. */
export function planItemWords(item: ItemRow): string {
  const late = daysLate(item);
  return late
    ? `${pluralize(late, "day", "days")} late`
    : plainWord(item.lifecycle);
}
