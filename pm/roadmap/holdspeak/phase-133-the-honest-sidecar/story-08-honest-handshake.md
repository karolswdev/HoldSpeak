# HS-133-08 — The honest handshake

- **Project:** holdspeak
- **Phase:** 133
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

The sidecar's front door lies twice. `auth.py`'s docstring claims hub
bearer authentication that never happens (both token paths yield
`PrincipalKind.OWNER`, auth.py:32) and stores a `HOLDSPEAK_URL`/`url`
field nothing reads. And Phase 122's charter promised a `holdspeak-mcp`
executable (story-07-mcp-server.md:63) that was never delivered —
`pyproject.toml` ships only `holdspeak`, and no `.mcp.json` exists for
client discovery despite CLAUDE.md's stale reference to one.

## Scope

### In

Per assets/surface-spec.md §2.1-2.2, verbatim:

- `auth.py` rewritten to the spec's corrected form: `DEFAULT_HOLDSPEAK_URL`,
  the `url` field, and the `HOLDSPEAK_URL` env read removed (grep-verified
  unimported); the docstring states process-boundary-as-trust-boundary
  and that the token only sets the identity label (`mcp-token` vs
  `local-mcp`), never gates access.
- `holdspeak-mcp = "holdspeak.mcp.server:main"` added to
  `[project.scripts]` (`main()` exists at server.py:109).
- `.mcp.json` created at repo root, holdspeak-only (counsel Q1), with
  the spec's exact JSON.

### Out

- Real authentication (the process boundary IS the correct model for a
  stdio sidecar). dw-mcp wiring (counsel Q1). Any server.py behavior
  change.

## Acceptance criteria

- [ ] `grep -r HOLDSPEAK_URL holdspeak/` returns nothing; the sidecar
  boots and handshakes without it.
- [ ] `HOME=$(mktemp -d) uv run holdspeak-mcp` accepts an `initialize`
  request on stdio and answers with the server info.
- [ ] `.mcp.json` exists, valid JSON, holdspeak entry only.
- [ ] A test asserts `resolve_auth()` yields OWNER with identity
  `local-mcp` (no token) and `mcp-token` (with token).

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py --tb=short`
  (auth tests) plus the live one-shot handshake pasted into evidence.
