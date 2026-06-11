// HS-56-02: Qlippy — the presence mascot dock + the sliding card shell.
//
// Framework-free, like presence-app.js (this runs inside the native webview
// too). Gated twice: it initializes only when /api/settings reports
// presence.enabled AND presence.mascot. With the flag off, every Qlippy node
// stays hidden and no listener does anything — the page renders exactly as
// the ring-only HUD.
//
// The dock mirrors `runtime_activity` (re-dispatched by presence-app.js as a
// DOM `hs-activity` event) through the state map below. The card shell is a
// one-at-a-time FIFO presenter (`window.qlippyCard.present(...)`) the event
// stories (actuator / learning / aftercare) hook into; it is also the
// dev/mock trigger for tests and screenshots.
//
// Motion ("Signal settle"): ~420 ms slide-in on the standard ease + a
// one-time settle bob (alert cards add the accent glow), ~280 ms slide-out.
// Reduced motion: crossfade only, sprite loops paused (CSS handles both).
// Qlippy never acts on his own: every action button is a user click routed
// to an existing endpoint by the story that presented the card.

const SPRITE_BASE = "/_built/qlippy/sprites/";
const GLYPH_BASE = "/_built/qlippy/glyphs/";
const SLEEP_AFTER_MS = 5 * 60 * 1000; // idle → sleeping (a constant, not config)
const FLOURISH_MS = 2000; // the one-time `approve` flourish on complete
const DEFAULT_AUTO_DISMISS_MS = 9000; // non-sticky cards

// runtime_activity.state → dock sprite (RFC §5).
const DOCK_MAP = {
  idle: "idle",
  listening: "listening",
  recording: "listening",
  meeting_live: "listening",
  transcribing: "thinking",
  processing: "thinking",
  saving: "thinking",
  typing: "thinking",
  error: "error",
};

const wrap = document.getElementById("qlippy");
const dockSprite = document.getElementById("qlippy-dock-sprite");
const cardEl = document.getElementById("qlippy-card");
const cardSprite = document.getElementById("qlippy-card-sprite");
const cardGlyph = document.getElementById("qlippy-card-glyph");
const headlineEl = document.getElementById("qlippy-headline");
const detailEl = document.getElementById("qlippy-detail");
const previewEl = document.getElementById("qlippy-preview");
const privacyEl = document.getElementById("qlippy-privacy");
const actionsEl = document.getElementById("qlippy-actions");
const queueHintEl = document.getElementById("qlippy-queue-hint");
const dismissBtn = document.getElementById("qlippy-dismiss");
const announcer = document.getElementById("qlippy-announcer");

let mascotOn = false;
let sleepTimer = null;
let flourishTimer = null;
let currentDockState = "idle";

function setSprite(el, state) {
  if (!el) return;
  el.style.backgroundImage = `url("${SPRITE_BASE}${state}.png")`;
  el.dataset.state = state;
}

function setDock(state) {
  if (currentDockState === state) return;
  currentDockState = state;
  setSprite(dockSprite, state);
}

function scheduleSleep() {
  clearTimeout(sleepTimer);
  sleepTimer = window.setTimeout(() => {
    if (currentDockState === "idle") setDock("sleeping");
  }, SLEEP_AFTER_MS);
}

function onActivity(activity) {
  if (!mascotOn || !activity) return;
  const state = String(activity.state || "idle").trim().toLowerCase();
  clearTimeout(flourishTimer);
  if (state === "complete") {
    // One brief `approve` flourish, then back to idle (no card — RFC §5).
    setDock("approve");
    flourishTimer = window.setTimeout(() => {
      setDock("idle");
      scheduleSleep();
    }, FLOURISH_MS);
    return;
  }
  const mapped = DOCK_MAP[state] || "idle";
  setDock(mapped);
  clearTimeout(sleepTimer);
  if (mapped === "idle") scheduleSleep();
}

// ── The card shell: one at a time, FIFO, never a pile ────────────────
const qlippyCard = {
  queue: [],
  current: null,
  _dismissTimer: null,
  _hovered: false,

  // card: {key, sprite, glyph, headline, detail, preview, privacy,
  //        actions: [{label, kind: "primary"|"danger"|"ghost", onClick}],
  //        sticky: bool, autoDismissMs}
  present(card) {
    if (!mascotOn || !card) return;
    if (this.current) {
      this.queue.push(card);
      this._updateQueueHint();
      return;
    }
    this._show(card);
  },

  _show(card) {
    this.current = card;
    setSprite(cardSprite, card.sprite || "alert");
    if (card.glyph) {
      cardGlyph.style.backgroundImage = `url("${GLYPH_BASE}${card.glyph}.png")`;
      cardGlyph.hidden = false;
    } else {
      cardGlyph.hidden = true;
    }
    headlineEl.textContent = card.headline || "";
    detailEl.textContent = card.detail || "";
    previewEl.textContent = card.preview || "";
    previewEl.hidden = !card.preview;
    privacyEl.textContent = card.privacy || "";
    privacyEl.hidden = !card.privacy;
    actionsEl.textContent = "";
    for (const action of card.actions || []) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `q-btn q-btn-${action.kind || "ghost"}`;
      btn.textContent = action.label;
      btn.addEventListener("click", () => {
        try {
          if (typeof action.onClick === "function") action.onClick(this);
        } finally {
          if (action.resolves !== false) this.resolve();
        }
      });
      actionsEl.appendChild(btn);
    }
    this._updateQueueHint();
    cardEl.hidden = false;
    cardEl.classList.remove("is-out");
    cardEl.classList.toggle("is-alert", (card.sprite || "alert") === "alert");
    // Next frame so the transition runs from the off-edge position.
    requestAnimationFrame(() => requestAnimationFrame(() => cardEl.classList.add("is-in")));
    if (announcer) {
      announcer.textContent = `${card.headline || ""}. ${card.detail || ""}`.trim();
    }
    if (!card.sticky) {
      this._armDismiss(card.autoDismissMs || DEFAULT_AUTO_DISMISS_MS);
    }
  },

  _armDismiss(ms) {
    clearTimeout(this._dismissTimer);
    this._dismissTimer = window.setTimeout(() => {
      if (!this._hovered) this.dismiss();
      else this._armDismiss(1500); // re-check after the hover ends
    }, ms);
  },

  _updateQueueHint() {
    if (!queueHintEl) return;
    queueHintEl.hidden = this.queue.length === 0;
    queueHintEl.textContent = this.queue.length ? `+${this.queue.length}` : "";
  },

  // A user action completed — slide out and present the next.
  resolve() {
    this._close();
  },

  dismiss() {
    this._close();
  },

  _close() {
    clearTimeout(this._dismissTimer);
    if (!this.current) return;
    this.current = null;
    cardEl.classList.remove("is-in");
    cardEl.classList.add("is-out");
    window.setTimeout(() => {
      cardEl.hidden = true;
      cardEl.classList.remove("is-out", "is-alert");
      const next = this.queue.shift();
      this._updateQueueHint();
      if (next) this._show(next);
    }, 300);
  },
};

cardEl?.addEventListener("mouseenter", () => {
  qlippyCard._hovered = true;
});
cardEl?.addEventListener("mouseleave", () => {
  qlippyCard._hovered = false;
});
dismissBtn?.addEventListener("click", () => qlippyCard.dismiss());

// The later stories (and tests) reach the shell here.
window.qlippyCard = qlippyCard;

// ── Boot: gated twice (presence.enabled AND presence.mascot) ─────────
fetch("/api/settings")
  .then((r) => r.json())
  .then((settings) => {
    const presence = (settings && settings.presence) || {};
    if (!presence.enabled || !presence.mascot) return;
    mascotOn = true;
    if (wrap) wrap.hidden = false;
    setSprite(dockSprite, "idle");
    scheduleSleep();
    document.addEventListener("hs-activity", (event) => onActivity(event.detail));
  })
  .catch(() => {});
