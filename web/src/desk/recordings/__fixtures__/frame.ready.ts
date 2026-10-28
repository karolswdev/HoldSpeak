// Recorded by scripts/record_recordings_fixtures.py through the real
// /api/recordings routes (fake ffmpeg, a recorded Tailscale Serve answer).
import type { RecordingStateFrame } from "../types";

export const frameReady: RecordingStateFrame = {
  "reason": "ready",
  "recording": {
    "id": "r2fd814f216",
    "started_ts": 1793214136.160115,
    "title": "Recording · Wed 28 Oct 15:02",
    "state": "ready",
    "ended_ts": 1793214136.1847308,
    "last_chunk_ts": 1793214136.176078,
    "bytes_in": 832,
    "bytes_out": 832,
    "chunks": 2,
    "width": 2880,
    "height": 1800,
    "duration_s": 2.380952380952381,
    "voice": false,
    "project_id": "",
    "note_ref": "note:n-rec-1",
    "progress": 100,
    "error": "",
    "encoder": "mp4",
    "view": "view-mac",
    "started_at": "2026-10-28T19:02:16.160115Z",
    "ended_at": "2026-10-28T19:02:16.184731Z",
    "shared": true,
    "video_name": "recording-2026-10-28-1502.mp4",
    "links": {
      "tailnet": "https://karols-macbook-pro.tailad9943.ts.net/r/r2fd814f216/IfW6EiHhkO8Vnw2UK4Wvhvx8/recording-2026-10-28-1502.mp4",
      "local": "http://127.0.0.1:8765/r/r2fd814f216/IfW6EiHhkO8Vnw2UK4Wvhvx8/recording-2026-10-28-1502.mp4"
    }
  }
};
