# Phase 56 — Agent Brief (read this first)

You are picking up **Phase 56 — Qlippy, the Presence Enhancer** for HoldSpeak.
This brief is self-contained: the mission, the exact code seams (mapped against
the live tree at scaffold time), the rules of the road, and a per-story
definition of success. The full design RFC is
[`../proposals/qlippy-presence-enhancer.md`](../proposals/qlippy-presence-enhancer.md)
— read it; this brief grounds it against the live tree and turns it into
stories. If anything here disagrees with the live status docs or the codebase,
the **codebase wins** — re-verify before trusting any line or number below.

---

## 0. Mission

The presence layer (Phases 41/43) shows a status ring + label. This phase gives
it a **face and a voice**: Qlippy, the warm-orange bent-paperclip mascot
(PixelLab pack already built), at two levels:

1. **Ambient dock** — small, quiet, reflects what HoldSpeak is doing (leaning
   in to listen, pondering, dozing). No text, no buttons, never in the way.
2. **The Qlippy card** — when a moment actually needs you (an actuator
   awaiting approval, something learned, a meeting's aftercare ready), a panel
   slides out smoothly with Qlippy animating, a contextual headline + detail,
   and action buttons that are a *faster path to the same decision* the
   dashboard offers. Act or dismiss, it slides away.

This makes the two most important, least-visible moments — **actuator
approval** and **the learning loop** — actionable in the moment, without
stealing focus. **This phase absorbs backlog candidate G** (privacy visible at
decision points): every actionable card answers, in plain language, *what data
is used, does anything leave this machine, what control do I have right now*.

From [backlog](../BACKLOG.md) candidate **J**, the third step of the agreed
sequence **54 → I → J → K**.

---

## 1. The one thing you must not get wrong

**Qlippy reflects and offers; he never acts, never steals focus, and never
inflates.**

- **Never auto-acts.** Approve/Decline on the card POST to the *existing*
  decision route — identical to deciding in the dashboard. Nothing runs
  without that click; the Phase-37 invariant (no side effect without explicit,
  audited, per-action human approval; executed == previewed) is untouched.
- **Opt-in, twice over.** Rides `presence.enabled` AND a new
  `presence.mascot` toggle (default **off** — existing presence users keep
  their minimal ring). Flag-unset is byte-identical.
- **Focus-safe.** The card may receive pointer events on its buttons but
  never keyboard focus, never raises above the user's work unexpectedly.
- **Quiet when nothing matters.** Passive states never open a card; one card
  at a time (FIFO queue, never a notification pile); every card dismissible;
  ignoring a card is always safe (the proposal still lives in the dashboard).
- **Honest.** `learned` only on a real correction with real Jaccard reach
  (quiet at N=0); `error` only when a stage actually failed. No invented
  moments.
- **Local-first.** Assets ship in the bundle; no network, no telemetry.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Fresh `.tmp/CONTRACT.md` per commit (7 checkboxes); a
  done-flip ships its `evidence-story-{n}.md` in the same commit; one
  done-flip per commit; the phase-exit story ships evidence **and**
  `final-summary.md` together.
- **No `Co-Authored-By`. No `--no-verify`.**
- **Operating cadence.** Story header + this phase's `current-phase-status.md`
  + project README + touched canon docs, same commit.
- **One PR per phase, merged on green CI.** Branch `phase-56-qlippy`.
- **Tests:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **Web bundle hygiene** + the Phase-54 frontend doc
  (`docs/internal/ARCHITECTURE_WEB_FRONTEND.md`): styles for JS-rendered DOM
  are `is:global`; screenshot-verify (a class in the bundle ≠ it applies).
- **High UI/UX bar** (`ui-ux-pro-max`): the card's motion spec (RFC §3 —
  "Signal settle", 360–460 ms in on `--ease-standard`, 260–320 ms out,
  one-time settle bob, pause-on-hover, reduced-motion crossfade) is the
  product. Screenshot evidence committed.
- **User-facing docs** pass the roadmap-vocab guard, no em/en dashes,
  `humanizer` run.
- **Dogfood on the live runtime** at closeout; flag-off byte-identical
  proven.

---

## 3. The ground truth (code seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift.

**Assets (built, on disk):** `~/Desktop/qlippy-concepts/final/` — 14
**80×80, 9-frame horizontal sprite strips** in `sprites/<state>.png`
(idle, listening, thinking, questioning, alert, approve, decline, learned,
present-note, celebrate, error, surprised, wave-hello, sleeping), crisp
status glyphs in `glyphs/` (`check` #34D399, `x` #F87171, `lightbulb`/`bang`
#FBBF24), canonical avatar `qlippy.png`(@4x), and a README with the
state→moment mapping. Animate strips with CSS `steps(9)`. Vendor into
**`web/public/qlippy/`** (no `web/src/assets/` exists; public assets serve
under the `/_built` base). The design rule: **body emotes, the UI composites
the glyph** above his head at runtime.

**The presence surface:**
- `web/src/pages/presence.astro` — a single `.presence-card` (ring + label +
  detail), scoped styles, loaded by the native HUD's WKWebView too.
- `web/src/scripts/presence-app.js` — connects `/ws`, seeds from
  `GET /api/state` (`state.activity` / `state.runtime.activity`), applies
  `{type: "runtime_activity", data}` where data =
  `{state, label, detail, last_error, last_event, source, window:{visible,
  mode, linger_ms}}`. States: idle, listening, recording, transcribing,
  processing, typing, complete, meeting_live, saving, error
  (`holdspeak/runtime_activity.py:12`).
- **Dock state map (RFC §5):** listening/recording/meeting_live → `listening`;
  transcribing/processing/saving/typing → `thinking`; complete → brief
  `approve` flourish → idle; error → `error`; idle → `idle` (→ `sleeping`
  after 5 min). Passive states never open a card.

**Broadcast:** `MeetingWebServer.broadcast(type, data)`
(`web_server.py:356`) is thread-safe (`run_coroutine_threadsafe`). Events
land on the same `/ws` all pages share.

**The actuator seam (M2):**
- **`actuator_proposed` is ALREADY broadcast** for live in-meeting proposals
  (`meeting_session.py:~476`, Phase 38) with `{id, target, action, preview,
  payload, created_at}`. The aftercare file-issue route
  (`web/routes/meetings.py:~907`) creates proposals **without** broadcasting —
  add the same broadcast there.
- Decision: `POST /api/meetings/{meeting_id}/proposals/{proposal_id}/decision`
  (`meetings.py:809`), payload `{decision: "approved"|"rejected",
  decided_by?}` — transitions state only, **no side effect** (HS-37-04);
  execution is a separate guarded step (`plugins/actuator_executor.py:85`,
  payload-hash parity, allow-list, audit). **The card mirrors exactly what
  the dashboard does — investigate how the dashboard triggers execution after
  approval and do the identical thing, nothing more.**
- **`actuator_result` does not exist** — add it where the executor records
  executed/failed and where a rejection is decided.
- Proposal record fields: id, meeting_id, status, target, action, preview,
  payload, reversible, required_capabilities, result, error
  (`_proposal_to_dict`, `meetings.py:~760`).

**The learning seam (M3):** the journal correct route
(`web/routes/dictation/pipeline.py:~477`) computes
`{taught, similar, enabled}` via `reach_for_gist` — broadcast
`learning_event` there **only when `taught and similar > 0`** (honest reach).

**The aftercare seam (M3):** `compute_meeting_aftercare(db, meeting_id)`
(`meeting_aftercare.py:~238`) is a pure read behind a GET. Broadcasting from
a GET is wrong; fire `aftercare_ready` where a meeting wraps (the save/stop
flow), computing the digest once and broadcasting only when `not is_empty`.

**Config:** `PresenceConfig` (`config.py:521`) has only `enabled: bool =
False`. Add `mascot: bool = False`; round-trips via `/api/settings`; the
presence toggle UI lives in `/settings` (Phase 43) — add the sub-toggle
beside it. The presence page needs the flag client-side: check what
`GET /api/state` exposes and extend minimally if needed.

**The native HUD (M4):** macOS `desktop_presence_cocoa.py` — NSPanel
**408×132**, borderless + non-activating, `ignoresMouseEvents=True`
(click-through!), top-right anchored, WKWebView loading `{url}/presence`.
For the card: a larger frame and **pointer events enabled on buttons while
staying non-activating** (`ignoresMouseEvents=False` + non-activating panel
style keeps focus safety; verify on this machine — it is a Mac).
`build_presence_window_view` / `desktop_window_policy`
(`desktop_presence.py`) project sizing/visibility; extend for a card-capable
frame. Linux (`_freedesktop`/GTK): best-effort sizing, code-reviewed not
hardware-proven (the standing posture).

---

## 4. Per-story definition of success

- **HS-56-01 — Assets + the mascot gate.** Sprites/glyphs/avatar vendored to
  `web/public/qlippy/` (committed; document provenance per the PixelLab
  memory pattern); `presence.mascot: bool = False` in config, round-tripping
  config-version-safe through `/api/settings`; the `/settings` presence
  section gains the sub-toggle (disabled/dimmed when presence itself is
  off); the flag reaches the presence page (via `/api/state` or equivalent).
  Flag-unset byte-identical (tests).
- **HS-56-02 — The dock + the card shell.** On `/presence`, behind the
  flag: the Qlippy dock (sprite-strip animation via `steps(9)`, the RFC
  dock-state map, idle → `sleeping` after 5 min, `complete` → one `approve`
  flourish) and the **card shell** with the full RFC anatomy (Qlippy bay,
  headline/detail, optional mono preview, action row, dismiss ✕) and motion
  spec (slide-in/settle/slide-out timings, FIFO queue + "+N" hint,
  pause-on-hover, reduced-motion crossfade), driven by a small internal
  event API (`qlippyCard.present(...)`) with a dev/mock path for tests and
  screenshots. ARIA live-region announce. Page-content + behavior tests;
  screenshots of dock states + an open card.
- **HS-56-03 — The actuator card (the marquee; absorbs G).** Backend: add
  the missing `actuator_proposed` broadcast on the aftercare file-issue
  route; add `actuator_result` broadcasts at the executor's
  executed/failed transitions and at a rejected decision. Frontend: the
  `alert` card on `actuator_proposed` (headline "A decision needs you",
  target · action · reversible, mono payload preview, **Approve / Decline**
  → the existing decision route, mirroring the dashboard's exact
  post-approval behavior), `approve`/`decline`/`error` result cards with
  the composited glyphs. **The G panel:** every actionable card carries the
  three plain-language privacy answers (what data — the preview/payload;
  does anything leave — the target, or "nothing leaves this machine" for
  local-only moments; what control — the buttons themselves + dismiss).
  Actionable cards linger until resolved or dismissed, never auto-deciding.
  Integration tests (broadcasts fire; the card's decision POST equals the
  dashboard's) + a live proof.
- **HS-56-04 — Learning + aftercare cards.** `learning_event` broadcast at
  the journal correct route only when `taught && similar > 0`
  ("Learned from you — applied *gist* — matches N past dictations", View
  digest action); `aftercare_ready` fired from the meeting wrap flow when
  the digest is non-empty ("Your meeting left N open items", top 1–2 items,
  Open aftercare action). `learned` 💡 and `present-note` cards. Honest at
  N=0 (no event). Tests on both seams + cards.
- **HS-56-05 — The native HUD frame.** The macOS NSPanel grows to host the
  card (edge-anchored, sized for the card frame), **buttons clickable**
  (`ignoresMouseEvents` flipped appropriately) while the panel stays
  non-activating (keyboard focus never leaves the user's app — verify live
  on this machine, it is a Mac); the window policy/view projection extended
  so card-bearing states size up and passive states stay small. Linux
  renderer updated best-effort (code + tests, hardware posture documented).
  Off-flag and ring-only (mascot off) behavior unchanged.
- **HS-56-06 — Docs.** The mascot documented product-tense in the presence
  guide section (what Qlippy is, when cards appear, the never-acts
  guarantee, the three privacy answers, both toggles, how to turn him off);
  guards + humanizer.
- **HS-56-07 — Closeout.** Live dogfood: dock follows real dictation states;
  a real proposal slides the card out and **Approve executes identically to
  the dashboard** (audit trail shown); a real correction with reach fires
  the learned card; flag-off byte-identical proven; screenshots; full suite;
  `final-summary.md`; BACKLOG **J** (and **G**, absorbed) flipped; PR
  merged on green.

---

## 5. Gotchas that will bite you

- **The page runs inside the native HUD too.** Until HS-56-05 lands, the
  NSPanel is 408×132 and click-through — the web card must not assume it is
  interactive in the HUD context (it IS interactive on `/presence` in a
  browser). Design the card to degrade: in a non-interactive host it still
  informs; the dashboard remains the decision surface. HS-56-05 closes the
  gap.
- **`prefers-reduced-motion`** is a hard requirement on every animation
  (sprite loops included — pause to the first frame or slow them).
- **Sprite strips are 9-frame, 80×80** — `background-size: 720px 80px` +
  `steps(9)`; pixelated rendering (`image-rendering: pixelated`) or they
  blur.
- **One card at a time.** The FIFO queue is behavior, not polish: concurrent
  events queue, never stack; `actuator_proposed` cards never auto-expire.
- **Broadcasts come from worker threads** — always go through
  `MeetingWebServer.broadcast` (thread-safe), never the ws manager directly.
- **Do not broadcast from GET routes** (aftercare). Fire events where state
  changes.
- **The executor's invariants are sacred:** the card never calls the
  executor with different inputs than the dashboard path; payload-hash
  parity and the allow-list stay exactly as they are.
- **`/api/state` shape:** the presence page seeds from it; extending it must
  not break the existing consumers (presence-app, dashboards).
- **Glyphs are composited, not baked** — the check/x/lightbulb overlays are
  the UI's job (absolute-positioned above the sprite), per the asset README.
- **Linux renderer:** code-reviewed best-effort only (no hardware here);
  say so in evidence, don't fake a proof.

---

## 6. Where to start

`HS-56-01` (assets + gate) is first and small: vendored sprites + the config
flag + the settings sub-toggle give every later story its foundation and its
off-switch. Then 02 (the dock + card shell, where the motion spec and the
mock path make everything after it demonstrable), 03 (the marquee actuator
card + G), 04 (learning/aftercare), 05 (the native frame), 06 (docs), 07
(closeout). Keep him quiet, honest, and never acting on his own — Qlippy is
the brand made visible, not a new permission system.
