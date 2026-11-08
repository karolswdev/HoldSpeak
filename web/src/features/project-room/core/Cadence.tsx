// R1 "the brief" (owner 2026-11-08): the Now status bar's words. When the
// project update runs and with which engine (a press opens the update's
// automation, where its schedule and engine are set), and when an update was
// last saved. Was the "Update" chips block on the face (parked
// `_parked/UpdateLine.tsx`).
import type { StatusBarItem } from "../../../desk/surface";
import { wireClock } from "../../../desk/surface";
import { useDesk } from "../../../desk/store";
import { Button } from "../../../components/signal/Signal";
import type { RoomSnapshot } from "../model";

/** `updates every friday 15:00 · Gemini CLI`, or `updates only when
 *  pressed · …` (the mono status bar of the bold canvas). Null with no
 *  update automation. */
export function cadenceWords(room: RoomSnapshot): string | null {
  if (room.updates.state !== "ok" || !room.updates.automation) return null;
  const automation = room.updates.automation;
  const when = automation.scheduleEnabled ? "updates every friday 15:00" : "updates only when pressed";
  return `${when} · ${automation.engineLabel}`;
}

/** The newest save of any update of the Project (`saved 18:39`). */
export function savedWords(room: RoomSnapshot): string | null {
  if (room.updates.state !== "ok") return null;
  let newest = "";
  for (const row of room.updates.recent) {
    const at = String(row.updated_at ?? row.created_at ?? "");
    if (at > newest) newest = at;
  }
  const clock = newest ? wireClock(newest) : "";
  return clock ? `saved ${clock}` : null;
}

export function cadenceItems(room: RoomSnapshot): StatusBarItem[] {
  const words = cadenceWords(room);
  const saved = savedWords(room);
  const automationId = room.updates.state === "ok" ? room.updates.automation?.id : undefined;
  const items: StatusBarItem[] = [];
  if (words && automationId) {
    items.push({
      key: "cadence",
      testId: "room-status-cadence",
      text: (
        <Button variant="chrome" className="room-link room-cadence"
          onClick={() => useDesk.getState().openWorkbenchWindow(automationId)}
          data-testid="room-status-cadence-open">
          {words}
        </Button>
      ),
    });
  }
  if (saved) items.push({ key: "saved", testId: "room-status-saved", text: saved });
  return items;
}
