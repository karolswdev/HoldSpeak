# Phase 173 - The Steward's Hand and Voice

**Last updated:** 2026-09-05.

## Goal

The steward writes a stakeholder update a human can read, nudges a
reviewer when the owner says yes, and surfaces the health signals
buried in Watch snapshots. The model drafter rewrites the deterministic
inventory into prose with every claim referenced and unverified claims
marked (Article VI). Reviewer latency and issue aging become NEEDS YOU
rows. The FIRST bounded external effect (a reviewer-nudge comment via
`gh`) ships behind the policy gate with a terminal receipt (Article V:
acting is armed; Article XI: admitted, receipted). Flaky CI and
merge-queue depth from `branch_ci` history surface as Room tokens. A
release-readiness scorecard row appears in the Room.

## Status

**ACTIVE 0/9 — STACKED on 172 (PR #555) on 171 (#554) on 170 (#553); branch `feat/the-stewards-hand` off `feat/the-loop-closes`.**

**Depends on:** Phase 172.

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Monday, 18:00. The steward drafted this week's update from the real
deltas: prose a stakeholder can read, every claim with its ref,
unverified claims marked. He edits two sentences and publishes. Tuesday,
09:00 the Room reads "Ania is the review bottleneck this week: 47 h
median, 3 PRs waiting" and the steward asks: "Nudge her on #612?" One
receipted comment if he says yes.

Census facts from THE-TUESDAY-ARC.md section 0 that this phase pays:
the model drafter is an identity stub (UPD-003); no reviewer latency
or issue aging derivations exist; no external effects have ever been
executed by the steward; the five V0 effect kinds
(project_steward_service.py:39) are all INTERNAL; `gh` is allow-listed
for reads only.

## Scope

- In:
  - The model drafter: the claim schema (Claim class,
    project_update_service.py:89) preserved; prose rewritten by the
    model; unverified claims marked (Article VI); the egress chip on
    the draft card (Article III).
  - Reviewer-latency and issue-aging derivations at evaluation time:
    per-person medians computed from `reviewRequests`, `updatedAt`,
    `reviewDecision` on PR entities in Watch snapshots; time-in-status
    from Jira entity timestamps; surfacing as NEEDS YOU rows and Room
    tokens.
  - The FIRST bounded external effect: `github.comment` (the reviewer
    nudge) behind the eligible_effect_kinds policy gate
    (project_steward_service.py:837) with a terminal receipt and the
    comment URL (Article V:1, Article XI:2).
  - Flaky-CI and merge-queue depth from `branch_ci` entity history
    (limit 10) in Watch snapshots; one GH search for open PRs to
    merge queue.
  - A release-readiness scorecard as a Room token row (green / amber /
    red per signal: review latency, CI health, open blockers, overdue
    commitments).
  - The design on the library before build (canvas at 1440 + 393).
  - His walk on his desk: a drafted update he edits and publishes; a
    nudge he approves.
- Out:
  - Non-GitHub external effects (Jira comments, Slack messages).
  - Automatic nudges (the owner must approve each one; Article V).
  - New Watch conditions or templates beyond the existing 16.
  - Calendar integration (Phase 175).
  - The full portfolio view across projects (Phase 178).

## Exit criteria (evidence required)

- [ ] The model drafter rewrites the deterministic inventory into
      stakeholder-readable prose with every claim referenced and
      unverified claims marked; the egress chip appears on the draft
      card.
- [ ] Reviewer-latency derivation computes per-person median hours
      from Watch snapshots; surfaces as a NEEDS YOU row when the
      median exceeds a threshold (default 48 h).
- [ ] Issue-aging derivation computes time-in-status from Jira entity
      timestamps; surfaces as a NEEDS YOU row when an issue exceeds
      the threshold.
- [ ] The reviewer nudge (`github.comment`) executes behind the policy
      gate with a terminal receipt containing the comment URL;
      verified by a rig that approves a nudge and reads the receipt.
- [ ] Flaky-CI signals and merge-queue depth from `branch_ci` history
      appear as Room tokens.
- [ ] The release-readiness scorecard appears in the Room with
      per-signal indicators.
- [ ] The design on the canvas at 1440 + 393 is ratified by the owner
      before the build.
- [ ] His walk on his desk: a drafted update, a nudge he approves,
      the reviewer-latency row; his word.
- [ ] Zero unreceipted egress; the nudge comment is the ONLY external
      write, behind the gate (Article III, Article V, Article XI).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-173-01 | The design (the Steward's faces on the canvas before build) | done | [story-01-the-design](./story-01-the-design.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-173-02 | The model drafter (claims preserved, prose rewritten, unverified marked) | done | [story-02-the-model-drafter](./story-02-the-model-drafter.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-173-03 | The health signals (reviewer latency, issue aging, flaky CI, merge-queue depth) | done | [story-03-the-health-signals](./story-03-the-health-signals.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-173-04 | The reviewer nudge (the first bounded external effect behind the policy gate) | in-progress | [story-04-the-reviewer-nudge](./story-04-the-reviewer-nudge.md) | -- |
| HS-173-05 | The release-readiness scorecard (the Room token row) | in-progress | [story-05-the-release-readiness](./story-05-the-release-readiness.md) | -- |
| HS-173-06 | The walk (his desk: a drafted update, a nudge he approves) | in-progress | [story-06-the-walk](./story-06-the-walk.md) | -- |
| HS-173-07 | The docs (the steward's hand in the architecture; the nudge in SECURITY) | done | [story-07-the-docs](./story-07-the-docs.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-173-08 | The hygiene lane (items from THE-TUESDAY-ARC.md section 4 this phase touches) | done | [story-08-the-hygiene-lane](./story-08-the-hygiene-lane.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-173-09 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-09-the-close](./story-09-the-close.md) | -- |

## Where we are

**2026-09-05 19:10 — 4/9 DONE on evidence (01 design · 02 drafter · 07
docs · 08 hygiene); the wire for 03/04/05 committed; the Room faces
checkpointed with seven small fixes landing (plurals, number format,
NUDGED JUST NOW after Send, the name as stored, the 393 lead, no empty
chip); the runner's selectors being filled. Then counsel-on-built →
his-desk walk (every write denied) → full suite → close (09) → PR
`--base feat/the-loop-closes`.**

**2026-09-05 17:25 — ACTIVATED, STACKED.** Under the standing goal the
faces build to counsel-ratified boards and his word gates the MERGE
(the decision recorded for 170–172). Nine boards for D2 (a)–(e) on the canvas
(https://claude.ai/code/artifact/9f1558b4-0867-4152-bc7e-1314dde5e82c),
counsel reading; the walk runner drafted (06); wire lanes follow the 172 suite. Merge order stays his:
#553 → #554 → #555 → 173's.

Earlier: PLANNED. Waiting for Phase 172. The recon is complete: the model drafter
exists as `_draft_with_model` (project_update_service.py:679) and is
functional -- it resolves a deployment revision for the
`project.update.draft` capability, builds a prompt from the
deterministic claim inventory, and invokes the inference runner; but on
the owner's desk no assignment is configured for this capability (the
170 concierge must land first); the steward has five V0 effect kinds
(project_steward_service.py:39: refresh_sources, create_proposals,
apply_proposal_effects, draft_update, create_door_item) all INTERNAL
with zero external writes; `eligible_effect_kinds_json` defaults to
`"[]"` (project_steward_service.py:1530); `gh` is allow-listed for
reads (the list command in provider runs); PR entities carry
`reviewRequests` (watch_sources.py:108), `reviewDecision`,
`updatedAt`; `branch_ci` entities exist
(project_service.py:61) but no latency/aging derivation is computed
from them; no release-readiness concept exists yet.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| The first external write is a constitutional event | High | Counsel reads the nudge implementation before the owner; the policy gate is opt-in per project; the receipt is terminal and carries the comment URL; Article V and XI are cited in every acceptance criterion | The owner rejects the nudge concept at design time |
| Model-drafted prose quality | Medium | The deterministic inventory is the floor; the model rewrites it; unverified claims are MARKED, never smoothed (Article VI); the owner edits before publish | > 30% of claims are marked unverified on the owner's real data |
| Reviewer latency false positives | Low | The threshold is configurable per project (default 48 h); the derivation is per-person median, not single-PR outliers | The owner mutes the latency row within 48 h of his walk |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- The reviewer-nudge comment template: the exact wording of the GH
  comment -- decided at design time, reviewed by counsel.
- The release-readiness signal set: which signals compose the
  scorecard (review latency, CI health, open blockers, overdue
  commitments are the candidates) -- decided at design time.
- The latency threshold default (48 h proposed) -- confirmed with the
  owner at design time.
