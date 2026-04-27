# HS-8-08 Evidence - Assisted Activity Enrichment Sources

## Shipped Result

HS-8-08 scopes the assisted enrichment layer that can extend the Local
Attention Ledger after Phase 8 without weakening its local-first privacy
contract.

The design artifact is:

- `docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md`

It defines:

- connector contract and registry expectations
- activity annotation result shape
- meeting candidate result shape
- proposed local tables for connector state, annotations, and candidates
- Calendar/Outlook meeting-candidate flow from existing local activity
- Firefox companion extension architecture and loopback event endpoint
- `gh`/`jira` CLI enrichment command boundaries
- permission and privacy matrix
- follow-up implementation story sequence

## Connector Boundaries

Base browser-history ingestion remains default-on and local. Assisted
connectors are individually visible and disabled until enabled by the
user.

Connectors may add local records, annotations, or meeting candidates.
They may not read cookies, credentials, form contents, page bodies,
private browsing windows, or hidden cloud sources. CLI connectors may
trigger network through already-authenticated local tools only after
explicit enablement, preview, timeouts, and output caps.

Meeting candidates require visible user action before recording is armed
or started. Microsoft Graph remains out of scope for this story.

## Follow-Up Stories Identified

- `HS-9-01`: Activity enrichment connector registry and annotation persistence.
- `HS-9-02`: Calendar/Outlook meeting candidates from existing local activity records.
- `HS-9-03`: Firefox companion extension event endpoint and local installation guide.
- `HS-9-04`: `gh` CLI enrichment preview and annotations for GitHub PRs/issues.
- `HS-9-05`: `jira` CLI enrichment preview and annotations for Jira tickets.
- `HS-9-06`: Assisted enrichment privacy controls, deletion, and phase exit.

## Verification

```text
uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_history.py tests/unit/test_activity_mapping.py
17 passed in 0.40s
```

```text
git diff --check
```
