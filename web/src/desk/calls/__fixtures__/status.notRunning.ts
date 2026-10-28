// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// GET /api/calls/status: ai-phone installed but its daemon is not running.
import type { CallsStatus } from "../types";

export const statusNotRunning: CallsStatus = {
  enabled: true,
  aiphone: { state: "not_running", words: "Not running" },
  lines: [{ id: "agent", kind: "sip", state: "ready", words: "A SIP address" }],
  engine: { profile_id: "engine-tailscale-karol-8080", model: "qwen3.8-27b", state: "ready", words: "Ready" },
  passphrase_set: true,
  listening: false,
  active: null,
  steps: [
    { id: "install", done: true, words: "Installed" },
    { id: "daemon", done: false, words: "Not running" },
    { id: "line", done: true, words: "A SIP address" },
    { id: "engine", done: true, words: "Ready" },
    { id: "passphrase", done: true, words: "Set" },
    { id: "enable", done: true, words: "On" },
  ],
};
