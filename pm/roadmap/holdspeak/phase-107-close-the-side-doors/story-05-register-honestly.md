# HS-107-05 - The register, honestly — what remains and why

- **Project:** holdspeak
- **Phase:** 107
- **Status:** planned
- **Depends on:** HS-107-02, HS-107-03, HS-107-04
- **Unblocks:** HS-107-06
- **Owner:** unassigned

## The thesis (the bar)

By this point three stories have moved sites out of the register.
This one makes sure the register still tells the truth about what is
left — because a shrinking number is exactly the kind of thing that
starts getting reported instead of examined.

The register is not a progress bar. It is **the enumerated debt of a
constitutional clause**, and Article XI clause 6 says no agent
principal may reach a path it names. That rule is only meaningful if
the register is accurate in both directions: nothing listed that is
actually covered, and nothing covered that is actually still reachable.

The bar: after this story, every remaining entry has a reason, a
closing condition, and an honest status — and the numbers in the docs
match the file.

## Problem

Three failure modes, all easy and all quiet:

1. **Inflation.** A site marked covered whose raw call still compiles
   and is still reachable. The count improves; nothing changed.
2. **Silent exemption.** A site re-classified as exempt without an
   argued reason, so a future reader cannot tell whether it was
   examined or waved through.
3. **Drift.** The docs, the charter, and the file disagreeing about
   how many are left — which is how "36 declared debt" becomes folklore.

## Recipe

1. **Re-derive the count from the file**, not from the story reports.
   Whatever the three migration stories claimed, the register plus the
   fence test are the truth.
2. **Audit every "covered" claim**: routed through the kernel AND the
   direct path removed or fenced. A site that is merely *usually*
   routed is not covered — it is mixed, and mixed is a status the
   register already has.
3. **Every remaining entry gets a closing condition** — what would
   have to be true for it to leave. For the ten raw-desktop primitives
   in `typer.py`, that condition is RFC §5b confinement; name it
   explicitly so the next phase inherits a work list rather than a
   mystery.
4. **Re-classified sites carry their argument.** Each exempt entry
   states why in one line — model invocation returning to the caller,
   latency-sensitive capture, a read. Enough that the judgement can be
   challenged later without re-deriving it.
5. **Clause 6's status, stated plainly.** The clause survives this
   phase. Say so, say what remains, and say what would repeal it. A
   transitional clause that quietly becomes permanent is exactly what
   the sunset was written to prevent.
6. **Reconcile every number** that appears anywhere: the register
   file, the fence test's asserted counts, the phase charter, and the
   docs. One number, four places, no disagreement.

## Out of scope

- Migrating anything further.
- Weakening the fence to make a count work.
- §5b confinement itself.

## Acceptance

- The register's counts are re-derived from the file and match the
  fence test's assertions exactly.
- Every "covered" claim audited against the reachability test; any
  that fails is demoted to `mixed` with a note — **demotions are a
  success of this story, not a failure of the previous ones.**
- Every remaining entry has a reason and a closing condition.
- Every re-classified entry carries its one-line argument.
- Clause 6's continued force is stated, with what would repeal it.
- The charter's own numbers are corrected where the triage stories
  proved them wrong (the charter's "11 migratable egress sites" is
  known to be wrong before this phase starts — HS-107-04's triage will
  produce the real figure).
- No number anywhere in the repo disagrees with the file.

## Test plan

- **Census:** register ↔ fence assertion agreement; reachability check
  per covered claim.
- **Docs guard:** the counts in `SECURITY.md`, `ARCHITECTURE_*`, the
  charter, and the register all match.
- **Unit:** a demoted site fails the covered assertion by name.

## Chef's notes

- Expect the number to be less impressive than the migration stories
  implied. That is the story working. The whole reason this exists as
  its own story is that the people who moved the sites are the worst
  people to audit whether they moved.
- If nothing gets demoted, be suspicious of the audit rather than
  pleased with the result.
- The closing conditions are the real deliverable for the next phase.
  "Blocked on §5b" beside ten entries is a charter someone can act on.
