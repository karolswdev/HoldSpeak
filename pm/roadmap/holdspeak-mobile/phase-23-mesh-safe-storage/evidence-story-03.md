# Evidence — HSM-23-03 — The readiness / doctor panel in Settings

**Status:** done (2026-07-04), on `holdspeak-mobile/hsm-23-03-readiness-panel`.

## 1. The pieces

- **`StoreHealthProbe` (Providers)** — the Wave-4 schema safety gets a reportable
  value: `ok(schema, integrityOK)` / `missing` / `refusedNewer(stored, build)` /
  `failed`, plus the `.bak` sibling count. Uses the SAME open path the app uses, so a
  refused-newer store reports exactly what the app hit. `StoreHealthProbeTests`
  (4 tests): missing-is-fresh-not-fault, healthy schema+integrity, refused-newer with
  both versions AND probe-twice-agrees (no heal/stamp), backup-sibling count after a
  v1 migration.
- **`SetupStatus.sections` (Contracts)** — the hub's per-check doctor block
  (`{id, label, status, detail}`, status `pass|warn|fail|unknown` per
  `_section_from_check`) finally decoded instead of dropped. The stub JSON in
  `SetupStatusClientTests` had drifted from the real wire (`"state"` — the route
  emits `"status"`); corrected to the real shape and asserted, plus the
  older-hub-without-sections tolerant decode. No new route: the same
  `GET api/setup/status` read (no api-surface regen needed).
- **The panel (`AppSettings.swift`)** — a READINESS section in Settings, two cards,
  labels not manuals: **This iPad** (store health chip, mic permission, models on
  device, app version) and **the paired desktop** (not paired / unreachable /
  overall rollup chip + every doctor section as a row with detail + status chip).
  `HS_DEMO_READINESS=1` (sim-only) autoscrolls to the section for screenshot runs —
  the same view the scroll gesture reaches.
- **The typed refusal (`MeetingCaptureApp.swift`)** — `StorageError.tooNew` no longer
  collapses into "Store unavailable: …": the banner states
  "Store written by a newer HoldSpeak (v7 > v2), left unread".

## 2. The live proofs (connected simulator, real scratch hub — never seeds)

Scratch hub: a real `MeetingWebServer` on `127.0.0.1:8123` (config + DB redirected
to a temp dir BEFORE imports, the standing pattern); the app installed FRESH
(persisted `hs.peer.*` defaults cleared) and paired via `HS_DESKTOP_HOST/PORT`.

- [`hsm-23-03-readiness-live-hub.png`](./screenshots/hsm-23-03-readiness-live-hub.png)
  — **both halves live**: This iPad (Store `ok · schema v2`, mic `not asked yet`,
  models `none on device`, app 0.1.0) and the hub card showing the REAL doctor:
  **Needs attention** (amber rollup), 23 sections, the genuine
  `meeting-intelligence-runtime` **warn** ("Intel model not found") amber among green
  passes — the hub's own truth, not a seeded state.
- [`hsm-23-03-readiness-refused-newer.png`](./screenshots/hsm-23-03-readiness-refused-newer.png)
  — a REAL future-version store (`user_version=7` seeded into the app container via
  sqlite3) renders the amber Store chip **`newer than this app · v7 > v2`** from the
  same refuse-newer guard the app open hits.
- [`hsm-23-03-refused-newer-banner.png`](./screenshots/hsm-23-03-refused-newer-banner.png)
  — the classic home wearing the typed banner (named protection, not a crash string).
- **The store survived everything**: after the app open + two panel probes,
  `PRAGMA user_version` still reads **7** and the future row + future column are
  intact (`mtg_future|1`) — refused, never downgrade-stamped, proven on the actual
  container file.

## Suites

- `swift test --filter 'StoreHealthProbeTests|SetupStatusClientTests'` — **9 passed**
  (4 new probe + 5 setup-status incl. the sections decode).
- Full `swift test` — see the story-close run in the phase status (green before
  commit).
- `uv run pytest -q tests/unit/test_doc_drift_guard.py` — **18 passed** (the new
  Swift copy is guard-clean).
- Meeting-capture sim build — **BUILD SUCCEEDED** (gen + patch + xcodebuild, the
  standing toolchain loop).

## Honest boundaries

- The three `try?` read sites (`DeskHome:239`, `ReviewUI:38`, `MeetingCaptureApp:406`)
  stay nil-tolerant by design — they render empty lists; the refusal itself is
  surfaced by the banner + the panel, which is where a person can act on it.
- Mic permission is read, never requested, from Settings (no permission prompt from a
  status panel).
- The desktop card reports; it does not repair (the desktop CLI owns fix flows).
