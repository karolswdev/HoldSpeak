# HS-9-06 evidence — Assisted enrichment controls + phase exit

## How each acceptance criterion is met

### Connector controls are visible

`/activity` carries a Connectors panel rendered from
`web/src/scripts/activity-app.js:renderConnectors`. Each known
connector (`gh`, `jira`, `calendar_activity`) appears as a card
with: title, monospace id, enabled/disabled pill, CLI-ready /
not-found pill (when applicable), capabilities, last_run,
optional CLI path, and a `last_error` block when the most
recent run reported one. The panel sits between Project rules
and Meeting candidates so the connector-shaped column reads
top-to-bottom.

Source: HS-9-12 evidence
(`pm/roadmap/holdspeak/phase-9-assisted-activity-enrichment/evidence-story-12.md`).

### Connector outputs are deletable

Per-connector deletion is wired through:

- `DELETE /api/activity/enrichment/connectors/{id}/annotations`
  for `gh` / `jira`.
- `DELETE /api/activity/enrichment/connectors/{id}/candidates`
  for `calendar_activity`.

The Connectors panel renders the corresponding "Clear annotations"
or "Clear candidates" button only on capabilities the connector
actually has, and the click goes through `holdspeakConfirm` with
the canonical "source data is untouched" scope copy.

Bulk-clear paths from earlier stories — `DELETE
/api/activity/records`, `DELETE
/api/activity/meeting-candidates?status=dismissed` — are still
available alongside.

### Focused assisted-enrichment sweep passes

```
$ uv run pytest \
    tests/unit/test_activity_extension.py \
    tests/unit/test_activity_connector_preview.py \
    tests/unit/test_activity_candidates.py \
    tests/unit/test_activity_github.py \
    tests/unit/test_activity_jira.py \
    tests/unit/test_activity_entities.py \
    tests/unit/test_activity_mapping.py \
    tests/unit/test_activity_history.py \
    tests/unit/test_activity_context.py \
    tests/integration/test_web_activity_api.py -q
…
111 passed in 2.77s
```

### Full regression passes

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1242 passed, 13 skipped in 28.33s
```

### Phase evidence bundle exists

Every shipped story in this phase has a matching evidence file
in this directory:

- `evidence-story-01.md` — Connector registry + annotations.
- `evidence-story-02.md` — Calendar / Outlook candidates.
- `evidence-story-03.md` — Firefox companion extension events.
- `evidence-story-04.md` — GitHub CLI enrichment.
- `evidence-story-05.md` — Jira CLI enrichment.
- `evidence-story-07.md` — Meeting candidate API surface.
- `evidence-story-08.md` — Meeting candidate browser controls.
- `evidence-story-09.md` — Candidate dedupe + time hints.
- `evidence-story-10.md` — Candidate recording workflow.
- `evidence-story-11.md` — Activity dashboard polish.
- `evidence-story-12.md` — Connector controls + output deletion.
- `evidence-story-13.md` — Connector dry-run harness.
- `evidence-story-06.md` — *this file* (DoD).

## Phase shape — what shipped

Phase 9 turned the local activity ledger into a real
assisted-enrichment platform:

- A persistent connector registry (`activity_enrichment_connectors`)
  + `activity_annotations` + `activity_meeting_candidates` tables
  (HS-9-01).
- Calendar / video-call meeting candidates inferred deterministically
  from existing local activity (HS-9-02), now reachable via
  `/api/activity/meeting-candidates/preview` (HS-9-07) and a
  browser-driven preview/save/dismiss/start flow (HS-9-08, HS-9-09,
  HS-9-10).
- Two read-only CLI enrichment connectors (`gh`, HS-9-04; `jira`,
  HS-9-05) that *preview* the exact commands they would run,
  refuse to execute until explicitly enabled, and write capped
  local annotations on a successful run.
- A companion Firefox extension (HS-9-03) that posts active-tab
  metadata over loopback. The receiving parser hard-rejects every
  field name that implies sensitive content; private/incognito
  events and non-`http(s)` URLs are blocked at the schema level.
- A polished `/activity` surface (HS-9-11) on the new design
  system, with empty-state grammar, candidate preview-vs-saved
  visual distinction, and panel-scoped messages.
- Browser-visible connector controls + scoped output deletion
  (HS-9-12) with the canonical destructive-confirmation pattern.
- A shared dry-run harness (HS-9-13) so every connector returns
  the same payload shape (`commands`, `proposed_annotations`,
  `proposed_candidates`, `warnings`, `permission_notes`,
  `truncated`) — mutation-free by construction and locked down
  by tests at both the harness and HTTP layers.

## What's intentionally out

- Microsoft Graph / OAuth.
- Browser-store distribution of the Firefox extension.
- Automatic recording or meeting join without an explicit user
  action.
- Reading or writing source-of-truth data on GitHub / Jira /
  any external system.
- Page bodies, cookies, headers, form data, screenshots,
  selection text, or anything from private-browsing windows.

These remain phase-scope exclusions and are mechanically
enforced by the parser
(`holdspeak/activity_extension.py:FORBIDDEN_FIELDS`) and the
connector run paths (which require explicit enablement and never
mutate source data).

## Phase exit

Phase 9 is **done**. The next active phase is **phase 11**
(Local Connector Ecosystem), which generalizes the static
`KNOWN_CONNECTORS` registry into manifest-driven connector
packs and ships first-party `gh` / `jira` packs against the
shared dry-run harness from HS-9-13.
