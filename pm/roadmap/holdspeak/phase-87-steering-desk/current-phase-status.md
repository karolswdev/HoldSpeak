# Phase 87 — The Steering Desk (B2: attach, steer, classify, ground)

**Last updated:** 2026-07-08 (HS-87-01 done — attach shipped).

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

- [ ] A live agent session is watched from the desk pull-out (real
      pane content, updating, honest staleness) with zero grants
      issued (HS-87-01).
- [ ] An unarmed steer is refused; an armed steer lands in the real
      pane; a recycled-pane steer is refused AND disarms; expiry and
      disarm are visible on the desk (HS-87-02/03, crown cases
      captured live).
- [ ] A steer carries a real desk object (meeting artifact or note)
      as hydrated, provenance-headed context, and the receiving
      agent's next output demonstrably uses it (control vs treatment,
      the Phase-53 proof pattern) (HS-87-04).
- [ ] Classify: a session's ask becomes a desk primitive; a story
      flip proposed from the pull-out rides the Phase-82 leg
      end-to-end (HS-87-05).
- [ ] The audit trail answers who/when/what/where for every steer of
      the walk; the suite + guards green; docs shipped (HS-87-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-87-01 | Attach: the session pull-out with the live pane view | done | [story-01-session-pullout](./story-01-session-pullout.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-87-02 | The arming grant: consent with a countdown | backlog | [story-02-arming-grant](./story-02-arming-grant.md) | - |
| HS-87-03 | Steer: the voice-first composer, delivered and audited | backlog | [story-03-steer-composer](./story-03-steer-composer.md) | - |
| HS-87-04 | Ground: desk objects ride into the steer | backlog | [story-04-desk-context](./story-04-desk-context.md) | - |
| HS-87-05 | Classify: triage from the pull-out | backlog | [story-05-classify-verbs](./story-05-classify-verbs.md) | - |
| HS-87-06 | The robustness rig, the walk, the docs | backlog | [story-06-robustness-walk](./story-06-robustness-walk.md) | - |

## Where we are

Attach is real (HS-87-01): `coder_steering.peek_pane` reads a pane's
tail through an injectable runner with the sha256 hash gate;
`GET /api/coders/{key}/peek` serves it with the honest envelope
(stale, awaiting, typed absences — `no_pane`, `pane_gone`,
`tmux_absent` — never a 500); the SessionPullout renders the live
view (poll only-while-open, 1.5 s, single-flight) and opens from the
conveyor SessionPin and the coder pull-out's "Watch live"; the hub's
one registry observer broadcasts `scope:"coder"` frames on
awaiting-response transitions. Proven live against a real tmux pane
(evidence). Next: HS-87-02, the arming grant.

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

## Decisions deferred

- Multi-pane sessions (windows beyond the registry's one pane) —
  trigger: a real registry entry with several panes — default: steer
  only the registered pane.
- Steering sessions on OTHER mesh nodes (the relay precedent) — B3+
  territory — default: local tmux only, typed absence otherwise.
- A persistent arming ledger (grants surviving restart) — default:
  no; fail closed is the feature.
