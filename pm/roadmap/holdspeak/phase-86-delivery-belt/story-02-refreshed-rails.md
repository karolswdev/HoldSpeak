# HS-86-02 — The refreshed rails: stamped gate + embedded dw

- **Project:** holdspeak
- **Phase:** 86
- **Status:** done
- **Depends on:** HS-86-01
- **Unblocks:** HS-86-03
- **Owner:** unassigned

## Problem

This repo runs an April-vintage framework install: one bash
pre-commit, no `commit-msg`/`post-commit`, no embedded `dw`, no
agent-docs block (`dw doctor`: four FAILs). The belt shells the
repo-embedded `.githooks/dw`; the gate that stamps facts and archives
contracts is also what makes the belt's gate-station lights real.
Refresh the rails from upstream main (with phase 16 merged).

## Scope

- In: `update.sh` (delivery-workbench, post-PR-#2 main) applied to
  this repo — embedded `dw` + `dw_pmo`, stamped-contract pre-commit,
  commit-msg trailer stamping, post-commit contract archive, the
  workbench/mcp helpers, `.claude/commands/dw-*` slash commands; the
  CLAUDE.md managed block via `.githooks/dw agent-docs` with the
  HoldSpeak-specific sections (tests, canon, cadence) kept outside
  the block and reconciled (the old hand-written contract walkthrough
  goes — the block owns that story now); `dw doctor` healthy; THIS
  story's commit is the first through the stamped gate.
- Out: enabling work-logs (stays off); rewriting `.githooks`
  config/local seams (none exist here); changing the PMO-CONTRACT
  rules; any hub code.

## Acceptance criteria

- [ ] `.githooks/dw doctor` reports healthy (hooks, dw-cli,
      agent-docs all ok).
- [ ] This story's own commit carries `PMO-Story: HS-86-02` and a
      `PMO-Contract-Digest` trailer, and the contract is archived
      under `.git/pmo-contract-archive/` (shown in evidence).
- [ ] CLAUDE.md holds the managed block verbatim (guarded by
      `dw check`'s rider drift detection) plus the HoldSpeak
      sections; no instruction contradicts the block.
- [ ] `git config core.hooksPath` still `.githooks`; full suite
      green; a deliberately unstamped hand-written contract is
      refused by the new gate (captured refusal in evidence).

## Test plan

- Unit: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Integration / Cypress: the doctor run + the refusal capture + this
  commit's own trailers.
- Manual / device: n/a.

## Notes / open questions

- The refresh changes every future commit's flow in this repo:
  stage → `.githooks/dw contract new` → verify + flip boxes →
  commit. The banner names remediations; never `--no-verify`.
