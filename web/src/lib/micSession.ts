// HS-112-06 — ONE microphone session for the whole Desk.
//
// Before this module every hold requested `getUserMedia` and tore the
// device down on release: a permission-and-teardown cycle per utterance,
// on the deprecated `ScriptProcessorNode`. Now the Desk asks for the
// microphone ONCE and keeps the grant: between utterances the session is
// SUSPENDED (context suspended, tracks disabled — nothing is captured),
// never re-requested. One `AudioWorklet` processor feeds BOTH the
// push-to-talk holds and the open mic; the RMS level tap the cockpit
// meters ride on is emitted from the same frames.
//
// The floor is still one. A hold (TALK, or any MicButton on the desk)
// preempts the open mic: while `holdActive` the open mic's frames are
// gated off and its in-flight utterance is dropped — the hold owns the
// floor exactly as the physical hotkey does.
//
// Off is real. `closeMicSession()` calls `MediaStreamTrack.stop()`; when
// the phase says CLOSED the device is released, not muted.

import { createVad, frameRms, type Vad, type VadTuning } from "./vad";

/** Samples per posted frame — ~21 ms at 48 kHz, ~64 ms at 16 kHz. */
const FRAME_SAMPLES = 1024;

/** A suspended session with nothing holding it is released after this.
 *  Short enough that the mic indicator never lingers past a working
 *  pause; long enough that a run of utterances costs ONE grant. */
export const IDLE_RELEASE_MS = 15_000;

/* The capture processor. Inlined and loaded as a blob module: an
   AudioWorklet needs a same-origin module URL and this keeps it in the
   bundle (no extra asset, no fetch). It only batches frames — every
   decision lives on the main thread. */
const WORKLET_SOURCE = `
class HoldspeakCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(${FRAME_SAMPLES});
    this.filled = 0;
  }
  process(inputs) {
    const input = inputs[0] && inputs[0][0];
    if (input) {
      for (let i = 0; i < input.length; i += 1) {
        this.buffer[this.filled] = input[i];
        this.filled += 1;
        if (this.filled === ${FRAME_SAMPLES}) {
          this.port.postMessage(this.buffer.slice(0));
          this.filled = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor("holdspeak-capture", HoldspeakCaptureProcessor);
`;

export type MicPhase = "closed" | "suspended" | "open" | "segmenting" | "held";

type Session = {
  stream: MediaStream;
  context: AudioContext;
  source: MediaStreamAudioSourceNode;
  node: AudioNode & { disconnect: () => void };
  rate: number;
  workletUrl: string | null;
};

type Segment = { chunks: Float32Array[]; rate: number };

let session: Session | null = null;
let starting: Promise<Session> | null = null;
let holdActive = false;
let holdChunks: Float32Array[] = [];
let openMicOn = false;
let vad: Vad | null = null;
let onSegment: ((segment: Segment) => void) | null = null;
let idleTimer: ReturnType<typeof setTimeout> | null = null;
let phase: MicPhase = "closed";

/* ── the taps: level (meters) and phase (the lamp that never lies) ── */

type LevelListener = (level: number) => void;
const levelListeners = new Set<LevelListener>();

export function subscribeCaptureLevel(listener: LevelListener): () => void {
  levelListeners.add(listener);
  return () => {
    levelListeners.delete(listener);
  };
}

function emitLevel(level: number): void {
  levelListeners.forEach((listener) => listener(level));
}

type PhaseListener = (phase: MicPhase) => void;
const phaseListeners = new Set<PhaseListener>();

export function subscribeMicPhase(listener: PhaseListener): () => void {
  phaseListeners.add(listener);
  listener(phase);
  return () => {
    phaseListeners.delete(listener);
  };
}

export function micPhase(): MicPhase {
  return phase;
}

function setPhase(next: MicPhase): void {
  if (phase === next) return;
  phase = next;
  phaseListeners.forEach((listener) => listener(next));
}

/** The phase the session is in when nothing is being captured. */
function restPhase(): MicPhase {
  if (!session) return "closed";
  if (holdActive) return "held";
  if (openMicOn) return vad?.state() === "speaking" ? "segmenting" : "open";
  return "suspended";
}

/* ── support (unchanged contract; the LAN-origin trap still speaks) ── */

type AudioWindow = Window &
  typeof globalThis & { webkitAudioContext?: typeof AudioContext };

export function micCaptureSupported(): boolean {
  const audioWindow = window as AudioWindow;
  return (
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    ("AudioContext" in window ||
      typeof audioWindow.webkitAudioContext === "function") &&
    // HS-112-06: the capture path is an AudioWorklet, full stop — there is
    // no deprecated ScriptProcessor fallback to hide behind, so a browser
    // without one is honestly unsupported rather than quietly degraded.
    typeof AudioWorkletNode === "function"
  );
}

/** Why capture is unavailable, or null when it is available.
 *
 * The mic must never vanish silently (Article VI): on a plain-HTTP LAN
 * origin the browser withholds `navigator.mediaDevices` entirely, and the
 * honest state is a disabled mic that says so. */
export function micCaptureReason(): string | null {
  if (micCaptureSupported()) return null;
  if (!navigator.mediaDevices && window.isSecureContext === false)
    return (
      "Mic capture needs a secure origin. Open this hub via localhost " +
      "or HTTPS to speak."
    );
  return "This browser cannot capture microphone audio.";
}

/* ── the session itself ── */

/** Await an AudioContext verb that a stubbed context may not have. */
async function settle(value: unknown): Promise<void> {
  if (value && typeof (value as Promise<void>).then === "function")
    await (value as Promise<void>).catch(() => undefined);
}

function clearIdleTimer(): void {
  if (idleTimer !== null) clearTimeout(idleTimer);
  idleTimer = null;
}

/** Nothing is holding the mic: keep the grant, capture nothing, and let
 *  the device go if the pause outlasts `IDLE_RELEASE_MS`. */
function idle(): void {
  if (!session || holdActive || openMicOn) return;
  session.stream.getAudioTracks().forEach((track) => {
    track.enabled = false;
  });
  void settle(session.context.suspend?.());
  emitLevel(0);
  setPhase("suspended");
  clearIdleTimer();
  idleTimer = setTimeout(() => {
    idleTimer = null;
    if (!holdActive && !openMicOn) closeMicSession();
  }, IDLE_RELEASE_MS);
}

/** Frames in. One path for the hold and the open mic; the hold wins. */
function onFrame(samples: Float32Array): void {
  // Speech RMS sits around 0.05–0.3; ×4 spreads it over the meter.
  emitLevel(Math.min(1, frameRms(samples) * 4));
  if (holdActive) {
    holdChunks.push(samples);
    return;
  }
  if (!openMicOn || !vad) return;
  for (const event of vad.push(samples)) {
    if (event.type === "speech-start") setPhase("segmenting");
    if (event.type === "dropped") setPhase("open");
    if (event.type === "utterance") {
      setPhase("open");
      onSegment?.({ chunks: event.chunks, rate: event.rate });
    }
  }
}

async function buildSession(): Promise<Session> {
  if (!micCaptureSupported())
    throw new Error("This browser cannot capture microphone audio.");
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioWindow = window as AudioWindow;
  const Context = window.AudioContext || audioWindow.webkitAudioContext;
  if (!Context)
    throw new Error("Audio capture is not supported by this browser.");
  const context = new Context();
  const source = context.createMediaStreamSource(stream);
  let node: (AudioNode & { disconnect: () => void }) | null = null;
  let workletUrl: string | null = null;
  const worklet = (
    context as AudioContext & { audioWorklet?: AudioWorklet }
  ).audioWorklet;
  if (!worklet || typeof AudioWorkletNode !== "function") {
    void settle(context.close?.());
    stream.getTracks().forEach((track) => track.stop());
    throw new Error("This browser cannot capture microphone audio.");
  }
  workletUrl = URL.createObjectURL(
    new Blob([WORKLET_SOURCE], { type: "text/javascript" }),
  );
  await worklet.addModule(workletUrl);
  const workletNode = new AudioWorkletNode(context, "holdspeak-capture");
  workletNode.port.onmessage = (event: MessageEvent) => {
    onFrame(new Float32Array(event.data as ArrayLike<number>));
  };
  node = workletNode;
  source.connect(node);
  node.connect(context.destination);
  return { stream, context, source, node, rate: context.sampleRate, workletUrl };
}

/** The grant. Called by every capture path; requests the device ONCE. */
async function ensureSession(): Promise<Session> {
  clearIdleTimer();
  if (session) {
    session.stream.getAudioTracks().forEach((track) => {
      track.enabled = true;
    });
    await settle(session.context.resume?.());
    return session;
  }
  if (!starting) {
    starting = buildSession()
      .then((built) => {
        session = built;
        return built;
      })
      .finally(() => {
        starting = null;
      });
  }
  return starting;
}

/** Off, for real: the tracks are stopped, not muted. */
export function closeMicSession(): void {
  clearIdleTimer();
  holdActive = false;
  holdChunks = [];
  openMicOn = false;
  vad = null;
  onSegment = null;
  const current = session;
  session = null;
  if (current) {
    try {
      current.source.disconnect();
      current.node.disconnect();
    } catch {
      /* already torn down */
    }
    current.stream.getTracks().forEach((track) => track.stop());
    if (current.workletUrl) URL.revokeObjectURL(current.workletUrl);
    void settle(current.context.close?.());
  }
  emitLevel(0);
  setPhase("closed");
}

/** True while the Desk holds a microphone grant (open OR suspended). */
export function micSessionLive(): boolean {
  return session !== null;
}

/* ── push-to-talk: the floor's first owner ── */

export async function beginHold(): Promise<void> {
  holdChunks = [];
  holdActive = true;
  // the open mic yields mid-word rather than double-capturing.
  vad?.reset();
  try {
    await ensureSession();
  } catch (error) {
    holdActive = false;
    setPhase(restPhase());
    throw error;
  }
  if (!holdActive) return; // released before the grant landed
  setPhase("held");
}

/** End the hold and hand back what it captured (null when nothing). */
export function endHold(): { chunks: Float32Array[]; rate: number } | null {
  if (!holdActive) return null;
  holdActive = false;
  const chunks = holdChunks;
  holdChunks = [];
  const rate = session?.rate ?? 16_000;
  if (openMicOn) {
    vad?.reset();
    setPhase(restPhase());
  } else {
    idle();
  }
  emitLevel(0);
  return chunks.length ? { chunks, rate } : null;
}

/** Abandon the hold, keeping the grant (the gesture was cancelled). */
export function abortHold(): void {
  if (!holdActive) return;
  holdActive = false;
  holdChunks = [];
  if (openMicOn) {
    vad?.reset();
    setPhase(restPhase());
  } else {
    idle();
  }
  emitLevel(0);
}

/** True while a hold owns the floor (the open mic is gated off). */
export function holdOwnsFloor(): boolean {
  return holdActive;
}

/* ── the open mic ── */

export async function startOpenMic(
  handler: (segment: Segment) => void,
  tuning?: Partial<VadTuning>,
): Promise<void> {
  const live = await ensureSession();
  onSegment = handler;
  vad = createVad(live.rate, tuning);
  openMicOn = true;
  setPhase(holdActive ? "held" : "open");
}

/** One verb drops the stream entirely — the lamp goes CLOSED because
 *  the device is closed. A live hold keeps its own grant. */
export function stopOpenMic(): void {
  openMicOn = false;
  vad = null;
  onSegment = null;
  if (holdActive) {
    setPhase("held");
    return;
  }
  closeMicSession();
}

export function openMicRunning(): boolean {
  return openMicOn;
}
