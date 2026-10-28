// Recorded by scripts/record_recordings_fixtures.py through the real
// /api/recordings routes (fake ffmpeg, a recorded Tailscale Serve answer).
import type { RecordingStateFrame } from "../types";

export const frameRemoteStarted: RecordingStateFrame = {
  "reason": "started",
  "recording": {
    "id": "r2fd814f216",
    "started_ts": 1793214136.160115,
    "title": "Recording · Wed 28 Oct 15:02",
    "state": "recording",
    "ended_ts": null,
    "last_chunk_ts": 1793214136.160115,
    "bytes_in": 0,
    "bytes_out": 0,
    "chunks": 0,
    "width": 2880,
    "height": 1800,
    "duration_s": 0.0,
    "voice": false,
    "project_id": "",
    "note_ref": "",
    "progress": 0,
    "error": "",
    "encoder": "",
    "view": "view-other",
    "started_at": "2026-10-28T19:02:16.160115Z",
    "ended_at": null,
    "shared": true,
    "video_name": null,
    "links": {
      "tailnet": null,
      "local": null
    }
  }
};
