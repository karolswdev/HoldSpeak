# HS-28-02 Evidence — `adr_drafter` (real run)

**Date:** 2026-06-01.
**Story:** [story-02-adr-drafter.md](./story-02-adr-drafter.md).

## Implementation Evidence

**Plugin** (`holdspeak/plugins/builtin/adr_drafter.py`) — real `AdrDrafterPlugin`
(`kind="artifact_generator"`, deferred, `required_capabilities=["llm"]`). Phase-16
pattern: strict prompt → single fenced ```json → `_extract_adrs` parses
`{"adrs": [{title, status, context, decision, consequences}]}`. `status` is
coerced via `_normalize_status` to one of `proposed | accepted | rejected |
superseded | deprecated` (synonyms: `approved`/`agreed`/`decided` → accepted,
`draft` → proposed, `obsolete` → deprecated; unknown → proposed). An ADR needs at
least a title **and** a decision to count. Success when ≥1 ADR; else the clean
failure shape. Uses `build_configured_meeting_intel` (honours `.43`).

**Registration:** `_REAL_PLUGINS` maps `adr_drafter` → the real class (**5 real
plugins now, 9 stubs**). **No routing ripple** — `adr_drafter` was already on the
`architect` / `architecture` chains as a stub.

**Synthesis** (registry, HS-28-01): added `_adr_body` (per ADR: `**title** —
_status_` then Context / Decision / Consequences lines, skipping empties) and
`_render_adrs`, registered under `"adr"` in `_ARTIFACT_RENDERERS`. Other bodies
unchanged.

**Web render** (`history.astro` + `history-app.js`): `adrsFor(artifact)` + an
`.adr-artifact` block — per record a title + status pill + Context / Decision /
Consequences lines, from `structured_json` (never raw `body_markdown`). The
plain-text fallback `x-show` now also excludes ADRs. `(cd web && npm run build)`
ran clean.

## Tests

- `tests/unit/test_adr_drafter_plugin.py` (13 cases): attributes, success +
  status, status-synonym coercion, unknown-status fallback, ADR-without-decision
  dropped, empty → failure, unparseable → failure, no-transcript,
  provider-exception, `_extract_adrs` edge cases, `_normalize_status`, registrar,
  capability-blocked.
- `tests/unit/test_artifact_synthesis_diagram.py` (+1): `adr` body + structured
  key; the byte-for-byte default-body guard still passes.
- No routing-test churn (already-routed stub flipped to real).

```bash
uv run pytest -q tests/unit/test_adr_drafter_plugin.py tests/unit/test_artifact_synthesis_diagram.py tests/unit/test_intent_dispatch.py   # 26 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                          # 1953 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (real `.43` Q6)

Direct plugin run against the live endpoint (real provider, no override):

```
summary: 2 ADR(s); 1 accepted.
confidence: 1.0
 - ACCEPTED :: Adopt Postgres for Billing Data Store
     decision: Adopt Postgres as the primary data store for billing instead of DynamoDB to guarantee ACID compliance for invoice transactions.
 - PROPOSED :: Implement Redis Queue for Notifications
     decision: Propose introducing a Redis queue ... to buffer and absorb notification traffic spikes ...
```

## Live evidence (spoken e2e, extended)

`tests/e2e/test_spoken_meeting_e2e.py` now runs **five** real plugins
(`mermaid_architecture`, `action_owner_enforcer`, `decision_capture`,
`requirements_extractor`, `adr_drafter`) against real endpoints and asserts the
`adr` artifact + `.adr-artifact .adr-record` render. From the *natural, implicit*
conversation the drafter inferred an ADR ("Implement Real-Time Feedback Status
Dashboard", status **accepted**, with Context / Decision / Consequences). The
screenshot capture was upgraded to grow the viewport to the modal's content
height (the meeting-detail modal is a fixed overlay that scrolls internally, so
`full_page` capped at the fold) — `evidence/spoken_meeting_artifacts.png` now
shows the transcript + all five artifacts in one frame. The e2e's `EVIDENCE_DIR`
was repointed to this phase's `evidence/`.

```bash
HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s   # 1 passed (artifacts: action_items, adr, decisions, diagram, requirements)
```

## Result

Five real plugins now flow end-to-end. The renderer registry (HS-28-01) made the
new `adr` body a drop-in. **Next: HS-28-03** (`milestone_planner`).
