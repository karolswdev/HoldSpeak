# Phase 56 — Qlippy, the Presence Enhancer

**Status:** in-progress (5/7). Opened 2026-06-11 on user direction ("lettuce go
with qlippy"), the third step of the agreed sequence **54 → I → J → K**, right after
Phase 55 closed + merged (PR #42). From the [project backlog](../BACKLOG.md):
candidate **J**, **absorbing candidate G** (privacy visible at decision
points). Design RFC: [`../proposals/qlippy-presence-enhancer.md`](../proposals/qlippy-presence-enhancer.md).

**Last updated:** 2026-06-11 (**HS-56-05 done: the native HUD frame —
proven live on real Linux metal.** One pure policy
(`presence_panel_frame`: passive IS the exact Phase-41 click-through
geometry, locked by test; a card is 408×460 + pointer events, never focus)
drives both native renderers, which learn about cards from the page itself
(`#qlippy-card.is-in` probe — mascot-off can never grow the frame). Real
metal (the `.43` Xorg box, on user direction) found **two real Phase-41
production bugs**: the unpinned `Gdk` import (grabs 4.0 on GTK4-shipping
boxes and explodes) and fork-from-threads deadlocking the overlay child
under a running server (→ `forkserver`). Live proof with no mocks: the
production wiring's real overlay grew for a real proposal's card
(xwininfo: 408x132 → 408x460 → 408x132, same origin), a REAL xdotool click
on Approve recorded the audited decision (approved, by web-user, no side
effect), and the X11 active window never changed. The macOS live click was
**waived by the user** (screen locked; "call the phase good") — the panel
boots+shows on this Mac, the macOS glue is unit-tested, and the ready
proof script ships. 11 tests; full suite **2601 passed, 17 skipped** (+11).
**HS-56-04 (prior): learning + aftercare cards.**
Three observational backend seams: the journal correct route broadcasts
`learning_event` only under the honest-reach rule (`taught && similar > 0` —
the wire's reach is asserted equal to the route's; one matcher, one number);
`MeetingSession.save()` broadcasts `aftercare_ready` only for a finished,
DB-saved meeting whose digest is non-empty (the new
`build_aftercare_ready_event` reads the same digest /history uses; an
autosave mid-meeting stays quiet); and the deferred intel queue gains a
purely-observational `on_meeting_ready` hook (exploding-observer-safe,
tested) the web drain route wires to the same broadcast. `qlippy-events.js`
presents the `learned` 💡 card ("matches N past dictations", with the
corrections-off honesty suffix, View digest) and the `present-note`
aftercare card (open count + top items, Open aftercare, 14-s auto-dismiss).
Live dogfood 4/4 with zero page errors — a real correction and a real
meeting wrap drove both cards; a refused teach stayed silent; two reviewed
screenshots. 8 tests; full suite **2590 passed, 17 skipped** (+8).
**HS-56-03 (prior): the actuator card (the marquee; G absorbed).** Three small backend seams: the aftercare route now
broadcasts `actuator_proposed` (wire-safe — the machine payload never rides a
broadcast, asserted), a rejection broadcasts `actuator_result`, and the
executor gains a purely-observational `on_result` hook (an exploding observer
never breaks the audited transition — tested). `qlippy-events.js` presents the
sticky alert card whose Approve/Decline send the **byte-identical request the
dashboard sends** (the investigation settled it: the dashboard's Approve is
decision-only, execution stays the guarded executor's job — so the card does
exactly that), plus the executed/failed/rejected result cards with composited
glyphs. The G privacy panel is verbatim-locked on every actionable card.
Proven live with no mocks: a real aftercare proposal's real broadcast slid the
card out, Approve recorded the audited decision (status=approved,
decided_by=web-user, no side effect), Decline's real result broadcast
presented the Declined card — 4/4, zero page errors, screenshots reviewed.
4 tests; full suite **2582 passed, 17 skipped** (+4).
**HS-56-02 (prior): the dock + the card shell.**
`qlippy.js` (framework-free, gated twice at boot, no POST in the shell — the
one fetch is the gate, locked by test) drives the dock through the RFC state
map (with the 5-min sleep + the complete flourish) and exposes
`window.qlippyCard.present(...)`: one-at-a-time FIFO with a "+N" hint,
pause-on-hover, slide-out on resolve/dismiss, an aria-live announcer. The page
carries a static hidden skeleton (scoped CSS survives; only the JS-created
action buttons are `is:global` per the Phase-54 rule) with the full motion
spec (420 ms in / 280 ms out on the Signal curve, the settle bob + accent
glow on alert, reduced-motion pauses + fade). `presence-app.js` re-dispatches
the socket as `hs-activity`/`hs-broadcast` DOM events (+4 lines, no second
WebSocket). A real CSS bug caught in-flight: scaling the dock by size desynced
the 9-frame keyframe math — fixed with `transform: scale`. Live dogfood 6/6
with zero page errors; 4 reviewed screenshots; 5 page locks; full suite
**2578 passed, 17 skipped** (+5). **HS-56-01 (prior): assets + the gate.** The
PixelLab pack vendored to `web/public/qlippy/` (14 strips + 4 glyphs + avatar +
provenance README; 136 KiB; 14 sprites verified in the built bundle);
`PresenceConfig.mascot: bool = False` round-tripping `/api/settings` with zero
route changes (the `PresenceConfig(**data)` construction carries it) and
coercing older config shapes forward; the `/settings` presence section gains
the indented, inert-when-presence-off "Qlippy, the mascot" sub-toggle with
honest copy. 5 tests; two reviewed screenshots; full suite **2573 passed, 17
skipped** (+5). Earlier: scaffolded — seams verified, incl. the find that
`actuator_proposed` is already broadcast (Phase 38).)

## The thesis — why this phase

The two most consequential, least-visible moments in HoldSpeak are an actuator
awaiting approval and the learning loop doing its job. The presence layer
already has the plumbing to surface them ambiently (one `/ws` stream, a
focus-safe HUD, a config-backed toggle); what it lacks is a face, a card, and
the per-decision privacy answers. Grounded in the live tree:

- **The event transport exists**: `MeetingWebServer.broadcast` is thread-safe;
  `runtime_activity` already drives the presence page; Phase 38 already
  broadcasts `actuator_proposed` live in-meeting.
- **The decisions exist**: the card's Approve/Decline POST to the existing
  proposal-decision route — a faster front door to the same audited flow.
- **The character exists**: the PixelLab pack (14 sprite strips + composited
  glyphs) is built, with the body-emotes/glyph-composited design rule
  documented.
- **G belongs here**: an actionable card is exactly the decision point where
  "what data / does anything leave / what control" must be answered.

## Goal

An opt-in (presence.enabled AND presence.mascot, both off by default) mascot
layer on the presence surface: an ambient dock that reflects runtime states,
and a sliding, focus-safe, one-at-a-time card for the moments that need the
user (actuator approval — the marquee; learning; aftercare), with the
three plain-language privacy answers on every actionable card. Qlippy never
acts on his own; flag-unset is byte-identical.

## Scope

- **In:** assets + the mascot gate (HS-56-01); the dock + card shell with the
  full motion spec (HS-56-02); the actuator card + `actuator_result` +
  the aftercare-route `actuator_proposed` broadcast + the G privacy panel
  (HS-56-03); learning + aftercare cards + their broadcasts (HS-56-04); the
  native HUD frame sized for the card with clickable, non-activating buttons
  (HS-56-05); docs (HS-56-06); closeout (HS-56-07).
- **Out:** the Wisp sidekick; the `wave-hello` first-run onboarding card and
  milestone/celebrate cards (post-phase polish); sound (silent always); the
  `questioning` low-confidence state (needs a DIR confidence signal that
  doesn't exist); any new write primitive or change to the actuator
  executor's invariants; per-surface mascot toggles (one global flag).

## Exit criteria (evidence required)

- Sprites/glyphs vendored with provenance; `presence.mascot` (default off)
  round-trips `/api/settings`; the settings sub-toggle ships; flag-unset
  byte-identical. (HS-56-01)
- The dock animates the RFC state map (incl. sleeping + the complete
  flourish) and the card shell implements the full anatomy + motion spec
  (FIFO, pause-on-hover, reduced-motion) behind the flag; tests +
  screenshots. (HS-56-02)
- `actuator_proposed` (aftercare route) + `actuator_result` broadcasts; the
  alert card's Approve/Decline equals the dashboard flow exactly; result
  cards with composited glyphs; the three privacy answers on every
  actionable card; tests + live proof. (HS-56-03)
- `learning_event` (only when taught && reach > 0) + `aftercare_ready` (fired
  on meeting wrap, only when non-empty) + their cards; tests. (HS-56-04)
- The macOS panel hosts the interactive card without stealing focus (proven
  live on this machine); Linux best-effort documented; ring-only behavior
  unchanged. (HS-56-05)
- Product-tense docs passing the guards; humanizer run. (HS-56-06)
- Live dogfood (dock ← real dictation; card ← real proposal; Approve ≡
  dashboard with the audit trail; learned ← real correction; flag-off
  byte-identical); full suite green; `final-summary.md`; BACKLOG J + G
  flipped; PR merged on green. (HS-56-07)

## Invariants

- **Never auto-acts; executed == previewed** (the Phase-37 invariant
  untouched).
- **Opt-in twice** (presence.enabled AND presence.mascot); flag-unset
  byte-identical.
- **Focus-safe; quiet when nothing matters; one card at a time; every card
  dismissible; ignoring is always safe.**
- **Honest:** learned only with real reach; error only on real failure.
- **Local-first:** assets in-bundle, no egress, no telemetry.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-56-01 | Assets + the mascot gate | done | none |
| HS-56-02 | The dock + the card shell | done | HS-56-01 |
| HS-56-03 | The actuator card (marquee; absorbs G) | done | HS-56-02 |
| HS-56-04 | Learning + aftercare cards | done | HS-56-02 |
| HS-56-05 | The native HUD frame | done | HS-56-02 |
| HS-56-06 | Docs: Qlippy | backlog | HS-56-03, HS-56-04 |
| HS-56-07 | Closeout: live dogfood + final-summary + PR | backlog | HS-56-01..06 |

## Where we are

**HS-56-01 → HS-56-05 shipped 2026-06-11.** Every card the phase promised is
live — and the native HUD now hosts them: a real X11 click on the real
overlay's Approve recorded a real audited decision without moving focus.

Next is **HS-56-06 — docs** (the presence guide learns about Qlippy:
product-tense, the never-acts guarantee + the three privacy answers
verbatim, humanizer pass), then **HS-56-07 — closeout** (full live dogfood,
final-summary, BACKLOG J shipped + G absorbed, PR merged on green).

## Open decisions (defaults chosen per the RFC's open questions; flag to change)

- **Anchor:** bottom-right (web); the native HUD stays top-right where the
  ring lives today (HS-56-05 resolved it: the panel grows DOWNWARD from the
  anchored top-right corner — no anchor move needed; documented in
  evidence).
- **One global `presence.mascot` toggle**, default off (existing presence
  users keep the minimal ring).
- **`actuator_proposed` cards never auto-expire**; non-actionable cards
  auto-dismiss (timings per the RFC, tuned in HS-56-02).
- **`questioning` stays unused** this phase; idle → sleeping at **5 minutes**
  (a constant, not config).
- **Silent always** (no chime).
