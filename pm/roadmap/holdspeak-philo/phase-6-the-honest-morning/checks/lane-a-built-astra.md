# Check — Astra, 2026-09-24 night, on built: Phase 6 lane A (PR #646 @ f6c0c0d1)

VERDICT: BOUNCE — do not merge #646 at `f6c0c0d1`. The rehearsal failures are inherited, but the branch introduces two misleading claims.

FINDINGS:

1. **P1 — A failed decision-record operation now claims success.** `_collect_changes` passes `broke=False` without checking the event’s error (`holdspeak/services/monday_brief_service.py:560`). I called the real observed `create_from_desk` producer with a missing decision, then generated the brief. The DB contains **zero decision records**, but stores both `Decision recorded` and `Decision did not record`. Archived main stores the old operation name instead. [Comparative DB evidence:29](/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo6-check-itsg79sl/decision-failure-comparison.json:29). **Fails Tenets 3/4 and Article VI.**

2. **P2 — The badge repair creates a wrongly attributed failure in the expanded row.** The one-line mapping is correct; no adapter or transcription change was needed. The producer→adapter→rendered fence is sound: producer and adapter pass before the fix; rendered badge and mapping assertions fail with SAVED. But the new FAILED value activates the summary-status well at `web/src/desk/chair/ChairHome.tsx:2172`, headed `SUMMARY` at line 2227. The `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-01-shots/20260925T023753Z-case.philo601.import_failed.badge-muaddib-1440/after.png` consequently says **SUMMARY / FAILED when the import failed**. Existing components do not make that new claim lawful. **Fails Tenet 3 / Article VI.** Counting the failure in `2 need you` is lawful. `importing`/`refused`/`live`→SAVED are inherited holes that may remain scoped debt, but `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/story-01-the-honest-import-badge.md:33` cannot claim the broad fallback guarantee satisfied.

3. **Clock ruling: ratify the existing idiom reuse; no new canvas required.** The charter expressly authorizes this repair. Caption and receipt use the same timestamp formatter; the offset-aware producer fixture and Warsaw rendered test establish the intended conversion. The receipt retains its existing meaning and structure. `web/src/desk/pullouts/views/BriefView.tsx:117`, `web/src/desk/chair/briefEgress.tsx:51`. The default producer’s naive timestamp remains a disclosed limitation, not proof of cross-zone correctness.

4. **Count ruling: ratify “no canvas needed.”** `THINGS WAITING` counts current Arrival triage rows; `Brief ready · N items` counts the generated snapshot. Those labels and meanings remain distinct. The fixture exercises THIS WEEK and a shelved row; its expected difference is correct. Fixing producer titles removes the unintended raw-name exclusion for these newly generated rows. `web/src/desk/chair/ChairHome.tsx:882`, `web/src/desk/chair/__tests__/briefTruth.philo602.test.tsx:83`. This does not repair historical snapshots containing old raw titles.

5. **P2 — Removing code punctuation does not establish human wording.** `Summary requested` correctly distinguishes request from completion, and the specific failure labels are short status labels. The generic fallback still exposes implementation vocabulary: a real observed missing-decision read produced **`Primitive: get decision did not complete`**. [Producer evidence:16](/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo6-check-itsg79sl/fallback-proof.json:16), `holdspeak/services/monday_brief_service.py:484`. Keeping “Primitive” to distinguish an atlas text selector is not a product-language justification. **Fails Tenet 4.** The existing re-pinned assertions were not weakened; their missing coverage is outcome truth and vocabulary, beyond a `Service.method` regex.

6. **The rehearsal failures reproduce independently of this branch.** I ran the unchanged driver against isolated, separately built archives:
   - **Main `66205729`:** import and summary succeeded; Codex used `door.add_item`; the driver failed on missing `desk.create`.
   - **Branch `f6c0c0d1`:** import and summary succeeded; MCP created `decision_d3dc1cebef9e`; the driver then failed resource-list reconciliation.

   [Comparison, transcripts and DB paths](/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo6-check-itsg79sl/rehearsal-comparison.json). Both driver hashes match. This supports inherited tool-selection/reconciliation failures, **not a new MCP regression**. Neither run completes the rehearsal. Also correct `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/evidence-story-02.md:60`: the two missing-`desk.create` runs created follow-through tasks through `door.add_item`, not decisions through `desk.create`.

7. **DONE is not justified by the gate’s evidence-pairing rule.** `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/evidence-story-02.md:64` explicitly records flipping DONE to satisfy lint while an acceptance criterion remained unmet. The required remedy is a visible, checked scope amendment (`docs/internal/ORCHESTRATION.md:69`), not status inflation. **Fails Tenet 3 / Article IX.** Deferring the inherited rehearsal failure solely to phase exit 3 is reasonable, but rewrite and record that amendment explicitly. As written, 02 remains incomplete.

8. **Mechanical checks pass; they do not override these findings.** I collected and ran **228 scoped Python tests**, including both Phase 5 compatibility files: all pass. **178 web tests** pass. All three generated checks, `dw check`, and `dw verify 66205729..HEAD` pass. [Python output](/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo6-check-itsg79sl/scoped-run.txt), [web output](/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo6-check-itsg79sl/scoped-web.txt). The retained actual-atlas runs support badge visibility and destination-title repair at both widths. Withholding `chairhome.patch` was correct: its canvas remains unratified. HEAD and the worktree remain unchanged.

CONDITIONS:

- Make completion wording depend on the recorded outcome; fence a real failed decision-record producer through the stored and rendered brief.
- Correct the expanded import-failure attribution and fence the complete row.
- Replace the exposed internal fallback vocabulary; change affected words and atlas selectors together.
- Correct the status/evidence claims, explicitly amend any rehearsal deferral, and assign inherited holes concrete backlog homes.
- Obtain the required final verification and completed CI assessment before merge.

MISSED:

1. Success wording was added to a collector that also includes failed operations.
2. The badge helper controls attention and expanded-well rendering, beyond the badge itself.
3. The destination still displays raw JSON and exception text, including overflow at 393. This is disclosed inherited debt, but “BACKLOG candidate” is not an assigned home.
4. Story 01 still contains the retracted adapter diagnosis beneath its correction.

TUESDAY: Not yet: he can see the failed import, but the face names the wrong failure, and his brief can claim a decision was recorded when none exists.

UNKNOWN: No full suite, completed closing rehearsal, updated S5 closing walk, or owner sitting was verified. At final inspection, CI unit tests were running and macOS integration/E2E jobs remained queued.