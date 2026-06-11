# Phase 56 — Qlippy, the Presence Enhancer

**Status:** scaffolded. Opened 2026-06-11 on user direction ("lettuce go with
qlippy"), the third step of the agreed sequence **54 → I → J → K**, right after
Phase 55 closed + merged (PR #42). From the [project backlog](../BACKLOG.md):
candidate **J**, **absorbing candidate G** (privacy visible at decision
points). Design RFC: [`../proposals/qlippy-presence-enhancer.md`](../proposals/qlippy-presence-enhancer.md).

**Last updated:** 2026-06-11 (scaffolded: AGENT-BRIEF + seven stories; seams
verified against the live tree — including the find that `actuator_proposed`
is **already broadcast** for live in-meeting proposals, so the marquee story
needs `actuator_result` + the aftercare-route broadcast, not a new event bus).

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
| HS-56-01 | Assets + the mascot gate | backlog | none |
| HS-56-02 | The dock + the card shell | backlog | HS-56-01 |
| HS-56-03 | The actuator card (marquee; absorbs G) | backlog | HS-56-02 |
| HS-56-04 | Learning + aftercare cards | backlog | HS-56-02 |
| HS-56-05 | The native HUD frame | backlog | HS-56-02 |
| HS-56-06 | Docs: Qlippy | backlog | HS-56-03, HS-56-04 |
| HS-56-07 | Closeout: live dogfood + final-summary + PR | backlog | HS-56-01..06 |

## Where we are

Scaffolded 2026-06-11. Nothing has shipped. Start with **HS-56-01** (assets +
gate): vendored sprites + the config flag + the settings sub-toggle are the
foundation and the off-switch for everything after.

## Open decisions (defaults chosen per the RFC's open questions; flag to change)

- **Anchor:** bottom-right (web); the native HUD stays top-right where the
  ring lives today (moving the native anchor is HS-56-05's call, documented
  in evidence).
- **One global `presence.mascot` toggle**, default off (existing presence
  users keep the minimal ring).
- **`actuator_proposed` cards never auto-expire**; non-actionable cards
  auto-dismiss (timings per the RFC, tuned in HS-56-02).
- **`questioning` stays unused** this phase; idle → sleeping at **5 minutes**
  (a constant, not config).
- **Silent always** (no chime).
