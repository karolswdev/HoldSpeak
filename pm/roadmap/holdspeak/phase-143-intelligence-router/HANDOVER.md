# HANDOVER — Phase 143 (Intelligence Router), written 2026-08-25

For the next agent. Main is at `8a6f8519` (PR #490); Stories 01–09 of
this phase are DONE and MERGED. Your job starts at **Story 10**. Read
this whole file, then `.githooks/dw next holdspeak` to confirm, then
go. The owner's verb is usually just "gooo" — that means open the next
story and run the full arc without waiting for permission at each
step.

## 1. The owner's standing laws (violate none of these)

1. **YOLO bar + TIE-BREAKER.** The product always runs YOLO mode.
   Findings count ONLY when a normal product action reproduces damage
   ("would this bite on a tired Tuesday?"). Crash-window /
   sleep-resume / takeover-race / adversarial scenarios are LEDGER
   NOTES, even when a probe reproduces them. **You (the orchestrator)
   are the tie-breaker over all counsel/audit output** — never
   implement a fix to make a reviewer happy; implement it because the
   product bug is real. The owner blasted a whole arc once for
   "catering to impossible edge cases to make Sol happy" — never
   again. Memory: `feedback_yolo_rigor_bar.md`.
2. **Ceremony budget.** Counsel/design rulings ONLY where the text is
   genuinely unruled; already-ruled canon needs no new ruling — turn
   open choices into [ORCH-CALL] items and decide them yourself with
   recorded dispositions. Where counsel is used at all: ONE ruling
   round + at most ONE fix round, then RATIFY-WITH-NOTES and ship.
   Story 09 shipped with ZERO counsel rounds and paired audits only —
   that is the model.
3. **Models.** Workers = Terra (`model: "terra"` on general-purpose
   agents) are lawful WHEN PAIRED WITH OPUS legs in the same arc —
   use `opus-worker` for gate audits/verification. Never Terra alone
   end-to-end; never delegate to Fable. Memory:
   `feedback_terra_order_hs143_08.md` (includes the OpenAI-endpoint
   QA-wording gotcha for Terra/Sol briefs).
4. **CI is dead.** GitHub Actions is out of minutes by owner order.
   NEVER consult, watch, or wait on CI. Verification is local-only:
   the full-suite sweep is the truth. Push and merge happen ONLY on
   the owner's explicit word ("push", "merge") — then merge without
   watching checks.
5. **Migrations stay minimal; no backwards-compat ceremony;
   ledger-not-UI** for background degradation; single-user reality.

## 2. Phase state (9/14 done, all on main)

| Story | State |
|---|---|
| 01–07 | done (pre-existing) |
| 08 Meetings/Speech/Background | done, merged PR #489 — every Meeting/speech/background model call rides the router |
| 09 Tool Capability Foundation | done, merged PR #490 — executable ToolTurn foundation + ruled fallback table; NO surface adopts it yet |
| **10 Agents/Workbenches/Recipes** | **NEXT** — also the chartered first tool adopter (Story 09 plan §7, ORCH-CALL 6: Story 10 decides which surface first invokes the ToolTurn foundation) |
| 11 HTTP/MCP sync + compatibility | backlog |
| 12 Model Library + Providers (owner glass) | backlog |
| 13 Capability Assignments experience (owner glass) | backlog — 12/13 are OWNER-FACING UI: the screenshot-walk law and "does this operate with joy?" bar apply |
| 14 Chaos glass + closeout | backlog — the kill-criteria ledger in `assets/architecture-contract.md` needs production-path evidence |

Canon to ground every story in: `assets/architecture-contract.md`
(the phase contract + kill criteria),
`proposals/inference-catalog-and-context-policy.md` (tool/catalog
canon), the per-story files, and `docs/internal/CONSTITUTION.md`
above all. Story 10's surfaces (Workbench/Recipe/agent placement and
runner entrances) are inventoried as deferred door X2 in
`assets/story-08-phase-f-cleanup-plan.md` — start your inventory
there and in the census fixtures.

## 3. The arc rhythm that works (Story 09 ran this start-to-finish in one day)

1. **Open**: `dw story status holdspeak 143 <NN> in-progress`; branch
   `feat/hs143-<NN>-<slug>` from fresh main in the primary checkout
   (worktrees only if the tree is dirty).
2. **Plan**: one Terra research worker reads the ruled canon +
   inventories the actual tree → writes
   `assets/story-<NN>-...-plan.md` (obligation register, inventory
   with file:line, slices with named proof files, [ORCH-CALL] items
   with recommendations — NO open counsel questions). You decide the
   ORCH-CALLs and append dispositions to the plan.
3. **Build**: Terra workers, 1–2 slices per round. Worker brief
   boilerplate that matters: never stage/commit; focused tests only,
   ALWAYS `uv run --python 3.13.11 pytest -q` with `HOME=$(mktemp -d)`
   when the kernel/DB is built; proofs construct PRODUCTION objects
   (decorated fakes are this phase's named sin — the only lawful fake
   is an external wire/library boundary); grep-audit every
   deleted/renamed symbol and run every referencing test file (a
   deletion round once missed 22 rigs); census/anchor/schema-snapshot
   regens are the LAST act of a round.
4. **Verify yourself**: rerun the worker's focused set with your own
   command and read the tail. Never trust tallies.
5. **Sweep**: full CI-style suite, DETACHED —
   `HOME_REAL=$HOME nohup env HOME=$(mktemp -d)
   PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright
   npm_config_cache=$HOME/.npm uv run --python 3.13.11 pytest -q -n
   auto --ignore=tests/e2e/test_metal.py > <log> 2>&1 & disown` plus
   a Monitor on the PID. (Harness-backgrounded runs have been killed
   at ~98% repeatedly; nohup+disown survives.)
6. **Triage**: diff the FAILED list against
   `assets/story-08-inherited-failure-baseline.txt` (main's own
   failure set, ~48 names reproduce). ZERO branch-new is the bar.
   Anything not in the baseline: run serially ×2 — green ×2 = xdist
   load flake (known families: workbench deadline, device-recording
   tick, refinement recovers-owner/reciprocal-stop, jira/github
   enablement, conductor deadline, delivery-campaign, glass e2es,
   sigkill process-input); red serially = REAL, send back to the
   worker with the failure chain. After any sweep:
   `git checkout -- pm/roadmap/holdspeak/phase-141-from-thought-to-work/assets/story-05a/`
   (glass e2es clobber those PNGs; never commit them).
7. **Commit**: stage by explicit path; append a Progress paragraph to
   the story file (sweep number in it); `.githooks/dw contract new
   --story HS-143-<NN>`; flip every box honestly; `git commit` with a
   real narrative message. One story per commit; never `--no-verify`.
8. **Gate audits**: at each part-gate and before story close, one
   `opus-worker` READ-ONLY audit briefed with the bar restated and
   "report evidence, not verdicts — the orchestrator tie-breaks; one
   report, no rounds". Accept only findings a normal action
   reproduces; ledger the rest.
9. **Close**: `dw evidence capture holdspeak 143 <NN> -- bash -c
   'set -o pipefail; <the full sweep command> 2>&1 | tail -120'`
   (pipefail = true exit code; tail = summary survives truncation);
   append an orchestrator triage note to the evidence file; `dw story
   status ... done`; update the status-doc row + Where-we-are + the
   project README `**Last updated:**` line (line ~320, one long
   line); close commit carries the evidence file. NOTE: `dw contract
   --tests-capture` REFUSES a nonzero-exit capture, and this suite
   lawfully exits 1 on the inherited baseline — use the plain
   contract and certify Tests-ran on the output you read.
10. **Push/merge**: ONLY when the owner says so; then
    `gh pr create` + `gh pr merge --merge`, no CI watching.

## 4. Gotchas that cost time (all learned the hard way)

- **Terra misfire**: a Terra worker once refused a brief because the
  auto-loaded claude-api reference workflow misread "provider-neutral
  adapter" as vendor-SDK work. "Provider" in this repo means
  HoldSpeak's OWN engine seam (llama.cpp/MLX behind
  `kernel/inference_runner.py`). Pre-empt it in briefs; on refusal,
  SendMessage a scope clarification — the resume works.
- **Schema**: additive-only via `db/reconcile.py`; but the
  `kernel_parent_runs.kind` CHECK is baked into stored DDL — new
  parent kinds heal existing DBs only through the kind-drift REBUILD
  in reconcile (proof pattern in `tests/unit/test_reconcile.py`).
  The canonical snapshot regen
  (`tests/fixtures/db_schema_canonical.txt`) uses an effectively
  no-op normalizer regex — regenerate so ONLY your lines change
  (see `test_db.py`; memory: `reference_schema_snapshot_regen.md`).
- **Python pin**: bare `uv sync`/`uv run` may grab 3.14 — always
  `--python 3.13.11`. Results from 3.14 get discarded.
- **Isolated HOME** for anything kernel/DB-shaped, or the owner's
  real database leaks in (migration-marker integrity errors, v-drift
  cascades).
- **Web bundle**: gitignored; lives at `holdspeak/static/_built`. A
  fresh worktree needs `npm ci && npm run build` in `web/` before
  full sweeps, else ~28 phantom web failures.
- **One-path guards** (`test_one_path_spine/provenance/cardinality/
  context/one_dial`) share rigs across surfaces — touching one leg
  can break others; run ALL legs. A guard failure is often a REAL
  product find (they caught a SERVICE authority-basis overwrite and
  a resolution leak) — never weaken a guard to pass it.
- **Counsel/audit output is input.** Twice an audit's "fix" would
  have shipped edge-case ceremony; twice sweeps caught real bugs the
  audits missed. Both directions prove the same rule: you triage,
  you decide.

## 5. What the phase's "done" means (Story 14's bar)

Every production inference call site in one versioned capability;
every execution behind a frozen route plan; ordered fallback with
receipts explaining every leg; legacy pointers migrated one-way with
no competing authority; adding a model changes zero assignments;
Model Library + Assignments glass at 1440/393/200% with
keyboard/reduced-motion proof; HTTP/MCP parity; and the
`architecture-contract.md` kill criteria each backed by
production-path evidence in Story 14's write-once ledger. On a tired
Tuesday the owner clicks whatever is in front of them and the glass
never lies.
