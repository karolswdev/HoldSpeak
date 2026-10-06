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
| Web interface | [UX canon](docs/internal/UX-CANON.md) and [frontend architecture](docs/internal/ARCHITECTURE_WEB_FRONTEND.md) |
| Runtime or meeting session | [Backend architecture](docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md) |
| Documentation | [Writing standard](docs/internal/DOCS_STYLE.md) and [terminology register](docs/internal/DOCS_TERMINOLOGY.md) |
| API or MCP contract | [API surface](docs/API_SURFACE.md) and [MCP sidecar](docs/MCP_SIDECAR.md) |

## Work flow

1. Branch from `main`.
2. Commit with `git commit`. There is no commit gate.
3. Open a pull request. Put the real test results in the description.
4. A reviewer gives one final review round when the work is finished. You
   fix the findings. There is at most one re-check.
5. Merge. Do not push to `main` directly.

[CLAUDE.md](CLAUDE.md) holds the full working agreements.

## Test your change

Run the tests that cover your change. Always use an isolated home, so the
tests never touch your real database.

```sh
HOME_REAL=$HOME; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q -n auto --dist worksteal -m "not slow" tests/unit tests/integration tests/critical tests/web tests/mcp tests/uat; rm -rf $H
```

This is the FAST run. It has no browser tests. To run one file, put its path
in place of the directories.

- If you change `web/src/` or `holdspeak/`, run the browser tests that cover
  the diff: `eval "$(uv run python scripts/glass_for.py --quiet)"`. Run
  `uv run python scripts/glass_for.py` to see which files it picks.
- Nightly CI runs the full suite. It excludes `tests/e2e/test_metal.py`,
  which needs a microphone, a model and desktop hardware.
- A type check does not validate runtime behavior.

For changes under `web/`, run the full web contract from that directory:

```sh
npm ci
npm run check
```

It checks tokens, architecture, types, tests, the production build and the
bundle limits. Some Python integration tests need the built bundle.

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
