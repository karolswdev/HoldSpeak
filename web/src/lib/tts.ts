/**
 * HS-154-01 — the ONE client TTS seam.
 *
 * speak(text)           — speak immediately; resolves whether it played (false on Stop)
 * enqueueSentence(text) — queue a sentence; speaks in order
 * stop()                — flush queue, cancel current utterance
 * onStateChange(cb)     — subscribe to state transitions; returns unsubscribe
 *
 * Default path: browser speechSynthesis with a sane local voice pick.
 * Server path:  preferred when GET /api/tts/status says {installed, model_ready}.
 * R4 law:       server first-chunk > 2 s → cancel + fall back to browser voice.
 */

import { apiRequest } from "./api";

// ---- state types ----

export type TtsState = "idle" | "speaking" | "loading";

// ---- module state ----

let state: TtsState = "idle";
let speechEpoch = 0;
const cancelled = new Set<() => void>();
const listeners = new Set<(s: TtsState) => void>();

/** Server status — probed lazily once per session. */
let serverChecked = false;
let serverInstalled = false;
let serverModelReady = false;

/** Whether we prefer the server path (when available). */
let preferServer = false;

/** The sentence queue. */
const queue: string[] = [];
let draining = false;

/** M1: module-level Audio ref so stop() can pause server-voice playback. */
let currentAudio: HTMLAudioElement | null = null;
let currentAudioUrl: string | null = null;

// ---- state machine ----

function setState(next: TtsState): void {
  if (state === next) return;
  state = next;
  listeners.forEach((cb) => {
    try {
      cb(next);
    } catch {
      /* listener errors must not stop the queue */
    }
  });
}

export function getState(): TtsState {
  return state;
}

export function onStateChange(cb: (s: TtsState) => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

// ---- server probe ----

async function probeServer(): Promise<void> {
  if (serverChecked) return;
  serverChecked = true;
  try {
    const res = await apiRequest("/api/tts/status");
    if (res.ok) {
      const data = await res.json();
      serverInstalled = Boolean(data.installed);
      serverModelReady = Boolean(data.model_ready);
      preferServer = serverInstalled && serverModelReady;
    }
  } catch {
    // Server unreachable — stay on browser voice.
  }
}

// ---- browser voice ----

/** S3: Pick the best local voice. Only localService voices are eligible
 *  (Art. III zero-egress). If none exist, return null — speakBrowser
 *  handles null voice gracefully (uses the browser default, which may
 *  be cloud-backed; the caller can choose to skip). */
function pickVoice(): SpeechSynthesisVoice | null {
  if (typeof speechSynthesis === "undefined") return null;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;
  // S3: only local voices — never select a cloud-backed voice.
  const local = voices.filter((v) => v.localService);
  if (!local.length) return null;
  const localEn = local.filter((v) => v.lang.startsWith("en"));
  if (localEn.length) return localEn[0];
  return local[0];
}

function speakBrowser(text: string, localOnly = false): Promise<boolean> {
  return new Promise<boolean>((resolve) => {
    if (typeof speechSynthesis === "undefined") {
      // No speechSynthesis — silent no-op with state event.
      setState("idle");
      resolve(false);
      return;
    }
    const voice = pickVoice();
    if (localOnly && !voice) {
      resolve(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    if (voice) utterance.voice = voice;

    utterance.onend = () => {
      resolve(true);
    };
    utterance.onerror = (e) => {
      // "canceled" is not a real error — it happens on stop().
      if (e.error !== "canceled") {
        // Silent degradation — never crash.
      }
      resolve(false);
    };
    setState("speaking");
    speechSynthesis.speak(utterance);
  });
}

// ---- server voice ----

/** R4 timeout: 2 seconds for the first chunk. */
const R4_TIMEOUT_MS = 2000;

async function speakServer(text: string, epoch: number): Promise<boolean> {
  setState("loading");
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), R4_TIMEOUT_MS);

    const res = await apiRequest("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!res.ok) {
      // Server refused — fall back to browser.
      return false;
    }

    const blob = await res.blob();
    if (!blob.size || epoch !== speechEpoch) return false;

    setState("speaking");
    return new Promise<boolean>((resolve) => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      // M1: hold module-level ref so stop() can pause this element.
      currentAudio = audio;
      currentAudioUrl = url;

      const cleanup = () => {
        if (currentAudio === audio) {
          currentAudio = null;
          currentAudioUrl = null;
        }
        URL.revokeObjectURL(url);
      };

      audio.onended = () => {
        cleanup();
        resolve(true);
      };
      audio.onerror = () => {
        cleanup();
        resolve(false);
      };

      audio.play().catch(() => {
        cleanup();
        resolve(false);
      });
    });
  } catch {
    // AbortError (R4 timeout) or network error — fall back.
    return false;
  }
}

// ---- public API ----

/** Speak immediately and clear the queue. localOnly uses an installed browser
 * voice, with no hub probe or fallback to a cloud voice. */
export async function speak(text: string, options: { localOnly?: boolean } = {}): Promise<boolean> {
  stop();
  const epoch = speechEpoch;
  if (!options.localOnly) await probeServer();
  if (epoch !== speechEpoch) return false;
  return new Promise<boolean>((resolve) => {
    const cancel = () => resolve(false);
    cancelled.add(cancel);
    void speakOne(text, epoch, options.localOnly).then(resolve, () => resolve(false)).finally(() => cancelled.delete(cancel));
  });
}

/** Enqueue a sentence. Sentences are spoken in order; stop() flushes. */
export function enqueueSentence(text: string): void {
  queue.push(text);
  void probeServer().then(() => {
    void drainQueue();
  });
}

/** Stop all speech and flush the queue. */
export function stop(): void {
  speechEpoch += 1;
  for (const cancel of cancelled) cancel();
  cancelled.clear();
  queue.length = 0;
  draining = false;
  // M1: stop server-voice Audio element.
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
      currentAudioUrl = null;
    }
    currentAudio = null;
  }
  if (typeof speechSynthesis !== "undefined") {
    speechSynthesis.cancel();
  }
  setState("idle");
}

// ---- internals ----

async function speakOne(text: string, epoch = speechEpoch, localOnly = false): Promise<boolean> {
  if (!text.trim()) {
    setState("idle");
    return false;
  }

  if (preferServer && !localOnly) {
    const ok = await speakServer(text, epoch);
    if (epoch !== speechEpoch) return false;
    if (ok) {
      setState("idle");
      return true;
    }
    // R4 / error fallback: use browser voice for this utterance.
  }

  const spoken = await speakBrowser(text, localOnly);
  if (epoch === speechEpoch) setState("idle");
  return epoch === speechEpoch && spoken;
}

async function drainQueue(): Promise<void> {
  if (draining) return;
  draining = true;
  while (queue.length > 0 && draining) {
    const text = queue.shift()!;
    await speakOne(text);
  }
  draining = false;
  if (state !== "idle") setState("idle");
}

// ---- test helpers ----

/** Reset internal state (tests only). */
export function _resetForTest(): void {
  stop();
  serverChecked = false;
  serverInstalled = false;
  serverModelReady = false;
  preferServer = false;
  listeners.clear();
  currentAudio = null;
  currentAudioUrl = null;
}

/** Override server preference (tests only). */
export function _setPreferServer(pref: boolean): void {
  serverChecked = true;
  preferServer = pref;
  serverInstalled = pref;
  serverModelReady = pref;
}

/** Read current queue (tests only). */
export function _getQueue(): string[] {
  return [...queue];
}

/** Read server probe state (tests only). */
export function _getServerState(): {
  checked: boolean;
  installed: boolean;
  model_ready: boolean;
  preferServer: boolean;
} {
  return {
    checked: serverChecked,
    installed: serverInstalled,
    model_ready: serverModelReady,
    preferServer,
  };
}
