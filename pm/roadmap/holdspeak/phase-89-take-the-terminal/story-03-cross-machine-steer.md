# HS-89-03 — Cross-machine steering: over the relay

- **Project:** holdspeak
- **Phase:** 89
- **Status:** backlog
- **Depends on:** HS-89-01, HS-89-02
- **Unblocks:** HS-89-04

## Problem

The rails observer already reaches events from another machine
(HS-88-04); manipulation should reach the other way — peek and steer a
pane on ANOTHER mesh node. A far node runs the tmux; the hub relays the
command; the far node executes locally and returns the result. The
grant and the audit stay on the hub; only keys + hashes cross the wire.

## Scope

- In: a steering worker leg on the mesh node (the Phase-85 pull-worker
  precedent) that executes a relayed peek/steer/keys against its OWN
  local tmux and returns the typed result; the hub-side relay
  (`POST /api/coders/{node}/{key}/...` or a `node` param) that enqueues
  the command and awaits the far result; honest liveness (a quiet node
  refuses by name, the Phase-85 rule); the audit records the node.
- Out: a fleet (scope the wire to ONE remote, the HS-88-04 discipline —
  ship the receiving/relay half proven two-process, defer the rest);
  any secret crossing the wire (the far node resolves its own tmux);
  autonomous remote steering (a human behind every remote keystroke).

## Acceptance criteria

- [ ] A peek of a pane on a REMOTE node returns that node's real pane
      content over the relay; the audit/result names the node.
- [ ] A steer/keys to a remote pane executes on THAT node (its worker's
      own log proves it), under a grant, audited with the node named.
- [ ] The node goes quiet → the remote steer refuses by name in honest
      time (the Phase-85 liveness rule), never a hang, never fabricated.
- [ ] Only keys + hashes cross the wire — a test asserts the relayed
      envelope carries no pane bytes beyond the peek snapshot and no
      secrets.
- [ ] Full suite green (read from the file).

## Test plan

- Unit: the relay envelope shape + liveness + the node-named audit,
  with a fake relay + fake remote worker.
- Integration: a second local process (`holdspeak mesh serve`-style,
  the Phase-85/88 walk pattern) running a steering worker; a real
  peek + steer of a pane it owns, captured.
- Manual / device: two machines if available; else the two-process
  local proof.

## Implementation direction

- **The precedent:** mirror `intel/mesh_relay.py` + the pull-worker.
  The steer/keys command is a job the far node's worker claims,
  executes against its local tmux (via `coder_steering.deliver` /
  `deliver_keys` ON THAT NODE), and completes with the typed result.
- **Grant + audit stay hub-side:** the hub checks the grant and writes
  the audit; the far node is the executor, not the authority. The far
  node authenticates with the mesh token (no new secret).
- **Liveness:** reuse `db.mesh_relay.worker_last_seen` +
  `DEFAULT_LIVENESS_WINDOW_SECONDS`; a stale node refuses fast + named.
- **Scope discipline:** if the relay-of-commands wire outgrows the
  story budget, ship the receiving worker + the hub relay proven with
  the two-process local rig and record the multi-machine polish as a
  deferred rider — the criterion is the wire PROVEN on one remote.
