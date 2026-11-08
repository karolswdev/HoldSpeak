# Parked pull-out bodies

- `MeetingPullout.tsx` — the meeting card (HS-117-15). PHILO-17 (owner
  2026-10-10, "A meeting opens in one window"): the meeting window
  `pullout:meeting:<id>` shows the whole record (`MeetingWindow.tsx`), so
  this card body is parked. Not compiled (`tsconfig.json` excludes
  `_parked`).

## Betterment daily D4: Today is one page (2026-10-18)

Today has no wings. These are parked, not compiled (`tsconfig.json` excludes
`_parked`) and not run (vitest excludes `**/_parked/**`):

- `FollowThroughView.tsx` (+ its test): the Follow-through wing. Its rows and
  verbs are the Needs-you rows; `openIntelligence({view: "follow-through"})`
  opens the Needs-you window. The `follow_through.*` MCP tools stay.
- `BriefWing.tsx`: the Brief wing (Generate, Refresh, Acknowledge, Defer,
  the PEOPLE overlay). Today's Since-yesterday fold (`views/BriefView.tsx`)
  replaces it; the brief is made when Today opens. The shelf data stays.
- The wing tests: `BriefView.test.tsx`, `briefOutcome.philo602r2.test.tsx`,
  `IntelligenceTruth.test.tsx` (the drill filter and brief triage),
  `IntelligenceWalk.test.tsx` (the segmented header).

- `ThreadPullout.tsx` and `thread-pullout.css` — the Thread window
  (HS-151-05). Betterment Q4 ("One Ask window", DECISIONS #14): Ask and
  Thread are one window; every Ask is kept as a thread and every thread opens
  in Ask (`openPullout` sends `thread:<id>` to `openAskThread`). The window's
  modes, tool rows, annotations and call chip are parked with it; its tests
  are in `_parked/__tests__/` (not collected). Not compiled.
- `threadWindowName.test.tsx` (from `desk/__tests__/`): the Thread window's title and Dock chip naming.

## One decision face (2026-11-08)

A decision has one face: its record in the Decisions window reader
(`views/DecisionsView.tsx`). Every decision ref (`decision:<id>`,
`desk_decision:<id>`) and every open of a Desk decision (`openPullout`) opens
that record (`openDeskDecisionRecord` in `openObject.ts`); a restored
`pullout:decision:<id>` window opens the reader and closes itself
(`DecisionToReader.tsx`). Parked, not compiled, not run:

- `DecisionPullout.tsx` — the Decision pullout. Its verbs moved to the reader:
  Edit (the editor and its kept draft, `views/DeskDecisionEdit.tsx`), Accept,
  Retire, Copy, Dictate about this, Filed in, the "Accepted · N open" receipt.
- `decisionEdit.ts` — the edit request the reader sent to the pullout. The
  reader now edits in place.
- `__tests__/decisionPullout.app.test.tsx`, `__tests__/philo301DecisionFace.test.tsx`,
  `__tests__/philo301DecisionNoLoss.test.tsx`,
  `__tests__/philo605DecisionBodyDiagnosis.test.tsx` — the pullout's cases as
  they were. The live cases are in `desk/__tests__/decision.app.test.tsx`.
