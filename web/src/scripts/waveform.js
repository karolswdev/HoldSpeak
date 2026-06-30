// HS-69-08: the reactive mic waveform — store + canvas render.
//
// The web port of the iPad's perceptual level meter (gamma-expanded bars, a
// scrolling history, an accent peak glow; MeetingCaptureApp.swift:3438-3466).
// Per the Phase-69 carried-in decision, the SOURCE is a small additive server
// `audio_level` WS frame — NOT a new in-browser mic surface. So this module
// subscribes to that frame on the shared runtime-bus and animates; it never
// touches getUserMedia.
//
// Frame contract: { type: "audio_level", data: { level: <float 0..1> } }.
//
// Framework-free (the shell must work with or without Alpine). The markup + CSS
// live in `Waveform.astro`; this module owns the rolling buffer + the rAF draw.

import { subscribe } from "./runtime-bus.js";

const BARS = 48; // history slots (newest on the right)
const IDLE_MS = 700; // no frame for this long → decay to rest + hide
const GAMMA = 0.6; // perceptual expansion: lifts quiet speech off the floor

const levels = new Float32Array(BARS); // smoothed bar heights 0..1
let target = 0; // newest incoming level (0..1)
let lastFrameAt = 0;
let active = false;
let raf = 0;
let els = null;

function ensureEls() {
  if (els) return els;
  const root = document.querySelector("[data-waveform]");
  if (!root) return null;
  const canvas = root.querySelector("canvas");
  els = { root, canvas, ctx: canvas ? canvas.getContext("2d") : null };
  return els;
}

function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

function resize(e) {
  const dpr = window.devicePixelRatio || 1;
  const w = e.root.clientWidth || 320;
  const h = e.root.clientHeight || 64;
  if (e.canvas.width !== Math.round(w * dpr) || e.canvas.height !== Math.round(h * dpr)) {
    e.canvas.width = Math.round(w * dpr);
    e.canvas.height = Math.round(h * dpr);
    e.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  return { w, h };
}

function draw() {
  const e = ensureEls();
  if (!e || !e.ctx) {
    raf = 0;
    return;
  }
  const { w, h } = resize(e);
  const ctx = e.ctx;
  ctx.clearRect(0, 0, w, h);

  // shift history left by one slot each frame, ease the newest toward `target`
  for (let i = 0; i < BARS - 1; i++) levels[i] = levels[i + 1];
  const decayed = target * 0.92; // slight per-frame decay so a held tone breathes
  levels[BARS - 1] += (decayed - levels[BARS - 1]) * 0.45;
  target *= 0.9; // toward rest until the next frame refreshes it

  const accent = cssVar("--accent", "#FF6B35");
  const gap = 2;
  const bw = (w - (BARS - 1) * gap) / BARS;
  const mid = h / 2;
  let peak = 0;
  let peakX = 0;

  for (let i = 0; i < BARS; i++) {
    const lvl = Math.pow(Math.min(1, Math.max(0, levels[i])), GAMMA);
    const bh = Math.max(1.5, lvl * (h - 4));
    const x = i * (bw + gap);
    const fade = 0.25 + 0.75 * (i / BARS); // older bars dimmer
    ctx.fillStyle = accent;
    ctx.globalAlpha = fade * (0.35 + 0.65 * lvl);
    // mirrored around the centre line — a symmetric meter
    ctx.fillRect(x, mid - bh / 2, bw, bh);
    if (lvl >= peak) {
      peak = lvl;
      peakX = x + bw / 2;
    }
  }
  ctx.globalAlpha = 1;

  // accent peak glow on the loudest recent bar
  if (peak > 0.08) {
    const g = ctx.createRadialGradient(peakX, mid, 0, peakX, mid, h * 0.7);
    g.addColorStop(0, accent + "66");
    g.addColorStop(1, accent + "00");
    ctx.fillStyle = g;
    ctx.fillRect(peakX - h * 0.7, 0, h * 1.4, h);
  }

  // idle → settle the bars flat, then stop + hide
  const sinceFrame = (window.performance ? performance.now() : Date.now()) - lastFrameAt;
  const restEnergy = levels.reduce((a, b) => a + b, 0);
  if (sinceFrame > IDLE_MS && restEnergy < 0.05) {
    active = false;
    e.root.classList.remove("is-active");
    raf = 0;
    return;
  }
  raf = window.requestAnimationFrame(draw);
}

function onLevel(data) {
  const lvl = Number(data && data.level);
  if (!Number.isFinite(lvl)) return;
  target = Math.min(1, Math.max(0, lvl));
  lastFrameAt = window.performance ? performance.now() : Date.now();
  const e = ensureEls();
  if (e && !active) {
    active = true;
    e.root.classList.add("is-active");
  }
  if (!raf) raf = window.requestAnimationFrame(draw);
}

export function mountWaveform() {
  if (!document.querySelector("[data-waveform]")) return;
  subscribe("audio_level", onLevel);
}

// Exposed for screenshot/proof harnesses to push a level without a socket.
if (typeof window !== "undefined") {
  window.__hsWaveformLevel = onLevel;
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mountWaveform);
} else {
  mountWaveform();
}
