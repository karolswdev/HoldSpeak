# Phase 90 — The Factory (session lifecycle + the manipulation UI)

**Last updated:** 2026-07-08 (phase scaffolded).

## Goal

Phase 89 made an EXISTING pane fully manipulable (any key, any pane, any
machine). This phase adds the LIFECYCLE — spawn a session, rename it,
kill it — on the same consent/audit spine, and gives the manipulation
its first on-glass surface (the fast follow the owner asked for): a key
palette, a pane picker, and a node chip on the web desk, so a human
drives a terminal from the desk instead of from `curl`.

The factory verbs ride the SAME chokepoint discipline. Spawn is a
create act (no pane to pin yet) — explicit + audited, name-validated so
a session name can never carry a shell payload. Kill is the ultimate
manipulation — it is gated exactly like a steer: armed, the pane `%N`
re-verified, refuse+revoke on a recycled pane, audited. Rename is a low
-consequence label change — explicit + audited. Nothing autonomous; a
human behind every act.

## Scope

- In: `coder_factory.spawn/rename/kill` (name validation, tmux, audited);
  the routes (`POST /api/coders/factory/{spawn,rename}`,
  `POST /api/coders/{key}/kill`); the web-desk manipulation surface (key
  palette + pane picker + node chip, reading the Phase-89 routes) and the
  factory controls (spawn/kill/rename) on glass; the walk + docs + close.
- Out: launching an AGENT into a spawned pane (spawn makes the pane; what
  runs in it is the human's command — no agent orchestration here);
  cross-machine factory (relay already reaches node steering; factory
  relay is a rider if the walk needs it); a full terminal emulator (peek
  stays the hash-gated poll).

## Exit criteria (evidence required)

- [ ] Spawn creates a real detached session and returns its pane; rename
      relabels it; kill (armed) terminates the verified pane; a recycled
      pane refuses+revokes the kill — every act audited (HS-90-01, live).
- [ ] The web desk drives a real pane: a key palette sends `C-c`/arrows,
      a pane picker attaches to any pane, a node chip targets a machine —
      screenshot-proven (HS-90-02).
- [ ] The factory is on glass: spawn/kill/rename from the desk, with the
      kill guarded by the arm (HS-90-03), screenshot-proven.
- [ ] The walk: spawn → steer → rename → kill, live, from the desk;
      the audit answers who/what/where; suite + guards green; docs
      shipped (HS-90-03).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-90-01 | The factory — spawn, rename, kill | **done** (2026-07-08, live) | [story-01-factory](./story-01-factory.md) | [evidence-01](./evidence-story-01.md) |
| HS-90-02 | The manipulation surface on the web desk | backlog | [story-02-manip-ui](./story-02-manip-ui.md) | - |
| HS-90-03 | The factory on glass + the walk + close | backlog | [story-03-factory-glass-walk](./story-03-factory-glass-walk.md) | - |

## Where we are

Scaffolded 2026-07-08 as the fast follow to Phase 89 (first-class
manipulation, CLOSED 4/4). Phase 89 made a pane fully manipulable; this
adds the lifecycle + the first UI.

**HS-90-01 done (2026-07-08, live) — the lifecycle rides the spine.**
`holdspeak/coder_factory.py`: `spawn` (`tmux new-session -d`, returns the
new `%N`) and `rename` are name-validated (`^[A-Za-z0-9_][...]$`, first
char alnum so a name can't be read as a flag) audited create/label acts;
`kill` is gated EXACTLY like a steer — `require_grant` → verify the
pinned `%N` → `kill-pane`/`kill-session` → drop the grant → audit.
Routes `POST /api/coders/factory/{spawn,rename}` + `POST /api/coders/
{key}/kill`. The destructive tmux verbs are census-pinned to the one
module. Proven live: spawn → rename → arm → steer (`BORN_AND_STEERED`
landed) → kill (session gone, grant dropped); a payload name
(`evil; reboot`) refused before tmux; the audit read back all five acts.
Suite 3514/0. Next: HS-90-02 (the manipulation UI on the web desk).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Spawn/rename take a name that carries a shell payload | the injection surface | strict name allow-list (alnum/dash/underscore); argv lists, never a shell string; a bad name refuses BY NAME | a session name reaching a shell unparsed |
| Kill terminates the wrong pane | the whole point of pinning | kill is gated like a steer: armed + `%N` re-verified + refuse/revoke; kills only the verified pane | a kill that skipped the grant/verify |
| The UI makes manipulation feel casual (a key sent by accident) | medium | the arm chip + countdown stays the gate on glass; keys need the armed window; kill wants an explicit confirm | a key/kill sent without the armed window |

## Decisions made (this phase)

- 2026-07-08 — Kill rides the STEER gate (armed + verified `%N` + audit);
  spawn/rename are explicit audited create/label acts (no pane to pin at
  spawn time). All three are name/argv-safe (allow-list, argv lists).

## Decisions deferred

- Launching an agent (claude/codex) INTO a spawned pane — default: spawn
  makes the pane, the human runs what they want; agent orchestration is a
  later concern.
- Cross-machine factory (spawn/kill on a node) — default: local; add a
  factory relay only if the walk needs it (the steering relay precedent).
