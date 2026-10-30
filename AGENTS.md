# HoldSpeak — agent development guide

HoldSpeak is an agentic-first, web-based AI operating system. The Desk is
its operating surface; the local hub owns the work. Build complete jobs:
capture context, ask with sources, hand work to an agent, review the result.
Ask: **Can the owner, tired on a Tuesday, do this without our narration?**

## Start here

1. Read [TWO-BRAINS](docs/internal/TWO-BRAINS.md) first each session, then
   [CLAUDE.md, How we work now](CLAUDE.md#how-we-work-now-the-fast-cycle-owner-ruling-2026-10-12).
   Read `pm/STATUS.md` for current work and open defects.
2. The [Constitution](docs/internal/CONSTITUTION.md) and its Seven Tenets
   govern the product. Follow the latest explicit owner ruling where older
   process passages conflict. The 2026-10-12 fast cycle supersedes historical
   premerge reviews, full-suite gates and Delivery Workbench rituals.
3. Read the guide for the paths you will change:

   | Scope | Instructions and source of truth |
   | --- | --- |
   | Interface, styling, interactions | [web/AGENTS.md](web/AGENTS.md), [UX canon](docs/internal/UX-CANON.md), [Design System](docs/internal/DESIGN_SYSTEM.md) |
   | Hub, services, persistence, tools | [holdspeak/AGENTS.md](holdspeak/AGENTS.md), [backend architecture](docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md) |
   | User documentation | [writing standard](docs/internal/DOCS_STYLE.md), [terminology](docs/internal/DOCS_TERMINOLOGY.md), current implementation |
   | Live capability walks | [capability verifier, Walk a case](agent/skills/holdspeak-capability-verifier/SKILL.md#walk-a-case-the-graph-rig) |

   Scoped guides add detail; they do not override the Constitution or the
   current owner workflow. Check paths and anchors: other lanes move main.

## Product priorities

The Seven Tenets come before implementation preferences. Their full owner
wording is in the Constitution. Apply them in every brief and review:

- Do not over-engineer for safety.
- Reduce the complexity that blocks first real use; remember the product's
  early stage.
- Help and accelerate. One clear next action beats many vague interfaces.
- Use ASD-STE100 simple English for product text and user documentation.
- Compose a modular framework in the manner of Amiga Intuition.
- Build Workbench 2.0+ on steroids, with native-grade behavior.
- Serve the first user's jobs: a Senior Software Architect with reports.

The interface is a first-class deliverable. A backend success that leaves
Loading, loses an edit, hides the result or requires an explanation is an
unfinished job. Prefer improving a shared pattern over adding another face.

## Roles and delegation

Astra (`gpt-6-astra`) is the reviewer. Muad'Dib (`claude-opus-5-5`) and his
workers build product code. Astra reviews merged changes and fixes findings
forward through the owning implementation lane; a security or data-loss
finding is the exception for revert. A documentation task may change docs;
it does not grant a new product-code lane. See TWO-BRAINS for dispatch roles.

### Luna lanes

Astra's delegated work uses `gpt-5.6-luna`, reasoning `xhigh`, with lowercase
`snake_case` names. Do not substitute another model unless the owner orders
it for the task. Muad'Dib's worker rules remain in CLAUDE.md and TWO-BRAINS.

A worker brief contains the job/story path, settled design, exact owned
paths, current anchors with a drift warning, other lanes' do-not-touch paths,
focused test files, isolated-state requirements and **hold for SHIP**.
Workers do not stage or commit. Serialize shipping in a shared tree. Reports
that name tests include collection output and the run tail; face reports name
the shots. Read reports and verify the claims that matter; the orchestrator
owns the done call, scope honesty and open-work ledger.

## Worktree and change discipline

- Work in the brief's isolated worktree. Never edit the main checkout at
  `/Users/karol/dev/tools/HoldSpeak` for a lane. Start a new lane from current
  main, for example `git worktree add ../wt-topic -b docs/topic origin/main`
  after fetching it. Reuse an appropriate attached worktree when possible.
- Never run `stash`, `reset`, `checkout --`, `restore`, `clean` or `switch`.
  Read committed content with `git show`; inspect with `status`, `diff`,
  `log` and `show`. Do not repair another lane's files.
- Stage explicit paths. Never `git add -A`. One commit lane per brain.
- Keep a change to one concern. Park retired implementations instead of
  deleting them. Do not add a parallel framework to avoid learning the one
  already here.
- Preserve unrelated work. A surprise diff or failing baseline is evidence
  to investigate and report, not permission to clean the tree.

## Verification that proves the job

Choose the cheapest tier that proves the behavior. Group tests by app,
not by phase. Use existing tests before adding another harness.

| Change or claim | First verification tier |
| --- | --- |
| Domain state, route, permission, lifecycle | Focused hub unit/integration test; inspect the stored result |
| App rendering, press, error and retry | App Vitest with recorded real hub answers; press through to the rendered result |
| Common layout and material | Generic Desk sweep at 1440 and 393; inspect the relevant shots |
| Drag, focus, keys, touch, hover, clipboard, multiple browsers, exact geometry | Scoped real-browser test |
| Physical device or live provider works | An authorized run on that device/provider; fixtures alone cannot prove it |

Every pytest, Vitest, `glass_for` and graph-walk run takes the machine-wide
lock through `scripts/test_lock.py`. Wait for it; never bypass or nest it.
Use `-n 8 --dist worksteal` for focused pytest runs. Never run
`tests/e2e/test_metal.py`. Workers run only the test files in their brief.
The full tape belongs to the main watcher after merge, and nightly CI.

Tests and walks use isolated rigs by default. Never use the owner's real
HOME, DB or Keychain as test state. Disable microphone, calendar, tmux,
agent, phone and external-destination access with the rig's opt-out switches;
the current list is in CLAUDE.md's Test commands. A new machine-state probe
needs its own switch. A separately authorized live walk may use its named
device/provider and target, with the engine mode explicit; keep it outside
the default quick check and retain isolated state. Do not treat a rig's
configured LAN default as permission to use it.

For a new environment use `uv sync --extra dev`; add only the platform
extras you need. Do not use `--all-extras` or strip test dependencies with
plain `uv sync`. For an extra focused Python run from the repository root:

```sh
(
  HS_REAL_HOME="$HOME"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_REAL_HOME/Library/Caches/ms-playwright"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/unit/test_desk_window_service.py
)
```

Replace the final test path with the files that cover your change. For
Vitest use the same isolated environment, `cd web`, then
`uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 <test-file>`.

Before merge, run `scripts/quick_check.sh [base]` (default `origin/main`).
It manages its own lock and isolated HOME: **do not wrap it in another lock**.
It runs the web build, related Vitest, affected Python tests, Desk sweep,
canon guards and repository guards. `QUICK_TESTS` adds explicit Python files;
name any required browser file the affected selector does not discover.
Red means fix first. Type checking, a build or a skipped sweep is not a pass.

Use real producers for fixtures and validators for assertions; do not invent
payloads that bypass the boundary being tested. Cover the failure that risks
owner work: stale replies, failed save, retained input, retry, cancellation
or duplicate dispatch, as relevant. Fix behavior and its existing fences in
the same change. Do not lower guards or grow allowlists to conceal a defect.

Read the output and inspect the changed UI at desktop and phone sizes.
For sweep PNGs, use `DESK_SWEEP_SHOTS=1 scripts/quick_check.sh`; capture is
opt-in, so a plain sweep pass does not prove PNGs were saved. Shots go to
`.tmp/evidence-shots/`; do not set `HOLDSPEAK_EVIDENCE_WRITE=1`.
A source inspection, a fixture pass, a live observation and the owner's
visual acceptance are different claims. State exactly which you have.
For a graph walk, follow the linked skill: one real-atlas case per invocation,
unique output directories, read `observation.json`, verify DB/build provenance
and inspect before/after shots. Report `none`, `replayed` or `real` engine
mode; a replay is not live-provider proof. Live effects need authorization
for that run and target, not an assumption from a local test task.

## Ship and report

Green quick check → explicit-path commit → PR → merge with `gh` when the
lane is authorized to ship. Never push main directly. There is no additional
premerge brain review, full-suite or owner approval gate in the fast cycle.
Update `pm/STATUS.md` at merge; leave `pm/roadmap/` as read-only history.
The main watcher redeploys and runs the full tape; Astra reviews after merge.
Verify that those steps ran before reporting them as complete.

A face gets a canvas in the shared library material before build. The owner
judges appearance live on the deployed Desk. Neither the canvas nor green
technical checks imply aesthetic acceptance. Fix findings forward; a
security/data-loss finding or a broken live desk uses CLAUDE.md's exception.

Report what changed, what actually passed, useful shot paths and what could
not be verified. Keep handovers in `docs/internal/` and open work in
`pm/STATUS.md`. No Delivery Workbench contracts, mandatory evidence dossiers or per-story flips.
Documentation must describe implemented behavior separately from a target
requirement; update affected contracts and guides with behavior changes.

## Checks

When dispatched for a check, change nothing unless the brief requests a fix.
Give evidence as `path:line`, a shot or a DB row; name the failed tenet.
Use this report shape:

```text
VERDICT: RATIFY | RATIFY-WITH-CONDITIONS | DO-NOT-RATIFY
FINDINGS: numbered, with evidence
CONDITIONS: what must change
MISSED: omissions, ranked by cost to the owner
TUESDAY: can the owner do the job?
UNKNOWN: what could not be verified, and why
```

A `claude -p` second opinion invoked by Astra is **advice**, never a
Muad'Dib session's check. Label its origin accurately. Historical review
rituals do not reinstate a gate removed by the current fast cycle.
