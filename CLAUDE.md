# Working agreements for HoldSpeak

This file is loaded automatically by Claude Code when it opens this
repo. It tells you (the agent) the rules of the road.

## PMO hygiene gate (Delivery Workbench)

This repo runs Delivery Workbench (installed from
`~/dev/reusable-processes/pmo-roadmap`; refreshed HS-86-02,
2026-07-07). The full agent workflow — orientation, story verbs,
evidence capture, the stamped commit contract, MCP tools — lives in
the managed "Delivery Workbench (PMO rails)" block at the end of this
file. That block is canon for HOW to commit; the short version:
stage, `.githooks/dw contract new`, verify + flip every box honestly,
`git commit`. Hand-written contracts are refused by the gate (the
stamped index tree is the freshness proof).

**One-time setup per fresh clone:**

```bash
git config core.hooksPath .githooks
```

**Methodology:** `pm/roadmap/roadmap-builder.md`.
**Rules canon:** `pm/roadmap/PMO-CONTRACT.md`.

## Roadmap

- **Project README:** `pm/roadmap/holdspeak/README.md`.
- **Current phase:** linked from the project README "Current phase" line.
- **Operating cadence:** every shipping commit updates the story
  header status, the phase's `current-phase-status.md` story-status
  row + "Where we are", this README's "Last updated" line, and any
  project-canon doc the story explicitly mentions. See
  `pm/roadmap/holdspeak/README.md` §"Operating cadence".

## Source canon

These are the docs phases must be grounded in. If any phase document
disagrees with one of these, canon wins:

- `docs/internal/CONSTITUTION.md` — **the supreme canon**: the ratified
  articles every phase, story, and design decision is measured against.
  Where any doc below disagrees with it, the Constitution wins.
- `README.md` — public install + usage surface.
- `docs/internal/POSITIONING.md` — the positioning canon: the story, the
  pillars, the named competitive frame, canonical feature names, and the
  voice rules every user-facing doc must align to.
- `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — parent plugin RFC.
- `docs/internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md` — meeting-side multi-intent routing (MIR-01).
- `docs/internal/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` — dictation pipeline (DIR-01).
- `docs/internal/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` — web-first runtime migration.
- `pyproject.toml` — package contract.

## Test commands

- All tests: `uv run pytest -q`
- Doctor only: `uv run pytest -q tests/ -k doctor`
- A single phase's planned tests: see the relevant story file's "Test plan" section.

The `Tests ran` rule (PMO contract §3) requires you to actually run
the relevant tests via these commands and read the output before
flipping a story to `done`. Type-check is not validation.

<!-- BEGIN DELIVERY WORKBENCH (managed by pmo-roadmap install.sh/update.sh — edits inside are overwritten) -->

## Delivery Workbench (PMO rails)

This repository uses Delivery Workbench: an evidence-first commit gate
over a Markdown roadmap under `pm/roadmap/<project>/` (phases, stories,
paired evidence files). Markdown is the source of truth; `.githooks/dw`
is the CLI for everything below. Run `.githooks/dw doctor` if anything
seems miswired. `.githooks/dw-workbench --root .` serves a localhost
web view of the roadmap (browse, health, trace, guarded edit).

Orient before working:

- `.githooks/dw context [project] --compact` — JSON snapshot: issues,
  warnings, next story, per-story trace paths.
- `.githooks/dw next [project]` — the next actionable story
  (exit 0 = found, 2 = nothing actionable, 1 = error; `--json` for a
  machine-readable object).
- `.githooks/dw check [project]` — structural and evidence-content
  lint; greppable `ERROR <path>: <issue>` lines, exit 1 on issues.

Work a story (statuses: backlog | ready | in-progress | blocked | done;
done-synonyms complete/closed/shipped gate identically):

1. `.githooks/dw story status <project> <phase> <story> in-progress`
2. Do the work.
3. Prove it — run the real verification through
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   (records command, exit code, index tree, and output into the story's
   evidence file; screenshots/binaries go under `assets/` next to it).
4. `.githooks/dw story status <project> <phase> <story> done`
   (refuses without evidence).

Commit — every commit passes the gate:

1. Stage everything (`git add …`), THEN generate the contract:
   `.githooks/dw contract new [--story ID] [--consent yes --reasons "…"]
   [--tests-capture <evidence-path>[#ts]]`
   It stamps machine-verified facts (branch, HEAD, index tree, staged
   sample, story IDs); restaging afterwards invalidates it (regenerate
   with `--force`).
2. Honestly verify each rule, then flip every `- [ ]` to `- [x]` in
   `.tmp/CONTRACT.md`. A `--tests-capture` reference pre-checks the
   "Tests ran." box and is re-verified by the gate.
3. `git commit`. Trailers (`PMO-Story`, `PMO-Contract-Digest`) and the
   contract archive under `.git/pmo-contract-archive/<sha>` are
   automatic; the contract survives an aborted commit.

Gate rules the machinery enforces: one story flips done per commit
(bundle only with `.tmp/BUNDLE-OK.md` + one-line rationale), the
flipped story's `evidence-story-NN.md` ships in the same commit, and
evidence never appears or disappears orphaned. Preflight any time with
`.githooks/dw gate [--porcelain]` — it never consumes the contract.
`.githooks/dw verify [<base>..<head> | --all]` re-derives the
structural rules from pushed history alone — audit any range,
no local contract needed.

MCP-capable agents: prefer the MCP tools over shelling out —
`.githooks/dw-mcp` (wired via `.mcp.json`) serves the same core as
structured tools with identical refusals: orientation (`dw_context`,
`dw_next`, `dw_check`, `dw_doctor`), verification (`dw_verify`,
`dw_gate`), guarded mutations (`dw_story_status`,
`dw_evidence_capture`, `dw_contract_new`). Certification is never a
tool call: flipping contract boxes stays a manual, deliberate edit
(see `docs/mcp.md` in the framework repo).

Never use `--no-verify`; when blocked, read the banner — it names the
rule and the remediation, and includes the exact contract template.

Slash commands (Claude Code, under `.claude/commands/`): `/dw-next`,
`/dw-story-done`, `/dw-contract`, `/dw-adopt`.

Canon: `pm/roadmap/PMO-CONTRACT.md` (rules),
`pm/roadmap/roadmap-builder.md` (methodology).

<!-- END DELIVERY WORKBENCH -->
