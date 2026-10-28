// Recorded by scripts/record_recordings_fixtures.py through the real
// /api/recordings routes (fake ffmpeg, a recorded Tailscale Serve answer).
import type { RecordingStateFrame } from "../types";

export const frameEncoding: RecordingStateFrame = {
  "reason": "progress",
  "recording": {
    "id": "r2fd814f216",
    "started_ts": 1793214136.160115,
    "title": "Recording · Wed 28 Oct 15:02",
    "state": "encoding",
    "ended_ts": 1793214136.1847308,
    "last_chunk_ts": 1793214136.176078,
    "bytes_in": 832,
    "bytes_out": 0,
    "chunks": 2,
    "width": 2880,
    "height": 1800,
    "duration_s": 2.380952380952381,
    "voice": false,
    "project_id": "",
    "note_ref": "",
    "progress": 42,
    "error": "",
    "encoder": "",
    "view": "view-mac",
    "started_at": "2026-10-28T19:02:16.160115Z",
    "ended_at": "2026-10-28T19:02:16.184731Z",
    "shared": true,
    "video_name": null,
    "links": {
      "tailnet": null,
      "local": null
    }
  }
};
