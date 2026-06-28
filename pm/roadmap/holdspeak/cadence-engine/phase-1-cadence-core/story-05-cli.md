# CAD-1-05 — CLI: `holdspeak cadence status | loops | run-now`

- **Program:** cadence-engine · **Phase:** 1 · **Status:** todo
- **Depends on:** CAD-1-01..04. **Unblocks:** the phase exit criteria (the first usable surface).

## Problem

The substrate needs a human surface to prove it works before any web/Telegram UI — and the design
calls for a CLI either way.

## The design

Follow the verified CLI pattern: a subcommand in `holdspeak/main.py` (subparsers) dispatching to
`holdspeak/commands/cadence.py` → `run_cadence_command(args, *, stream=None) -> int`.

- **`holdspeak cadence status`** — is cadence enabled? policy summary (quiet hours, max/day,
  pressure), loop counts by status, last tick time.
- **`holdspeak cadence loops`** — list open loops, ordered by `stale_score` desc: id, title,
  project, source_type, score, owner, status. `--json` for the structured form; `--all` to include
  closed/killed.
- **`holdspeak cadence run-now`** — run one `CadenceService.tick(now)` synchronously (no thread,
  works even when `enabled=False` so it's testable/dogfoodable) and print the projected + scored
  loops + which would be due. This is the phase's headline deliverable.

Register: a `cadence` subparser in `main.py` with a `cadence_action` sub-subparser, and an
`elif args.command == "cadence": return run_cadence_command(args)` handler. Reuse `get_database()`.

## Scope

- **In:** the three subcommands + `--json`/`--all`; argparse registration; the handler.
- **Out:** snooze/kill from the CLI (Phase 2 adds lifecycle verbs once the web surface exists — or a
  fast-follow if trivial), brief/closeout (Phases 5/6).

## Proof / acceptance

- `holdspeak cadence run-now` on a seeded DB prints the projected loops with scores and due flags,
  and is idempotent across runs.
- `holdspeak cadence loops --json` emits valid JSON the future web/Telegram surfaces can reuse.
- `holdspeak cadence status` reflects `enabled` honestly.

## Test plan

`tests/unit/test_cadence_cli.py` — invoke `run_cadence_command` with a fake/seeded DB + a captured
stream; assert ordering, `--json` shape, and that `run-now` works with `enabled=False`.
`uv run pytest -q tests/unit/test_cadence_cli.py`.
