// questline analytics — the single seam for tracked events.
//
// INVARIANT: every meaningful interaction emits a tracked event through
// track(). If a feature does not call track() at least once, it is not
// done. Events are append-only and mirror the Event model in
// prisma/schema.prisma.

import { prisma } from "./db";

/**
 * Canonical event names. Add new names here so the funnel stays legible.
 */
export type EventName =
  | "quest_created"
  | "quest_completed"
  | "streak_extended"
  | "streak_broken"
  | "freemium_gate_hit"
  | "guild_created"
  | "guild_joined"
  | "onboarding_step_viewed";

export interface TrackOptions {
  /** The acting user, if known. */
  userId?: string;
  /** Structured properties — keep keys stable; growth slices on them. */
  props?: Record<string, unknown>;
}

/**
 * Record a tracked event. Fire-and-forget at the call site, but we await
 * the write so tests can assert on it. Never throw into the request path:
 * a dropped event must not break a user action.
 */
export async function track(
  name: EventName,
  { userId, props = {} }: TrackOptions = {},
): Promise<void> {
  try {
    await prisma.event.create({
      data: { name, userId: userId ?? null, props },
    });
  } catch (err) {
    // Analytics is best-effort. Log and move on.
    console.error(`[analytics] failed to track ${name}:`, err);
  }
}
