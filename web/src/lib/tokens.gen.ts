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
  snapTop: 28,
  snapBottom: 84,
} as const;

export const GLOW_POOL: Record<string, string> = {
  meeting: "#56C7F5",
  note: "#34D399",
  kb: "#818CF8",
  recipe: "#C7D2FE",
  artifact: "#2DD4BF",
  chain: "#A78BFA",
  workflow: "#56C7F5",
  directory: "#94A3B8",
  coder: "#C7D2FE",
};

export const ZONE_TINT_POOL = [
  "#94A3B8",
  "#56C7F5",
  "#34D399",
  "#A78BFA",
  "#2DD4BF",
  "#818CF8",
] as const;
