# HS-85-03 — `holdspeak mesh serve`, the edge worker

- **Project:** holdspeak
- **Phase:** 85
- **Status:** done
- **Depends on:** HS-85-01
- **Unblocks:** HS-85-05
- **Owner:** unassigned

## Problem

The wire needs a real node on the other end. The reference worker is a CLI
any machine can run: it turns that machine into a mesh edge — polling the
hub for relay work, executing each job on its OWN effective provider (its
engine, its profiles, its keys — nothing transits), and posting results
back. Running the command IS the consent (the Phase-52 posture: configuring
is consent, off by default because it never runs unless started).

## Scope

- In: `holdspeak mesh serve --hub <url> [--node <name>] [--token-env
  HOLDSPEAK_HUB_TOKEN]` — resolves the node name via the existing
  `resolve_device_name()` default; polls `POST /api/mesh/relay/claim` on
  the pinned cadence (~3s; jittered); executes a claimed `llm` job through
  the node's own `effective_intel_cloud`-resolved engine
  (`build_configured_meeting_intel().run_prompt(...)`); posts
  `complete`/`fail`; exponential backoff on hub-unreachable; clean SIGINT
  shutdown (in-flight job finishes or fails honestly).
- In: every claim/execute/complete logged as one honest line each (node,
  job id, duration, outcome) — the worker's log is walk evidence.
- In: a `--once` flag (claim at most one job, run it, exit) — the testing
  and scripting seam.
- Out: daemonization/launchd, TLS/tailnet transport concerns (the hub URL
  is whatever the mesh already uses), the Apple worker (HSM follow-up),
  serving transcription.

## Acceptance criteria

- [ ] Against a test hub (in-process app): `mesh serve --once` claims a
  queued job, executes it via an injected engine, and the hub row completes
  with the result verbatim (test).
- [ ] A job whose execution raises posts `fail` with the error message
  verbatim (test).
- [ ] Hub unreachable ⇒ backoff, no crash-loop; SIGINT mid-poll exits
  cleanly (tests where cheap; the loop is factored so the poll step is
  unit-testable without real time).
- [ ] The worker's claims stamp liveness (asserted through the HS-85-01
  `live_nodes` helper in an end-to-end unit test).
- [ ] No config file changes: the command's arguments are its whole
  contract.

## Test plan

- Unit: `tests/unit/test_mesh_serve_worker.py` — the loop factored into
  testable steps (claim/execute/report), engine injected;
  `uv run pytest -q tests/unit -k mesh_serve`.
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: HS-85-05 runs the real worker as a second process
  against the real hub.

## Notes / open questions

- The worker reuses the CLI's existing auth posture (`X-HoldSpeak-Token`
  from an env var; never a flag, so tokens don't land in shell history).
- Deliberately a *reference* implementation: simple, synchronous, one job
  at a time. Parallel claims are a future knob, not a v1 accident.
- **Implementation notes (recorded):** the worker rides `urllib` (the house
  pattern; `requests` is not a package dependency). `--once` does ONE claim
  poll and exits 0 on no-work (deterministic for scripts) but exits 1 on an
  unreachable hub — silence and outage are different answers. The `mesh`
  subcommand nests (`holdspeak mesh serve`) so future mesh verbs have a
  home. No route changes ⇒ api-surface untouched. The engine builds lazily
  ONCE and is reused across jobs (a GGUF engine must not reload per job).
