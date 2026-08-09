# HS-130-10 — The inherited ledger: triage and assign the 96

- **Project:** holdspeak
- **Phase:** 130
- **Status:** done
- **Depends on:** HS-130-03, HS-130-04, HS-130-05, HS-130-06, HS-130-07, HS-130-08
- **Unblocks:** HS-130-11
- **Owner:** unassigned

## The thesis (the bar)

Phase 129's first full backend run found 98 failures; triage on pre-129 main
reproduced 96 as inherited Phase 118–128 integration debt (companion
slack/github/webhook, intel streaming, dictation surfaces, history slack,
decision records, live bus, workbench-walk e2e, sync/guards). The 129 handoff
transferred that ledger to **this** phase as a dedicated repair story
(evidence-story-11 in phase-129 carries the reproduction logs). Sol's cut puts
the **sync registry and deployment revisions in Phase 131** — so the
sync-contract failures cannot be *fixed* here, but they must be **triaged and
assigned a single home** so 130 and 131 do not double-count them. Silence about
a red suite is the one unforgivable sin (ORCHESTRATION §The ledger).

### What changes

1. Re-run the full backend suite on current main; diff the failure **names**
   against the 129-recorded 96 (same-env baseline discipline). Classify each:
   **repaired-by-130** (a defect this phase's stories touch — deployment/egress/
   settings/decision-rename adjacent), **131-owned** (needs the sync registry or
   deployment revisions — e.g. `test_schemas_cover_exactly_sync_kinds`,
   `test_web_routes_sync.py` pull/push, the workbench sync bucket gap),
   **still-inherited** (unrelated integration debt — re-ledger with a named
   future home), or **newly-caused** (this phase's regressions — fix before the
   walk).
2. Repair the failures that fall to 130's own scope (the decision-rename kind
   drift, any egress/deployment assertion the stories move, settings tests).
3. Assign every remaining failure exactly one home in a written ledger table
   (test name → class → owner phase), checked into evidence. No test appears
   under two owners.
4. Reconcile with Backlog Candidate Z (BACKLOG.md:242-258) so the owner's
   pending 129-sitting ruling has one coherent picture.

## Acceptance criteria

1. A ledger table maps every one of the ~96 to exactly one of {repaired-by-130,
   131-owned, still-inherited, newly-caused}; no test double-homed.
2. Every newly-caused failure (a 130 regression) is fixed before HS-130-11.
3. The repaired-by-130 set is green; the 131-owned set is named for the 131
   charter; the still-inherited set is re-ledgered with a future home.
4. The classification is reproduced from a same-env run on current main, logs
   in evidence.

## Test plan

- Full backend suite on current main captured via `dw evidence capture`; the
  diff and classification recorded; the repaired subset re-run green.
- No focused-only claim: this story reads the FULL suite output from file.

## Out of scope

- Fixing the 131-owned sync-contract failures (Phase 131).
- Fixing unrelated still-inherited integration debt (re-ledgered, not repaired
  here).
