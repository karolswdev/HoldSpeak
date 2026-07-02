// The ONE live runtime bus (Phase 72 — was HS-69-07's additive side-channel).
//
// A single subscribable connection to the runtime's `/ws` broadcast. Every
// live consumer on the web rides THIS socket: the shell widgets (Queue HUD,
// Qlippy, waveform, generation theater, egress badge), the /live dashboard's
// message router, the /presence HUD, and the /setup + /welcome first-dictation
// listeners. The web opens exactly one `/ws` per page.
//
// History: HS-69-07 introduced this bus deliberately ALONGSIDE the dashboard's
// own socket ("additive, not a unification") to avoid rewriting the dashboard
// router mid-convergence. Phase 72 finished the unification: the dashboard,
// presence, setup and welcome apps now subscribe here and their private
// sockets are gone. The dashboard's hard-won connection robustness moved INTO
// the bus (15s keepalive ping, exponential backoff with jitter, connection
// state) so every consumer inherits it.
//
// ── The event vocabulary (one place) ─────────────────────────────────────
// Wire frames (server `/ws` broadcasts, `{type, data}`): `runtime_activity`,
// `intel_status`, `intel_token`, `intel_complete`, `intel`, `segment`,
// `duration`, `bookmark_added`, `actuator_proposed`, `actuator_result`,
// `aftercare_ready`, `learning_digest`, … — subscribe by `type`, or `"*"` for
// every frame. Synthetic bus events (never on the wire):
//   - `bus_status` — `{state: "connecting"|"connected"|"reconnecting",
//     reconnectAt}` on connection transitions (the /live connection pill).
// DOM re-dispatch (for listeners outside the module graph, e.g. qlippy.js and
// `new Function`-evaluated Alpine factories):
//   - `hs-activity`  — detail = the `runtime_activity` frame's data
//   - `hs-broadcast` — detail = every full `{type, data}` frame
// Eval'd factories can also use `window.__hsBus` (`{subscribe, seedState}`).
//
// Frameless / framework-free on purpose: it loads in the shell, which must work
// with or without Alpine (`AppLayout.astro`), and in the chromeless /presence
// webview.

const subscribers = new Map(); // type -> Set<fn>
let ws = null;
let reconnectTimer = null;
let pingTimer = null;
let reconnectAttempt = 0;
let started = false;

function wsUrl() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws`;
}

function dispatch(type, msg) {
  const fns = subscribers.get(type);
  if (fns) {
    for (const fn of fns) {
      try {
        fn(msg.data, msg);
      } catch (_e) {
        /* one bad subscriber must not poison the stream */
      }
    }
  }
  const wildcard = subscribers.get("*");
  if (wildcard) {
    for (const fn of wildcard) {
      try {
        fn(msg.data, msg);
      } catch (_e) {}
    }
  }
}

/** One delivery pipeline for wire frames AND seeded state: DOM events first
 * (qlippy + eval'd listeners), then typed subscribers. */
function deliver(msg) {
  if (!msg || typeof msg.type !== "string") return;
  if (msg.type === "runtime_activity") {
    document.dispatchEvent(new CustomEvent("hs-activity", { detail: msg.data }));
  }
  document.dispatchEvent(new CustomEvent("hs-broadcast", { detail: msg }));
  dispatch(msg.type, msg);
}

function status(state) {
  dispatch("bus_status", {
    type: "bus_status",
    data: { state, reconnectAt: state === "reconnecting" ? reconnectAtMs : null },
  });
}

let reconnectAtMs = null;

function startPing() {
  stopPing();
  pingTimer = window.setInterval(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    try {
      ws.send("ping");
    } catch (_e) {}
  }, 15000);
}

function stopPing() {
  if (pingTimer) window.clearInterval(pingTimer);
  pingTimer = null;
}

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }
  status(reconnectAttempt ? "reconnecting" : "connecting");
  try {
    ws = new WebSocket(wsUrl());
  } catch (_e) {
    scheduleReconnect();
    return;
  }
  ws.onopen = () => {
    reconnectAttempt = 0;
    reconnectAtMs = null;
    startPing();
    status("connected");
  };
  ws.onmessage = (event) => {
    if (typeof event.data !== "string") return;
    let msg = null;
    try {
      msg = JSON.parse(event.data);
    } catch (_e) {
      return;
    }
    deliver(msg);
  };
  ws.onclose = () => {
    ws = null;
    stopPing();
    scheduleReconnect();
  };
  ws.onerror = () => {};
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  // The dashboard's backoff, inherited by every consumer: 500ms * 2^n,
  // capped at 12s, with up to 400ms of jitter.
  reconnectAttempt = Math.min(reconnectAttempt + 1, 8);
  const base = 500 * Math.pow(2, reconnectAttempt - 1);
  const delay = Math.min(12000, base + Math.floor(Math.random() * 400));
  reconnectAtMs = Date.now() + delay;
  status("reconnecting");
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    if (subscribers.size > 0) connect();
  }, delay);
}

function ensureStarted() {
  if (started) return;
  started = true;
  connect();
}

/**
 * Subscribe to a runtime frame type (see the vocabulary above), `"*"` for
 * every frame, or the synthetic `"bus_status"`. The first subscription opens
 * the shared socket lazily. Returns an unsubscribe function.
 *
 * @param {string} type  the WS message `type`, "*", or "bus_status"
 * @param {(data: any, msg: any) => void} fn
 * @returns {() => void} unsubscribe
 */
export function subscribe(type, fn) {
  if (!subscribers.has(type)) subscribers.set(type, new Set());
  subscribers.get(type).add(fn);
  ensureStarted();
  return () => {
    const fns = subscribers.get(type);
    if (fns) {
      fns.delete(fn);
      if (fns.size === 0) subscribers.delete(type);
    }
  };
}

/** Seed consumers from the current runtime state on load (one-shot). Runs
 * through the SAME delivery pipeline as wire frames, so DOM listeners
 * (qlippy) and typed subscribers both see the seed. */
export function seedState() {
  return fetch("/api/state")
    .then((r) => r.json())
    .then((state) => {
      const activity =
        (state && state.activity) || (state && state.runtime && state.runtime.activity);
      if (activity) {
        deliver({ type: "runtime_activity", data: activity });
      }
      if (state && state.intel_status && typeof state.intel_status === "object") {
        deliver({ type: "intel_status", data: state.intel_status });
      }
      return state;
    })
    .catch(() => null);
}

// `new Function`-evaluated Alpine factories (live/setup/welcome) cannot use
// ES imports; they reach the same singleton here.
window.__hsBus = { subscribe, seedState };
