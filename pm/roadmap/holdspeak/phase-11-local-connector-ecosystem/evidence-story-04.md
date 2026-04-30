# HS-11-04 evidence — GitHub CLI connector pack

## Files shipped

- `holdspeak/connector_packs/github_cli.py` (new) — exports a
  validated `MANIFEST`, an `ALLOWED_SUBCOMMANDS` frozenset, and
  an `is_command_allowed(command)` validator. Plus
  `DEFAULT_TIMEOUT_SECONDS`, `DEFAULT_MAX_BYTES`,
  `DEFAULT_LIMIT` for runtime tuning.

## Manifest declaration

```
id:          gh
kind:        cli_enrichment
capabilities: ["annotations", "commands"]
requires_cli: gh
requires_network: true
permissions: ["read:activity_records", "write:activity_annotations",
              "shell:exec", "network:outbound"]
source_boundary: "Local `gh` CLI subprocess. Only commands listed in
                  ALLOWED_SUBCOMMANDS are permitted; …"
dry_run:     true
```

## Read-only command allowlist

```python
ALLOWED_SUBCOMMANDS = frozenset({
    ("pr", "view"),
    ("issue", "view"),
})
```

`is_command_allowed(command)` checks the second + third tokens
against this set. Mutating verbs are rejected:

| Command | allowed |
|---|---|
| `gh pr view 1 --repo o/r` | ✅ |
| `gh issue view 12 --repo o/r` | ✅ |
| `gh pr edit 1 --repo o/r` | ❌ |
| `gh pr merge 1 --repo o/r` | ❌ |
| `gh pr close 1` | ❌ |
| `gh issue close 1` | ❌ |
| `gh issue create --title x` | ❌ |
| `gh auth login` | ❌ |
| `gh repo delete o/r` | ❌ |

## How acceptance criteria are met

- **Connector manifest marks the connector as network-capable
  through local CLI.** `requires_network: true` +
  `requires_cli: "gh"` + permissions include `shell:exec` and
  `network:outbound`. The validator
  (`holdspeak/connector_sdk.py:validate_manifest`) demands at
  least one network permission whenever `requires_network` is
  true.
- **Only read-only `gh` commands are allowed.** Locked down by
  the `ALLOWED_SUBCOMMANDS` frozenset + `is_command_allowed`
  + 12 parametrized policy tests covering every mutating verb
  identified above.
- **Fixture tests produce deterministic annotations.** The
  HS-11-02 fixture harness with `gh-happy-path.json` runs the
  shared `dry_run()` path and asserts 2 records → 2 commands
  → 2 proposed annotations, deterministically.
- **Command failures surface as connector run errors.** The
  underlying `activity_github.run_github_cli_enrichment` (HS-9-04)
  catches subprocess failures and persists `last_error` via
  `db.record_activity_enrichment_run`; the manifest layer just
  describes that contract, doesn't replace it.

## Tests

```
$ uv run pytest tests/unit/test_connector_packs.py -q -k github
…
13 passed in 0.03s
```
