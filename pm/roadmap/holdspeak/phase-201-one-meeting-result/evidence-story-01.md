# Evidence - HS-201-01

- **Story:** HS-201-01 - The desk names the one thing it needs
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T22:47:08Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.NOSmwmJFDK PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text
......                                                                   [100%]
6 passed in 27.21s
```

### Captured run — 2026-09-19T22:47:39Z

- **Command:** `sh -c cd web && npx vitest run src/desk/chair/arrivalOneThing.test.tsx src/desk/setup.test.ts src/pages/cores/historyHeadline.test.ts 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text

 Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  16:47:39
   Duration  917ms (transform 609ms, setup 281ms, import 827ms, tests 41ms, environment 951ms)
```

## Counsel fix round

Astra's counsel on built (`checks/laneb-built-astra.md`, 2026-09-19) and
Muad'Dib's response 1, 3, 4, 5. Four fixes, each proved red first.

### 1. The row clears on the OPEN desk (Astra finding 1)

`web/src/desk/chair/ChairHome.tsx:451-489` — the assignment roster was read
once, on mount. It is now re-read on the hub's `desk_changed` frame
(trailing-debounced, as `useDeskChangedRefresh` does) and on `window`
focus, so the row goes when the owner comes back from the repair without
navigating. The glass rig no longer re-arrives: it assigns through the
real service, fires the browser's own focus event, and waits for the row
to disappear on the same page
(`tests/e2e/test_hs201_one_thing_glass.py:280-290`).

RED — the same rig against the pre-fix Chair (the refresh effect removed
from ChairHome.tsx, restored immediately after):

```text
$ HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=... uv run pytest -q \
    "tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_chair_names_the_blocker[1440]"
>           page.wait_for_function(
                """() => !document.querySelector("[data-testid='arrival-blocker']")""",
                timeout=15_000,
            )
tests/e2e/test_hs201_one_thing_glass.py:284:
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 15000ms exceeded.
FAILED tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_chair_names_the_blocker[1440]
1 failed in 19.98s
```

The roster assertions above that line PASSED in the same run: the product
had both capability heads assigned while the open Desk still drew the
blocker row. That is exactly the defect — the machine passed while the
owner's desk kept asking.

RED — the unit fences for the same defect
(`web/src/desk/chair/arrivalRefresh.test.tsx`, same pre-fix Chair):

```text
     × re-reads the roster when the window takes focus again 1034ms
     × re-reads the roster on the hub's desk_changed frame 6ms
 FAIL  src/desk/chair/arrivalRefresh.test.tsx > ... > re-reads the roster when the window takes focus again
AssertionError: expected <div data-testid="arrival-blocker">…(1)</div> to be null
 FAIL  src/desk/chair/arrivalRefresh.test.tsx > ... > re-reads the roster on the hub's desk_changed frame
TypeError: actual value must be number or bigint, received "undefined"
 Test Files  1 failed (1)
      Tests  2 failed (2)
```

### 2. An unknown is not a clear desk; speech joins the path (finding 3)

`web/src/desk/chair/meetingPathBlocker.ts` — the helper now answers with
every blocker in path order. A roster that has not been read (in flight,
or failed) is its own row, `Could not read setup`, with one library Button
that re-reads it; `speech.transcribe` with no effective assignment is its
own row, `No engine for speech`, with the same `Choose an engine` Button.
The summary predicate is unchanged (Astra finding 2: confirmed). The
speech predicate accepts ANY effective assignment, because an
owner-started recording resolves that capability through the ordinary
inheritance chain — only the SERVICE-fired paths need the exact head
(`holdspeak/services/inference_service_route_policy.py:198-254`).
The microphone action stays out of this story (ledgered as a doctor
concern).

RED — `web/src/desk/chair/arrivalOneThing.test.tsx:115` no longer blesses
unknown-as-clear:

```text
     × names the unknown as its own row when the roster could not be read 1003ms
     × draws a row when no engine transcribes speech 1007ms
     × draws BOTH rows when neither engine is assigned 7ms
 FAIL  ... > names the unknown as its own row when the roster could not be read
 FAIL  ... > draws a row when no engine transcribes speech
 FAIL  ... > draws BOTH rows when neither engine is assigned
 Test Files  1 failed (1)
      Tests  3 failed | 6 passed (9)
```

### 3. Inbound exposure is kept as its own token (finding 4)

`web/src/desk/setup.ts` — `inboundBadge()` / `inboundLine()` state who may
REACH this hub, from `web_bind` + `auth_token_set`
(`holdspeak/setup_status.py:176-177`), independent of the destinations.
The chrome carries `OPEN TO NETWORK` beside the egress chip
(`web/src/desk/components/DeskChrome.tsx:236-241`) and the Trust window
adds one line, `Open to the network: yes · Token: not set`
(`web/src/desk/components/TrustWindow.tsx:96-104`). The egress chip no
longer folds the inbound fact into `External reach enabled`.

RED:

```text
 FAIL  src/desk/setup.ts > inboundBadge — the hub is open to the network > ... (5 tests)
TypeError: inboundBadge is not a function
 FAIL  src/desk/components/__tests__/trustInbound.test.tsx > ... (2 tests)
TestingLibraryElementError: Unable to find an element by: [data-testid="trust-inbound"]
 Test Files  2 failed (2)
      Tests  7 failed | 3 passed (10)
```

### 4. Two labels this lane owns (response 5)

`web/src/desk/chair/ChairHome.tsx:2136` — `Develop a thought` →
`Write a thought`. `ChairHome.tsx:1755` — the Chair's own
`Untitled meeting` fallback → `Meeting with no title`. The rigs that name
those strings were updated: `tests/e2e/test_hs141_chair_geometry.py:158`,
`:189`, `tests/e2e/live170_walk.py:310`.

### GREEN

```text
$ cd web && npx vitest run src/desk/chair/arrivalOneThing.test.tsx \
    src/desk/chair/arrivalRefresh.test.tsx src/desk/setup.test.ts \
    src/desk/components/__tests__/trustInbound.test.tsx --maxWorkers=2
 Test Files  4 passed (4)
      Tests  21 passed (21)
   Duration  1.56s
```

```text
$ cd web && npx tsc --noEmit
tsc exit=0
```

```text
$ cd web && npx vitest run src/desk --maxWorkers=2     # no collateral damage
 Test Files  170 passed (170)
      Tests  1508 passed (1508)
```

```text
$ HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
    uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py
..........                                                               [100%]
10 passed in 34.97s
```

### Shots (assets/story-01-shots/)

- `chair-before-repair-1440.png`, `chair-before-repair-393.png` — the two
  rows before the repair, on the desk that is never navigated again.
- `chair-assigned-1440.png`, `chair-assigned-393.png` — the SAME page
  after the assignment: no SETUP section, `Nothing needs you`.
- `chair-speech-row-1440.png`, `chair-speech-row-393.png` — the SETUP
  section: `No engine for speech` and `No engine for summaries`, one
  library Button each.
- `chair-unknown-setup-1440.png`, `chair-unknown-setup-393.png` — the
  roster read refused: `Could not read setup` with `Try again`, and the
  headline is `1 need you`, never the all-clear.
- `open-to-network-1440.png`, `open-to-network-393.png` — `OPEN TO
  NETWORK` in the chrome beside `⌂ THIS DEVICE`, with the Trust window's
  line `Open to the network · yes · Token: not set`.
- `chair-blocker-*.png`, `meetings-failed-*.png`, `chip-and-trust-*.png`
  re-shot by the same run.

### Unknown

- No live metal: the glass rigs run on a cold isolated HOME with the
  concierge hardware scan stubbed, and no engine executes.
- The `OPEN TO NETWORK` rig states the hub's trust block as an
  off-loopback bind with no token (`_trust_block` patched at
  `setup_status.py:114`); the hub itself still binds the loopback in the
  rig. The two fields the face reads are the real ones.
- The `desk_changed` wire is proved by unit fence only: an assignment
  write emits no such frame today
  (`holdspeak/web/routes/inference_assignments.py:71-79`), so the glass
  leg proves the focus wire.
- Full suite not run in this lane (orchestrator's job).

## Counsel fix round — second pass

Two rulings from the orchestrator on the questions the first pass raised.

### Ruling 1 — a pending read draws nothing; only a FAILED read speaks

`web/src/desk/chair/meetingPathBlocker.ts:56-58` — `pending` returns no
rows at all (tenet 3: no noise on every arrival), `failed` returns the one
`Could not read setup` row with `Try again`. The all-clear still waits for
the roster: `web/src/desk/chair/ChairHome.tsx:566-575` withholds
`Nothing needs you` while the read is in flight.

### Ruling 2 — one filled primary: both halves missing is ONE row

`web/src/desk/chair/meetingPathBlocker.ts:70-78` — with NEITHER engine
assigned the Chair draws one row, `No engine yet`, with one
`Choose an engine` Button. `No engine for speech` and
`No engine for summaries` are drawn only when exactly one half is
missing. The glass rig now asserts `.btn--primary` count is 1 on the whole
face (`tests/e2e/test_hs201_one_thing_glass.py:212-214`) and repairs the
two halves ONE at a time on the open desk, so the row changes its words
and then goes — twice, with no navigation
(`tests/e2e/test_hs201_one_thing_glass.py:262-300`).

RED (second pass):

```text
     × draws no setup row while the roster read is still in flight 1008ms
     × draws ONE row when neither engine is assigned 1006ms
 FAIL  src/desk/chair/arrivalOneThing.test.tsx > ... > draws no setup row while the roster read is still in flight
AssertionError: expected <div data-testid="arrival-blocker">…(1)</div> to be null
 FAIL  src/desk/chair/arrivalOneThing.test.tsx > ... > draws ONE row when neither engine is assigned
TestingLibraryElementError: Unable to find an element with the text: No engine yet.
 Test Files  1 failed (1)
      Tests  2 failed | 8 passed (10)
```

GREEN (second pass):

```text
$ cd web && npx tsc --noEmit
tsc exit=0

$ cd web && npx vitest run src/desk/chair/arrivalOneThing.test.tsx \
    src/desk/chair/arrivalRefresh.test.tsx src/desk/setup.test.ts \
    src/desk/components/__tests__/trustInbound.test.tsx --maxWorkers=2
 Test Files  4 passed (4)
      Tests  22 passed (22)

$ cd web && npx vitest run src/desk --maxWorkers=2
 Test Files  171 passed (171)
      Tests  1511 passed (1511)

$ HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
    uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py
..........                                                               [100%]
10 passed in 40.05s
```

### Shots re-shot by that run (assets/story-01-shots/)

- `chair-blocker-1440.png`, `chair-blocker-393.png` — the cold desk: ONE
  row, `No engine yet`, ONE filled Button on the whole face.
- `chair-before-repair-1440.png`, `chair-before-repair-393.png` — the same
  state, immediately before the repair.
- `chair-no-engine-yet-1440.png`, `chair-no-engine-yet-393.png` — the
  SETUP section alone in that combined state.
- `chair-speech-row-1440.png`, `chair-speech-row-393.png` — the SAME open
  desk after only the summary engine is assigned: the row now says
  `No engine for speech`.
- `chair-assigned-1440.png`, `chair-assigned-393.png` — after the speech
  engine too: no SETUP section, `Nothing needs you`.
- `chair-unknown-setup-*`, `open-to-network-*`, `meetings-failed-*`,
  `chip-and-trust-*` re-shot unchanged in meaning.

## Full-suite fallout

The orchestrator's full run in this worktree: 19 failed / 11122 passed.
One (`test_hs153_practice_glass` guardrail) is main's own. The other 18,
classified per ORCHESTRATION.md §4 — (a) the test asserts the OLD posture,
(b) a REAL regression the change exposed, (c) not this lane's.

| Test | Class | Reason | Change |
| --- | --- | --- | --- |
| `test_hs144_door_glass::test_hs144_door_empty_and_error_shots[1440]`, `[393]` | a | Asserts `Nothing needs you` on a cold HOME. Under HS-201-01 a desk with no meeting engine is NOT clear; the Door is this rig's subject, setup is not. | Pins both halves of the meeting path before the arrival (`tests/e2e/test_hs144_door_glass.py:398`). |
| `test_hs145_door_polish_glass::test_hs145_connect_calendar_affordance_and_quiet_state` | a | Same: `Nothing needs you` on a quiet calendar. The calendar rail is the subject. | Pins the path (`tests/e2e/test_hs145_door_polish_glass.py:324-326`). |
| `test_hs170_arrival_glass::test_arrival_quiet_1440`, `_393` | a | Same: the quiet arrival's headline. | Pins the path (`tests/e2e/test_hs170_arrival_glass.py:470-473`). |
| `test_hs171_command_deck_glass::test_command_deck_projects_1440`, `_393` | c | NOT this lane's. The rig seeds every Watch with a FROZEN `last_success_at = "2026-09-04T10:00:00"`; the coverage horizon is 6 hours (`needs_you_aggregate.py:72`, `:671-687`), so fifteen days later every seeded Room reads `stale` and the deck draws a STALE token on the Room the rig calls quiet (measured: the badge text was `'STALE'`). Lane B changes nothing on that path — `git diff origin/main...HEAD` touches neither `needs_you_aggregate.py` nor `DeskToolShelf.tsx`. | Fixed at source: the seed stamps `datetime.now(timezone.utc)` (`tests/e2e/test_hs171_command_deck_glass.py:102-108`). UTC, because a naive value in that column is read as UTC (`project_service.aware_iso`) while the rigs pin a fixed-offset desk zone. |
| `test_hs200_attention_glass::{test_one_project,test_three_projects,test_long_row}` × `{1440,393}` | **b** | **A REAL regression my row exposed.** `_primaries()` asserts exactly ONE filled primary on the whole face (`:463`), and the quiet rig asserts ZERO (`:694`): the ratified HS-200-15 law gives the filled primary to the first attention row. My SETUP row's `Choose an engine` was a second one (`['… :: Choose an engine', '… :: Open']`). | **Product fixed:** the SETUP verb is now the library Button's default species, never a filled primary (`web/src/desk/chair/ChairHome.tsx:862-876`). The fences that state the law were flipped with it (`web/src/desk/chair/arrivalOneThing.test.tsx:168-171`, `tests/e2e/test_hs201_one_thing_glass.py:212-216`). Also pinned the engines so these rigs' faces and shots stay the ratified ones. |
| `test_hs200_attention_glass::test_quiet_all_clear` × `{1440,393}` | a | Asserts `Nothing needs you` on a cold HOME. | Pins the path in `_arrive` (`tests/e2e/test_hs200_attention_glass.py:311-316`). |
| `test_hs200_coverage_glass::test_arrival_complete_empty_1440`, `_393` | a | Same all-clear assertion. | Pins the path in `_arrive` (`tests/e2e/test_hs200_coverage_glass.py:158-163`). |
| `tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date` | c | NOT this lane's, and already paid on main: `97d10e1a "HS-201: regenerate the UAT build ledger for Phase 201"`, which `feat/hs-201-b` does not yet contain (`git diff origin/main...HEAD -- uat/` is empty). | None. The orchestrator's merge of `origin/main` pays it. |

### The fixture question, answered

In every e2e rig above the hub DOES serve `/api/inference/assignments`: it
answers a real roster that names no engine, so the SETUP row was TRUE, not
a fixture artifact. The rigs are therefore pinned (they assign both
capability heads through the real service) rather than the product being
taught to treat a cold desk as clear — a cold desk is exactly what this
story exists to name. The only fixtures that never served the route were
the jsdom siblings `arrivalAttention.test.tsx` / `arrivalCoverage.test.tsx`;
those now return an empty roster (a read that LANDS and names nothing), so
their subject stays the attention band.

One shared seeding helper, so the rigs do not each grow a copy:
`tests/e2e/glass_infra.py:360-434` — `engine_profile()`, `assign_engine()`,
`seed_meeting_engines()`. `tests/e2e/test_hs201_one_thing_glass.py` now
imports them instead of holding its own.

### GREEN

```text
$ HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
    uv run pytest -q tests/e2e/test_hs144_door_glass.py \
      tests/e2e/test_hs145_door_polish_glass.py tests/e2e/test_hs170_arrival_glass.py \
      tests/e2e/test_hs171_command_deck_glass.py tests/e2e/test_hs200_attention_glass.py \
      tests/e2e/test_hs200_coverage_glass.py tests/e2e/test_hs201_one_thing_glass.py
.........s.......................................                        [100%]
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:181: HS-170: door-board scroll-hint PARKED
48 passed, 1 skipped in 214.61s (0:03:34)
```

```text
$ cd web && npx tsc --noEmit
tsc=0

$ cd web && npx vitest run src/desk --maxWorkers=2
 Test Files  171 passed (171)
      Tests  1511 passed (1511)
```

### Tracked shots restored

These rigs re-render tracked PNGs from OTHER phases. All 31 were restored
with `git show HEAD:<path> > <path>` after the last run (never
`checkout --`): 11 under `phase-144-the-dashboard-door/assets/`, 4 under
`phase-145-the-door-polish/assets/story-03-shots/`, 6 under
`phase-170-the-great-pass/assets/story-04-shots/`, 2 under
`phase-171-the-heartbeat/assets/story-07-shots/`, 8 under
`phase-200-the-working-practice/assets/story-07-shots/`.

### Unknown

- Six UNTRACKED PNGs from other phases' rigs sit in the tree
  (`phase-153-.../door-no-chip-*`, `phase-170-.../census/change-places-*`,
  `phase-171-.../build-command-deck-{archive,search}-1440.png`). Two of
  them are from the `hs171` rig I ran; the rest predate this lane's runs.
  Nothing was deleted (the never-delete law).
- The full suite was not re-run here (orchestrator's job); only the files
  named in the fallout list.

## Counsel fix round — third pass

Astra's round-2 conditions.

### Condition 1 — the product's OWN return signal, not a synthetic focus

`web/src/desk/chair/ChairHome.tsx:479` — the Chair's assignment re-read is
now subscribed to `onReturnToTask`, the `holdspeak:settings-updated` signal
(`web/src/desk/returnToTask.ts:37`, dispatched at `:113`) that Models
announces the moment it applies a set
(`web/src/features/concierge/useConciergeController.ts:507`). The
`desk_changed` frame and the window-focus wires stay; they cost nothing.

The glass rig no longer dispatches a focus event. It opens Models from the
row, closes it, assigns through the real service, and then fires the
product's own signal on the same open page — `_settings_updated()`,
`tests/e2e/test_hs201_one_thing_glass.py:92-106`, used at `:246` and
`:290`. This rig stubs the Concierge hardware scan (`_quiet_concierge`), so
the Models face has no proposal row to apply; the rig therefore fires the
same event Models fires rather than the Apply button. Stated as a limit,
not as a proof of the Models face (story 05 owns that).

RED (subscription removed, everything else as shipped):

```text
$ cd web && npx vitest run src/desk/chair/arrivalRefresh.test.tsx
     × re-reads the roster on the product's settings-updated signal 1011ms
AssertionError: expected <div data-testid="arrival-blocker">…(1)</div> to be null
 Test Files  1 failed (1)
      Tests  1 failed | 2 passed (3)

$ HOME=$(mktemp -d) … uv run pytest -q \
    "tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_chair_names_the_blocker[1440]"
tests/e2e/test_hs201_one_thing_glass.py:260:
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 15000ms exceeded.
```

### Condition 2 — OPEN TO NETWORK inside the width at 393

Measured before the fix: the right cluster reached `right=405.7` on a
393px bar (the desk's own overhang there is `395.7` WITHOUT the token), and
Search was pushed off the edge. The fix follows the bar's existing
doctrine — the egress badge already clamps to 88px with its words kept in
its title (`chrome-menus.css`, the 720px rule):

- `web/src/desk/components/chrome-menus.css:912-925` — at ≤720px the
  inbound token keeps its lamp and drops its words (`font-size: 0`), and
  the badge beside it gives back the lamp's width (`max-width: 80px`), so
  the bar is no wider than it is without the token.
- `web/src/desk/components/DeskChrome.tsx:236-250` — the words live in
  `aria-label` and the reason in `title` at every width.
- Fence: `tests/e2e/test_hs201_one_thing_glass.py:466-486` asserts the
  accessible name carries `OPEN TO NETWORK` at both widths, the words are
  visible above 720px, the document does not scroll horizontally, and
  Search is whole and on the bar.

### GREEN

```text
$ cd web && npx tsc --noEmit
tsc=0

$ cd web && npx vitest run src/desk/chair/arrivalOneThing.test.tsx \
    src/desk/chair/arrivalRefresh.test.tsx src/desk/setup.test.ts \
    src/desk/components/__tests__/trustInbound.test.tsx --maxWorkers=2
      Tests  23 passed (23)

$ cd web && npx vitest run src/desk --maxWorkers=2
 Test Files  171 passed (171)
      Tests  1512 passed (1512)

$ HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
    uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py
..........                                                               [100%]
10 passed in 36.46s
```

### Shots

- `open-to-network-1440.png` — the words on the desktop bar beside
  `⌂ THIS DEVICE`, with the Trust window's line.
- `open-to-network-393.png` — the lamp alone on the phone bar (words in
  the title and the accessible name), Search whole, and the same Trust
  line in words.
- `chair-before-repair-*`, `chair-no-engine-yet-*`, `chair-speech-row-*`,
  `chair-assigned-*`, `chair-blocker-*`, `chair-unknown-setup-*`,
  `meetings-failed-*`, `chip-and-trust-*` re-shot by the same run.
- No tracked PNG from another phase was touched by this run (checked:
  zero dirty outside `phase-201-one-meeting-result/`).
