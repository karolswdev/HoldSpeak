# HS-11-05 evidence — Jira CLI connector pack

## Files shipped

- `holdspeak/connector_packs/jira_cli.py` (new) — exports a
  validated `MANIFEST`, an `ALLOWED_SUBCOMMANDS` frozenset, and
  an `is_command_allowed(command)` validator. Same shape as the
  github_cli pack.

## Manifest declaration

```
id:          jira
kind:        cli_enrichment
capabilities: ["annotations", "commands"]
requires_cli: jira
requires_network: true
permissions: ["read:activity_records", "write:activity_annotations",
              "shell:exec", "network:outbound"]
source_boundary: "Local `jira` CLI subprocess. Only commands listed
                  in ALLOWED_SUBCOMMANDS are permitted; …"
dry_run:     true
```

## Read-only command allowlist

```python
ALLOWED_SUBCOMMANDS = frozenset({
    ("issue", "view"),
})
```

| Command | allowed |
|---|---|
| `jira issue view HS-101 --plain` | ✅ |
| `jira issue view HS-101` | ✅ |
| `jira issue create --summary x` | ❌ |
| `jira issue assign HS-101 user` | ❌ |
| `jira issue transition HS-101 Done` | ❌ |
| `jira issue delete HS-101` | ❌ |
| `jira auth login` | ❌ |

## How acceptance criteria are met

Same shape as HS-11-04:

- **Connector manifest marks the connector as network-capable
  through local CLI.** `requires_network: true`,
  `requires_cli: "jira"`, network permission declared.
- **Only read-only `jira` commands are allowed.** Locked down
  by `ALLOWED_SUBCOMMANDS` + 8 parametrized policy tests
  covering every mutating verb identified above.
- **Fixture tests produce deterministic annotations.** The
  HS-11-02 fixture harness with `jira-happy-path.json` runs
  through `dry_run()` and asserts 2 tickets → 2 commands → 2
  annotations.
- **Command failures surface as connector run errors.**
  Inherited from `activity_jira.run_jira_cli_enrichment`
  (HS-9-05).

## Tests

```
$ uv run pytest tests/unit/test_connector_packs.py -q -k jira
…
11 passed in 0.03s
```
