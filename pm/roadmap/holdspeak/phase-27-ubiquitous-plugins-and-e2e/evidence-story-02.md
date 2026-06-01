# HS-27-02 Evidence — Spoken-meeting end-to-end harness

**Date:** 2026-06-01.
**Story:** [story-02-spoken-meeting-e2e.md](./story-02-spoken-meeting-e2e.md).

## Implementation Evidence

**Harness** (`tests/e2e/test_spoken_meeting_e2e.py`) — a single pytest test, all
Python, no mocks, on real endpoints:

1. `say` (voices Alex / Samantha) synthesizes each scripted line to a 16 kHz wav.
2. `Transcriber` (Whisper `base`) transcribes each line → per-speaker
   `TranscriptSegment`s; the joined text is the meeting transcript.
3. `PluginHost(enabled_capabilities={"llm"})` + `register_builtin_plugins`;
   `mermaid_architecture` and `action_owner_enforcer` are queued (deferred) and
   drained via `process_next_deferred_run` — hitting the **real `.43` Q6 LLM**.
4. A temp SQLite DB (`reset_database()` + `get_database(tmp)`) gets the meeting
   (with transcript segments) + artifacts via `synthesize_and_persist`.
5. `MeetingWebServer` serves it; **Playwright (sync, Python)** drives `/history`,
   clicks the meeting, auto-waits for the rendered SVG + the action-item checklist
   + the transcript, and screenshots `evidence/spoken_meeting_artifacts.png`.

**Opt-in + skip-guarded:** module-skips unless `HOLDSPEAK_SPOKEN_E2E=1` (so the
default sweep never runs it), and skips cleanly if `say` / scipy / Playwright /
the intel endpoint / Whisper are absent. Marker `spoken_e2e` registered in
`pyproject.toml` (`--strict-markers` is on).

Run: `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`.

## Two real gaps the e2e surfaced (and fixed)

This is the value of a true e2e — both were invisible to the unit tests:

1. **Plugins ignored the configured provider.** `register_builtin_plugins` built
   each plugin with a bare `MeetingIntel()` (module defaults), so in the real
   runtime they never used the `.43` config and returned their *failure* shape.
   Fixed in commit `fe9c0e8` (`build_configured_meeting_intel`, reads
   `Config.load().meeting`). Prior HS-16 tests passed an explicit `intel_call`
   override, so they never hit this path. (This also fixed `mermaid_architecture`
   in the live runtime, not just the e2e.)
2. **Action-items rendered as a raw-markdown blob.** `/history` showed an
   artifact's `body_markdown` via a plain-text binding, so the checklist markdown
   collapsed into an unreadable `### … - [ ] … ⚠️ missing both` string. Fixed:
   `history.astro` + `history-app.js` now render `structured_json.action_items`
   as a proper checklist (task + `owner:` / `due:` pills + a warn badge), with
   friendly gap labels (`missing_both` → "No owner or due date"). The diagram
   keeps its SVG render; only the raw-markdown fallback path was the problem.

## Result (screenshot)

`evidence/spoken_meeting_artifacts.png` — the `/history` detail for the spoken
meeting shows all three, end to end on real endpoints:

- **Transcript:** per-speaker, real Whisper output ("Me [0:00] … the API gateway
  routes to the off service …" — "off" is Whisper mishearing "auth", proof it's
  genuinely the spoken pipeline).
- **Mermaid Architecture (diagram, 100%):** rendered SVG (Client / Notifications
  → Queue → Redis, API Gateway → Off/Billing Service → Postgres).
- **Action Owner Enforcer (action_items, 100%):** a clean checklist —
  *Draft the OAuth flow* (owner Carol · Friday); *Book the offsite venue*
  (**No owner or due date**); *Review the migration plan* (owner Maria ·
  **No due date**).

## Tests

```bash
HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s   # 1 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py          # 1915 passed, 14 skipped
```

The `--strict-markers` default sweep collects the e2e and skips it (opt-in env
unset) — it does not run or slow the default suite.

## Result

A real spoken meeting becomes a transcript, a rendered diagram, and a structured
action-item report in the actual UI — and the exercise hardened two production
paths the unit tests couldn't reach. Phase 27 is 2/5. **Next: HS-27-03**
(`decision_capture`), which should ship with its own structured web render.
