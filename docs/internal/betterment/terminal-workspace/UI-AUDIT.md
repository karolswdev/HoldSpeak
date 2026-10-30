# Terminal workspace UI audit

Status: frontend audit and implementation handoff for the owner-started terminal/parallel-agent workspace. The audit preceded the settled design; the verification record below covers the native Terminals implementation. No runtime state, owner state, or upstream nodeterm source/assets were used.

## Outcome

The Desk already has the ingredients for a good workspace, but the user-facing model is fragmented and single-target. `ConductorWindow`, `LaneWindow`, `SessionPullout`, `PanePicker`, and `DeliveryTerminalWindow` each expose a different path to related work. The smallest complete replacement is one persistent **Terminal workspace** Desk application:

- one `DeskWindowFrame` owns the chrome and compositor behavior;
- an agent/session rail selects existing sessions and launches, reconnects, or resumes them;
- the main area holds at least two persistent terminal cards at once;
- each card retains its target identity, output, live state, draft, and focus;
- a phone view folds the rail into the existing WorkMenu/strip pattern and gives the selected card the full usable width.

This is a spatial work surface inside Desk, not a second operating system. It must use the existing window framework, application manifest, RuntimeBus, typed transport boundaries, and workspace persistence.

### Recommendation for the first slice

Prefer a **Terminals inventory plus multiple native Terminal DeskWindow instances** over a new bounded canvas. Each instance gets its own controller and target, while the existing compositor supplies drag, resize, focus, Tile/Overview, persistence, and the phone bottom sheet. This is the smallest route to a genuinely spatial workspace and avoids rebuilding a second window system. The inventory is the launch/reconnect surface; opening an item focuses its existing instance or creates one. A 2-up card/grid composition can follow later if the owner wants fixed docking, but the first slice should not implement both models.

The “card” references below mean a terminal instance's identity and state. They do not require a custom canvas: a native Desk window is the card boundary.

## What exists now

| Surface | Evidence | Current behavior relevant to this job |
| --- | --- | --- |
| Agents/Conductor | `web/src/desk/conductor/ConductorWindow.tsx:424-449,796-912`; `web/src/desk/conductor/store.ts:137-208` | Roster, asks, running/ended/installed groups, and Start/Resume/Retry. It is a list and action drawer, not a persistent pane surface. |
| Launched agent lane | `web/src/desk/lane/LaneWindow.tsx:97-220,224-387`; `web/src/desk/lane/laneStore.ts:156-185` | One launched agent window with steps/events/objects and a Raw terminal wing. Raw opens the lane's one steering session. |
| Plain session pullout | `web/src/desk/components/SessionPullout.tsx:702-912` | One global session window. Terminal is a local alternate view of that session, with Back returning to the report/composer. |
| Pane picker | `web/src/desk/components/SessionPullout.tsx:244-344`; `web/src/desk/components/window/launcherRegistry.ts:17-30` | `Terminals` is a transient dock popup. It lists panes, attaches one selected pane, or spawns a session; it is not a persisted workspace or window family. |
| Delivery terminal | `web/src/desk/components/DeliveryTerminalWindow.tsx:161-240`; `web/src/desk/deliveryTerminal.ts:227-318` | A separate target/generation terminal window and store with its own subscription, snapshot/delta handling, and command receipts. |
| Shared terminal well | `web/src/desk/surface/Surface.tsx:500-590`; `web/src/desk/surface/XtermPane.tsx:82-196` | Good shared read-only viewer seam: ANSI/raw or stripped fallback, search, copy-on-select, geometry, and optional `onData`. Current session use still sends through the typed composer rather than terminal input. |
| Desk mounting and identity | `web/src/desk/DeskApp.tsx:267-302`; `web/src/desk/applications.ts:7-9,176-192,737-753`; `web/src/routes.tsx:79-83` | Desk mounts Conductor, lane, delivery, and session-related hosts separately. Agents is the registered application; `panes` is a Go/Dock launcher row, not an application identity. |
| Open routing | `web/src/desk/shell.ts:172-206`; `web/src/desk/conductor/open.ts:1-34` | Opening a coder session chooses lane or plain session. Conductor member actions navigate to lane/session/info instead of focusing a shared terminal surface. |
| Window persistence | `web/src/desk/components/DeskWindow.tsx:1-9,136-171`; `web/src/desk/store/types.ts:280-320`; `web/src/desk/store/compositorSlice.ts:521-646`; `web/src/desk/store/workspaceStorage.ts:20-65,369-420` | Desk already persists window instances, rects, order, depth, minimized/maximized state, and workspace layout. A workspace must extend this owner rather than create a parallel layout store. |
| Live bus and agent registry | `web/src/runtime/RuntimeBus.tsx:14-100`; `web/src/desk/useDeskChangedRefresh.ts:69-124,172-190`; `web/src/desk/agentFlights.ts:1-9,235-350,456-522` | One RuntimeBus and a shared agent-flight/session read source already exist. Coder frames and `desk_changed` should drive status refresh; a new workspace must not open another WebSocket or duplicate the roster fetch. |

## Findings

### 1. The core problem is replacement, not missing terminal rendering

`PaneWell` and `XtermPane` can already render a capable terminal viewer. The failure is that the product presents terminal work as a sequence of replacements: picker → one session, Conductor → one lane/session, or delivery target → another terminal window. `SessionPullout` explicitly keeps one `openKey` and switches between report and terminal (`SessionPullout.tsx:702-767`); its own store description says it is a one-session pullout (`web/src/desk/steering.ts:1-8`). That makes parallel work disappear from view and makes returning to a prior target depend on memory.

### 2. There are three transport/ownership seams, each with a one-target lifecycle

The relevant state is split across `useSteering` (`web/src/desk/steering.ts:321-349,430-488,734-805`), `useDeliveryTerminal` (`web/src/desk/deliveryTerminal.ts:227-318`), and `useLane` (`web/src/desk/lane/laneStore.ts:156-185,243-303`). They each poll or subscribe, fence a target, and own send/receipt behavior. A workspace should compose these authorities behind a card model; it must not copy their API calls or create a fourth raw transport.

### 3. Agent context and terminal context are navigationally separate

Conductor member verbs open lane/session/info (`web/src/desk/conductor/open.ts:1-34`), while Desk mounts Conductor and lane as separate hosts (`web/src/desk/DeskApp.tsx:296-301`). The owner cannot see the roster, several terminals, and the current ask in one stable surface. “Open in workspace” should focus an existing card or add one without closing the others; lane details can remain a deep view.

### 4. “Reconnect” has no durable user-facing card identity

The compositor persists window instances and geometry, but current terminal/session windows are represented as single-purpose IDs. `openCoderSession` selects a lane or one steering session (`web/src/desk/shell.ts:172-206`), and the lane store opens/closes steering based on one raw toggle (`web/src/desk/lane/laneStore.ts:156-185`). A workspace card needs an explicit compound identity: use the server target/generation when available (`web/src/desk/deliveryTerminal.ts:25-55`), otherwise the typed session/pane identity. A recycled or stale target must become an honest card state with Retry/Reconnect, not silently show a different pane.

### 5. The current PanePicker is not a workspace

The picker is a fixed popup above the dock (`web/src/desk/components/SessionPullout.tsx:244-344`; `web/src/desk/components/session-pullout.css:208-243`). It has useful discovery and spawn actions, but no card layout, no retained selection set, no per-card draft, and no persistence. Its launcher also lives in `GO_EXTRA_ROWS` (`web/src/desk/applications.ts:737-753`), so the replacement needs one registered application/route, not another launcher registry.

### 6. Phone needs a folded rail, not a shrunken desktop grid

`DeskWindowFrame` already owns phone bottom-sheet behavior (`web/src/desk/components/DeskWindow.tsx:1-9`), and the existing PanePicker has a mobile width rule (`web/src/desk/components/session-pullout.css:208-243`). The workspace should use that framework: show one selected card at usable width, put the session rail behind a WorkMenu/strip control, keep actions at touch size, and preserve drafts when the owner moves between cards. Do not add horizontal scrolling or a second mobile shell.

## Smallest complete workflow

1. The owner opens **Terminal workspace** from the existing Agents/Go surface. It is one application identity and one Desk window. A deep link or Conductor action opens/focuses the same window.
2. The left rail shows live and recent sessions from the existing agent-flight/conductor read model, plus explicitly labelled untracked panes from the existing steering discovery boundary. Each row has agent/session identity, state, last activity, and one clear action.
3. Selecting a row focuses its existing card or adds one. The default desktop arrangement is a 2-up grid with room for more cards; each card keeps terminal output, target/session identity, live state, and a compact action footer. Closing or minimizing a card does not discard its draft or server target metadata.
4. A launched agent card can expose a Steps/Details fold or open the existing lane for deep review. The workspace remains the stable terminal context; lane is not reimplemented inside the card.
5. The selected card owns Direct/send-keys actions through the existing typed authority and shows an acknowledged receipt. Drafts are keyed by card identity. Raw terminal keystroke input stays out of scope until the settled design explicitly defines its authority; the optional `XtermPane.onData` prop is not permission to bypass typed transport.
6. On refresh/reconnect, the workspace restores its card set and layout from Desk persistence, then revalidates each server target. A stale, ended, or unreachable card says what happened and offers the existing Start/Resume/Retry/Reconnect action. It never silently swaps to another pane.
7. On phone, the rail folds into the existing menu/strip, cards stack, and only the selected card is expanded. Back returns to the rail without losing the draft or terminal output projection.

### Acceptance boundary

The first complete slice is substantial when all of these are true:

- two or more cards can remain visible at once at desktop size;
- switching cards preserves output, focus state, and unsent draft;
- Conductor, lane, plain session, delivery target, and pane discovery resolve to the same card/window surface;
- live/working/waiting/asked/done/ended/unreachable states are visible with icon plus words;
- target/generation or compound session identity is stale-fenced and reconnectable;
- one active card can send through the existing typed transport and show a receipt;
- reload restores workspace layout and card metadata through Desk persistence;
- 393px behavior is a usable selected-card view with no clipped controls or second chrome.

## Active integration points

| Concern | Existing owner | Workspace rule |
| --- | --- | --- |
| Application/window identity | `web/src/desk/applications.ts`, `web/src/routes.tsx`, `web/src/desk/DeskApp.tsx` | Add one Terminals manifest identity and route/open action; model each target window as a stable scoped instance. Do not add a second registry or a standalone page shell. |
| Compositor/focus/geometry | `web/src/desk/components/DeskWindow.tsx`, `web/src/desk/compositor/hubWindows.ts`, `web/src/desk/store/compositorSlice.ts` | Keep one `DeskWindowFrame` per terminal instance; give each instance a stable target-derived ID/scope, let compositor focus/Tile/Overview own spatial behavior, and persist geometry through existing hub/store adapters. |
| Workspace persistence | `web/src/desk/store/types.ts`, `workspaceStorage.ts` | Persist card order, selected card, and target metadata within the existing workspace document or its typed window scope. Avoid another localStorage key. |
| Source roster and launch actions | `web/src/desk/agentFlights.ts`, `web/src/desk/conductor/members.ts`, `web/src/desk/conductor/store.ts`, `conductor/open.ts` | Reuse existing reads and verbs. Conductor actions should focus/add a card, not navigate away by default. |
| Session/terminal authority | `web/src/desk/steering.ts`, `deliveryTerminal.ts`, `lane/laneStore.ts` | Adapt existing stores behind a card model. Preserve their target, generation, stale fences, receipts, and cancellation behavior. No duplicated fetch or WebSocket. |
| Terminal material | `web/src/desk/surface/Surface.tsx`, `XtermPane.tsx`, `surface.css` | Reuse `PaneWell`/xterm. Any new card material belongs in the shared surface library and must respect the bounded terminal well exception. |
| Live updates | `web/src/runtime/RuntimeBus.tsx`, `useDeskChangedRefresh.ts` | Subscribe to the existing bus, filter relevant frames, and clean up on unmount. Poll only where the existing typed authority requires it. |

## Suggested ownership split for implementation

This is a future split after the design is settled; no lane should start from this audit alone.

1. **Workspace state/integration lane** — application manifest, route/open action, compositor adapter, Desk persistence, and a small typed card registry. Owned paths should be limited to `applications.ts`, `routes.tsx`, `shell.ts`, `conductor/open.ts`, compositor/store integration, and a new `web/src/desk/terminal-workspace/registry.ts`/`model.ts`.
2. **Workspace face lane** — new `TerminalWorkspaceWindow.tsx`, card/rail components, and scoped CSS under `web/src/desk/terminal-workspace/`. Own desktop/phone layout only; consume the state contract and do not change transport authorities.
3. **Transport adapter lane** — the new card-to-authority adapter under `web/src/desk/terminal-workspace/`, plus narrowly scoped shared `PaneWell` changes if required. Preserve `steering`, `deliveryTerminal`, and `laneStore` contracts; no application or persistence edits.
4. **Verification lane** — focused Vitest and real-browser coverage after the state and face contracts settle. It should own new test files and evidence notes only.

If the existing APIs cannot supply a required target or reconnect operation, stop and make a separate backend contract brief. Do not smuggle a new server protocol into the UI lane.

## Focused verification and before-screens

Existing tests provide useful seams to preserve:

- `web/src/desk/components/__tests__/sessionWork.surface.test.tsx:30-132` covers absent sessions, terminal absence, retry/back, retained identity, and pending questions.
- `web/src/desk/components/__tests__/sessionAnswer.f2.test.tsx:46-100` covers Direct, Enter routing, draft clearing, terminal unmount, and draft retention.
- `web/src/desk/surface/__tests__/terminalWell.test.tsx:101-172` covers xterm repaint, geometry/cursor, search, tokens, and stripped fallback.
- `web/src/desk/lane/__tests__/laneWindow.c2.test.tsx:307-410,673-716,846-910` covers lane ownership, terminal wing, return to work, and raw binding.
- `web/src/desk/__tests__/agents.app.test.tsx:75-182,361-713,866-1115` and `web/src/desk/__tests__/conductor.app.test.tsx:71-140` cover roster, lane/terminal verbs, asks, and source selection.
- `tests/e2e/test_conductor_glass.py:229-365` already exercises the 1440/393 session frame, terminal-unavailable, lane, and asking states; its named shots (`plain-working`, `plain-terminal-unavailable`, `plain-asking`, `lane-working`, `lane-terminal-unavailable`, `lane-asking`) are good before comparisons.

Add a new focused suite only after the contract is fixed, for example `web/src/desk/terminal-workspace/__tests__/workspaceWindow.app.test.tsx`, covering two-card focus, draft retention, stale/reconnect, live status, and restore. Extend the existing compositor/window tests for persistence and single-instance behavior rather than creating a new harness. Use the existing isolated e2e rig for before/after shots at 1440 and 393; do not use the owner's HOME, DB, Keychain, providers, or live panes.

## Unknowns to settle before implementation

- Which server identity is canonical for a plain coder session versus a discovered tmux pane, and which identities survive a browser reload?
- Should an untracked pane be attachable to the workspace, or only a launch/session returned by the agent registry?
- Is the first card allowed to send only through Direct/keys, or is a typed terminal input contract being added separately?
- Which lane details belong in the card fold versus the existing LaneWindow, and what is the exact phone back path?
- Does the owner want a fixed 2-up default or a user-resizable grid after the first complete slice?

Done — wrote the read-only UI audit and held for the settled design/SHIP brief.

## Implementation handoff verification

The settled native implementation owns the following integration seams:

- `web/src/desk/terminals/TerminalsCore.tsx`, `TerminalWindows.tsx`, `windows.ts`, `open.ts`, and `terminals.css`: searchable inventory, typed shell factory launch, independent descriptor windows, native compositor Tile/focus, reconnect/absence states, phone Back, retained drafts, and per-window activity authority.
- `web/src/desk/applications.ts`, `web/src/routes.tsx`, and `web/src/desk/DeskApp.tsx`: the `open-terminals` manifest/route and `surface-terminals` host.
- `web/src/desk/store/{types.ts,compositorSlice.ts,workspaceStorage.ts}`, `web/src/desk/compositor/hubWindows.ts`: persisted descriptor IDs, native window lifecycle, and hub restoration adapters.
- `web/src/desk/components/SessionPullout.tsx` plus `_parked/terminals/PanePicker.tsx`: the old transient picker is parked; its launcher opens the canonical application.
- `web/src/desk/conductor/ConductorWindow.tsx` and `web/src/desk/lane/LaneWindow.tsx`: canonical Terminals doors.

Focused verification was run from the isolated web rig with the machine test lock:

```text
uv run --no-project python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 \
  src/desk/store/__tests__/windowSingleInstance.test.ts \
  src/desk/compositor/__tests__/hubWindows.test.ts \
  src/desk/terminals/__tests__/terminals.app.test.tsx \
  src/desk/DeskApp.test.tsx

Test Files  4 passed (4)
Tests       70 passed (70)
Duration    1.98s
```

`tsc --noEmit` and `git diff --check` passed. The token gate still reports its existing repository-wide baseline of 183 raw values; none are in the terminal additions. The architecture guard remains red on existing baseline findings; no terminal, Conductor, lane, or parked picker finding remains after using the surface barrel imports.

The native fit pass is now in place: terminal frames use the existing `desk-pullout` material/positioning, their body is flex-bounded so the terminal screen scrolls internally, and the default frame height is 560px. The toolbar keeps the existing shared Keys menu (with the transport token `C-c` presented as `Ctrl-C`) and a shared Find toggle; the interactive pane sets `copyOnSelect={false}` and uses the landed `PaneWell` `header="find" | "none"` contract. Root's real-browser walk is green at 1440 and 393: two independent terminal windows, readable output, quiet menu/Find behavior, and composer/status regions remain inside the viewport above the phone dock. The browser walk also proved the new-shell cwd, independent keyboard input, reload without opening inventory, and close-with-process-alive behavior. The focused Vitest tail above predates only the final native-fit CSS/toolbar polish; the root lane owns the required final quick check and browser rerun.

Final bounded integration verification ran under the machine lock after the live-inventory, copy, menu, metadata, resize-fit, and recent-reference fixes:

```text
uv run --no-project python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 \
  src/desk/terminals/__tests__/terminals.app.test.tsx \
  src/desk/__tests__/menuGlyphs.test.tsx \
  src/desk/__tests__/applicationManifest.test.ts \
  src/desk/__tests__/menus.app.test.tsx \
  src/desk/__tests__/palette.app.test.tsx \
  src/desk/__tests__/phoneDoors.test.tsx \
  src/desk/components/DeskMenuBar.test.tsx \
  src/desk/components/window/phoneRing.test.tsx

Test Files  8 passed (8)
Tests       125 passed (125)
Duration    10.28s
```

`tsc --noEmit -p tsconfig.json` passed with no output. The live inventory owner now refreshes only when its app or terminal frames are open, preserves descriptors on failed reads, and reports retained work plus a retry path. The canonical Terminals app is the only recent reference (`app:open-terminals`); dynamic `terminal:<id>` references are not recorded.
