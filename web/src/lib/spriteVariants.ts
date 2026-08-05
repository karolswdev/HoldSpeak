/**
 * HS-118-07 — Sprite-variant key function.
 *
 * Pure function: `(kind, state) -> variantKey`. The variant key is
 * used to select the correct sprite image (when a state-specific
 * texture exists) and to apply the correct CSS hint class. Falls
 * back to the base kind when state is null or not recognized.
 *
 * Key format: `kind-state` (hyphen separator) matching the asset
 * naming convention (e.g. `workbench-running.png`).
 */

import { isValidSpriteState, spriteStateCssClass } from "./spriteStates";

/**
 * Compute a sprite variant key from a primitive kind and its current
 * sprite state. The key encodes the kind and (when valid) the state
 * as `kind-state`; when the state is null or unrecognized, the key
 * is the bare `kind` (the base/default variant).
 */
export function spriteVariantKey(
  kind: string,
  state: string | null | undefined,
): string {
  if (state && isValidSpriteState(kind, state)) {
    return `${kind}-${state}`;
  }
  return kind;
}

/**
 * Convenience: given a variant key, extract the kind and state parts.
 * The first hyphen after the kind splits kind from state; bare kinds
 * (no hyphen matching a vocab entry) return null state.
 */
export function parseVariantKey(key: string): {
  kind: string;
  state: string | null;
} {
  const sep = key.indexOf("-");
  if (sep < 0) return { kind: key, state: null };
  const kind = key.slice(0, sep);
  const state = key.slice(sep + 1);
  if (isValidSpriteState(kind, state)) return { kind, state };
  // Not a recognized kind-state pair: the whole key is the kind.
  return { kind: key, state: null };
}

/**
 * Get the CSS hint class for a variant key.
 */
export function variantCssClass(variantKey: string): string {
  const { state } = parseVariantKey(variantKey);
  return spriteStateCssClass(state);
}

/**
 * HS-118-07 — derive sprite state for a workbench from its pending
 * count and runtime events.
 *
 * The fresh->idle timer (5 min after run_complete) is handled by the
 * caller via setTimeout; this function only reads the current snapshot.
 */
export function deriveWorkbenchSpriteState(
  pendingCount: number,
  runtimeState?: string | null,
): string {
  if (runtimeState === "running") return "running";
  if (runtimeState === "fresh") return "fresh";
  if (pendingCount > 0) return "pending";
  return "idle";
}

/**
 * HS-118-07 — derive sprite state for an artifact from its status field.
 */
export function deriveArtifactSpriteState(
  status: string | null | undefined,
): string {
  if (!status) return "draft";
  const lower = status.toLowerCase();
  if (lower === "final" || lower === "complete" || lower === "completed")
    return "final";
  if (
    lower === "pending-review" ||
    lower === "pending_review" ||
    lower === "review" ||
    lower === "reviewing"
  )
    return "pending-review";
  return "draft";
}

/**
 * HS-118-07 — derive sprite state for a meeting from recording state.
 */
export function deriveMeetingSpriteState(
  recordingState?: string | null,
): string {
  if (recordingState === "recording") return "recording";
  if (recordingState === "paused") return "paused";
  return "idle";
}
