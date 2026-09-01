# HS-160-02 - The collectors: five adapters, one contract, honest coverage

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-160-01
- **Unblocks:** HS-160-03
- **Owner:** unassigned

## Problem

§7.1: the V0 collector supports adapters for meetings/transcripts,
resources/artifacts/notes, decisions, follow-through, and
watch-backed sources — the last consuming canonical watch
observations/evaluations, NEVER re-issuing provider reads. Each
adapter returns a cursor/version, freshness, normalized
observations, and adapter-local errors; one failure never discards
the others (TST-003, DOM-008).

## Scope

- **In:** `ProjectEvidenceCollector` (composed behind ProjectService
  per §6.1) + a small adapter protocol; the five native adapters
  reading the REAL seams (the desk reads 159's suggestion engine
  already uses + project_sources bindings); normalized observation
  kinds per source (decision lifecycle changes, action-item
  overdue/stale transitions, meeting association, resource/evidence
  arrival, watch evaluation deltas via diff_snapshots' semantic
  events); deterministic pobs_ identity from the P0 generators;
  persistence through 01's repo (retry → no-op); per-source
  freshness_state written to project_sources; coverage summary
  (ok/stale/failed per source — the §5.8 manifest's raw material).
- **Out:** the review algorithm (03), any provider fetch, scheduling.

## Acceptance criteria

- [ ] TST-003: retry dedup (same fact/version → same pobs_ or no-op), stale/failed coverage explicit, partial success (one adapter raises → others' observations persist + that source marked failed).
- [ ] The watch adapter consumes ONLY canonical evaluations/snapshots (a test proves no fetcher is invoked).
- [ ] Every observation carries kind/subject_ref/source_version/observed_at/fact_json/content_hash per §5.5; refs canonical via holdspeak.refs.
- [ ] 157-159 pins untouched-green.

## Test plan

- **Unit:** `tests/unit/test_evidence_collectors.py` (per-adapter truth tables over seeded fixtures, the three TST-003 laws, the no-fetch proof).

## Notes / open questions

- The 159 seeding walls (no create routes for meetings/decisions/door) bite here too — fixtures seed at the DB layer, noted per the standing law.
