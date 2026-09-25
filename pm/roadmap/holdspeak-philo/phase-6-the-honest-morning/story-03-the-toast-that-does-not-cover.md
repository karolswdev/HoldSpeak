# PHILO-6-03 - The toast that does not cover

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** done
- **Depends on:** - (the placement build depends on its canvas ratification)
- **Unblocks:** exit 3 (no zero token, no overlap at 393)
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", ledger row 4; Astra's check of the drafts, finding 2 row 3
- **Canvas:** the zero tokens none; the PLACEMENT a SMALL CANVAS at 1440 and 393, ratified by the owner before build

## Problem

At the Phase 5 baseline, after a summary the Arrival showed a transient toast `MEETING READY · N open · 0 decided`.

- **Zero token.** `AmbientLayer.tsx:175` renders `{signal.openTotal} open · {signal.decidedTotal} decided` with no guard. A count of zero breaks UX-CANON A.8. The numeric facts are correct and stay: `intelligenceAttention.ts:95-96` stores `openTotal` and `decidedTotal`.
- **Overlap.** The toast is fixed with a hard-coded bottom offset (`web/src/components/AmbientLayer.tsx:170`, `bottom: "104px"`). At 393 it covers the summary text and the capture bar (`../phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/summary/393-after.png`). The proposed patch inserts an empty `data-aftercare-slot` div at `web/src/desk/chair/ChairHome.tsx:1442`, immediately before `<CaptureBar />`. It does not change the existing capture-clearance measurement. The build needs the slot, an `AmbientLayer` portal and auto-scroll; the patch alone places no card.

## Scope

- **In:** omit zero tokens at render (canvas-free); the placement drawn on a small canvas at both widths with the unobstructed position, ratified before build; the build of what was ratified; the rendered transition proof; the rig case at 1440 and 393.
- **Out:** new toast words, a new toast kind, a dismiss verb; any change of the numeric facts in `intelligenceAttention.ts`; everything the phase status lists as out.

## Acceptance criteria

- [x] Zero tokens are omitted at render: `0 decided` and `0 open` never render; numeric facts in `intelligenceAttention.ts` are unchanged. Real `publishAftercare` producer tests cover all four count pairs. Archive red: `docs/internal/philo/phase-6/toast/zero/red-origin-behavior.txt` (3 failed, 6 passed); parent DW green: `toast/zero/dw-validation.md` (13 passed).
- [x] The placement canvas: the toast at 1440 and 393 over a real summary and the capture bar, from the real library species, with the unobstructed position; RATIFIED by the owner BEFORE the placement build. Ratification: `38cf713a`, merged as `d8f608c8`; build starts from that revision. Boards: `docs/internal/philo/phase-6/toast/shots/`.
- [x] The built placement is the ratified one. In the validated Chromium run at 393 the toast covers neither the summary text nor the capture bar (a geometry fence on the rendered transition: the toast's box does not intersect the capture bar or the summary's readable text). Red pre-fix. Proof: `placement-proof/red-rendered.txt`, the three archived 393 observations, and the six final runs linked in `placement-proof/lane-report.md`; the real phone CaptureBar is 138 px high.
- [x] Lane law: the proposed slot goes to lane 01/02 as `docs/internal/philo/phase-6/toast/chairhome.patch`, with separate rationale. `toast/canvas-dw-validation.md` proves `git apply --check` and an empty ChairHome diff. The build brief grants Astra the exact patch as the only ChairHome change, in its own gated commit; applied as `d1e355f2`. Lane A owns reconciliation. Focused capture: `docs/internal/philo/phase-6/toast/placement-proof/slot-validation.md`.
- [x] Rendered transition proof: the toast appears after a summary, with its words, and leaves, at both widths. `assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/` and `20260925T052913Z-case.philo603.toast.arrival-astra-1440/`: real Dismiss click; card absent, slot empty and hidden, CaptureBar 9/9; before, after and dismissed shots inspected.
- [x] Rig: the build brief names actual atlas cases `case.philo603.toast.arrival`, `.meetings_window`, and `.floor_list`, each at 1440 and 393. A real meeting-intelligence producer with a declared provider replay triggers the aftercare signal. The card owns all 9 sampled points; on the active Arrival, summary text and CaptureBar own 9/9, and off Arrival the foreground Meetings headline or Floor-list header owns 9/9; card rectangles do not intersect summary, capture or BRIEF rows. A scroll observer is armed before the trigger. Spatial WebGL Floor retains fixed fallback with a shot and ledger entry. The phase-wide Phase 5 rehearsal remains the integration lane’s exit criterion. Proof: `placement-proof/lane-report.md` per-run table and `live-readings.txt`; scroll calls are one at 393 and zero at 1440. The Arrival backdrop hidden by a Meetings window is not claimed readable.

## Effort (council-style estimate, not a promise)

0.5 day for the zero tokens; 0.5–1 day for the placement incl. the canvas

## Test plan

- **Unit:** vitest on `AmbientLayer` (no zero token; red pre-fix); a rendered geometry fence at 393 (Playwright or the glass tests with `HOLDSPEAK_EVIDENCE_WRITE=1`).
- **Integration:** the three actual atlas cases at both widths through `scripts/graph_walk.py`, one case per invocation; `--out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`. Every pytest uses isolated HOME; shots use `HOLDSPEAK_EVIDENCE_WRITE=1`. The build brief limits suite scope to AmbientLayer + rendered fences, chair, pullouts, shell, atlas/rig tests, generated checks and DW check.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- Round two — the canvas also covers a Meetings window and the Floor at 1440 and 393. Recommended off Arrival: a top-of-current-surface flow slot, with no assumption that every surface has a CaptureBar. `AppShell.tsx:24` mounts AmbientLayer on every surface, so the future portal must follow the current surface. Ask 2 states that phone auto-scroll moves the owner’s reading position and scrolls the Arrival head off. At that canvas stage, owner ratification remained pending; it is recorded as resolved below.
- Round two — omit `Open proposals` at 0/0 as an authorized render-only correction (UX-CANON A.11, Tenet 3); retain Dismiss and unchanged numeric facts. Focused red/green proof is recorded in the lane round-two validation, not a placement-completion claim.

- 2026-09-24 night — partial delivery only: zero omission built; placement canvas at `docs/internal/philo/phase-6/toast/toast-placement.html` has today/proposed/summary-open/capture boards at 1440 and 393. Parent independently recaptured all boards and longer-summary probes (`toast/parent-shots/`, `toast/canvas-dw-validation.md`). Owner ratification, placement build and actual rehearsal remain open; no paired done evidence is claimed. Exact strings and two owner asks are in `toast/README.md`. Muad'Dib publishes the canvas.
- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 3: zero tokens canvas-free; placement is design and needs a canvas; finding 3: the ChairHome seam by patch; corrected to `ChairHome.tsx:1442` in round two).
- 2026-09-24 night — RATIFIED by the owner (AskUserQuestion): the card in flow directly above the capture bar on the Arrival; off the Arrival a top-of-surface flow slot (inside the open Meetings window; above the Floor list); on the phone AUTO-SCROLL to the card's slot (he accepts that it moves his reading position). Canvas: `docs/internal/philo/phase-6/toast/` (artifact https://claude.ai/artifact/GMPLRZZ8AU2A9bF4phWHUS v3). Build what was ratified: the slot + an AmbientLayer portal + the auto-scroll; the spatial Floor's WebGL geometry is not drawn and is out of scope (ledger).

- Build-lane authority (2026-09-24 night): worktree `../wt-philo-6-03`, branch `feat/philo-6-03-placement`; current main is the fork. The owner’s build brief supersedes the earlier lane-A-only patch instruction for this exact four-line insertion and names the actual atlas proof above. No placement redesign or string change is authorized. PR only; Muad’Dib counsels on built before merge.

- Browser proof boundary (Astra-invoked built check C1): 393 is a Chromium viewport, not a physical-phone or Safari observation. Native scroll anchoring preserves the card while late summary content expands. Safari 27 supports this feature, but no Safari result is claimed; older engines without anchoring are a named limitation in `docs/internal/philo/phase-6/ledger.md`.

- Build closure — 2026-09-24 night (UTC captures 2026-09-25): [lane report](../../../../docs/internal/philo/phase-6/toast/placement-proof/lane-report.md) pays each box, with raw red/green tails, six actual cases, Dismiss at both widths, and the spatial fallback. Focused Vitest: 30 pass; Python: 104 pass; broader scoped Vitest: 235 assertions pass but exits 1 on the inherited `currentBucket is not iterable` fixture error, reproduced on untouched main. The fixture repair is in the phase-local ledger. Astra-invoked check conditions are paid; calling Muad’Dib counsel remains before merge.
