# Terminals — native parallel workspace

Owner request, 2026-10-30: implement a generous parallel implementation inspired
by nodeterm; the current panes are unusable. This request scopes the product
implementation lane. Astra coordinates scoped workers and verifies it.

## Job and settled direction

See several real sessions, know which needs attention, type into one, arrange
it beside another, close and reopen a view without ending its work. Can the
owner do that on a Tuesday without learning pane IDs or an arm-strip console?

Use the Desk as the spatial canvas. A new **Terminals** inventory is a normal
manifest application; each opened terminal is a separate `DeskWindowFrame`.
Reuse OS focus, drag, resize, Zoom, Stage/Overview, tiling and durable hub window
rows. Do not build another nested window manager or graph canvas.

This applies Tenets 3, 5, 6 and 7: fewer interfaces, shared framework, native
Workbench behavior, useful parallel architectural work. Tenets 1, 2 and 4 keep
the flow small and the words plain. Current fast cycle governs shipping; the
canvas sets direction, not owner aesthetic acceptance.

## Inspiration and boundary

Reference: https://github.com/eneskirca/nodeterm, README and License inspected
at `758aae867b65cc7fe1c5b7521d4ba82fecce7c95`. Adopt workflow ideas: spatial
persistent sessions, visible agent states, focus, voice draft input and clear
close-versus-stop semantics. No upstream implementation source or assets are
used. Its BUSL grant restricts competing hosted/embedded use. HoldSpeak keeps
its React/xterm/tmux/hub stack and its own component material.

Do not copy upstream boards, an Electron runtime, an editor, licensing logic,
remote relay or a parallel source-control system. Existing Projects, agents,
repositories and Programs retain those jobs.

## Surface

- **Go > Work > Terminals**, also Search and `/terminals` deep link. Keep the
  old `panes` launcher as a compatibility door into this same application;
  park its cramped transient picker.
- Inventory: one Toolbar (New terminal, Start an agent, Refresh, Tile terminals),
  an in-flow search/filter and rows grouped by session/project path where known,
  one StatusBar. Show label, command/agent, truthful state, folder, Open/Focus.
  New shell asks for a name and optional local folder in place. Start an agent
  reuses the existing StartAgent composition and real handoff path.
- Each terminal: normal OS title bar, a quiet Toolbar with Enable typing /
  View only and Keys, a dark xterm screen, optional voice/text composer, one
  StatusBar for Live/Not connected/Not sent and input posture. Do not repeat
  the old token forest, gauges and raw metadata. Failure retains composition.
- All open terminals remain independent. Clicking one targets that instance;
  keyboard input is accepted only from its focused xterm. Focus changes never
  redirect pending input. Keys use the existing named/literal allow-list.
- Close means close view only. Do not call any kill endpoint on close,
  unmount, minimized state, reload or discovery absence. Explicit interrupt
  is Ctrl-C; any kill uses the existing granted/confirmed lifecycle path.
- On phone, the inventory opens one normal compact terminal sheet at a time;
  Back returns to the same inventory. Keep 44 px controls and legible text.
  A terminal can scroll horizontally as an intentional code well. Do not
  shrink terminal text below the type floor to fake desktop tiling on phone.

Canvas: `canvas.html`. It is a static material/direction sketch, not a runtime
or an owner acceptance claim. Active examples use the production kit.

## Contracts and ownership

### Backend

Extend the existing delivery-terminal router with
`GET /api/delivery/terminal/sessions` using its already-composed target registry.
No new DB or workspace JSON file. The new endpoint returns:

```text
{status: "ok" | "tmux_absent" | "error", detail?: string, sessions: [{
  id: opaque stable fingerprint ID (safe [A-Za-z0-9_-], <= 100 chars),
  label: human session/title, session: tmux session name,
  key: existing steering key (hook key when correlated, otherwise pane:%N),
  agent: name or "pane", command: current command, current_path: folder,
  state: truthful hook state or "live" for an unclassified live shell,
  target: {node_id: "local", target_id: opaque ID, target_generation: opaque},
  pane_id: canonical pane ID (compatibility transport field)
}]}
```

Metadata is not identity: rename/chdir/title/command do not change `id`.
Fingerprint includes tmux server instance and pane process identity, so a reused
`%N` after restart/respawn cannot restore as the previous terminal. Strengthen
TerminalTargetRegistry verification to bump generation on fingerprint changes,
while keeping existing fake resolver compatibility explicit in tests.
A restored window finds only its `id`; a missing ID stays absent and never
silently switches to a current pane with the same numeric selector.

Use a small injected service for discovery and optional hook correlation.
Thin async route delegates blocking work off-loop. Existing principals and
terminal command/receipt/grant authority remain. New shell supports a validated
optional local `cwd` through the existing audited factory; no browser command
builder or credential bypass. Add `surface-terminals` and `terminal:` to the
existing hub window registry. No new general kernel or process manager.

### Browser transport

Create a per-instance terminal controller in `desk/terminals/terminalSession.ts`.
It consumes the existing immutable target subscription and command endpoints;
never reuse the global steering/delivery store as a selection authority.
`terminal.text` and `terminal.keys` commands are target-bound, serialized and
carry no client-supplied authority. Read/grant/arm through the session's existing
steering routes. A grant/posture permits typing only for that controller.

Use hash/sequence-gated polling: approximately 350 ms for the focused terminal,
1200 ms for other visible instances; pause minimized/hidden instances. One read
in flight per controller. Correct `screen` deltas replace the snapshot, append
deltas append; resync/absence is explicit. No blind command retry after an
unknown outcome. Closing/disarming/failure cancels queued unsent input. A newer
text edit survives an older successful send. Queue capture binds to the exact
target, not the terminal currently selected when the promise resolves.

Upgrade the shared XtermPane species without breaking read-only consumers:
stable callback refs, no emulator remount for every callback update, no repaint
when content is unchanged, preserve user scrollback position during refresh,
ResizeObserver for container fit when no physical pane geometry is supplied,
focus/input semantics and command-key selection/escape isolation. Do not invent
another terminal renderer. Add a small reusable surface wrapper only if needed;
update the matching surface contract and reference for API changes.

### Window/application integration

Use a `terminal:<session.id>` window family, `DeskState.terminalWindows` and the
existing workspace document's optional additive terminal list. Integrate it in
hubWindows adapters/snapshots/restore, the compositor and DeskApp's normal
frame mounting. Geometry/depth/minimize stay in the one existing authority.
Opening an already open terminal focuses it. Tile terminals arranges only the
terminal frames through existing compositor methods, preserving other apps.
Provide a door from Agents and from its existing Terminal/Watch live flow to
the native terminal when its session is discoverable. Keep honest fallback for
unavailable or non-tmux sessions; no dead Open action.

## Proof and honest limits

Focused T1: fingerprint/generation reuse, discovery producer, auth, missing
source, optional cwd, terminal registry/geometry. T2: two independent targets,
queued/stale input, screen delta semantics, retained drafts, existing read-only
xterm contract, inventory search/open/new shell and window cache/hub restore.
Use real producer-recorded fixture payloads for app tests.

T4 real browser: private TMUX_TMPDIR and isolated HOME/hub/DB; two distinct
real shell outputs, type into A then B and observe each actual pane, close A
without killing it, reopen, drag/resize or tile and reload from hub rows,
keyboard focus and 393px Back. Existing fixtures/rigs, no owner tmux or live
agent/provider execution. Capture and inspect 1440/393 shots. Main required
quick check remains the merge check. No full suite as an extra gate.

Initial transport is bounded recent-screen polling, not a byte-perfect PTY
stream or persisted infinite scrollback. Window resize does not yet change the
remote PTY geometry; do not claim full-screen TUI resize support. No remote
sessions until an authenticated screen subscription is actually available.
Tmux survives window/browser close; machine reboot continuity is not promised.
