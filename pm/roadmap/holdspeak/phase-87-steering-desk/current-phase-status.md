# Phase 87 — The Steering Desk (B2: attach, steer, classify, ground)

**Last updated:** 2026-07-08 (**PHASE CLOSED 6/6** — the walk passed live, docs shipped).

## Goal

The desk becomes the primary steering surface for live agent
sessions — a real view into a real session (attach), voice-first
reply with desk objects riding in as hydrated context (steer +
ground), and triage onto the rails and the desk (classify) — every
verb admitted only under the Telegram layer's consent spine or
stronger: watching free, steering armed, pane identity verified per
keystroke, everything audited, the dw gate keeping final say. Owner
bar: *"so robust, it will literally destroy our brains."*

## Scope

- In: the session pull-out with a live pane view (`coder_steering.py`
  peek + content-hash gating + `scope:"coder"` frames); the arming
  grant model (TTL, pinned pane identity, disarm, fail-closed on
  restart); the voice-first steer composer delivering through
  `send_text_to_pane` behind per-keystroke ownership checks with a
  full audit trail; desk-object grounding into steers (the Phase-83
  hydration seam, factored and reused); classify verbs (session→story
  pin, ask→desk-primitive, story flips via the Phase-82 proposal
  leg, all reachable from the pull-out); the robustness rig (crown
  cases proven live) + docs + the closing walk.
- Out: any NEW egress (steering never leaves the machine); B3 ("New
  Project" from the desk) and B4 (DeskOS/iPad belt) per the RFC;
  changes to the Telegram layer upstream (precedent only); autonomous
  steering of any kind (a human is behind every keystroke or it does
  not send).

## Exit criteria (evidence required)

- [x] A live agent session is watched from the desk pull-out (real
      pane content, updating, honest staleness) with zero grants
      issued (HS-87-01).
- [x] An unarmed steer is refused; an armed steer lands in the real
      pane; a recycled-pane steer is refused AND disarms; expiry and
      disarm are visible on the desk (HS-87-02/03, crown cases
      captured live in the walk).
- [x] A steer carries a real desk object (meeting artifact or note)
      as hydrated, provenance-headed context, and the receiving
      agent's next output demonstrably uses it (control vs treatment
      on .43, the Phase-53 proof pattern) (HS-87-04).
- [x] Classify: a session's ask becomes a desk primitive; a story
      flip proposed from the pull-out rides the Phase-82 leg
      end-to-end (HS-87-05).
- [x] The audit trail answers who/when/what/where for every steer of
      the walk; the suite + guards green; docs shipped (HS-87-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-87-01 | Attach: the session pull-out with the live pane view | done | [story-01-session-pullout](./story-01-session-pullout.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-87-02 | The arming grant: consent with a countdown | done | [story-02-arming-grant](./story-02-arming-grant.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-87-03 | Steer: the voice-first composer, delivered and audited | done | [story-03-steer-composer](./story-03-steer-composer.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-87-04 | Ground: desk objects ride into the steer | done | [story-04-desk-context](./story-04-desk-context.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-87-05 | Classify: triage from the pull-out | done | [story-05-classify-verbs](./story-05-classify-verbs.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-87-06 | The robustness rig, the walk, the docs | done | [story-06-robustness-walk](./story-06-robustness-walk.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Attach, arm, AND steer are real (HS-87-01/02/03). The full spine
sends: `coder_steering.deliver` is the ONE chokepoint — grant check
→ resolve the registry's current pane → send to the VERIFIED `%N`
(never the target string, so nothing re-resolves between check and
keystroke) → audit row. Delivery reuses `send_text_to_pane` verbatim
(literal text, `\r` submit). The `steering_audit` table (schema v12,
canonical snapshot regenerated) records who/when/session/pane/shape
for every attempt, delivered or refused; the receipt is the sha256 +
first 120 chars, never the full steer. Routes: `POST /{key}/steer`
(unarmed → typed 409, revoking refusal frames the disarm), `GET
/steering/audit`. Desk: the voice-first composer (MicButton, no-submit
`⏎` toggle) mounts only while armed — the ARM chip IS the unarmed
affordance. The chokepoint census (`test_steering_chokepoint.py`)
pins the `send_text_to_pane` call sites mechanically; the steering
routes were carved into `coder_steering_routes.py` (the Phase-79
single-concern budget). Live-proven: an armed steer lands in a real
pane, the recycled-pane crown case refuses and revokes.

Grounding is real (HS-87-04): the Phase-83 ask hydration was factored
verbatim into `holdspeak/grounding.py` (`hydrate_refs` →
`GroundingBlock`s; ask's `[MEETING: …]` formatting is a thin re-export
so ask/recipes tests pass unmodified). `compose_steer` builds the
steer — message first, then per-object `--- from <kind>: "<title>" ---`
fences, then a count line — hard-capped at 8 KB (over-cap refuses at
compose time, executed == previewed via `preview: true`). `POST
/{key}/steer` gained `grounding` refs (unknown → 400 named, over-cap →
409 named); the audit row carries the refs; the desk composer mounts
`GroundingSection` with an 8 KB gauge. Control-vs-treatment PROVEN on
.43: the bare question gets "I don't have access…"; the grounded steer
gets "Friday the 13th at 3:47pm, code-named BLUEBIRD" — the exact
composed text landing in a real pane.

Classify is real (HS-87-05): three triage verbs from the pull-out,
all through existing write paths. **Keep as note** — `POST
/{key}/keep-note` mints a real desk note whose body is the ask and
whose lineage names session/agent/timestamp (proven live openable).
**Pin to story** — a desk-side `manualPins` map in `steering.ts`
(localStorage, the positions-contract channel), rendered by the
conveyor as a HOLLOW dashed ring, never disguised as the correlator's
verdict, dropped when the session leaves the registry and re-asserted
when it returns. **Flip from here** — `flipTargetForStory` resolves
the session's correlated story to `{repo, project, story}` and calls
the Phase-82 `proposeFlip`; the ProposalCard renders where it always
does.

**CLOSED (HS-87-06).** The eight-beat walk ran live against one real
tmux pane and the real `.43` model: attach, refuse-unarmed, arm,
steer, ground (control vs treatment), classify (keep note), then the
crown cases — recycled pane refused+revoked, TTL expiry
refused+revoked, cross-surface disarm → next send unarmed — and the
audit trail read back with every steer's row present. Mechanical
rules: the chokepoint census pins `send_text_to_pane`'s call sites,
audit-completeness pins one row per outcome, the desk locks already
cover the pull-out tree. Docs shipped: USER_GUIDE "Steer a session
from the desk", the SECURITY.md consent-model boundary, the
ARCHITECTURE.md steering-chokepoint paragraph. The B3/B4 handoff is
in the [final summary](./final-summary.md).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Typing into the wrong pane (recycled id / retargeted registry) | the reason this phase exists | pane_id pinned at arm, verified per keystroke, mismatch disarms; property-tested + a live crown case | any delivered steer whose pane_id was not re-verified |
| Peek polling melts the hub or the event loop | medium | capture only while a pull-out is open (1–2 s), content-hash `not_modified`, subprocess via to_thread | hub p95 degrades while one pull-out idles |
| Grounding bloats a steer past what a TUI agent can take | medium | ~8 KB hydration cap, shown in the composer; fenced blocks with provenance headers | a steer truncated silently by the terminal |
| Consent theater (arming that nothing actually enforces) | low | enforcement lives hub-side in ONE chokepoint (`coder_steering.deliver`), not in the UI; unarmed API calls refused in tests | any steer path that bypasses the chokepoint |
| The desk out-grows the phone but loses its craft (settle delays, literal sends) | low | delivery reuses `send_text_to_pane` verbatim; upstream absorb-ledger items 8/21 re-read at HS-87-03 | garbled multi-line steers on a real session |

## Decisions made (this phase)

- 2026-07-08 — Watching is free, steering is armed; arming is
  per-session, TTL'd, pinned to pane identity, fail-closed on
  restart — the Telegram consent spine ported natively — owner bar +
  upstream precedent.
- 2026-07-08 — One hub-side chokepoint for every keystroke toward a
  pane (`coder_steering.deliver`); the UI can never be the enforcer —
  the consent-theater risk row.
- 2026-07-08 — Steers within an armed window are auto-approved by the
  grant but always audited — the voice-macro consent rule, applied.
- 2026-07-08 — Grounding reuses the Phase-83 hydration seam (factored,
  not forked) — one hydration truth for ask and steer.
- 2026-07-08 (HS-87-01) — The awaiting-transition watcher lives
  hub-side (`web_server._coder_frames_loop`): the ingest-side
  detection runs in the hook's own process and cannot reach the bus,
  so the hub stats the registry file's mtime (2 s) and diffs
  awaiting flags — one observer, first observation a baseline
  (the HS-86-03 rule), frames on the one bus.
- 2026-07-08 (HS-87-03) — The legacy voice-answer paths (option (b)
  of the story): `/api/coders/select` + `/api/dictation/remote` (and
  the cadence Telegram answer leg) stay as they are, documented as
  the flows that TYPE ONLY WHEN A CODER ASKED — their consent story
  is the agent's own question. They never gain free-text steering;
  anything composed at the desk goes through `deliver`. The
  chokepoint census (`test_steering_chokepoint.py`) pins the
  call-site set mechanically.
- 2026-07-08 (HS-87-03) — `deliver` sends to the VERIFIED `%N`, not
  the target string: nothing can re-resolve between the ownership
  check and the keystroke (the TOCTOU window closed by construction).
- 2026-07-08 (HS-87-05) — The manual story pin is a DESK-SIDE view
  preference (localStorage `hs.steering.pins`), never the hub db and
  never `dw sessions` output: it renders as a hollow dashed ring, is
  skipped where the correlator already placed the session, and drops
  when the session leaves the registry (re-asserts on return). The
  honest correlation is untouched. Keep-as-note and flip reuse the
  existing note-create and Phase-82 propose→approve→execute paths —
  zero new write machinery.
- 2026-07-08 (HS-87-04) — Hydration factored to `holdspeak/grounding.py`
  as `hydrate_refs` → `GroundingBlock`s (raw), with ask's `[MEETING:…]`
  headers a thin re-export (`hydrate_grounding_blocks`); ask.py and
  recipes.py import the names unchanged, tests byte-identical. Steer
  composition (`compose_steer`) is separate from delivery: the route
  composes, `preview: true` returns the exact send text, and the send
  re-composes identically (executed == previewed by construction, one
  function). Steer cap is 8 KB, refused at compose time.

## Decisions deferred

- Multi-pane sessions (windows beyond the registry's one pane) —
  trigger: a real registry entry with several panes — default: steer
  only the registered pane.
- Steering sessions on OTHER mesh nodes (the relay precedent) — B3+
  territory — default: local tmux only, typed absence otherwise.
- A persistent arming ledger (grants surviving restart) — default:
  no; fail closed is the feature.
