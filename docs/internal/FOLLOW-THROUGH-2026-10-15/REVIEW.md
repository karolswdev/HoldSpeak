# Follow-through final source review — 2026-10-15

**DRAFT · UNCHECKED — awaiting Muad'Dib. Root owns release.**

Worktree `/Users/karol/dev/tools/wt-follow-through-20261015`; base
`420a0eb28`. One bounded initial source review and one focused recheck of the
frozen corrections. Read `TWO-BRAINS.md` first, then the current fast cycle,
Constitution/UX canon, settled design, build reports, changed product files
and relevant changed tests. This review ran no tests, build, browser, or git
mutation and changed only this report.

VERDICT: RATIFY

FINDINGS:

1. **P2 · fixed — record origin confused a decision id with a meeting id.**
   The initial Decisions reader made the top-level record origin an “Open
   meeting” action. The producer stores `decision.id` in that `source_id`
   (`holdspeak/services/decision_record_service.py:112`); the actual meeting
   is separate evidence (`:126`). The frozen fix uses the existing
   `decisionRecordSourceRef` mapper at
   `web/src/desk/pullouts/views/DecisionsView.tsx:484` and opens that ref as
   “Open decision” at `:503`. Evidence meeting actions retain their own
   identity at `:307` and `:514`. The regression at
   `web/src/desk/pullouts/views/DecisionsView.test.tsx:194` checks both refs
   and rejects `meeting:<decision-id>`. **Tenets 3/7; UX A.11.**

2. **P2 · fixed — late Brief failures hid the original Retry subject.**
   Clearing a receipt when selecting a new person/item did not stop an
   earlier agenda or shelf refusal from seating its unnamed Retry later.
   The frozen fix names and captures the original person/item in each
   attempt (`web/src/desk/pullouts/views/BriefView.tsx:333`, `:358`) and
   keeps the latest selected subject visible alongside any failure
   (`:274`, `:603`). It preserves the original request's Retry target.
   The two real hook regression cases at
   `web/src/desk/pullouts/views/BriefView.test.tsx:311` and `:342` cover late
   agenda/shelf refusal, changed/cleared selection, and exact original
   Retry. Local wrapping is at
   `web/src/desk/pullouts/attention-records.css:92`.
   **Tenets 3/7.**

3. **P2 · fixed in source — root observed an offscreen Follow write refusal.**
   Root's production walk found the board-top date refusal above the
   scrolled editor; reported shot:
   `.tmp/follow-through/after-retry-1440/date-refused-newer-draft.png`.
   The frozen correction scrolls the failure notice nearest only when a
   new `writeError` is seated
   (`web/src/desk/pullouts/views/FollowThroughView.tsx:180`). The notice
   names the failed verb, task, and reason at `:283`. The strengthened
   test at `web/src/desk/pullouts/views/FollowThroughView.test.tsx:442`
   checks the actual notice target, one scroll, no quiet-refresh scroll,
   retained newer draft, and exact rejected-date Retry. Root owns the
   subsequent live re-observation. **Tenets 3/7; UX A.10.**

No other confirmed defect in the reviewed backend or frozen Follow face.
Missing-loop Snooze is inserted and updated in the existing transaction
(`holdspeak/services/follow_through_service.py:514`); source identity
suppresses action/decision mirrors across filters (`:168`, `:176`, `:237`).
The Follow face keeps People receipts in memory, discards legacy persisted
People receipts, retains exact failed writes through empty states, preserves
newer drafts, and dispatches loop ids through the cadence writers.
Addressed row scrolling/focus comes from the existing library row
(`web/src/desk/surface/Surface.tsx:887`).

CONDITIONS:

No open source condition after the focused fix recheck. Root's quick check,
live proof, and release disposition remain root-owned work.

Saved proof read independently, without rerunning it:

- `.tmp/follow-through/backend-enrichment-collect.log`: 44 collected;
  `backend-enrichment-green.log`: 44 passed.
- `.tmp/follow-through/neighbors-custody-collect.log`: the origin and two
  late-receipt regressions are named;
  `neighbors-custody-green.log`: 6 files, 60 passed.
- `.tmp/follow-through/follow-collect.log`: the five-file scope is named;
  `follow-green-notice.log`: 5 files, 46 passed. This log includes a
  non-failing jsdom canvas warning from DeskIcon.

MISSED:

Ranked by cost to the owner: an unnamed Retry could act on an earlier
person/item; the record origin could open the wrong object; a refusal could
remain outside the current scroll position. All three have bounded fixes
above. No framework expansion is requested.

TUESDAY:

The source supports reading the full task, owner and date and taking one named action; root and the owner own the live 1440/393 judgment.

UNKNOWN:

No independent runtime, geometry, pointer reach, keyboard/mobile date entry,
browser-console, real encrypted-store, microphone, clipboard, external-send,
owner DB, quick-check, merge, or deployment verification. The root-reported
offscreen-error shot was cited as root evidence and was not independently
opened by this reviewer. Controlled web responses prove face dispatch and
rendered state; the saved passing logs do not establish those live facts.
