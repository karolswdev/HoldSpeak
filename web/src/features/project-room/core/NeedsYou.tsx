import { wireDate } from "../../../desk/surface/format";
import type { RoomHealthPerson } from "../model";

export function nudgeCooldownToken(nudge: RoomHealthPerson["nudge"]): string | null {
  if (!nudge || nudge.state !== "sent" || !nudge.sentAt) return null;
  const sentDate = wireDate(nudge.sentAt);
  if (!sentDate) return null;
  const diffMs = Date.now() - sentDate.getTime();
  const diffDays = diffMs / 86_400_000;
  if (diffDays > 7) return null; // past cooldown
  if (diffDays < 1 / 24) return "NUDGED JUST NOW"; // under 1 hour
  if (diffDays < 1) return `NUDGED ${Math.max(1, Math.round(diffDays * 24))} H AGO`; // hours under a day
  return `NUDGED ${Math.max(1, Math.round(diffDays))} D AGO`;
}
