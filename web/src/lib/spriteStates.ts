/**
 * HS-118-07 — Sprite state vocabulary registry.
 *
 * Each primitive kind that supports visual state declares its valid
 * states here. The registry is the single source of truth for which
 * state strings a kind accepts; unknown states fall back to the base
 * (idle / null).
 *
 * Format: each entry is a { key, label, cssHint? } object so the
 * registry carries both the machine key and the human label in one
 * place.
 */

/** A single sprite state entry in the registry. */
export interface SpriteStateEntry {
  /** Machine key (e.g. "idle", "running", "recording"). */
  key: string;
  /** Human-readable label (e.g. "Idle", "Running"). */
  label: string;
  /** Optional CSS class applied to the sprite container. */
  cssHint?: string;
}

/** Valid sprite states per primitive kind. */
export const SPRITE_STATE_VOCAB: Readonly<
  Record<string, readonly SpriteStateEntry[]>
> = {
  /** Workbench states: derived from pending count + runtime bus. */
  workbench: [
    { key: "idle", label: "Idle" },
    { key: "pending", label: "Pending", cssHint: "sprite-pending" },
    { key: "running", label: "Running", cssHint: "sprite-active" },
    { key: "fresh", label: "Fresh", cssHint: "sprite-fresh" },
  ],
  /** Meeting states: derived from recording lifecycle. */
  meeting: [
    { key: "idle", label: "Idle" },
    { key: "recording", label: "Recording", cssHint: "sprite-active" },
    { key: "paused", label: "Paused" },
  ],
  /** Artifact states: mapped directly from artifact.status. */
  artifact: [
    { key: "draft", label: "Draft", cssHint: "sprite-pending" },
    { key: "final", label: "Final" },
    { key: "pending-review", label: "Pending review", cssHint: "sprite-pending" },
  ],
};

/** Check whether `state` is a valid sprite state for `kind`. */
export function isValidSpriteState(
  kind: string,
  state: string | null | undefined,
): boolean {
  if (!state) return false;
  const vocab = SPRITE_STATE_VOCAB[kind];
  return vocab ? vocab.some((entry) => entry.key === state) : false;
}

/** Return the CSS hint class for a given sprite state, or "" if none. */
export function spriteStateCssClass(
  state: string | null | undefined,
): string {
  if (!state) return "";
  for (const entries of Object.values(SPRITE_STATE_VOCAB)) {
    const entry = entries.find((e) => e.key === state);
    if (entry?.cssHint) return entry.cssHint;
  }
  return "";
}
