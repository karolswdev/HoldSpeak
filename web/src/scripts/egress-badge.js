// HS-69-01: the shared egress-badge renderer.
//
// The egress badge is the canonical, structured `{scope, label}` chip — the
// one-glance replacement for privacy prose (POSITIONING canon, §"egress
// badge": ONE structured badge, never a sentence). It already shipped on
// `/presence` via Qlippy (`qlippy.js`, the `q-egress` element); Phase 69
// lifts that SAME badge onto the main cockpit cards.
//
// `scope` is one of:
//   "local"  — nothing leaves the machine            (ok / cobalt)
//   "mixed"  — local + cloud                          (accent)
//   "cloud"  — leaves the device, usually → a target  (accent + the target)
// `label` is an optional override of the default text (e.g. the cloud
// target's name). When absent, the scope's fallback word is shown.
//
// The CSS lives in `web/src/styles/global.css` (`.egress-badge`) so the chip
// styles apply to Alpine/JS-injected DOM too — the standing Astro-scoped-CSS
// gotcha (a scoped style would not reach runtime-rendered cards).

// scope → glyph + fallback word + status modifier. The glyphs and the
// local=ok / mixed|cloud=accent split mirror `qlippy.js`'s `EGRESS` map and
// `/presence`'s `.q-egress.is-*` rules exactly — this is a placement port, not
// a new visual language.
export const EGRESS_SCOPES = {
  local: { glyph: "⌂", fallback: "Local" },
  mixed: { glyph: "⌂+☁", fallback: "Local + cloud" },
  cloud: { glyph: "☁", fallback: "Leaves device" },
};

/**
 * Normalize an arbitrary egress payload to the canonical `{scope, label}`,
 * or `null` when there is no egress data to state (honesty over coverage —
 * a card with no egress meaning renders no badge).
 *
 * Accepts:
 *   - the structured `{scope, label}` shape directly, or
 *   - the dashboard runtime posture `{enabled, can_transmit_offmachine,
 *     provider, egress}` (from `/api/runtime/status`'s `intel_egress`).
 */
export function toEgressBadge(input) {
  if (!input || typeof input !== "object") return null;

  // Already a canonical badge.
  if (typeof input.scope === "string" && EGRESS_SCOPES[input.scope]) {
    return { scope: input.scope, label: input.label || undefined };
  }

  // Runtime intel-egress posture → canonical badge.
  if ("can_transmit_offmachine" in input || "enabled" in input) {
    if (input.enabled === false) {
      return { scope: "local", label: "Intel off" };
    }
    if (!input.can_transmit_offmachine) {
      return { scope: "local", label: "Local only" };
    }
    const provider = String(input.provider || "").toLowerCase();
    const label = provider === "auto" ? "Auto → cloud" : "Cloud";
    return { scope: "cloud", label };
  }

  return null;
}

/** The chip's display text: `glyph label` (label falls back to the scope word). */
export function egressBadgeText(badge) {
  const meta = badge && EGRESS_SCOPES[badge.scope];
  if (!meta) return "";
  return `${meta.glyph} ${badge.label || meta.fallback}`;
}

/**
 * Render (or update) an egress chip inside `el` for the given badge.
 * Hides the element when `badge` is null. Used by JS-rendered cards
 * (Qlippy, history). Sets `.egress-badge.is-<scope>` and the text.
 */
export function renderEgressBadge(el, badge) {
  if (!el) return;
  const text = egressBadgeText(badge);
  if (!badge || !text) {
    el.hidden = true;
    el.textContent = "";
    return;
  }
  el.textContent = text;
  el.className = `egress-badge is-${badge.scope}`;
  el.hidden = false;
}
