# Preserved invariants

**Shared reference for the current [ordered plan](EXECUTION_INDEX.md). Detailed planning is authorized; this document grants no repository execution or shipping permission.**
These are acceptance constraints wherever their stated scope applies, including refactors. Each task names the rows needed for its bounded onboarding; that reading list does not waive another applicable safety, authority or preservation constraint. A change that violates an applicable invariant is incomplete even if local tests pass. Evidence and exact source anchors are in [Evidence](EVIDENCE.md).

| ID | Invariant | Where it matters |
| --- | --- | --- |
| I01 | The hub owns durable domain state; frontend cache owns read coordination, not a competing canonical model | E01, E04, HS-S11 |
| I02 | Use the existing `deskQueryClient`, typed API boundary and RuntimeBus; no new general cache, websocket or feature fetch layer | E01 |
| I03 | Only matching Program events invalidate a keyed detail read; a broad Program event may refresh the active Program, unrelated entities must not | E01 |
| I04 | Acknowledged mutation results can update the matching resource; an older in-flight read must not undo that acknowledgment or overwrite another resource | E01 |
| I05 | Detaching an observer does not cancel execution. Cancel is an explicit request; terminal/persisted completion is a separate fact | E02 |
| I06 | Ask/Calls admission, Thread persistence, emitted event meaning, spoken approval and Calls answer-later behavior survive the handle refactor | E02 |
| I07 | Automatic HTTP tool-loop work and interactive Thread turns keep distinct lifecycles; sharing a policy helper is not permission to merge them | E02, E03 |
| I08 | CLI source-policy identity is durable/authenticated; HTTP identity comes from trusted run context. Client JSON or model arguments never create authority | E03 |
| I09 | Project scope, private 1:1 descendant exclusions and explicit owner-filed exceptions remain exactly as implemented; owner confirmation still controls final send | E03 |
| I10 | Channel sends retain frozen payload/target/provenance, durable dispatch claims and unknown-outcome recovery. Unknown external outcome is not safe-to-retry | E02, E03 |
| I11 | Optional checkpoint pin failure is nonblocking. The original checkpoint and handoff history remain truthful; there is no automatic pin retry or silent replacement | E04 |
| I12 | A stored checkpoint ref proves a stored pin reference, not perpetual Git availability. Actual Start from here failures remain visible and do not show false success | E04 |
| I13 | Extracted/source decision text and currently accepted canonical decision state remain distinct; no table unification or lifecycle fallback is introduced | E03, R01 |
| I14 | Memory enrichment can be eventual, but live admission and content-hash validation before inclusion remain immediate; an incomplete full-sweep kind must not infer deletion from its unprocessed remainder. Completed kinds and explicitly checked targeted refs may already reconcile derived state | all, R02 |
| I15 | Memory Pages retain sentence-level stale/withheld semantics and commit-time source/scope/prior-page validation; generic writes to thought-owned notes stay rejected | all |
| I16 | Tests use isolated state, no owner HOME/DB/Keychain, no live provider/device effects by implication; machine-wide lock is never bypassed or nested | all |
| I17 | New UI uses the shared surface, plain named failures and real accessible controls. Loading resolves to data or failure; inputs/receipts survive failed operations | E01, E04, HS-S11 |
| I18 | Documentation distinguishes target requirements from implemented behavior. No test, deployment or runtime claim without evidence | all |

## Current cross-cutting constraints

| ID | Invariant | Relevant current work |
| --- | --- | --- |
| I19 | A local classifier does not replace authenticated writer/admission checks, owner-only lower-bar handling, revisions or conflict handling | HS-S23 and other Program contracts |
| I20 | Program `within` is the documented night-planning scope, not a filesystem sandbox; manual planning, direct update and post-change diff enforcement remain distinct | HS-S23 |
| I21 | Preserve a domain's known effect/request identity and uncertainty; reconciliation is not permission to create a fresh effect or silently retry | HS-E30, HS-S11, HS-S42 |
| I22 | Historical evidence and current eligibility are different; unavailable observation is not fabricated revocation, and a present field is not enforcement proof | HS-E20 |
| I23 | Canonical membership, source provenance, ordinary obligations and encrypted People identity/obligations remain distinct even when shown together | HS-E40 |
| I24 | Preserve exact checkpoint starts, same-worktree continuation and the owner's checkout; no hidden rebind/reset/fetch policy is inferred from navigation or readiness | HS-S22, HS-S35 |
| I25 | Scope/target navigation does not save or accept work; preserve newer drafts and separate Save, Confirm and Send authority | HS-E10 |

## Non-goals of the retained four-seam draft only

These exclusions constrained the earlier seam proposal. They do not preempt the user's broader structural audit or prevent a different target from being proposed after evidence and supervision. No implementation or cleanup is authorized now.

Within that earlier proposed scope: no broad frontend migration, new state-management framework, universal asynchronous-job interface, new authorization engine, auth caching, channel provenance-constructor refactor, generic recovery/retry framework, decision schema merge, memory worker/index consolidation, live device validation, repository-wide cleanup or changes to shipped control levels. Discovery findings require a new scoped implementation brief, not opportunistic edits.

For HS-S42, acknowledged canonical/source IDs and current membership are distinct from historical receipts. Canonical project correction must not redirect source KB/drawer axes or rewrite meeting/provenance. Best-effort workspace receipt persistence is not a cross-device or crash-proof guarantee.
