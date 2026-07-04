// questline feature flags — the rollout seam.
//
// INVARIANT: no user-facing change reaches production without a flag
// here. Flags ride the ladder off -> dogfood -> 10% -> GA (see
// .hs/workflows.md). Resolution is deterministic per user so cohorts
// are stable across requests.

import { createHash } from "crypto";

export type FlagState = "off" | "dogfood" | "percent" | "on";

interface FlagConfig {
  state: FlagState;
  /** rollout percentage 0-100, used when state === "percent" */
  percent?: number;
}

/**
 * The flag registry. Edit state/percent to advance a rung.
 */
export const FLAGS = {
  "guildsV1": { state: "off" } as FlagConfig,
  "onboardingTemplatesV2": { state: "percent", percent: 10 } as FlagConfig,
  "streakEngineTzFix": { state: "dogfood" } as FlagConfig,
  "xpBoosts": { state: "on" } as FlagConfig,
} satisfies Record<string, FlagConfig>;

export type FlagKey = keyof typeof FLAGS;

const DOGFOOD_USER_IDS = new Set<string>([
  "user_priya",
  "user_marcus",
  "user_dana",
  "user_sam",
]);

/** Stable 0-99 bucket for a (flag, user) pair. */
function bucket(flag: string, userId: string): number {
  const h = createHash("sha1").update(`${flag}:${userId}`).digest();
  return h[0] % 100;
}

/**
 * Is `flag` enabled for `userId`? Anonymous users only see GA ("on").
 */
export function isEnabled(flag: FlagKey, userId?: string): boolean {
  const cfg = FLAGS[flag];
  switch (cfg.state) {
    case "on":
      return true;
    case "off":
      return false;
    case "dogfood":
      return !!userId && DOGFOOD_USER_IDS.has(userId);
    case "percent":
      if (!userId) return false;
      return bucket(flag, userId) < (cfg.percent ?? 0);
  }
}
