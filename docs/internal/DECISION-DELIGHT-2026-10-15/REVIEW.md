# Independent source review — Decision delight

2026-10-15. Base `c910cd580`; worktree `wt-decision-delight-20261015`.
Initial bounded review of the finished product and focused test changes,
followed by one focused source recheck of finding 1. Review cycle complete.
This is delegated source counsel for Astra, not a Muad'Dib check.
**UNCHECKED — awaiting Muad'Dib.**

VERDICT: RATIFY

FINDINGS:

1. **CLOSED — status Retry during body saving (low cost; Tenet 3 / UX-CANON
   A11).** The initial source had an enabled Retry whose handler returned
   while the body write was pending. The focused fix at
   `web/src/desk/pullouts/DecisionPullout.tsx:152` now uses
   `disabled={savingStatus || savingDecision}`, matching the status choice
   and writer guard. The adjusted existing regression at
   `web/src/desk/__tests__/decision.app.test.tsx:137` creates a real refused
   status response, starts a delayed body save, checks the disabled Retry,
   and checks that pressing it cannot add a status write. Read run tails:
   `.tmp/decision-delight/decision-status-retry-red.log` failed this disabled
   assertion (1 failed / 64 passed); the corresponding
   `decision-status-retry-green.log` passed all 65 tests in the same five
   files. These were worker runs, not runs by this reviewer.

CONDITIONS:

None remain from this bounded source review. Root's runtime and release
verification remains outside this verdict.

MISSED:

Finding 1 was the only omission found and is closed. The ordinary-preview version signature at
`web/src/desk/pullouts/DecisionPullout.tsx:76` covers the actual renderer's
fields (`holdspeak/services/document_sources.py:359`). The boolean save,
synchronous duplicate-write guard and draft-version comparison at
`web/src/desk/pullouts/DecisionPullout.tsx:86` retain newer local fields;
the existing store Retry captures the original patch at
`web/src/desk/store/dataSlice.ts:639`, and the local failure checks its
subject at `web/src/desk/pullouts/DecisionPullout.tsx:164`.

The folded host retains one sends read, failed-read Retry and nonzero
discovery at `web/src/desk/surface/send/SendWell.tsx:859`; its held-prefix
check opens the existing well and blocks Hide. The settled Edit/Back
unmount boundary is unchanged. Prepared preview remains derived from the
stored row at `web/src/desk/surface/send/SendWell.tsx:696`; ordinary preview
alone depends on `doc.version` at
`web/src/desk/surface/send/SendWell.tsx:527`.

The divider uses actual participant ranks at
`web/src/desk/compositor/CompositorLayer.tsx:94` and mounts after the window
hosts at `web/src/desk/DeskApp.tsx:300`. Its drag/key handlers, constraints,
mode suppression and shared geometry are unchanged. The new component
test derives real mounted ranks and checks real keyboard store writes at
`web/src/desk/compositor/__tests__/CompositorLayer.test.tsx:39`.

TUESDAY:

The source supports reading once, opening Send deliberately and keeping
later draft input, with consistent pending controls.

UNKNOWN:

Source review only. No tests, typecheck, build, browser, live API operation
or git mutation was performed by this reviewer. Worker build records were
read, and the focused finding-1 red/green log tails were inspected; no
worker test was rerun here.
Root owns actual 1440/393 shots, refused-save and held-remount behavior on
glass, actual divider paint/pointer ownership and exposed drag/key behavior,
quick check, and release. This report does not establish the owner's live
verdict or a Muad'Dib check.
