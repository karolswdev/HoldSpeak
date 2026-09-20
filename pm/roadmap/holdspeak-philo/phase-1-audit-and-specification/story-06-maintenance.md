# PHILO-1-06 — Registries, validation and repository skills

- **Project:** holdspeak-philo
- **Phase:** 1
- **Status:** done
- **Owner:** Astra

## Goal

Registries, validation and repository skills, with evidence pinned to the research snapshot.

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

Four curated shards and generated references retain source, assertion and
execution evidence separately. Validation rejects invalid source/test symbols,
routes, enums, references and missing egress/authority data. Root ran 64 focused
tests, schema/generation checks and all fourteen skill format checks. Descriptive
MCP and security corrections reduce the existing known-false ratchet to zero
without claiming missing runtime controls were implemented.
