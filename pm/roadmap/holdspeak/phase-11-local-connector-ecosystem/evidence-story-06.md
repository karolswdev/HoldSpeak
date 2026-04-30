# HS-11-06 evidence — Connector developer documentation

## File shipped

- `docs/CONNECTOR_DEVELOPMENT.md` (new) — the connector
  authoring guide. Sections:
  - **TL;DR** — three-step starter.
  - **Connector lifecycle** — manifest → preview → enrich →
    clear, with each step's contract.
  - **Manifest reference** — every required + optional field
    documented as a table.
  - **Permission model reference** — every permission string
    + its meaning, plus the `requires_network` rule.
  - **Dry-run output shape** — the canonical payload shape
    matching `ConnectorDryRunResult.to_payload()`, with notes
    on the per-section `PAYLOAD_SECTION_CAP`.
  - **Privacy checklist** — eight explicit, testable items.
  - **Dry-run fixture tutorial** — runnable example. Drop a
    JSON file under `tests/fixtures/connectors/`, run `pytest`,
    fixture is auto-discovered by the HS-11-02 harness.
  - **Built-in connector packs** — table linking every pack
    module + manifest + fixture.
  - **Minimal example** — complete `connector_packs/example.py`
    with manifest + preview function in ~25 lines.
  - **Out of scope** — explicitly disclaims a remote publishing
    workflow, marketplace, third-party plugin loader.

## How acceptance criteria are met

- **Docs explain connector lifecycle and output types.** The
  Lifecycle section diagrams the four-step flow and notes
  which steps are gated by `enabled`. The Dry-run Output
  Shape section enumerates every field of the canonical
  payload.
- **Docs include a runnable fixture-based example.** The
  Fixture Tutorial section gives a concrete JSON fixture and
  the exact `pytest` command that runs it. The fixture
  discovery is automatic — readers don't need to register the
  test anywhere.
- **Privacy checklist is explicit and testable.** Eight
  items, each phrased as a yes/no question with a concrete
  enforcement point (manifest field, `FORBIDDEN_FIELDS`
  re-export, scheme allowlist, `enabled` gate, scoped
  `Clear`, mutation-free dry-run). The fixture harness from
  HS-11-02 mechanically enforces the no-mutation item; the
  others map to manifest validation rules already covered by
  `validate_manifest`.
- **Built-in connectors link to their manifests and fixtures.**
  The Built-in Packs table links each pack module + its
  manifest export + every fixture file. Calendar candidates
  (descriptor-only, no pack module yet) is also listed with a
  link to its descriptor source.

## Tests

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1305 passed, 13 skipped in 29.56s
```

Documentation-only change; the suite is included as a
regression check.
