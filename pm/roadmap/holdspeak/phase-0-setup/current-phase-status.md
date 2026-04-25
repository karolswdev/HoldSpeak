# Phase 0 — Setup

**Last updated:** 2026-04-25.

## Goal

Stand up the PMO roadmap framework against HoldSpeak and clean up the
two packaging defects that block a vanilla `holdspeak` install from
working out-of-the-box. This phase establishes the operating discipline
that phase 1 (DIR-01) will be executed under. This section is
**immutable** for the life of the phase.

## Scope

- **In:**
  - Install `pmo-roadmap` framework into the repo (methodology, contract, hook, scaffold).
  - Move `fastapi` + `uvicorn[standard]` into core deps in `pyproject.toml` (web is the default runtime).
  - Add `Web runtime` doctor check (`holdspeak/commands/doctor.py`).
  - Bump version to `0.2.1`.
  - Add `CLAUDE.md` with the PMO gate snippet.
- **Out:**
  - All DIR-01 (dictation pipeline) work — phase 1.
  - Any `[meeting]` extra reshaping beyond removing now-redundant `fastapi`/`uvicorn` entries.
  - `install.sh` changes — once core deps include web, the curl install just works.

## Exit criteria (evidence required)

- [x] `pm/roadmap/holdspeak/` scaffold exists with README + phase-0 folder.
- [x] `.githooks/pre-commit` installed and `git config core.hooksPath` set to `.githooks`.
- [x] `pm/roadmap/PMO-CONTRACT.md` and `pm/roadmap/roadmap-builder.md` present.
- [x] `pyproject.toml` has `fastapi` and `uvicorn[standard]` in core `dependencies`; `[meeting]` no longer lists them.
- [x] `holdspeak doctor` reports `Web runtime: PASS` on the reference machine — see `evidence-story-02.md`.
- [x] `pytest -k doctor` passes (9 tests) — see `evidence-story-02.md`.
- [x] `CLAUDE.md` exists at repo root with the PMO gate snippet.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-0-01 | Install pmo-roadmap framework | done | [story-01-bootstrap](./story-01-bootstrap.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-0-02 | Fix vanilla `holdspeak` install (web deps + doctor check) | done | [story-02-packaging-fix](./story-02-packaging-fix.md) | [evidence-story-02](./evidence-story-02.md) |

## Where we are

Phase 0 is closed in this commit. Both HS-0-01 (framework install) and
HS-0-02 (packaging fix) ship as a deliberate bundle — rationale in
`.tmp/BUNDLE-OK.md`: HS-0-02 was already executed in this session
before the framework existed, splitting it now would create an
artificial first commit with no real work. From the next commit forward
the one-story-per-commit rule applies normally. Phase 1 (DIR-01) is
ready to begin in a fresh session — start with `HS-1-01`
(`phase-1-dictation-intent-routing/story-01-baseline-and-spike.md`).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Bundling HS-0-01 + HS-0-02 in one commit normalizes bundling | low | Single rationale recorded in `.tmp/BUNDLE-OK.md`; no bundling thereafter | A second `.tmp/BUNDLE-OK.md` appears in the next 5 commits |
| Framework adds friction without payoff | low | Reassess after 5 commits; remove if friction > value | 3 consecutive commits where the gate blocked legitimate work |

## Decisions made (this phase)

- 2026-04-25 — Adopt `pmo-roadmap` framework — user request, "ensure discipline" — owner: user.
- 2026-04-25 — Mark project as post-launch (not greenfield) — `v0.2.0` is shipped and there are public install instructions — owner: agent (with rationale documented in roadmap README).
- 2026-04-25 — Move `fastapi` + `uvicorn[standard]` into core deps — web is the default `holdspeak` runtime; hiding its deps in `[meeting]` was the structural cause of the broken-default-install bug — owner: agent.
- 2026-04-25 — Use `uvicorn[standard]` (not plain `uvicorn`) — `[standard]` pulls in `websockets`, `uvloop`, `httptools`, `watchfiles`; without it the web UI spams `Unsupported upgrade request` warnings on every page load — owner: agent.

## Decisions deferred

- `[meeting]` extra reshape (split into `[intel]`, `[speaker]`, etc.) — trigger: when adding a third intel-only feature — default: leave as-is.
