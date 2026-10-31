// PG-DIRECTION DIR3 (DIRECTION-2026-10-31.md §6 "What the desk shows"): the
// desk's half of the briefing page. Copy page link makes the package and its
// token on the hub (POST /api/reach/packages) and puts the page's link on the
// clipboard; Revoke ends the token (the item stays held). A row says where
// the item went in its line, never in a chip (UX-CANON A.9).
import { apiFetch } from "../lib/api";

/** An open page for a held item, as the hub sends it on the item. */
export type OpenPage = { package_id: string; expires_at: string };

/** The held items a page answers (the hub's `BRIEFABLE`). */
const BRIEFABLE = new Set([
  "core", "merge", "finding", "parked", "limited", "race", "add_step", "requirement_word",
  "requirement_left", "requirement_proposed", "step_change", "step_amend",
]);

export function briefable(kind: string): boolean {
  return BRIEFABLE.has(kind);
}

/** The Needs you row id of a Program's your-turn item (the package's ref). */
export function programRef(programId: string, itemId: string): string {
  return `program:${programId}:${itemId}`;
}

/** The packages whose link this desk copied in this session. */
const copied = new Set<string>();

function clock(stamp: string): string {
  const at = new Date(stamp);
  return Number.isNaN(at.getTime())
    ? ""
    : `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
}

/** The row's line for an open page: "Page link copied · open until 06:30"
 *  right after the copy, else "Page open until 06:30". */
export function pageWords(page: OpenPage | null | undefined): string {
  if (!page) return "";
  const until = clock(page.expires_at);
  return copied.has(page.package_id) ? `Page link copied · open until ${until}` : `Page open until ${until}`;
}

type Made = { id: string; path: string; link?: string | null; expires_at: string };

/** Make the page for one held item and copy its link. */
export async function copyPageLink(ref: string): Promise<OpenPage> {
  const made = await apiFetch<Made>("/api/reach/packages", { method: "POST", json: { refs: [ref] } });
  const link = made.link || `${window.location.origin}${made.path}`;
  copied.add(made.id);
  await navigator.clipboard.writeText(link);
  return { package_id: made.id, expires_at: made.expires_at };
}

/** End a page's token (the item stays held). */
export async function revokePage(packageId: string): Promise<void> {
  copied.delete(packageId);
  await apiFetch(`/api/reach/packages/${encodeURIComponent(packageId)}/revoke`, { method: "POST", json: {} });
}
