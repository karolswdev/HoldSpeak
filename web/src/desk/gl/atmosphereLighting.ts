import type { AtmosphereActivity } from "./atmosphereRuntime";

/** A restrained warm lift from actual capture, never a simulated event. */
export function captureLightBoost(activity?: AtmosphereActivity): number {
  if (!activity?.recording && !activity?.speaking) return 1;
  const level = Number.isFinite(activity.level)
    ? Math.min(Math.max(activity.level, 0), 1)
    : 0;
  return 1.12 + level * 0.1;
}
