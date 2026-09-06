# Contributing to HoldSpeak

Use this guide to prepare, verify, and submit a change.
For installation without development tools, read [Getting Started](docs/GETTING_STARTED.md).

## Set up a checkout

Install Python 3.10 or later, `uv`, and Node.js 22.12 or later first.
Install the platform audio dependencies listed in Getting Started.

```sh
git clone https://github.com/karolswdev/HoldSpeak.git
cd HoldSpeak
uv venv
source .venv/bin/activate
uv pip install -e '.[dev]'
git config core.hooksPath .githooks
```

The build hook installs Web dependencies and builds the bundled app.
Use the `linux` extra on Linux when you need transcription.
Install other runtime extras only for the capabilities you develop.
See [Models](docs/MODELS.md) for model runtime requirements.

## Read the applicable contract

| Change | Reference |
| --- | --- |
| Product behavior | [Constitution](docs/internal/CONSTITUTION.md) and the feature guide |
| Web interface | [UX canon](docs/internal/UX-CANON.md) and [frontend architecture](docs/internal/ARCHITECTURE_WEB_FRONTEND.md) |
| Runtime or meeting session | [Backend architecture](docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md) |
| Documentation | [Writing standard](docs/internal/DOCS_STYLE.md) and [terminology register](docs/internal/DOCS_TERMINOLOGY.md) |
| API or MCP contract | [API surface](docs/API_SURFACE.md) and [MCP sidecar](docs/MCP_SIDECAR.md) |

## Update documentation

New and revised prose follows the ASD-STE100 reference and the repository's product terminology.
The writing standard defines page structure, language review, and the limits of automated checks.

1. Verify each changed procedure against the current control, command, or service contract.
2. Update the relevant guide in the same change as the behavior.
3. Add new guides to [the documentation index](docs/README.md).
4. Review language and technical terms against the writing standard.
5. Run the applicable documentation checks.
6. Record the results and any remaining uncertainty in the PR.

For documentation changes, run from the repository root:

```sh
python scripts/check_docs.py
python -m unittest discover -s tests/unit -p test_docs_navigation.py
python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short tests/unit/test_doc_drift_guard.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_api_surface.py
```

The proof driver isolates Python home/path resolution before it imports pytest.
It avoids the owner's application database without changing the shell's home variable.
It is suitable for the listed Python documentation checks.
It does not isolate arbitrary subprocesses for every possible test suite.

The navigation checker verifies local links and heading targets in public Markdown.
The drift guards compare documented counts, product terms, and generated contracts with their sources.
These checks do not certify STE vocabulary or meaning.
Review those manually with the official standard and the terminology register.

After changing HTTP routes or MCP tools, regenerate the relevant reference:

```sh
python scripts/gen_api_surface.py
python scripts/gen_mcp_sidecar_doc.py
```

Run generators and application tests in an isolated development or CI environment.
The existing generator fixtures use temporary databases for their inventories.
Do not use an owner's live database as test data.

## Test implementation changes

Run the tests that exercise the changed behavior and its integration boundaries.
Run the complete relevant suite for broad runtime changes and release validation.
Use the isolated CI jobs or a disposable development environment for tests that start product processes.

```sh
python -m pytest -q --ignore=tests/e2e/test_metal.py
ruff check holdspeak/
```

The excluded test requires microphone, model, and desktop hardware.
A type check alone does not validate runtime behavior.

For changes under `web/`, run the complete Web contract from that directory:

```sh
npm ci
npm run check
```

The command checks tokens, architecture, types, tests, the production build, and bundle limits.
Some Python integration tests also require that built bundle.
Use the [dogfood protocol](dogfood/PROTOCOL.md) for whole-product or release exercises.

## Commit workflow

Every commit requires a generated contract tied to the staged tree.
Read [the contract rules](pm/roadmap/PMO-CONTRACT.md) before certifying the change.

1. Stage the intended files with `git add`.
2. Generate the contract.

   ```sh
   .githooks/dw contract new
   ```

3. Read `.tmp/CONTRACT.md`.
4. Mark each box only after you verify its statement.
5. Commit normally with `git commit`.

The hooks validate the staged facts and archive the successful contract.
If you change the staged files, regenerate the contract with `--force` before committing.
A hand-written contract or `--no-verify` bypass is not an accepted workflow.

For roadmap work, update the associated tracking and evidence in the same commit.
For other work, include the actual validation results in the commit or PR description.
The [repository working agreements](CLAUDE.md) describe the complete process.

## Report a problem

Use the [issue tracker](https://github.com/karolswdev/HoldSpeak/issues) for reproducible product problems.
Include the version, relevant setup, steps, expected result, and observed result.
Remove secrets and private source content before attaching logs.
For a security issue, read [Security & Privacy](docs/SECURITY.md) first.

## See also

- [Documentation index](docs/README.md): user guides and technical references.
- [Writing standard](docs/internal/DOCS_STYLE.md): controlled English and source review.
- [Architecture](docs/ARCHITECTURE.md): runtime and data flow.
