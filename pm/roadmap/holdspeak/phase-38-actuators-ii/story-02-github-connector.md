# HS-38-02 — GitHub write connector (`gh issue create`)

- **Project:** holdspeak
- **Phase:** 38
- **Status:** done
- **Depends on:** HS-38-01
- **Unblocks:** HS-38-05
- **Owner:** unassigned

## Problem

The first **real** write connector: turn an approved `followup_ticket_actuator` proposal
into an actual GitHub issue via `gh issue create`. The existing `github_cli` pack is
read-only (`gh pr/issue view`); this adds a *write* path that is narrowly gated so it can
do exactly one thing and nothing else.

## Scope

- **In:**
  - A **GitHub write connector** built with `build_gated_connector` (HS-38-01): permission
    `shell:exec` via `PermissionGate.run_subprocess`, manifest allow-listed to
    `gh issue create` **only** (repo / title / body from the proposal payload). Returns the
    created issue ref (url/number) as the result; a non-zero `gh` exit → raises → the
    executor records `failed` + audit.
  - Point a follow-up actuator at it (reuse `followup_ticket_actuator`'s proposal, or a
    `github_issue_actuator` sibling whose payload carries `repo`/`title`/`body`).
  - An **opt-in** test that drives the full loop (propose → approve → execute) with an
    **injected runner** (deterministic, no real `gh`); plus a refusal test (any non-`gh
    issue create` argv is refused before egress). A real run against a throwaway repo is
    documented if reachable (not in CI).
- **Out:**
  - PR comments / other `gh` writes — `gh issue create` only this story.
  - Auth management — relies on an already-authenticated local `gh`.

## Acceptance criteria

- [x] The connector runs `gh issue create` (and only that) through `PermissionGate`; the
      payload maps to `--repo`/`--title`/`--body`; the created issue ref is returned.
- [x] A non-allow-listed argv (e.g. `gh repo delete`) is refused **before** egress; the
      runner is never invoked (spy).
- [x] Full loop (opt-in, injected runner): approve → execute → `executed` + the issue ref
      in the result + an audit row; gate off / unapproved ⇒ no `gh` call.
- [x] Default suite makes no real `gh` call; suite green; module ruff + F821 clean.

## Test plan

- Unit: argv built from payload; allow-check permits `gh issue create`, refuses others.
- Unit (loop): injected runner returns a fake issue url → `executed`; runner raises →
  `failed` + audit.
- Manual/opt-in: real `gh issue create` against a throwaway repo (documented, gated, not
  CI).
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Notes / open questions

- Decision (this story): the GitHub connector is a **host-side gated connector** (the
  executor injects it), mirroring Phase-37's `build_outbox_connector` — not a discovered
  pack. Record in the evidence.
- Keep the actuator's `run()` pure (build the proposal from context); the `gh` call lives
  only in the connector, reached only after approval + the gate.
