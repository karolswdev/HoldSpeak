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

- Focused backend: 101 collected, 101 passed. Logs:
  `.tmp/terminal-workspace/focused.collect.log` and `focused.run.log`.
- Existing real-tmux transport plus new discovery: 12 collected, 12 passed.
  Logs: `.tmp/terminal-verification/backend-live-{collection,run}.log`.
- Direct server deep-link regression: 6 passed. Log:
  `.tmp/terminal-workspace/pages.run.log`.
- Focused controller/renderer: 24 passed in three Vitest files; TypeScript
  passed. Exact command and run tail: `VERIFICATION-AUDIT.md`.
- Final grant/correlation regressions: 12 collected, 12 passed. Logs:
  `.tmp/terminal-workspace/respawn.{collect,run}.log`. A grant pins the process
  fingerprint; a respawn with the same pane number revokes it. Hook state uses
  the existing idle/dead decay, and conflicting or ended records are ignored.
- Real browser: 2 collected, 2 passed at 1440×900 and 393×852. Actual shell
  output proves separate A/B input. The walk proves folder selection,
  Escape ownership, native tiling, persisted geometry, terminal-only reload,
  close-without-kill and reopening. It checks frame/footer bounds against the
  dock and terminal text contrast (17.9:1). Logs:
  `.tmp/terminal-verification/browser-{collection,run}.log`.
  Inspected runtime shots: `.tmp/evidence-shots/terminal-workspace/workspace-1440.png`
  and `workspace-393.png`; adjacent `observation-*.json` records the private
  producer, DB, target IDs, output markers and measured layout.
- Public documentation navigation: 74 documents passed. Ruff and
  `git diff --check` passed.

The final required quick-check results are recorded below after
the final implementation run. No deployment, postmerge full tape, provider
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

## Ship

Pending final required quick check and PR integration.
