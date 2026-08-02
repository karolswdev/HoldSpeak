// HS-112-06 — where an utterance starts and where it ends.
//
// Synthetic PCM in, boundaries out: the detector is pure, so the rules
// the owner will hear on the real desk (a breath does not cut a
// sentence; a door slam is not words; a stuck mic still delivers) are
// pinned here rather than argued about.
import { describe, expect, it } from "vitest";
import { createVad, frameRms, VAD_TUNING } from "../vad";

const RATE = 16_000;
const FRAME = 1024; // 64 ms at 16 kHz — the session's own frame size.

/** One frame at a given RMS. */
function frame(rms: number): Float32Array {
  const samples = new Float32Array(FRAME);
  for (let index = 0; index < FRAME; index += 1)
    samples[index] = index % 2 ? rms : -rms;
  return samples;
}

const LOUD = frame(0.2);
const QUIET = frame(0.001);

function feed(
  vad: ReturnType<typeof createVad>,
  samples: Float32Array,
  count: number,
) {
  const events = [];
  for (let index = 0; index < count; index += 1)
    events.push(...vad.push(samples));
  return events;
}

describe("VAD segmentation (HS-112-06)", () => {
  it("measures frame RMS", () => {
    expect(frameRms(LOUD)).toBeCloseTo(0.2, 5);
    expect(frameRms(new Float32Array(0))).toBe(0);
  });

  it("opens only after sustained speech, then closes on the hangover", () => {
    const vad = createVad(RATE);
    // one loud frame (64 ms) is under openMs — no utterance yet.
    expect(feed(vad, LOUD, 1)).toEqual([]);
    expect(vad.state()).toBe("quiet");
    const opened = feed(vad, LOUD, 1);
    expect(opened).toEqual([{ type: "speech-start" }]);
    expect(vad.state()).toBe("speaking");
    // enough speech to clear the minimum, then silence past the hangover.
    feed(vad, LOUD, 6);
    const closing = feed(vad, QUIET, 12);
    const utterance = closing.find((event) => event.type === "utterance");
    expect(utterance).toBeTruthy();
    expect(utterance).toMatchObject({ rate: RATE, reason: "hangover" });
    expect(vad.state()).toBe("quiet");
  });

  it("keeps pre-roll so the first phoneme is not clipped", () => {
    const vad = createVad(RATE);
    feed(vad, QUIET, 10); // room tone — trimmed to preRollMs
    feed(vad, LOUD, 8);
    const [utterance] = feed(vad, QUIET, 12).filter(
      (event) => event.type === "utterance",
    );
    expect(utterance.type).toBe("utterance");
    if (utterance.type !== "utterance") return;
    const heldMs = (utterance.chunks.length * FRAME * 1000) / RATE;
    const spokenMs = (8 * FRAME * 1000) / RATE;
    // the head carries pre-roll, and it is bounded (never the whole tape).
    expect(heldMs).toBeGreaterThan(spokenMs);
    expect(heldMs).toBeLessThan(
      spokenMs + VAD_TUNING.preRollMs + VAD_TUNING.hangoverMs + 200,
    );
  });

  it("a breath inside a sentence does not cut it in two", () => {
    const vad = createVad(RATE);
    feed(vad, LOUD, 6);
    feed(vad, QUIET, 5); // 320 ms — under the 700 ms hangover
    const mid = feed(vad, LOUD, 6);
    expect(mid.filter((event) => event.type === "utterance")).toHaveLength(0);
    const events = feed(vad, QUIET, 12);
    expect(events.filter((event) => event.type === "utterance")).toHaveLength(1);
  });

  it("drops a slam shorter than the minimum instead of delivering it", () => {
    const vad = createVad(RATE, { minUtteranceMs: 600 });
    feed(vad, LOUD, 4); // ~256 ms of speech
    const events = feed(vad, QUIET, 12);
    expect(events).toEqual([
      { type: "dropped", reason: "too-short", speechMs: expect.any(Number) },
    ]);
  });

  it("cuts an unending utterance at the ceiling", () => {
    const vad = createVad(RATE, { maxUtteranceMs: 1000 });
    const events = feed(vad, LOUD, 40);
    const cut = events.filter((event) => event.type === "utterance");
    expect(cut.length).toBeGreaterThanOrEqual(1);
    expect(cut[0]).toMatchObject({ reason: "max" });
  });

  it("reset forgets the in-flight utterance (a hold took the floor)", () => {
    const vad = createVad(RATE);
    feed(vad, LOUD, 8);
    expect(vad.state()).toBe("speaking");
    vad.reset();
    expect(vad.state()).toBe("quiet");
    expect(feed(vad, QUIET, 12)).toEqual([]);
  });

  it("flush closes what is in flight when the mic is dropped", () => {
    const vad = createVad(RATE);
    feed(vad, LOUD, 8);
    const events = vad.flush();
    expect(events[0]).toMatchObject({ type: "utterance" });
    expect(vad.flush()).toEqual([]);
  });

  it("two utterances separated by silence arrive as two segments", () => {
    const vad = createVad(RATE);
    const events = [
      ...feed(vad, LOUD, 8),
      ...feed(vad, QUIET, 12),
      ...feed(vad, LOUD, 8),
      ...feed(vad, QUIET, 12),
    ];
    expect(events.filter((event) => event.type === "utterance")).toHaveLength(2);
  });
});
