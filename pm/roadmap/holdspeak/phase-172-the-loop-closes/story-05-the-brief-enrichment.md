# HS-172-05 — The 1:1 brief enrichment

- **Project:** holdspeak
- **Phase:** 172
- **Status:** in-progress
- **Depends on:** HS-172-03, HS-172-04
- **Unblocks:** HS-172-07
- **Owner:** unassigned

## Problem

The 1:1 brief (people_service.py:364) today returns open commitments,
agenda items, grounding note count, and linked meetings via
calendar_links. It does NOT read Watch data: open PRs waiting on the
person, review latency, open Jira assignments. The arc says: "the 1:1
brief and the People card read from Watches + commitments + meetings --
the chief-of-staff loop closed."

## Scope

- In:
  - The `one_on_one_brief` method gains Watch-derived sections:
    - PRs waiting on the person (using the People resolver from
      HS-172-04 to match reviewer strings to the relationship).
    - Days since the oldest waiting PR was requested (review latency).
    - Open Jira assignments for the person.
    - Overdue commitments count (already partially present).
  - The brief is transient (the 138 law: never writes to any store).
  - The Watch data is read from the persisted snapshots
    (`_entities()` on project_service.py:505); no new evaluations
    triggered (reads are free; Article V.5).
  - The face for the enriched brief follows the HS-172-01 artboard.
- Out:
  - Reviewer latency derivations as standalone metrics (Phase 173).
  - Watch evaluation triggers from the brief path.
  - Persisting the enriched brief (it is computed at read time).

## Acceptance criteria

- [ ] `one_on_one_brief` returns `watch_summary` with: PRs waiting on
      the person (list), oldest waiting days (int), open Jira
      assignments (list); verified by a unit test with a seeded
      Watch snapshot and a linked People alias.
- [ ] The brief is transient: no writes to any store (the 138 law).
- [ ] Watch data is read from persisted snapshots; no new evaluations
      are triggered (verified by asserting no Watch evaluation calls).
- [ ] When the People resolver finds no match (no alias linked), the
      Watch sections are empty (Article VI: honest at zero).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k brief_enrichment`
  - Enriched brief with matched alias returns Watch data.
  - Enriched brief with no matched alias returns empty Watch sections.
  - No writes to any store during brief computation.
  - No Watch evaluations triggered.
- Integration: n/a (computed at read time from existing snapshots).
- Manual: the owner's People card shows the enriched brief.

## Notes / open questions

- The brief currently takes `db` as an optional parameter
  (people_service.py:364). The Watch data lives in the same db
  (project_service snapshots). The enrichment reads from
  `connector_watches` table snapshots, filtered by the resolved
  person's identity strings.
