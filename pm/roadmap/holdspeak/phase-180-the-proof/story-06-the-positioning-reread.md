# HS-180-06 — The positioning re-read

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** HS-180-01
- **Unblocks:** HS-180-09
- **Owner:** unassigned

## Problem

POSITIONING.md makes claims: four pillars, a competitive frame,
canonical feature names. The release candidate must not ship with
claims the code does not back. The positioning is re-read against the
shipped product and the measured week's verdicts.

## Scope

- In:
  - Re-read each pillar claim against the shipped product:
    - "Everything local, including the intelligence" -- verified
      against Article III evidence, the egress posture, the Concierge.
    - "It learns how you work, and shows you the receipts" -- verified
      against dictation corrections, the learning digest, the journal.
    - "Meetings end with their loops closed" -- verified against 172's
      decisions, commitments, the 1:1 brief, the measured week's
      meeting verdicts.
    - "Honest by construction" -- verified against `holdspeak doctor`,
      the census, the Constitution audit.
  - Re-read the competitive frame: are the "What HoldSpeak does
    better" claims still true?
  - Re-read the canonical feature names: are any stale, renamed, or
    retired?
  - Re-read the voice rules: do the shipped docs comply?
  - Gaps named honestly; amendments proposed to the owner.
- Out:
  - Amending POSITIONING.md (the owner amends; this story names gaps).
  - Marketing material.

## Acceptance criteria

- [ ] Every pillar claim re-read with evidence from the shipped
      product and the measured week (Article VI.3 -- copy never
      promises what the code does not do).
- [ ] The competitive frame re-read; stale claims named.
- [ ] Canonical feature names re-read; stale names flagged.
- [ ] The re-read document filed as evidence.
- [ ] Amendments proposed to the owner for any gaps.

## Test plan

- Unit: n/a.
- Integration: n/a.
- Manual: the re-read is a manual review.

## Notes / open questions

- The "Meetings end with their loops closed" pillar is the most
  demanding: it requires 172 to have shipped and the measured week
  to have included at least one real meeting with decisions and
  commitments.
