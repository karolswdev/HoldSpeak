# Decision, Ask and Thread — delivery record

The owner's priority is how daily work looks, feels and operates. This batch rebuilds the composition of the three named faces with the existing Workbench components.

## Result

- **New decision:** a wider, warm-paper writing surface leads the window. Context and Consequences are folds that retain drafts. The creation prompt names the decision and uses Create. Done remains in the footer on a phone.
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

Independent integrated advisory review: RATIFY, recorded in `INTEGRATED-REVIEW.md`. Merge, normal local delivery and formal postmerge review follow. Full-main runs after merge in the separate proof worktree.
