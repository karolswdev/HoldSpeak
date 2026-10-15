# Workbench pickers — independent finished source review

DRAFT — UNCHECKED, awaiting Muad'Dib. This is the bounded source review
requested by the root orchestrator, not Muad'Dib's check or the owner's
acceptance. Base `91275406b`, worktree
`/Users/karol/dev/tools/wt-workbench-pickers-20261014`.

VERDICT: RATIFY

FINDINGS:

1. **P2 — ordinary parent renders dismiss the open picker — FIXED.** The original
   `web/src/components/signal/WorkbenchSelect.tsx:126` unconditionally
   closes the popup when `children` identity changes. CycleGadget creates
   new option children each render at
   `web/src/desk/surface/gadgets.tsx:188`; therefore unchanged logical
   options still cancelled an in-progress selection. Source reproduction:
   open Language with Enter, move the active row to Polish, then rerender
   the same CycleGadget with the same value and option data. The list
   disappears instead of preserving the active row. This can occur on a
   real Thread enum while unrelated thread updates rerender its ancestors:
   `web/src/desk/pullouts/ThreadPullout.tsx:1201` subscribes to buffers,
   `web/src/desk/threads.ts:825` changes that object for each delta, and
   the non-memoized message/tool/form chain reaches the enum at
   `web/src/desk/pullouts/ThreadPullout.tsx:190`. Tenet 3: picking a value
   should complete without repeated reopening. The one fix recheck finds
   the semantic native snapshot comparison at
   `web/src/components/signal/WorkbenchSelect.tsx:126` preserves the popup
   when selected index and option values/labels/disabled state are unchanged;
   actual changes or a disabled/non-dropdown owner still close it. The
   regression at
   `web/src/components/signal/WorkbenchSelect.test.tsx:177` preserves the
   Polish active row, English saved choice and zero writes after an
   equivalent rerender. Its logged original failure was a missing listbox
   (`kit-lifecycle-red.log`: 1 failed, 40 passed); the final focused run
   reports 41 passed (`kit-lifecycle-green.log`). No open source finding
   remains.

CONDITIONS:

- None for the reviewed source. Production verification, the owner's live
  acceptance and Muad'Dib's check remain with their named owners; this
  source verdict does not assert those outcomes.

MISSED:

- The original stale-roster test reused a stable JSX constant. It covered
  value changes but missed the ordinary fresh option arrays produced by
  CycleGadget consumers. This was the only concrete source failure found.
- The moved Button and native picker are genuine library implementations.
  The exact path additions at `scripts/ux_canon_scan.py:558` and
  `scripts/ux_canon_scan.py:739` preserve the existing policy; the new
  `tests/unit/test_ux_canon_ratchet.py:227` cases reject matching face
  basenames and prefix/suffix lookalikes. No ceiling changed.

TUESDAY: Source supports the existing picker jobs and writers in one
Workbench component, including uninterrupted choices across ordinary renders.

UNKNOWN:

- This review ran no tests, build, browser, install, or owner-state action.
  Native popup suppression, touch/cancel behavior, live hit ownership,
  visual viewport placement, assistive technology and actual saved-value
  behavior require the root's production walks; source cannot prove them.
- I read the full tracked diff and the four new kit files, the task brief,
  adoption census, fast-cycle agreement and UX canon. The active-source
  select search found only the shared native implementation and Interview's
  legacy Select consumer. This supports adoption coverage, not a live
  result for every face.
- I inspected proof logs rather than running them: final kit collection
  lists the 41 tests (`.tmp/workbench-pickers/kit-lifecycle-collect.log`);
  the final kit run reports 41 passing tests
  (`.tmp/workbench-pickers/kit-lifecycle-green.log`); adoption reports 65 passing
  tests (`.tmp/workbench-pickers/adoption-tests.log`); the focused scanner
  run reports 7 passing tests
  (`.tmp/workbench-pickers/kit-scanner-green.log`). Adoption and scanner
  runs predate the lifecycle fix; the root owns the combined quick check.

Review frozen after the one fix recheck. No product files were edited and
nothing was staged or committed by this reviewer.
