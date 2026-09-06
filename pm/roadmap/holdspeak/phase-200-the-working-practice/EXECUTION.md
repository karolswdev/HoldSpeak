# Phase 200 execution brief

**Start here when implementation is authorized.**
The owner has requested the roadmap and its direction.
Use current session authority for subsequent work.
Do not add a new approval ritual because a step appears in this plan.

## Orient

1. Read root CLAUDE.md and the current session instructions.
2. Inspect Git status and worktrees. Preserve unrelated work.
3. Refresh current main and inspect changes since the planning baseline.
4. Read this phase's README, status, baseline, contracts, and acceptance.
5. Read the story and its dependencies before changing code.
6. Identify the actual running process and database before a live action.

The planning baseline is main `519afd4f`.
An older checkout contains unrelated Interview edits.
Never copy runtime files across checkouts to simulate integration.
Never use a shared stash to clear another session's work.

## First implementation task

Start **HS-200-01**, currently the only ready story.
Produce a current integration and runtime map.
Record what is implemented, what is actually running, and what remains unproved.
Choose the pilot Project and source scope when available.
Map current CI failures to their actual repair stories.

The older Delivery Workbench queue can still identify historical in-progress work.
The project's Current phase pointer and this phase's dependency graph establish Phase 200's chosen sequence.
Do not falsely close historical stories to change a queue result.
Reconcile their disposition in 01.

## Before implementing a story

Record one disposition: reuse and prove, integrate, fix a demonstrated gap, implement a missing capability, or defer.
Name the current code and the actual failed scenario.
Use the existing domain owner and transport pattern.
Design concurrency-sensitive state before implementing it.
Review the state machine, transaction boundaries, authority, failure windows, and late-result behavior.

New UI controls use the shared library and the approved daily-flow design.
Keep the primary action visible in partial, failed, and interrupted states.
Check voice, keyboard, focus, and both viewport sizes.
Retain the Desk's existing visual language.

## Verification commands

The commands below are execution recipes.
They are not a claim that future test files already exist or have passed.
Run commands from the selected implementation worktree.

For documentation changes:

```sh
python3 scripts/check_docs.py pm/roadmap/holdspeak/phase-200-the-working-practice/*.md
.githooks/dw check holdspeak
git diff --check
```

The baseline has five known structural issues.
Compare exact issue identities and require zero new issues from a planning change.
Do not fabricate old evidence or summaries.

For scoped Python product verification, use the existing isolated proof driver when its isolation covers the tested path:

```sh
uv run python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short tests/unit/test_interview_service.py tests/unit/test_interview_tool_execution.py
```

HS-200-03 must verify database and configuration isolation for the integrated critical journeys.
Use explicit temporary stores for services that do not honor the proof driver's path isolation.
Never run a product suite against the owner database.
Do not change shell HOME or other common system variables to repurpose the environment.

Planned-test naming rule:

- A story naming suite `phase200_runtime_identity` creates or extends the relevant `test_phase200_runtime_identity.py` module.
- Place state tests under `tests/unit`, real-service flows under `tests/integration`, and browser/physical orchestration under `tests/e2e`.
- Use only the levels needed by the changed behavior.
- If existing tests cover the requirement, cite and extend them instead of creating mirrored tests.
- Put exact commands and actual output in the story evidence.

Example command after those planned files exist:

```sh
uv run python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short tests/unit/test_phase200_runtime_identity.py tests/integration/test_phase200_runtime_identity.py
```

For Web changes:

```sh
npm --prefix web run check
```

Run the relevant production-browser scenario after a fresh build.
Use the real coordinator and services with controlled external adapters for deterministic tests.
Then run the required physical, live-model, worker, or owner leg.
A passing fixture cannot replace those legs.

For release, use the current commands in CLAUDE.md and the release scripts.
First inspect those scripts and their data targets.
Run the required jobs on the exact candidate.
Broaden testing when a new change or unresolved failure justifies it.

## Evidence and story status

Before implementation:

```sh
.githooks/dw story status holdspeak phase-200-the-working-practice story-01-baseline-and-obligation-map in-progress
```

Verify CLI argument spelling with the installed command help if its interface differs.
Use Delivery Workbench evidence capture for actual checks.
The owner or physical verdict is recorded separately from automated output.
Only mark a story done when all its acceptance criteria are supported.

One story ships in one scoped PR.
The same shipping change updates the story header, status row, Where we are, project Last updated, and affected public procedure.
Create `evidence-story-NN.md` only at the story's shipping boundary.
Do not create `final-summary.md` before phase exit.

For commits, stage only the intended files and generate the stamped contract.
Verify each box honestly.
Never bypass the hooks or weaken a guard to make the phase look complete.
A planning-only commit has documentation checks and no product completion claim.

## Decisions and escalation

Resolve routine reversible choices using existing authority and evidence.
When a missing answer prevents a specific effect, complete the independent work and present the concrete decision.
An unavailable physical device or live source leaves that proof open.
It does not prevent isolated implementation or documentation.

The roadmap does not select a model for delegated agents or authorize new parallel sessions.
Follow applicable session and repository rules for any delegation.
Record independent design review where the foundation requires it.

## Completion standard

Every report names what changed, what actually ran, the result, and the remaining limitation.
Do not describe configuration as execution, execution as verification, or verification as adoption.
Stop expansion when the current recipe costs more effort than it saves.
Repair the observed cause and measure again.

The first product checkpoint is the two-day Project sequence.
The final checkpoint is the exact packaged release with accepted G0–G5 evidence.
