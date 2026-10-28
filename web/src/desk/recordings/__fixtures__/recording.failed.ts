// Recorded by scripts/record_recordings_fixtures.py through the real
// /api/recordings routes (fake ffmpeg, a recorded Tailscale Serve answer).
import type { Recording } from "../types";

export const recordingFailed: Recording = {
  "id": "r50c7feff04",
  "started_ts": 1793214136.228478,
  "title": "Recording · Wed 28 Oct 15:02",
  "state": "failed",
  "ended_ts": 1793214136.236307,
  "last_chunk_ts": 1793214136.232151,
  "bytes_in": 192,
  "bytes_out": 0,
  "chunks": 1,
  "width": 1440,
  "height": 900,
  "duration_s": 0.007828950881958008,
  "voice": false,
  "project_id": "",
  "note_ref": "",
  "progress": 0,
  "error": "ffmpeg stopped (1): in.webm: Invalid data found when processing input",
  "encoder": "",
  "view": "view-mac",
  "started_at": "2026-10-28T19:02:16.228478Z",
  "ended_at": "2026-10-28T19:02:16.236307Z",
  "shared": true,
  "video_name": null,
  "links": {
    "tailnet": null,
    "local": null
  }
};
