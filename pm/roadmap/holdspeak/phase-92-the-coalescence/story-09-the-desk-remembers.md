# HS-92-09 — The Desk remembers what needs you

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress
- **Depends on:** HS-92-03, HS-92-04, HS-92-05, HS-92-06, HS-92-07, HS-92-08
- **Unblocks:** HS-92-10
- **Owner:** unassigned

## Problem

Archive, journal, Activity, Cadence, Qlippy, Queue HUD, Mission Control, sync,
proposal, connector, and steering audit surfaces each answer part of “what needs
me and what happened.” A new global queue would create another competing product.
Attention and receipts should instead attach to the Desk subject and remain
operable without spatial/pointer dexterity.

## Scope

- **In:** Additive AttentionProjection and Receipt index over existing domain
  records; subject/destination/correlation links; Desk contextual badges/cards;
  today/tomorrow return state; detail drawer; progressive disclosure; Web
  semantic list/search/filter/count/pagination; keyboard/focus; Swift semantic
  list/actions, VoiceOver, Reduce Motion, Dynamic Type; forced failure recovery.
- **Out:** Replacing feature journals/audits; a universal queue page; remote
  analytics; removing Qlippy, the belt, spatiality, or platform-native motion.
- **Paths:** existing audit/journal/job repositories under `holdspeak/db/`,
  `holdspeak/web/routes/activity/`, `holdspeak/web/routes/cadence.py`,
  `holdspeak/web/routes/missioncontrol.py`, `holdspeak/web/routes/sync.py`,
  `web/src/desk/`, `web/src/components/AmbientLayer.tsx`,
  `web/src/runtime/RuntimeBus.tsx`, `apple/App/MeetingCapture/DeskDioramaStage.swift`,
  `apple/App/MeetingCapture/DeskHome.swift`, native Queue/Presence components,
  and accessibility/fault/UAT tests.

## Acceptance criteria

- [ ] One additive index can answer subject, reason, decision kind, attention
      state, actual destination, authority basis, attempt/outcome, timestamp,
      and source-record link without copying sensitive payloads unnecessarily.
- [ ] Meeting, Artifact, Persona/Workflow run, Coder session, Integration,
      pairing/sync, capture recovery, and failed job each project contextual
      attention/receipts onto their Desk subject.
- [ ] Returning the next day shows what is waiting, what failed, what ran, and
      what is complete without requiring visits to seven feature histories; a
      dismissed projection does not mutate its subject.
- [ ] Detailed feature journals/audits remain reachable from the Receipt drawer
      for expert inspection; Qlippy and Mission Control consume the shared
      projection rather than inventing independent decision semantics.
- [ ] Web Desk offers visible counts, search/filter, pagination/virtualization,
      and a semantic list mode with no silent 24-item truncation or horizontal
      overflow at compact width.
- [ ] Keyboard-only Web and VoiceOver native users can create/open/select/file,
      run, inspect destination, review/approve, recover failure, and inspect a
      Receipt; no primary action requires drag, hover, or spatial memory.
- [ ] Reduce Motion stops continuous decorative animation and accessibility
      text sizes preserve state and actions while the normal Desk retains its
      materialize, sprite, haptic, and spatial delight.
- [ ] Forced 400, 401/403, 409, 500, timeout, offline, disk-full, malformed
      response, and partial completion retain user work and offer the correct
      next action on both clients.

## Test plan

- **Unit:** Receipt/attention adapters for actuator, steering, sync, dictation,
  meeting, job, and Cadence stores; `uv run pytest -q tests/unit/test_web_null_read_guard.py tests/unit/test_frontend_density_guard.py tests/unit/test_steering_audit_completeness.py`; Web axe/focus/list tests; Swift accessibility/state tests.
- **Integration:** Qlippy, Activity, Cadence, History, Desk, sync, and RuntimeBus
  tests plus `scripts/web_ui_audit.py`; UAT return-next-day and forced-failure
  campaigns with exact production targets.
- **Manual / device:** Seed 1,000 mixed Desk items and one of every attention/
  receipt family; complete keyboard-only Web and screen-curtain VoiceOver walks,
  reduced motion, accessibility text, compact/wide/orientation, relaunch, and
  next-day pickup.

## Notes / open questions

Receipt is a user-facing read model over authoritative records. Do not turn it
into a second audit store that can disagree with the source lifecycle.
