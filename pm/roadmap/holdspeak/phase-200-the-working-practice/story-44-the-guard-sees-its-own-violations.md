# HS-200-44: Make the release guards see what they claim to guard

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-03
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** the 2026-09-13 operational-surface audit §10.4 (`docs/internal/OPERATIONAL-SURFACE-AUDIT.md`)

## Problem

**The guard that underwrites the owner's own face ruling sees about 5% of its
violations.**

`scripts/ux_canon_scan.py:431` matches `r'<button[\s>/]'` against lines produced
by `content.splitlines()` — which strips the newline. Prettier puts `<button`
alone at the end of a line, so the character the regex requires after the tag is
not there. The scanner reports **A1: 4**; an independent count finds **187** raw
`<button>` elements in the same scope. Verified by the orchestrator by running
the scanner and counting separately.

`docs/internal/UX-CANON.md:131-132` presents "4 residues with reasons" as a fact
about the code. **It is an artifact of the regex.** The owner's ruling — every
verb is the library Button, a raw `<button>` is a species bug — has been
guarded by a scanner that could not see the violations.

This is the `reference_lying_test_doubles` family one level up: not a double that
lies about a field, but a guard whose matcher cannot express the thing it
certifies. HS-200-03 turned three absolute fences into dated down-only ratchets;
a ratchet counting the wrong number ratchets nothing.

## Scope

Make the canon scanner's matchers see multi-line JSX, restate the true counts as
the honest starting ceiling, and audit the scanner's other rules for the same
class of blindness.

Implementation seams: `scripts/ux_canon_scan.py`; the ratchet ceilings; the census
assets the scanner writes; `docs/internal/UX-CANON.md`'s stated residue count.

Out: fixing the 187 raw buttons. That is face work, it is large, and it belongs
to whichever face story touches each file. This story makes the debt VISIBLE and
sets the ratchet so it can only shrink.

## Acceptance criteria

- [x] The A1 matcher sees a multi-line `<button` opening, and the scanner's count
      matches an independent count over the same scope.
- [x] **Every other rule in the scanner is checked for the same line-shape
      assumption**, and the ones that share it are fixed or named as not
      applicable, with the reason recorded.
- [x] The ceilings are reset to the true counts, dated, down-only — no rule is
      quietly relaxed to make a number pass.
- [x] `UX-CANON.md`'s residue claim is corrected to the measured truth.
- [x] A fence test proves the scanner catches a multi-line raw button, and FAILS
      against the pre-fix scanner.
- [x] The scanner stops writing census assets into the repo as a side effect of
      running, or the write is made explicit — a guard that dirties the tree on
      every run is how other phases' evidence gets rewritten by accident
      (see `reference_suite_dirties_evidence_assets`).

## Test plan

Planned suite: `phase200_canon_guard`. Feed the scanner a fixture containing both
line shapes; assert both are caught. Re-run over `web/src` and diff against an
independent count.

## Notes / open questions

The 187 are debt, not regression: they accumulated while the guard was blind.
Expect the ratchet's opening number to be large and honest.
