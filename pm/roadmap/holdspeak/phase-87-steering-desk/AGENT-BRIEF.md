# AGENT-BRIEF — Phase 87: The Steering Desk (B2, at the owner's bar)

Read this, then `docs/internal/MISSION_CONTROL_DESK.md`, then the
upstream Telegram interface (`~/dev/reusable-processes/integrations/
telegram/` + `docs/absorption-ccgram.md`) before touching anything.
The Telegram layer is the steering-craft PRECEDENT this phase ports
natively; the desk must end up strictly better, never looser.

## The owner's bar (verbatim, 2026-07-07/08)

> "are we really going to pretend that it's seriously robust enough
> to actually offer a real view into a real agent session (ability to
> attach to a sesh just as exposed by dw via the telegram
> integration) — but also — at the same time — offer an even more…
> streamlined DeskOS-first way to react/steer and classify things.
> Even things like including specific things from the Desk as context
> and so on. Like I said — this should be an incredibly robust thing
> around this framework. So robust, it will literally destroy our
> brains."

Decode: four capability families, one admission criterion.

1. **Attach** — a real live view into a real agent session, from the
   desk, in the desk grammar.
2. **Steer** — react and reply, voice-first, streamlined beyond what
   the phone offers.
3. **Classify** — triage what the session is doing onto the rails and
   the desk (session→story, ask→primitive, flip via the proposal leg).
4. **Desk objects as context** — a note, meeting, artifact, or KB
   entry from the desk rides INTO the steer, hydrated with provenance.

The admission criterion for every verb: the Telegram layer's consent
spine, or stronger. Robustness is not a story here; it is the gate.

## What already exists (do not rebuild)

| Capability | Where | State |
|---|---|---|
| Session registry (agent, model, awaiting, last text, tmux pane) | `~/.config/holdspeak/agent_sessions.json`, watched by `agent_context/` | production |
| Session board + spoken answer to a waiting coder | `web/routes/system/coders.py` (`/api/coders/status\|sessions\|select\|pin\|dismiss\|clear-stale`), `tmux_transport.send_text_to_pane` | production (Phase 78: the coder answered by voice) |
| Session↔story correlation | `dw sessions` via `missioncontrol_bridge.sessions_payload` | production (Phase 82/86) |
| Story-flip from the belt | `/api/missioncontrol/story/propose` + decision → gated two-argv dw connector | production (Phase 82) |
| Desk-object hydration with provenance | the grounding pass: hub `/api/ask` `grounding` refs hydration, `ContextEnvelope`+`GroundingSelection`, the "Ground this ask" picker, `GroundingSection.tsx` | production (Phase 83 / HSM-15-12) |
| In-place pull-out surface | `web/src/desk/components/Pullout.tsx` (the DioPullout port) | production |
| Live-view/steering craft: capture-pane with content-hash gating, per-keystroke pane-ownership verification, arming grants (TTL, revoke), session recovery | UPSTREAM `integrations/telegram/{tmuxdrive,consent,lifecycle,runtime}.py` | precedent to port, not import |
| The one bus + belt frames | `runtime-bus.js`, `scope:"belt"` frames (Phase 86) | production |

## The consent spine (ported semantics — pinned, not optional)

- **Watching is free; steering is armed.** Opening the session
  pull-out (read view) needs no grant. ANY keystroke toward a pane
  requires an active ARMING GRANT for that session.
- **Arming is an explicit desk act** per session: default TTL 15
  minutes (the upstream default), a visible countdown, one-tap
  disarm, auto-expiry. Arming state is hub-side and in-memory (a
  restart disarms everything — fail closed).
- **Pane identity is pinned at arm time and re-verified before every
  keystroke.** Capture `#{pane_id}` when the grant is issued; before
  each send, resolve the registry's pane target and compare pane_id;
  mismatch = refuse and DISARM (the upstream recycled-pane-id lesson:
  tmux reuses `%N`; a recycled pane must never receive text meant for
  its predecessor).
- **Every steer is audited**: who/when/session/pane_id/text-hash/
  grounding refs, queryable. A steer within an armed window is
  auto-approved by the grant (the voice-macro rule: configuring —
  here, arming — is the consent), but never invisible.
- **The dw gate keeps final say** on anything touching the rails; its
  refusal banner rides back verbatim (the Phase-82 crown case).
- **Nothing here egresses the machine.** Steering is a local
  consequential act; SECURITY.md gets a consent-model row, not an
  egress row (verify against the table before writing).

## The manipulation bar (owner-set, cross-surface)

> "being basically so incredibly well versed in writing plugins, that
> its affordances, integration seams, natural interfaces… become
> incredibly vital to us… they basically act so natively awesomely,
> both on the web, but as well as on the iPad and iPhone, that oh my
> gosh, don't we just want to keep manipulating it, no?"

Three binding consequences:

1. **Every steering/belt shape is a CONTRACT, not a view model.** The
   grant, the peek, the steer, the audit row, the classify verbs get
   documented wire shapes the way the Primitive Framework documents
   primitives (`pm/roadmap/holdspeak-mobile/contracts/`), so the iPad
   and iPhone render them natively instead of scraping a web page.
   The phone already answers a waiting coder by voice (HSM Phase 13)
   — the session pull-out, armed steer, and grounding picker are its
   next chapter, and B4 must not need a redesign to get them. When a
   story adds a wire shape, it writes the shape down.
2. **The seams stay plugin-writable.** The framework already writes
   HoldSpeak plugins (the upstream dw synthesizer + actuator packs);
   the belt and the steering surface must return the favor: awaiting
   sessions and gate refusals are broadcast frames any card surface
   (Qlippy, HUD, a future pack) can render; the classify verbs land
   on public routes a pack can call through the same gates. Nothing
   in this phase may be reachable only from inside one React tree.
3. **Delight is acceptance, not decoration.** The test of every
   affordance is the owner's sentence: do you want to keep
   manipulating it? Chips that answer in place, holds that feel like
   consent, lights that are receipts — if a verb needs explaining,
   it fails the desk grammar and goes back.

## Implementation directions that are already decided

- **Peek transport:** `tmux capture-pane -p -t <pane> -e -S -<N>` via
  a new `holdspeak/coder_steering.py` module (subprocess, injectable
  runner, the `missioncontrol_bridge` pattern). Content-hash gate:
  return `not_modified` when the hash matches the client's last seen
  (the upstream `/live` edit-in-place trick) so polling stays cheap.
  Strip ANSI with a compiled regex; cap at ~200 lines / 64 KB.
- **Frames, not private polling:** peek reads ride a short poll from
  the OPEN pull-out only (1–2 s while open, stop on close); a
  `scope:"coder"` frame on the one bus announces awaiting-response
  transitions (the registry watcher already knows them) so closed
  surfaces stay current without polling.
- **Steer delivery:** compose → ownership check → `send_text_to_pane`
  (literal text, settle delay, Enter as its own keystroke — the
  upstream TUI-send craft is already inside `send_text_to_pane`;
  verify, don't duplicate).
- **Grounding into a steer:** reuse the `/api/ask` hydration seam —
  factor the hydration helper so both ask and steer call it; the
  steered text carries fenced blocks with one-line provenance headers
  (`--- from <kind>: <title> ---`). Token budget: cap hydrated
  context (~8 KB) and SAY so in the composer (the gauge pattern).
- **UI:** the session pull-out is a desk `Pullout` sibling, not a new
  surface; the composer is the desk composer with `MicButton`
  (voice-mic-every-input canon); the grounding picker is
  `GroundingSection` reused. No modals; no prose; Signal tokens.
- **State:** zustand slice `steering.ts` beside `missioncontrol.ts`;
  wire shapes normalized the same way (snake_case wire → camelCase
  view, typed statuses rendered honestly).

## Gotchas from the trenches

- The registry can go stale (30 min TTL upstream); a stale session
  must render stale and REFUSE arming.
- `send_text_to_pane` submits with Enter by default — the composer
  needs an explicit no-submit mode for multi-part steers (check the
  `submit` flag; it exists).
- tmux absent (`shutil.which`) is a typed absence everywhere, never
  a 500 — the coders board already has this posture; keep it.
- The suite lands in a file and is READ before any story flips
  (memory: read-output-before-flip; it earned its place this phase).
- api-surface regen AFTER web call sites; web bundle rebuilt from
  `web/src`; screenshots get looked at, not just taken.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
