# Terminals implementation record

Owner request: independently implement the useful parallel-terminal workflow
from nodeterm inside HoldSpeak, replacing the cramped panes interaction.

## Built

The Terminals application is in Go > Work and Search, with a `/terminals` deep
link. It discovers local tmux panes, groups them by folder, finds sessions by
name/agent/command/folder, opens independent native Desk windows, starts a shell
in a chosen local folder, and offers the existing Start an agent flow. Existing
Panes, Agents and agent-session doors lead to this application.

Each terminal owns its target, output subscription, grant, input queue and draft.
The existing compositor owns focus, movement, resize, tiling, minimization and
hub-backed placement. Closing the view leaves the process alive. Terminal-only
reloads restore without requiring the inventory window to remain mounted.
Process fingerprints prevent an old window from selecting a successor with a
reused tmux pane number. Input uses the existing authority and acknowledged
command boundary; an unknown outcome is not automatically retried.

The shared PaneWell remains read-only by default. Its opt-in input and quiet
header modes let the terminal use the same renderer without a second terminal
framework. Find is available on demand. A failed message keeps its draft, and
an older acknowledgement cannot erase a newer edit.

## Verification

All runtime tests use the machine-wide test lock and isolated HOME/DB. Real
terminal tests additionally use a private short `TMUX_TMPDIR`, unset `TMUX`,
and kill only their own explicitly identified socket at teardown. No owner
terminal, agent CLI, microphone, calendar, remote engine or provider is used.
Hard-coded fixture producers use a local `.venv` link to the same complete
shared runtime as the test command. The incomplete worker-created environment
was parked under `.tmp/`; its missing NumPy caused the first broad fixture
failures. No product assertion was changed to accommodate that setup issue.

- Focused backend: 101 collected, 101 passed. Logs:
  `.tmp/terminal-workspace/focused.collect.log` and `focused.run.log`.
- Existing real-tmux transport plus new discovery: 12 collected, 12 passed.
  Logs: `.tmp/terminal-verification/backend-live-{collection,run}.log`.
- Direct server deep-link regression: 6 passed. Log:
  `.tmp/terminal-workspace/pages.run.log`.
- Focused controller/renderer and swallowed-write guard: 33 passed in four
  Vitest files; TypeScript passed. Exact command and tail: `VERIFICATION-AUDIT.md`.
- Final inventory/menu integration: 125 passed in eight files, plus six
  single-window/recents checks. Exact command and tail: `UI-AUDIT.md`.
- Final terminal/composition regressions: 32 collected, 32 passed. Logs:
  `.tmp/terminal-verification/backend-final/composition-final.{collect,run}.log`.
  This repeats the grant/correlation cases: a same-number process respawn
  revokes its typing grant, and hook state follows existing idle/dead decay.
- Factory route contracts: 42 collected, 42 passed, including explicit cwd
  forwarding. Log: `.tmp/terminal-verification/backend-final/coder-steer.run.log`.
  The earlier `respawn.run.log` was overwritten by an interrupted follow-up;
  the final 32-case run supersedes it.
- Real browser: 2 collected, 2 passed at 1440×900 and 393×852. Actual shell
  output proves separate A/B input. The walk proves folder selection,
  Escape and shared Keys menu ownership, Find, native tiling and a real grip
  resize to a narrow/short desktop window, persisted geometry, terminal-only reload,
  close-without-kill and reopening. It checks frame/footer bounds against the
  dock and terminal text contrast (17.9:1). Logs:
  `.tmp/terminal-verification/browser-{collection,run}.log`.
  Inspected runtime shots: `.tmp/evidence-shots/terminal-workspace/workspace-1440.png`
  and `workspace-393.png`, plus `workspace-narrow-desktop.png`; adjacent
  `observation-*.json` records the private
  producer, DB, target IDs, output markers and measured layout.
- Public documentation navigation: 74 documents passed. Ruff and
  `git diff --check` passed.

The final required quick check is GREEN. Its full logs are in
`.tmp/terminal-verification/quick-final/`. No deployment, postmerge full tape, provider
execution or owner aesthetic acceptance is implied by local verification.

Supplementary web checks expose existing repository debt: `tokens:gate`
reports 183 raw CSS values; `guard:architecture` reports existing injection,
API-client and private-import findings outside this lane. No Terminals path is
among those findings. `tokens:check` also fails on unchanged baseline files:
the committed CSS has `--desk-badge-slot-w`, which its JSON source lacks.
Generating in a disposable copy reproduces that single removed declaration;
the TypeScript mirror is identical. This lane neither deletes the badge token
nor changes a guard/allowlist to hide these failures. Logs:
`.tmp/terminal-verification/{tokens-gate,architecture}.log`.

### Findings fixed during the real-browser walk

The first walk exposed a missing server page allowlist entry: the registered
React route returned 404 on a direct visit. The next walk proved real shell
input but exposed missing shared frame material/positioning, nearly invisible
terminal text after the global paper/ink theme change, and the phone composer
extending behind the dock. Those failures were retained as regression assertions
rather than removed from the walk. Initial failure log:
`.tmp/terminal-verification/browser-run-initial-404.log`.
The intermediate layout failure and shots are retained as
`browser-run-initial-layout.log` and `failed-layout-{1440,393}.png` in the
same log/shot directories.

### First integrated quick check

The first complete check is retained in
`.tmp/terminal-verification/quick-first/`. It passed the build and 128 Desk
sweep cases, then failed stale menu/factory mock expectations and three real
guards: swallowed disarm failure, new in-route service construction, and new
copy/metadata violations. The fixes preserve exact membership/status
assertions, return disarm acknowledgement/failure, compose discovery through
`DeliveryService` over the same target registry, and use shared metadata plus
clear retained-work/retry copy. No guard ceiling or residual ledger was raised.
The live inventory now follows relevant agent bus events and retains cached
descriptors on a failed inventory refresh. A quiet read cannot tear down an
otherwise healthy terminal controller.

### Acknowledged typing state

The second quick check passed 4,743 web tests, 192 web guards, 128 Desk sweep
cases, 27 canon checks and 1,185 repository guards. Its affected Python run
passed 862 cases and failed the desktop terminal observation under load. The
browser helper requested typing permission and immediately typed without
waiting for the rendered grant acknowledgement. It now waits for **View only**
before focusing and typing; the assertion still requires the exact output line
in the real target, and failure captures both panes and the visible state.

The button now shows shared pending feedback and rejects a duplicate press
until that acknowledgement. Focus remains an explicit pane click; a late reply
never performs asynchronous autofocus. The focused six-case app run and type
check pass. The final integrated run below supersedes the second red run, kept
in `.tmp/terminal-verification/quick-second/`.

## Scope and remaining work

This is an independent HoldSpeak implementation of workflow ideas. Reference:
[nodeterm](https://github.com/eneskirca/nodeterm), README and LICENSE at
`758aae867b65cc7fe1c5b7521d4ba82fecce7c95`. No upstream implementation or assets
were copied. The new workspace uses HoldSpeak's React/xterm/tmux/hub stack.

Output remains bounded recent-screen polling, not a complete transcript or a
byte-perfect PTY stream. Resizing the view does not resize the host PTY. Only
local terminals with an authenticated output path are offered. A browser view
can survive reload while its process lives; machine reboot restoration is not
implemented. The existing agent launch path is reused; no live agent/provider
launch was part of this verification.

Agent hook records do not contain a process fingerprint. Their labels are
correlated metadata, not identity proof; fresh records with matching coordinates
can still outlive their process until the registry's normal decay. Terminal
target identity and typing-grant checks use the live process independently.

The audit reports are historical proposals plus implementation reports. Their
initial holds were resolved by the settled design and the owner's implementation
request. The verification audit's suggested premerge owner screenshot gate is
superseded by the current fast cycle: technical verification precedes merge;
the owner judges appearance on the deployed Desk. This record does not claim
that later acceptance.

## Final required check and ship

`DESK_SWEEP_SHOTS=1 QUICK_TESTS="tests/e2e/test_terminal_workspace_glass.py
tests/integration/test_delivery_terminal_live.py
tests/integration/test_coder_steering_live.py" scripts/quick_check.sh origin/main`
ran with the complete shared Python runtime, this checkout on PYTHONPATH and
the bundled Node runtime on PATH. The script manages its own lock and HOME.

```text
build ok
432 Vitest files: 4,744 passed
19 web-guard files: 192 passed
affected Python: 863 passed, 1 intentional YOLO-contract skip
Desk sweep: 128 passed
canon guards: 27 passed
repository guards: 1,185 passed
QUICK CHECK GREEN
```

The final browser build is newer than the final terminal source, including
the pending-state change without asynchronous autofocus. Desktop, phone and
narrow-desktop screenshots were inspected. TypeScript, Ruff, diff checks and
74-document public navigation passed. No new ceiling, allowlist or residual
ledger entry was added. Supplementary pre-existing web-quality debt remains
listed above; GREEN refers to the required quick check, not every optional CI
job in the repository.

PR: [#1652](https://github.com/karolswdev/HoldSpeak/pull/1652), branch
`feat/terminal-workspace`. The lane integrated main through `d71467e73`; main
then gained the non-overlapping PG21 change `4b2c7b5d2`, whose changed paths were
inspected. GitHub's PR record is the source of truth for the eventual merge
revision. Deployment, the main watcher's full tape and owner appearance
acceptance are not claimed by this local result.
