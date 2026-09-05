# HS-172-03 — The proposal bridge

- **Project:** holdspeak
- **Phase:** 172
- **Status:** backlog
- **Depends on:** HS-172-02
- **Unblocks:** HS-172-05, HS-172-07
- **Owner:** unassigned

## Problem

The follow-through service (follow_through_service.py:114) has the
propose/approve/execute shape with provenance (meeting, segment,
speaker, timestamp) and the commit_decision verb
(follow_through_service.py:263). But extracted decisions and action items
from intelligence plugins never arrive as PROPOSALS in the Room's NEEDS
YOU today. The decision_records and decision_commitments tables are both
at 0 rows on the owner's desk. The arc says: decisions + action items
arrive as PROPOSALS confirmed through the kernel; Confirm writes the
decision record and the commitment (Article IV: voice arms, it does not
fire).

## Scope

- In:
  - After an intel job completes for a Room-linked meeting, the
    extracted decisions and action items become FollowThroughCards with
    provenance (meeting_id, segment index, speaker label, timestamp).
  - These cards appear in the Room's NEEDS YOU section as PROPOSALS
    (the existing follow_through board shape, filtered to the Room's
    project_id).
  - The Confirm verb on a PROPOSAL writes the decision_record and the
    decision_commitment through the kernel (Article V:
    propose-approve-execute; Article XI: receipted).
  - Edit lets the owner amend the extracted text before confirming.
  - Drop dismisses the proposal without creating a record.
  - The face for the PROPOSAL card follows the HS-172-01 artboard.
- Out:
  - Automatic filing (Confirm is the chokepoint; no auto-commit).
  - External notifications about decisions (Phase 173).
  - Editing a decision record after confirmation (existing
    update_record in decision_record_service.py:132 covers this).

## Acceptance criteria

- [ ] After a completed intel job for a Room-linked meeting, the
      extracted decisions and action items appear as FollowThroughCards
      with provenance; verified by reading the follow_through board.
- [ ] The Room's NEEDS YOU section shows these cards as PROPOSALS;
      verified at both widths (1440 + 393).
- [ ] Confirm writes a decision_record and a decision_commitment
      through the kernel; the receipt exists (Article XI.2).
- [ ] Edit allows amending the extracted text before Confirm; the
      amended text is what gets persisted.
- [ ] Drop dismisses the proposal; no decision_record or
      decision_commitment is created.
- [ ] No auto-commit of any extracted item (Article IV: voice arms, it
      does not fire).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k proposal_bridge`
  - Intel results produce FollowThroughCards with provenance.
  - Confirm writes decision_record + decision_commitment.
  - Edit + Confirm persists amended text.
  - Drop creates no record.
- Integration: the rig boots a hub, completes an intel job, reads the
  follow_through board, confirms one card, reads decision_records.
- Manual: the owner sees PROPOSALS in NEEDS YOU after a test meeting.

## Notes / open questions

- Which intelligence plugins produce decisions vs action items today?
  The existing plugins include DecisionAnnouncementDrafterPlugin
  (plugins/builtin/decision_announcement_drafter.py:104) which may
  already extract decisions. The mapping from plugin artifacts to
  FollowThroughCards is the bridge this story builds.
