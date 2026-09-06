# HS-190-14 — The CF-0 close: fault campaigns, rollback, verdict

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-190-01 through HS-190-13
- **Unblocks:** CF-1 charter
- **Owner:** unassigned

## Problem

Individual green stories do not prove that CF-0 composes safely. The phase must
be attacked as one system—migration, concurrency, privacy, source capture,
derivatives, shadow consumers, product fixtures, disable/rollback—and must leave
an honest indexed record from which CF-1 can begin.

## Scope

- **In:** execute CF-0 §18 gates and mandatory structural/fault fixtures;
  upgraded-database rehearsal; post-migration doctor; full canary/leakage scan;
  cross-component crash campaigns; disable and old-code compatibility drill;
  complete requirement/story/evidence index; focused and broad regression;
  council severity review and owner close verdict; only after every gate passes,
  write evidence-story-14 and `final-summary.md`. A defect discovered here
  reopens its owning story before close or creates a numbered HS-160 corrective
  story/PR when ownership crosses stories; HS-190-14 does not absorb product
  fixes into its evidence/report PR.
- **Out:** fixing deferred CF-1 quality work inside the close, destructive schema
  downgrade, releasing the Memory app, enabling shadow plans, or claiming
  embedding/recall performance.

## Acceptance criteria

- [ ] Every current-phase exit checkbox maps to immutable evidence from its
  shipping story; every CF0 requirement has test, inspection, demonstration,
  receipt, benchmark, amendment, or explicit not-applicable proof.
- [ ] All CF-0 §18.1 crypto, representation, claim, poisoning/egress,
  derivative, publication, and product fixtures pass on declared environments.
- [ ] Clean and representative upgraded DBs pass foreign-key/constraint,
  encrypted-inventory, source-journal, generation-lineage, and proof-ledger
  doctor checks before and after restart.
- [ ] Current-binary flags-off differential proves behavioral compatibility
  through the v2 resolver and existing relationship-aware path. After capture
  and encrypted writers stop, an old-binary fixture proves canonical read/open
  in degraded posture with additive dormant tables, while every model-bearing
  operation, Continuity adoption, and plaintext write is fenced. Neither path
  requires data loss, plaintext-writer reactivation, or destructive down migration.
- [ ] Existing relationship-aware memory focused tests plus named Ask, Thread,
  Recipe, Workflow, Workbench, Coder, HTTP, MCP, desktop, and web contracts have
  zero branch-new regression.
- [ ] Council reports zero open severity-1/2 authority, privacy, corruption,
  deletion, or cross-scope defects; lower waivers name owner, expiry,
  requirements, degraded behavior, and verification date.
- [ ] Every discovered defect links either to a reopened owning story/PR or a
  numbered corrective story/PR that is done before close; the close diff is
  limited to campaign/evidence/report machinery.
- [ ] Final summary says precisely what CF-0 does and does not ship, names all
  deferred CF-1 choices, and links the owner/council verdicts and rollback run.

## Test plan

- **Campaign:** run every fixture named in CF-0 §18.1 with reproducible commands,
  environment record, artifact digests, and sanitized results.
- **Migration/rollback:** clean, representative legacy, interrupted upgrade,
  restart, current-binary flags-off via v2, old-binary canonical-only reopen
  after writer stop with inference/adoption/plaintext writes blocked, and
  backup restore rehearsal.
- **Regression:** focused Continuity and relationship suites, relevant broad
  backend/web/desktop suites, static census/fence checks.
- **Review:** independent systems, AI-memory, and product council read the final
  evidence index; owner issues the phase verdict.

## Notes / open questions

- CF-1 may be chartered only after this story is done. Planning CF-1 is not a
  substitute for closing CF-0.
- Evidence and final summary are intentionally absent today; creating them in
  this planning PR would falsely imply execution.
