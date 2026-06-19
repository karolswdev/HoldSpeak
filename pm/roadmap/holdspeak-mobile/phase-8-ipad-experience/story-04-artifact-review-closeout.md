# HSM-8-04 — Artifact review + notebook closeout

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HSM-8-01, HSM-8-02, HSM-8-03, HSM-6-02, HSM-7-03
- **Owner:** unassigned

## Problem

The charter's Track I gate is "meeting notebook workflow complete." That means
the loop closes: a recorded meeting yields artifacts the user can review on the
iPad, alongside their linked notes. This story adds the review surface and proves
the whole workflow end to end.

## Scope

- **In:** an artifact-review surface showing the Phase-6 artifacts
  (actions/decisions/risks/requirements/summary, plus ADR candidates/follow-ups)
  for a meeting, with the MIR profile selectable via the Phase-7 seam; the
  Propose→Review→Approve affordance on proposals (review + approve, never
  autonomous execute); the Gate closeout — the full record→notebook→link→review
  workflow on a real iPad.
- **Out:** building the artifact engine (Phase 6) or MIR (Phase 7). Connector
  execution. Sync (Phase 10). iPhone (Phase 9).

## Acceptance criteria

- [ ] A meeting's artifacts render on the iPad in a review surface, grouped by
      type, reflecting the active MIR profile (via the HSM-7-03 seam).
- [ ] Proposals can be reviewed and approved on-device; nothing executes
      autonomously (charter non-goal preserved).
- [ ] **Track I gate:** the full workflow — record → live transcript → PencilKit
      notebook → linked transcript moments → artifact review — runs end to end on
      a real iPad, evidenced by a device walkthrough.
- [ ] Egress on any actionable surface is shown as the desktop's egress badge
      (local / local+cloud / cloud + target), not privacy prose (positioning
      canon).

## Test plan

- Manual / device: the full end-to-end walkthrough on an iPad, captured as the
  gate evidence (screens/screen-recording).
- Unit: the review view-model over fake artifacts → grouping + approve flow
  without executing.

## Notes / open questions

- Depends on Phase 6 (artifacts) and Phase 7 (profile seam); sequence this story
  after they land so the review shows real, profile-shaped artifacts (phase risk).
- This closes Phase 8; on pass write `evidence-story-04.md` + `final-summary.md`.
- Inherit the desktop voice rules on these surfaces (egress badge, canonical
  names) per POSITIONING canon.
