# HS-160-01 — The owner canon: amendments and decision ledger

- **Project:** holdspeak
- **Phase:** 160
- **Status:** blocked
- **Depends on:** —
- **Unblocks:** HS-160-02, HS-160-04, HS-160-05, HS-160-06, HS-160-08, HS-160-10, HS-160-11
- **Owner:** HoldSpeak owner

## Problem

CF-0 contains choices that code cannot legitimately make: what is retained,
what the Memory application is, which device is authoritative, where consent
appears, what scope precedence means, and what model/license posture is
acceptable. Treating council recommendations as owner decisions would make the
implementation precise but unauthorized.

## Scope

- **In:** create the versioned owner-amendment and decision ledger named by
  CF-0 §14.5; present every row as a separate approve/amend/reject verdict;
  record rationale, effective version, affected requirements, and replacement
  law; reconcile the result into both SRS documents and Constitution when
  needed; record non-decisions explicitly.
- **Out:** schema, runtime code, migrations, model selection, UI production
  work, and umbrella approval of the entire SRS.

## Acceptance criteria

- [ ] Every §14.5 decision has an explicit owner verdict covering positioning;
  Dock/program/shortcut; vocabulary; launch destination; first-run placement;
  phone authority; procedure adapters; caps; scope precedence; invalidation;
  retention/Forget; model/license posture; proof retention/export;
  accessibility matrix; reference hardware/corpus; and resume synthesis.
- [ ] Model/evaluation decisions are separated by release train: CF-0 ratifies
  license-admission law, structural fixture environments, and sanitized-corpus
  policy; CF-1 later selects actual models/backends, performance hardware,
  evaluation corpus, thresholds, and licenses admitted under that law.
- [ ] Each verdict records `decision_id`, status, exact chosen law, rationale,
  effective date/version, superseded law, and affected requirement IDs.
- [ ] Amendments update the parent and child SRS in the same PR; conflicting
  statements fail a decision-consistency check.
- [ ] Constitutional changes, if any, are explicit amendments—not comments or
  council inference—and unresolved conflicts keep this story blocked.
- [ ] The ledger distinguishes decisions required for CF-0 execution from
  concrete model/vector/quality choices deliberately deferred to CF-1, so a
  structural fixture verdict cannot be read as model selection.
- [ ] Downstream stories replace `TBD` assumptions with ledger references.

## Test plan

- **Static:** decision-ID uniqueness; complete §14.5 row coverage; valid SRS
  anchors; no unresolved placeholder consumed by a downstream story.
- **Review:** owner signs each row; systems/product/AI council checks internal
  consistency but cannot substitute its vote for the owner's.
- **Negative:** omission, umbrella approval, or contradictory retention/scope
  verdict fails the gate.

## Notes / open questions

- This story is `blocked` because the necessary act is owner ratification. The
  story itself is the exact instrument needed to unblock it.
- Candidate output: `docs/internal/CONTINUITY_OWNER_AMENDMENTS.md`; the final
  path may follow repository convention, but its stable decision IDs may not.
