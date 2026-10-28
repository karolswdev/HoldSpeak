/* Recordings (RECORDINGS-DESIGN-2026-10-28 §2): the screen capture of this
 * view. One store for the whole desk: the dock tile, the menu-bar lamp, ⌃⇧R
 * and the Recordings window all read and press the same capture.
 *
 * The browser's own picker opens (`getDisplayMedia`, "this tab" first in
 * Chromium). `MediaRecorder` posts a chunk each 5 s; the hub appends it.
 * Stop, the browser's "Stop sharing", a closed tab (a `keepalive` stop) or a
 * hub that refuses a chunk (another view pressed Stop) ends it. A recording
 * that another view of this desk runs is `remote`: this view shows its lamp
 * and can Stop it. */
import { useSyncExternalStore } from "react";
import { ApiError, apiFetch, apiRequest, readableError } from "../../lib/api";
import type { Recording } from "./types";

export type CapturePhase = "idle" | "asking" | "recording" | "stopping";

export interface CaptureState {
  phase: CapturePhase;
  /** The recording this view captures. */
  id: string | null;
  startedAt: number | null;
  /** A recording another view of this desk captures (from the frame). */
  remote: Recording | null;
  /** The last refusal, in words (no picker, no microphone, the hub said no). */
  error: string;
  voice: boolean;
}

/** One chunk each 5 s (the hub's stale close is 2 minutes). */
export const CHUNK_MS = 5000;
const VOICE_KEY = "hs.recordings.voice";
/** This view's name on the hub (a recording knows which view captures it). */
export const VIEW_ID = `view-${Math.random().toString(36).slice(2, 10)}`;

function readVoice(): boolean {
  try { return window.localStorage.getItem(VOICE_KEY) === "on"; } catch { return false; }
}

let state: CaptureState = { phase: "idle", id: null, startedAt: null, remote: null, error: "", voice: readVoice() };
const listeners = new Set<() => void>();
let recorder: MediaRecorder | null = null;
let tracks: MediaStreamTrack[] = [];
let uploads: Promise<unknown> = Promise.resolve();
let onPageHide: (() => void) | null = null;

function set(next: Partial<CaptureState>): void {
  state = { ...state, ...next };
  listeners.forEach((listener) => listener());
}

export function captureState(): CaptureState {
  return state;
}

export function subscribeCapture(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useCapture(): CaptureState {
  return useSyncExternalStore(subscribeCapture, captureState, captureState);
}

/** The browser can film a screen (an iPhone cannot: no getDisplayMedia). */
export function canCapture(): boolean {
  return typeof navigator !== "undefined" && typeof navigator.mediaDevices?.getDisplayMedia === "function"
    && typeof MediaRecorder !== "undefined";
}

/** A recording runs: here, or on another view. */
export function isLive(current: CaptureState = state): boolean {
  return current.phase === "recording" || current.phase === "stopping" || Boolean(current.remote);
}

export function setVoice(on: boolean): void {
  try { window.localStorage.setItem(VOICE_KEY, on ? "on" : "off"); } catch { /* per-view convenience */ }
  set({ voice: on });
}

function mimeType(audio: boolean): string {
  const wants = audio
    ? ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"]
    : ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"];
  const supported = typeof MediaRecorder.isTypeSupported === "function"
    ? wants.find((type) => MediaRecorder.isTypeSupported(type))
    : undefined;
  return supported ?? "";
}

function release(): void {
  tracks.forEach((track) => { try { track.stop(); } catch { /* already gone */ } });
  tracks = [];
  recorder = null;
  if (onPageHide) {
    window.removeEventListener("pagehide", onPageHide);
    onPageHide = null;
  }
}

async function finish(id: string, tellHub: boolean): Promise<void> {
  await uploads.catch(() => undefined);
  if (tellHub) {
    await apiFetch(`/api/recordings/${encodeURIComponent(id)}/stop`, { method: "POST", json: {} }).catch(() => undefined);
  }
  release();
  set({ phase: "idle", id: null, startedAt: null });
}

/** Start: the picker, then the hub's row, then the recorder. */
export async function startCapture(options: { projectId?: string } = {}): Promise<void> {
  if (state.phase !== "idle" || state.remote) return;
  if (!canCapture()) {
    set({ error: "This browser cannot record the screen" });
    return;
  }
  set({ phase: "asking", error: "" });
  let screen: MediaStream;
  try {
    screen = await navigator.mediaDevices.getDisplayMedia({
      video: { frameRate: 15 },
      audio: false,
      preferCurrentTab: true,
      selfBrowserSurface: "include",
    } as DisplayMediaStreamOptions);
  } catch {
    // He closed the picker: nothing happened, nothing to say.
    set({ phase: "idle" });
    return;
  }
  let mic: MediaStream | null = null;
  let note = "";
  if (state.voice) {
    try {
      mic = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      note = "No microphone; recording without voice";
    }
  }
  tracks = [...screen.getTracks(), ...(mic?.getTracks() ?? [])];
  const video = screen.getVideoTracks()[0];
  const size = video?.getSettings?.() ?? {};
  const stream = new MediaStream([...screen.getVideoTracks(), ...(mic?.getAudioTracks() ?? [])]);
  let row: Recording;
  try {
    row = await apiFetch<Recording>("/api/recordings", {
      method: "POST",
      json: {
        width: size.width ?? 0,
        height: size.height ?? 0,
        voice: Boolean(mic),
        project_id: options.projectId ?? "",
        view: VIEW_ID,
      },
    });
  } catch (error) {
    release();
    set({ phase: "idle", error: readableError(error) });
    return;
  }
  const phone = window.innerWidth <= 520;
  const type = mimeType(Boolean(mic));
  const media = new MediaRecorder(stream, {
    ...(type ? { mimeType: type } : {}),
    videoBitsPerSecond: phone ? 1_200_000 : 2_500_000,
  });
  recorder = media;
  uploads = Promise.resolve();
  const id = row.id;
  media.ondataavailable = (event: BlobEvent) => {
    if (!event.data || event.data.size === 0) return;
    const blob = event.data;
    uploads = uploads.then(() => apiFetch(`/api/recordings/${encodeURIComponent(id)}/chunks`, {
      method: "POST",
      body: blob,
      headers: { "Content-Type": "video/webm" },
    })).catch((error) => {
      // The hub stopped it (another view pressed Stop): end here too.
      if (error instanceof ApiError && (error.status === 409 || error.status === 404) && recorder === media) {
        try { media.stop(); } catch { /* stopped */ }
      }
    });
  };
  media.onstop = () => { void finish(id, true); };
  // The browser's own "Stop sharing" ends the video track.
  video?.addEventListener("ended", () => stopCapture());
  onPageHide = () => {
    void apiRequest(`/api/recordings/${encodeURIComponent(id)}/stop`, {
      method: "POST",
      keepalive: true,
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }).catch(() => undefined);
  };
  window.addEventListener("pagehide", onPageHide);
  media.start(CHUNK_MS);
  set({ phase: "recording", id, startedAt: Date.now(), error: note });
}

/** Stop: this view's recorder (its last chunk, then the hub's stop), or the
 *  recording another view runs. */
export function stopCapture(): void {
  if (state.phase === "recording" && recorder) {
    set({ phase: "stopping" });
    try {
      recorder.stop();
    } catch {
      void finish(state.id ?? "", Boolean(state.id));
    }
    return;
  }
  const remote = state.remote;
  if (remote) {
    set({ remote: null });
    void apiFetch(`/api/recordings/${encodeURIComponent(remote.id)}/stop`, { method: "POST", json: {} })
      .catch((error) => set({ remote, error: readableError(error) }));
  }
}

/** The press of the tile and of ⌃⇧R. */
export function toggleCapture(options: { projectId?: string } = {}): void {
  if (isLive()) stopCapture();
  else void startCapture(options);
}

/** A `recording_state` frame (or the first read): another view's live
 *  recording becomes `remote`; this view's own recording, stopped by the hub,
 *  stops here. */
export function applyRecording(row: Recording | null | undefined): void {
  if (!row) return;
  if (row.id === state.id) {
    if (row.state !== "recording" && state.phase === "recording" && recorder) {
      try { recorder.stop(); } catch { /* stopped */ }
    }
    return;
  }
  if (row.state === "recording" && row.view !== VIEW_ID) {
    set({ remote: row });
  } else if (state.remote?.id === row.id) {
    set({ remote: null });
  }
}

/** Seconds since the live recording started (here or on another view). */
export function liveStartedAt(current: CaptureState = state): number | null {
  if (current.startedAt) return current.startedAt;
  if (current.remote?.started_ts) return current.remote.started_ts * 1000;
  return null;
}

export function resetCaptureForTests(): void {
  release();
  uploads = Promise.resolve();
  state = { phase: "idle", id: null, startedAt: null, remote: null, error: "", voice: false };
  listeners.forEach((listener) => listener());
}
