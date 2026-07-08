# HS-88-02 — The grounding picker learns the rails

- **Project:** holdspeak
- **Phase:** 88
- **Status:** done
- **Depends on:** HS-88-01
- **Unblocks:** HS-88-05
- **Owner:** unassigned

## Problem

The hub can hydrate a rail object (HS-88-01); now the human has to be
able to PICK one. The grounding picker offers meetings today; it must
also offer the belt's live phases and stories, pickable into an ask
AND a Phase-87 steer through the one shared hydration — so grounding a
run with "the story I'm on" is one tap.

## Scope

- In: `GroundingSection` (or a rails-aware sibling) gains a rails
  source drawn from the `/api/missioncontrol/state` feed the conveyor
  already fetches (open phases + their stories, per repo/project); a
  picked rail object rides `hubGrounding` as a `rails` ref; the gauge
  prices it; the picker mounts in BOTH the ask panel and the Phase-87
  steer composer (one component, both surfaces); over-cap and unknown
  refuse in place.
- Out: the observer (03); a bespoke rails catalog endpoint if the
  state feed suffices; grounding rail objects the belt is not showing
  (off-belt/other-repo picks wait for the reach story).

## Acceptance criteria

- [ ] The picker lists the belt's live phases and their stories (from
      the state feed, no new endpoint if avoidable); picking one adds
      a `rails` ref to the grounding selection.
- [ ] The SAME picker selection grounds an ask and a Phase-87 steer
      identically — one hydration, proven by a test that the wire
      `rails` refs are byte-identical across both call sites.
- [ ] The token gauge counts a picked rail object's real fetched size;
      an over-budget selection refuses in the composer before the run
      (the existing gauge posture).
- [ ] Control vs treatment on a real model: the same question asked
      without and with a grounded OPEN STORY; the answer demonstrably
      uses the story's content (the Phase-53 proof pattern), captured.
- [ ] Desk locks green (no modals, no prose); full suite green (read
      from the file); desk vitest green; api-surface regenerated if a
      route was added.

## Test plan

- Unit: `web/src/desk/__tests__` — the rails source normalizer
  (state-feed → pickable rows), `hubGrounding` carrying `rails` refs,
  the gauge including a rail block; the ask/steer wire parity.
- Integration: the control-vs-treatment live proof (a real open story
  grounded, the model's answer using it).
- Manual / device: pick an open story into a steer on the live desk;
  screenshot the composer with the rail chip + gauge.

## Implementation direction

- **The source:** the conveyor already holds `repos → projects →
  phases/stories` in the `useMissionControl` store; expose a selector
  that flattens the CURRENT phase's stories (+ the phase itself, + the
  roadmap) into pickable `{repo, project, kind, id, title}` rows. No
  new fetch if the store is warm; a lazy fetch of the state feed if
  the picker opens cold.
- **The wire:** `hubGrounding` (grounding.ts) gains a `rails` array
  beside `meeting_ids`/`artifact_ids`; the hub route (ask + steer)
  passes it to the HS-88-01 hydrator.
- **The gauge:** a rail object's size is its file length / 4 (the
  existing token estimator); fetch the real length when picked (mirror
  `fetchGroundingMeeting`) so the gauge is honest, never guessed.
- **The UI:** a "Rails" group in the picker beside "Meetings";
  Signal tokens, a distinct-but-quiet glyph; no modal, no prose — the
  chip states WHAT (`HS-88-01`), the gauge states how much.
