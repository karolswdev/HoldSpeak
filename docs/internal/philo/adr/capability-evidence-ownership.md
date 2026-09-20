# Proposed ADR: keep capability evidence beside existing registries

**Status: PROPOSED.** This document recommends the maintenance policy. It does
not change runtime authority or establish that every capability is verified.

## Context and current reality

The code already has route, MCP, primitive, command, drop, plugin and inference
registries. Philo adds a cross-domain capability view with implementation,
assertion, documentation, platform and boundary references. Replacing the
runtime registries would create another owner for executable behavior.

## Problem

A flat feature list cannot distinguish a route that exists from a job that a
person completed. A path-only validator can become a misleading proof badge.
The source briefs ask for capability status and continuous drift detection.

## Options

1. Generate every capability from code names. Cheap, but loses user purpose,
   authority semantics and proof quality.
2. Make a new master registry drive all runtime systems. High migration cost
   and risk; not justified by a documentation audit.
3. Add curated evidence shards and derive reference views while retaining the
   current runtime owners. This is the recommendation.

## Recommendation

Keep `docs/internal/philo/data` as curated research input. Stable IDs name user
or developer capabilities, not a route count. Each row carries status rationale,
source, inspected assertion, test execution, release and owner-observation facts
separately. The six generated registries are projections. Update domain owners
first; then update evidence and regenerate. A changed source anchor or missing
route must fail the relevant drift check.

The existing `tests/unit/doc_claims/registry.py` remains the predicate-based
owner for load-bearing prose claims. Path validation complements those tests;
it cannot replace them. Semantic coverage gaps remain visible in the coverage
report. Do not label a capability Stable solely because its fields are filled.

## Migration impact and compatibility

No product database, API or UI migration. Contributor workflow gains metadata
validation and generated-output checks. Historical research snapshots remain
pinned; a new product snapshot requires deliberate review and new evidence.
If metadata volume becomes burdensome, reduce duplicated projections before
adding another framework.

## Security impact

Evidence contains paths, symbols and synthetic examples. It must not contain
owner transcripts, provider credentials or live records. Egress and authority
fields are declared claims requiring source review, not grants to execute.

## Rejected alternatives

A code-name encyclopedia cannot answer a user's job. A master runtime registry
would redesign HoldSpeak while documenting it. Neither is necessary for this PR.

## Acceptance

An invalid ID, enum, missing path/test, undeclared external boundary, or stale
projection fails a focused test. A nonempty source path alone never makes an
unexecuted assertion count as a passing test. The final report names scope gaps
and the exact product revision the evidence describes.
