/**
 * HS-118-07 — Pixi sprite state tints.
 *
 * Applies visual tints to Pixi Sprite objects based on sprite states.
 * Variant textures are looked up first via spriteVariantKey; if no
 * variant texture exists, tint overlays are used as fallback.
 *
 * Tint vocabulary:
 *   - "fresh":     green tint 0x88cc88, clears after 500ms
 *   - "recording": red tint 0xcc4444
 *   - "running":   ticker-driven alpha pulse (0.5..1.0)
 *   - "pending":   static dimmed alpha (0.7)
 */

import type { Sprite, Ticker } from "pixi.js";

/** Tint color values for sprite states. */
export const STATE_TINTS = {
  fresh: 0x88cc88,
  recording: 0xcc4444,
} as const;

/** Alpha range for running pulse (spec: 0.6–1.0, 1.5s cycle). */
const RUNNING_ALPHA_MIN = 0.6;
const RUNNING_ALPHA_MAX = 1.0;
/** Pulse speed: 2π / 1.5s = ~4.19 rad/s. */
const RUNNING_PULSE_SPEED = (2 * Math.PI) / 1.5;

/** Duration before fresh tint clears (ms). */
const FRESH_TINT_DURATION_MS = 500;

interface TintState {
  spriteState: string | null;
  freshTimer: ReturnType<typeof setTimeout> | null;
  tickerFn: ((ticker: { deltaMS: number }) => void) | null;
  /** Accumulated time for running pulse. */
  elapsed: number;
}

const tintStates = new Map<string, TintState>();

/**
 * Apply Pixi tints for a sprite state. Call this in the render loop
 * for each object node.
 *
 * @param key     Unique key for this node (e.g. "recipe:abc123")
 * @param sprite  The Pixi Sprite to tint
 * @param state   The current sprite state (from spriteStateStore)
 * @param ticker  The Pixi Application ticker (for running pulse)
 */
export function applySpriteStateTint(
  key: string,
  sprite: Sprite,
  state: string | null | undefined,
  ticker: Ticker | null,
): void {
  const current = tintStates.get(key);
  const prevState = current?.spriteState ?? null;
  const newState = state ?? null;

  // State unchanged -- only update running pulse if active.
  if (prevState === newState && current) {
    if (newState === "running" && current.elapsed !== undefined) {
      // Pulse is driven by the ticker callback, nothing to do here.
    }
    return;
  }

  // State changed -- clean up previous.
  if (current) {
    if (current.freshTimer) clearTimeout(current.freshTimer);
    if (current.tickerFn && ticker) {
      ticker.remove(current.tickerFn);
    }
  }

  // Reset sprite to default.
  sprite.tint = 0xffffff;
  sprite.alpha = 1;

  if (!newState || newState === "idle" || newState === "final" || newState === "paused" || newState === "draft") {
    tintStates.set(key, {
      spriteState: newState,
      freshTimer: null,
      tickerFn: null,
      elapsed: 0,
    });
    return;
  }

  if (newState === "fresh") {
    sprite.tint = STATE_TINTS.fresh;
    const freshTimer = setTimeout(() => {
      sprite.tint = 0xffffff;
      const ts = tintStates.get(key);
      if (ts) ts.freshTimer = null;
    }, FRESH_TINT_DURATION_MS);
    tintStates.set(key, {
      spriteState: newState,
      freshTimer,
      tickerFn: null,
      elapsed: 0,
    });
    return;
  }

  if (newState === "recording") {
    sprite.tint = STATE_TINTS.recording;
    tintStates.set(key, {
      spriteState: newState,
      freshTimer: null,
      tickerFn: null,
      elapsed: 0,
    });
    return;
  }

  if (newState === "running") {
    const ts: TintState = {
      spriteState: newState,
      freshTimer: null,
      tickerFn: null,
      elapsed: 0,
    };
    const tickerFn = (dt: { deltaMS: number }) => {
      ts.elapsed += dt.deltaMS / 1000;
      const t = (Math.sin(ts.elapsed * RUNNING_PULSE_SPEED) + 1) / 2;
      sprite.alpha =
        RUNNING_ALPHA_MIN + t * (RUNNING_ALPHA_MAX - RUNNING_ALPHA_MIN);
    };
    ts.tickerFn = tickerFn;
    if (ticker) ticker.add(tickerFn);
    tintStates.set(key, ts);
    return;
  }

  if (newState === "pending" || newState === "pending-review") {
    sprite.alpha = 0.7;
    tintStates.set(key, {
      spriteState: newState,
      freshTimer: null,
      tickerFn: null,
      elapsed: 0,
    });
    return;
  }

  // Unknown state: no tint.
  tintStates.set(key, {
    spriteState: newState,
    freshTimer: null,
    tickerFn: null,
    elapsed: 0,
  });
}

/**
 * Cleanup all tint state for a node (call on node destruction).
 */
export function clearSpriteTint(
  key: string,
  ticker: Ticker | null,
): void {
  const ts = tintStates.get(key);
  if (!ts) return;
  if (ts.freshTimer) clearTimeout(ts.freshTimer);
  if (ts.tickerFn && ticker) ticker.remove(ts.tickerFn);
  tintStates.delete(key);
}

/**
 * Cleanup all tint states (for engine destruction).
 */
export function clearAllSpriteTints(ticker: Ticker | null): void {
  for (const [key] of tintStates) clearSpriteTint(key, ticker);
}
