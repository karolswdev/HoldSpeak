# Decision, Ask and Thread — daily experience

Owner direction: improve how these three faces look, feel and operate. Backend reliability alone did not satisfy this request.

Working tree: `/Users/karol/dev/tools/wt-daily-experience-20261017`, branch `feat/daily-experience-20261017`, base `7f17b5858`.

Tuesday question: can the owner write a decision, ask about selected material, then continue a thread without wrestling stacked controls or losing the reading position?

Direction: one connected Workbench visual grammar, content-led paper surfaces, compact steel context and action areas, clear primary action, useful advanced functions within reach. No new component dialect. New decision must make the decision text primary. Ask and Thread must have generous reading space and clear composers. Preserve existing draft retention, retries, source identity and route disclosure.

Workers first diagnose the named sources and provide concrete design changes. Root settles the actual-library canvas before product implementation. No worker stages or commits; HOLD FOR SHIP. Root integrates and judges real desktop and phone screenshots. Current fast cycle applies. Owner acceptance remains distinct from our visual review.

## Verification

Only scoped checks named in worker briefs, all serialized with `scripts/test_lock.py`, isolated HOME and private keystores, no provider keys or native effects. Never `tests/e2e/test_metal.py`. One graph case per invocation, shots at 1440 and 393. Quick check before merge, normal idle delivery, formal postmerge review and full-main followup.

## Settled composition — 2026-10-17

Root inspected actual-library canvas at `.tmp/daily/canvas/decision-1440.png`, `ask-1440.png`, `thread-393.png` before implementation. Direction chosen for build; owner has not accepted it. Preserve the Workbench title bar, square controls, steel support areas and warm document paper. Use current tokens, not hard-coded canvas colors. Actual app verification must enforce the existing 44px phone targets.

- Decision: 680px default window width, compact status/facts row, Decision first in a generous paper editor with focus. Context and Consequences stay mounted inside library folds, initially open when populated. All writing uses readable proportional body type. Saved view keeps the same order. Done/Cancel lead editing; retain Copy/Dictate as existing secondary capabilities. Name-first creation remains; label its create action Create and make the title prompt visibly specific to the decision. No record on abandon.
- Ask: 740px wide stable 620px default window, paper question/answer reading area, selected source titles visible above writing. No empty filler or unrelated No projects row. Sources and instructions remain available through existing folds; show selected identities even when folded. After an answer, Edit question reopens the existing question and retains the answer until the next explicit Ask; do not imply conversational memory the request does not carry. Keep stays available. Scroll to the beginning of a new answer once; do not drag the reader to its end. Reserve a bounded composer outside the answer scroll region, with visible source/engine information and reachable Ask.
- Thread: 740px default width, compact top strip with Call visible and Thread details for Rename, assignment and usage. Paper transcript uses role labels above text (no 76px wasted column), consistent readable type and restrained separators. Keep as note visible on completed answers; other routine actions under More. Error/retry/held tool controls stay visible. Sent source identities remain inspectable. Compact two-row growing composer with Sources and Commands buttons opening existing pickers, mic and Send/Stop nearby. Mode options remain one clear disclosure away, with selected mode named. Enter while streaming must not accidentally stop a run while the owner edits a draft: Stop stays explicit, Enter edits normally until sending is possible. Preserve normal Enter/Shift+Enter and IME behavior.

Ownership: decision worker owns DecisionPullout, decision-only attention-records.css, palette decision entry in DeskToolShelf/chrome-menus.css and PULLOUT_SIZE decision/thread dimensions in pullouts/size.ts. Ask worker owns AskPanel/ask-panel.css and shared surface/patterns/conversation.css for the agreed role-above-paper grammar; no shared picker API changes unless root authorizes. Thread worker owns ThreadPullout/thread-pullout.css/ThreadComposer and scoped tests. Root owns this document, canvas, integration walkthrough and release records.

## Loaded Ask refinement

The real Note-to-Ask walk found that global desktop icon selection can drop a source while its Note window remains open. The handoff now carries the saved canonical Note and a body-valid quote. A newer handoff opens the composer and an older request cannot hide it on completion; answer sources and Keep retain the submitted snapshot.

The phone walk also exposed a quote crowding out Ask after Edit question. Selected text uses the library fold, open on the initial handoff and collapsed after sending. Context scrolls within a bounded area; the question has an 80px minimum and the action strip stays reachable. The Ask body explicitly establishes the same named surface container used by the other window interiors.
