// HS-41-03: minimal runtime-presence HUD driver.
//
// Connects to /ws, renders the Signal presence card from `runtime_activity`
// messages, and hides the card when the activity window policy says hidden
// (idle). Seeds from /api/state on load, and auto-reconnects. No framework —
// this is loaded in a small native webview, so it stays tiny.

const card = document.getElementById("presence-card");
const ring = document.getElementById("presence-ring");
const labelEl = document.getElementById("presence-label");
const detailEl = document.getElementById("presence-detail");
const sourceEl = document.getElementById("presence-source");

const LABELS = {
  idle: "Ready",
  listening: "Listening",
  recording: "Recording",
  transcribing: "Transcribing",
  processing: "Processing",
  typing: "Typing",
  complete: "Complete",
  meeting_live: "Meeting live",
  saving: "Saving",
  error: "Needs attention",
};
const SOURCES = {
  hotkey: "Hotkey",
  device: "Device",
  dictation: "Dictation",
  meeting: "Meeting",
  runtime: "Runtime",
  voice: "Voice",
};

function toneClass(state) {
  if (state === "error") return "tone-error";
  if (state === "complete") return "tone-complete";
  if (state === "recording" || state === "listening" || state === "meeting_live")
    return "tone-recording";
  if (state === "idle") return "tone-idle";
  return "tone-working";
}

function isLive(state) {
  return !["idle", "complete", "error"].includes(state);
}

function applyActivity(activity) {
  if (!activity || typeof activity !== "object") return;
  // HS-56-02: let the mascot layer (qlippy.js) follow the same stream.
  document.dispatchEvent(new CustomEvent("hs-activity", { detail: activity }));
  const state = String(activity.state || "idle").trim().toLowerCase() || "idle";
  const policy = activity.window && typeof activity.window === "object" ? activity.window : {};
  const visible = policy.visible !== undefined ? Boolean(policy.visible) : state !== "idle";

  card.hidden = !visible;
  if (!visible) return;

  card.className = "presence-card " + toneClass(state);
  ring.className = "presence-ring" + (isLive(state) ? " is-live" : "");
  labelEl.textContent = String(activity.label || LABELS[state] || "Ready").trim() || "Ready";
  detailEl.textContent = String(
    activity.last_error || activity.detail || activity.last_event || ""
  ).trim();
  const source = String(activity.source || "runtime").trim().toLowerCase();
  sourceEl.textContent = SOURCES[source] || source || "Runtime";
}

// Seed from the current runtime state so the HUD reflects reality immediately.
fetch("/api/state")
  .then((r) => r.json())
  .then((state) => {
    const activity =
      (state && state.activity) || (state && state.runtime && state.runtime.activity);
    if (activity) applyActivity(activity);
  })
  .catch(() => {});

function connect() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${proto}//${window.location.host}/ws`);
  ws.onmessage = (event) => {
    let msg = null;
    try {
      msg = JSON.parse(event.data);
    } catch (_e) {
      return;
    }
    if (msg && msg.type === "runtime_activity") applyActivity(msg.data);
    // HS-56-02: re-dispatch every broadcast as a DOM event so the mascot's
    // card stories (actuator / learning / aftercare) ride the same socket.
    if (msg && msg.type) {
      document.dispatchEvent(new CustomEvent("hs-broadcast", { detail: msg }));
    }
  };
  ws.onclose = () => window.setTimeout(connect, 1500);
  ws.onerror = () => {};
}

connect();
