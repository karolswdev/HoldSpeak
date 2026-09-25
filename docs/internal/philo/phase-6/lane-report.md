# LANE — Astra B, PHILO-6-03 / 04 / 05

Last updated: 2026-09-24 night, round two. PR: [#647](https://github.com/karolswdev/HoldSpeak/pull/647).
Worktree: `../wt-philo-6-b`; branch: `feat/philo-6-b-toast-rows-body`.
Base: `66205729332ef66a6d16a186c04ae4801311734a`.

## OUTCOME

04 and 05 are verified and done in this lane. 03 is partial: zero-count
omission and the 0/0 dead-verb omission are built; the placement canvas now
includes Meetings and Floor boards off Arrival, plus the ChairHome patch
proposal. Placement is **not built** and awaits the owner's
ratification. Muad'Dib publishes the canvas and applies the seam in his lane
after the owner's word. ChairHome has no lane B diff.

Three original gated commits plus one round-two records/canvas correction,
one lane PR, **no merge**:

- `e8ad4022` — PHILO-6-04, one cause / one observer row.
- `8bd4a05b` — PHILO-6-03 partial, zero omission and placement canvas.
- `f443a3ff` — PHILO-6-05, saved-body refresh fence.
- Round two — this commit: counsel of record, provenance corrections, amended
  canvas, named 0/0 render fence and follow-up ledger; no story flip.

Runtime worker evidence is in [delegation.md](delegation.md) and
[worker-runtime.json](worker-runtime.json): all three workers ran
`gpt-5.6-luna` at `xhigh`. Astra captured DW evidence, reviewed raw results
and glass, flipped stories, certified contracts and committed. The user
required scoped tests only; no full-suite claim is made. Round two used two
more Luna workers, verified in [round-two-worker-runtime.json](round-two-worker-runtime.json).

## PROOF

Round-two verification: [record and raw outputs](round-two/README.md). Parent
collected and ran 14 focused frontend tests, inspected the actual 0/0 component
at 1440/393, independently captured 14 canvas boards/probes (geometry matched), re-ran both retained actual-atlas sidecar/transition verifiers,
and passed all five generated checks. The phase DW check passes. Repository-wide
DW check has six errors identical to the retained pre-phase archive; no
new DW error is claimed. The DW component/canvas captures are [round-two/dw-validation.md](round-two/dw-validation.md); the full facts and parent shots are alongside them.

Paths in the tables are relative to this report unless named as repository paths.
The phase roadmap contains paired `evidence-story-04.md` and
`evidence-story-05.md`; 03 remains in progress and its partial DW captures live
inside the canvas artifact, with no orphan paired done evidence.

| Story / acceptance box | Result and evidence |
| --- | --- |
| 04.1 One missing read, one failure row | PASS. Real SQLiteObserver rows in `rows/green-http-{1440,393}/observer-rows.json`; route resolves durable owner before one service call. |
| 04.2 Legacy decision lineage | PASS. Production artifact/desk producers in `test_philo6_04_one_cause_one_row.py`: lifecycle-only reads retain lineage, desk wins colliding IDs. Legacy reads no longer create a false desk failure. |
| 04.3 No global failure suppression | PASS. Both actual service failures still observed; `rows/observer-mutation.txt` fails when both observers are removed. No observer/service modification. |
| 04.4 Pre-fix fence | PASS. Archive `rows/pre-fix-missing-id.txt`: `assert 2 == 1`. Parent DW 33 focused tests pass. |
| 04.5 Actual atlas sidecar parity | PASS. The rig refusal cases report `pass` before and after; the lane sidecar verifier over `walk_one_row.py` rows owns the parity verdict. HTTP case viewport 393 was added at `atlas-phase3.json:6500`. `case.philo504.decision_missing.refusal` and `.op` at both widths. `rows/verify_parity.py`: HTTP rows 67/68 versus op row 6 becomes HTTP 67 versus op 6, **FAIL 2:1 → PASS 1:1**. HTTP transport shots inspected at both widths; these are not a visible-refusal or final-morning claim. |
| 05.1 Cause before repair | PASS. [body/diagnosis.md](body/diagnosis.md), continuous archive S4 traffic and store trace. CREATE emits `desk_changed`; its decision GET resolves blank before Done, then waits for a slower sibling and commits after the optimistic save. |
| 05.2 First and subsequent frames readable | PASS. [body/verify_transition.py](body/verify_transition.py), actual S4 red/green traces. First frame was already good on main; later blank +159.1 ms at 393 / +77.3 ms at 1440. Built first frame +10.8 / +10.4 ms; all 129 recorded frames to terminal ~1.07 s readable at each width. Observer armed before Done. |
| 05.3 Failed save / receipt | PASS. Real store, subscribed projection, pullout and receipt; slow/failed rollback reads and stale refusal after newer success. Final test checks body and SAVE FAILED after the failed rollback refresh commits. Archive 5 failed / 2 controls; built all 7 pass. Existing scoped suites total 29 pass. |
| 05.4 Actual S4 / glass | PASS. `case.closure.chain.s4_saved_content` at 393 and 1440; `body/green-s4-*/observation.json` and `after.png`. Astra inspected both shots. Readability includes viewport and hit ownership. [body/build-identity.json](body/build-identity.json) ties the observed bundle to the source digest and unchanged store hash. |
| 03.1 Omit zero tokens | PASS. Real `publishAftercare`, all four count pairs; actual archive 3 failed / 6 passed, built 13 passed with AftercareNote. Numeric facts untouched. [toast/zero/dw-validation.md](toast/zero/dw-validation.md). |
| 03.2 Canvas and owner ratification | Canvas READY; owner ratification PENDING. Arrival comparison/proposal boards plus Meetings and Floor off-Arrival boards at 1440 and 393, library species and exact existing strings. Earlier canvas review was an Astra-invoked claude -p check. The actual Muad’Dib counsel conditions prompted this round-two canvas correction. |
| 03.3 Ratified built placement | OPEN. Existing fixed `bottom: 104px` remains; no placement implementation before owner's word. |
| 03.4 ChairHome lane seam | PASS as a proposal. [toast/chairhome.patch](toast/chairhome.patch), [rationale](toast/chairhome-rationale.md); parent and Astra-invoked claude -p `git apply --check`, target unchanged. Empty unhidden slot before the real CaptureBar; patch inserts only an empty `data-aftercare-slot` at ChairHome.tsx:1442 before CaptureBar. Build also needs the AmbientLayer portal, auto-scroll and current-surface off-Arrival slot; lane A integrates after ratification. |
| 03.5 Rendered production transition | OPEN. Canvas geometry is not a production appearance/egress transition proof. |
| 03.6 Actual rehearsal summary step | OPEN. Owed after ratified placement; not replaced by canvas or S4. |

Raw red/green lines (verbatim from retained outputs):

```text
E       assert 2 == 1
33 passed in 11.73s
      Tests  3 failed | 6 passed (9)
      Tests  13 passed (13)
      Tests  5 failed | 2 passed (7)
      Tests  29 passed (29)
      Tests  7 passed (7)
143 tests collected in 0.19s
143 passed in 99.83s (0:01:39)
15 passed in 2.32s
VERDICT: fail terminal=settled
VERDICT: pass terminal=settled
```

The last two lines are the actual S4 atlas red/green verdicts at **both** widths.
The 143 checks validate the rig; the actual S4 traces prove the product. Final
typecheck and build pass. OpenAPI, graph, API reference, capability docs and
boundary census were regenerated; shared generated files need reconciliation
by the integration lane. Historical graph conflicts are unchanged, not newly
certified by regeneration.

Canvas publication artifact: [toast/toast-placement.html](toast/toast-placement.html).
Board matrix and exact strings: [toast/README.md](toast/README.md).
Parent independent geometry: [toast/canvas-dw-final-validation.md](toast/canvas-dw-final-validation.md).

| Board | 1440 | 393 |
| --- | --- | --- |
| Today | [shot](toast/shots/today-1440.png) | [shot](toast/shots/today-393.png) |
| Proposed | [shot](toast/shots/proposed-1440.png) | [shot](toast/shots/proposed-393.png) |
| Summary open | [shot](toast/shots/summary-open-1440.png) | [shot](toast/shots/summary-open-393.png) |
| Capture (pressed-mic fixture) | [shot](toast/shots/capture-1440.png) | [shot](toast/shots/capture-393.png) |
| Meetings (off Arrival) | [shot](toast/shots/meetings-1440.png) | [shot](toast/shots/meetings-393.png) |
| Floor, list view (off Arrival) | [shot](toast/shots/floor-1440.png) | [shot](toast/shots/floor-393.png) |

Two owner asks, through Muad'Dib's publication:

1. Ratify the normal-flow slot before CaptureBar on Arrival, and the
   recommended top-of-current-surface flow slot inside Meetings or above the
   Floor work area off Arrival. Not every surface has a CaptureBar.
2. Ratify phone auto-scroll: it **moves his reading position**. The Arrival
   head scrolls off screen, as proposed-393 shows, to bring the card clear of
   the sticky CaptureBar. The mechanism is not implemented.

## LEDGER

[ledger.md](ledger.md) owns follow-ups: the unidentified slow read, delete/rename
race class, setup-read rejection, concurrent deletion during the protected
window, two overlapping refusals, probe completion metadata, hub-import
provenance improvement, and phase-wide closing rehearsal/owner review. The
old `pm/roadmap/holdspeak/` tree changes only BACKLOG’s three PHILO-6 follow-up
rows: slow refresh (performance, not a fence hole), unreachable kind clears
its siblings (pre-existing bug), and rig 1.2.0 stamp versus 1.3.0 predicate
(cosmetic). This lane records no owner sitting.

The earlier four Markdown records (03 canvas/zero, 04 built, 05 design and
05 built) are labelled **Astra-invoked claude -p check**, with
`astra-invoked-claude` filenames. The three JSON responses carry the same
notice in their first-line provenance field and remain valid JSON. Historical
verdict text is retained. These are Astra self-checks, not Muad’Dib’s check.
The actual Muad’Dib counsel is copied verbatim, without its Scratch archive
line, to `checks/lane-b-built-muaddib.md` in the phase roadmap. It is the
RATIFY-WITH-CONDITIONS record for PR #647 at f443a3ff; it does not purport to
review the round-two edits that follow it.
The PR remains a handover to Muad'Dib for integration; no lane B merge.

## AMENDMENTS

- S4 criterion strengthened to continuous readability. A first-frame-only red
  would be false: it already passed on main. Both the story and phase status
  record the checked amendment and the owner's right to overrule it.
- HTTP missing-decision atlas case admits 393 as required by this brief.
- The first fixed-offset canvas was rejected because it covered other Arrival
  text; one copy stays parked. Current proposal uses normal flow and discloses
  the sticky-bar/scroll dependency.
- Round-two correction follows the recorded counsel: off-Arrival flow boards,
  plain reading-position trade-off, correct slot/portal/scroll seam, and
  `Open proposals` withheld only at 0/0. Numeric facts stay unchanged.
- The misleading `body/red-s4-393/` folder is renamed to
  `body/negative-control-first-frame-393/`; its PASS remains raw evidence.
- 03 is intentionally partial. Its captured evidence is retained inside the
  artifact until placement can be ratified and built; it is not flipped done.
- Excluded trials are named in `rows/README.md` and `body/README.md`: wrong
  editable import, unavailable old viewport, held-prop control, first-frame-only
  probe, CLI omission, and corrected typecheck failure. The toast's initial
  lane-behaviour red was replaced by an actual archive run and retained as a
  labelled control. None is promoted to a valid product red/green.

## UNKNOWN

The slower sibling holding the whole-desk refresh is unidentified. The
unreachable-kind collection bug remains pre-existing debt and was not newly
reproduced here. Repository-wide DW errors remain in unchanged older phases. The spatial WebGL Floor is not proved by the list-mode canvas. The toast
placement is not owner-ratified or built, and its live transition/rehearsal is
not verified. The phase-wide morning rehearsal and owner review remain open.
S4's green trace bounds continuous readability through its terminal observation;
it is not a long-running soak. No full suite was run under this scoped lane law.

Tuesday: one missing decision makes one observed cause; Done keeps the sentence
readable; the owner can review a concrete toast proposal before placement build.
