/* W1-TRUTH (atlas 2026-10-27): the ONE Import image flow. Settings ▸
 * Accounts ▸ Import image and the Calendar snapshot window both press this:
 * pick up to three images, POST them to the hub's snapshot reader, and open
 * the review (`review-calendar-snapshot`) on the hub's answer. */
import { apiFetch, readableError } from "../lib/api";
import { openSurface } from "./shell";
import { hostPlace } from "./surface/egress";

/** At most this many images go in one read (the hub's own limit). */
export const CALENDAR_IMAGES_MAX = 3;

export function importCalendarImage(onRefusal: (message: string) => void): void {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".png,.jpg,.jpeg,.webp";
  input.multiple = true;
  input.onchange = async () => {
    if (!input.files?.length) return;
    const fd = new FormData();
    for (let i = 0; i < Math.min(input.files.length, CALENDAR_IMAGES_MAX); i++) fd.append("files", input.files[i]);
    try {
      openSurface("review-calendar-snapshot", JSON.stringify(await apiFetch<Record<string, unknown>>("/api/calendar/snapshot", { method: "POST", body: fd })));
    } catch (error) {
      onRefusal(readableError(error));
    }
  };
  input.click();
}

/** HS-175 counsel C10 -- the chip beside ``Snapshot``: the resolved
 * vision host (LAN / cloud / paired device) or THIS DEVICE when the model
 * runs here.  ``null`` when no vision model resolves (nothing can leave
 * and the upload refuses by name) -- absence is the signal. */
export function snapshotEgressChip(
  egress: { scope?: string; host?: string | null } | null | undefined,
): { label: string; scope: "local" | "cloud" | "mixed"; title: string } | null {
  if (!egress || !egress.scope) return null;
  const host = (egress.host || "").trim();
  if (!host || hostPlace(host).place === "mac") return null;
  const where = egress.scope === "cloud" ? "a cloud service" : egress.scope === "mesh" ? "a paired device" : "a device on your network";
  return { label: host, scope: egress.scope === "cloud" ? "cloud" : "mixed", title: `The screenshot is sent to ${host} (${where}) for extraction.` };
}
