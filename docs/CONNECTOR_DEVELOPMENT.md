# Connector Development

> A connector is anything that produces local activity records,
> annotations, candidates, or planned commands for HoldSpeak.
> Phase 9 shipped the first three first-party connectors; phase 11
> generalises the contract so anyone can author a local one.

This guide documents the contract you need to satisfy and the
testing surface you get for free.

---

## TL;DR

A connector is a Python module that:

1. Declares a `ConnectorManifest` (validated at import time via
   `holdspeak.connector_sdk.validate_manifest`).
2. Produces a payload through
   `holdspeak.activity_connector_preview.dry_run()` that
   matches the canonical shape (commands /
   proposed_annotations / proposed_candidates / warnings /
   permission_notes / truncated).
3. Has at least one fixture under `tests/fixtures/connectors/`
   to lock its dry-run shape.

Look at `holdspeak/connector_packs/github_cli.py` for the
canonical example.

---

## Connector lifecycle

```
   ┌─────────────┐    ┌───────────┐    ┌────────────┐    ┌────────────┐
   │   manifest  │ →  │  preview  │ →  │   enrich   │ →  │   clear    │
   │  (declare)  │    │ (dry-run) │    │  (mutate)  │    │ (per-cap)  │
   └─────────────┘    └───────────┘    └────────────┘    └────────────┘
        always         always           gated by enabled  user-initiated
```

- **Manifest** declares what the connector is, what it can
  produce, and what permissions it needs. Always loaded; static.
- **Preview** is a mutation-free dry run. Always available
  regardless of `enabled`. Surfaces planned commands +
  proposed-output rows + warnings + permission notes.
- **Enrich** is the mutating step. The runtime refuses to call
  it unless the connector's persisted state has
  `enabled=true`. The connector itself does not own
  enablement.
- **Clear** removes the rows the connector authored, scoped by
  `source_connector_id = self.manifest.id`. One method per
  capability (annotations / candidates).

---

## Manifest reference

Full schema lives in `holdspeak/connector_sdk.py`. Required
fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | `^[a-z][a-z0-9_]{0,31}$`. Persisted as `source_connector_id`. |
| `label` | string | Human-readable name shown on `/activity`. |
| `version` | string | Semver-ish: `MAJOR.MINOR.PATCH` (with optional `-pre.N`). |
| `kind` | string | One of `KNOWN_KINDS`: `cli_enrichment`, `candidate_inference`, `extension_events`, `history_import`. |
| `capabilities` | list[string] | Subset of `KNOWN_CAPABILITIES`: `records`, `annotations`, `candidates`, `commands`. Cannot be empty. |

Optional:

| Field | Type | Notes |
|---|---|---|
| `description` | string | One-line explainer. |
| `requires_cli` | string\|null | If your connector shells out, name the binary here. *Required when `kind=cli_enrichment`.* |
| `requires_network` | bool | If true, you must declare at least one network permission (see below). |
| `permissions` | list[string] | See "Permission model". |
| `source_boundary` | string | Where data comes from in plain English. |
| `dry_run` | bool | Always `true` in practice — connectors must support dry-run. |

### Validation

```python
from holdspeak.connector_sdk import validate_manifest

MANIFEST = validate_manifest({
    "id": "my_connector",
    "label": "My Connector",
    "version": "0.1.0",
    "kind": "cli_enrichment",
    "capabilities": ["annotations", "commands"],
    "requires_cli": "mycli",
    "requires_network": True,
    "permissions": [
        "read:activity_records",
        "write:activity_annotations",
        "shell:exec",
        "network:outbound",
    ],
})
```

`validate_manifest` collects **every problem** before raising,
so authors fix all issues in one pass. Each problem is a
`ManifestError(field, code, message)` with a stable `code`
(`id_format`, `version_format`, `unknown_kind`,
`network_permission_required`, etc) you can switch on.

---

## Permission model

Recognised permissions (from `holdspeak.connector_sdk.KNOWN_PERMISSIONS`):

| Permission | Means |
|---|---|
| `read:activity_records` | Connector reads the activity ledger. |
| `write:activity_records` | Connector writes new activity_records rows (e.g. extension events). |
| `write:activity_annotations` | Connector writes activity_annotations rows. |
| `write:activity_meeting_candidates` | Connector writes meeting candidates. |
| `shell:exec` | Connector invokes a local CLI subprocess. |
| `fs:read` | Connector reads files outside HoldSpeak's own data dir. |
| `loopback:http` | Connector accepts loopback POSTs (e.g. browser extension). |
| `network:outbound` | Connector opens an outbound socket — high-trust. |

Network rule: if your manifest declares `requires_network: true`,
you must include at least one of `loopback:http` or
`network:outbound` in `permissions`. Validation fails with
`network_permission_required` otherwise.

---

## Dry-run output shape

`holdspeak.activity_connector_preview.dry_run(db, connector_id, *, limit)`
returns a `ConnectorDryRunResult`. Its `to_payload()` returns
exactly this shape:

```python
{
    "connector_id": "my_connector",
    "kind": "cli_enrichment",
    "capabilities": ["annotations", "commands"],
    "enabled": False,
    "cli_required": "mycli",
    "cli_available": True,            # null when requires_cli=None
    "commands": [                     # only when "commands" in capabilities
        {"command": ["mycli", "...", "..."], ...},
    ],
    "proposed_annotations": [         # only when "annotations" in capabilities
        {"annotation_type": "...", "title": "...", "activity_record_id": 1},
    ],
    "proposed_candidates": [          # only when "candidates" in capabilities
        {"title": "...", "starts_at": "...", "meeting_url": "..."},
    ],
    "warnings": ["..."],
    "permission_notes": ["..."],
    "truncated": False,
}
```

Section caps: each list is capped at
`PAYLOAD_SECTION_CAP = 100`. Exceeding the cap sets
`truncated: true`.

`permission_notes` is the right place to surface "the
connector is currently disabled" / "the CLI binary isn't on
PATH" — the runtime + UI render them as advisory blocks above
the planned commands.

---

## Privacy checklist

Before merging a connector:

- [ ] Does the manifest's `permissions` list match the
      narrowest capabilities the connector actually needs? No
      "just in case" `network:outbound` declarations.
- [ ] Does `source_boundary` describe in plain English where
      data comes from and where it doesn't?
- [ ] If your connector parses external input (extension
      events, file content), do you reject every field name
      that implies sensitive content (cookies, body, headers,
      form data, screenshots, selection text)? See
      `holdspeak/activity_extension.py:FORBIDDEN_FIELDS` for
      the canonical list — re-export and *extend* it for any
      new sensitive surface.
- [ ] Are non-`http(s)` URLs rejected at the schema layer?
- [ ] Is `requires_network` honest? (Reading a local file is
      not network.)
- [ ] Does your `Enrich` implementation respect the
      `connector.enabled` flag? The runtime gates it but
      defense-in-depth doesn't hurt.
- [ ] Is your `Clear` implementation scoped to
      `source_connector_id == self.manifest.id`?
- [ ] Does dry-run mutate the database? (It must not. The
      fixture harness will catch you.)

---

## Dry-run fixture tutorial

Add a JSON file under `tests/fixtures/connectors/`:

```json
{
  "id": "my-connector-happy-path",
  "connector": "my_connector",
  "limit": 10,
  "activity_records": [
    {
      "url": "https://example.com/things/1",
      "title": "Thing 1",
      "domain": "example.com",
      "entity_type": "my_entity_type",
      "entity_id": "thing-1",
      "last_seen_at": "2026-04-30T10:00:00"
    }
  ],
  "expect": {
    "kind": "cli_enrichment",
    "capabilities": ["annotations"],
    "command_count": 1,
    "annotation_count": 1,
    "candidate_count": 0,
    "permission_notes_contain": ["disabled"],
    "warnings_contain": [],
    "truncated": false
  }
}
```

Run the harness:

```
$ uv run pytest tests/unit/test_connector_fixture_harness.py -k my-connector
```

Fixtures are discovered automatically. No test code to write.
On failure you get a readable diff naming every drifted field
+ a payload summary you can paste back as the new
expectation.

Every `expect` field is optional. Lock down only what you care
about.

---

## Built-in connector packs

The first-party packs in `holdspeak/connector_packs/` are the
canonical reference implementations:

| Pack | Source | Manifest | Fixture |
|---|---|---|---|
| Firefox companion | [firefox_ext.py](../holdspeak/connector_packs/firefox_ext.py) | `firefox_ext.MANIFEST` | none — coverage via [`tests/unit/test_activity_extension.py`](../tests/unit/test_activity_extension.py) parser-contract tests |
| GitHub CLI | [github_cli.py](../holdspeak/connector_packs/github_cli.py) | `github_cli.MANIFEST` | [`gh-happy-path.json`](../tests/fixtures/connectors/gh-happy-path.json), [`gh-empty-ledger.json`](../tests/fixtures/connectors/gh-empty-ledger.json) |
| Jira CLI | [jira_cli.py](../holdspeak/connector_packs/jira_cli.py) | `jira_cli.MANIFEST` | [`jira-happy-path.json`](../tests/fixtures/connectors/jira-happy-path.json), [`jira-empty-ledger.json`](../tests/fixtures/connectors/jira-empty-ledger.json) |
| Calendar candidates | [activity_candidates.py](../holdspeak/activity_candidates.py) | (built-in via the descriptor in [`activity_connectors.py`](../holdspeak/activity_connectors.py)) | [`calendar-happy-path.json`](../tests/fixtures/connectors/calendar-happy-path.json), [`calendar-empty-ledger.json`](../tests/fixtures/connectors/calendar-empty-ledger.json) |

The github_cli + jira_cli packs are the cleanest references
because they ship a read-only command allowlist + a policy
validator (`is_command_allowed`) alongside the manifest. Read
those before building your own.

---

## Minimal example

```python
# holdspeak/connector_packs/example.py
from ..connector_sdk import ConnectorManifest, validate_manifest

MANIFEST: ConnectorManifest = validate_manifest({
    "id": "example",
    "label": "Example Connector",
    "version": "0.1.0",
    "kind": "candidate_inference",
    "capabilities": ["candidates"],
    "permissions": ["read:activity_records",
                    "write:activity_meeting_candidates"],
    "source_boundary": "Reads activity_records; writes "
                       "activity_meeting_candidates only.",
})

def preview(db, *, limit: int = 25):
    """Return the dry-run payload shape for this connector.

    Mutation-free: only reads from db, never writes.
    """
    records = db.list_activity_records(limit=limit)
    return {
        "connector_id": MANIFEST.id,
        "kind": MANIFEST.kind,
        "capabilities": list(MANIFEST.capabilities),
        "enabled": False,
        "cli_required": None,
        "cli_available": None,
        "commands": [],
        "proposed_annotations": [],
        "proposed_candidates": [
            {"title": r.title, "starts_at": None, "meeting_url": r.url}
            for r in records[:limit]
        ],
        "warnings": [] if records else ["No activity to convert."],
        "permission_notes": [],
        "truncated": False,
    }
```

That's a complete connector. Drop a fixture and you're done.

---

## Out of scope

This story does not cover:

- A remote publishing workflow.
- A marketplace.
- A plugin loader for third-party packages from the internet.

Phase 11 ships the *contract* and the *first-party packs*. Any
external distribution mechanism is a separate phase, not on
the current roadmap.
