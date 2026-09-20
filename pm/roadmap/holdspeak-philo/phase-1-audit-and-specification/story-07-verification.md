# PHILO-1-07 — Integrated audit and final verification

- **Project:** holdspeak-philo
- **Phase:** 1
- **Status:** done
- **Owner:** Astra

## Goal

Integrated audit and final verification, with evidence pinned to the research snapshot.

## Scope

Documentation, research fixtures and documentation tools only. Product changes remain proposals.
The source briefs and source checklist define the required subject coverage.

## Acceptance criteria

- [x] Requested subjects in this lane have source-backed output or an explicit verification limit.
- [x] Current implementation and proposed requirements are distinct.
- [x] Source paths and inspected test assertions are recorded.
- [x] Relevant validation passes or each failure is classified with evidence.
- [x] Astra verifies the delivered artifacts and records the result.

## Test plan

Run the existing documentation navigation checker over this lane's Markdown.
Tooling receives focused positive/negative tests. Full suites run only in the quiet final lane.
Every pytest invocation uses isolated HOME. Never run tests/e2e/test_metal.py.

## Notes

Owner override for Philo: Astra owns the final deliverable; Luna xhigh workers only;
no Muad'Dib dependency. One umbrella PR, individually gated story commits.
Workers do not stage, commit, capture evidence, flip stories or create contracts.

## Astra verification

Astra integrated all lanes, checked source assertions, ran the full Python and
web suites, fixed five documentation failures, reran the ten intermittent runtime
failures, inspected visual evidence and classified four baseline failures.
The final report preserves unresolved interference, hardware, owner-use and
release limits. Main still points to the audited source commit at final fetch.
The independent Luna check and baseline investigation ship with this story.
The owner explicitly waived the Muad'Dib dependency for this initiative.

## CI portability correction

The first Linux documentation job found API-reference drift caused by unsorted
filesystem enumeration of candidate test paths. Sort before serialization; a
regression test reverses enumeration and requires identical output. The full
documentation job is checked locally on Python 3.12 as well as the authoring
runtime. This is a follow-up atomic correction under the same completed story.

The clean-run source check also exposed one Qlippy reference to a build copy.
Corrected it to tracked source and added a validator regression for build and
environment artifacts. Source inspection narrowed Qlippy rendering/interaction
claims and clarified hub transport for its bundled assets.
