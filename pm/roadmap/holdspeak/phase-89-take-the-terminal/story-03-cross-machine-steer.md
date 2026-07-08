# HS-89-03 — Cross-machine steering: over the relay

- **Project:** holdspeak
- **Phase:** 89
- **Status:** done
- **Shipped:** 2026-07-08 — local-only is gone. `coder_steering_relay.relay` forwards a peek/arm/steer/keys to a configured node's OWN steering routes; the node executes against its own tmux. Proven TWO-PROCESS live: the hub (never touching tmux) relayed arm+C-c+steer to a separate node process — the runaway stopped, "REMOTE_STEER_OK" landed in the node's pane; killing the node refused `node_offline` by name in 0.00s. Suite 3499/0. Evidence: [evidence-story-03.md](./evidence-story-03.md).
- **Depends on:** HS-89-01, HS-89-02
- **Unblocks:** HS-89-04

## Problem

The rails observer already reaches events from another machine
(HS-88-04); manipulation should reach the other way — peek and steer a
pane on ANOTHER node. A far node runs the tmux; the hub relays the
command; the far node executes locally and returns the result.

## Design refinement (shipped)

The scaffold said "grant + audit stay on the hub." Building it, the
**safer** model was clear and shipped instead: **the machine that types
owns the consent AND the audit.** The far node checks its OWN grant and
writes its OWN audit row for the keystroke it delivers — the hub is a
relay, never the authority over someone else's terminal. The hub stamps
`node` onto the relayed result so the caller knows WHERE the keystroke
landed. Recorded as a phase decision.

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

- [x] A relayed verb reaches the node's OWN route with the pane key
      percent-encoded + the bearer token; the result is stamped with the
      node (`test_coder_steering_relay.py`). Peek rides the same relay
      helper as arm/steer/keys.
- [x] A steer/keys to a remote pane executes on THAT node — proven
      two-process: the hub never touched tmux, yet the node's pane
      changed (runaway stopped, `REMOTE_STEER_OK` landed), armed in the
      node's OWN process (`evidence-story-03.md`).
- [x] The node goes quiet → the relay refuses `node_offline` BY NAME in
      honest time (0.00s live), never a hang; `unknown_node` for an
      unconfigured name.
- [x] Only the command (text / keys) crosses the wire — the relay body
      is `{text}` / `{keys}`, no secret beyond the node's own bearer
      token; a test pins the body + the encoded URL.
- [x] Full suite green (3499/0, read from the file).

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
