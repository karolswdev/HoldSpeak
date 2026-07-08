# HS-87-05 — Classify: triage from the pull-out

- **Project:** holdspeak
- **Phase:** 87
- **Status:** backlog
- **Depends on:** HS-87-03
- **Unblocks:** HS-87-06
- **Owner:** unassigned

## Problem

React and steer are half the loop; the other half is putting what a
session surfaces WHERE IT BELONGS: this question is a decision to
keep, that ask maps to a story, this session IS story HS-87-03 even
though the correlation said ambiguous. Classify verbs turn session
exhaust into desk primitives and rails truth — through existing
write paths only.

## Scope

- In: from the session pull-out — (a) **keep as note**: the session's
  current ask (`last_assistant_text`) becomes a desk note primitive,
  lineage naming the session key + agent + ts (the existing
  primitive-create route; no new store); (b) **pin to story**: an
  `ambiguous`/`idle_on_rails` session manually pinned to a story id,
  the pin held desk-side (a `steering.ts` pinning map persisted via
  the existing desk positions/state channel), rendered by the
  conveyor's pins with a `manual` marker — the honest correlation
  stays untouched and re-asserts if the registry changes; (c) **flip
  from here**: the Phase-82 story-flip proposal launched from the
  pull-out with the session's story pre-picked — the SAME
  propose→approve→execute leg, zero new write machinery.
- Out: auto-classification of any kind; editing dw files directly;
  new primitive kinds; touching `dw sessions` correlation logic.

## Acceptance criteria

- [ ] "Keep as note" creates a real desk note whose body is the ask
      and whose lineage names session/agent/timestamp; it files,
      ropes, and opens like any primitive (the filed-objects-stay-
      openable rule).
- [ ] A manual pin renders distinctly from an `on_story` correlation
      (never disguised as the correlator's verdict) and survives a
      conveyor refresh; clearing it is one tap.
- [ ] "Flip from here" round-trips the Phase-82 leg end-to-end from
      the pull-out (proposal card, approve, the dw gate's say) — its
      existing tests untouched.
- [ ] Desk locks green (no prose, no modals); full suite green (read
      from the file).

## Test plan

- Unit: note-creation payload/lineage tests; pin store tests
  (manual vs correlated precedence, clear); flip-prefill tests.
- Integration: the live keep-as-note + flip from a real session.
- Manual / device: triage a real session end to end.

## Implementation direction

- **Keep as note:** the desk create path already exists
  (`web/src/desk/api.ts` primitive create + the hub primitives
  routes); lineage rides the same provenance shape the ask keep-flow
  mints (see the Phase-83 "kept answer becomes an artifact" pass —
  mirror its fields, do not invent).
- **Manual pin storage:** desk-side, in the same channel the desk
  persists its own arrangement (the positions contract) — NOT the
  hub db and NOT the registry; the pin is a view preference over
  receipts, and it must never masquerade as `dw sessions` output
  (`manual: true` in the view model, a hollow pin ring in CSS).
- **Flip prefill:** the conveyor's `PickTarget` already carries
  repo/project/story — export the picker action from
  `missioncontrol.ts` and call it with the pinned story; the
  ProposalCard renders where it always renders.
- **Voice:** every new input in these verbs gets the mic (canon);
  keep-as-note's title field included.
