/** Local view custody: a guide borrows selection and gives it back.
 * Host snapshots (priority 1) restore after kit callbacks (priority 0).
 * A host that declares its own frame supplies ownerId before its provider. */
import { useLayoutEffect, useRef } from "react";
import { useWindowId } from "../components/window/windowIdContext";
type Checkpoint = { take: () => () => void; priority: number };
const views = new Map<string, Set<Checkpoint>>();
export function useGuideView<T>(
  read: () => T,
  restore: (saved: T) => void,
  prepare?: () => void,
  priority = 0,
  ownerId?: string,
) {
  const inherited = useWindowId();
  const windowId = ownerId ?? inherited;
  const live = useRef({ read, restore, prepare });
  live.current = { read, restore, prepare };
  useLayoutEffect(() => {
    if (!windowId) return;
    const checkpoint = {
      priority,
      take: () => {
        const saved = live.current.read();
        live.current.prepare?.();
        return () => live.current.restore(saved);
      },
    };
    const rows = views.get(windowId) ?? new Set<Checkpoint>();
    rows.add(checkpoint);
    views.set(windowId, rows);
    return () => {
      rows.delete(checkpoint);
      if (!rows.size) views.delete(windowId);
    };
  }, [windowId, priority]);
}
export function borrowGuideView(windowId: string): () => void {
  const restore = [...(views.get(windowId) ?? [])]
    .sort((a, b) => a.priority - b.priority)
    .map((checkpoint) => checkpoint.take());
  return () => restore.forEach((giveBack) => giveBack());
}
