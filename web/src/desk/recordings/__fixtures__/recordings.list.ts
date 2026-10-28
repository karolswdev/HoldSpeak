// Recorded by scripts/record_recordings_fixtures.py through the real
// /api/recordings routes (fake ffmpeg, a recorded Tailscale Serve answer).
import type { RecordingsPayload } from "../types";

export const recordingsList: RecordingsPayload = {
  "recordings": [
    {
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
    },
    {
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
  ],
  "usage": {
    "bytes": 3018,
    "keep_days": 30
  },
  "links": {
    "local": "http://127.0.0.1:8765",
    "tailnet": "https://karols-macbook-pro.tailad9943.ts.net"
  },
  "encoder": "ffmpeg",
  "folder": "/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs-rec-fixtures-msddmjqj/recordings"
};
