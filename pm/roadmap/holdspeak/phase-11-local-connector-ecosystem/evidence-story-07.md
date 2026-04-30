# HS-11-07 evidence — Connector ecosystem phase exit

## How acceptance criteria are met

### Phase evidence bundle exists

Every shipped story in phase 11 has a matching evidence file
in this directory:

- `evidence-story-01.md` — Connector manifest + SDK shape.
- `evidence-story-02.md` — Fixture-driven dry-run harness.
- `evidence-story-03.md` — Firefox companion connector pack.
- `evidence-story-04.md` — GitHub CLI connector pack.
- `evidence-story-05.md` — Jira CLI connector pack.
- `evidence-story-06.md` — Connector developer documentation.
- `evidence-story-07.md` — *this file* (DoD).

### Connector manifest/fixture tests pass

```
$ uv run pytest \
    tests/unit/test_connector_sdk.py \
    tests/unit/test_connector_fixture_harness.py \
    tests/unit/test_connector_packs.py -q
…
63 passed in 0.24s
```

Breakdown:

- 27 manifest validation tests (`test_connector_sdk.py`).
- 8 fixture-harness tests (`test_connector_fixture_harness.py`),
  including 6 parametrized fixture cases auto-discovered from
  `tests/fixtures/connectors/`.
- 28 connector-pack tests (`test_connector_packs.py`):
  manifest shapes, network-permission rule, firefox parser
  drift, github + jira read-only command policy.

### First-party connector dry-runs pass

The fixture harness covers happy-path + empty-ledger for all
three first-party connectors. Every case asserts both shape
match *and* zero rows added to `activity_annotations` /
`activity_meeting_candidates` during the dry run.

### Full regression passes

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1305 passed, 13 skipped in 29.93s
```

13 skipped are model-fixture-dependent (mock_meeting.wav,
llama_cpp); none are introduced by phase 11.

### Phase status is updated

`current-phase-status.md` story table fully populated; parent
README phase index flips phase 11 to `done` in this same
commit.

## Phase shape — what shipped

Phase 11 took the phase-9 first-party assisted enrichment work
from "ad-hoc Python modules" to a coherent local connector
ecosystem:

- **HS-11-01** ships the contract: `ConnectorManifest` frozen
  dataclass, `validate_manifest()` that collects every problem
  in one pass, four runtime-checkable Protocols (`Discover` /
  `Preview` / `Enrich` / `Clear`), frozen vocabulary sets
  enumerating exactly what the phase-9 connectors actually
  use.
- **HS-11-02** ships the fixture harness:
  `holdspeak/connector_fixtures.py` discovers JSON fixtures
  under `tests/fixtures/connectors/`, runs each through
  `dry_run()` with pre/post row-count snapshots, and renders
  failures as readable diffs.
- **HS-11-03/04/05** ship three first-party packs in
  `holdspeak/connector_packs/`. Firefox re-exports the
  parser's `FORBIDDEN_FIELDS`/`ALLOWED_FIELDS` so manifest-
  vs-parser drift fails at unit-test time. The two CLI packs
  ship explicit read-only command allowlists with 20+
  parametrized policy tests rejecting every mutating verb.
- **HS-11-06** ships the developer-facing guide
  (`docs/CONNECTOR_DEVELOPMENT.md`) covering lifecycle,
  manifest reference, permission model, dry-run output shape,
  privacy checklist, and a runnable fixture-based example.

## What's intentionally out

- A remote publishing workflow.
- Browser-store distribution of the Firefox extension.
- A marketplace for third-party packs.
- A plugin loader pulling code from the internet.
- OAuth-backed cloud connectors.

These remain phase-scope exclusions. The phase-11 contract
gives the *shape* — anyone authoring a local connector pack
follows the contract, drops a fixture, gets the full no-
mutation + manifest-validation test surface for free.

## Phase exit

Phase 11 is **done**. The next active phase is the planning
slot for whatever comes after — phase 11 deliberately does not
prescribe phase 13.
