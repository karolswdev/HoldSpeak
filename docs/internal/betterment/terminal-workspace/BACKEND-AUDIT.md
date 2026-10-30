# Terminal workspace: backend audit

Status: read-only audit of `8c6ad9989` (2026-10-30). This document records
the smallest backend contract that can support several live terminal windows.
No product code, tests, runtime state, or upstream source was changed for this
audit.

## Decision in one paragraph

Keep the current terminal target, capture, command, factory, node-link, and Desk
window services. They are good boundaries. Add a session descriptor and a
rehydration step around them; do not add a second shell launcher, pane selector,
terminal database, or nested layout system. Use one persisted Desk window row
per logical terminal session. The opaque target handle remains short lived and
is refreshed from the durable session descriptor after a hub or tmux restart.
Each window gets its own controller and its own subscription, but all input,
keys, resize, grants, receipts, and generation checks continue through the
existing command chokepoints.

The current backend can fan out one pane to several subscribers, but the Desk
cannot keep more than one terminal open. Remote reads and resize are absent,
remote writes cannot obtain a sequence from the UI, and target IDs die with the
hub process. These are contract gaps, not a reason for a rewrite.

## What exists today

The live path is already shaped correctly for a first implementation:

```text
Desk terminal store
  -> /api/delivery/terminal/{targets,subscriptions,commands}
  -> TerminalTargetRegistry + TerminalStreamService
  -> HubCommandService / process.input admission
  -> NodeCommandProcessor
  -> coder_steering deliver/deliver_keys
  -> tmux_transport
```

The application composition creates one shared target registry and one command
service (`holdspeak/web_server.py:1749-1789`). `TerminalTargetRegistry` pins a
mutable reference to a tmux `%N` and a generation, then proves that pair again
before use (`holdspeak/delivery/terminal.py:70-160`). `TerminalStreamService`
does the right fan-out work: one `TerminalCapture` per pane, a bounded ring,
sequence/hash resume, and typed absence responses
(`holdspeak/delivery/terminal.py:168-448`). The command path already has
idempotent receipts and policy-derived authority.

The factory already creates named sessions through the typed
`factory.spawn` operation and records its launch and target
(`holdspeak/delivery/factory_launch.py:1543-1569`). Its discovery method joins
tmux panes to launch records and issues target handles
(`holdspeak/delivery/factory_launch.py:2099-2175`). Reuse these adapters.

## Findings that block a real multi-terminal workspace

### 1. The backend fan-out is present; the Desk is a singleton

The TypeScript store has one `openTarget`, one poll timer, one sequence/hash,
and `open()` replaces the previous target (`web/src/desk/deliveryTerminal.ts:99-125`
and `:227-247`). Restore also stores exactly one `delivery-terminal` record
(`web/src/desk/returningWindows.tsx:47-50` and `:95-106`), and the component
uses the fixed DOM/window id `delivery-terminal`
(`web/src/desk/components/DeliveryTerminalWindow.tsx:161-215`). Opening pane B
therefore closes or repoints pane A. This is the owner-visible “terrible panes”
failure even though the backend can serve two subscribers.

### 2. The subscription route is local-only

`_SubscriptionRequest` has no `node_id`, and the route always calls its local
`TerminalStreamService` (`holdspeak/web/routes/delivery_terminal.py:55-64`
and `:155-171`). A target response does include `node_id`, and commands have a
node target, so a remote target can appear selectable while its screen can
never be read. `NodeLinkState` currently provides authenticated hello,
heartbeat, command claim, and result legs, not a terminal capture/read leg.

### 3. Target handles are process memory, not a durable identity

`TerminalTargetRegistry._by_id` and `_by_ref` are in-memory maps
(`holdspeak/delivery/terminal.py:81-88`). A target persisted by a launch record
or browser cache becomes `target_gone` after a hub restart. That failure is
safe, but it loses the open window and forces the owner to rediscover it.
`LaunchLedger` records a target (`holdspeak/delivery/factory_launch.py:1560-1564`)
but does not rebuild the registry on startup.

The stable thing must be the logical session, not `%N` and not the opaque
`term_*` handle:

* `launch:<launch_id>` for a factory launch. The launch ledger already owns
  this identity and the named tmux session.
* `agent:<agent>:<session_id>` for a hook-observed agent session. The agent
  registry persists this key and its tmux context
  (`holdspeak/agent_context/sessions.py:374-405`). A fresh `SessionStart` must
  reattach it to the current pane.
* `attach:<node_instance>:<tmux_session>:<pane_index>` for an unowned pane.
  This is explicitly attach-only. The node instance is kept in the existing
  node/ledger metadata; after a node restart the row reports
  `reattach_required` rather than silently claiming a recycled pane.

At discovery or restore, resolve the logical key, call `TerminalTargetRegistry.issue`
for the current pane, and return a fresh `{target_id,target_generation}`. A
missing launch or hook association is not proof of identity and must not be
auto-attached.

### 4. Remote terminal commands cannot get a sequence from the current UI

`HubCommandService._submit_native` refuses a remote command when
`expected_sequence` is absent (`holdspeak/delivery/commands.py:1028-1038`).
The Desk command builder deliberately sends target, operation, and payload but
no sequence (`web/src/desk/deliveryTerminal.ts:167-198`). Thus remote text and
keys can be visible in a target list but cannot complete through the generic
terminal controller.

Do not expose `GET next_sequence`: two windows could read the same value. The
fast fix is a node-side atomic reservation in the existing
`NodeReceiptLedger.target_sequences` table
(`holdspeak/db/delivery_receipts.py:55-59` and `:116-159`). Allow a remote
envelope to carry `expected_sequence: null` plus an explicit
`sequence_policy: "node_next"`; when the authenticated node claims it, reserve
the next slot and persist the receipt/sequence in one transaction. Local
commands keep the current server-side allocation. This adds no new database
schema and preserves ordered, duplicate-safe delivery.

### 5. There is no resize operation

The read side already obtains pane geometry with `display-message`
(`holdspeak/coder_steering.py:97-133`), but there is no typed resize verb or
`resize-pane` transport. The terminal window has no resize command
(`web/src/desk/components/DeliveryTerminalWindow.tsx:217-237`). Browser geometry
must not call raw tmux. Add `terminal.resize` as a sibling of
`terminal.text` and `terminal.keys` in the existing delivery command protocol,
not as a new kernel `process.resize` operation. It is a small terminal
transport contract with bounded `cols` and `rows`, target id/generation,
receipt, policy, and audit.

### 6. Screen deltas are typed by the backend but appended by the client

The capture emits `kind: "append"` or `kind: "screen"`
(`holdspeak/delivery/terminal.py:171-180` and `:287-303`). The store currently
joins every delta and appends it (`web/src/desk/deliveryTerminal.ts:297-307`).
A full redraw therefore corrupts the display. A per-instance controller must
replace the raw/lines state for `screen` and append only `append`. Keep this
fix beside the multi-window work; it is part of the stream contract.

### 7. The old grant is pane-bound, while the new command is target-bound

`require_grant` checks the current resolved pane against the in-memory grant's
`pane_id` and revokes on mismatch (`holdspeak/coder_steering.py:473-521`). The
send chokepoints do re-check the live target immediately before typing
(`holdspeak/coder_steering.py:710-794` and `:880-945`), which is the right
last-hop safety. Keep grants in memory and fail closed across restart; do not
persist authority. For the multi-window controller, bind the command's
`target_id + target_generation` first, then pass the verified pane to the
existing grant/posture check. Do not create one global “active pane” grant.
An optional later hardening is to store target id/generation alongside
`pane_id` in the grant record; the generation check remains authoritative.

### 8. Hook context can retain an old pane hint

When a hook event has no tmux context, the session registry carries forward the
previous pane/session/window fields (`holdspeak/agent_context/sessions.py:390-394`).
This is useful for a transient hook, but it is not proof that a pane is still
owned. Discovery should label this association stale until a live tmux resolve
and a current `SessionStart`/lifecycle event confirm it. Never use the retained
hint as a raw selector.

### 9. Strengthen identity without replacing the stream

The fastest durable identity improvement is a richer tmux observation, not a
PTY rewrite. Extend the local discovery/identity query with current path,
session/window ids, pane index, pane PID, pane tty/start command, and the tmux
server instance signature (server PID when the deployed tmux supports it;
otherwise the socket path plus server-start signature). Return
`current_path`, optional hook/agent state, and the opaque fingerprint in the
inventory row. `current_path`, title, active state, and current command are
useful labels but are mutable and must not by themselves trigger a generation.

Store a fingerprint alongside the target's `%N`, for example a digest of:

```text
node_instance + tmux_server_instance + pane_id + pane_pid + pane_tty
```

On every `issue`/`verify`, compare the fresh fingerprint even when `%N` is the
same. A changed server instance (hub/tmux restart) or pane PID (pane respawn)
bumps the target generation and refuses the old handle. A deliberate reissue
from the stable `session_ref` gets the new handle. Do not silently reattach an
old Desk row to the changed fingerprint. This is a small extension to
`resolve_pane_identity` and `TerminalTargetRegistry`, and it also makes the
inventory useful: `current_path`, hook state, agent/session key, lifecycle,
and fingerprint explain what the owner is about to open.

Keep the first stream implementation as the existing hash-gated fast poll.
It already shares one bounded capture between subscribers and gives honest
snapshot/delta/resync statuses. Document its limits in the terminal contract:
it is a recent bounded screen tail, not a byte-perfect PTY stream; redraws are
typed `screen` deltas; update latency follows the client poll interval and the
server throttle; and scrollback/cursor state is not persisted. A live PTY/Web
Socket stream can be a later capability after the multi-window identity and
control path is correct.

## Settled backend contract

### Logical session and target records

The browser stores a `TerminalSessionRef`, not a pane id:

```json
{
  "node_id": "node-local",
  "session_ref": "launch:launch_123",
  "label": "HoldSpeak / review-42",
  "source": "launch|agent_session|attach",
  "launch_id": "launch_123",
  "agent_session_key": "claude:session_abc",
  "lifecycle": "working|waiting|stopped|unknown"
}
```

`launch_id` and `agent_session_key` are optional and are server-derived. The
wire target handle is ephemeral:

```json
{
  "node_id": "node-local",
  "session_ref": "launch:launch_123",
  "target_id": "term_…",
  "target_generation": "gen_…",
  "capabilities": ["observe", "input", "resize"],
  "status": "issued"
}
```

On restart, a restored window first asks for its `session_ref`, then receives a
new target. It must never keep using an old target id or fabricate a new
generation. Return `reattach_required` for an attach-only pane whose node
instance changed, `target_gone` for a known session whose process ended, and
`generation_mismatch` when a live mutable address now names another pane.

### Endpoint shapes

These are the recommended additions/changes to
`holdspeak/web/routes/delivery_terminal.py`. Existing response fields remain
valid during migration.

#### Inventory

```http
GET /api/delivery/terminal/targets?node_id=node-local
```

Response:

```json
{
  "status": "ok",
  "node_id": "node-local",
  "targets": [
    {
      "session_ref": "launch:launch_123",
      "target_id": "term_…",
      "target_generation": "gen_…",
      "label": "review-42",
      "source": "launch",
      "launch_id": "launch_123",
      "agent_session_key": "claude:session_abc",
      "lifecycle": "working",
      "capabilities": ["observe", "input", "resize"]
    }
  ]
}
```

For the local node, implement this as a thin projection of
`LaunchService.discover()` plus hook sessions and `coder_steering.list_panes()`.
Deduplicate by the server-owned logical session; an unowned pane is an
attach-only row. For a remote node, use the node's authenticated inventory
capability and return `node_offline` or `capability_unavailable`, never a
half-filled target.

#### Issue or refresh

```http
POST /api/delivery/terminal/targets
Content-Type: application/json

{"node_id":"node-local", "session_ref":"launch:launch_123"}
```

Compatibility input `{"ref":"pane:%5"}` may remain for local callers, but
new Desk code must not send raw pane refs. The response is the target record
above. A refresh is idempotent for the same live logical session and may issue
a new generation only after a deliberate reattach/recycle decision.

#### Subscribe

```http
POST /api/delivery/terminal/subscriptions
Content-Type: application/json

{
  "node_id":"node-local",
  "target_id":"term_…",
  "target_generation":"gen_…",
  "resume_sequence":17,
  "last_hash":"sha256:…"
}
```

The response keeps the existing `snapshot`, `deltas`, `not_modified`, and
`resync_required` envelopes. It must also carry `node_id`, target id, and
generation. Dispatch local reads to the existing `TerminalStreamService`.
Dispatch remote reads through an authenticated node terminal-read leg that
accepts only the target handle and resume fields. Do not put terminal bytes in
heartbeat metadata. Map failures to `node_offline`, `stream_unavailable`,
`target_gone`, and `generation_mismatch` with the current HTTP absence mapping.

The node-side read service should reuse `TerminalTargetRegistry` and
`TerminalStreamService`; the hub must not resolve a remote `%N` itself.

#### Commands

Keep the existing envelope and receipt route:

```http
POST /api/delivery/terminal/commands
```

Every command carries the immutable target object, not a mutable pane selector:

```json
{
  "command_schema": 1,
  "command_id": "uuid",
  "target": {
    "node_id":"node-local",
    "target_id":"term_…",
    "target_generation":"gen_…"
  },
  "operation": {"family":"coder_steering", "verb":"terminal.text"},
  "payload": {
    "session_key":"claude:session_abc",
    "text":"run the focused tests",
    "submit":true
  },
  "expected_sequence": 4
}
```

`terminal.keys` continues to use the existing named-key allow-list and literal
transport. `terminal.resize` is a new typed operation:

```json
{
  "operation":{"family":"terminal", "verb":"terminal.resize"},
  "payload":{"cols":120, "rows":36}
}
```

Bounds belong in the codec (for example, 20–500 columns and 5–200 rows), and
the command goes through policy, target/generation verification, receipt, and
audit. It calls `tmux resize-pane -x <cols> -y <rows>` only after the target is
resolved to the verified `%N`. Browser resize should be debounced and sent as
an explicit terminal-controller operation, not a hidden raw HTTP side effect.

For remote writes, use the `sequence_policy: "node_next"` reservation described
above. Do not make the UI guess or poll a sequence number.

#### Window persistence

Do not add `/terminal/workspace` or a terminal-specific layout database. Extend
the Desk window registry so a terminal instance is a normal compositor window:

```text
window id:  terminal:<url-safe-session-ref>
app:        delivery-terminal
object_ref: JSON or compact ref containing node_id + session_ref + label
```

`desk_windows` already persists `id`, `app`, `object_ref`, geometry, depth,
minimized/zoomed state, room, and CAS revision
(`holdspeak/db/schema.py:2108-2144`); `DeskWindowService` already provides
idempotent open/close and compare-and-set writes
(`holdspeak/services/desk_window_service.py:392-478` and `:778-824`).
Remove `delivery-terminal` from `NOT_ON_HUB`, add a `terminal:` dynamic family,
and register the family in the Desk compositor. Each row is one independent
terminal. Keep the current `hs.desk.workspace.v1` browser document as a first
paint cache only; it is not an authority and should migrate its one terminal
place to these rows.

Persist view metadata only (geometry, depth, minimized/zoomed, active/focused,
follow/scroll preference if needed). Never persist raw terminal output, grants,
tmux `%N`, or node tokens. A stale row remains visible as `reattach_required`
until the server reissues a target; it is not silently retargeted.

## Fast implementation order

1. Add `TerminalSessionRef` discovery and reissue. Rebuild a target from
   `launch_id`/agent session on restore; mark unowned attach rows honestly.
2. Add `node_id` to issue/subscribe requests and a node terminal-read adapter.
   Reuse the existing node token/auth and typed absence mapping. Keep terminal
   bytes out of heartbeat events.
3. Add `terminal.resize` and node-side atomic sequence allocation using the
   existing receipt ledger. Add a focused real-tmux proof for text, keys,
   resize, recycling, and duplicate command ids.
4. Allow `terminal:<session_ref>` Desk rows and wire the compositor to one
   per-instance controller. Replace the singleton store/timer with a map keyed
   by `node_id|session_ref|target_generation`; replace `screen` deltas rather
   than append them.
5. Retire the old singleton restore path only after existing
   `delivery-terminal` rows have been migrated. Keep the old coder steering
   routes as compatibility adapters into the same command chokepoint; do not
   add a third pane-control path.

## Control and safety rules

* `terminal.text`, `terminal.keys`, and `terminal.resize` always require the
  immutable target and generation. The browser supplies no authority, policy,
  grant, or actor.
* Keep `control_mode`, policy resolution, wait-episode checks, direct-owner
  gestures, and YOLO posture in their current services. A terminal window is a
  new view, not a new control mode.
* Keep grants in memory and fail closed after restart. Verify target generation
  before checking the pane-bound grant, then pass only the freshly verified pane
  to `deliver`/`deliver_keys`.
* Serialize writes per logical target. A resize and a text send must not race
  on a remote node. Receipts remain the retry/idempotency boundary.
* A missing pane, recycled pane, tmux outage, remote node outage, or stale
  sequence is a typed refusal with no keystroke and no fabricated screen data.

## Focused verification plan

All runs use the machine-wide test lock and isolated HOME/DB/tmux state from
`CLAUDE.md`; no owner tmux server or database is allowed.

### Unit and route seams

Start with these existing files and add only focused cases for the new
contract:

* `tests/unit/test_delivery_terminal_stream.py` — two or more targets, one
  capture per pane, interleaved subscribers, `append` versus `screen`, ring
  resync, target generation and capture eviction.
* `tests/unit/test_delivery_terminal_routes.py` — `node_id` routing, refresh
  after registry restart, remote offline/absence statuses, and independent
  subscription bodies.
* `tests/unit/test_delivery_commands.py` — target/generation binding, node-side
  sequence reservation, duplicate receipt, resize bounds, and policy refusal.
* `tests/unit/test_coder_steering_panes.py`,
  `tests/unit/test_coder_steering_keys.py`, and
  `tests/unit/test_tmux_transport.py` — last-hop identity, key allow-list, and
  resize transport command shape.
* `tests/unit/test_factory_launch.py`,
  `tests/unit/test_delivery_factory_routes.py`, and
  `tests/unit/test_agent_session_lifecycle.py` — launch/hook session refs and
  restart rehydration.
* `tests/unit/test_desk_window_service.py` and the compositor window tests —
  two `terminal:` rows, idempotent open, CAS geometry, close one without
  closing the other, and restore of stale rows.

### Real isolated tmux proof

Reuse the `live_pane` fixture in
`tests/integration/test_delivery_terminal_live.py:33-52`. It creates a named
`bash --norc --noprofile` session and cleans it up. Extend a focused fixture to
create two or three named sessions/panes on the same test tmux server. The
existing test configuration gives each run a private `TMUX_TMPDIR`; the fence
is asserted by `tests/unit/test_tmux_rig_isolated.py:17-34`.

The useful proof sequence is:

1. Issue three logical session refs and targets. Open three independent
   subscriptions and interleave polls. Assert each snapshot/delta contains only
   its pane marker and `capture_metrics()` contains one capture per pane.
2. Send text and named keys to pane A, resize pane B, and assert pane C has no
   output or geometry change. Retry the same command id and assert one effect.
3. Kill/recycle pane B. Assert its old target refuses with
   `generation_mismatch`/`target_gone`, no text lands in the replacement, and a
   deliberate refresh returns a new generation.
4. Recreate the target registry while retaining the launch/session ledger.
   Assert a launch or hook session ref reissues a new target, while an unowned
   attach row returns `reattach_required`.
5. Exercise the remote adapter with an injected fake `NodeLinkState`/node
   transport. Prove node auth, `node_offline`, generation refusal, sequence
   reservation, and receipt reconciliation without LAN access.

This proves live tmux behavior and isolation. A FakeTmux route test alone does
not prove the real pane, resize, or socket boundary. Do not run
`tests/e2e/test_metal.py`.

## Explicit non-goals

This slice does not persist scrollback, grants, pane ids, or tokens; add an
xterm/terminal emulator only as a rendering improvement after the stream
contract is correct. It does not introduce a shell command endpoint, a second
launch framework, a nested canvas, or a heartbeat carrying terminal bytes. It
does not inspect or copy competing upstream implementations.

The key Tuesday test is simple: the owner can open pane A, open pane B, see and
control both without either window changing identity, reload the Desk and find
both windows again, and receive an honest reattach/refusal when a pane was
recycled. Anything less is still a singleton with better paint.


## Final implementation and review (2026-10-30)

The settled implementation is described in DESIGN.md and RESULT.md. Discovery
uses the live target registry, the factory validates and forwards optional cwd,
and the existing hub window registry accepts the inventory and terminal family.
The direct `/terminals` page is served by the production SPA allowlist.

A second review found two real gaps and fixed them in this lane. Arm grants now
pin the rich process fingerprint; `require_grant` refuses and revokes a grant
when the same pane number belongs to a new process. Hook matching rejects
conflicting available coordinates (including integer zero), ignores ended and
effectively dead records, and renders the existing registry's age-decayed state.

Final focused command, under the machine lock and isolated HOME:

```sh
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal \
  tests/unit/test_coder_steering_panes.py \
  tests/unit/test_terminal_workspace.py
```

```text
12 tests collected in 0.75s
12 passed in 2.64s
```

Logs: `.tmp/terminal-workspace/respawn.collect.log` and `respawn.run.log`.
The earlier five-file backend run passed 101 cases; the direct-page regression
passed six. The root lane owns the final integrated quick check.

Hook records have no process fingerprint. A non-ended historical hook with
matching pane number and coordinates remains correlated metadata until normal
decay; it is not process proof. Live target generation and the typing grant
provide independent process checks. Legacy `%N`-only injected test runners keep
their explicit compatibility behavior. No owner process or provider was used.
