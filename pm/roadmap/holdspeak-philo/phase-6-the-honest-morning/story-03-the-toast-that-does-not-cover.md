# PHILO-6-03 - The toast that does not cover

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** in-progress
- **Depends on:** - (the placement build depends on its canvas ratification)
- **Unblocks:** exit 3 (no zero token, no overlap at 393)
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", ledger row 4; Astra's check of the drafts, finding 2 row 3
- **Canvas:** the zero tokens none; the PLACEMENT a SMALL CANVAS at 1440 and 393, ratified by the owner before build

## Problem

After a summary the Arrival shows a transient toast `MEETING READY · N open · 0 decided`.

- **Zero token.** `AmbientLayer.tsx:175` renders `{signal.openTotal} open · {signal.decidedTotal} decided` with no guard. A count of zero breaks UX-CANON A.8. The numeric facts are correct and stay: `intelligenceAttention.ts:95-96` stores `openTotal` and `decidedTotal`.
- **Overlap.** The toast is fixed with a hard-coded bottom offset (`web/src/components/AmbientLayer.tsx:170`, `bottom: "104px"`). At 393 it covers the summary text and the capture bar (`../phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/summary/393-after.png`). The proposed patch inserts an empty `data-aftercare-slot` div at `web/src/desk/chair/ChairHome.tsx:1442`, immediately before `<CaptureBar />`. It does not change the existing capture-clearance measurement. The build needs the slot, an `AmbientLayer` portal and auto-scroll; the patch alone places no card.

## Scope

- **In:** omit zero tokens at render (canvas-free); the placement drawn on a small canvas at both widths with the unobstructed position, ratified before build; the build of what was ratified; the rendered transition proof; the rig case at 1440 and 393.
- **Out:** new toast words, a new toast kind, a dismiss verb; any change of the numeric facts in `intelligenceAttention.ts`; everything the phase status lists as out.

## Acceptance criteria

- [x] Zero tokens are omitted at render: `0 decided` and `0 open` never render; numeric facts in `intelligenceAttention.ts` are unchanged. Real `publishAftercare` producer tests cover all four count pairs. Archive red: `docs/internal/philo/phase-6/toast/zero/red-origin-behavior.txt` (3 failed, 6 passed); parent DW green: `toast/zero/dw-validation.md` (13 passed).
- [ ] The placement canvas: the toast at 1440 and 393 over a real summary and the capture bar, from the real library species, with the unobstructed position; RATIFIED by the owner BEFORE the placement build.
- [ ] The built placement is the ratified one. At 393 the toast covers neither the summary text nor the capture bar (a geometry fence on the rendered transition: the toast's box does not intersect the capture bar or the summary's readable text). Red pre-fix.
- [x] Lane law: the proposed slot goes to lane 01/02 as `docs/internal/philo/phase-6/toast/chairhome.patch`, with separate rationale. `toast/canvas-dw-validation.md` proves `git apply --check` and an empty ChairHome diff. Proposal only; lane A applies it after owner ratification.
- [ ] Rendered transition proof: the toast appears after a summary, with its words, and leaves, at both widths.
- [ ] Rig: the Phase 5 rehearsal summary step (`scripts/philo5_his_words.py`) at 1440 and 393; the `summary/393-after` shot shows the toast clear of the text and the capture bar, no zero token.

## Effort (council-style estimate, not a promise)

0.5 day for the zero tokens; 0.5–1 day for the placement incl. the canvas

## Test plan

- **Unit:** vitest on `AmbientLayer` (no zero token; red pre-fix); a rendered geometry fence at 393 (Playwright or the glass tests with `HOLDSPEAK_EVIDENCE_WRITE=1`).
- **Integration:** the rehearsal summary step at 1440 and 393, `--out` under this phase's assets.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- Round two — the canvas also covers a Meetings window and the Floor at 1440 and 393. Recommended off Arrival: a top-of-current-surface flow slot, with no assumption that every surface has a CaptureBar. `AppShell.tsx:24` mounts AmbientLayer on every surface, so the future portal must follow the current surface. Ask 2 states that phone auto-scroll moves the owner’s reading position and scrolls the Arrival head off. Owner ratification remains pending.
- Round two — omit `Open proposals` at 0/0 as an authorized render-only correction (UX-CANON A.11, Tenet 3); retain Dismiss and unchanged numeric facts. Focused red/green proof is recorded in the lane round-two validation, not a placement-completion claim.

- 2026-09-24 night — partial delivery only: zero omission built; placement canvas at `docs/internal/philo/phase-6/toast/toast-placement.html` has today/proposed/summary-open/capture boards at 1440 and 393. Parent independently recaptured all boards and longer-summary probes (`toast/parent-shots/`, `toast/canvas-dw-validation.md`). Owner ratification, placement build and actual rehearsal remain open; no paired done evidence is claimed. Exact strings and two owner asks are in `toast/README.md`. Muad'Dib publishes the canvas.
- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 3: zero tokens canvas-free; placement is design and needs a canvas; finding 3: the ChairHome seam by patch; corrected to `ChairHome.tsx:1442` in round two).
- 2026-09-24 night — RATIFIED by the owner (AskUserQuestion): the card in flow directly above the capture bar on the Arrival; off the Arrival a top-of-surface flow slot (inside the open Meetings window; above the Floor list); on the phone AUTO-SCROLL to the card's slot (he accepts that it moves his reading position). Canvas: `docs/internal/philo/phase-6/toast/` (artifact https://claude.ai/artifact/GMPLRZZ8AU2A9bF4phWHUS v3). Build what was ratified: the slot + an AmbientLayer portal + the auto-scroll; the spatial Floor's WebGL geometry is not drawn and is out of scope (ledger).
