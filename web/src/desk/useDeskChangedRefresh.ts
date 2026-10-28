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
 * from the Transcribe worker when a transcription ends, success or failure
 * (`MeetingService._run_transcribe_job`), from the summary queue after durable running and settled transitions
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
 * A burst that does not stop still refreshes: the wait has a hard cap
 * (`BURST_MAX_WAIT_MS`, `burstTimer.ts`).
 *
 * Debounced trailing, not leading: a burst (a steward run publishing an update,
 * a zone of notes filed at once) arrives as many frames in a few hundred
 * milliseconds, and the desk needs the state AFTER the burst, not a re-read per
 * frame. A frame that arrives during the wait extends it.
 */
import { useEffect, useRef } from "react";
import { useRuntimeBus } from "../runtime/RuntimeBus";
import { burstTimer } from "./burstTimer";
import { isCoderFrame } from "./steering";
import { useDesk } from "./store";
import { frameNames } from "./components/window/dockState";

/** Shared dependency groups for the desk's live readers. */
export const ALL_DESK_CHANGE_KINDS = Object.freeze([
  "action", "action_item", "agent", "artifact", "assignment", "automation", "door",
  "brief", "calendar", "calendar_event", "chain", "channel", "coder",
  "commitment", "decision", "decision_record", "destination", "directory",
  "engine", "follow_through", "inference", "inference_assignment", "kb", "launch", "meeting",
  "meeting_ready_read", "meeting_summary", "mode", "model", "model_profile",
  "note", "person", "pipeline_event", "project", "project_item", "project_update", "relationship",
  "proposal", "prompt", "recipe", "receipt", "repository", "resource",
  "scheduled_recording", "send", "sequence", "setting", "settings", "skill", "source",
  "thought", "thread", "watch", "workbench", "workbench_item", "workflow",
]);

/** The primitive store has no Thought collection; working-note saves do not
 * change any of its list reads. Memory faces opt into `thought` separately. */
export const DESK_STORE_CHANGE_KINDS = Object.freeze(
  ALL_DESK_CHANGE_KINDS.filter((kind) => kind !== "thought"),
);



export const AGENT_CHANGE_KINDS = Object.freeze(["agent", "coder", "launch", "project"]);

export const MEETING_CHANGE_KINDS = Object.freeze([
  "action", "action_item", "decision", "decision_record", "meeting", "meeting_ready_read",
  "meeting_summary", "proposal", "send", "thought", "follow_through",
]);

export const ROOM_CHANGE_KINDS = Object.freeze([
  "action", "action_item", "artifact", "commitment", "decision", "decision_record",
  "follow_through", "meeting", "note", "person", "project", "project_item", "project_update", "proposal",
  "relationship", "resource", "watch", "workbench", "workbench_item",
]);

/** Needs you is the Door's cards, the Room rows, the meeting blockers, the
 * failed summaries and the unfiled proposals (`ProjectService.needs_you`), so
 * it reads on every Room kind and on the Door, calendar, summary and
 * recording kinds as well. */
export const NEEDS_YOU_CHANGE_KINDS = Object.freeze([...new Set([
  ...ROOM_CHANGE_KINDS,
  "agent", "coder", "door", "launch", "meeting_ready_read", "send",
  "calendar", "calendar_event", "meeting_summary", "scheduled_recording",
])]);

export const WORKBENCH_CHANGE_KINDS = Object.freeze([
  "artifact", "automation", "mode", "recipe", "skill", "workbench", "workbench_item", "workflow",
]);

export const PEOPLE_CHANGE_KINDS = Object.freeze([
  "action_item", "calendar_event", "commitment", "meeting", "person", "project", "relationship",
]);

export const MEMORY_CHANGE_KINDS = ALL_DESK_CHANGE_KINDS;

/** Trailing-edge debounce window for a `desk_changed` burst, in ms. */
export const DESK_CHANGED_DEBOUNCE_MS = 300;

export function useDeskChangedRefresh(
  debounceMs: number = DESK_CHANGED_DEBOUNCE_MS,
): void {
  const { subscribe } = useRuntimeBus();

  useEffect(() => {
    // Read the store imperatively: this hook must not re-subscribe every
    // time the desk's data changes, which is exactly what depending on a
    // selected `refresh` would cause.
    const burst = burstTimer(() => void useDesk.getState().refresh(), debounceMs);
    // PHILO-16 (16b): a window write changed no desk data; the hub's windows
    // follow it (`compositor/hubWindows.ts`), never a whole-desk re-read.
    const unsubscribe = subscribe("desk_changed", (frame) => {
      if (frameNames(frame?.data, DESK_STORE_CHANGE_KINDS)) burst.bump();
    });
    return () => {
      burst.cancel();
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
  kinds: readonly string[] = ALL_DESK_CHANGE_KINDS,
  debounceMs: number = DESK_CHANGED_DEBOUNCE_MS,
): void {
  const subscribe = useBusSubscribe();
  const latest = useRef(reload);
  latest.current = reload;
  const kindsKey = kinds.join("\u0000");

  useEffect(() => {
    if (!subscribe) return;
    const burst = burstTimer(() => latest.current(), debounceMs);
    const unsubscribe = subscribe("desk_changed", (frame) => {
      if (frameNames(frame?.data, kinds)) burst.bump();
    });
    return () => {
      burst.cancel();
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, [subscribe, debounceMs, kindsKey]);
}

/** The bus's `subscribe`, or nothing when the window is drawn with no bus
 * (a component test with no provider). The context read always runs, so the
 * hook order is the same on every render. */
export function useBusSubscribe(): ReturnType<typeof useRuntimeBus>["subscribe"] | undefined {
  try {
    return useRuntimeBus().subscribe;
  } catch {
    return undefined;
  }
}

/** Conductor K3: a window that shows coder sessions re-reads on a
 * `scope:"coder"` frame (an agent began or stopped waiting for the owner),
 * the frame `MissionControlConveyor` reads with {@link isCoderFrame}. The
 * frame is rare (one per transition), so there is no debounce. Without a bus
 * (a component test) it does nothing. */
export function useOnCoderFrame(reload: () => void): void {
  const subscribe = useBusSubscribe();
  const latest = useRef(reload);
  latest.current = reload;

  useEffect(() => {
    if (!subscribe) return;
    const unsubscribe = subscribe("intel_status", (frame) => {
      if (isCoderFrame(frame)) latest.current();
    });
    return () => {
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, [subscribe]);
}
