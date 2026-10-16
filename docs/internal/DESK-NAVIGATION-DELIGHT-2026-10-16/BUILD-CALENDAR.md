# Calendar snapshot review

DRAFT — root canvas GO received. UNCHECKED — awaiting Muad'Dib.

Tuesday: read each event, correct it without losing focus, and confirm the same
review after a refused save. Tenets 3, 4 and 5; Constitution VI and VII.

Observed by root at 1440 and 393 on build `0cdc79ec2f8a34ae`: typing ` ready`
into the first event title leaves only the first space and loses focus. At 393
the mic takes the title field's entire visible width. The current Save failure
also discards the review surface and draft. Evidence: `.tmp/navigation/after-1440/`
and `.tmp/navigation/after-393/calendar-snapshot-populated.png`.

Settled direction: existing SurfaceSection, SurfaceLedgerRow, StringGadget,
CycleGadget, StateChip, SurfaceFooter and Button. Full width title and location;
day and readable time fields in a grid which stacks on the phone. Local row IDs
are created once and removed with the event. No editable value or shifted index
is a React key. Confirm keeps the review mounted, disables editing while pending,
and guards duplicate presses. A refused Save keeps anchor and events, with Retry
on the same reviewed payload. The accepted receipt names the returned source and
event count. No provider, OCR, voice or backend claim.

Root read the 1440 and 393 review/refusal directions and the phone pending
direction; GO received for this bounded pass. Remove retains the existing kit
two-step `Remove` / `Remove?`. The pending fieldset also disables the inherited
voice Buttons. The title's text width is 532 px at 1440 and 269 px at 393.

Owned paths: CalendarSnapshotReviewCore.tsx, its named test, face CSS, this story,
and canvas-calendar/. All other lanes and shared components are out of scope.

Validation budget: collect, then run only
`web/src/pages/cores/__tests__/CalendarSnapshotReviewCore.test.tsx` through
`.tmp/navigation/locked.py` with isolated HOME. Root owns production browser
observations and the isolated real ICS writer walk. Hold for SHIP; no staging or
commit.

Worker result: HOLD for SHIP. The named test file collected 17 cases and passed
17/17 under the machine lock and an isolated HOME. Logs:
`.tmp/navigation/calendar-test-collect.log` and
`.tmp/navigation/calendar-test-run.log` (2.35 s). Cases cover all text-field
keystrokes, weekday focus, retained nodes after two-step removal, one in-flight
Confirm, pending field/mic disablement, refusal with the exact Retry payload,
network rejection with a revised draft, empty-draft disablement and honest
accepted source/count. No wider suite ran. Root's production shots and isolated
real writer walk remain the evidence for live behavior.

Mechanical correction after root's quick check: the layout rewrite dropped
the existing constant `key="start"` and `key="end"` on the structured HH:MM
fields. The canon scanner binds its justified clock mic exceptions to those
field identities. Both constants are restored on the same StringGadgets; the
HH:MM placeholders, mic opt-outs and review behavior remain. No scanner,
allowlist or ceiling changes. The same 17-case file is collected and rerun;
root owns the canon and full quick check rerun.

Correction result: collected 17, passed 17/17 in 2.39 s, under the lock and an
isolated HOME. Logs: `.tmp/navigation/calendar-clock-keys-collect.log` and
`.tmp/navigation/calendar-clock-keys-run.log`. Scoped diff check clean. Frozen
again, HOLD for SHIP.

Live phone amendment, settled by root: the first refused Save shot at
`.tmp/navigation/after-release-393/calendar-snapshot-refused-keeps-review.png`
kept Retry visible while the reason had scrolled above the events. The same
refusal StateChip/reason now occupies SurfaceFooter's wrapping receipt beside
Retry; the redundant body Save section is removed. The existing receipt and
token `data-wrap` contracts keep long reasons readable. No change to pending,
payload, Retry or row identity. A focused footer-composition case joins the
same Calendar file; root authorized only that file and the canon ratchet
preflight, under the lock with an isolated HOME. Root owns the final built
phone observation and real ICS writer walk.

Footer amendment result: Calendar collected 18 and passed 18/18 in 2.47 s;
canon ratchet collected 7 and passed 7/7 in 2.33 s. Both ran under the lock
with an isolated HOME. Logs: `.tmp/navigation/calendar-footer-{collect,run}.log`
and `.tmp/navigation/calendar-footer-canon-{collect,run}.log`. Scoped diff
check clean. No scanner or ceiling edits. Frozen, HOLD for SHIP.
