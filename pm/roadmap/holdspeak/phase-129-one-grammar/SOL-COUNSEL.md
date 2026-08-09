# Sol's acceptance counsel — Phase 129 (recorded verbatim for the sitting)

**Reviewer:** Sol (acceptance partner per docs/internal/ORCHESTRATION.md §6)
**Date:** 2026-08-09 (post-merge review of PR #447; the phase closed before
the Sol-counsel section was canonized — this is the retroactive pass)
**Verdict: DO NOT RATIFY** (the closure claim; Sol found no evidence of an
unacknowledged 129-caused regression and called the implementation
"materially better").

## The findings, and their remediation state

| # | Finding | Class | Remediation |
|---|---------|-------|-------------|
| 1 | The backend verdict classified the 98 FAILED but not the 14 ERROR cases (workbench-walk e2e, ERR_CONNECTION_REFUSED :8778); "plausibly environmental, but plausibility is not proof". Backend evidence lacked command/exit-code provenance. | blocker | **FIXED with proof:** all 14 pass with a hub present (`HOLDSPEAK_HUB_URL` set) — captured through `dw evidence capture` with full provenance in evidence-story-11.md (2026-08-09). Classification: environmental, requires a running hub. |
| 2 | The walk's acceptance criterion says both widths for every surface; the harness walked 38 on desktop but only 4 at 393px, and the roadmap/final-summary overstated this. | blocker | **PARTIALLY FIXED, remainder ledgered by owner direction:** harness mobile scope extended 4 → 23 intended checks; desktop + mobile-dock coverage passes the strengthened contract; the mobile Go/object/editor segment is explicitly recorded NOT WALKED (dev-server 500s at the cut; failed-run provenance in evidence) and rides Candidate Z. |
| 3 | The harness treats footer/head as optional (`if (after.foot)`), so footless windows pass footer assertions; resized-small head check tautological; height asserted vs viewport, not the working band. | blocker | **FIXED — and the stricter harness caught three REAL defects:** the fitContent band-cap family (Intelligence 64–868, object pullout 191.3–895.3 vs band [54,848]; fixed at the DeskWindow seam) and the Brief resized-small overflow (fixed + regression test). Per-surface required anatomy, per-form contracts, post-state re-measure all landed. |
| 4 | The 96-failure ledger transfer was "the right regression decision, but not a sufficient holistic-product verdict"; the transfer was a promise without a structural home. | concern | **LEDGERED:** the 96-name list + the Sol conditions (owner, exit condition, no baseline expansion) parked in BACKLOG.md pending the owner's Phase 130 chartering; CI failure-name diffs saved as durable artifacts (assets/hs-129-11/ci-*.txt). |
| 5 | Merging over red CI: "sound as a no-regression exception, unsound as an emerging default" — the 'house practice' sentence is normalization of deviance. | concern | **ACCEPTED:** the durable CI-diff artifacts land with this remediation; the no-baseline-expansion rule is written into the BACKLOG ledger entry. The owner is asked to ratify the exception-not-default rule at the sitting. |
| 6 | The walk proves geometry on one seeded Chromium session, not "one grammar" across product states (fresh-home, hostile content, interaction, second engine, occlusion). | concern | **LEDGERED** for the Phase 130-class walk deepening; named in BACKLOG.md. |
| 7 | The OS-chrome exemption's "attention/system surfaces" wording is an open-ended Article VII.2 escape hatch; ShortcutSheet itself is ratifiable (non-modal in fact). | concern | **FIXED:** the decision-log wording narrowed to Sol's boundary — read-only, non-focus-trapping, immediately dismissible, no creation/edit flow, no concealment of actionable failure. |
| 8 | The commandDeck ArrowDown/Enter repair proves less than its predecessor (dispatch bookkeeping vs target action). No falsification found anywhere. | observation | **LEDGERED:** target-specific object + program cases named in BACKLOG.md. |
| 9 | Token before-count inconsistent across docs (23 vs 27). Deletions and generated-token claims verified true; both radius exceptions ratified. | observation | **FIXED:** documents reconciled ("27 gate findings, 23 of them raw values"). |

## Sol's questions for the owner (verbatim)

1. Do you want "one grammar" to mean **no Phase 129 regressions**, or do you
   intend the holistic mandate to withhold the claim until the inherited
   dictation/history/sync planes are healthy? The current documents move
   between those two meanings.
2. Will you require a supplemental exit proof before ratification:
   classification or successful rerun of the 14 backend errors, anatomy-
   presence assertions, and a truthful mobile scope? *(Delivered by this
   remediation — the question stands as ratification of its sufficiency.)*
3. Do you ratify a narrowly defined read-only OS-chrome exception to
   Article VII.2, or should every full-screen overlay — including
   ShortcutSheet and attention surfaces — be converted into an in-world
   window or drawer?

## The orchestrator's position

Sol's three blockers were correct and are fixed with evidence; the concerns
are fixed where cheap and ledgered where they are Phase 130-class work. The
orchestrator proceeds under §6's rule — naming, not omitting — and puts
both opinions before the owner: Sol's DO-NOT-RATIFY-as-reviewed, and the
orchestrator's remediated-close. **The phase's ratification is the owner's
call at the sitting, with Sol's three questions as the agenda.**
