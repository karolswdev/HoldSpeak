// PARKED 2026-11-11: Kit lists show every brief record; app label-width and token caps are retired.
/** HS-172-05: build the `N PRs waiting on {name}` summary label (the name as
 * typed). If the name will not fit at 393, falls back to `N PRs waiting`. */
export function prsSummaryLabel(count: number, displayName: string): string {
  const label = `${count} ${count === 1 ? "PR" : "PRs"} waiting on ${displayName}`;
  if (label.length > 30) return `${count} ${count === 1 ? "PR" : "PRs"} waiting`;
  return label;
}

/** HS-172-05: cap inline reference tokens at three, then `+N`. */
export function capTokens(items: string[], max: number = 3): string {
  if (items.length === 0) return "";
  const shown = items.slice(0, max);
  const rest = items.length - max;
  const parts = shown.join(" · ");
  return rest > 0 ? `${parts} +${rest}` : parts;
}

