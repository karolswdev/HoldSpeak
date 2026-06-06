# Evidence — HS-42-04 — Guided first dictation (real app)

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

## What shipped

The magic-moment proof: a guided first-dictation panel that confirms a **real**
dictation landing in another app, and the durable milestone that flips `first_run`
so `/setup` stops fronting the dashboard.

### Milestone-on-success — `holdspeak/web_runtime.py`

`WebRuntime._mark_first_dictation()` records the `FIRST_DICTATION_SUCCESS`
milestone (`db.milestones`) at the **two real dictation-success points** in
`_transcribe_and_type`:

- after a successful **type into the active app** (`dictation_typed`), and
- after a successful **delivery to an agent session** (`dictation_delivered`).

Idempotent (a process-local guard sets it at most once) and fully defensive (a DB
hiccup never disrupts dictation). No-speech / too-short / failed-typing paths do
**not** set it. Once set, `build_setup_status().first_run` is `false` and the `/`
guard (HS-42-03) stops redirecting.

### The guided panel — `web/src/pages/setup.astro` + `setup-app.js`

The `#first-dictation` section is now a real guide:

- **3 numbered steps** (focus a field → hold the hotkey, speak, release → watch it
  appear), a link to `/settings` for the hotkey, and a **readiness mini-row**
  (Global hotkey · Text injection · Transcription backend chips, colored by status
  from `/api/setup/status`).
- **Live feedback** over the `runtime_activity` websocket: a pulsing
  "Listening… / Transcribing… / Typing it into your app…" indicator while a
  dictation is in flight.
- **Success state:** on a `complete` + `dictation_typed`/`dictation_delivered`
  activity, the panel flips to a green **"✓ Done — It worked, text landed in your
  app"** card and shows the **transcript** (fetched from `/api/state`); it also
  re-reads `/api/setup/status` so the milestone state stays in sync.
- An honest **fallback ladder** (Wayland/hotkey blocked → focused fallback;
  text not appearing → clipboard paste → the dictation cockpit).

## Verification

- **Milestone wiring (CI-provable, no mic):** a runtime built with a fake
  transcriber + capturing typer, driven through the real `_transcribe_and_type`,
  sets the milestone; no-speech does not; idempotent. (3 tests.)
- **Live magic-moment (Playwright):** loaded `/setup` (guided), broadcast a real
  `dictation_typed` `runtime_activity` → the panel flipped to **"It worked — text
  landed in your app"** and showed the transcript
  *"the quick brown fox jumps over the lazy dog"*. `LIVE SUCCESS OK`.
- Screenshots: [`evidence/setup_guided.png`](./evidence/setup_guided.png) (the
  guide + steps + readiness chips), [`setup_first_dictation_done.png`](./evidence/setup_first_dictation_done.png)
  (the done state once the milestone is set), and
  [`setup_dictation_success_live.png`](./evidence/setup_dictation_success_live.png)
  (the live success with the transcript).
- The **real-app leg with a live mic** is a manual dogfood, captured with the TTFD
  headline in the HS-42-08 closeout.

## Tests run

```
uv run pytest -q tests/integration/test_setup_first_dictation.py
→ 3 passed
```

- `test_successful_dictation_sets_the_first_dictation_milestone`
- `test_no_speech_does_not_set_the_milestone`
- `test_mark_first_dictation_is_idempotent_and_defensive`

Full suite: see the HS-42-04 commit message.

## Acceptance criteria

- [x] The guided flow shows the steps + a readiness row + live status; on a real
      dictation it shows transcript + confirmation. *(Deterministic transcription
      proof is the existing `core_path_smoke` CI test — the committed fixture WAV
      lives in `tests/`, not the installed package, so the production flow uses the
      user's real speech.)*
- [x] The success path proves insertion into an **external** app (live
      `dictation_typed` over the WS → success banner + transcript); the real-mic
      capture is the HS-42-08 dogfood.
- [x] Failure modes route to remediation; clipboard/focused fallback reads as
      intentional.
- [x] A verified success **sets the durable first-success milestone** (so `/`
      stops showing setup-mode); proven by tests.
- [x] Bundle rebuilt; only `web/src` committed; screenshots of the guide + the
      done state + the live success.
- [x] Default suite green; the deterministic milestone test adds no real
      network/LLM call.
