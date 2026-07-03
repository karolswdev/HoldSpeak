# Handover — 2026-07-02/03 — The Desk Era session

One session took the repo from "Phase 72 scaffolded" to **seven phases
closed and merged** (72–78), two standalone fixes, and a green main at
**3,100 tests**. This is the map for whoever picks it up: what shipped,
what the owner decided, what remains, and the traps.

## Where main stands

- **HEAD:** the Phase-78 merge (PR #214). Every PR this session merged on
  a conclusion-checked green (`gh pr checks N --json bucket` all `pass`
  before `gh pr merge` — see "The CI incident" below for why this is now
  mechanical law).
- **Suite:** 3,100 passed / 37 skipped (`uv run pytest -q
  --ignore=tests/e2e/test_metal.py`). Web: 17 Astro pages + the React
  desk island; vitest `npm run test:desk` 9/9. Swift package green.
- **Schema:** **v7** (v6 = run-born artifacts; v7 = agent pinned
  context). Both v5→ and v6→ facsimile upgrade paths are locked by tests
  that assert the pre-migration `.bak` lands first.
- **Version:** pyproject 0.3.1 on PyPI; `CHANGELOG.md` has a populated
  `[Unreleased]` covering everything since. **No release was cut** — the
  owner has not yet touched the new front door.

## The phases, one line each

| Phase | PR | What it is |
|---|---|---|
| 72 — One Spine | #207 | Cross-surface contract guards, the one runtime bus (`runtime-bus.js`, sole `/ws` owner), route naming; 14 real bugs |
| 73 — The Desk, Inhabited | #208 | **The web front door `/` is a React 19 island** (`web/src/desk/`); create/open/edit/file/record/run all in-world; the Alpine desk deleted (−3,265 lines) |
| 74 — The Run Story | #209 | Runs persist as **run-born artifacts** (schema v6, `origin='run'`) with lineage + honest `intel_status scope:"run"` frames; results materialize on the stage |
| 75 — Preview Before It Types | #210 | Opt-in `dictation.preview_before_type` (off by default, off-path locked byte-identical); one shell `PreviewCard` on every route |
| 76 — The Documentation Sweep | #211 | Truth audit of 22 docs; README presents the Desk; ARCHITECTURE's map caught up; WEB_DESK rewritten; **SECURITY's egress table completed** (3 missing desk-actuator doors) |
| 77 — Loose Ends | #212 | Schema v7 (agent `manual_context`/`use_zone_context` round-trip byte-faithful); the real `runtime_queue` frame for the Queue HUD; the coders-status conflation dead (flags → `GET /api/desk/actuators/status`) |
| 78 — Talk to the Desk | #214 | The hub's first transcribe route; **hold-to-talk mics on every desk input**; the waiting coder answered **by voice** through the HSM-13 seam; the re-recorded demo |

Standalone: **#213** (filed objects leave the open stage — the owner's
video-review bug) and the six dead root strays deleted (owner-ordered,
`48b1c9b`).

## Owner decisions made this session (standing law)

1. **The Desk is the main web surface** — `/` IS the desk; Phase 70's
   Home is retired; `/desk` 307-redirects home.
2. **React + Vite for interactive surfaces; no new Alpine, ever.** Astro
   stays for document pages.
3. **Voice-first applies to the web too** ("we need to be able to just
   talk to this stuff") — every input carries a hold-to-talk mic; never
   present confirm-friction as the default story.
4. **A filed object leaves the open stage** (the iPad grammar is the
   contract); **demos must seed every lane including a waiting coder**.
5. Merge phases via PR, **on conclusion-checked green only**.

## Outstanding — needs the OWNER's hands (blocked on testing access)

- The **desk feel pass**: `holdspeak`, open the browser, live in it.
- **Mic-in-hand**: a real orb recording; a real hold-key dictation with
  `preview_before_type` on; a real spoken ask on the rail/coder.
- The **Phase-72 iPad walk** (legacy `@AppStorage` decode in anger; the
  renamed routes; coder-board and desk-relay taps).
- **The next release cut** (the `[Unreleased]` section is ready) — do NOT
  publish before the owner's feel pass.

## Outstanding — buildable headless (the candidate next phases)

1. **Lock the Walks** (offered twice, still the strongest): the phase
   proof scripts are throwaway — none of the desk/preview/voice behavior
   is protected by committed CI Playwright tests. The harness pattern is
   proven (see below); converting the walks is mostly transcription.
2. **Backend Decomposition II**: `db/activity.py` (1,596 lines) and
   `routes/meetings.py` (1,525) via the Phase-63 verbatim discipline.
3. Hub follow-up from 74: the `/run` routes could broadcast `intel_token`
   streams if the engine ever streams (today they honestly emit
   running→ready only).
4. iPad candidates: materialize run artifacts with a beat on the iPad
   desk; surface `manual_context` in the web agent editor (the hub
   persists it now; the web editor doesn't show it).

## The proof-harness pattern (used ~20 times this session)

```python
# uvicorn thread + scratch DB + monkeypatched hsdb.get_database +
# sync_playwright. Screenshots into the phase's screenshots/ dir.
db = Database(tmp / "x.db"); hsdb.get_database = lambda *a, **k: db
db.milestones.mark(FIRST_DICTATION_SUCCESS)   # or "/" bounces to /welcome
server = MeetingWebServer(WebRuntimeCallbacks(..., on_transcribe=..., on_remote_dictation=...))
# server.broadcast("frame_name", {...}) drives the live bus from the test.
```
- **Real speech**: launch Chromium with `--use-fake-device-for-media-stream`
  + `--use-file-for-fake-audio-capture=tests/fixtures/core_path_smoke_16k.wav`
  and a real `Transcriber(model_name="base")` behind `on_transcribe`.
- **Real LLM**: the hub's configured engine reaches `.43`; the Bash
  sandbox blocks LAN — run those proofs with the sandbox disabled.
  Always use instruction-following prompts ("say the word X and nothing
  else") so a followed instruction proves prompt delivery.
- **Video**: `record_video_dir` on the context; rename `page.video.path()`
  after `ctx.close()`.
- **Seed a waiting coder**: `ingest_agent_hook_event(agent="claude",
  payload={session_id, cwd, hook_event_name:"Stop", transcript_path},
  state_path=..., capture_messages=True)` where the transcript is a JSONL
  line `{"role":"assistant","content":"...?"}` — the awaiting flag
  derives from the TRANSCRIPT under `capture_messages`, and the question
  rides the wire as `last_assistant_text`. Point
  `sessions_mod._default_state_file` at your state path.

## Traps (each cost real time this session)

- **`gh pr checks --watch` exits on completion, not success** — never
  chain a merge after it. Check conclusions explicitly.
- **Guards grep comments too**: never name-drop banned strings
  (`aria-modal`, `getUserMedia`) in comments; it fired twice.
- **`[hidden]` loses to a class's `display:`** — restate
  `.x[hidden]{display:none}`; assert `is_visible()`, not the attribute.
- **`Config.load`'s explicit constructors drop unnamed fields** — a new
  config field must be added to BOTH the dataclass and the loader's
  constructor call, or it silently reverts on restart.
- **FastAPI without the `Request` import** silently degrades a body
  param to a required query field (422s).
- **The shell's cwd persists between Bash calls** and proof scripts run
  from `web/` write artifacts into `web/pm/...` — `cd` to the repo root
  in every compound command.
- **The schema snapshot regenerates with the test's LITERAL `r'\\s+'`
  normalizer** (it is intentionally not a real `\s+`).
- The **HUD linger contract**: reconcilers mark resolved jobs done +
  `schedulePrune`, never delete instantly.
- The wire rule for run-born artifacts: **DB stores NULL `meeting_id`,
  every serialized surface emits `""`** (the iPad's decode is
  non-optional).
- `web/package-lock.json` quirk: `npm ci` validates differently across
  platforms on the `@emnapi` optionals — CI uses `npm install
  --no-audit --no-fund` (a recorded soft spot).

## Where things live

- Phase folders: `pm/roadmap/holdspeak/phase-7X-*/` — every story has an
  `evidence-story-N.md`; every closed phase has `final-summary.md`.
- The desk island: `web/src/desk/` (store.ts is the verb surface;
  `world.ts` owns stage visibility — filed objects filter at root,
  `allObjects` is the open/edit lookup).
- The one mic call site: `web/src/scripts/speak-to-fill.js`; the one
  socket: `web/src/scripts/runtime-bus.js`.
- Memory (Claude's): one file per phase under the project memory dir;
  `feedback_desk_video_review.md` carries the owner's review as law.
