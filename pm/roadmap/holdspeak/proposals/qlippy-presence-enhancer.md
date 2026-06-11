# Proposal — Qlippy, the Presence Enhancer

> Status: **draft proposal** (candidate phase). Author-facing RFC, not yet a
> roadmap phase. Grounds in the existing presence layer (Phase 41/43), the
> actuator system (Phase 37/38), the dictation pipeline (DIR), and the visible
> learning loop (Phase 48).

## 1. The pitch

HoldSpeak already has a **runtime presence** layer — a small, focus-safe HUD
that shows what the app is doing (listening, transcribing, typing…). Today it
renders as a status ring + label. This proposal gives that layer a **face and a
voice**: **Qlippy**, a warm-orange bent-paperclip mascot (a Clippy homage).

Qlippy works at two levels:

1. **Ambient dock** — a small, quiet Qlippy parked at a screen edge who simply
   *reflects* what HoldSpeak is doing (leaning in to listen, pondering while it
   transcribes, dozing when idle). No text, no buttons, never in the way.
2. **The Qlippy card** — when a moment actually needs you (an actuator awaiting
   approval, something learned, a meeting wrapped, an error), a panel **slides
   out smoothly and slowly** from the edge with Qlippy animating inside it, a
   short **contextual headline + detail**, and **action buttons that change with
   the context** (Approve / Decline, View digest, Open aftercare, Retry…). When
   you act or dismiss, it **slides back out of view**.

This makes the two most important, least-visible moments in HoldSpeak — **an
actuator awaiting approval** and **the learning loop** — not just legible but
*actionable in the moment*, without stealing focus. The card is a faster path to
the **same** approval you'd make in the dashboard; Qlippy never acts on his own.

Brand fit: he embodies the HoldSpeak voice — *competent, honest, encouraging,
quiet when nothing matters, a gatekeeper around side effects*. Opt-in, off by
default, exactly like the presence layer he extends.

## 2. The character (already built)

A complete asset pack exists at `~/Desktop/qlippy-concepts/final/` (see its
`README.md`). Hero: PixelLab object `44c0b009-…`, 80×80 native, 9-frame v3
animations. Sidekick (the flame **Wisp**) exists but is out of scope here.

**Design rule:** a paperclip has no hands, and at 80×80 the generator can't
render tiny symbols. So **Qlippy emotes with body + eyebrows**, and the UI
**composites crisp status glyphs** (✓ `#34D399`, ✗ `#F87171`, ! / 💡 `#FBBF24`)
above his head at runtime. Large props that render cleanly (the note, the Zzz)
are baked into the sprite. Glyph PNGs ship in `final/glyphs/`.

States in the pack: `idle`, `listening`, `thinking`, `questioning`, `alert`,
`approve`, `decline`, `learned`, `present-note`, `celebrate`, `error`,
`surprised`, `wave-hello`, `sleeping`.

## 3. The Qlippy card — anatomy & motion

This is the heart of what's new. The card is a single, focus-safe panel anchored
to a screen edge (default **bottom-right**, configurable).

### Anatomy

```
┌───────────────────────────────────────────┐
│ ●                                       ✕  │   ← dismiss
│  ┌──────┐   A DECISION NEEDS YOU            │   ← headline (Space Grotesk)
│  │      │   File a GitHub issue in          │   ← detail   (Inter, muted)
│  │ Qlip │   acme/widgets · reversible       │
│  │ -py  │   ┌─────────────────────────────┐ │
│  │ anim │   │ title: "Fix flaky test…"    │ │   ← optional preview
│  └──────┘   │ labels: bug, ci             │ │     (JetBrains Mono, payload)
│             └─────────────────────────────┘ │
│             [ Approve ]  [ Decline ]  View   │   ← contextual actions
└───────────────────────────────────────────┘
```

- **Qlippy bay** (left, ~72–88px): the looping sprite for the current context
  (`alert`, `learned`, `approve`…), with the composited glyph when relevant.
- **Content column:** headline (display face), detail line (muted UI face), an
  optional **preview block** (monospace — the actuator payload, the correction,
  the meeting items), then an **action row**.
- **Action row:** 0–3 buttons whose labels/handlers depend on the event (see
  §5). Primary action uses the Signal accent; destructive/decline is bordered.
- **Dismiss ✕** and the whole card are click-targets; the rest is inert.

### Motion ("Signal settle", slow + smooth)

- **Slide-in:** translate from off-edge to rest (e.g. `translateX(110%) → 0`)
  with a gentle fade, **~360–460ms** on `cubic-bezier(0.16, 1, 0.3, 1)` (the
  Signal `--ease-standard`). Deliberately slower than UI snappiness so it reads
  as "arriving," not "popping." Qlippy plays his entrance state as it lands.
- **Settle / attention:** a one-time subtle bob + the accent glow ring
  (`--accent-glow`) on `alert`; then he holds calmly. No perpetual motion.
- **Slide-out:** reverse, **~260–320ms**, on resolve or dismiss. Then Qlippy
  collapses back to the **ambient dock** (small avatar) or fully hides.
- **Pause-on-hover:** hovering the card cancels any auto-dismiss timer.
- **One at a time:** a single card; concurrent events **queue** (FIFO) rather
  than stack — Qlippy presents them one after another, so it never becomes a
  notification pile. A small "+N" affordance can hint at queued items.
- **Reduced-motion:** no slide; cross-fade the static avatar + glyph instead.

### Ambient dock vs. card

| State class | Surface | Example states |
|---|---|---|
| Passive / status | **dock only** (no card, no buttons) | `idle`, `listening`, `thinking`, `typing`, `sleeping` |
| Notable / actionable | **card slides out** | `alert`, `approve`, `decline`, `learned`, `present-note`, `error`, `wave-hello`, `celebrate` |

The dock is always-small and quiet; the card is the exception that earns the
slide. Passive states never produce a card — that's what keeps it non-annoying.

## 4. How it hooks in (reuse, don't reinvent)

The presence plumbing is already there. Qlippy is a new **renderer + card** on
the same event stream; button clicks reuse the **existing REST routes**.

- **Event transport (in):** the `/ws` websocket —
  `holdspeak/web/routes/system.py` (`@router.websocket("/ws")`), fanned out by
  `holdspeak/web_server.py::WebSocketManager.broadcast` as `{type, data}`.
- **Action transport (out):** button clicks POST to existing REST endpoints
  (e.g. proposal decision below). `/ws` stays one-way; **no new inbound channel
  needed.**
- **State source of truth:** `holdspeak/runtime_activity.py` (`RuntimeActivity`,
  `VALID_ACTIVITY_STATES`, `RuntimeActivityTracker.update`). Set centrally by
  `holdspeak/web_runtime.py::_set_runtime_activity()`, pushed via
  `_broadcast_runtime_activity()` as message type `runtime_activity`.
- **Web consumer (the model to copy):** `web/src/scripts/presence-app.js`
  connects to `/ws`, seeds from `GET /api/state`, applies `runtime_activity`.
  Qlippy is a new component in `web/src/pages/presence.astro` (+ a sibling
  `qlippy.js`) that adds the card UI on top of that subscription.
- **Desktop hosts:** `holdspeak/desktop_presence.py`
  (`build_presence_window_view`, `desktop_window_policy`) + `_cocoa` / `_freedesktop`
  / `_gtk`. The native macOS panel renders the presence page in a WKWebView, so
  the card lights up the native HUD for free — **but the host window must be
  allowed to size up to the card** (see §7 open items: the panel currently sizes
  for a small ring; the card needs a larger, edge-anchored frame and pointer
  events enabled on the buttons while staying non-activating).
- **Config gate:** `holdspeak/config.py::PresenceConfig.enabled = False`
  (default off), toggled live by `web_runtime._apply_presence_config_toggle()`,
  persisted via `PUT /api/settings`. Qlippy rides this gate; add a
  `presence.mascot` sub-toggle so users can keep the minimal ring.

## 5. Context → card content (what slides out, with which buttons)

Passive states (no card) omitted. Buttons call existing routes where they exist.

| Event (`/ws` type) | Qlippy | Headline | Detail / preview | Buttons → handler |
|---|---|---|---|---|
| `actuator_proposed` | `alert` | "A decision needs you" | target · action · `reversible`; payload preview (mono) | **Approve** / **Decline** → `POST /api/meetings/{id}/proposals/{pid}/decision`; **View** → open proposal UI |
| `actuator_result` (ok) | `approve` ✓ | "Done — {action}" | short result | **Undo** (if reversible, where supported) · Dismiss |
| `actuator_result` (no) | `decline` ✗ / `error` | "Didn't run" | failure reason | **Retry** / **Details** · Dismiss |
| `learning_event` | `learned` 💡 | "Learned from you" | "Applied *{gist}* — matches {reach} past dictations" | **View digest** → `/api/dictation/learning-digest` UI · **Undo** · Dismiss |
| `aftercare_ready` | `present-note` | "Your meeting left {n} open items" | top 1–2 items | **Open aftercare** · Dismiss |
| `first_run` (one-shot) | `wave-hello` | "Hi, I'm Qlippy" | one-line intro | **Show me around** → `/welcome` · No thanks |
| `error` (dictation stage) | `error` | "{stage} didn't finish" | "Typed what I heard." | **Details** · Dismiss |
| milestone/streak (optional) | `celebrate` | celebratory line | — | Dismiss |

### Already-emitted runtime states (dock only, zero backend work)
| `runtime_activity` state | Qlippy dock state |
|---|---|
| `idle` (short) → (long) | `idle` → `sleeping` after N min |
| `listening` / `recording` / `meeting_live` | `listening` |
| `transcribing` / `processing` / `saving` | `thinking` |
| `typing` | `thinking` (subtle) |
| `complete` | brief `approve` flourish → `idle` (no card) |
| `error` | `error` (card, per above) |

### New broadcasts to add (small; one line beside each existing transition)
- `actuator_proposed` — at `db.actuators.transition_proposal(... "proposed")` /
  routes in `web/routes/meetings.py`. Payload: proposal id, meeting id, target,
  action, preview, reversible.
- `actuator_result` — at `actuator_executor.execute()` success/failure and at
  reject in the decision route.
- `learning_event` — when `dictation_learning.best_correction_signal` yields a
  correction whose `reach` crosses the threshold.
- `aftercare_ready` — when the Phase-49 aftercare digest is computed for a
  wrapped meeting.

No new event bus: each is `self.server.broadcast(type, data)` next to logic that
already runs.

## 6. Behavior & guardrails (non-negotiable, brand-true)

- **Opt-in, off by default.** Inherits `presence.enabled`; add `presence.mascot`.
- **Focus-safe.** Non-activating window; the card may receive *pointer events on
  its buttons* but must never steal keyboard focus or raise above the user's work
  unexpectedly (extend `desktop_window_policy` for the card frame).
- **Quiet when nothing matters.** Passive states never open a card. Cards play
  once and slide away; one at a time, queued not stacked.
- **Never auto-acts.** Approve/Decline are *your* clicks routed to the existing
  decision endpoint — identical to approving in the dashboard. Nothing runs
  without that click. Qlippy reflects and offers; he never executes.
- **Honest.** `learned` only on a real correction with real Jaccard reach (no
  inflation). `error` only when a stage actually failed, paired with the existing
  typed-fallback.
- **Dismissible & non-blocking.** Every card has ✕; ignoring it is always safe
  (the underlying proposal still lives in the dashboard). Auto-dismiss for
  non-actionable cards; actionable cards (e.g. `actuator_proposed`) linger until
  resolved or dismissed, never auto-deciding.
- **Local-first.** Assets in-bundle; no network, no telemetry.
- **Accessible.** Reduced-motion fallback; every card maps to the text
  `label`/`detail` already in `RuntimeActivity`; buttons are keyboard-reachable
  when the surface is focusable; ARIA live-region announce on slide-in.

## 7. Asset pipeline

- Sprites + glyphs in source at `web/src/assets/qlippy/<state>.png` +
  `glyphs/`, driven by a new `web/src/scripts/qlippy.js` (sibling to
  `presence-app.js`) and a card component in `presence.astro`.
- `cd web && npm run build` emits into `holdspeak/static/_built/` (gitignored),
  served by the existing FastAPI StaticFiles mount. **Commit source only** — see
  the web-bundle hygiene rule.
- Native HUD picks them up automatically (renders the built presence page) —
  pending the larger card frame noted in §4.

## 8. Rollout (suggested phasing)

1. **M1 — Dock + card shell (web).** Qlippy ambient dock driven by today's
   `runtime_activity`, plus the sliding card component with mocked content and
   the full motion spec. Reduced-motion fallback. Behind `presence.mascot`. Pure
   front-end + assets.
2. **M2 — Actuator card (headline).** Add `actuator_proposed` / `actuator_result`
   broadcasts; wire the Approve/Decline card to the existing decision route. The
   marquee moment.
3. **M3 — Learning + aftercare cards.** Add `learning_event` / `aftercare_ready`;
   wire `learned` (💡) and `present-note` cards.
4. **M4 — Native frame + onboarding + polish.** Enlarge/anchor the desktop panel
   for the card with safe pointer-events, `wave-hello` first-run, `sleeping`
   idle, settings preview, the Wisp sidekick.

Each milestone is independently shippable and reversible.

## 9. Non-goals

- Not a chat assistant; no unsolicited advice, no tips you didn't trigger. Cards
  are 1:1 with real events and always dismissible.
- Does not replace existing UI (proposals, digest, aftercare keep working
  standalone); the card is a faster front door, not the only door.
- No focus-stealing, no modal blocking, never on by default.

## 10. Open questions

- Anchor edge + slide direction default (bottom-right ↗ vs. right-center)?
- Native panel: simplest path to a resizable, edge-anchored, non-activating
  window that still accepts button clicks on macOS (NSPanel) and Linux?
- Card auto-dismiss timings per type; does `actuator_proposed` ever auto-expire?
- One global mascot toggle or per-surface (desktop HUD vs. web dashboard)?
- Should `questioning` surface low-confidence transcriptions (needs a DIR
  confidence signal) or stay aftercare-only for now?
- Idle→`sleeping` threshold (5 min? configurable?).
- Sound: silent always, or optional off-by-default soft chime on `alert`?

---

*Companion asset pack:* `~/Desktop/qlippy-concepts/final/` ·
*Project memory:* `project_qlippy_mascot`.
