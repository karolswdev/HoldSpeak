import { type ComponentPropsWithRef } from "react";

/** HS-202-03 — the CHROME variant.
 *
 * Some verbs are not plated buttons: a menu row, a wing tab, a dock chip, a
 * formatting-rail key, the mic, the record orb.  Their material is drawn by
 * the strip they ride (`chrome-menus.css` keys off `.desk-menu-list button`,
 * `pullout.css` off `.desk-wing`, `window-chrome.css` off `.desk-dock-*`,
 * and so on), so for `variant="chrome"` the plate classes (`btn`,
 * `btn--secondary`, `btn--sm`) are WITHHELD and only the marker
 * `btn--chrome` is stamped: the strip keeps its own ink to the pixel.
 *
 * What the variant DOES carry is the species (UX-CANON A.1 — every verb is
 * the library Button): one element, one `type="button"` default, one
 * `loading` / `disabled` / `aria-busy` grammar.  Before HS-202-03 the
 * surface inventory of 2026-09-20 (§3.3) found these shared controls were
 * the WORST raw-HTML sites in the product — every menu item, every wing
 * tab, the dock itself — so a stranger's first five minutes met raw HTML at
 * every turn.
 *
 * It is not a licence to draw a new look: a `chrome` verb always carries the
 * className of a strip that already owns its material, and `Signal.test.tsx`
 * plus `desk/__tests__/hs202ChromeSpecies.test.tsx` fence the no-plate rule.
 */
export function Button({
  variant = "secondary",
  dense = false,
  loading = false,
  children,
  className = "",
  disabled,
  type = "button",
  ...props
}: ComponentPropsWithRef<"button"> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "chrome";
  dense?: boolean;
  loading?: boolean;
}) {
  // A raw <button> in a form submits; the species never does unless asked.
  return (
    <button
      type={type}
      className={
        variant === "chrome"
          ? `btn--chrome ${className}`.trim()
          : `btn btn--${variant}${dense ? " btn--sm" : ""} ${className}`
      }
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <span className="signal-spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}

