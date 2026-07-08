# HS-90-01 — The factory: spawn, rename, kill

- **Project:** holdspeak
- **Phase:** 90
- **Status:** done
- **Shipped:** 2026-07-08 — the lifecycle rides the spine. `coder_factory.spawn/rename/kill` (name-validated, kill gated like a steer). Proven live: spawn → rename → arm → steer → kill, the audit reading back every act; a payload name refused before tmux. Suite 3514/0. Evidence: [evidence-story-01.md](./evidence-story-01.md).
- **Depends on:** Phase 89 (the manipulation spine)
- **Unblocks:** HS-90-02, HS-90-03

## Problem

Phase 89 manipulates panes that already exist. The lifecycle — create a
session, relabel it, end it — is the missing half of "take over the
terminal." It must ride the same consent/audit discipline, and it must
be injection-safe (a session name is user input).

## Scope

- In: `holdspeak/coder_factory.py` — `spawn(name, command=None)`
  (`tmux new-session -d`, returns the new `%N`), `rename(target, name)`
  (`tmux rename-session`), `kill(key, current_target, scope)`
  (armed + verified `%N`, `tmux kill-pane`/`kill-session`); strict name
  validation (alnum/dash/underscore, argv lists never a shell string);
  every act audited; routes `POST /api/coders/factory/{spawn,rename}` +
  `POST /api/coders/{key}/kill`.
- Out: launching an agent into the pane (the human runs their command);
  cross-machine factory (rider); the UI (HS-90-02/03).

## Acceptance criteria

- [x] `spawn` creates a real detached session and returns `{session,
      pane_id}`; a name with a shell metachar / space / leading `-` is
      refused BY NAME (never reaches tmux); tmux-absent is typed. Audited
      (`test_coder_factory.py`).
- [x] `rename` relabels a session; the same name guard; audited.
- [x] `kill` is gated like a steer: unarmed refuses, a recycled pane
      refuses AND revokes, an armed kill terminates the VERIFIED `%N`
      (pane or session scope) and drops the grant; audited. Pinned by
      tests mirroring `deliver`, and a shape test (require_grant before
      `kill-pane`).
- [x] The routes return typed results; `POST /kill` is a 409 when
      unarmed; spawn bad-name is 409 (`test_web_routes_coders_steer.py`).
- [x] Live (`evidence-story-01.md`): spawn → rename → arm → steer → kill;
      the audit read back all five acts with the pane named; a payload
      name refused before tmux.
- [x] Full suite green (3514/0); api-surface regenerated; the factory's
      destructive tmux verbs (`kill-pane`/`kill-session`/`new-session`/
      `rename-session`) pinned to `coder_factory.py` by a census.

## Test plan

- Unit: name validation (good/bad); spawn/rename argv; the kill
  chokepoint (unarmed/recycled/armed, audit) mirroring deliver.
- Integration: a live spawn → rename → arm → kill against real tmux.

## Implementation direction

- **Name guard:** `^[A-Za-z0-9_-]{1,64}$`; anything else → `bad_name`
  (refused before tmux). `command` (for spawn) is passed as tmux's
  trailing arg (its own argv slot), never concatenated into a shell
  string beyond what tmux itself runs.
- **Kill = the steer gate:** `kill` calls `require_grant(key,
  current_target)` then kills the verified `%N` (pane) or its session.
  Reuse the `deliver` shape (grant → verify → act → audit). Add
  `send`-style indirection only if a test needs it; otherwise call tmux
  directly through the injectable runner.
- **Audit:** reuse the steering audit; the "text head" is the act
  (`spawn hs:work`, `kill %5 (session)`), so the trail reads plainly.
