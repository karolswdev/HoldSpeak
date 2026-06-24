// HS-69-07: the shared runtime WS bus.
//
// A single subscribable connection to the runtime's `/ws` broadcast, so every
// shell-level live component (the Queue HUD here; future cockpit Qlippy) reads
// the SAME stream without each opening its own socket. This is the connective
// backbone the convergence's shell components ride (web-technical-design §2 +
// the "one shared dependency" section).
//
// ── Additive, NOT a unification ──────────────────────────────────────────
// The dashboard page (`dashboard-app.js`) opens and owns its OWN `/ws` socket
// with its full message router, ping/pong, and reconnect/backoff. That stream
// is load-bearing and works; this bus does NOT touch it. The bus runs its own
// lightweight socket ALONGSIDE it (the same additive posture `presence-app.js`
// takes on `/presence`). So on the dashboard route there are two sockets — the
// page's and the bus's — by design: fully unifying them would mean rewriting
// the dashboard's router to subscribe here, which is the risky move the brief
// said to avoid. The bus is opt-in per shell component and only connects when
// something subscribes (so idle routes with no live shell component pay
// nothing). It also re-dispatches `hs-activity` / `hs-broadcast` DOM events,
// mirroring `presence-app.js:89-94`, so a future cockpit Qlippy can ride it.
//
// Frameless / framework-free on purpose: it loads in the shell, which must work
// with or without Alpine (`AppLayout.astro:7-9`).

const subscribers = new Map(); // type -> Set<fn>
let ws = null;
let reconnectTimer = null;
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

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }
  try {
    ws = new WebSocket(wsUrl());
  } catch (_e) {
    scheduleReconnect();
    return;
  }
  ws.onmessage = (event) => {
    if (typeof event.data !== "string") return;
    let msg = null;
    try {
      msg = JSON.parse(event.data);
    } catch (_e) {
      return;
    }
    if (!msg || typeof msg.type !== "string") return;

    // Re-dispatch as DOM events too, so a future cockpit Qlippy (which listens
    // for `hs-activity` / `hs-broadcast`) can be fed from this one socket —
    // exactly as `presence-app.js` does on `/presence`.
    if (msg.type === "runtime_activity") {
      document.dispatchEvent(new CustomEvent("hs-activity", { detail: msg.data }));
    }
    document.dispatchEvent(new CustomEvent("hs-broadcast", { detail: msg }));

    dispatch(msg.type, msg);
  };
  ws.onclose = () => {
    ws = null;
    scheduleReconnect();
  };
  ws.onerror = () => {};
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    if (subscribers.size > 0) connect();
  }, 1500);
}

function ensureStarted() {
  if (started) return;
  started = true;
  connect();
}

/**
 * Subscribe to a runtime frame type (e.g. "runtime_activity", "intel_status",
 * "intel_token", "intel_complete", "intel"). Use "*" to receive every frame.
 * The first subscription opens the shared socket lazily. Returns an
 * unsubscribe function.
 *
 * @param {string} type  the WS message `type`, or "*" for all
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

/** Seed shell components from the current runtime state on load (one-shot). */
export function seedState() {
  return fetch("/api/state")
    .then((r) => r.json())
    .then((state) => {
      const activity =
        (state && state.activity) || (state && state.runtime && state.runtime.activity);
      if (activity) {
        dispatch("runtime_activity", { type: "runtime_activity", data: activity });
      }
      if (state && state.intel_status && typeof state.intel_status === "object") {
        dispatch("intel_status", { type: "intel_status", data: state.intel_status });
      }
      return state;
    })
    .catch(() => null);
}
