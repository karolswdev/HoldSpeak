# HS-0-01 — Install pmo-roadmap framework

- **Project:** holdspeak
- **Phase:** 0
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-1-01 (DIR-01 begins under the gate)
- **Owner:** agent (this session)

## Problem

Until this session, HoldSpeak shipping discipline was implicit: the
recent `0b05af6` and `a102b65` commits combined feature work and
docs without an evidence/contract trail. Phase 1 (DIR-01) is too
big to ship without that trail. The user's request: "implement this
framework so we manage it properly... this would ensure discipline."

## Scope

- **In:**
  - Install `pmo-roadmap` from `~/dev/reusable-processes/pmo-roadmap` via `install.sh`.
  - Scaffold `pm/roadmap/holdspeak/` with the `phase-0-setup/` skeleton.
  - Replace the README/phase-status/story stubs with project-real content.
  - Create `CLAUDE.md` at repo root with the PMO gate snippet.
  - Create phase-1 skeleton (`current-phase-status.md`, first two stories) so DIR-01 has a home.
- **Out:**
  - Customizing rules beyond the canonical 7 (no project extensions yet — adopt as-is).
  - Migrating prior commits into the framework retroactively beyond phase-0.
  - Any DIR-01 implementation work.

## Acceptance criteria

- [x] `pm/roadmap/holdspeak/README.md` describes vision, source canon, phase index.
- [x] `pm/roadmap/PMO-CONTRACT.md` and `pm/roadmap/roadmap-builder.md` present (copied by installer).
- [x] `.githooks/pre-commit` exists and is executable.
- [x] `git config --get core.hooksPath` returns `.githooks`.
- [x] `.tmp/` is in `.gitignore`.
- [x] `CLAUDE.md` exists at repo root and references the PMO gate.
- [x] `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` exists with the DIR-01 spec linked as canon.

## Test plan

- **Unit:** n/a (framework install is a file-system change).
- **Integration:** Verify the hook fires by attempting a commit without `.tmp/CONTRACT.md` — expect block (manual verification, see evidence).
- **Manual:** Run `git config --get core.hooksPath`, `ls .githooks/pre-commit`, `ls pm/roadmap/holdspeak/`.

## Notes / open questions

- This story closes alongside HS-0-02 in a single commit, justified
  by `.tmp/BUNDLE-OK.md` rationale: the framework install and the
  packaging fix were in the working tree before the framework
  existed; splitting them now would create an artificial first commit
  with no real work. From the next commit forward, the one-story-per-
  commit rule applies normally.
- No project-extension rules added in this phase — the canonical 7
  are sufficient for now.
