# Contributing to HoldSpeak

Use this guide to prepare, verify, and submit a change. For an installation
without development tools, read [Getting Started](docs/GETTING_STARTED.md).

## Set up a checkout

Install Python 3.10 or later, `uv`, and Node.js 22.12 or later. Install the
platform audio dependencies listed in Getting Started.

```sh
git clone https://github.com/karolswdev/HoldSpeak.git
cd HoldSpeak
uv venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

The build hook installs the web dependencies and builds the bundled app. On
Linux, add the `linux` extra to get transcription. Add other extras only for
the capabilities you work on. See [Models](docs/MODELS.md).

## Read the contract for your change

| Change | Read |
| --- | --- |
| Product behavior | [Constitution](docs/internal/CONSTITUTION.md) and the feature guide |
| Web interface | [Design author map](web/README.md#design-author-map), [UX canon](docs/internal/UX-CANON.md), and [frontend architecture](docs/internal/ARCHITECTURE_WEB_FRONTEND.md) |
| Runtime or meeting session | [Backend architecture](docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md) |
| Documentation | [Writing standard](docs/internal/DOCS_STYLE.md) and [terminology register](docs/internal/DOCS_TERMINOLOGY.md) |
| API or MCP contract | [API surface](docs/API_SURFACE.md) and [MCP sidecar](docs/MCP_SIDECAR.md) |

## Work flow

1. Branch from `main` in an isolated worktree.
2. Implement a small change and run `scripts/quick_check.sh` under the test
   lock with an isolated home. Read the relevant desktop and narrow shots.
3. Commit with explicit paths. Open a pull request with the real results.
4. Merge on the green required check; do not push to `main` directly.
5. Redeploy main and update `pm/STATUS.md`. The full tape and Astra's review
   run after merge. Fix findings forward; security or data-loss findings
   require the exception defined in CLAUDE.md.

The owner judges appearance live. Owner aesthetic acceptance is distinct
from the technical merge check; there is no extra owner approval gate.

[CLAUDE.md](CLAUDE.md) holds the full working agreements.

## Test your change

Run the tests that cover your change. Always use an isolated home, so the
tests never touch your real database.

Before merge, use the required quick check:

```sh
scripts/quick_check.sh
```

It runs the build, related web tests, affected Python/browser files, the desk
sweep and repository guards under the one-run-at-a-time lock and an isolated
home. For an additional focused run, use `uv run python scripts/test_lock.py
-- <command>` with an isolated `HOME`, the real Playwright browser cache and
`-n 8` for pytest. See [CLAUDE.md](CLAUDE.md#test-commands) for the exact
commands and isolation switches. Never run `tests/e2e/test_metal.py` as an
agent. Type checking alone does not validate runtime behavior.

The main watcher runs the full tape after merge. A new failure is traced and
fixed forward. Nightly CI also runs the full suite; wider local suites are
not another pre-merge gate.

Use the [dogfood protocol](dogfood/PROTOCOL.md) for whole-product or release
checks. Run lint with `ruff check holdspeak/`.

## Update documentation

Write in ASD-STE100 Simplified Technical English and use the product
terminology. The writing standard defines the page structure and the limits
of the automated checks.

1. Check each changed procedure against the current command, control or route.
2. Change the guide in the same pull request as the behavior.
3. Add a new guide to the [documentation index](docs/README.md).
4. Run the documentation checks from the repository root:

```sh
python scripts/check_docs.py
python -m unittest discover -s tests/unit -p test_docs_navigation.py
python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short tests/unit/test_doc_drift_guard.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_api_surface.py
```

The proof driver isolates the Python home before it imports pytest. The
navigation check verifies local links and heading targets. The drift guards
compare documented counts, terms and generated contracts with their sources.
These checks do not certify STE vocabulary. Review it by hand.

After you change HTTP routes or MCP tools, regenerate the references:

```sh
python scripts/gen_api_surface.py
python scripts/gen_mcp_sidecar_doc.py
```

`scripts/gen_docs.sh` runs every generator. Do not edit generated files by
hand. Never use a live database as test data.

## Report a problem

Use the [issue tracker](https://github.com/karolswdev/HoldSpeak/issues) for a
product problem you can reproduce. Include the version, your setup, the
steps, the expected result and the observed result. Remove secrets and
private content from logs. For a security issue, read
[Security & Privacy](docs/SECURITY.md) first.

## See also

- [Documentation index](docs/README.md)
- [Writing standard](docs/internal/DOCS_STYLE.md)
- [Architecture](docs/ARCHITECTURE.md)
