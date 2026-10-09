/** PHILO-16 (L6) — one owner of the visible pixels, one timing.
 *
 * The four motion moments of §6 (raise 180, open 240, seat 200, arrange 220)
 * become one function: the duration scales with how far a box travels, a box
 * whose end is out of sight is simply there (`seenOnly`), the person's tempo
 * multiplies the speed, and reduced motion makes every moment instant (the end
 * states are kept). One easing for everything. Pure: no DOM. */

export type MotionKind = "raise" | "open" | "seat" | "arrange";

export const EASE = "cubic-bezier(.2,.8,.2,1)";

export const BASE_MS: Readonly<Record<MotionKind, number>> = {
  raise: 180,
  open: 240,
  seat: 200,
  arrange: 220,
};

export const MIN_MS = 120;
export const MAX_MS = 360;
/** The travel (px) at which a moment takes exactly its base duration. */
export const REFERENCE_PX = 400;

export interface TimingInput {
  /** How far the box travels, in px (centre to centre). Absent: the base. */
  distance?: number;
  /** The box ends out of sight: it does not animate (seenOnly). */
  leaving?: boolean;
  /** The person's tempo, 0.5 (slow) to 2 (fast); 1 by default. */
  tempo?: number;
  /** prefers-reduced-motion: every moment is instant. */
  reducedMotion?: boolean;
}

export interface Timing {
  duration: number;
  easing: string;
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

/** The duration and easing of one motion moment. A duration of 0 means
 * "no animation: write the end state". */
export function timing(kind: MotionKind, input: TimingInput = {}): Timing {
  if (input.reducedMotion || input.leaving) return { duration: 0, easing: EASE };
  const base = BASE_MS[kind];
  const tempo = clamp(input.tempo ?? 1, 0.5, 2);
  // Travel stretches the moment: 3/4 of the base for a box that does not
  // move, the base at REFERENCE_PX, longer beyond (clamped).
  const scaled =
    input.distance === undefined
      ? base
      : base * (0.75 + 0.25 * (Math.max(0, input.distance) / REFERENCE_PX));
  return { duration: Math.round(clamp(scaled / tempo, MIN_MS, MAX_MS)), easing: EASE };
}
