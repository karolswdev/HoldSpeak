---
name: holdspeak-capability-verifier
description: Use when checking whether a claimed HoldSpeak capability exists, works, or is released. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-capability-verifier

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/internal/philo/data/README.md`
- `docs/CAPABILITIES.md`
- `tests/unit/doc_claims/registry.py`

## Vocabulary and invariants

Code presence, inspected assertions, executed tests, public release and owner observation are separate evidence axes.

## Change path

Inspect the route, service, schema and test assertions; update the relevant metadata row. Preserve unknowns; never promote status because a file exists.

Update `docs/CAPABILITIES.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_phase200_doc_claims.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_phase200_doc_claims.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Walk a case (the graph rig)

This is the one walk procedure. Other walk instructions link here.
`scripts/graph_walk.py` is the one rig; `docs/internal/philo/graph/atlas.json`
holds the cases; `docs/generated/graph.json` is the join of the passes.

1. **Mint a case.** Add or change it in the atlas (contract:
   `docs/internal/philo/graph/atlas.schema.json`). Set its state through real
   production entry points (`api`, `ui`, `fixture`, `cli` steps). Do not inject
   rows or finished responses and call them producer evidence. Give it one
   `trigger` and an `expected` predicate at a named `observe_at`. Check it with
   `HOME="$(mktemp -d)" uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py`.
2. **Run the rig, one case per invocation, in a fresh HOME:**

   ```sh
   REAL_HOME="$HOME"
   HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$REAL_HOME/Library/Caches/ms-playwright" \
     uv run --extra dev python scripts/graph_walk.py run \
       --atlas docs/internal/philo/graph/atlas.json --case <case id> \
       --brain <muaddib|astra> --viewport <1440|393> --engine <real|replayed|none> \
       --out .tmp/graph-walk/<story>/<run label>
   ```

   Run cases one at a time, with one hub. Read each result before the next.
   Face cases run at 1440 and at 393; protocol cases run once.
3. **Read the observation** at `<out>/<run id>/observation.json`. The predicate
   decides the verdict, not the diff. Check `provenance.db_path` is under the
   temporary HOME, and check `revision` and `dirty`. Read `initial_feedback`
   and `terminal_outcome` separately. `blocked` with its reason is a result.
   Look at `before.png` and `after.png` yourself.
4. **Give every run its own output directory.** Use `--out` under `.tmp/` or
   the pass's own `observations/<brain>/` directory. Never write over tracked
   shots, and never edit an observation by hand.
5. **Never use a blanket restore loop.** If a suite run rewrote tracked files,
   restore only the paths `git status --porcelain` shows as ` M`, by explicit
   path. Never touch `??` paths: a loop over every path truncated untracked
   shots. Workers restore nothing; they report.
6. **Fold the result into the graph.** A sealed pass JSON is not edited
   later. After the council records its resolutions, run
   `python scripts/philo_graph_reference.py` and commit
   `docs/generated/graph.json`; `--check` proves it is current, and
   `uv run --extra dev python scripts/philo_graph_reference.py --census` lists
   new, removed and changed entry points since the passes. The census reads
   HTTP routes from source (the app that `scripts/gen_api_surface.py`
   assembles), not from the committed OpenAPI. Subtype conflicts between the
   passes show as `note:` lines; the join does not choose one.
7. **When you change a route, do these steps in this order:**

   ```bash
   # 1. change the route in source
   uv run --extra dev python scripts/philo_openapi_reference.py        # 2. OpenAPI
   python scripts/philo_graph_reference.py                             # 3. the join
   python scripts/philo_graph_reference.py --check                     # 4. current
   uv run --extra dev python scripts/philo_graph_reference.py --census # 5. census
   ```

   A `stale` line means step 2 is not done. The census then names the new,
   removed or changed edge. Do not edit a sealed pass to agree with the new
   route. Pass evidence describes the route as it was at its recorded
   revision, and that evidence is never rewritten. A new pass or a council
   resolution records the current route.

The isolated-HOME law covers every step: never the owner's data directory,
keychain or microphone, and never a hub on his port.

## Traps

Do not equate packaging Beta with owner-verified usability.

A calibration on the rig's own sample atlas proves nothing about the real
atlas: run actual atlas cases on a real hub. A request sent, a spinner or a
receipt on one branch does not prove the result, or any other branch.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.
