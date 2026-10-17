# Decision, Ask and Thread — finish the work and return to it

The owner asked for more than functional screens. This pass makes the three named surfaces easier to read and improves the transitions after writing and saving. [Settled actual-library direction](DESIGN.md).

- Decision is one paper document, with compact facts, visible Cancel and explicit Save. Unfinished fields survive closing and reload. An old Save acknowledgement only clears fields it actually saved; newer writing stays. The repeated Send label is removed from the shared fold.
- Ask puts the answer first, with the exact Question, Sources and Run details available in folds. The writer precedes one bounded context well. Keep opens the confirmed artifact and preserves Ask behind it; Open saved answer returns to that same object without another save. A late reply cannot hide newer typing. Escape belongs to the foreground window.
- Thread has a searchable, bounded command picker with single-line choices, real Arrow/Enter selection and Escape return. Source and argument choices use the same compact well. Keep and successful Retry show the confirmed note/artifact opener while retaining the conversation draft.

## Verification

Implementation tree: `wt-daily-delight-20261017`, base `ebd2387b1`. Initial runtime UI build `b1e0bdd242f3f719`; final runtime-walk build `b7a721be7286af6a` adds the visible Thread search cues and smaller result wells, plus two TypeScript test-option corrections. Thread walks repeat on this build. The release build is `f5317bcd54bf056e`; subsequent changes are route tests/comments and JSX formatting only. Its source digest matches exactly. All tests, builds and walks use the machine lock and private HOME/keys; no owner DB/provider/native actions. The existing live hub and Jupiter preview remain separate.

Focused runs: Decision/Send81, Ask72, Thread126 (279 total), all passed; logs `.tmp/delight/{decision-tests,ask-route-tests,thread-tests}.log`. Thread tests now use actual library controls. Atlas schema/anchors747 passed (`atlas-final.log`); the changed Background render anchor and prior Decision Save walk label are updated. TypeScript passes (`typecheck-final.log`); ordinary quick is GREEN:4,167 related web tests (414 files),109 desktop/phone sweep cases and17 canon guards. Logs are `.tmp/delight/quick-final.log` and `quick-logs/`.

The isolated graph rig uses `atlas-daily-delight.json`, one case per invocation at1440 and393. Cases cover Decision create/save and close/reopen/reload/save; Ask answer/edit with selected Note passage and Keep/exact-artifact/return/reopen; Thread command filtering/keyboard/focus and Keep/exact-note/return. Ask uses a declared provider reply replay, not a live inference claim. Extra journey proof records actual POST return ids, exact opened window ids, retained input/context, and the Decision row before and after Save. Root inspects the actual screenshots and critical control pointer ownership.

The shipped baseline reproduces Decision draft loss on close/reopen (`baseline-retention2`); the draft never reappears. A first baseline harness attempt used the citation prefix instead of the arrival prefix and was corrected. Later harness corrections distinguish controls below a scrolling document from fixed actions, and accept the routes' actual201 creation status. These are recorded as harness corrections, not product defects or unqualified green attempts.

Independent source review found and closed two defects before delivery: background Ask's global Escape listener and missing Thread continuation after receipt Retry. The recheck ratified both fixes and inspected Ask phone/desktop screenshots; root owns the complete runtime judgement. This is not owner aesthetic acceptance.

## Outstanding work retained

The previous merged full run at`ebd2387b1` had16,698 passes and one Room review phone failure (`summary.phase_results` absent before the UI press). Its exact paired rerun passed; the cause remains unknown. The earlier People503 in quick/sweep is also unresolved despite a later green quick. Both remain tracked in the [prior exact verification](https://github.com/karolswdev/HoldSpeak/pull/1244#issuecomment-6239495252). This UI change does not claim to fix either.

Formal postmerge review, exact merged full-suite result and idle local delivery are recorded in the PR and linked from Status. Physical phone hardware, real provider output and native voice capture are outside these isolated UI proofs.

## Completed runtime proof

All12 desktop/phone case invocations pass, including critical control pointer ownership. Root inspected Decision editing/reading, Ask answer/edit/return, Thread command search/last selection/arguments and settled saved-note return screenshots. `journey-proof.json` beside the relevant shots records the exact additional assertions. Custom screenshots wait for finite window animations before capture.

| Journey | 1440 observation directory | 393 observation directory |
| --- | --- | --- |
| decision-save | `.tmp/delight/decision-save-1440/20261017T233336Z-case.delight.decision.save-astra-1440` | `.tmp/delight/decision-save-393/20261017T233328Z-case.delight.decision.save-astra-393` |
| decision-retain | `.tmp/delight/decision-retain-1440/20261017T233356Z-case.delight.decision.retain-astra-1440` | `.tmp/delight/decision-retain-393/20261017T233346Z-case.delight.decision.retain-astra-393` |
| ask-passage | `.tmp/delight/ask-passage-1440/20261017T233450Z-case.delight.ask.passage-astra-1440` | `.tmp/delight/ask-passage-393/20261017T233434Z-case.delight.ask.passage-astra-393` |
| ask-keep | `.tmp/delight/ask-keep-1440/20261017T233636Z-case.delight.ask.keep-astra-1440` | `.tmp/delight/ask-keep-393/20261017T233626Z-case.delight.ask.keep-astra-393` |
| thread-commands | `.tmp/delight/thread-commands-1440/20261017T233909Z-case.delight.thread.commands-astra-1440` | `.tmp/delight/thread-commands-393/20261017T233900Z-case.delight.thread.commands-astra-393` |
| thread-keep | `.tmp/delight/thread-keep-1440/20261017T233929Z-case.delight.thread.keep-astra-1440` | `.tmp/delight/thread-keep-393/20261017T233919Z-case.delight.thread.keep-astra-393` |

The first ordinary quick was RED: three Ask tests still expected the old full-route footer, and the raw-id scanner misread compact JSX map syntax as rendered ids. The route assertions now check the answer-first layout while retaining exact egress, provenance, refusal, fallback and elapsed-time checks. Multiline JSX removes the scanner false positive without changing controls or ceilings. The first logs are retained in `.tmp/delight/quick-first-logs/`; the isolated final ratchet has7 passes.
