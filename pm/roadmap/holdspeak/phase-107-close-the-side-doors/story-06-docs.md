# HS-107-06 - Docs — the new number at the entry points

- **Project:** holdspeak
- **Phase:** 107
- **Status:** planned
- **Depends on:** HS-107-05
- **Unblocks:** HS-107-07
- **Owner:** unassigned

## The thesis (the bar)

Phase 106's docs told the truth about a kernel that covered almost
nothing: *"an audit and consent boundary for cooperating code... not a
sandbox"*, with 36 sites named as declared debt. That sentence was
correct then and it is **still correct now** — because the raw
primitives are still reachable and §5b confinement has not landed.

The bar: the numbers change, the narrowing does not. This story
updates the count and resists the temptation to upgrade the claim
alongside it.

## Problem

A phase that closes twenty-something doors creates real pressure to
say something stronger about safety. The strength of the claim is
governed by the *weakest* remaining path, not by the number of closed
ones — and the weakest path is unchanged: any in-process Python can
still call `typer.py` directly.

## Recipe

1. **Update every count** to HS-107-05's audited figure — the register
   file, `docs/SECURITY.md`, the architecture doc, and anywhere else a
   number appears. One number, everywhere.
2. **Keep the narrowing exactly where it is** (`docs/SECURITY.md:11`,
   before any prevention claim) and **do not strengthen it**. Add one
   sentence naming what *did* change: these families now admit and
   receipt; the primitives remain reachable; confinement is still the
   threshold.
3. **The register gets documented as shrinking, with its remainder** —
   what is left, why, and that clause 6 remains in force with its
   sunset unmet.
4. **`USER_GUIDE`** — only if the owner's experience changed. If
   dictation, wake, or Cadence now behave differently in any visible
   way, say so plainly; if they don't, say nothing. **No user-facing
   page gains kernel vocabulary.**
5. **Truth-audit every claim** against the shipped tree, HS-104-06
   method: a claim-by-claim table in the evidence with the file and
   line making each true. A claim that outran the implementation gets
   fixed here, in either direction.

## Out of scope

- Strengthening the security claim.
- New capability.
- Rewriting Phase 106's architecture material beyond the counts and
  the one sentence.

## Acceptance

- Every count in the repo matches HS-107-05's audited figure; a guard
  or test pins the agreement so they cannot drift apart again.
- The cooperating-code narrowing is **unchanged in strength** and
  still appears before any prevention claim.
- The remainder and clause 6's continued force are documented with the
  sunset condition.
- Claim-by-claim audit recorded, each claim citing file and line.
- Doc voice and vocabulary guards green; no kernel vocabulary on user
  pages.

## Test plan

- **Guards:** doc voice/vocabulary, link check, count agreement.
- **Audit (evidence):** the claim table.
- **Full suite** per the phase's rails.

## Chef's notes

- The one sentence to get right: what changed is *coverage*, not
  *containment*. Those are different words and only one of them is
  earned.
- If a reviewer reads the updated security page and comes away more
  relaxed than before, the story failed — the risk profile against
  untrusted code is identical.
