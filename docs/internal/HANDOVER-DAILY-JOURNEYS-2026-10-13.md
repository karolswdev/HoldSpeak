# Daily journeys — 2026-10-13

PR: [#1198](https://github.com/karolswdev/HoldSpeak/pull/1198).
Branch: `feat/delight-daily-journeys`. Base: `8d6ee083d` (#1197).
One combined PR at the owner's request. Builders: Luna workers; integration
and verification: Sol. This extends the October 13 designs and the owner's
**Inside Meetings, with Back** decision. Merge follows the October 12 fast
cycle in `CLAUDE.md`; this record is not an owner usability verdict or a
Muad'Dib check.

## Jobs changed

- **Prep → Record:** the linked Next 1:1 offers Record meeting as its primary
  action. The existing capture route validates and carries the calendar event
  key into the session. Private People notes and agendas stay in People.
  Stale context gets an explicit refusal. Refused and overlapping starts clear
  pending calendar, title, and tags so another recording cannot inherit them.
  An owner's ordinary idle title/tags still work.
- **Outcomes → Work:** correct text, owner, and date in a prefilled inline
  well; Confirm writes them together. A durable reread supplies the accepted
  row and its Follow-through destination. A failed reread leaves the successful
  write visible with Retry. More is the shared menu, with transcript and
  destination actions. People destinations come from the actual Door projection
  by action identity; ambiguous names are not guessed. Saved records show one
  review fact instead of duplicate identity and static progress steps.
  Changed drafts preview their values after Close edit. Confirm all cannot
  bypass pending corrections; individual Confirm commits them first. Blank
  task text or clearing a populated owner/date cannot silently restore the
  original values through the existing confirm contract.
- **Note → Selected text → Task / Ask:** the shared editor exposes its actual
  selection. Task starts with that passage and keeps the canonical note source.
  Ask shows a removable quote, preserves the unsent question, and sends the
  same quote with the question. Save precedes each handoff; stale selections
  clear after edits. Project continues to link the whole note. Ask opens at a
  useful default size, keeps saved geometry, offers Back to note and openable
  context, and omits the empty traffic card.
- **Keep place:** hosted surfaces save scroll by window and scope. Restoration
  waits for content, yields to the owner's input, and does not jump again on
  refresh. Existing record selection and draft persistence remain authoritative.
- **Week readiness:** retained meeting rows no longer make a pending detail
  refresh look complete. The existing reading marker follows current-generation
  requests while keeping the visible row and transcript fold in place.

The settled direction and production-component canvas are in
[DESIGN-daily-journeys.md](philo/phase-17/DESIGN-daily-journeys.md).
The canvas is synthetic design material, not product or owner evidence.

## Verification

Final integrated quick check: **GREEN** (`.tmp/delight/quick-r5.log`):
3,508 related web tests, 1,302 affected Python tests, 106 desk sweep checks
(3 existing known reds xfailed), and 15 canon guards passed. Final typecheck
passed. Source was quiet for this run; the temporary Week instrumentation was
removed. All runs used the machine lock and isolated HOME; Vitest used two
workers. The full suite remains the postmerge watcher’s job.
Focused logs, all under `.tmp/delight/` in the retained worktree:

- `quick-r1-final/run2.log`: 114 Python tests passed, including actual
  `_start_meeting` refusal and overlapping scheduler metadata cases.
- `quick-r1-final/web-collect.log`: 43 People/recording tests passed.
- `meeting-refresh202.log`: 9 record freshness tests passed; identity checks
  now use the owning window title instead of the removed body duplicate.
- `place-run.log`: 11 scroll/place tests passed.
- `rig-predicates.log`: 31 graph predicate tests passed. The mixed `all_of`
  input-value selector now reads the input instead of an earlier presence
  selector. The original apparent lost Prep draft was a verifier defect.
- `outcomes-layout-typecheck-unit.log`: typecheck and 17 backend Outcomes
  tests passed. The integrated check also covers all changed web tests.
- `outcomes-bulk-reread2.log`: 25 focused web tests passed, including
  closed-edit preview, blocked bulk acceptance, blank-field handling, exact
  per-row confirmation fields, durable values replacing the draft, and a
  successful bulk write whose failed reread leaves Retry instead of REFUSED.
- `typecheck-ship2.log`: final web typecheck passed.
- `week-readiness-run.log` / `week-readiness-sweep.log`: 5 focused web tests
  and both Week widths passed. The integrated run includes the strengthened
  test that awaits stale completion and then releases current reads one by one.
- `generate-final.log`: API/OpenAPI/graph/capability generation and architecture
  validation passed (154 architecture records). No owner-observed release
  claim was promoted.
- `canvas-shots.log`: six production-component canvas captures at 1440/393;
  scripts checked browser errors and waited for the sections to finish drawing.

Real isolated hub walks are declared in
[atlas-delight.json](philo/graph/atlas-delight.json):

| Case | Observed result | Retained directories below `.tmp/delight/walks/` |
|---|---|---|
| `case.delight.note.task` | Keyboard-selected second line becomes the exact task text and canonical note source after UI Add | `selected-task-1440`, `selected-task-393` |
| `case.delight.note.ask` | Selected quote, canonical note, and unsent question are visible together; no inference claimed | `selected-ask-1440-r2`, `selected-ask-393-final` |
| `case.delight.prep.draft` | Exact linked person and unsent agenda remain after reload | `prep-draft-1440-final-r2`, `prep-draft-393-final` |
| `case.delight.prep.refusal` | Real recorder refusal keeps the agenda and shows NO RECORDER ON THIS HUB | `prep-refusal-1440-final`, `prep-refusal-393-final` |
| `case.delight.outcomes.confirm` | Real import and summary producer; UI Edit/Confirm writes exactly one accepted action with corrected text, Me, and 2026-10-20 | `outcomes-confirm-1440-ship`, `outcomes-confirm-393-ship` |

Observations retain protocol readings, provenance, and before/after shots.
The graph rig removes its temporary DB on cleanup; there is no retained DB
snapshot. Intermediate failures remain in scratch, including obsolete UI
selectors and one producer schema-lock contention before the passing Prep
rerun. The first integrated run exposed stale assertions and two test fixture
isolation defects, all fixed. The second completed 3,505 web tests but stopped
because the orchestrator named a nonexistent extra test file; the final run
uses `tests/unit/test_product_copy.py`.
The third and fourth integrated runs passed their web (3,505 / 3,506), 1,302
Python, and 15 canon checks but caught intermittent Week stillness failures
(166 / 118 px). Six focused
Week checks did not reproduce it. The investigation proved a separate
retained-detail refresh readiness gap and added the focused regression/fix
above. The precise cause of that original movement remains unproven; it is
not claimed fixed merely because a later run passes.
Three bounded complete diagnostic sweeps each passed 106 checks with the same
3 expected xfails. Their trace (`week-r4-trace.jsonl`) showed loaded fonts,
unchanged window/body/preceding sections, and no pending marker during the
passing stillness watch. Instrumentation was removed before the final check.
A separate hermetic sweep of the unchanged #1197 product (`61cfec1e9`) also
passed 106 checks / 3 xfails (`week-baseline-r2.log`). That passing baseline
does not establish which revision introduced the intermittent movement.

## Limits and next work

- No real microphone, owner DB, Keychain, external calendar/delivery, or LAN
  model was exercised. Prep's graph rig has no recorder: refusal is evidence
  for honest feedback and draft retention, not successful audio capture.
- Outcomes uses a recorded loopback engine response at the actual provider
  boundary and the real import/summary/proposal producers. This proves the
  handoff; it does not establish real model quality or latency.
- Owner usability, phone hardware, and the reported 122-second Ask delay
  remain unobserved. Component and synthetic-hub checks do not settle them.
- Automatic extraction on Finish remains later work. The current intelligence
  queue owns real meeting identity and readiness. A subject-aware durable
  producer is needed; no fake meeting or direct background model call was added.
- The full main watcher tape and Astra's postmerge review remain due under the
  fast cycle. Existing desk sweep known reds remain unchanged.
