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
import { parseLocal } from "../pullouts/views/BriefView";

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
 * PHILO-15-09 (B04, ruling 1): `GENERATED · 11:08`. A second Generate on
 * the same day makes the same brief again, so the receipt names the time it
 * was made (the producer's `generated_at`, in the viewer's zone). The count
 * is not repeated here: the headline above says what the brief holds.
 */
export function briefReceipt(brief: GeneratedBrief | null): string | null {
  if (!brief) return null;
  const at = parseLocal(brief.generated_at);
  if (!at) return "GENERATED";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `GENERATED · ${pad(at.getHours())}:${pad(at.getMinutes())}`;
}
