# Evidence — HS-35-04: Spoken-e2e breadth (incident retro)

**Date:** 2026-06-04. **Story:** [story-04-spoken-e2e-incident.md](./story-04-spoken-e2e-incident.md).

## What shipped

A second opt-in spoken-meeting end-to-end scenario,
`test_spoken_incident_retro_end_to_end`, in `tests/e2e/test_spoken_meeting_e2e.py`.
The existing scenario covered balanced / architecture / delivery / product; this one
exercises the previously-uncovered **incident** + **comms** chains end-to-end on the
real stack:

```
say (multi-voice incident postmortem) -> per-line wav -> Whisper (base) ->
transcript segments -> PluginHost (real .43 Qwen3.5-9B-Q6, deferred queue drained) ->
synthesize_and_persist -> temp SQLite (meeting + transcript + artifacts) ->
MeetingWebServer -> Playwright drives /history -> screenshots the rendered artifacts
```

The script is a short incident retro — detection, 38-minute impact window, the 2:05
deploy trigger, connection-pool exhaustion, rollback, root cause, a runbook step to
add, a holiday-traffic risk, a canary-deploy decision, and a leadership note to send —
so the chain has natural material to infer:

| Plugin | Inference | Artifact rendered |
|---|---|---|
| `incident_timeline` | chronological events | Incident Timeline (`.incident-timeline li`) |
| `runbook_delta` | added/modified runbook steps | Runbook Delta (`.runbook-list .runbook-change`) |
| `risk_heatmap` | cross-cutting risks | Risk Heatmap table (`.risk-table tbody tr`) |
| `stakeholder_update_drafter` | headline + highlights/risks/next | Stakeholder Update (`.stakeholder-update`) |
| `decision_announcement_drafter` | decisions to announce + audience | Decision Announcement (`.announcement-artifact .announcement`) |

Assertions are **structural** (the real LLM is non-deterministic), matching the
existing scenario: each plugin returns `success`; outputs carry `events` / `changes` /
`risks` / `update` (headline or highlights) / `announcements`; the persisted artifacts
carry the same keys under the mapped artifact types (`incident_timeline`,
`runbook_delta`, `risk_register`, `stakeholder_update`, `decision_announcement`); and
the web view renders each artifact's selector. Exact wording is never asserted.

Opt-in exactly like the existing scenario: `pytestmark = spoken_e2e, slow` and a
module-level `pytest.skip(allow_module_level=True)` unless `HOLDSPEAK_SPOKEN_E2E=1`.
Any missing external piece (`say`, scipy, playwright, a reachable intel endpoint)
skips cleanly rather than failing.

## Tests

### The new scenario, run for real against `.43` (Qwen3.5-9B-Q6)

```
$ HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s \
    tests/e2e/test_spoken_meeting_e2e.py::test_spoken_incident_retro_end_to_end
[e2e:incident] transcript: Okay, let's walk through last Tuesday. Check out was hard
down for 38 minutes between 2.15 and 2.53 ... we're switching the payment service to
Canari Deploy starting next Monday ... so everyone hears it from us first.
[e2e:incident] artifacts: ['decision_announcement', 'incident_timeline',
'risk_register', 'runbook_delta', 'stakeholder_update']
[e2e:incident] screenshot saved:
pm/roadmap/holdspeak/phase-35-plugin-frontier/evidence/spoken_incident_artifacts.png
1 passed, 5 warnings in 24.14s
```

All five incident + comms plugins fired, produced non-empty structured output, were
persisted as the five mapped artifact types, and rendered in the web view.

**Screenshot:** [`spoken_incident_artifacts.png`](./evidence/spoken_incident_artifacts.png)
(1280×3094) — the meeting modal with the transcript and all five rendered artifacts
(Stakeholder Update, Runbook Delta, Risk Heatmap severity table, Incident Timeline,
Decision Announcement).

### Default suite (opt-in module skips cleanly)

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
...
2007 passed, 15 skipped in 58.38s
```

The spoken-e2e module skips without `HOLDSPEAK_SPOKEN_E2E=1`; the rest of the suite is
green. `tests/e2e/test_spoken_meeting_e2e.py` is ruff-clean.

## Note surfaced while verifying (out of scope, flagged for follow-up)

Running the scenario for real required the intel endpoint to resolve. The user's
`~/.config/holdspeak/config.json` still carried `meeting.web_enabled` — the key
**retired in HS-32-06**. `Config.load()` parses each sub-config as
`MeetingConfig(**data)` inside a broad `except Exception: return cls()`, so that one
unknown key made the **entire** config silently fall back to defaults (provider
`local`, no `intel_cloud_base_url`) — i.e. the configured `.43` cloud endpoint was
ignored on every load, not just in the test. The stale key was removed from the user
config to unblock the run. The silent total-fallback is a latent foundation bug
(any legacy/extra key invisibly discards the whole config); recommend a small
hardening fix (filter unknown keys per sub-config, or log instead of swallow). Tracked
as a closeout follow-up, not folded into this story.
