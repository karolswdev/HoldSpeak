# HS-160-02 — The domain grammar: identity, scope, time, claims

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-160-01
- **Unblocks:** HS-160-03, HS-160-04, HS-160-05, HS-160-06, HS-160-09, HS-160-10
- **Owner:** unassigned

## Problem

Continuity cannot be safe if each feature invents its own identity, scope,
temporal, confidence, and claim encoding. The existing qualified-ref authority
is a useful seam, but CF-0 needs a complete canonical grammar and additive
storage contract before command or retrieval behavior can be deterministic.

## Scope

- **In:** amend the central qualified-ref registry for all CF-0 citizens;
  canonical JSON and digest rules; decimal/confidence representation, with
  confidence diagnostic/proposal-only and never part of identity, truth, or
  precedence; composite
  scope grammar and precedence hooks; bounded/unknown temporal intervals;
  claim, version, proposal, evidence-span, lineage, decision, operation, and
  command-ledger schemas; validators and additive migrations; a requirement →
  schema/constraint traceability table.
- **Out:** accepting proposals, collecting source prose, encryption mechanics,
  vector generation, graph traversal, ranking, and UI.

## Acceptance criteria

- [ ] Every identifier and qualified ref has one parse/format law; registered
  citizens round-trip; aliases format canonically; unknown citizens remain
  inspectable but cannot be mutated without registration.
- [ ] Canonical JSON defines Unicode normalization, key order, decimal form,
  absent/null distinction, array order, and digest algorithm with golden bytes.
- [ ] Claim identity separates semantic key, scope, time, subject, predicate,
  qualifiers, and version; source identity is not mistaken for claim identity.
- [ ] Accepted-memory scope validators cover stable owner plus optional Project,
  Recipe, and Workbench forms and their ratified composites; precedence is
  referenced from the owner ledger. Person/People, speaker, Thread, and
  device/private are rejected as accepted-memory scopes; Thread is represented
  only as a plan `working_scope`.
- [ ] Temporal and evidence-span constraints reject invalid intervals, offsets,
  fabricated targets, bad UTF-8 boundaries, and impossible source revisions.
- [ ] Clean/upgraded/down-disabled database tests prove additive, reversible
  deployment without dropping relationship-memory or existing consumer data.

## Test plan

- **Unit/property:** refs, canonical bytes/digests, Unicode/NFC, decimals,
  qualifier permutations, ratified composite scopes, rejected person/speaker/
  Thread/device scopes, Thread working-scope separation, and DST/unknown
  interval boundaries.
- **Migration:** empty DB plus representative pre-CF-0 DB; foreign-key and
  constraint probes; downgrade-by-disable (not destructive down migration).
- **Regression:** existing ref and relationship-aware memory suites unchanged.

## Notes / open questions

- CF-0 §4–6 and INV-001–007 are the primary contract anchors.
- No plaintext source prose belongs in the observation/journal schema; that
  boundary is enforced with HS-160-04/05.
