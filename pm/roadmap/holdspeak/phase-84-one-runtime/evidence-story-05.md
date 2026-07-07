# Evidence — HS-84-05 — Docs + the live walk

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-84-05-docs-and-the-live-walk` (the closing PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `docs/MODELS.md` — §3 (endpoint) leads with "author the endpoint once as a
  runtime profile, then pick it"; the raw config shape demoted to the
  documented fallback; the "Runtime profiles" section gains the hub-pipeline
  pickers + the doctor line.
- `docs/MEETING_MODE_GUIDE.md` — the endpoint bullet + the homelab fast path
  teach the picker; `intel_cloud_base_url` noted as the no-profile fallback.
- `docs/USER_GUIDE.md` — both endpoint sections (dictation backend, meeting
  cloud/homelab) gain the picker path; examples labeled as the fallback shape.
- `docs/DICTATION_PIPELINE_GUIDE.md`, `docs/DICTATION_COPILOT.md` — pointer
  paragraphs under their runtime config examples.
- `scripts/walk_hs84_live.py` — the six-beat walk (stays as the phase's
  regression rig; self-cleaning, reuses the HS-83 token-wrapper arrival).
- Phase close: `current-phase-status.md` (CLOSED 5/5, exit criteria re-run),
  `final-summary.md`, `BACKLOG.md` row S → SHIPPED, roadmap README
  (pointer + index row 84 → done).
- 4 committed screenshots under `screenshots/` (profile authored, settings
  picked, runtime picked, the agent badge).

## Verification artifacts

The walk, on the REAL hub (127.0.0.1:8765, restarted on merged main with
`HOLDSPEAK_WEB_PORT=8765`) → the `.43` llama.cpp — full output:

```
prior assignments: intel=None dictation=None
beat 1: profile authored in the editor → profile_7a350e4e2108
beat 2a: meeting intel picked in Settings and saved
beat 2b: dictation picked on the Runtime tab and saved
beat 3: agent badge = '☁ Qwen3.5-9B-Q6_K · 192.168.1.43'
beat 4: reroute executed on the profile; artifacts_saved=4
beat 5: dictation dry-run OK (keys: ['blocks_count', 'final_text',
        'journal_id', 'learning', 'project', 'runtime_detail',
        'runtime_status', 'stages'])
beat 6: doctor → "[PASS] Runtime profiles: meeting intel: profile
        'Walk .43' (192.168.1.43); dictation: profile 'Walk .43'
        (192.168.1.43)"
HS-84-05 LIVE WALK: all six beats PROVEN on the real hub → .43
cleanup: assignments restored; walk recipe + profile removed
```

- Docs/voice guards: `uv run pytest -q tests/unit/test_doc_drift_guard.py
  tests/unit -k "doc or voice"` → **143 passed**.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3250 passed, 37 skipped** (env-gated), docs-and-script story so the
  count matches HS-84-04's baseline.

## Acceptance criteria — re-checked

- [x] The walk passes end to end on the real hub → `.43`, all three runs in
  one pass, no endpoint URL entered outside `/profiles` — the output above;
  the URL was typed once, in the profile editor (beat 1).
- [x] Doctor output captured naming the profile per pipeline — beat 6,
  verbatim above.
- [x] Docs guards green; touched guides read product-tense — 143 passed.
- [x] BACKLOG row S, roadmap README pointer/index, phase status, and
  final-summary updated in this closing commit.
- [x] Full suite green — above.

## Deviations from plan

- The deferred legacy-fields decision resolved as KEEP (recorded in the
  story Notes + final summary): headless setups write the config fields
  directly, they cost one resolver branch, and deletion is migration pain
  with no behavior win.
- The walk surfaced an ops wrinkle, recorded in the story Notes: a hub
  restart without `HOLDSPEAK_WEB_PORT` pinned can fall back to an ephemeral
  port while 8765 sits in TIME_WAIT.
- One walk-script fix during the run: `<option>` elements never report
  "visible" to Playwright; the picker-populated wait uses
  `wait_for_function` on the option count.

## Follow-ups

- None required. The mobile track's Apple surfaces already carry their half
  of the profiles arc (HSM Phase 24); the BACKLOG S map records the whole
  lineage.
