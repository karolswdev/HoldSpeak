# Phase 90 — The Factory — final summary

**Closed 2026-07-08, 3/3, scaffolded and shipped the same day.**

## What it is

The fast follow to Phase 89. Phase 89 made an existing pane fully
manipulable (any key, any pane, any machine); this phase added the
session LIFECYCLE and gave the whole capability its first on-glass
surface, so a person drives a terminal from the desk instead of `curl`.

## The three stories

- **HS-90-01 — the factory (spawn/rename/kill), live.**
  `holdspeak/coder_factory.py`: `spawn` (`tmux new-session -d`, returns
  the new `%N`) and `rename` are name-validated (`^[A-Za-z0-9_][...]$`,
  first char alnum so a name can never be read as a flag) audited
  create/label acts; `kill` reuses the STEER gate outright
  (`require_grant` → verify the pinned `%N` → `kill-pane`/`kill-session`
  → drop the grant → audit). Injection-safe (argv lists, a bad name
  refuses before tmux); the destructive verbs are census-pinned to the
  one module. Proven live: spawn → rename → arm → steer → kill.
- **HS-90-02 — the manipulation surface on the web desk, screenshot.**
  The armed session pull-out gained a KEY PALETTE (`^C`/`Esc`/`Tab`/`⏎`/
  arrows → `/keys`, `^C` loud, armed-only), a `⧉ Panes` picker (attach to
  any `pane:%N`), and a NODE CHIP (this Mac / a configured node, routing
  through the relay via one `verbEndpoint` helper). The steering store is
  node-aware end to end. New hub route `GET /api/coders/steering/nodes`
  (names only, never tokens).
- **HS-90-03 — the factory on glass + the walk + close.** The picker
  gained a `+ Spawn` row; the armed pull-out gained a SESSION row with
  Rename and a two-step-confirm ⌫ Kill. The walk passed 8/8 live through
  the desk's EXACT routes: spawn → in the picker → arm → `C-c` → steer
  (`WALKED_FROM_GLASS` landed) → rename → kill (session gone) → the audit
  read it all back. Docs shipped (USER_GUIDE, SECURITY, ARCHITECTURE).

## Proof

Full suite 3514+/0; the factory lifecycle proven live twice (the
functions in HS-90-01, the desk routes in HS-90-03's walk); the web built
+ desk tests 97/97 + tsc clean; the manipulation and factory surfaces
screenshot-verified; both the key chokepoint and the factory verbs
census-pinned; voice guard green.

## What's next / inherited

- **The iPad catches up.** The B4 track (Phase 26) has the steering
  client but no keys/panes/factory verbs and no interactive surface yet.
  The web desk is now the reference; the iPad mirrors it (a couch-felt
  build).
- **Cross-machine factory.** Kill/spawn on a remote node is deferred: the
  relay forwards peek/arm/steer/keys, not the factory verbs. A factory
  relay is a small rider on the proven precedent when wanted.
- **Launching an agent into a spawned pane.** Spawn makes the pane and
  the human runs their command; wiring an agent (claude/codex) into a
  fresh pane is a later orchestration concern.

## Decisions of record

- Kill rides the steer gate (armed + verified `%N` + audit); spawn/rename
  are explicit audited create/label acts, name/argv-safe.
- The node chip lists NAMES ONLY; a targeted node routes through the
  relay; the factory stays local (its relay is a deferred rider).
- The web bundle is built to verify and screenshot; only source is
  committed (the `dist` is gitignored).
