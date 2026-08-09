// HS-130-09 — the ONE token vocabulary for a Workbench's "Runs on" target.
//
// Stored truth: `profile_id` is `null` when unset. An unset target means
// "inherit" (HS-130-01's precedence resolver decides the effective target
// server-side). The display must NOT fabricate a `this_machine` string that
// was never stored — the displayed token and the stored token are the same
// vocabulary, and the unset case reads as an explicit inherited default.

/** Display sentinel for an unset (inherited) target. Distinct from any real
 * inference-target id so the picker never mistakes it for a destination. */
export const INHERIT_TARGET = "__inherit__";

/** The token to DISPLAY for a stored `profile_id`. Unset → the inherit
 * sentinel (never a fabricated `this_machine`). */
export function displayTargetToken(profileId: string | null | undefined): string {
  return profileId && profileId.length > 0 ? profileId : INHERIT_TARGET;
}

/** The token to STORE for a chosen display token. The inherit sentinel (and
 * empty) round-trips back to `null` — the unset/inherit stored value. */
export function storedTargetToken(displayToken: string | null | undefined): string | null {
  if (!displayToken || displayToken === INHERIT_TARGET) return null;
  return displayToken;
}

/** True when the stored target is unset (inheriting the default). */
export function isInheritedTarget(profileId: string | null | undefined): boolean {
  return !profileId || profileId.length === 0;
}
