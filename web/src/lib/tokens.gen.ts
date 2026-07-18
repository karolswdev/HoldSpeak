// GENERATED FILE — do not edit (HS-96-02). Source of truth:
// web/design-tokens.json → node scripts/generate-tokens.cjs.
// The TS mirror of the Desk OS component tokens, so the window
// physics and the GL world can never drift from the CSS ladder.

export const DESK_Z = {
  canvas: 0,
  worldOverlay: 25,
  chrome: 30,
  windowBase: 42,
  dock: 80,
  transient: 81,
} as const;

export const DESK_WINDOW = {
  margin: 10,
  grab: 72,
  cascade: 26,
  snapTop: 54,
  snapBottom: 52,
} as const;

export const GLOW_POOL: Record<string, string> = {
  meeting: "#56C7F5",
  note: "#34D399",
  kb: "#FBBF24",
  recipe: "#FF6B35",
  artifact: "#FF9E64",
  chain: "#A78BFA",
  workflow: "#56C7F5",
  directory: "#E0A458",
  coder: "#FF6B35",
};

export const ZONE_TINT_POOL = [
  "#E0A458",
  "#56C7F5",
  "#34D399",
  "#A78BFA",
  "#FF9E64",
  "#FBBF24",
] as const;
