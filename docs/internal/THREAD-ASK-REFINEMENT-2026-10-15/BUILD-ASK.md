# Ask lane

2026-10-15 · DRAFT · held for SHIP · no staging or commit

Built the settled direction in `AskPanel.tsx`, `ask-panel.css` and
`RailsPicker.tsx`. Root authorized the final bounded `GroundingSection.tsx`
caller label and budget visibility seam. Tests live in
`web/src/desk/__tests__/askPanelRunsOn.test.tsx` and
`web/src/desk/__tests__/askPanelExperience.test.tsx`. Root also authorized the
Ask prefix selector repair in `web/src/desk/__tests__/routeInFooter.test.tsx`.
No shared conversation CSS, Thread, notification or model behavior edits.
Root later authorized the one artifact source allowlist repair in
`holdspeak/db/plugins.py`; its real database proof is recorded below.

Ask now pins the question with its selected passage, lens, copied desk
context, built grounding and rails wire, and Keep context. Retry sends that
snapshot; a fresh Ask builds a new one. Keep records the sent instruction
and its original context. A newer durable draft stays untouched. Close,
Cancel, Escape and unmount abort this view's HTTP wait and guard late
responses. This does not claim that the backend run stopped.

The face imports the shared conversation treatment, uses the labeled
PadGadget with one external mic and the existing `desk-ask` durable scope,
and puts Copy
by the answer and Keep/Bin only in the footer. The single failure line owns
its recovery action. Keep shows the library busy state until its writer
returns an artifact id; a failed Keep can be tried again. Add notes and
Rails use their existing native folds without an outer disclosure or normal
budget counters. Optional GroundingSection label/showBudget and RailsPicker
showBudget props preserve the default behavior of other callers. Rails rows
have one focusable CheckGadget and a non-focusable click band.

Fresh Ask uses the shell's existing fitContent mode, a 640px preferred width,
and 360px compose / 600px traffic CSS heights. Persisted owner geometry stays
authoritative through the shell's inline geometry; there are no custom
geometry writes.

## Focused proof

The commands use the root-provided lock and isolated HOME helper:

```text
.venv/bin/python .tmp/thread-ask/locked.py ask-route-list --web ./node_modules/.bin/vitest list src/desk/__tests__/askPanelRunsOn.test.tsx src/desk/__tests__/askPanelExperience.test.tsx src/desk/__tests__/routeInFooter.test.tsx --maxWorkers=2
.venv/bin/python .tmp/thread-ask/locked.py ask-route-after --web ./node_modules/.bin/vitest run src/desk/__tests__/askPanelRunsOn.test.tsx src/desk/__tests__/askPanelExperience.test.tsx src/desk/__tests__/routeInFooter.test.tsx --maxWorkers=2
```

Collection: `.tmp/thread-ask/ask-route-list.log` — exit 0, 33 tests listed.
Run: `.tmp/thread-ask/ask-route-after.log` — exit 0, final tail:

```text
Test Files  3 passed (3)
     Tests  33 passed (33)
  Start at  22:42:27
  Duration  3.07s (transform 1.25s, setup 172ms, import 2.14s, tests 2.40s, environment 560ms)
```

The tests exercise exact Retry and Keep payloads after the question, selected
passage, selected desk source, resource grounding and rail choices change;
fresh Ask after a failure; all three close paths during a pending request,
late completion after reopen, and the new request's independent completion;
pending/failed Keep; one action home; one no-engine failure/action; one Add
notes fold with no normal budget; Space/click use of the Rails checkbox; and
late speech appending to the newest edited draft through exactly one mic.
Transport responses are declared fixtures. The existing production request
serialization and Keep writer execute in these tests. No full suite or
root quick check ran in this worker. Explicit-path `git diff --check` passed.

## Unknown

The worker did not run product browser shots or a live model. Root owns the
actual 1440/393 product verification, replay plus real Keep writer checks,
quick check and owner desk judgment. The root's canvas shots are direction
only and are not a runtime claim.

## Final waiting treatment

Root requested one final CSS-only change after the focused run: the running
Ask RunLine now shows the library loading glyph `◌` through its scoped
`::before`, with the existing `surface-state-pulse` keyframe and
`--duration-long` timing. Reduced motion disables the pulse. The existing
elapsed timer and status text are unchanged. Root's quick check owns the
visual coverage. The final focused run above includes this CSS state.

## Source counsel repair

Round 1 found that PadGadget's captured-value mic callback could overwrite
a draft edited during transcription. Ask now sets Pad `mic=false` and uses
one external MicButton with the original functional draft append and
`draftScope="desk-ask"`. No shared gadget API changed. The held callback
test captures the old completion callback, edits the draft, then invokes the
held completion and verifies both visible and durable text retain the newer
edit followed by the speech. The final focused collection and run above
include this repair. Held for root's one fix recheck; no staging or commit.

## Quick-check fallout repair

Root's quick run found two Ask failures in `routeInFooter.test.tsx`. The same
bounded three-file scope reproduced them before editing:
`.tmp/thread-ask/ask-route-before.log` — exit 1, 2 failed / 31 passed (33).
The test still selected the parked `HUB>` prefix, and the completed RunLine
had been removed. The selector now matches the current `Answer` prefix;
the existing LAN lamp, host, model, receipt and model-count assertions stay.
The answer again includes the completed RunLine with the actual frozen
elapsed time and no duplicate model or place. The existing test checks that
`Answered in 0 s` remains unchanged after the clock advances and rerender.
The final run above passes all 33 tests. No other product files changed for
this repair. Root owns the other quick-check findings and runtime fixture.

## Real Keep source repair

Root's actual Keep walk found HTTP 500 for a replayed answer grounded on a
real Note: `Invalid artifact source type: 'note'`. AskService already validates
qualified refs, hydrates their real sources, and writes canonical kind names
with exact refs. The artifact store's older source allowlist rejected those
canonical kinds.

The only backend product change is in `holdspeak/db/plugins.py`: union the
existing `RESOURCE_KINDS` closed vocabulary with the existing legacy artifact
source types. This preserves typed lineage, exact qualified refs and existing
producer types. Unknown kinds still fail both service ref validation and the
artifact store. There is no schema, migration, API or AskService change, and
this repair does not touch the frozen frontend.

New `tests/unit/test_ask_keep_sources.py` uses the real Database and
AskService.keep without a model. It verifies Note and Knowledge source rows,
exact quoted prompt and qualified refs after reopening the DB, the original
Zone/Knowledge/Project relationship snapshot, lookup by typed source, real
Zone grounding, and rejection of unknown qualified and artifact source kinds.
The existing `test_run_artifacts.py` and `test_philo12_artifact_source.py`
files are present and cover existing producer and artifact source behavior.

```text
.venv/bin/python .tmp/thread-ask/locked.py ask-keep-list .venv/bin/python -m pytest --collect-only -q tests/unit/test_ask_keep_sources.py tests/unit/test_run_artifacts.py tests/unit/test_philo12_artifact_source.py
.venv/bin/python .tmp/thread-ask/locked.py ask-keep-before .venv/bin/python -m pytest -q -n auto --dist worksteal tests/unit/test_ask_keep_sources.py tests/unit/test_run_artifacts.py tests/unit/test_philo12_artifact_source.py
.venv/bin/python .tmp/thread-ask/locked.py ask-keep-after .venv/bin/python -m pytest -q -n auto --dist worksteal tests/unit/test_ask_keep_sources.py tests/unit/test_run_artifacts.py tests/unit/test_philo12_artifact_source.py
```

All three commands use the root helper's isolated HOME and test lock.

- `.tmp/thread-ask/ask-keep-list.log`: exit 0, 21 collected in 0.60s.
- `.tmp/thread-ask/ask-keep-before.log`: exit 1, 2 failed / 19 passed in
  4.24s; the real writer rejects `note` and `zone`.
- `.tmp/thread-ask/ask-keep-after.log`: exit 0, `21 passed in 3.88s`.

Explicit-path diff check passed. Held for SHIP; no staging or commit. Root
owns the fresh actual Keep walks at 1440 and 393 and the final DB observation.
