/** ReadyStrip — every finished step's success token, in one row.
 *
 *  First run, option A "One screen" (owner ratified 2026-10-05). When the
 *  owner has done every step, the strip names what is now true, one
 *  success StateChip per step (`LOCAL AI · ON DEVICE`, `HEARD · 8 WORDS`).
 *  A step with nothing to say gives no chip; no chips, no strip.
 */
import { StateChip } from "./StateChip";
import "./ready-strip.css";

export interface ReadyStripItem {
  /** Stable key (the step). */
  key: string;
  /** The token: uppercase, `·`-separated facts. */
  label: string;
}

export function ReadyStrip({
  items,
  ariaLabel = "Ready",
}: {
  items: ReadyStripItem[];
  ariaLabel?: string;
}) {
  const shown = items.filter((item) => item.label.trim());
  if (!shown.length) return null;
  return (
    <ul className="surface-ready-strip" aria-label={ariaLabel} data-testid="ready-strip">
      {shown.map((item) => (
        <li key={item.key} data-step={item.key}>
          <StateChip state="success" label={item.label} />
        </li>
      ))}
    </ul>
  );
}
