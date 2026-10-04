/** HS-200-45 R4: one frame for a changed desk object, one debounced refresh.
 *
 * The desk used to learn about its own writes and nothing else: every mutator
 * in `dataSlice` calls `refresh()` after its own `fetch`, so the browser that
 * made the write re-read the hub and every OTHER open surface -- a second tab,
 * the iPad, an agent writing over MCP -- saw nothing until someone pressed
 * "Refresh from hub" by hand. The 2026-09-13 operational-surface audit (§9)
 * measured that: "A remote write lands in the DB and sits there."
 *
 * The hub now emits ONE `desk_changed` frame after a successful write through
 * its composed `PrimitiveService` / `WorkbenchService` (notes, decisions, kbs,
 * directories, workflows, chains, workbenches, items, skills), whoever made it,
 * plus the writers below those services that announce themselves (reaction and
 * resourceful projections, coder-materialized notes, the rails journal, the
 * guardrail seeds). Meeting changes announce themselves from the import worker
 * when an import ends, success or failure (`MeetingService._run_import_job`),
 * from the summary queue after durable running and settled transitions
 * (`_notify_queue_meeting_changed`), and when a meeting is parked or restored
 * (`MeetingService.delete_meeting`, `restore_meeting`).
 *
 * Since 2026-10-03 every write announces: `OperationRegistry.invoke` sends the
 * frame for each write operation, and one HTTP middleware
 * (`holdspeak/web/announce.py`) sends it for each mutating `/api` request that
 * answers 2xx. A window that reads its own data (the Room, People, the
 * Follow-through, Decisions and Brief views) follows the bus with
 * {@link useOnDeskChanged}.
 * This hook is the
 * whole client half: subscribe, and re-read. No per-kind patching and no new
 * UI -- the existing `refresh()` already loads the desk consistently, and a
 * patch-by-kind reducer would be a second, divergent model of the same data.
 *
 * Debounced trailing, not leading: a burst (a steward run publishing an update,
 * a zone of notes filed at once) arrives as many frames in a few hundred
 * milliseconds, and the desk needs the state AFTER the burst, not a re-read per
 * frame. A frame that arrives during the wait extends it.
 */
import { useEffect, useRef } from "react";
import { useRuntimeBus } from "../runtime/RuntimeBus";
import { useDesk } from "./store";

/** Trailing-edge debounce window for a `desk_changed` burst, in ms. */
export const DESK_CHANGED_DEBOUNCE_MS = 300;

export function useDeskChangedRefresh(
  debounceMs: number = DESK_CHANGED_DEBOUNCE_MS,
): void {
  const { subscribe } = useRuntimeBus();

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;

    const unsubscribe = subscribe("desk_changed", () => {
      if (timer !== null) clearTimeout(timer);
      timer = setTimeout(() => {
        timer = null;
        // Read the store imperatively: this hook must not re-subscribe every
        // time the desk's data changes, which is exactly what depending on a
        // selected `refresh` would cause.
        void useDesk.getState().refresh();
      }, debounceMs);
    });

    return () => {
      if (timer !== null) clearTimeout(timer);
      unsubscribe();
    };
  }, [subscribe, debounceMs]);
}

/** A mount point for {@link useDeskChangedRefresh}. Renders nothing. */
export function DeskChangedRefresh(): null {
  useDeskChangedRefresh();
  return null;
}

/** A window that reads its own data: call *reload* after a `desk_changed`
 * burst (trailing debounce, as {@link useDeskChangedRefresh}). The reload
 * must be quiet: no loading state, no cleared error, and the last read stays
 * on the glass when it fails. Without a bus (a component test) it does
 * nothing. */
export function useOnDeskChanged(
  reload: () => void,
  debounceMs: number = DESK_CHANGED_DEBOUNCE_MS,
): void {
  const subscribe = useBusSubscribe();
  const latest = useRef(reload);
  latest.current = reload;

  useEffect(() => {
    if (!subscribe) return;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const unsubscribe = subscribe("desk_changed", () => {
      if (timer !== null) clearTimeout(timer);
      timer = setTimeout(() => {
        timer = null;
        latest.current();
      }, debounceMs);
    });
    return () => {
      if (timer !== null) clearTimeout(timer);
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, [subscribe, debounceMs]);
}

/** The bus's `subscribe`, or nothing when the window is drawn with no bus
 * (a component test with no provider). The context read always runs, so the
 * hook order is the same on every render. */
function useBusSubscribe(): ReturnType<typeof useRuntimeBus>["subscribe"] | undefined {
  try {
    return useRuntimeBus().subscribe;
  } catch {
    return undefined;
  }
}
