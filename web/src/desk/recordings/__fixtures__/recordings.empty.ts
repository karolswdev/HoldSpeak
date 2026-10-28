// Recorded by scripts/record_recordings_fixtures.py through the real
// /api/recordings routes (fake ffmpeg, a recorded Tailscale Serve answer).
import type { RecordingsPayload } from "../types";

export const recordingsEmpty: RecordingsPayload = {
  "recordings": [],
  "usage": {
    "bytes": 0,
    "keep_days": 30
  },
  "links": {
    "local": "http://127.0.0.1:8765",
    "tailnet": "https://karols-macbook-pro.tailad9943.ts.net"
  },
  "encoder": "ffmpeg",
  "folder": "/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs-rec-fixtures-msddmjqj/recordings"
};
