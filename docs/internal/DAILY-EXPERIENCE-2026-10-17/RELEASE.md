# Decision, Ask and Thread — delivery record

The owner's priority is how daily work looks, feels and operates. This batch rebuilds the composition of the three named faces with the existing Workbench components.

## Result

- **New decision:** a wider, warm-paper writing surface leads the window. Background and Consequences are folds that retain drafts. The creation prompt names the decision and uses Create. Done remains in the footer on a phone.
- **Ask:** a stable reading window, a paper question editor and explicit question/answer sources replace the compressed form. Edit question retains the previous answer and Keep action until a new Ask. A new answer opens at its beginning. The request does not claim conversational memory it does not carry.
- **Thread:** readable paper turns, a compact header and a bounded writer. Sources and Commands expose the existing pickers; command focus returns to the writer. Enter during streaming edits the draft, while Stop remains explicit. Expanded source lists scroll within the header and show meaningful names.

Root inspected the actual-library canvas before build and the resulting application at 1440 and 393. Owner aesthetic acceptance remains open. These changes are not acceptance of every product face.

## Actual application observations

Walks use `scripts/graph_walk.py`, one case per invocation, isolated HOME and a real local hub/database. The atlas is `docs/internal/philo/graph/atlas-daily-experience.json`. Ask uses the declared recorded provider-boundary reply in `tests/fixtures/daily_experience_answer.json`; Thread content enters through the real import API. Neither proves live provider quality or throughput. No walk writes to the owner's desk.

| Job | Evidence | Result |
| --- | --- | --- |
| Create, write and save Decision, 1440 | `.tmp/daily/decision-paper-1440/20261017T181918Z-case.daily.decision.save-astra-1440/` | Pass; paper/padding and Done verified |
| Create, write and save Decision, 393 | `.tmp/daily/decision-paper-393/20261017T181943Z-case.daily.decision.save-astra-393/` | Pass; paper/padding and footer verified |
| Read and edit Ask, 1440 | `.tmp/daily/ask-1440/20261017T181812Z-case.daily.ask.edit-astra-1440/` | Pass; answer retained, draft restored |
| Read and edit Ask, 393 | `.tmp/daily/ask-393/20261017T181842Z-case.daily.ask.edit-astra-393/` | Pass; reader, composer and Keep reachable |
| Thread Commands, 1440 | `.tmp/daily/thread-final-1440/20261017T182636Z-case.daily.thread.commands-astra-1440/` | Pass; draft retained and command focused |
| Thread Commands, 393 | `.tmp/daily/thread-commands-393/20261017T182225Z-case.daily.thread.commands-astra-393/` | Pass; draft retained and command focused |
| Thread 12 named sources, 393 | `.tmp/daily/thread-final-sources-393/20261017T182939Z-case.daily.thread.sources-astra-393/` | Pass; header 240px, reader 319px, composer 124px |

The pointer probe moves the real browser pointer across nine points of the visible primary controls' target areas. Reported controls own these points; screenshots alone do not establish this. Final Thread source titles resolve seeded refs from the live desk, prefer frozen names, exclude import bookkeeping and retain an honest missing-source fallback.

## Findings fixed during integration

The first Decision screenshot exposed a generic section rule overriding paper padding; the scoped rule now wins in the actual application. The first Thread source screenshot exposed raw seed refs and import bookkeeping; meaningful titles now render. Independent review also found command focus and unbounded expanded headers, both corrected and rechecked.

The real Note → selected passage → phone More → Ask journey exposed a separate failure: Ask relied on global floor selection, which can discard a note that is not a desktop icon. The failed observation is preserved at `.tmp/daily/ask-passage-393-v5/20261017T182452Z-case.daily.ask.passage-astra-393/`. A retrieval citation in the answer did not prove explicit passage custody. The canonical saved-source handoff now passes, including the exact selected passage. A newer handoff reopens the composer and an older request cannot close it on success. The sent answer and Keep retain their original source snapshot.

## Verification and delivery

Focused Decision checks: 46 passed. Final Thread component/composer checks: 119 passed. Final Ask/Note/handoff checks: 95 passed. Existing Ask browser regressions: seven passed, including guardrail/refused-send and reference-chip phone controls. Atlas checks: 54 passed. Documentation guards: 75 passed. TypeScript passes. These counts support behavior, not aesthetic acceptance.

The populated Ask desktop walk passes at `.tmp/daily/ask-final-1440/20261017T183625Z-case.daily.ask.passage-astra-1440/`: the selected note and quote survive editing, with Ask and Keep owned by their real pointer targets. The fully expanded phone case passes at `.tmp/daily/ask-expanded-393-v2/20261017T183607Z-case.daily.ask.passage-astra-393/`: quote and Add notes both open, Back/Remove reachable through the context scroll, and Ask/Keep visible. The 377px composer leaves 214px for the answer. The final ScrollHint build also passes at `.tmp/daily/ask-scrollhint-393/20261017T184302Z-case.daily.ask.passage-astra-393/`: Back, Remove, Ask and Keep own all nine real-pointer probe points; the composer remains 377px with no overflow.

Source digest and built bundle agree: `e95ae448a3f033e6`. The broad ordinary quick passed 4,188 related tests and found one stale test that expected Listen before opening More. The corrected test retains all speech/stop assertions and its 11-test file passes. The final ordinary quick against product commit `3bdd33132` is GREEN: 11 related tests, 109 desktop/phone sweep cases and 17 canon checks. The earlier broad sweep and canon checks also passed. No product behavior changed between these quicks; the remaining delta is one test interaction.

Independent integrated advisory review: RATIFY, recorded in `INTEGRATED-REVIEW.md`. PR #1243 merged and was delivered locally; the formal review and subsequent full-run findings are recorded below.

## Delivered, reviewed and fixed forward

[PR #1243](https://github.com/karolswdev/HoldSpeak/pull/1243) merged at `018a1358f`. Normal idle delivery started PID14353 from `/Users/karol/dev/tools/wt-daily-experience-20261017`, port8765, build `e95ae448a3f033e6`. Source and served build agreed; Desk, health, Conductor and Models returned200. The actual root Desk address printed by `holdspeak web` was opened; credentials remain private. No tests or builds run in that serving tree after delivery.

The final same-build desktop Ask walk also passes at `.tmp/daily/ask-scrollhint-1440/20261017T184456Z-case.daily.ask.passage-astra-1440/`: reader287px, composer225px, Ask/Keep own all nine real pointer points.

[Formal Astra postmerge review](https://github.com/karolswdev/HoldSpeak/pull/1243#issuecomment-6238883336) ratified the delivered surfaces, with full-main pending. The subsequent full run at `018a1358f` completed with **5 failed, 16,693 passed, 26 skipped and 1 expected failure** in681.06seconds; mandatory live bus passed3 in24.44seconds. Evidence: `/Users/karol/dev/tools/wt-main-proof-20261016/.tmp/daily-main/{main-full.log,main-full-results.xml,main-full-state.json}`. These original failures are retained:

- Product copy: the generic command action **Run** did not name its consequence. It now uses the existing command label, such as **Switch mode** or **Toggle guardrail**.
- Product language: Decision's unqualified **Context** label becomes **Background**, including copied text. The stored field and draft custody remain unchanged.
- Receipt browser checks at1440/393: Rename moved into **Thread details**. The tests now open that fold and retain every receipt/pointer assertion; both pass.
- Recall withdrawal after a project edit: one `database is locked` exception occurred in the memory-index write. Diagnosis and its final disposition are recorded below; no speculative retry is added.

Focused follow-up checks pass: Decision46, Thread composer93, receipt browser2 and copy/language21. The proof tree's initially empty shared dependency directory was restored from the existing verified installation. The serving source and bundle were unchanged; the proof build then matched `e95ae448a3f033e6` before the full run.

### Recall lock disposition

The lock remains **unresolved**, not dismissed as a flake. The original failing parameter passes alone (1), and the complete scoped file passes52 with3 fixture-recording skips after55 collected. Logs: `.tmp/daily-main/recall-{collect,original,file-before}.log`. The sweep materializes source readers before index writes; post-terminal ThreadService work is a read and cleanup, and broker receipt persistence precedes terminal publication. Bounded competing-write probes did not reproduce the exception. The original report has no SQLite extended error code, so a snapshot/upgrade race remains a hypothesis. No transaction patch, retry or sleep is justified by this evidence. A recurrence should retain `sqlite_errorname`, transaction state and SQL/thread traces. A later passing full run does not establish a cause or erase this finding.

The ordinary follow-up quick check is GREEN:304 related web checks,12 affected
browser checks,109 desktop/phone sweep cases and17 canon checks. It builds the
follow-up source and retains logs at `.tmp/daily-main/quick-followup.log` and
`.tmp/daily-main/quick-logs/`. The full suite will run on the merged follow-up in
the separate proof tree, with failure-only SQLite metadata capture.

## Follow-up delivered; source anchor corrected

[PR #1244](https://github.com/karolswdev/HoldSpeak/pull/1244) merged at `ac55cd318`.
Actual Toggle guardrail controls pass at1440 and393: all nine real-pointer target
points owned, full label fits, exact draft retained on Close and writer focus
restored. Root inspected both images. Evidence in the proof tree:
`.tmp/daily-main/thread-argument-1440/20261017T190826Z-case.daily.thread.argument_label-astra-1440/`
and `.tmp/daily-main/thread-argument-393/20261017T190939Z-case.daily.thread.argument_label-astra-393/`.
Both use the same compiled frontend; the first records the precommit worktree
and the second `92a47b65a` during the root's record changes.

Normal idle delivery now serves from `wt-daily-delivery-20261017`, PID38565,
port8765. Source and served build equal `22aa76d6327046a1`. The verified bundle
was copied byte-for-byte from the separate proof tree. Desk, health, Conductor
and Models return200. The actual root Desk address printed by `holdspeak web`
was opened privately. Jupiter preview4488 and the stable dependency chain
remain intact. No tests or builds run in the new delivery tree after it starts
serving. [Formal Astra review](https://github.com/karolswdev/HoldSpeak/pull/1244#issuecomment-6239292955): RATIFY.

The follow-up full run completed with **16,697 passed,1 failed,26 skipped and1
expected failure**. Exact tail: `1 failed, 16697 passed, 26 skipped, 1 xfailed, 12 warnings in 674.18s (0:11:14)`. Mandatory live bus: `3 passed in 23.82s`. The sole
failure is `test_every_source_reference_lands_on_its_symbol[atlas-phase8.json]`:
the phase8 atlas still cites the old Context label. Its one source anchor now
cites Background; all26 source-anchor checks pass after26 collected. No
product source changes in this correction. Logs and JUnit remain in
`.tmp/daily-main-fixed/`; the original five-failure run remains in
`.tmp/daily-main/`. Failure-only SQLite metadata reporting did not alter
product transactions or retry tests.

The final documentation/anchor merge receives its postmerge run. Its exact
head and result are kept in the [final verification record](https://github.com/karolswdev/HoldSpeak/pull/1244#issuecomment-6239495252)
and the proof tree's `.tmp/daily-final/main-full-state.json`, JUnit and logs.
This avoids treating the previous one-failure run as green.

The original recall-lock case passed in the follow-up full run; its earlier
cause remains unknown and open. Owner aesthetic acceptance and live provider/
native behavior remain separate. The three requested faces are built, merged
and available on the local Desk; the broader visual inventory remains active.

The final metadata correction also updates the legacy saved-Decision case to
the actual Background fold. It checks both the heading and saved body, with
case-correct absence of empty Consequences. Three scoped schema/source checks
pass after three collected. Real graph walks pass at1440 and393; root inspected
both after shots in `.tmp/daily-main/decision-phase8-1440/20261017T192654Z-case.p8.decision_heads.hidden-astra-1440/`
and `.tmp/daily-main/decision-phase8-393/20261017T192715Z-case.p8.decision_heads.hidden-astra-393/`.
Ordinary documentation quick passes109 desktop/phone sweep cases and17 canon
checks; the final case-only metadata adjustment has its separate scoped checks
and actual walks. The unchanged product bundle remains `22aa76d6327046a1`.
