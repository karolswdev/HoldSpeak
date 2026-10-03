# PHILO-13-01 — B0 closing verification

LANE: B0 / PHILO-13-01. Owner: Astra. Prior built counsel: Muad'Dib.
Worktree: `../wt-philo-13-close-astra`; branch: `docs/philo-13-close-astra`;
PR: [#755](https://github.com/karolswdev/HoldSpeak/pull/755).
Astra session: `01a103a3-6d2a-7022-95e6-a97f018f75d2`.

OUTCOME: built. All nine B0 cases pass at both widths on the product code
merged by B2 #747, main `050ce14d6fc3c2f029d3dff75d37686147044e03`.
F1 and F2 pass. Eight related Park, Dock and Update runs also pass.
The table distinguishes each predicate result from remaining face defects.
The full-suite result and follow-up homes are recorded below; this is not a
claim that the whole product is green.

## Authority and source

This close executes the caller's 2026-10-03 instruction: “on your #755
branch, merge origin/main (050ce14d), make the zone Floor step optional,
rerun ALL B0 cases on main's head one per invocation at both widths,
capture canonical evidence-story-01.md, flip 01 done (+ status row,
Where we are, README Last updated), self-merge #755 with a merge record.”
The instruction is conditional on passing cases and does not authorize
closing over a failed B0 case. All 18 core runs pass.

Muad'Dib's built counsel is the signed [#726 r3 check](https://github.com/karolswdev/HoldSpeak/pull/726#issuecomment-5962766839),
RATIFY-WITH-CONDITIONS; the durable-pin condition and fresh-clone check
were paid in the [#726 merge record](https://github.com/karolswdev/HoldSpeak/pull/726#issuecomment-5963142100).
His [C5 ruling](https://github.com/karolswdev/HoldSpeak/pull/726#issuecomment-5945830968)
allows defects outside B2 to retain their named homes, requires F2 green,
and requires F1 to be walked after #725. This record applies that settled
gate and the explicit closure dispatch. It does not invent a new Muad'Dib
review of these closing artifacts. Astra's closing verdict is RATIFY for
B0, with the limits and follow-up homes below.

B0 first merged as `44ec934a` (#726); its later Zone repair merged as
`a30544db` (#757). [B2's merge record](https://github.com/karolswdev/HoldSpeak/pull/747#issuecomment-5973594494)
names those commits and its B0 evidence. B2's [batch table](assets/story-07-shots/merge-runs/summary-batch.txt)
and [optional-Floor reruns](assets/story-07-shots/merge-runs/summary-zone-floor-optional.txt)
are retained. Their observations report `ab9bd1ea` with `dirty=true`;
they are branch evidence, not observations minted at `050ce14d`.
The current runs below close that source-attribution gap. Canonical
story-01 evidence is supplied by this closure after B2 merged; the
chronology is explicit, not backdated.

The lane merged main as `95ee5fe315c2760c8cbdd185a44206345bc6b5a9`.
Every current observation reports that revision, `dirty=true`, the same
built frontend, and atlas SHA-256
`a7258d2f94f445d61b10456efdbc20e8572ca875ab07523ea8885cdd33fbe40a`.
[Source provenance](assets/story-01-close-final/source-provenance.json)
records no product-code differences from `050ce14d` across `holdspeak`,
`web/src`, `scripts` and dependency files. The dirty changes are the
Zone atlas setup, its fence, and closure records. B2's People anchor is
confirmed at `PeopleCore.tsx:421` (`PrepLens`), formerly 401; it is a
line-only move in `state.people.p13_prep`.

## PROOF

The [canonical capture](evidence-story-01.md) contains the actual commands,
exit codes and output. The [26-run index](assets/story-01-close-final/runs.json)
records every predicate, bound, hit result, native-touch adapter and DB
path. Each run used a separate invocation and a distinct temporary hub
HOME; every resolved DB path is beneath that HOME. The [manifest](assets/story-01-close-final/manifest.json)
hashes all 26 unaltered observations and 52 shots. Astra inspected every
before and after shot at its recorded width. The superseded preparation
[run index](assets/story-01-close-prep/runs.json) and failed shots are
retained separately; none is counted as a current pass.

All 18 core runs reach their initial face, settle within their stated
bound and own all nine final hit-test points. PASS means that the declared
case predicate passed; Calendar and Roadmap deliberately test their
observed refusal lifecycle. Their residual defects are still open.

| Path | 1440 | 393 touch | Product-red and home | Proof limit / useful result |
|---|---|---|---|---|
| Calendar snapshot | [PASS 4.660 s](assets/story-01-close-final/walks/calendar.snapshot_window-1440/20261003T212903Z-case.p13.calendar.snapshot_window-astra-1440/observation.json) | [PASS 5.245 s](assets/story-01-close-final/walks/calendar.snapshot_window-393/20261003T212922Z-case.p13.calendar.snapshot_window-astra-393/observation.json) | F6 / B0-L1: raw no-model refusal; Tenet 4. | Refusal lifecycle only; no vision extraction. |
| Roadmap | [PASS 11.236 s](assets/story-01-close-final/walks/roadmap.window-1440/20261003T212940Z-case.p13.roadmap.window-astra-1440/observation.json) | [PASS 7.853 s](assets/story-01-close-final/walks/roadmap.window-393/20261003T213010Z-case.p13.roadmap.window-astra-393/observation.json) | F4 / B0-L4: Roadmap not found; Tenet 3. | Refusal lifecycle; repository router seam below. |
| Repository | [PASS 10.055 s](assets/story-01-close-final/walks/repository.window-1440/20261003T213036Z-case.p13.repository.window-astra-1440/observation.json) | [PASS 6.981 s](assets/story-01-close-final/walks/repository.window-393/20261003T213104Z-case.p13.repository.window-astra-393/observation.json) | None in this run; F3 useful file is visible. | Repository router seam below. |
| Delivery dossier | [PASS 11.604 s](assets/story-01-close-final/walks/delivery.dossier_window-1440/20261003T212753Z-case.p13.delivery.dossier_window-astra-1440/observation.json) | [PASS 11.785 s](assets/story-01-close-final/walks/delivery.dossier_window-393/20261003T212636Z-case.p13.delivery.dossier_window-astra-393/observation.json) | F9 / B0-L5: zero counters; Tenets 3 and 6. | F2 clear, including 393; repository router seam. |
| Delivery terminal | [PASS 12.889 s](assets/story-01-close-final/walks/delivery.terminal_window-1440/20261003T212831Z-case.p13.delivery.terminal_window-astra-1440/observation.json) | [PASS 12.951 s](assets/story-01-close-final/walks/delivery.terminal_window-393/20261003T212716Z-case.p13.delivery.terminal_window-astra-393/observation.json) | F9 / B0-L5: clipped or overflowing controls; Tenets 3 and 6. | F2 clear, including 393; repository router seam. |
| Chain pullout | [PASS 10.945 s](assets/story-01-close-final/walks/chain.pullout-1440/20261003T213128Z-case.p13.chain.pullout-astra-1440/observation.json) | [PASS 7.183 s](assets/story-01-close-final/walks/chain.pullout-393/20261003T213159Z-case.p13.chain.pullout-astra-393/observation.json) | None in this run; F1 clear. | Card and Dock chip close and reopen after reload. |
| Coder pullout | [PASS 8.976 s](assets/story-01-close-final/walks/coder.pullout-1440/20261003T213222Z-case.p13.coder.pullout-astra-1440/observation.json) | [PASS 6.663 s](assets/story-01-close-final/walks/coder.pullout-393/20261003T213250Z-case.p13.coder.pullout-astra-393/observation.json) | None in this run; F1 clear. | Card and Dock chip close and reopen after reload. |
| Directory → Zone | [PASS 30.340 s](assets/story-01-close-final/walks/directory.zone-1440/20261003T212430Z-case.p13.directory.zone-astra-1440/observation.json) | [PASS 17.438 s](assets/story-01-close-final/walks/directory.zone-393/20261003T212545Z-case.p13.directory.zone-astra-393/observation.json) | None in this run; F7 clear. | Native touch at 393; 40 s bound unchanged. |
| Info | [PASS 28.852 s](assets/story-01-close-final/walks/info.window-1440/20261003T213322Z-case.p13.info.window-astra-1440/observation.json) | [PASS 16.937 s](assets/story-01-close-final/walks/info.window-393/20261003T213427Z-case.p13.info.window-astra-393/observation.json) | None in this run. | Native touch at 393; 75 s bound unchanged. |

Related cases were also rerun from the actual Astra atlas:

| Case | 1440 | 393 | What this proves |
|---|---|---|---|
| meeting.park_restore | [PASS 2.230 s](assets/story-01-close-final/walks/meeting.park_restore-1440/20261003T213505Z-case.p13.meeting.park_restore-astra-1440/observation.json) | [PASS 2.235 s](assets/story-01-close-final/walks/meeting.park_restore-393/20261003T213525Z-case.p13.meeting.park_restore-astra-393/observation.json) | Real API Park/Restore retains the transcript. Protocol proof; the face's Park button is not exercised. |
| workbench.park_restore | [PASS 2.244 s](assets/story-01-close-final/walks/workbench.park_restore-1440/20261003T213543Z-case.p13.workbench.park_restore-astra-1440/observation.json) | [PASS 2.239 s](assets/story-01-close-final/walks/workbench.park_restore-393/20261003T213605Z-case.p13.workbench.park_restore-astra-393/observation.json) | Real API Park/Restore retains the result and body. Protocol proof; the face's Park button is not exercised. |
| dock.needs_you_week | [PASS 2.239 s](assets/story-01-close-final/walks/dock.needs_you_week-1440/20261003T213627Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | [PASS 2.232 s](assets/story-01-close-final/walks/dock.needs_you_week-393/20261003T213646Z-case.p13.dock.needs_you_week-astra-393/observation.json) | Real-producer week reads 6 → 5 on the Dock. |
| update.linked_week | [PASS 0.951 s](assets/story-01-close-final/walks/update.linked_week-1440/20261003T213705Z-case.p13.update.linked_week-astra-1440/observation.json) | [PASS 0.957 s](assets/story-01-close-final/walks/update.linked_week-393/20261003T213734Z-case.p13.update.linked_week-astra-393/observation.json) | Replayed meeting-summary input; real deterministic draft returns 200 and stores summary, decision, action and owner text. |

The Update case passes its declared `text_contains` outcome at both widths.
Its phone hit-sample flag is false; it is not nine-point input-ownership
proof or a full phone-layout audit. Meeting and Workbench run in the
native-touch browser context at 393, but their mutations are API steps.
No protocol-only result is presented as a clicked face transition.

Repository-backed cases use the existing `build_roadmaps_router` seam to
point production repository routes at a fixture repository beneath the
run HOME. The repository and rows are minted through the real producers;
this is not proof of unmodified production hub wiring. This qualification
carries Muad'Dib's C4 ruling into the final evidence.

Tests:

- The corrected Zone setup and its fence ship together. The worker first
  ran the new fence against the old atlas and saw the required failure
  (“post-reload Floor re-entry must be optional”). [Red output](assets/story-01-close-final/tests/red.log),
  [red collection](assets/story-01-close-final/tests/collect-red.log),
  [green collection](assets/story-01-close-final/tests/collect-green.log),
  [33 passed](assets/story-01-close-final/tests/green.log).
- The five-file story selection, including all three shared fences,
  [collects 173 tests](assets/story-01-close-final/tests/focused-collect.txt)
  and passes all 173 in the canonical capture at `2026-10-03T21:25:56Z`.
  The first attempt omitted the browser-cache environment variable and
  failed five browser launches; it is retained, then rerun with the
  required environment. It is not counted as a product defect.
- Full Python: **104 failed, 13,907 passed, 117 skipped, four xfailed,
  four setup errors** in 2,345.41 s. The tree had no worker editing; Metal
  was excluded and HOME, browser and npm caches were isolated/configured. [Collection](assets/story-01-close-final/tests/full-collect.txt),
  [full output](assets/story-01-close-final/tests/full-python.txt),
  [JUnit](assets/story-01-close-final/tests/full-python.xml).
- Web baseline: the final serial run has **3,263 executed tests passed**
  and zero assertion failures. The baseline checker exits 0, but Vitest
  exits 1 because `DeskApp.test.tsx` cannot load: its TrustWindow mock
  omits `useTrustWindow`. This also fails on exact main `050ce14d`.
  The checker ignores suite-load failures, so this is not a green web
  suite claim. The initial six assertion failures pass twice in serial
  isolation (90/90 each), then all executed tests pass in the final run.
  [Commands and class-c evidence](assets/story-01-close-final/tests/web-run-commands.md);
  [final JSON](assets/story-01-close-final/tests/web-vitest-final.json);
  [exact-main collection failure](assets/story-01-close-final/tests/baseline-deskapp.json).
- All 12 documentation commands ran: nine pass, including link checks
  and the graph join. Architecture validation fails on two old B2 test
  titles in `docs/internal/philo/data/desk.json:619,1404`; capability-doc
  and coverage checks also stop on that invalid metadata. The same two
  errors reproduce on exact main. Home: B2 architecture test-reference
  maintenance. `dw doctor` is healthy. `dw check` reports the phase final
  summary missing now that all story headers are done; the phase exit
  record remains Muad’Dib’s separate close, with its criteria still to settle.

## LEDGER

| Class | Finding and cost to the owner | Open home |
|---|---|---|
| b — observed product defect | F4: Roadmap opens a twice-qualified identity and shows “Roadmap not found” at both widths. The architect cannot read this roadmap. Tenet 3. | [B0-L4](../BACKLOG.md), faces lane / C4 residual; story 14 being done does not close this finding. |
| b — observed product defect | F6: Calendar exposes `no_vision_model_assigned` at both widths. The refusal is not STE product text. Tenet 4. | [B0-L1](../BACKLOG.md), Calendar face owner. |
| b — observed product defect | F9: Dossier shows zero counters; Terminal controls overflow or clip. F2's visible front sheet is fixed, but this does not cure every layout defect. Tenets 3 and 6; UX-CANON A.8. | [B0-L5](../BACKLOG.md), Delivery faces / C1 and C7 residuals. |
| resolved in current actual runs | F1 Chain/Coder close card and Dock chip, then reopen; F2 Dossier/Terminal visible and hit-owned at 393; F3 Repository reads a useful file; F7 Zone opens; L2/L3 native input paths pass. | Historical findings and observations remain in the tree. No new product fix is attributed to this closure. |
| harness limit | Meeting/Workbench API transitions, Update replay and phone hit limit, repository router seam, no model-backed Calendar extraction. | B0 proof boundary above; owner-use proof remains separate. |

The full-suite residuals remain open in [BACKLOG B0-L6](../BACKLOG.md).
Highest-cost follow-ups include FirstWords Keep as Note at both widths,
People fixture/schema compatibility, the People raw-ID ratchet and PHILO-8
post-action receipts. These are separate from the core B0 pass table.

The full Python failure ledger is recorded with exact node names and
follow-up homes; no failure is silently described as inherited from a
matching name alone. [Ledger](assets/story-01-close-final/tests/failure-ledger.md).
All 29 failed unit nodes were collected and rerun on exact main `050ce14d`:
28 reproduce the same causes; the primitive-envelope node passes once and
remains unclassified. Of the other 80 red nodes, 32 names recur from the
prior ledger and 48 are new to that record. These are named recurrences,
not same-cause baseline claims. The unit comparison preserves 25 exact
message matches and three set-order or generated-ID-only differences.

## AMENDMENTS

No chartered product criterion changed. The caller authorized one setup
repair: Zone's post-reload `Floor` click is optional because B2 already
restores the Floor. The old click could toggle away from it. The change
is the same class as the merged Info and Delivery repairs. The window's
identity, readable content, nine hit points, close/reopen lifecycle and
40 s bound remain unchanged. The negative fence also covers Info.
B2's historic 42.704 s batch miss remains in its table; the current solo
Zone run passes at 30.340 s. No timeout was raised to obtain this close.

## UNKNOWN

The phase final summary and exit-criterion reconciliation are still owed
by the phase owner; B0 does not mark them complete to clear a lint rule.
The three documentation validation failures remain homed to the stale
B2 architecture test references.

The remaining 80 full-Python failure causes are not individually
attributed against main. The owner's real desk, microphone, live model extraction and unrestricted
hub wiring were not exercised. No sends or owner DB writes were made.
The full phase's other exit criteria and older Phase 7–12 live walks were
not re-certified by this B0 close. Tuesday: the nine window lifecycles
work in these runs; Roadmap's useful view, Calendar's refusal wording and
Delivery's remaining layout still need their named face work.
