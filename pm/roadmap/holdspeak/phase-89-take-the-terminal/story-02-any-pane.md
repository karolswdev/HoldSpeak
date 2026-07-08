# HS-89-02 — Attach to any pane: beyond the registry

- **Project:** holdspeak
- **Phase:** 89
- **Status:** done
- **Shipped:** 2026-07-08 — the registry is no longer the gate. `list_panes` names every tmux pane; a `pane:%N` key steers ANY of them directly. Proven live: a HAND-started pane (confirmed not an agent session) was discovered, watched free, armed, steered, and keyed. Suite 3488/0. Evidence: [evidence-story-02.md](./evidence-story-02.md).
- **Depends on:** HS-89-01
- **Unblocks:** HS-89-03

## Problem

Steering is gated on the hook registry: only sessions the agent hooks
recorded (with a captured pane) can be peeked or steered. A tmux
session you start BY HAND is invisible to the desk. First-class
manipulation means attaching to ANY pane on the machine — the registry
becomes one source of panes, not the gate.

## Scope

- In: `coder_steering.list_panes(runner)` — every tmux pane on the
  machine with its `%N`, session, window, current command, title, and
  active flag; `GET /api/coders/steering/panes`; the peek/arm/steer/
  keys verbs accept a RAW pane target (a `pane:%N` pseudo-key) resolved
  directly (not through `_registry_session`); watching any pane is
  free, steering/keys need a grant pinned to that `%N`.
- Out: spawning/killing sessions (B3); cross-machine (03); changing
  how registered sessions steer (their `agent:session_id` keys keep
  working — this ADDS the pane path).

## Acceptance criteria

- [x] `list_panes` returns every pane (`tmux list-panes -a`), typed
      absence when tmux is missing, honest empty on no-server, each
      carrying its `%N` + command + title; parse pinned
      (`test_coder_steering_panes.py`).
- [x] A `pane:%N` key peeks read-only with no grant; arm pins that
      `%N`; steer/keys deliver to it under the grant; a recycled `%N`
      refuses + revokes (the Phase-87 spine, unchanged) — route tests.
- [x] A pane started BY HAND (never in the registry) is discoverable
      via `/panes`, watchable, and steerable under a grant — proven
      live (`evidence-story-02.md`): discovered, confirmed not an agent
      session, peeked free, armed, steered + `C-c`, the text landed.
- [x] The registry path is unchanged: an `agent:session_id` key still
      resolves + steers exactly as in Phase 87 (a regression test).
- [x] Full suite green (3488/0, read from the file); api-surface regen.

## Test plan

- Unit: `list_panes` parse (fake runner); the `pane:%N` resolution in
  peek/arm/steer/keys; the registry-still-works regression.
- Integration: a live hand-started pane — discover, peek, arm, steer.
- Manual / device: attach to a pane the hooks never saw.

## Implementation direction

- **Discovery:** `tmux list-panes -a -F '#{pane_id}\t#{session_name}\t
  #{window_index}\t#{pane_current_command}\t#{pane_title}\t#{pane_active}'`
  via the injectable runner; parse tab-split rows; `shutil.which` guard.
- **The pane key:** a `pane:%N` pseudo-key. In the routes, branch on
  the key prefix: `pane:` → resolve the target as `%N` directly (verify
  it still exists via `resolve_pane_identity`); else → the Phase-87
  `_registry_session` path. `require_grant` already verifies against
  the CURRENT target, so a `pane:%N` grant re-checks `%N == %N`
  trivially, and a dead `%N` refuses+revokes.
- **Honesty:** a `pane:%N` that no longer resolves is `pane_gone`
  (typed), never a 500. The panes list marks the active pane and the
  command so the human picks the right one.
- **Safety unchanged:** watching any pane is free; manipulating any
  pane is armed + audited + one-chokepoint — the reach grows, the
  consent does not shrink.
