# Evidence — HS-202-01: The first-use fence

Lane A, Astra. Base `50ca0dd6`, branch `feat/hs-202-01-fence`, worktree
`/Users/karol/dev/tools/wt-202-01`. Muad'Dib checks the built fence before
the done call. This story ships a failing regression fence before repairs;
it does not close the phase or the owner's sitting.

## Follow-up — the two ruled-design seams

The same revised smoke is verified against two product trees: an isolated
baseline worktree at the inventory product (`50ca0dd6`, also `3595fcb6^`), and an isolated
scratch worktree pinned to story 02 at `3595fcb6`. The scratch tree adds only
this smoke file; it has its own synced environment and web build. Each run
uses a fresh HOME and the fixture audio device. Neither lane B nor the main
checkout is used. The capture prints the tree commit and smoke SHA-256.

At 393, Go carries New Note and the Object and Window entries. The fence
requires those rows on screen after menu scroll and no inaccessible
separate titles announced. New Note is opened through Go. At 1440 the four
menus are checked as before. The inventory failure names stay unchanged.

The edit has a new visible Kept receipt in its editor before Save. A new
editor must have no such status before typing; after the body PUT succeeds,
only its own visible `Kept` status can pass. Save then closes the editor and
the exact title/body remain in the API. This is autosave confirmation,
**not a receipt emitted by the Save click**. The source, literal wording
distinction, two-brain check and remaining limits are in
[the follow-up check](checks/story-01-followup-muaddib.md).

The original full-suite capture and its ledger below remain historical
proof from the delivery commit; this bounded harness follow-up does not
claim a new full-suite run. Its verification is the same smoke on both
trees plus the unchanged source-button ratchet and relevant metadata checks.

### Follow-up result — partial, 2026-09-21 UTC

| Capture | Result read by Astra |
|---|---|
| Inventory default, 02:27:13Z | 2 failed in 87.76s; exactly the original five desktop and nine phone failures |
| Inventory strict plus unchanged ratchet, 02:30:40Z | 6 passed in 92.95s; both widths verify the exact unchanged KNOWN sets |
| Story 02 default plus unchanged ratchet, 02:28:51Z | **2 failed, 4 passed in 72.14s**; `import-refresh` at both widths; `menu-Object` and `menu-Window` also fail at 393 |
| Collection | 6 tests collected in 1.93s |
| Generated API reference | `API reference checked` |
| Documentation links and generated ledger, 02:36:58Z | 2 passed in 1.40s |

All three runs use smoke SHA-256
`1529454a786f613e1555df1091ffce3cd83f9b288a8936b74a0988ed66f6b530`.
The completed story-02 run passes the editor receipt, note persistence,
desktop menus, phone New Note through Go, summary completion, Notes query,
and both restart/refind legs. Its default result is **not GREEN**. The Go
menu is 1,404 px high with visible overflow: Object/Open remains at y=877.5
and Window/Close at y=1221.5 in an 852 px viewport after attempted scroll.
The import transcript loads, but Run summary still requires reopening.
These findings stay in HS-202-02; the fence does not add exceptions for them.

[The follow-up manifest](assets/story-01-followup/manifest.json) identifies
11 shots from that single story-02 run, their hashes, and the receipt timing.
Astra inspected the receipts at both widths, folded Go, the stale import,
and the refound content on glass. Raw final logs and collection output sit
beside it; the original delivery's 26 shots are unchanged.

Earlier captures below are retained as failed exploratory runs, not hidden:
some abort on FirstWords handoff; one trial used the root URL and was
reverted. The unchanged speech leg later completes on both product trees.
The intermittent handoff cause is unproved and remains a follow-up in the
[ledger](verification-ledger-story-01.md). No loading timeout is accepted
by strict mode. No full-suite rerun, product GREEN, or real-voice claim.
Story 01 stays done; this follow-up has no status flip and no merge.
Luna `fence_followup` (gpt-5.6-luna, xhigh) implemented the phone menu
branch and supplied bounded source diagnosis. Astra refined the selectors,
receipt and pointer checks, then ran and inspected the final proof.
Muad'Dib returned RATIFY-WITH-CONDITIONS for this partial shipment;
[the recorded response](checks/story-01-followup-muaddib.md) closes each
condition and corrects the parent-commit claim with Git evidence.

The keyboard leg also parks the pointer at (0,0) before Meta+K. A resting
pointer had selected a different result as the list reordered. This isolates
keyboard selection and discloses a separate hover behavior for HS-202-02;
it does not prove how a resting pointer and keyboard selection should mix.

Final capture blocks are **02:27:13Z**, **02:28:51Z**, **02:30:40Z**, all
at SHA 1529454a above. The other follow-up blocks, including SHA 9654ff79
and SHA a17bb05f, are exploratory. The raw commands' `story02-green` label
was a target, never a passing result; the archived final log is named
`assets/story-01-followup/story02-default-RED.log`. Its SHOT paths name the
scratch tree's `story-01-fence/` export directory. Eleven selected files
were copied to `story-01-followup/`; the original 26 shots in this lane were
not modified. The manifest ties the copied files to this exact final run.

## Verification boundary

The normal smoke must report the observed first-use defects. The explicit
expected-failure verification must execute the same assertions, accept only
the exact named defect set, and reject unexpected failures and healed
defects. Fixture audio and a stub engine do not prove the owner's real
recording, external-app dictation, or judgment of the result.

## Final proof read by Astra — 2026-09-21 UTC

| Proof | Captured result |
|---|---|
| Final normal RED, `red-reviewed`, 00:50:32Z | 2 failed in 86.83s: exactly five named defects at 1440 and nine at 393 |
| Final strict GREEN and unchanged ratchet, `green-exported`, 00:52:00Z | 6 passed in 86.83s; both widths print VERIFIED exact expected failures |
| Full isolated suite, 00:53:28Z | 8 failed, 11,299 passed, 116 skipped, 4 xfailed in 35:28; both fence parameters passed |
| Web baseline, 01:30:55Z | 2,645 passed; zero failures or branch-new results; five old baseline entries healed |
| Two metadata repairs, 01:32:18Z | 2 passed in 0.78s |
| Pinned-base comparison, 01:34:03Z | Base: 2 failed / 4 passed. Lane immediately after both fence cases: 2 failed / 6 passed |
| Second serial confirmation, 01:39:50Z | The four full-run-only failures: 4 passed in 26.75s |

All times above are UTC on 2026-09-21. The comparator's exit 0 is not a
test-green certificate: both nested pytest exits are 1 and are printed.
The [verification ledger](verification-ledger-story-01.md) classifies all
eight full-suite failures: two inherited metadata failures fixed, two
inherited runtime failures reproduced on base, and four flakes green twice
serially on this lane. Their parallel causes remain unknown.

The only source of the 26 shipped PNGs is `green-exported`.
[The manifest](assets/story-01-fence/manifest.json) records that capture,
dimensions and SHA-256 hashes. Astra checked all hashes after the full
suite and comparison runs, and read the final glass at both widths:
planned hosts, the stale record, the reopened summary, and note/meeting
refind. For example, [393 stale record](assets/story-01-fence/record-refresh-393.png)
and [393 reopened summary](assets/story-01-fence/summary-reopened-393.png)
show the missing live state and persisted result. These are isolated rig
shots, not the owner's desk. Earlier captures below are iteration history.

The suite rewrote 478 other tracked PNGs and six generated text/JSON
records; their HEAD bytes were put back. Nine untracked suite shots were
parked under `.tmp/hs202-01/parked-full-suite-output`, not shipped. Repeated
checks leave the final exported PNG bytes unchanged.

Focused collection output:

```text
tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
tests/unit/test_ux_canon_ratchet.py::test_ratchet
tests/unit/test_ux_canon_ratchet.py::test_hard_zeros
tests/unit/test_ux_canon_ratchet.py::test_ceiling_carries_its_date_and_reason
tests/unit/test_ux_canon_ratchet.py::test_healing

6 tests collected in 0.63s
```

## Initial ledger

- **(b), inherited product defects:** the doors and visible-state defects
  from the inventory belong to HS-202-02. This test-only lane records them;
  it does not repair product code. The phase still requires an unmarked
  green smoke after the repair stories land.
- **(b), inherited roadmap bookkeeping:** the initial `dw check holdspeak`
  reported the six errors below before this lane's implementation. Their
  homes are the named existing phase records; no unrelated status is flipped.

```text
ERROR pm/roadmap/holdspeak/phase-101-the-native-innards/evidence-story-04.md: evidence exists but matching story is not done
ERROR pm/roadmap/holdspeak/phase-152-the-hands: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-153-the-practice: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-154-the-call: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-156-the-front-door: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-200-the-working-practice: all stories are done but final-summary.md is missing
```

The unchanged source-button ratchet collected four tests and passed all four
in 2.03 seconds in an isolated HOME. No census gate or ceiling was added.

- **(b), additional inherited refresh defect:** after fixture import, the
  transcript loads but the selected list row keeps its initial state and
  withholds Run summary. The new `import-refresh` predicate records this
  independently of `record-refresh`. Home: HS-202-02, same refresh repair.
  The fixture holds transcription until the importing row loads, then
  waits on completion events; no timing sleep or product patch supplies
  the result. The real conductor completion callback is supplied when the
  test drains the summary queue.
- **Finding refined:** Notes highlights Change places; Enter executes it.
  Exact-title search correctly commits the selected note. The fence names
  a query/ranking defect, not a broken Enter dispatcher.

## Captured verification

The captures below are the command output, including nonzero exits. Early
captures are iteration history. The final exported GREEN run is the shot
provenance; default runs now write shots only in tmp_path. The full suite
cannot overwrite this lane's exported shots.

[Muad'Dib's check and Astra's response](checks/story-01-muaddib.md) record
the per-door split, stricter destination and visible-truth assertions,
and the UI-created profile binding, including the exact localhost port.

The rig does not claim the owner lock. Its drainer is OFF; NOT DRAINING on
glass is rig state. The test drains the production queue and calls its
production completion callback. FakeIntel replaces the summary provider;
the receipt proves the bound route contract, not physical network contact.
Engine Check uses real localhost HTTP. Restart replaces the in-process
server, DB singleton and browser context, but keeps Python module state.

The new test changes the generated API reference's candidate-test links;
the existing generator was rerun. No route or census gate was added.
The default CI E2E command collects both RED parameters. This is expected
until HS-202-02 repairs them; the owner ordered an open PR, not a merge.

### Captured run — 2026-09-21T00:37:55Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright PYTHONUNBUFFERED=1 uv run pytest -q -s --tb=short tests/e2e/test_hs202_first_use_smoke.py 2>&1 | tee .tmp/hs202-01/red.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** dbb87607f8ca085db1ca0302cbc23afffaf5e65d

```text
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-1440.png
PASS: Speak, Meetings and Desk memory dock doors fit and own their hit targets
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-1440.png
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-1440.png
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-1440.png
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-1440.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-1440.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-1440.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-1440.png
FSHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
FAIL: Speak, Meetings and Desk memory dock doors fit and own their hit targets
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/dock-393.png
FAIL: Desk menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Desk-393.png
FAIL: Object menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
PASS: Go menu door is reachable
PASS: Go menu content loaded
FAIL: Window menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-393.png
RECOVERY: use New Note keyboard command after the recorded menu failure.
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-393.png
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-393.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-393.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-393.png
F
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:447: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 1440: first-use steps failed: import-refresh, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'import-refresh', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:447: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 393: first-use steps failed: dock, import-refresh, menu-Desk, menu-Object, menu-Window, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'dock', 'import-refresh', 'menu-Desk', 'menu-Object', 'menu-Window', 'notes-query', ...}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed in 86.56s (0:01:26)
```

### Captured run — 2026-09-21T00:39:49Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright PYTHONUNBUFFERED=1 HS202_EXPECTED_FAILURES=1 uv run pytest -q -s --tb=short tests/e2e/test_hs202_first_use_smoke.py tests/unit/test_ux_canon_ratchet.py 2>&1 | tee .tmp/hs202-01/green.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dbb87607f8ca085db1ca0302cbc23afffaf5e65d

```text
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-1440.png
PASS: Speak, Meetings and Desk memory dock doors fit and own their hit targets
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-1440.png
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-1440.png
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-1440.png
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-1440.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-1440.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-1440.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-1440.png
VERIFIED exact expected failures: 1440 ['import-refresh', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door']
.SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
FAIL: Speak, Meetings and Desk memory dock doors fit and own their hit targets
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/dock-393.png
FAIL: Desk menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Desk-393.png
FAIL: Object menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
PASS: Go menu door is reachable
PASS: Go menu content loaded
FAIL: Window menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-393.png
RECOVERY: use New Note keyboard command after the recorded menu failure.
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-393.png
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-393.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-393.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-393.png
VERIFIED exact expected failures: 393 ['dock', 'import-refresh', 'menu-Desk', 'menu-Object', 'menu-Window', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door']
....ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
.
6 passed in 87.61s (0:01:27)
```

### Captured run — 2026-09-21T00:42:54Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright PYTHONUNBUFFERED=1 uv run pytest -q -s --tb=short tests/e2e/test_hs202_first_use_smoke.py 2>&1 | tee .tmp/hs202-01/red-final.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** bafabac1d0f3d0f2d13460ad136a4d9de7d1ef18

```text
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 10239
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-1440.png
PASS: Speak, Meetings and Desk memory dock doors fit and own their hit targets
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-1440.png
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-1440.png
PLANNED 127.0.0.1 sha256:64908cca3d478af0e2c28d0ee20438dd0ca9ae85bad4a37c1ef5c0c466c593df
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-1440.png
RECEIPT succeeded sha256:64908cca3d478af0e2c28d0ee20438dd0ca9ae85bad4a37c1ef5c0c466c593df 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-1440.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-1440.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-1440.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-1440.png
FSHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
FAIL: Speak, Meetings and Desk memory dock doors fit and own their hit targets
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/dock-393.png
FAIL: Desk menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Desk-393.png
FAIL: Object menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
PASS: Go menu door is reachable
PASS: Go menu content loaded
FAIL: Window menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-393.png
RECOVERY: use New Note keyboard command after the recorded menu failure.
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-393.png
PLANNED 127.0.0.1 sha256:c1c1a358dd8838cf0af399aa6d9a097d5b9201ae7ef77a876417a73c60bd28f7
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
RECEIPT succeeded sha256:c1c1a358dd8838cf0af399aa6d9a097d5b9201ae7ef77a876417a73c60bd28f7 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-393.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-393.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-393.png
F
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:469: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 1440: first-use steps failed: import-refresh, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'import-refresh', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:469: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 393: first-use steps failed: dock, import-refresh, menu-Desk, menu-Object, menu-Window, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'dock', 'import-refresh', 'menu-Desk', 'menu-Object', 'menu-Window', 'notes-query', ...}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed in 87.40s (0:01:27)
```

### Captured run — 2026-09-21T00:50:32Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm PYTHONUNBUFFERED=1 uv run pytest -q -s --tb=short tests/e2e/test_hs202_first_use_smoke.py 2>&1 | tee .tmp/hs202-01/red-reviewed.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 10239
PASS: engine setup completed visibly without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/engine-set-1440.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
FAIL: Write a thought opens a note authoring surface
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/thought-door-1440.png
FAIL: Save shows a new visible confirmation
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/save-confirmation-1440.png
PLANNED 127.0.0.1 sha256:2914f699d548803f671e8666aa363b4f80404eaf9ecb5eed84958380c08b3623
FAIL: The imported transcript exposes Run summary without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/planned-host-1440.png
RECEIPT succeeded sha256:2914f699d548803f671e8666aa363b4f80404eaf9ecb5eed84958380c08b3623 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/record-refresh-1440.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/summary-reopened-1440.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/notes-query-1440.png
PASS: refind the saved note and its body in two navigation moves
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_1440_900_0/shots/meeting-after-restart-1440.png
FSHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
FAIL: Desk memory dock door fits and owns its hit target
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/dock-memory-393.png
FAIL: Desk menu door is reachable
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/menu-Desk-393.png
FAIL: Object menu door is reachable
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/menu-Object-393.png
PASS: Go menu door is reachable
PASS: Go menu content loaded
FAIL: Window menu door is reachable
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/menu-Window-393.png
FAIL: Write a thought opens a note authoring surface
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/thought-door-393.png
RECOVERY: use New Note keyboard command after the recorded menu failure.
FAIL: Save shows a new visible confirmation
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/save-confirmation-393.png
PLANNED 127.0.0.1 sha256:c0f0a23d8a93f04611c624f4a90548d01531be61992ee3a4a3cee42c09f90c50
FAIL: The imported transcript exposes Run summary without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/planned-host-393.png
RECEIPT succeeded sha256:c0f0a23d8a93f04611c624f4a90548d01531be61992ee3a4a3cee42c09f90c50 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/record-refresh-393.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/summary-reopened-393.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/notes-query-393.png
PASS: refind the saved note and its body in two navigation moves
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9381/test_first_use_fence_393_852_0/shots/meeting-after-restart-393.png
F
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:492: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 1440: first-use steps failed: import-refresh, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'import-refresh', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:492: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 393: first-use steps failed: dock-memory, import-refresh, menu-Desk, menu-Object, menu-Window, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'dock-memory', 'import-refresh', 'menu-Desk', 'menu-Object', 'menu-Window', 'notes-query', ...}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed in 86.83s (0:01:26)
```

### Captured run — 2026-09-21T00:52:00Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm PYTHONUNBUFFERED=1 HS202_EXPECTED_FAILURES=1 HS202_EXPORT_SHOTS=1 uv run pytest -q -s --tb=short tests/e2e/test_hs202_first_use_smoke.py tests/unit/test_ux_canon_ratchet.py 2>&1 | tee .tmp/hs202-01/green-exported.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-1440.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-1440.png
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-1440.png
PLANNED 127.0.0.1 sha256:311e59e9b8f126bc2e4a37610d603bfb7d4508835621f707ed972cdc87aa61d2
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-1440.png
RECEIPT succeeded sha256:311e59e9b8f126bc2e4a37610d603bfb7d4508835621f707ed972cdc87aa61d2 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-1440.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-1440.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-1440.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-1440.png
VERIFIED exact expected failures: 1440 ['import-refresh', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door']
.SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
FAIL: Desk memory dock door fits and owns its hit target
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/dock-memory-393.png
FAIL: Desk menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Desk-393.png
FAIL: Object menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
PASS: Go menu door is reachable
PASS: Go menu content loaded
FAIL: Window menu door is reachable
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
FAIL: Write a thought opens a note authoring surface
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/thought-door-393.png
RECOVERY: use New Note keyboard command after the recorded menu failure.
FAIL: Save shows a new visible confirmation
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/save-confirmation-393.png
PLANNED 127.0.0.1 sha256:1d0e15a239d4c49b6e7695fb9557ade332c9c1d8079ced42974fea0efc2606b5
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
RECEIPT succeeded sha256:1d0e15a239d4c49b6e7695fb9557ade332c9c1d8079ced42974fea0efc2606b5 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/record-refresh-393.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/notes-query-393.png
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-393.png
VERIFIED exact expected failures: 393 ['dock-memory', 'import-refresh', 'menu-Desk', 'menu-Object', 'menu-Window', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door']
....ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
.
6 passed in 86.83s (0:01:26)
```

### Captured run — 2026-09-21T00:53:28Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm PYTHONUNBUFFERED=1 HS202_EXPECTED_FAILURES=1 uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py --tb=short 2>&1 | tee .tmp/hs202-01/full.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
........................................................................ [  1%]
........................................................................ [  2%]
........................................................................ [  3%]
........................................................................ [  3%]
........................................................................ [  4%]
........................................................................ [  5%]
........................................................................ [  5%]
........................................................................ [  6%]
.............................ssssssssssssssssssssssssssss............... [  6%]
........................................................................ [  7%]
........................................................................ [  8%]
........................................................................ [  8%]
........................................................................ [  9%]
........................................................................ [ 10%]
........................................................................ [ 10%]
................ss...................................................... [ 11%]
...........s.s.......................................................... [ 11%]
........................................................................ [ 12%]
........................................................................ [ 13%]
........................................................................ [ 13%]
........................................................s............... [ 14%]
.....................................ss........ss......ss............... [ 15%]
.............................................................s.......... [ 15%]
.....................................s.................................. [ 16%]
................sssss................................................... [ 17%]
..................................s..................................... [ 17%]
........F..................F..............F............................. [ 18%]
........................................................................ [ 18%]
........................................................................ [ 19%]
........................................................................ [ 20%]
...................................s.................................... [ 20%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 22%]
........................................................................ [ 23%]
.........ss............................................................. [ 23%]
........................................................................ [ 24%]
........................................................................ [ 25%]
...........................................................s............ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 27%]
........................................................................ [ 28%]
........................................................................ [ 29%]
......................................s................................. [ 29%]
........................................................................ [ 30%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 32%]
........................................................................ [ 33%]
......................................................................F. [ 34%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 37%]
........................................................................ [ 38%]
...........s............................................................ [ 39%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 42%]
..............................................................sss....... [ 42%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 49%]
........................................................................ [ 50%]
.......................................................................s [ 51%]
........................................................................ [ 51%]
........................................................................ [ 52%]
..............................s............sss.......................... [ 52%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
...F..........................s......................................... [ 55%]
........................................................................ [ 56%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 66%]
.........................................F.............................. [ 66%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 69%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 75%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 76%]
........................................................................ [ 77%]
.................................................s...................... [ 78%]
........................................................................ [ 78%]
.......................................s................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 92%]
.........................................s.............................. [ 93%]
........................................................................ [ 93%]
........................................................................ [ 94%]
........................................................................ [ 95%]
............................s........................................... [ 95%]
........................................................................ [ 96%]
..................................................F..................... [ 97%]
..............x.......ssssssssssssx....sssssssss...........x...........s [ 97%]
sss....ssssss.x......................................................... [ 98%]
........F............................................................... [ 98%]
..........................................ssssssssss..s................. [ 99%]
...........................................                              [100%]
=================================== FAILURES ===================================
__ test_promotion_cancellation_after_provider_return_never_publishes_artifact __
[gw11] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/unit/test_decision_record_service.py:456: in test_promotion_cancellation_after_provider_return_never_publishes_artifact
    assert child_receipt is not None and child_receipt["outcome"] == "succeeded"
E   AssertionError: assert ({'actor_identity': 'promotion-owner', 'actor_kind': 'owner', 'authority_basis': 'authenticated_principal+declared_capability+hard_prerequisites+interruption_policy', 'created_at': 1789952166.7658691, ...} is not None and 'cancelled' == 'succeeded'
E
E     - succeeded
E     + cancelled)
___________________ test_thought_workbench_real_glass[1440] ____________________
[gw0] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/e2e/test_hs141_thought_workbench_glass.py:251: in test_thought_workbench_real_glass
    page.get_by_role("region", name="Thought", exact=True).wait_for(timeout=10000)
.venv/lib/python3.12/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.12/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.12/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:559: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for get_by_role("region", name="Thought", exact=True) to be visible
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________ test_no_live_doc_has_a_dangling_relative_link _________________
[gw8] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/unit/test_doc_drift_guard.py:269: in test_no_live_doc_has_a_dangling_relative_link
    assert not offenders, (
E   AssertionError: A maintained doc links a path that does not exist (dangling relative link). Fix the path or the move:
E       docs/internal/checks/surface-inventory-astra.md:11: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/01-measured-walk.md:6004
E       docs/internal/checks/surface-inventory-astra.md:11: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/02-coherence-astra.md:158
E       docs/internal/checks/surface-inventory-astra.md:13: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/01-measured-walk.md:392
E       docs/internal/checks/surface-inventory-astra.md:13: -> /Users/karol/dev/tools/wt-202-audit/web/src/desk/surface/gadgets.tsx:111
E       docs/internal/checks/surface-inventory-astra.md:13: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/01-measured-walk.md:1862
E       docs/internal/checks/surface-inventory-astra.md:13: -> /Users/karol/dev/tools/wt-202-audit/scripts/surface_census_measure.js:134
E       docs/internal/checks/surface-inventory-astra.md:15: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/03-interaction-walk.md:209
E       docs/internal/checks/surface-inventory-astra.md:15: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/03-interaction-walk.md:323
E       docs/internal/checks/surface-inventory-astra.md:15: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/03-interaction-walk.md:90
E       docs/internal/checks/surface-inventory-astra.md:17: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/03-interaction-walk.md:283
E       docs/internal/checks/surface-inventory-astra.md:17: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/03-interaction-walk.md:383
E       docs/internal/checks/surface-inventory-astra.md:19: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/interaction.json:8692
E       docs/internal/checks/surface-inventory-astra.md:19: -> /Users/karol/dev/tools/wt-202-audit/scripts/surface_interaction_walk.py:902
E       docs/internal/checks/surface-inventory-astra.md:19: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/04-sober-eye.md:101
E       docs/internal/checks/surface-inventory-astra.md:21: -> /Users/karol/dev/tools/wt-202-audit/scripts/surface_interaction_walk.py:298
E       docs/internal/checks/surface-inventory-astra.md:21: -> /Users/karol/dev/tools/wt-202-audit/web/src/pages/cores/settingsWallpaper.tsx:95
E       docs/internal/checks/surface-inventory-astra.md:21: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/interaction.json:3781
E       docs/internal/checks/surface-inventory-astra.md:21: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/01-measured-walk.md:6111
E       docs/internal/checks/surface-inventory-astra.md:23: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/UX-CANON.md:77
E       docs/internal/checks/surface-inventory-astra.md:23: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/02-coherence-astra.md:228
E       docs/internal/checks/surface-inventory-astra.md:25: -> /Users/karol/dev/tools/wt-202-audit/pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md:68
E       docs/internal/checks/surface-inventory-astra.md:33: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/04-sober-eye.md:245
E       docs/internal/checks/surface-inventory-astra.md:33: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/04-sober-eye.md:116
E       docs/internal/checks/surface-inventory-astra.md:34: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inventory-2026-09-20/01-measured-walk.md:6102
E       docs/internal/checks/surface-inventory-astra.md:50: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/SURFACE-INVENTORY-2026-09-20.md:90
E       docs/internal/checks/surface-inventory-astra.md:50: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/SURFACE-INVENTORY-2026-09-20.md:120
E       docs/internal/checks/surface-inventory-astra.md:50: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/SURFACE-INVENTORY-2026-09-20.md:148
E       docs/internal/checks/surface-inventory-astra.md:52: -> /Users/karol/dev/tools/wt-202-audit/web/src/pages/cores/SettingsCore.tsx:738
E       docs/internal/checks/surface-inventory-astra.md:54: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/SURFACE-INVENTORY-2026-09-20.md:169
E       docs/internal/checks/surface-inventory-astra.md:56: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/SURFACE-INVENTORY-2026-09-20.md:181
E       docs/internal/checks/surface-inventory-astra.md:60: -> /Users/karol/dev/tools/wt-202-audit/pm/roadmap/holdspeak/phase-201-one-meeting-result/SITTING-07.md:35
E   assert not ['docs/internal/checks/surface-inventory-astra.md:11: -> /Users/karol/dev/tools/wt-202-audit/docs/internal/surface-inv...ecks/surface-inventory-astra.md:13: -> /Users/karol/dev/tools/wt-202-audit/scripts/surface_census_measure.js:134', ...]
_______________ TestCalendarSourcesRoute.test_matched_this_week ________________
[gw10] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/unit/test_hs175_calendar_sources.py:169: in test_matched_this_week
    assert row["cnt"] >= 1
E   assert 0 >= 1
__________ test_real_http_executor_receipt_and_sigkill_cursor_replay ___________
[gw2] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/integration/test_kernel_real_hub.py:209: in test_real_http_executor_receipt_and_sigkill_cursor_replay
    process = start()
              ^^^^^^^
tests/integration/test_kernel_real_hub.py:122: in start
    raise AssertionError(f"spawned hub did not become healthy:\n{output}")
E   AssertionError: spawned hub did not become healthy:
E   HoldSpeak runtime identity: backend_commit=50ca0dd6cf8f45a7b78576fbd3d995761be97001 frontend_build=f818c13f80fd4d93 database_path=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9383/popen-gw2/test_real_http_executor_receip0/home/.local/share/holdspeak/holdspeak.db
_____________________ test_committed_ledger_is_up_to_date ______________________
[gw6] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/uat/test_build_ledger.py:11: in test_committed_ledger_is_up_to_date
    assert build_ledger.main(["--check"]) == 0
E   AssertionError: assert 1 == 0
E    +  where 1 = <function main at 0x11108b420>(['--check'])
E    +    where <function main at 0x11108b420> = build_ledger.main
----------------------------- Captured stderr call -----------------------------
features.yaml is stale — re-run: uv run python -m uat.tools.build_ledger
_____________________________ test_speak_loop_393 ______________________________
[gw1] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/e2e/test_hs176_loop_glass.py:374: in test_speak_loop_393
    _run(tmp_path, monkeypatch, 393, 852)
tests/e2e/test_hs176_loop_glass.py:356: in _run
    _loop(page, width)
tests/e2e/test_hs176_loop_glass.py:278: in _loop
    assert landed == APPLIED_TEXT, landed
E   AssertionError: Ship the queue for platform on schedule
E   assert 'Ship the que...m on schedule' == 'Ship the Q4 ...rm in October'
E
E     - Ship the Q4 platform in October
E     + Ship the queue for platform on schedule
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____________________ TestMeetingsGlass.test_meetings_face _____________________
[gw0] darwin -- Python 3.12.12 /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
tests/e2e/test_hs170_meetings_glass.py:318: in test_meetings_face
    expect(facet_area).to_be_visible(timeout=3_000)
E   AssertionError: Locator expected to be visible
E   Actual value: None
E   Error: element(s) not found
E   Call log:
E     - Expect "to_be_visible" with timeout 3000ms
E     - waiting for locator("[data-testid='meetings-facets']")
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:17: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:58: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:109: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:99: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/unit/test_dictation_session_admission.py:497: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:924: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:993: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ietdcUWp8c/xdist-gw4/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ietdcUWp8c/xdist-gw4/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1175: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1196: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2242: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2494: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2534: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/unit/test_dictation_session_admission.py:2548: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2588: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ietdcUWp8c/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:181: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:84: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:139: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:169: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:207: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:160: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_web_runtime.py:269: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:552: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:618: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:171: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:232: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:281: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:149: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:396: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:461: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:554: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:270: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:521: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:673: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:921: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1090: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:327: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1636: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:318: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:281: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:367: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/wt-202-01/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:118: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
FAILED tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact
FAILED tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]
FAILED tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link
FAILED tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week
FAILED tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay
FAILED tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date - ...
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - AssertionErr...
FAILED tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face
8 failed, 11299 passed, 116 skipped, 4 xfailed in 2128.07s (0:35:28)
```

### Captured run — 2026-09-21T01:30:55Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/check_web_baseline.py --run 2>&1 | tee .tmp/hs202-01/web-baseline.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2645 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-21T01:32:18Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q --tb=short tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date 2>&1 | tee .tmp/hs202-01/metadata-repairs.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
..                                                                       [100%]
2 passed in 0.78s
```

### Captured run — 2026-09-21T01:34:03Z

- **Command:** `python3 .tmp/hs202-01/compare-scoped.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
SCOPED BASELINE COMPARISON base /Users/karol/dev/tools/wt-202-01-baseline
COMMAND ['uv', 'run', 'pytest', '-v', '--tb=short', 'tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact', 'tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]', 'tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week', 'tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay', 'tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393', 'tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face']
============================= test session starts ==============================
platform darwin -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0 -- /Users/karol/dev/tools/wt-202-01-baseline/.venv/bin/python3
cachedir: .pytest_cache
holdspeak: HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-compare-3r0r1rwm
rootdir: /Users/karol/dev/tools/wt-202-01-baseline
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 300.0s
timeout method: thread
timeout func_only: False
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 6 items

tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact PASSED [ 16%]
tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440] PASSED [ 33%]
tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week FAILED [ 50%]
tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay PASSED [ 66%]
tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 PASSED           [ 83%]
tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face FAILED [100%]

=================================== FAILURES ===================================
_______________ TestCalendarSourcesRoute.test_matched_this_week ________________
tests/unit/test_hs175_calendar_sources.py:169: in test_matched_this_week
    assert row["cnt"] >= 1
E   assert 0 >= 1
_____________________ TestMeetingsGlass.test_meetings_face _____________________
tests/e2e/test_hs170_meetings_glass.py:318: in test_meetings_face
    expect(facet_area).to_be_visible(timeout=3_000)
E   AssertionError: Locator expected to be visible
E   Actual value: None
E   Error: element(s) not found
E   Call log:
E     - Expect "to_be_visible" with timeout 3000ms
E     - waiting for locator("[data-testid='meetings-facets']")
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week
FAILED tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face
========================= 2 failed, 4 passed in 44.60s =========================
COMPARISON EXIT base 1
SCOPED BASELINE COMPARISON lane-after-fence /Users/karol/dev/tools/wt-202-01
COMMAND ['uv', 'run', 'pytest', '-v', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py', 'tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact', 'tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]', 'tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week', 'tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay', 'tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393', 'tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face']
============================= test session starts ==============================
platform darwin -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0 -- /Users/karol/dev/tools/wt-202-01/.venv/bin/python3
cachedir: .pytest_cache
holdspeak: HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-compare-knz39g_7
rootdir: /Users/karol/dev/tools/wt-202-01
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 300.0s
timeout method: thread
timeout func_only: False
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 8 items

tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900] PASSED [ 12%]
tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852] PASSED [ 25%]
tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact PASSED [ 37%]
tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440] PASSED [ 50%]
tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week FAILED [ 62%]
tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay PASSED [ 75%]
tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 PASSED           [ 87%]
tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face FAILED [100%]

=================================== FAILURES ===================================
_______________ TestCalendarSourcesRoute.test_matched_this_week ________________
tests/unit/test_hs175_calendar_sources.py:169: in test_matched_this_week
    assert row["cnt"] >= 1
E   assert 0 >= 1
_____________________ TestMeetingsGlass.test_meetings_face _____________________
tests/e2e/test_hs170_meetings_glass.py:318: in test_meetings_face
    expect(facet_area).to_be_visible(timeout=3_000)
E   AssertionError: Locator expected to be visible
E   Actual value: None
E   Error: element(s) not found
E   Call log:
E     - Expect "to_be_visible" with timeout 3000ms
E     - waiting for locator("[data-testid='meetings-facets']")
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week
FAILED tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face
=================== 2 failed, 6 passed in 115.04s (0:01:55) ====================
COMPARISON EXIT lane-after-fence 1
```

### Captured run — 2026-09-21T01:39:50Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q --tb=short tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact 'tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]' tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 2>&1 | tee .tmp/hs202-01/serial-confirm.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
....                                                                     [100%]
4 passed in 26.75s
```

### Captured run — 2026-09-21T01:43:31Z

- **Command:** `bash -o pipefail -c HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q --tb=short tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date 2>&1 | tee .tmp/hs202-01/final-metadata.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c54723672e64d8e2cf85fb86e1c8584cb3772ca3

```text
..                                                                       [100%]
2 passed in 0.81s
```

### Captured run — 2026-09-21T02:07:47Z

- **Command:** `python3 .tmp/hs202-followup/run-proof.py story02-green`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
PROOF LEG story02-green
ROOT /Users/karol/dev/tools/wt-202-01/.tmp/hs202-followup/story02
HEAD 3595fcb696c07ce8d01fad0da58396fb4fc5ef9e
SMOKE SHA256 9654ff79571d95dd17c59920c18891ca75ab7ecfb951442c73485e708d3ba548
ISOLATED HOME /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-followup-v_f7xeh2
COMMAND ['uv', 'run', 'pytest', '-q', '-s', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py', 'tests/unit/test_ux_canon_ratchet.py']
FSHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 10239
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-go-menu-393.png
PASS: New Note is visible and reachable in the folded Go menu
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-menu-Desk-393.png
FAIL: Open is visible and reachable as an Object entry in Go (missing from Go)
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
FAIL: Close window is visible and reachable as a Window entry in Go
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
PASS: Write a thought opens a note authoring surface
PASS: The edit has a new visible Kept receipt in its editor before Save
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/editor-kept-before-save-393.png
PLANNED 127.0.0.1 sha256:8351954f3e5fcb04558b08d7b0971a79f51c7e60dbaf3c6450fc59e936b078d2
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
RECEIPT succeeded sha256:8351954f3e5fcb04558b08d7b0971a79f51c7e60dbaf3c6450fc59e936b078d2 127.0.0.1
PASS: The open record shows the completed summary and actual host without a reload
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ↗ / Custom webhook / NOT CONFIGURED
F...ratchet: A1 175 -> 174 -- lower the ceiling
ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
.
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:248: in test_first_use_fence
    _loaded(first_note.get_by_text(WORDS, exact=True))
tests/e2e/test_hs202_first_use_smoke.py:50: in _loaded
    locator.wait_for(state="visible", timeout=10_000)
.venv/lib/python3.12/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.12/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.12/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:559: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for get_by_role("region", name="First dictation", exact=True).get_by_text("The quick brown fox jumps over the lazy dog.", exact=True) to be visible
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:536: in test_first_use_fence
    _loaded(page.locator(".prefs-wallpaper-grid"))
tests/e2e/test_hs202_first_use_smoke.py:50: in _loaded
    locator.wait_for(state="visible", timeout=10_000)
.venv/lib/python3.12/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.12/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.12/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:559: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for locator(".prefs-wallpaper-grid") to be visible
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed, 4 passed in 74.45s (0:01:14)
PYTEST EXIT 1
```

### Captured run — 2026-09-21T02:12:17Z

- **Command:** `python3 .tmp/hs202-followup/run-proof.py story02-green`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
PROOF LEG story02-green
ROOT /Users/karol/dev/tools/wt-202-01/.tmp/hs202-followup/story02
HEAD 3595fcb696c07ce8d01fad0da58396fb4fc5ef9e
SMOKE SHA256 1529454a786f613e1555df1091ffce3cd83f9b288a8936b74a0988ed66f6b530
ISOLATED HOME /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-followup-jtfrpx90
COMMAND ['uv', 'run', 'pytest', '-q', '-s', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py', 'tests/unit/test_ux_canon_ratchet.py']
FSHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 10922
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-go-menu-393.png
PASS: New Note is visible and reachable in the folded Go menu
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-menu-Desk-393.png
FAIL: Open is visible and reachable as an Object entry in Go
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
MENU GEOMETRY menu-Object {'x': 11, 'y': 877.5, 'width': 371, 'height': 28} {'height': 1404, 'scrollHeight': 1404, 'overflow': 'visible'}
FAIL: Close window is visible and reachable as a Window entry in Go
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
MENU GEOMETRY menu-Window {'x': 11, 'y': 1221.5, 'width': 371, 'height': 28} {'height': 1404, 'scrollHeight': 1404, 'overflow': 'visible'}
PASS: Write a thought opens a note authoring surface
PASS: The edit has a new visible Kept receipt in its editor before Save
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/editor-kept-before-save-393.png
PLANNED 127.0.0.1 sha256:95876410ed92d840920425e3168c8370554ddd0703222eca1c6a548113e7e425
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
RECEIPT succeeded sha256:95876410ed92d840920425e3168c8370554ddd0703222eca1c6a548113e7e425 127.0.0.1
PASS: The open record shows the completed summary and actual host without a reload
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ○ / Fence architecture note / NOTE
PASS: Typing Notes and Enter reaches notes
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-393.png
F...ratchet: A1 175 -> 174 -- lower the ceiling
ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
.
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:251: in test_first_use_fence
    _loaded(first_note.get_by_text(WORDS, exact=True))
tests/e2e/test_hs202_first_use_smoke.py:50: in _loaded
    locator.wait_for(state="visible", timeout=10_000)
.venv/lib/python3.12/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.12/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.12/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:559: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for get_by_role("region", name="First dictation", exact=True).get_by_text("The quick brown fox jumps over the lazy dog.", exact=True) to be visible
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:579: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 393: first-use steps failed: import-refresh, menu-Object, menu-Window
E   assert not {'import-refresh', 'menu-Object', 'menu-Window'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed, 4 passed in 92.13s (0:01:32)
PYTEST EXIT 1
```

### Captured run — 2026-09-21T02:14:39Z

- **Command:** `python3 .tmp/hs202-followup/run-proof.py inventory-red`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
PROOF LEG inventory-red
ROOT /Users/karol/dev/tools/wt-202-01
HEAD 6f73788308b8309cdd5ade5aa9ead98d31857fbe
SMOKE SHA256 1529454a786f613e1555df1091ffce3cd83f9b288a8936b74a0988ed66f6b530
ISOLATED HOME /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-followup-geg6adwa
COMMAND ['uv', 'run', 'pytest', '-q', '-s', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py']
FF
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:251: in test_first_use_fence
    _loaded(first_note.get_by_text(WORDS, exact=True))
tests/e2e/test_hs202_first_use_smoke.py:50: in _loaded
    locator.wait_for(state="visible", timeout=10_000)
.venv/lib/python3.12/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.12/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.12/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:559: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for get_by_role("region", name="First dictation", exact=True).get_by_text("The quick brown fox jumps over the lazy dog.", exact=True) to be visible
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:251: in test_first_use_fence
    _loaded(first_note.get_by_text(WORDS, exact=True))
tests/e2e/test_hs202_first_use_smoke.py:50: in _loaded
    locator.wait_for(state="visible", timeout=10_000)
.venv/lib/python3.12/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.12/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.12/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:559: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for get_by_role("region", name="First dictation", exact=True).get_by_text("The quick brown fox jumps over the lazy dog.", exact=True) to be visible
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed in 42.99s
PYTEST EXIT 1
```

### Captured run — 2026-09-21T02:18:06Z

- **Command:** `python3 .tmp/hs202-followup/run-proof.py story02-green`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
PROOF LEG story02-green
ROOT /Users/karol/dev/tools/wt-202-01/.tmp/hs202-followup/story02
HEAD 3595fcb696c07ce8d01fad0da58396fb4fc5ef9e
SMOKE SHA256 a17bb05ff02afe32cb39ebcc2518b3cd52139507615591a76a8a68a1f86f4503
ISOLATED HOME /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-followup-ac4xjkse
COMMAND ['uv', 'run', 'pytest', '-q', '-s', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py', 'tests/unit/test_ux_canon_ratchet.py']
FSHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 10240
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-go-menu-393.png
PASS: New Note is visible and reachable in the folded Go menu
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-menu-Desk-393.png
FAIL: Open is visible and reachable as an Object entry in Go
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
MENU GEOMETRY menu-Object {'x': 11, 'y': 877.5, 'width': 371, 'height': 28} {'height': 1404, 'scrollHeight': 1404, 'overflow': 'visible'}
FAIL: Close window is visible and reachable as a Window entry in Go
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
MENU GEOMETRY menu-Window {'x': 11, 'y': 1221.5, 'width': 371, 'height': 28} {'height': 1404, 'scrollHeight': 1404, 'overflow': 'visible'}
PASS: Write a thought opens a note authoring surface
PASS: The edit has a new visible Kept receipt in its editor before Save
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/editor-kept-before-save-393.png
PLANNED 127.0.0.1 sha256:faac7738587f1901bcb9aebd0c511b1decc2a3c8308b481cde7b3ab6dc59af57
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
RECEIPT succeeded sha256:faac7738587f1901bcb9aebd0c511b1decc2a3c8308b481cde7b3ab6dc59af57 127.0.0.1
PASS: The open record shows the completed summary and actual host without a reload
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ○ / Fence architecture note / NOTE
PASS: Typing Notes and Enter reaches notes
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-393.png
F...ratchet: A1 175 -> 174 -- lower the ceiling
ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
.
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:253: in test_first_use_fence
    _loaded(first_note.get_by_text(WORDS, exact=True))
tests/e2e/test_hs202_first_use_smoke.py:50: in _loaded
    locator.wait_for(state="visible", timeout=10_000)
.venv/lib/python3.12/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.12/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.12/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
.venv/lib/python3.12/site-packages/playwright/_impl/_connection.py:559: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E   Call log:
E     - waiting for get_by_role("region", name="First dictation", exact=True).get_by_text("The quick brown fox jumps over the lazy dog.", exact=True) to be visible
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:581: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 393: first-use steps failed: import-refresh, menu-Object, menu-Window
E   assert not {'import-refresh', 'menu-Object', 'menu-Window'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed, 4 passed in 85.82s (0:01:25)
PYTEST EXIT 1
```

### Captured run — 2026-09-21T02:27:13Z

- **Command:** `python3 .tmp/hs202-followup/run-proof.py inventory-red`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
PROOF LEG inventory-red
ROOT /Users/karol/dev/tools/wt-202-01-baseline
HEAD 50ca0dd6cf8f45a7b78576fbd3d995761be97001
SMOKE SHA256 1529454a786f613e1555df1091ffce3cd83f9b288a8936b74a0988ed66f6b530
ISOLATED HOME /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-followup-xqkm92v8
COMMAND ['uv', 'run', 'pytest', '-q', '-s', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py']
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/engine-set-1440.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
FAIL: Write a thought opens a note authoring surface
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/thought-door-1440.png
FAIL: The edit has a new visible Kept receipt in its editor before Save
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/save-confirmation-1440.png
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/editor-kept-before-save-1440.png
PLANNED 127.0.0.1 sha256:9e2fd3bfcb2bc4c7b8c8c0285adb84c496a83db03e9cc80e0066b20ddb0be1f1
FAIL: The imported transcript exposes Run summary without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/planned-host-1440.png
RECEIPT succeeded sha256:9e2fd3bfcb2bc4c7b8c8c0285adb84c496a83db03e9cc80e0066b20ddb0be1f1 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/record-refresh-1440.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/summary-reopened-1440.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/notes-query-1440.png
PASS: refind the saved note and its body in two navigation moves
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_1440_900_0/shots/meeting-after-restart-1440.png
FSHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
FAIL: Desk memory dock door fits and owns its hit target
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/dock-memory-393.png
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/folded-go-menu-393.png
FAIL: New Note is visible and reachable in the folded Go menu (missing from Go)
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/menu-Desk-393.png
FAIL: Open is visible and reachable as an Object entry in Go (missing from Go)
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/menu-Object-393.png
FAIL: Close window is visible and reachable as a Window entry in Go (missing from Go)
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/menu-Window-393.png
FAIL: Write a thought opens a note authoring surface
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/thought-door-393.png
RECOVERY: use New Note keyboard command after the recorded menu failure.
FAIL: The edit has a new visible Kept receipt in its editor before Save
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/save-confirmation-393.png
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/editor-kept-before-save-393.png
PLANNED 127.0.0.1 sha256:fa52864d741f098b8996ddb8af9fec2c9173f4aba2337c69dd4597dd2684dc1e
FAIL: The imported transcript exposes Run summary without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/planned-host-393.png
RECEIPT succeeded sha256:fa52864d741f098b8996ddb8af9fec2c9173f4aba2337c69dd4597dd2684dc1e 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/record-refresh-393.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/summary-reopened-393.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/notes-query-393.png
PASS: refind the saved note and its body in two navigation moves
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9424/test_first_use_fence_393_852_0/shots/meeting-after-restart-393.png
F
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:579: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 1440: first-use steps failed: import-refresh, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'import-refresh', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:579: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 393: first-use steps failed: dock-memory, import-refresh, menu-Desk, menu-Object, menu-Window, notes-query, record-refresh, save-confirmation, thought-door
E   assert not {'dock-memory', 'import-refresh', 'menu-Desk', 'menu-Object', 'menu-Window', 'notes-query', ...}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed in 87.76s (0:01:27)
PYTEST EXIT 1
```

### Captured run — 2026-09-21T02:28:51Z

- **Command:** `python3 .tmp/hs202-followup/run-proof.py story02-green`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
PROOF LEG story02-green
ROOT /Users/karol/dev/tools/wt-202-01/.tmp/hs202-followup/story02
HEAD 3595fcb696c07ce8d01fad0da58396fb4fc5ef9e
SMOKE SHA256 1529454a786f613e1555df1091ffce3cd83f9b288a8936b74a0988ed66f6b530
ISOLATED HOME /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-followup-m0dhszom
COMMAND ['uv', 'run', 'pytest', '-q', '-s', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py', 'tests/unit/test_ux_canon_ratchet.py']
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-1440.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
PASS: Write a thought opens a note authoring surface
PASS: The edit has a new visible Kept receipt in its editor before Save
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/editor-kept-before-save-1440.png
PLANNED 127.0.0.1 sha256:adfd91308384de34ddcc2f04a65a2ece3b2d1a6ad9c430d09c08d982f4f6ea34
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-1440.png
RECEIPT succeeded sha256:adfd91308384de34ddcc2f04a65a2ece3b2d1a6ad9c430d09c08d982f4f6ea34 127.0.0.1
PASS: The open record shows the completed summary and actual host without a reload
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-1440.png
Notes query highlighted: ○ / Fence architecture note / NOTE
PASS: Typing Notes and Enter reaches notes
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-1440.png
FSHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-go-menu-393.png
PASS: New Note is visible and reachable in the folded Go menu
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/folded-menu-Desk-393.png
FAIL: Open is visible and reachable as an Object entry in Go
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Object-393.png
MENU GEOMETRY menu-Object {'x': 11, 'y': 877.5, 'width': 371, 'height': 28} {'height': 1404, 'scrollHeight': 1404, 'overflow': 'visible'}
FAIL: Close window is visible and reachable as a Window entry in Go
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/menu-Window-393.png
MENU GEOMETRY menu-Window {'x': 11, 'y': 1221.5, 'width': 371, 'height': 28} {'height': 1404, 'scrollHeight': 1404, 'overflow': 'visible'}
PASS: Write a thought opens a note authoring surface
PASS: The edit has a new visible Kept receipt in its editor before Save
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/editor-kept-before-save-393.png
PLANNED 127.0.0.1 sha256:ddbefc6e26251fcbd905e5d71c25522f8b2d2d355ef148ee6f40c613a584dda3
FAIL: The imported transcript exposes Run summary without a reload
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/planned-host-393.png
RECEIPT succeeded sha256:ddbefc6e26251fcbd905e5d71c25522f8b2d2d355ef148ee6f40c613a584dda3 127.0.0.1
PASS: The open record shows the completed summary and actual host without a reload
PASS: the persisted summary and run receipt agree with the planned host
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/summary-reopened-393.png
Notes query highlighted: ○ / Fence architecture note / NOTE
PASS: Typing Notes and Enter reaches notes
PASS: refind the saved note and its body in two navigation moves
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-01-fence/meeting-after-restart-393.png
F...ratchet: A1 175 -> 174 -- lower the ceiling
ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
.
=================================== FAILURES ===================================
________________________ test_first_use_fence[1440-900] ________________________
tests/e2e/test_hs202_first_use_smoke.py:579: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 1440: first-use steps failed: import-refresh
E   assert not {'import-refresh'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________________________ test_first_use_fence[393-852] _________________________
tests/e2e/test_hs202_first_use_smoke.py:579: in test_first_use_fence
    assert not failures, f"{width}: first-use steps failed: {', '.join(sorted(failures))}"
E   AssertionError: 393: first-use steps failed: import-refresh, menu-Object, menu-Window
E   assert not {'import-refresh', 'menu-Object', 'menu-Window'}
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]
FAILED tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]
2 failed, 4 passed in 72.14s (0:01:12)
PYTEST EXIT 1
```

### Captured run — 2026-09-21T02:30:40Z

- **Command:** `python3 .tmp/hs202-followup/run-proof.py inventory-strict`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
PROOF LEG inventory-strict
ROOT /Users/karol/dev/tools/wt-202-01-baseline
HEAD 50ca0dd6cf8f45a7b78576fbd3d995761be97001
SMOKE SHA256 1529454a786f613e1555df1091ffce3cd83f9b288a8936b74a0988ed66f6b530
ISOLATED HOME /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs202-followup-93ofga06
COMMAND ['uv', 'run', 'pytest', '-q', '-s', '--tb=short', 'tests/e2e/test_hs202_first_use_smoke.py', 'tests/unit/test_ux_canon_ratchet.py']
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/fixture-speech-kept-1440.png
PASS: fixture speech became visible text and a kept note; PCM samples 9898
PASS: engine setup completed visibly without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/engine-set-1440.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
PASS: Desk memory dock door fits and owns its hit target
PASS: Desk menu door is reachable
PASS: Desk menu content loaded
PASS: Object menu door is reachable
PASS: Object menu content loaded
PASS: Go menu door is reachable
PASS: Go menu content loaded
PASS: Window menu door is reachable
PASS: Window menu content loaded
FAIL: Write a thought opens a note authoring surface
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/thought-door-1440.png
FAIL: The edit has a new visible Kept receipt in its editor before Save
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/save-confirmation-1440.png
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/editor-kept-before-save-1440.png
PLANNED 127.0.0.1 sha256:40bbfc74fdb6ded618d7c0ccd9a254bdd8d0e9041d88d7189020eec11f5d24c1
FAIL: The imported transcript exposes Run summary without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/import-refresh-1440.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/planned-host-1440.png
RECEIPT succeeded sha256:40bbfc74fdb6ded618d7c0ccd9a254bdd8d0e9041d88d7189020eec11f5d24c1 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/record-refresh-1440.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/summary-reopened-1440.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/notes-query-1440.png
PASS: refind the saved note and its body in two navigation moves
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/note-after-restart-1440.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_1440_900_0/shots/meeting-after-restart-1440.png
VERIFIED exact expected failures: 1440 ['import-refresh', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door']
.SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/fixture-speech-kept-393.png
PASS: fixture speech became visible text and a kept note; PCM samples 10239
PASS: engine setup completed visibly without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/engine-set-393.png
PASS: Speak dock door fits and owns its hit target
PASS: Meetings dock door fits and owns its hit target
FAIL: Desk memory dock door fits and owns its hit target
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/dock-memory-393.png
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/folded-go-menu-393.png
FAIL: New Note is visible and reachable in the folded Go menu (missing from Go)
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/menu-Desk-393.png
FAIL: Open is visible and reachable as an Object entry in Go (missing from Go)
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/menu-Object-393.png
FAIL: Close window is visible and reachable as a Window entry in Go (missing from Go)
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/menu-Window-393.png
FAIL: Write a thought opens a note authoring surface
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/thought-door-393.png
RECOVERY: use New Note keyboard command after the recorded menu failure.
FAIL: The edit has a new visible Kept receipt in its editor before Save
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/save-confirmation-393.png
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/editor-kept-before-save-393.png
PLANNED 127.0.0.1 sha256:5df7abee67ba9dc4862d0a2b4a69728465ccd9970c41b49b19636722b7b7cea4
FAIL: The imported transcript exposes Run summary without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/import-refresh-393.png
RECOVERY: reopen the imported meeting after the recorded import refresh failure.
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/planned-host-393.png
RECEIPT succeeded sha256:5df7abee67ba9dc4862d0a2b4a69728465ccd9970c41b49b19636722b7b7cea4 127.0.0.1
FAIL: The open record shows the completed summary and actual host without a reload
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/record-refresh-393.png
RECOVERY: reopen the persisted meeting after the recorded refresh failure.
PASS: the persisted summary and run receipt agree with the planned host
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/summary-reopened-393.png
Notes query highlighted: ▧ / Change places / PROGRAM / ⌘⇧P
FAIL: Typing Notes and Enter reaches notes
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/notes-query-393.png
PASS: refind the saved note and its body in two navigation moves
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/note-after-restart-393.png
PASS: refind the meeting summary in two navigation moves; its receipt survives in the hub
SHOT /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9426/test_first_use_fence_393_852_0/shots/meeting-after-restart-393.png
VERIFIED exact expected failures: 393 ['dock-memory', 'import-refresh', 'menu-Desk', 'menu-Object', 'menu-Window', 'notes-query', 'record-refresh', 'save-confirmation', 'thought-door']
....ratchet: A3-prose 48 -> 43 -- lower the ceiling
ratchet: B 32 -> 30 -- lower the ceiling
.
6 passed in 92.95s (0:01:32)
PYTEST EXIT 0
```

### Captured run — 2026-09-21T02:36:58Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.UCrG6298Ga uv run pytest -q tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4df98eee75e3b1160a8903745689c11d834a2ba1

```text
..                                                                       [100%]
2 passed in 1.40s
```
