# Terminal workspace verification audit

Status: verification design only. No tests, browser walks, builds, or product
edits were run for this audit.

Repository: `feat/terminal-workspace`, base `8c6ad9989` (the current main
commit at audit time). Scope is the proposed independent, node-term-inspired
multi-terminal and parallel-agent workspace. This document does not copy or
derive implementation code from the upstream project; it records the proof
we need in HoldSpeak's existing seams.

## Bottom line

The current repository proves a single terminal pullout and a single durable
Desk window well. It does not yet prove an independent workspace with several
live panes, pane-local focus, durable layout restore, or the distinction
between closing a view and killing an agent/session. Do not call the feature
verified from the existing terminal tests alone.

The implementation should reuse these authorities:

| Concern | Existing seam to reuse | Verification boundary |
| --- | --- | --- |
| Window placement, depth, zoom, minimize and restore | `DeskWindowFrame`, `desk_window_service.py`, `web/src/desk/compositor/hubWindows.ts`, `web/src/desk/store/workspaceStorage.ts` | Hub rows/revisions are durable authority; browser storage is a presentation cache. A reload must read the same result, not merely redraw local rectangles. |
| Terminal bytes and target identity | `web/src/desk/components/DeliveryTerminalWindow.tsx`, `web/src/desk/surface/XtermPane.tsx`, `web/src/desk/deliveryTerminal.ts` | A pane is painted only for its current immutable target (`target_id` plus generation). Late polls, receipts, and refusals must not paint a replacement pane. |
| Stream fan-out, resync, generation and typed absences | `holdspeak/delivery/terminal.py` and the delivery-terminal route | Subscribers may share one capture, but every subscriber still has an independent target and resume position. Dead, recycled, unauthorized, and unavailable are observable states. |
| Agent/session lifecycle and grouping | `web/src/desk/processWindow.ts`, `processWindowReducer.ts`, Conductor/steering stores | Reuse the existing journal/fold and correlation identity. Do not create a second authoritative lifecycle stream in the workspace. |
| Pane discovery and explicit kill | `web/src/desk/steering.ts` (`listPanes`, `spawnSession`, `killOpen`) | “Close pane” must be a view/subscription operation. “Kill” must remain an explicit server operation with its own receipt/refusal. |

The existing `PROGRAMS-DESIGN-2026-10-28.md` says Programs is not a terminal
multiplexer and that `herdr` owns terminals. The new owner request is a
settled scope change, not permission to fork a second terminal authority:
keep terminal/session truth in the hub and make the new workspace a Desk
presentation and routing surface over those producers.

### Anchor index

These are the most useful current anchors for implementation and review:

- `web/src/desk/deliveryTerminal.ts:227-365` — target replacement, close,
  single-flight polling, target equality guards, text/key command receipts.
- `web/src/desk/steering.ts:321-380,523-603,629-714,734-805` — session open/
  close, stale-guarded key sends, pane discovery/spawn, explicit kill, poll.
- `web/src/desk/store/workspaceStorage.ts:15,184-285,369-431` — browser
  workspace cache version, validation/migration, and serialization.
- `web/src/desk/__tests__/windows.test.tsx:54-88,90-179,229-327` — close
  refusal, parked mounts, focus depth, and persistence round-trip.
- `web/src/desk/compositor/__tests__/hubWindows.test.ts:176-348` — multiple
  views, hub-seated state, and 393px behavior.
- `tests/unit/test_delivery_terminal_stream.py:94-332` and
  `tests/unit/test_delivery_terminal_routes.py:164-357` — stream/route
  target, resync, generation, command-idempotency, and authority/token fences.
- `tests/e2e/test_windows_glass.py:1-57,505-583,617+` — the existing
  real-browser geometry, depth, Escape, touch, and evidence helpers.
- `tests/e2e/test_native_repository_windows_glass.py:104-226` — two-view
  desktop/phone interaction and sibling-close behavior.
- `tests/e2e/test_betterment_st8_signin_glass.py:77-92,118-185` — positive
  private `TMUX_TMPDIR` rig and real xterm helper focus; its teardown is
  socket-scoped.
- `tests/e2e/glass_infra.py:199-328` — isolated HOME/DB and capability
  switches; around `282-287` documents why ordinary glass must not launch
  panes on the owner's tmux socket.
- `scripts/test_lock.py:1-24` — the machine-wide lock contract.

## Proof matrix

Use the cheapest test that proves each claim, then use a real browser only for
the geometry and interaction claims that jsdom cannot observe. Focused tests
must use real service/route producers or the repository's existing recordings;
do not fabricate a payload that bypasses target, revision, or lifecycle
boundaries.

### T1: hub and service behavior

Extend the existing focused tests before adding a new harness.

| Behavior | Existing evidence and useful anchor | Required assertion for the workspace |
| --- | --- | --- |
| Target identity and stream safety | `tests/unit/test_delivery_terminal_stream.py` (normalization, stable target, dead/recycled pane, shared capture, ring/resync, ANSI and typed absences); `tests/unit/test_delivery_terminal_routes.py` (target issue, snapshot/delta, 404/409, node/browser token, duplicate command receipt) | Open at least two targets concurrently. A recycled or dead A target cannot paint B. A delayed subscriber gets a real resync. The same `command_id` creates one transport effect and one receipt. Client-supplied authority/name is refused. |
| Close versus kill | `web/src/desk/steering.ts` `killOpen` and `closeSession`; `tests/unit/test_conductor_k5_supervision.py`; `tests/unit/test_conductor_real_use.py` | Closing a workspace pane removes its view/subscription only. It must not call `kill-session`, end the process, or erase the session. Explicit Kill alone may produce the kill receipt. Reopen must show output from the still-live producer. |
| Durable Desk window state | `holdspeak/services/desk_window_service.py` geometry/revision verbs; `tests/unit/test_desk_window_service.py`; `web/src/desk/compositor/__tests__/hubWindows.test.ts` | Move, resize, depth, zoom and close write the hub row with revision handling. A stale write is rejected/re-read; one browser view closing does not silently remove another view's state. |
| Existing layout cache contract | `web/src/desk/store/workspaceStorage.ts`; `web/src/desk/__tests__/windows.test.tsx` persistence round-trip and `panelDepth.test.ts` | Local cache can speed boot, but a fresh boot and a second view converge on hub state. Corrupt/old cache is ignored or migrated without losing durable windows. |
| Lifecycle fold and correlation | `web/src/desk/__tests__/processWindow.test.ts` and `processWindowReducer.test.ts` | A pane/session can be grouped under the correct active agent, needs-you state, and ended tail. A late old worker result cannot overwrite a newer wait or draft. |

The existing backend terminal tests are a particularly strong starting point:
they already cover bounded ring behavior, real snapshot bytes, ANSI
pass-through, generation mismatch, transient stream unavailability, command
idempotency, and token/authority refusal. The missing T1 cases are the
multi-target and close-is-not-kill semantics, not another fake terminal
transport.

### T2: app rendering and routing (Vitest)

Add a focused app test alongside the implemented surface, using recorded real
hub answers and the existing store seams. The exact filename should follow the
implementation's directory; do not create a parallel test framework.

Reuse these current tests as the fixtures/contracts:

- `web/src/desk/surface/__tests__/terminalWell.test.tsx`: read-only xterm
  wiring, geometry resize, search, raw fallback, and honest absences. `XtermPane`
  has an optional `onData` seam but defaults to `disableStdin`; decide and test
  whether command input is a separate focused composer or an intentionally
  enabled pane.
- `web/src/desk/components/__tests__/sessionWork.surface.test.tsx` and
  `sessionAnswer.f2.test.tsx`: terminal absence retains work, Back restores
  material and drafts, delivery clears only after success, and switching
  identity rejects stale terminal state.
- `web/src/desk/__tests__/windows.test.tsx` and
  `web/src/desk/compositor/__tests__/hubWindows.test.ts`: one shared frame,
  close refusal retention, parked mounts, focus depth, phone behavior, and
  cross-view hub state.

The new app-level proof should cover all of the following in one coherent
fixture, not isolated snapshots:

1. Mount A, B, and C at once. Each has its own target/line stream, loading,
   absence, and receipt state. Updating A cannot replace B or C.
2. Open a pane after the desk is already crowded or after a pane has been
   minimized. It must mount into a visible, clamped frame; an offscreen active
   pane is a failure even if its store state is correct.
3. Move/resize/raise/zoom and close a pane, then restore from the persisted
   state. The pane identity, order, depth, and geometry must survive, while a
   closed view must not resurrect from a stale subscription.
4. Type in A, switch focus to B while the command is pending, and resolve A.
   A's receipt/refusal must remain on A; B's draft and stream must be
   unchanged. Repeat with closing A before the late response.
5. Click A, raise it, and send a key. Only A receives it. Escape must follow
   the established Desk ordering (context menu first, then window); it must
   not leak a global key into an unfocused terminal.
6. At 393px, keep an honest compact presentation: no horizontal overflow,
   reachable 44px controls, stable focus/back behavior, and no two opaque
   panes covering the active one. If the settled design supports a roster plus
   one sheet on phone, test that explicit pattern instead of pretending a
   desktop tiling layout is usable at phone width.

### T3: generic Desk sweep

The generic Desk sweep is necessary for shared material and responsive
regressions, but it is not proof of exact terminal key routing. Run it at
1440px and 393px after the focused app tests. For visual evidence, opt in with
`DESK_SWEEP_SHOTS=1`, inspect the resulting `.tmp/evidence-shots/`, and report
the actual shot paths. Check that the workspace has no clipped title bars,
unreachable controls, hidden active panes, loading holes, or stale overlay
after close. A plain sweep pass without saved shots is only a functional
sweep, not visual acceptance.

### T4: scoped real-browser interaction

The repository already has the correct geometry and isolation patterns. Extend
the relevant existing glass suite (most naturally
`tests/e2e/test_windows_glass.py` for compositor behavior and
`tests/e2e/test_native_repository_windows_glass.py` for two-view behavior) or
add one feature-specific file only if the implementation cannot fit those
scopes. Do not create a phase-named browser harness.

At 1440px, the real-browser walk should:

- open three live panes and capture pane id, target id, frame rectangle, depth,
  and visible status;
- drag A, B, and C, then click each in turn and prove the clicked frame is
  frontmost at its point (not just that a React state changed);
- zoom one pane and verify its restore geometry and sibling visibility;
- focus A's actual xterm textarea/composer, send a key, then focus B and send a
  different key. Assert the server-side bytes/receipts identify the intended
  target only;
- create/open a pane after layout is crowded and assert its frame is inside
  the desk band. Include a pane that would otherwise be placed offscreen;
- close A, verify its frame and subscription disappear, and verify the agent
  session/process remains live and can be reopened. Then exercise explicit Kill
  separately and verify its receipt and resulting terminal absence;
- leave a command pending, switch or close the pane, resolve the old command,
  and assert no replacement pane, draft, receipt, or status changes;
- reload and compare pane identity, rectangles, order, depth, and zoom with
  the durable hub result, not only localStorage;
- exercise Escape, context-menu close, pointer focus, and any key palette
  without the body or another pane receiving the key.

At 393px with touch enabled, repeat the smallest owner-critical path: open the
workspace, select a pane, pan/swipe or use the roster/sheet, focus a key input,
go Back/Escape, and return to the same live pane. Assert no horizontal scroll,
no clipped 44px target, no hidden active pane, and no accidental kill. The
existing `test_betterment_st8_signin_glass.py` shows how to focus the real
xterm helper textarea before Enter; reuse that helper style rather than
asserting against a fake canvas.

For cross-view behavior, use two pages against the same test server as in
`test_windows_follow_the_bus_glass.py` and the native repository window tests:
an update or close in one view must converge through the hub bus, while a
view-local focus/selection change must not steal the other view's focus.

## Failure ledger: genuine Tuesday failures

These are the minimum failures that would block ratification because they
lose work or make the workspace appear to work while the owner cannot use it.

1. **Multiple panes are concurrent in data but not in identity.** A, B, and C
   are visible, but a delayed A snapshot or receipt paints B, or one shared
   `openTarget` causes all panes to show the last-opened stream.
2. **Offscreen mount is treated as success.** A pane exists in the store but
   its title bar or input is outside the desk band, behind the dock, or under
   an older opaque pane. The owner cannot discover or focus it.
3. **Persistent layout restores the picture but not the live target.** After
   reload, rectangles look right while target generations, subscriptions, or
   pane/session associations are stale. The first update then appears in the
   wrong pane or silently stops.
4. **Close is an accidental kill.** Closing a workspace window sends the kill
   operation, destroys the agent session, or makes the terminal impossible to
   reopen. This is a data/lifecycle failure, not a cosmetic close-button bug.
5. **Stale input clears or overwrites new work.** A command submitted in A
   resolves after the owner switches to B or closes A; its late receipt clears
   B's draft, updates B's status, or reopens A without a deliberate action.
6. **Focus keys leak.** Clicking A visually raises it, but a key goes to B,
   the body shortcut, or every pane. Escape closes the wrong layer, and the
   owner cannot tell where input will go.
7. **Phone is a shrunken desktop.** At 393px panes overlap, the active one is
   offscreen, controls are below the 44px target, or Back/Escape kills or loses
   the live session. This fails the first-use tenets even when desktop tests
   pass.

## Isolated before-capture procedure

This is the required setup for a later test run or evidence walk. It is not a
claim that this audit ran it.

1. Take the machine-wide lock through `scripts/test_lock.py`. Keep one lock
   around the build, server, browser, and test that share the rig; never nest
   or bypass it. Use a disposable home and database. The standard
   `tests/e2e/glass_infra.py::_boot` is the source of truth for the disabled
   capabilities and isolated config: calendar, agent state, CLI engines,
   real CLI, phone/external destinations, desktop notification, restart and
   screen rules are off, and `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and
   `PI_CODING_AGENT_DIR` are under the disposable home.
2. Before starting any hub or importing code that resolves tmux, create a
   private temporary socket directory, set `TMUX_TMPDIR` to it, and unset
   `TMUX` so a nested owner session cannot be selected. Keep
   `HOLDSPEAK_OWN_AGENTS=off` for ordinary glass tests. A positive terminal
   walk may launch only its own named test panes, with the private socket and
   an explicit engine mode. The ordinary glass rig deliberately shares the
   owner tmux socket but launches no sessions (`glass_infra.py` around
   lines 282-287); it is not sufficient for this feature's positive path.
3. On teardown, kill only the known private socket with
   `tmux -S <private-socket> kill-server`, then remove that temporary
   directory. Never call global `tmux kill-server`, inspect or reuse the
   owner's socket, or use the real HOME/DB/Keychain.
4. Build under the same lock using the existing `_ensure_build` helper. Use
   reduced motion for deterministic capture, wait for the exact hub response
   and settled geometry, and fail on page errors. Capture only after the
   target status, pane rectangles, and stream receipts are observable. Save
   screenshots in the test evidence directory and inspect them; do not enable
   `HOLDSPEAK_EVIDENCE_WRITE=1`.
5. For a two-page proof, create both pages against the same isolated server
   and token. Do not reload the passive page to make it pass: verify the hub
   bus delivers the update. For a one-page proof, still assert the backend
   target and receipt rows so the screenshot cannot hide a stale or fake
   fixture.

## Reporting standard

The eventual handoff should distinguish:

- source inspection (this audit and code anchors);
- T1 service/route results and stored receipts/rows;
- T2 rendered app results with real hub answers;
- T3 screenshots at 1440 and 393;
- T4 live browser observations of drag, pan, focus, key, zoom, reload, and
  close/kill behavior.

Report the exact test command and collection/tail, isolated state, private
tmux socket policy, and every shot path. A fixture pass is not live-provider
proof, and a build or a generic Desk sweep is not proof of pane-local key
routing. Hold the change for settled design and SHIP until the seven failure
cases above are covered and the owner has inspected the desktop and phone
captures.

## Implementation verification addendum (2026-10-30)

The design-only status at the top of this audit predates the focused
implementation work. This addendum records the actual owned-lane verification;
it does not claim a generic Desk sweep, live-provider walk, or aesthetic
acceptance.

Focused Vitest command (machine-wide lock, disposable `HOME`; no owner tmux
socket or provider access):

```sh
HS_REAL_HOME="$HOME"; HS_TEST_HOME="$(mktemp -d)"; export HOME="$HS_TEST_HOME"; export npm_config_cache="$HS_REAL_HOME/.npm"; /usr/bin/python3 ../scripts/test_lock.py -- /Users/karol/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/vitest/vitest.mjs run --maxWorkers=8 src/desk/terminals/__tests__/input.test.ts src/desk/terminals/__tests__/terminalSession.test.ts src/desk/surface/__tests__/terminalWell.test.tsx
```

Collection and run tail:

```text
test_lock: acquired after 110 s

 RUN  v4.1.9 /Users/karol/.codex/worktrees/terminal-workspace/HoldSpeak/web

 Test Files  3 passed (3)
      Tests  24 passed (24)
   Start at  16:20:23
   Duration 1.74s (transform 615ms, setup 310ms, import 821ms, tests 493ms, environment 980ms)
```

Typecheck command (exit 0, no diagnostics):

```sh
/Users/karol/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node web/node_modules/typescript/bin/tsc --noEmit -p web/tsconfig.json
```

The same locked run covered the terminal input decoder, per-instance
terminal-session lifecycle/receipt/queue behavior, shared xterm wiring,
quiet-header modes, contrast fallback, sticky failed-delivery messaging, and
sticky arm-refusal messaging.
Owned-path `git diff --check` also exited 0. No files were staged or committed;
the worktree remained shared with the other implementation lanes.
