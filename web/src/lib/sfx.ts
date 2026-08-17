/**
 * HS-135-12 — the desk clicks: six mechanical sounds, one global toggle.
 *
 * Runtime is a typed enum + lazy AudioContext + per-sound buffer cache +
 * concurrent pool cap of 3 (oldest silently dropped).
 *
 * NO CSS custom properties — the "sound" section in design-tokens.json
 * documents names only (counsel ruling A.L4 condition 1).
 */

// ---- the six canonical sound names (L4 trigger table) ----

export type SfxName =
  | "key-down"
  | "key-up"
  | "latch"
  | "land"
  | "file"
  | "error";

const SFX_NAMES: SfxName[] = [
  "key-down",
  "key-up",
  "latch",
  "land",
  "file",
  "error",
];

// ---- state ----

let audioCtx: AudioContext | null = null;
const bufferCache = new Map<SfxName, AudioBuffer>();
const activeSources = new Map<SfxName, AudioBufferSourceNode[]>();
const POOL_CAP = 3;

/** Global enable flag. Starts true (on by default per L4).
 * Reads localStorage for a persisted preference. */
const SFX_STORAGE_KEY = "hs.desk.sfx-enabled";
let enabled = (() => {
  if (typeof localStorage === "undefined") return true;
  try {
    const stored = localStorage.getItem(SFX_STORAGE_KEY);
    return stored === null ? true : stored !== "false";
  } catch {
    return true;
  }
})();

// Sync the CSS class on <html> from the initial state.
if (typeof document !== "undefined" && !enabled) {
  document.documentElement.classList.add("sfx-off");
}

/** prefers-reduced-motion mutes regardless of the toggle. */
let reducedMotion = false;

// Listen for reduced-motion changes at module load time.
if (typeof window !== "undefined" && window.matchMedia) {
  const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
  reducedMotion = mql.matches;
  mql.addEventListener("change", (e) => {
    reducedMotion = e.matches;
  });
}

// ---- public API ----

/** Set the global enable flag. Called by the settings toggle. */
export function setSfxEnabled(on: boolean): void {
  enabled = on;
  // L4: "The toggle sets a CSS class on <html>"
  if (typeof document !== "undefined") {
    document.documentElement.classList.toggle("sfx-off", !on);
  }
  // Persist to localStorage for cross-session state.
  try {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(SFX_STORAGE_KEY, String(on));
    }
  } catch {
    /* storage unavailable */
  }
}

/** Read the current enable state (for the toggle's initial value). */
export function isSfxEnabled(): boolean {
  return enabled;
}

/** Subscribe to enable-state changes. Returns an unsubscribe function. */
const listeners = new Set<(on: boolean) => void>();
export function subscribeSfxEnabled(cb: (on: boolean) => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function notifyListeners(): void {
  listeners.forEach((cb) => cb(enabled));
}

/** Set + notify. */
export function toggleSfx(on: boolean): void {
  setSfxEnabled(on);
  notifyListeners();
}

/** Check whether sound is currently muted (toggle off OR reduced-motion). */
export function isMuted(): boolean {
  return !enabled || reducedMotion;
}

let preloaded = false;

/** Play a named sound. No-op when muted. */
export function play(name: SfxName): void {
  if (isMuted()) return;
  if (typeof window === "undefined") return;

  // Lazy AudioContext creation (must be after user gesture).
  if (!audioCtx) {
    try {
      audioCtx = new AudioContext();
    } catch {
      return; // AudioContext unavailable
    }
  }

  // Resume if suspended (browsers suspend until user gesture).
  if (audioCtx.state === "suspended") {
    void audioCtx.resume();
  }

  // Preload all sounds on first play (user gesture unlocks AudioContext).
  if (!preloaded) {
    preloaded = true;
    for (const n of SFX_NAMES) void loadBuffer(n);
  }

  const buffer = bufferCache.get(name);
  if (!buffer) {
    // Buffer not yet loaded — fire and forget the load, play on next call.
    void loadBuffer(name);
    return;
  }

  playBuffer(name, buffer);
}

function playBuffer(name: SfxName, buffer: AudioBuffer): void {
  if (!audioCtx) return;

  // Pool cap: evict oldest if at capacity.
  let pool = activeSources.get(name);
  if (!pool) {
    pool = [];
    activeSources.set(name, pool);
  }
  while (pool.length >= POOL_CAP) {
    const oldest = pool.shift()!;
    try {
      oldest.stop();
    } catch {
      // already stopped
    }
  }

  const source = audioCtx.createBufferSource();
  source.buffer = buffer;
  source.connect(audioCtx.destination);
  source.onended = () => {
    const p = activeSources.get(name);
    if (p) {
      const idx = p.indexOf(source);
      if (idx >= 0) p.splice(idx, 1);
    }
  };
  pool.push(source);
  source.start();
}

// ---- buffer loading ----

/** Determine the asset URL. OGG preferred, WAV fallback. */
function assetUrl(name: SfxName): string {
  // Test if the browser can play OGG (all modern browsers except old Safari).
  if (typeof document !== "undefined") {
    const audio = document.createElement("audio");
    if (audio.canPlayType('audio/ogg; codecs="opus"') || audio.canPlayType("audio/ogg")) {
      return `/desk/sfx/${name}.ogg`;
    }
  }
  return `/desk/sfx/${name}.wav`;
}

async function loadBuffer(name: SfxName): Promise<void> {
  if (bufferCache.has(name)) return;
  if (!audioCtx) return;

  try {
    const url = assetUrl(name);
    const response = await fetch(url);
    if (!response.ok) return;
    const arrayBuffer = await response.arrayBuffer();
    const decoded = await audioCtx.decodeAudioData(arrayBuffer);
    bufferCache.set(name, decoded);
  } catch {
    // Sound loading failed — silently degrade.
  }
}

/** Preload all six sounds. Called once after the first user gesture. */
export function preloadAll(): void {
  if (typeof window === "undefined") return;
  if (!audioCtx) {
    try {
      audioCtx = new AudioContext();
    } catch {
      return;
    }
  }
  for (const name of SFX_NAMES) {
    void loadBuffer(name);
  }
}

// ---- testing helpers ----

/** Reset internal state (for tests only). */
export function _resetForTest(): void {
  audioCtx = null;
  bufferCache.clear();
  activeSources.clear();
  enabled = true;
  reducedMotion = false;
  preloaded = false;
  listeners.clear();
}

/** Inject a mock AudioContext (for tests only). */
export function _setAudioContext(ctx: AudioContext | null): void {
  audioCtx = ctx;
}

/** Inject a buffer into the cache (for tests only). */
export function _setBuffer(name: SfxName, buffer: AudioBuffer): void {
  bufferCache.set(name, buffer);
}

/** Read the active source pool for a sound (for tests only). */
export function _getPool(name: SfxName): AudioBufferSourceNode[] {
  return activeSources.get(name) ?? [];
}

/** Force the reduced-motion flag (for tests only). */
export function _setReducedMotion(on: boolean): void {
  reducedMotion = on;
}
