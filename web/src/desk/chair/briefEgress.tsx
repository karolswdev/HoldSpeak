/* HS-202-02 — the brief's badge and its receipt.
 *
 * `Generate` was one of the eleven verbs with neither
 * (03-interaction-walk.md finding 4), and one of the two the walk fired
 * live: `POST /api/brief/generate` went out with no badge on the row and
 * nothing said afterwards.
 *
 * Where it goes, checked on the hub rather than assumed: the route
 * (holdspeak/web/routes/monday_brief.py:110-115) calls
 * `MondayBriefService.generate` and `_compose_overlay`, which read the
 * database, the People sidecar and the follow-through service. Neither
 * module imports an inference path; nothing is sent anywhere. The badge
 * names THIS DEVICE because that is true, not because it is the default.
 */
import { EgressChip } from "../surface";

export function BriefEgress() {
  return (
    <EgressChip
      label="THIS DEVICE"
      scope="local"
      title="The brief is built from this desk's own records."
    />
  );
}

export type GeneratedBrief = {
  /** The hub's shape: `{changed, broke, waiting, decisions}` of items. */
  sections?: Record<string, unknown[]>;
  is_empty?: boolean;
  generated_at?: string;
};

/** The receipt after the press: what was built, and when.
 *
 * HS-202-02 (Astra's counsel finding 2 on PR #595) — the first round
 * counted `brief.items`, a field `MondayBrief` does not have
 * (`ChairHome.tsx:136-142`), so every receipt silently dropped its count.
 * The helper-only test could not see it; the rendered fence did.
 */
export function briefReceipt(brief: GeneratedBrief | null): string | null {
  if (!brief) return null;
  const count = Object.values(brief.sections ?? {}).reduce(
    (total, rows) => total + (Array.isArray(rows) ? rows.length : 0),
    0,
  );
  const when = new Date(String(brief.generated_at ?? ""));
  const time = Number.isNaN(when.getTime())
    ? ""
    : when.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  // UX-CANON A.8 — no counter of zero: an empty brief says it is ready
  // and says nothing about a count.
  const parts = ["Brief ready"];
  if (count > 0) parts.push(`${count} item${count === 1 ? "" : "s"}`);
  if (time) parts.push(time);
  return parts.join(" · ");
}
