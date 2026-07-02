// HS-41-03: minimal runtime-presence HUD driver.
//
// Renders the Signal presence card from `runtime_activity` frames and hides
// the card when the activity window policy says hidden (idle). Phase 72: the
// frames arrive over the ONE runtime bus (runtime-bus.js — it owns the /ws
// socket, the reconnects, the seed, and the hs-activity/hs-broadcast DOM
// dispatch that qlippy.js rides). No framework — this is loaded in a small
// native webview, so it stays tiny.

import { seedState, subscribe } from "./runtime-bus.js";

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
  // (The bus dispatches hs-activity/hs-broadcast for the mascot layer.)
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

// The bus seeds from /api/state (through the same delivery pipeline as wire
// frames, so qlippy sees the seed too) and keeps the card live from there.
subscribe("runtime_activity", (data) => applyActivity(data));
seedState();
