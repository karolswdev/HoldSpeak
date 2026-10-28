// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// GET /api/calls/status: ai-phone not installed, Calls off, no passphrase.
import type { CallsStatus } from "../types";

export const statusOff: CallsStatus = {
  enabled: false,
  aiphone: { state: "not_found", words: "Not installed" },
  lines: [],
  engine: { profile_id: "engine-tailscale-karol-8080", model: "qwen3.8-27b", state: "ready", words: "Ready" },
  passphrase_set: false,
  listening: false,
  active: null,
  steps: [
    { id: "install", done: false, words: "Not installed" },
    { id: "daemon", done: false, words: "Not running" },
    { id: "line", done: false, words: "No line" },
    { id: "engine", done: true, words: "Ready" },
    { id: "passphrase", done: false, words: "Not set" },
    { id: "enable", done: false, words: "Off" },
  ],
};
