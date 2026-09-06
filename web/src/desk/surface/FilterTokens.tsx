/* HS-176-03 — FilterTokens: the flat one-tap filter strip.
 *
 * Promoted into the library from the composition already ratified on the
 * Project Room's history wing (`ProjectRoomCore.tsx:1550-1566`): a
 * `role="group"` span of library `Button` species, `aria-pressed` on each,
 * `data-filter-active` on the one that is on. Canon B: a recurring element
 * a face needs and the library lacks is ADDED to the library, documented in
 * contract.md, then used — never invented inline.
 *
 * It is NOT `LedgerFilterBar` (ruling R6). That species renders a query
 * `<input>` (`LedgerFilter.tsx:112`), a `matchCount/total` count (`:120-122`),
 * two raw `<button>`s (`:124`, `:147`) and removable chips (`:134-155`), and
 * it returns `null` below `SPARSE_THRESHOLD` items (`:104`, `sparse.ts:4`).
 *
 * Three laws bind this species:
 *   1. Every verb is the library Button (UX-CANON A.1) — the active token is
 *      `primary dense`, the resting ones `ghost dense`. No raw `<button>`.
 *   2. NO sparse rule. It never returns null: a filter strip that vanishes on
 *      an empty list leaves the owner no way to widen the view.
 *   3. It carries NO count. `matchCount/total` would be a second count on a
 *      face that already says its one count elsewhere (UX-CANON A.7/A.8).
 *
 * Exactly one token is active at a time; `value` is the caller's state and
 * the caller decides what the "all" token's value means (an empty string is
 * the usual "no filter" wire value).
 */
import "./filter-tokens.css";
import { Button } from "../../components/signal/Signal";

export type FilterTokenOption = {
  /** The value handed back to `onChange` (and usually the wire's param). */
  value: string;
  /** The token as the face reads it — a caption-step word, never a sentence. */
  label: string;
};

export function FilterTokens({
  options,
  value,
  onChange,
  label,
  className,
}: {
  options: FilterTokenOption[];
  /** The active option's `value`. */
  value: string;
  onChange(next: string): void;
  /** The group's accessible name (e.g. "Source filter"). */
  label: string;
  className?: string;
}) {
  const cx = ["surface-filter-tokens", className].filter(Boolean).join(" ");
  return (
    <span className={cx} role="group" aria-label={label}>
      {options.map((option) => {
        const active = option.value === value;
        return (
          <Button
            key={option.value}
            dense
            variant={active ? "primary" : "ghost"}
            className="surface-filter-token"
            data-filter-active={active || undefined}
            aria-pressed={active}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </Button>
        );
      })}
    </span>
  );
}
