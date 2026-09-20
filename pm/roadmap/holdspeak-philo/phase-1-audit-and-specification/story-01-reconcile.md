# PHILO-1-01 — Reconcile the request and sources

- **Project:** holdspeak-philo
- **Phase:** 1
- **Status:** done
- **Owner:** Astra

## Goal

Reconcile the request and sources, with evidence pinned to the research snapshot.

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

The preserved briefs map to artifact owners in source-checklist.md. Source authority
and executable behavior are separate in SOURCE_HIERARCHY.md. The introductory
guides explain four user jobs and preserve first-use limits. Navigation passed
through the captured command in evidence-story-01.md. The umbrella PR bundles
seven individually gated documentation stories by explicit owner request.
