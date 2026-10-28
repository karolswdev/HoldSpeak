// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// GET /api/calls/status: ai-phone running, a SIP address line, the home
// engine ready, a passphrase set, Calls on, nobody on the line.
import type { CallsStatus } from "../types";

export const statusReady: CallsStatus = {
  enabled: true,
  aiphone: { state: "running", words: "Running" },
  lines: [{ id: "agent", kind: "sip", state: "ready", words: "A SIP address" }],
  engine: { profile_id: "engine-tailscale-karol-8080", model: "qwen3.8-27b", state: "ready", words: "Ready" },
  passphrase_set: true,
  listening: true,
  active: null,
  steps: [
    { id: "install", done: true, words: "Installed" },
    { id: "daemon", done: true, words: "Running" },
    { id: "line", done: true, words: "A SIP address" },
    { id: "engine", done: true, words: "Ready" },
    { id: "passphrase", done: true, words: "Set" },
    { id: "enable", done: true, words: "On" },
  ],
};
