# Continuous terminals and host size

2026-10-30. Implementation brief for `feat/terminal-live`.
Status: built. Required quick check GREEN; owner appearance acceptance is open.

## The job

Open a terminal, press Type, and work with continuous output. Resize its Desk
window and have the host terminal follow the active typing view. Keep selection,
scrollback, the shell and unrelated views through ordinary output and reconnects.
The owner explicitly asked to include this improvement in the connected workspace.

This serves the Seven Tenets: remove first-use friction, expose one clear act,
compose the shared framework and keep native Workbench behavior. The Desk owns
the windows and their placement. The existing Type act supplies input authority.

## Settled design

Use tmux control mode for actual output bytes. Preserve existing pane pipes.
Keep the legacy snapshot subscription for its existing consumers. Native
Terminals uses a target-scoped, authenticated HTTP NDJSON subscription through
the common API boundary. It does not add a second general WebSocket or broadcast
terminal output to all Desk clients.

A stream has its own identity, sequence and bounded replay. Bootstrap and resync
come from a real current screen. Subsequent frames carry actual output bytes,
encoded for safe transport. A gap causes an explicit resync. Reader shutdown
releases the control client, not the shell. Terminal content stays ephemeral.
Drain each output batch before verifying its immutable target, then emit it.
A reused pane or respawned process cannot inherit an old window's subscription.
Blocking process and identity work stays off the hub event loop.

The active Type-granted, visible front view supplies dimensions from its local
pixel area. Read-only views use the host geometry. Size changes are coalesced
and pass through a typed `process.resize` operation and the existing command
receipt machinery. Recheck the Type grant and target at execution. A successful
receipt describes verified host dimensions. A refused or uncertain resize stays
visible and has a useful retry. It cannot change the input target or focus.

The shared xterm renderer accepts incremental output as an opt-in species seam.
Existing snapshot consumers keep their behavior. Preserve bytes through Unicode
chunk boundaries, ANSI cursor/mode changes and alternate screen operations.
React batching and lazy mounting must not discard intermediate output.

Design reference: [tmux control mode](https://github.com/tmux/tmux/wiki/Control-Mode).
The protocol supplies command response blocks and asynchronous pane output;
HoldSpeak owns the HTTP framing, lifecycle, authority and replay design above.

## Verification target

Use the existing terminal app/controller and real private-shell browser cases,
plus focused transport/kernel tests. Prove ordered bursts, snapshot boundaries,
resume and overflow resync, cleanup, generation refusal, actual `stty size`,
independent views, failed resize retry, retained Message drafts, selection and
focus at 1440, 393 and a narrow desktop frame. Default engine mode is `none`.
Use the machine test lock and isolated state for every run. No provider, owner
tmux, physical microphone, remote destination or owner's DB is a test target.

## Built and verified

Native Terminals now uses `terminal_live.py` and the authenticated NDJSON route.
The shared xterm species appends output bytes, consumes renderer device queries,
and measures desired size separately from actual host geometry. A verified
`process.resize@1` receipt updates that geometry. Refusal keeps the host size.
Input and resize share a per-target command lock, so both cannot claim the same
sequence. Existing snapshot consumers keep their transport.

Disconnect cancels the off-thread iterator and wakes its reader. A short idle
grace retains bounded replay. Hub stop closes the shared service before Uvicorn
drains connections; shutdown also refuses a control client still starting.
Shells and existing pane pipes survive output-client cleanup.

The required `DESK_SWEEP_SHOTS=1 scripts/quick_check.sh origin/main` passed:

- Production build; 3,863 UI tests in 329 files; 192 web guards.
- 5,264 affected Python tests; three existing posture/model skips.
- 129 Desk sweep cases at desktop/phone sizes; 27 canon guards; 1,194 repository guards.
- Logs: `.tmp/terminal-live/quick-merge/`.

The legacy live-LAN summary leg was explicitly deselected in this non-provider
run; its controlled stub producer remained selected. That legacy leg still
needs an explicit opt-in switch. One background Thread test emitted a missing `deployment_revisions` table
warning; no assertion failed. That warning remains open.
Full-file web-server lint retains an unchanged `E731` at its existing notification
lambda. New terminal Python paths/tests pass Ruff; TypeScript `noEmit` passes.

The final test producer uses Python 3.10-compatible byte construction. Its six
real private-tmux cases passed again after that fixture-only cleanup; collection
and run tails are in `.tmp/terminal-live/transport-compat/`.

Real browser observations use an isolated hub/database and private tmux, engine
mode `none`. The measured xterm DOM grid, receipt, tmux and `stty` agree: 64×14 in
the narrow desktop terminal on a 1440 viewport, 52×29 on a 393 viewport. Read-only
panes remain 100×30. Both observations report no page errors. The active captures
were inspected:

- `.tmp/evidence-shots/terminal-live/live-terminal-active-1440.png`
- `.tmp/evidence-shots/terminal-live/live-terminal-active-393.png`
- `.tmp/evidence-shots/terminal-live/observation-{1440,393}.json`

These are test captures, not owner aesthetic acceptance. Resizing supports an
independent single-pane tmux window; split layouts receive a named refusal and
retain their geometry. Physical devices, provider execution, SSH, reboot recovery
and a saved complete transcript are outside this slice. Deployment and the
main watcher's postmerge tape remain unverified at handover.
