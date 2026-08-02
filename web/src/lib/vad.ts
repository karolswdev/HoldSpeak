// HS-112-06 — the edge VAD: where an utterance starts and where it ends.
//
// Energy + hangover, no model. Frames arrive from the one capture worklet
// (lib/micSession); the detector answers with events, never with I/O — it
// is pure so the boundaries can be pinned by test with synthetic PCM.
//
// The shape: an utterance OPENS after `openMs` of frames above `openRms`
// (with `preRollMs` of history prepended so the first phoneme survives),
// and CLOSES after `hangoverMs` of frames below `closeRms`. Two
// thresholds, not one — hysteresis keeps a breath mid-sentence from
// cutting the utterance in half. Anything shorter than `minUtteranceMs`
// of actual speech is a door slam, not words: dropped. Anything longer
// than `maxUtteranceMs` is cut so a stuck-open mic still delivers.

export type VadTuning = {
  /** RMS at or above which a frame counts as speech. */
  openRms: number;
  /** RMS below which a frame counts as silence (hysteresis floor). */
  closeRms: number;
  /** Speech this long opens an utterance. */
  openMs: number;
  /** Trailing silence this long closes it. */
  hangoverMs: number;
  /** Audio kept before the open so the first phoneme is not clipped. */
  preRollMs: number;
  /** Speech shorter than this is dropped (a cough, a keystroke). */
  minUtteranceMs: number;
  /** An utterance is cut at this length no matter what. */
  maxUtteranceMs: number;
};

/* Tuning lives HERE, in one block, in real units — the only place these
   numbers exist. Speech RMS on a laptop mic sits ~0.03–0.25; room tone
   sits under 0.01. Raise `openRms` in a loud room, lower it for a quiet
   talker; lengthen `hangoverMs` if slow speech gets chopped mid-thought,
   shorten it for a snappier turn. */
export const VAD_TUNING: VadTuning = {
  openRms: 0.02,
  closeRms: 0.012,
  openMs: 120,
  hangoverMs: 700,
  preRollMs: 300,
  minUtteranceMs: 350,
  maxUtteranceMs: 15_000,
};

export type VadEvent =
  | { type: "speech-start" }
  | {
      type: "utterance";
      chunks: Float32Array[];
      rate: number;
      /** Speech milliseconds, trailing hangover excluded. */
      speechMs: number;
      /** Why it closed: silence, or the hard ceiling. */
      reason: "hangover" | "max";
    }
  | { type: "dropped"; reason: "too-short"; speechMs: number };

export type VadState = "quiet" | "speaking";

export type Vad = {
  /** Feed one frame of mono float samples. Returns what it decided. */
  push(samples: Float32Array): VadEvent[];
  /** Forget the in-flight utterance (a PTT hold took the floor). */
  reset(): void;
  /** Close whatever is in flight — used when the mic is dropped. */
  flush(): VadEvent[];
  state(): VadState;
};

/** RMS of one frame, 0..1. Exported for the level tap and for tests. */
export function frameRms(samples: Float32Array): number {
  if (!samples.length) return 0;
  let sum = 0;
  for (let index = 0; index < samples.length; index += 1)
    sum += samples[index] * samples[index];
  return Math.sqrt(sum / samples.length);
}

export function createVad(
  rate: number,
  tuning: Partial<VadTuning> = {},
): Vad {
  const t: VadTuning = { ...VAD_TUNING, ...tuning };
  let state: VadState = "quiet";
  // pre-roll ring: frames held while quiet, trimmed to preRollMs.
  let preRoll: Float32Array[] = [];
  let preRollMs = 0;
  let chunks: Float32Array[] = [];
  let speechMs = 0;
  let silenceMs = 0;
  let candidateMs = 0;

  const msOf = (samples: Float32Array) => (samples.length / rate) * 1000;

  const reset = () => {
    state = "quiet";
    preRoll = [];
    preRollMs = 0;
    chunks = [];
    speechMs = 0;
    silenceMs = 0;
    candidateMs = 0;
  };

  /** Close the in-flight utterance: emit it, or drop it as too short. */
  const close = (reason: "hangover" | "max"): VadEvent[] => {
    const emitted = chunks;
    const heard = speechMs;
    reset();
    if (heard < t.minUtteranceMs)
      return [{ type: "dropped", reason: "too-short", speechMs: heard }];
    return [
      { type: "utterance", chunks: emitted, rate, speechMs: heard, reason },
    ];
  };

  return {
    state: () => state,
    reset,
    flush: () => (state === "speaking" ? close("hangover") : []),
    push(samples: Float32Array): VadEvent[] {
      if (!samples.length) return [];
      const ms = msOf(samples);
      const rms = frameRms(samples);
      const events: VadEvent[] = [];

      if (state === "quiet") {
        preRoll.push(samples);
        preRollMs += ms;
        while (preRoll.length > 1 && preRollMs - msOf(preRoll[0]) >= t.preRollMs)
          preRollMs -= msOf(preRoll.shift() as Float32Array);
        candidateMs = rms >= t.openRms ? candidateMs + ms : 0;
        if (candidateMs < t.openMs) return events;
        // OPEN — the pre-roll IS the head of the utterance.
        state = "speaking";
        chunks = preRoll;
        speechMs = candidateMs;
        silenceMs = 0;
        preRoll = [];
        preRollMs = 0;
        candidateMs = 0;
        events.push({ type: "speech-start" });
        return events;
      }

      chunks.push(samples);
      if (rms < t.closeRms) {
        silenceMs += ms;
      } else {
        silenceMs = 0;
        speechMs += ms;
      }
      if (silenceMs >= t.hangoverMs) return [...events, ...close("hangover")];
      if (speechMs + silenceMs >= t.maxUtteranceMs)
        return [...events, ...close("max")];
      return events;
    },
  };
}
