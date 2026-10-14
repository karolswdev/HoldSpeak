# Daily work repair canvas

DRAFT — HOLD FOR SHIP. UNCHECKED — awaiting Muad'Dib.

Owner-approved composition from `docs/internal/SURFACE-REPAIR-2026-10-14.md`.
The small Meeting, Week, Ask and Needs artboards use production components and
synthetic content. Run the existing Vite canvas config on port 24182; select an
artboard with `?face=meeting`, `week`, `ask` or `needs`.

The Tuesday job: review the saved work, see its real source, ask about it, and
act on the next item without opening optional tools first. This follows Tenets
2, 3, 4, 5 and 7. No service or authority semantics changed.

## Delivered composition

- Meeting source menus require a stored integer segment in transcript bounds;
  zero remains valid. The ledger says Decisions, and an unsupported proposal
  with no source says Not in the transcript.
- Meetings keeps its existing record and Back. Send opens on request and
  receives focus when its reads finish. More holds transcript, Decide, project
  filing, exports and Park. The phone footer is Send and More.
- Week rows remain closed, carry a wrapping summary excerpt, and open the
  existing meeting. A failed import retains its plain cause and Open.
- Ask leads with the question, engine and named source. Add notes holds the
  existing optional pickers. The draft-replacing lens strip is unmounted;
  its lens definitions and default run semantics remain in the existing Ask
  service. The budget appears only over limit. The false assignment footer is
  removed.
- Needs proposals show Confirm and More. One kind plate names each row. The
  redundant proposal state lamp is hidden; meaningful work and failure states
  remain. All replaces Ranked; coverage folds; one Checked receipt remains.

## Proof and limits

All commands used `.tmp/surface-audit/locked.py`, which holds
`scripts/test_lock.py`, isolates HOME and disables machine state. No owner hub,
DB, microphone, agent execution, model execution or Send dispatch was used.

- `.tmp/surface-audit/repair-work-unit.log`: six focused Vitest files,
  **90 passed**. Includes actual proposal menu cases for null, undefined,
  negative, out-of-range, fractional, string and valid-zero segment values.
- `.tmp/surface-audit/repair-work-week-send-fixed.log`: seven focused
  Week/meeting/Send Vitest files, **59 passed**. These runs overlap; the numbers
  are not a unique total. An initial old expanded-import-well expectation
  failed; its successor checks the closed row's retained cause and Open.
- `.tmp/surface-audit/repair-work/observations.json`: **24 final shots**, both
  1440 and 393, **no blocked state or browser error**. Existing desk-sweep clip,
  overlap and actual touch ownership probes reported no failures for those
  poses. It covers default Week, Needs and its More, Meeting and its More,
  Decide, requested Send, held real preview pending and ready, unsupported
  source menu, Ask and Add notes. `capture.py` reuses existing isolated fixture
  helpers; it is scratch evidence, not a new verification framework.
- `.tmp/surface-audit/repair-work-glass-collect.log`: exactly two retained
  meeting Send cases collected, `[1440]` and `[393]` of
  `TestOneMeetingOneWindow::test_a_meeting_with_a_summary_holds_still_while_its_send_preview_lands`.
- `.tmp/surface-audit/repair-work-glass.log`: the initial retained browser run
  **failed 2 cases** on its old standalone meeting-window selector, before
  reaching Send. The targeted case now opens `surface-meetings` with the
  meeting scope. `.tmp/surface-audit/repair-work-glass-fixed.log`: the corrected
  rerun **passed both cases**, including no Send before the held preview and
  focus inside the requested well when ready (8.07 seconds).
- `.tmp/surface-audit/repair-work-types.log`: type-check was blocked by the
  sibling Session test's invalid `exact` option; it reported no daily work
  error after the saved-summary field fix. Root owns the combined quick check.

Actual inference, Send dispatch, project filing, export, Park and proposal
writes remain unobserved on glass. Existing focused unit tests cover their
unchanged wiring. Empty, incomplete coverage, waiting and muted Needs states
retain their existing tests and were not claimed as captured. No staging,
commit or push was performed.
