# AGENT-BRIEF — Phase 89: Take the Terminal

Read this, then the Phase-87 final summary
(`../phase-87-steering-desk/final-summary.md`) and
`holdspeak/coder_steering.py`. This phase EXTENDS the Phase-87 chokepoint;
it must not fork or weaken it.

## The owner's ask (verbatim, 2026-07-08)

> "Do we have a robust 'take over a tmux session' integrated? We
> basically need first-class agent manipulation IN this framework."

The honest audit that scaffolded this phase: Phase 87 shipped a real,
consent-gated, audited steering channel — but scoped three ways:
**text-only** (no `C-c`/arrows/control keys), **registry-gated** (only
hook-registered agent panes, not arbitrary tmux), and **local-only**
(no cross-machine). This phase removes all three, on the same spine.

## The spine you extend (do NOT rebuild)

| Piece | Where | Reuse |
|---|---|---|
| The grant store (arm/disarm/require_grant, `%N` pinned, monotonic, fail-closed) | `coder_steering.py` | verbatim — new verbs call `require_grant` |
| The chokepoint | `coder_steering.deliver` | the model for `deliver_keys`; ONE path per pane |
| The literal send craft | `tmux_transport.send_text_to_pane` (`send-keys -l`) | add `send_keys_to_pane` (named keys) beside it |
| The audit | `db/steering.py` (`steering_audit`, hash+head) | keys audit the same way (the key list is the "text") |
| The routes | `coder_steering_routes.py` | new verbs are new routes on the same router |
| The chokepoint census | `test_steering_chokepoint.py` | extend to pin the new send-keys call sites |
| The mesh relay (cross-machine) | `intel/mesh_relay.py`, the pull-worker + liveness | the precedent for HS-89-03 |

## The three verbs

1. **Full key control (HS-89-01).** `send_keys_to_pane(pane, keys)` —
   `keys` is a list of tmux key names (`C-c`, `Enter`, `Escape`, `Up`,
   `Down`, `Tab`, or a `-l` literal run). `coder_steering.deliver_keys(
   key, keys, current_target, ...)` is the SAME grant-check → verify
   `%N` → send → audit as `deliver`, but sends keys. The audit's
   text_head is the key sequence rendered (`C-c`, `Down Down Enter`).
   Route: `POST /api/coders/{key}/keys`. `C-c` interrupts; arrows drive
   a TUI.
2. **Attach to any pane (HS-89-02).** `list_panes(runner)` →
   `tmux list-panes -a -F '#{pane_id}\t#{session_name}\t#{window_index}\t
   #{pane_current_command}\t#{pane_title}\t#{pane_active}'` → every pane
   on the machine. Route: `GET /api/coders/steering/panes`. The peek/
   arm/steer/keys verbs accept a raw pane target (a `pane:%N`
   pseudo-key) resolved directly, NOT through `_registry_session`.
   Watching any pane is free; steering needs a grant pinned to its `%N`.
   A hand-started pane is now first-class.
3. **Cross-machine steering (HS-89-03).** A far node runs a steering
   worker; the hub relays a peek/steer/keys command; the far node
   executes the tmux op LOCALLY and returns the result. The grant +
   audit live on the hub; the far node authenticates (the mesh token).
   Honest liveness: a quiet node refuses by name. Only keys + hashes
   cross the wire — no pane bytes beyond the peek snapshot, no secrets.
   Scope the wire honestly (the HS-88-04 discipline): ship the
   receiving/relay half proven two-process; defer a fleet.

## The safety rules (pinned — the whole point)

- **Watch free, manipulate armed.** Peek/list are read-only, no grant.
  Any key toward a pane (text OR control) needs an active grant for
  that pane, pinned to its `%N`, re-verified before every send.
- **One chokepoint per pane.** `deliver` and `deliver_keys` are the
  ONLY callers of the tmux send craft; the census grep pins it.
- **Refuse AND revoke** on a recycled/retargeted pane — for keys too.
- **Everything audited**, keys included (the sequence, hashed + head).
- **A human behind every keystroke.** No autonomous manipulation.

## Gotchas

- `tmux send-keys` named keys: `C-c` (Ctrl-C), `Escape`, `Up`/`Down`/
  `Left`/`Right`, `Tab`, `Enter`, `BSpace`. A literal run uses `-l`.
  Do NOT mix `-l` and named in one call — send them as ordered calls
  or one `send-keys` with named args.
- The submit-craft lesson stays: Claude Code TUIs want a raw `\r`
  (`send_text_to_pane` already does this); `Enter` as a NAMED key is
  for OTHER TUIs — offer both.
- Read the suite output from a file before flipping (memory).
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Prove on real metal: interrupt a REAL runaway, drive a REAL TUI.
