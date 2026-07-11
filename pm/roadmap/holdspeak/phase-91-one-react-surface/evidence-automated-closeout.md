# Phase 91 automated closeout evidence

**Captured:** 2026-07-10

**Result:** HS-91-01 through HS-91-09 pass; HS-91-10 remains in progress for
owner workflows and actual Swift DeskOS parity evidence.

## Architecture and build

- One `web/index.html`, React 19 entry, browser router, typed API/auth helpers,
  and `RuntimeBusProvider` serve every product route.
- The architecture guard passed across 79 source files with zero legacy
  framework residue, selector bootstraps, HTML injection, or direct request
  bypasses.
- FastAPI's `SPA_ROUTES` integration lock proved every direct link returns the
  byte-identical Vite shell, including aliases and a tokenized deep link.
- The production Vite build emitted to `holdspeak/static/_built/`.
- Initial JavaScript is 79.54 kB gzip (`index` 62.33 + React/router 17.21) and
  shared CSS is 31.62 kB gzip. Heavy route chunks remain lazy: Desk 77.41 kB,
  Dictation 4.51 kB, History 3.81 kB, Live 2.57 kB, and Workbench 2.10 kB gzip.

Command:

```text
cd web && npm run check
```

Result: architecture guard passed; TypeScript passed; 13 Vitest files / 109
tests passed; production build passed.

## Backend and wire contracts

Command:

```text
.venv/bin/python -m pytest -q tests/integration/test_web_*.py \
  tests/integration/test_dictation_moment_of_truth.py \
  tests/integration/test_dictation_journal_replay.py \
  tests/integration/test_actuator_presence_broadcasts.py \
  tests/integration/test_history_slack_surfaces.py \
  tests/integration/test_presence_mascot_gate.py \
  tests/integration/test_presence_qlippy_shell.py \
  tests/integration/test_settings_language_ui.py \
  tests/integration/test_settings_spoken_symbols.py \
  tests/integration/test_wake_ux.py \
  tests/unit/test_frontend_density_guard.py \
  tests/unit/test_web_null_read_guard.py \
  tests/unit/test_web_presence_indicator.py \
  tests/unit/test_desk_locks.py tests/unit/test_doc_drift_guard.py
```

Result: **541 passed** in 105.47 seconds. Pytest reported one non-failing
background-thread warning from transcript-import fixture teardown: its temporary
SQLite database was removed while the import worker was completing. The Web
migration assertions passed and no test was skipped.

The pass caught and fixed a material proposal-parity defect before closeout:
History and Qlippy now send the audited backend decisions `approved` and
`rejected`, and enable them for the production `proposed` state.

## Browser and accessibility audit

The audit drove all 17 canonical routes at 1440×1000 and 430×932 through a
fresh FastAPI process. The checked-in [report](./evidence/web-audit/report.json)
and 34 captures record:

- 34/34 HTTP 200 loads;
- zero console errors;
- zero unnamed visible controls;
- zero effective targets below 24 px;
- zero native-style select fallbacks; and
- zero horizontal viewport overflow.

The component gallery also passes its axe smoke test and demonstrates shared
default, selected, disabled, loading, success, warning, error, dialog, field,
choice, disclosure, toolbar, and empty states. Keyboard tests pin tab-arrow
navigation and dialog focus return.

## Non-waivable close gate

Automated browser evidence does not prove native behavior. Before HS-91-10 or
the phase can be marked done, the owner must complete real first-run/model
setup, dictation, live meeting-to-archive, Desk create/edit/ask, profile, and
Workbench workflows. The same closeout must capture the actual Swift app beside
Web for arrival, Desk, Dictation, Meetings, Settings, and one Studio tool.
