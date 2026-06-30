// HS-69-09: the generation theater — store + DOM driver.
//
// The web port of the iPad "model-thinking" theater (the plasma orb + rings +
// the artifact-type constellation lighting per artifact; MeetingCaptureApp.swift
// :4526-4614). It is driven LIVE by the meeting-intelligence WS frames that
// already flow — NO backend change (web-technical-design "derive-first"):
//
//   • intel_status {state} → reveal while generating (queued|live|initializing|
//       running), hold + light the rest on `ready`, hide on ready/error/disabled.
//   • intel_token (string chunks) → the streaming heartbeat: the orb pulses
//       faster while tokens arrive.
//   • intel_complete (the snapshot) → light the constellation nodes for the
//       artifact types actually produced (summary / decisions / actions / topics).
//
// Framework-free; markup + CSS live in GenerationTheater.astro.

import { subscribe } from "./runtime-bus.js";

const GENERATING = new Set(["queued", "live", "running", "initializing", "analyzing", "processing"]);
const DONE = new Set(["ready", "error", "disabled"]);

let els = null;
let hideTimer = 0;
let streamTimer = 0;

function ensureEls() {
  if (els) return els;
  const root = document.querySelector("[data-theater]");
  if (!root) return null;
  els = {
    root,
    label: root.querySelector("[data-theater-label]"),
    nodes: root.querySelectorAll("[data-type]"),
  };
  return els;
}

function setLabel(text) {
  const e = ensureEls();
  if (e && e.label) e.label.textContent = text;
}

function reveal(label) {
  const e = ensureEls();
  if (!e) return;
  if (hideTimer) {
    window.clearTimeout(hideTimer);
    hideTimer = 0;
  }
  e.root.classList.add("is-on");
  if (label) setLabel(label);
}

function hide(delay = 0) {
  const e = ensureEls();
  if (!e) return;
  if (hideTimer) window.clearTimeout(hideTimer);
  hideTimer = window.setTimeout(() => {
    e.root.classList.remove("is-on", "is-streaming");
    for (const n of e.nodes) n.classList.remove("is-lit");
    hideTimer = 0;
  }, delay);
}

function litTypesFromSnapshot(snap) {
  const lit = new Set();
  if (!snap || typeof snap !== "object") return lit;
  if (typeof snap.summary === "string" && snap.summary.trim()) lit.add("summary");
  if (Array.isArray(snap.action_items) && snap.action_items.length) lit.add("actions");
  if (Array.isArray(snap.topics) && snap.topics.length) lit.add("topics");
  if (Array.isArray(snap.decisions) && snap.decisions.length) lit.add("decisions");
  return lit;
}

function lightNodes(types) {
  const e = ensureEls();
  if (!e) return;
  let i = 0;
  for (const n of e.nodes) {
    if (types.has(n.dataset.type)) {
      // stagger the constellation lighting for a "settling" cascade
      window.setTimeout(() => n.classList.add("is-lit"), 90 * i++);
    }
  }
}

function onStatus(data) {
  const state = String((data && data.state) || "").toLowerCase();
  if (GENERATING.has(state)) {
    reveal("Generating intelligence…");
  } else if (DONE.has(state)) {
    if (state === "ready") {
      setLabel("Intelligence ready");
      hide(1600);
    } else {
      hide(400);
    }
  }
}

function onToken() {
  const e = ensureEls();
  if (!e) return;
  reveal();
  e.root.classList.add("is-streaming");
  setLabel("Thinking…");
  // tokens are a heartbeat; if they stop flowing, drop the fast pulse.
  if (streamTimer) window.clearTimeout(streamTimer);
  streamTimer = window.setTimeout(() => {
    e.root.classList.remove("is-streaming");
  }, 1200);
}

function onComplete(data) {
  const e = ensureEls();
  if (!e) return;
  e.root.classList.remove("is-streaming");
  lightNodes(litTypesFromSnapshot(data));
  setLabel("Intelligence ready");
  hide(1800);
}

export function mountTheater() {
  if (!document.querySelector("[data-theater]")) return;
  subscribe("intel_status", onStatus);
  subscribe("intel_token", onToken);
  subscribe("intel_complete", onComplete);
}

// Exposed for screenshot/proof harnesses (drive without a socket).
if (typeof window !== "undefined") {
  window.__hsTheater = { onStatus, onToken, onComplete, reveal, hide };
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mountTheater);
} else {
  mountTheater();
}
