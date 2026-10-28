/* Recordings (RECORDINGS-DESIGN-2026-10-28 §4): the wire shapes of
 * `/api/recordings` and the `recording_state` frame. */

export type RecordingState = "recording" | "encoding" | "ready" | "failed";

export interface RecordingLinks {
  /** The Tailscale link (Tailscale Serve proxies to this hub), or none. */
  tailnet: string | null;
  /** The 127.0.0.1 link. */
  local: string | null;
}

export interface Recording {
  id: string;
  title: string;
  state: RecordingState;
  started_ts: number;
  ended_ts: number | null;
  last_chunk_ts: number | null;
  started_at: string | null;
  ended_at: string | null;
  bytes_in: number;
  bytes_out: number;
  chunks: number;
  width: number;
  height: number;
  duration_s: number;
  voice: boolean;
  project_id: string;
  note_ref: string;
  progress: number;
  error: string;
  /** `mp4` (ffmpeg made it) or `webm` (no ffmpeg); empty until ready. */
  encoder: "" | "mp4" | "webm";
  view: string;
  shared: boolean;
  video_name: string | null;
  links: RecordingLinks;
}

export interface RecordingsPayload {
  recordings: Recording[];
  usage: { bytes: number; keep_days: number };
  links: RecordingLinks;
  /** `ffmpeg` or `none` (kept as webm). */
  encoder: "ffmpeg" | "none";
  folder: string;
}

export type RecordingFrameReason =
  | "started" | "chunk" | "stopped" | "encoding" | "progress"
  | "ready" | "failed" | "parked" | "shared";

export interface RecordingStateFrame {
  reason: RecordingFrameReason;
  recording: Recording;
}
