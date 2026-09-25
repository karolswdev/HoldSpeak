# PHILO-6-03 - The toast that does not cover

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** backlog
- **Depends on:** - (the placement build depends on its canvas ratification)
- **Unblocks:** exit 3 (no zero token, no overlap at 393)
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", ledger row 4; Astra's check of the drafts, finding 2 row 3
- **Canvas:** the zero tokens none; the PLACEMENT a SMALL CANVAS at 1440 and 393, ratified by the owner before build

## Problem

After a summary the Arrival shows a transient toast `MEETING READY · N open · 0 decided`.

- **Zero token.** `AmbientLayer.tsx:175` renders `{signal.openTotal} open · {signal.decidedTotal} decided` with no guard. A count of zero breaks UX-CANON A.8. The numeric facts are correct and stay: `intelligenceAttention.ts:95-96` stores `openTotal` and `decidedTotal`.
- **Overlap.** The toast is fixed with a hard-coded bottom offset (`web/src/components/AmbientLayer.tsx:170`, `bottom: "104px"`). At 393 it covers the summary text and the capture bar (`../phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/summary/393-after.png`). The Arrival already measures the capture bar and sets `--arrival-capture-clearance` (`web/src/desk/chair/ChairHome.tsx:685`); the toast does not use it.

## Scope

- **In:** omit zero tokens at render (canvas-free); the placement drawn on a small canvas at both widths with the unobstructed position, ratified before build; the build of what was ratified; the rendered transition proof; the rig case at 1440 and 393.
- **Out:** new toast words, a new toast kind, a dismiss verb; any change of the numeric facts in `intelligenceAttention.ts`; everything the phase status lists as out.

## Acceptance criteria

- [ ] Zero tokens are omitted at render (`AmbientLayer.tsx:175`): `0 decided` and `0 open` never render; the numeric facts at `intelligenceAttention.ts:95-96` are unchanged. Fence red pre-fix (`0 decided` renders today).
- [ ] The placement canvas: the toast at 1440 and 393 over a real summary and the capture bar, from the real library species, with the unobstructed position; RATIFIED by the owner BEFORE the placement build.
- [ ] The built placement is the ratified one. At 393 the toast covers neither the summary text nor the capture bar (a geometry fence on the rendered transition: the toast's box does not intersect the capture bar or the summary's readable text). Red pre-fix.
- [ ] Lane law: if the placement needs the capture-clearance seam at `ChairHome.tsx:685`, the change goes to lane 01/02 as a PATCH; this lane never edits `ChairHome.tsx`.
- [ ] Rendered transition proof: the toast appears after a summary, with its words, and leaves, at both widths.
- [ ] Rig: the Phase 5 rehearsal summary step (`scripts/philo5_his_words.py`) at 1440 and 393; the `summary/393-after` shot shows the toast clear of the text and the capture bar, no zero token.

## Effort (council-style estimate, not a promise)

0.5 day for the zero tokens; 0.5–1 day for the placement incl. the canvas

## Test plan

- **Unit:** vitest on `AmbientLayer` (no zero token; red pre-fix); a rendered geometry fence at 393 (Playwright or the glass tests with `HOLDSPEAK_EVIDENCE_WRITE=1`).
- **Integration:** the rehearsal summary step at 1440 and 393, `--out` under this phase's assets.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 3: zero tokens canvas-free; placement is design and needs a canvas; finding 3: the `ChairHome.tsx:685` seam by patch).
