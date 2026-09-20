# PHILO-1-02 — Kernel, authority, storage and operations

- **Project:** holdspeak-philo
- **Phase:** 1
- **Status:** in-progress
- **Owner:** Astra

## Goal

Kernel, authority, storage and operations, with evidence pinned to the research snapshot.

## Scope

Documentation, research fixtures and documentation tools only. Product changes remain proposals.
The source briefs and source checklist define the required subject coverage.

## Acceptance criteria

- [ ] Requested subjects in this lane have source-backed output or an explicit verification limit.
- [ ] Current implementation and proposed requirements are distinct.
- [ ] Source paths and inspected test assertions are recorded.
- [ ] Relevant validation passes or each failure is classified with evidence.
- [ ] Astra verifies the delivered artifacts and records the result.

## Test plan

Run the existing documentation navigation checker over this lane's Markdown.
Tooling receives focused positive/negative tests. Full suites run only in the quiet final lane.
Every pytest invocation uses isolated HOME. Never run tests/e2e/test_metal.py.

## Notes

Owner override for Philo: Astra owns the final deliverable; Luna xhigh workers only;
no Muad'Dib dependency. One umbrella PR, individually gated story commits.
Workers do not stage, commit, capture evidence, flip stories or create contracts.
