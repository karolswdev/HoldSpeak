# Phase 40 — Desktop Presence & Runtime Activity Indicators

**Status:** closed in `/tmp`. Scaffolded 2026-06-05 in
`/tmp/holdspeak-gui-indicator` for review only; not applied to the live
checkout.

**Last updated:** 2026-06-05 (HS-40-01 through HS-40-05 have temp
implementation slices: runtime activity payload + websocket event, optional
desktop presence host behind `HOLDSPEAK_DESKTOP_PRESENCE=1`, transient Tk
renderer/view model, `/` web cockpit presence card, and dictation/meeting
activity mapping for model load/warm/error, hotkey/device busy/error, meeting
segments, intel, action proposals, and save completion. HS-40-06 has full
non-metal pytest, focused backend/web tests, lint, compile, CI-safe desktop
view fixture evidence, build, browser screenshot evidence, native desktop
presence screenshot evidence, completed Tk smoke, and frontmost-app focus
smoke. HS-40-07 closeout is written. Live checkout still untouched.)

## Goal

Make HoldSpeak visibly explain what it is doing in real time even when the
browser dashboard is not open: ready, hotkey held/listening, recording
accepted, transcribing, dictation pipeline work, typing/injection, meeting
recording, meeting save, intel/plugin processing, and error states. The result
is a native-like desktop presence layer for macOS/Linux, backed by the existing
web runtime's local state stream.

## Scope

### In

- **Runtime activity event contract (HS-40-01).** Normalize a small status
  model for voice typing and meetings: `idle`, `listening`, `recording`,
  `transcribing`, `processing`, `typing`, `complete`, `meeting_live`,
  `saving`, `error`. Add timestamps, source (`hotkey`, `device`, `meeting`,
  `runtime`), and last activity detail. Broadcast status changes over the
  existing websocket and expose a reconnect-safe snapshot on
  `/api/runtime/status`.
- **Desktop presence host (HS-40-02).** Add an optional desktop client process
  owned by the HoldSpeak runtime. It subscribes to the local activity stream
  and can show/hide transient native-like windows on macOS and Linux without
  requiring the browser dashboard to be visible.
- **Native-style status window renderer (HS-40-03).** Design the actual
  overlay/toast window: compact, polished, keyboard/mouse non-disruptive,
  privacy-safe, reduced-motion-aware, and stable across state labels. It shows
  the state ring, short label, detail, last utterance/result where safe, and
  errors. Native windows are **transient only**: `idle` means hidden; activity
  states show/update; `complete`/`error` linger briefly and then hide/destroy.
- **Web cockpit reference indicator (HS-40-04).** Add the same presence
  rendering to `/` so the web dashboard remains the reference implementation,
  debug surface, and fallback when the desktop host is unavailable.
- **Dictation + meeting activity mapping (HS-40-05).** Map real HoldSpeak
  events into the activity model: hotkey/device dictation lifecycle,
  transcription/pipeline/injection, meeting live/saving, intel/plugin work,
  actuator proposals, and attached-device health.
- **Desktop + web verification (HS-40-06).** Add focused backend tests,
  websocket/client tests, web Playwright screenshots, and native-host fixture
  screenshots or smoke tests for idle/listening/transcribing/meeting/saving/
  error states on supported platforms.
- **Closeout (HS-40-07).** Update README/guide references, capture evidence,
  write `final-summary.md`, and leave Phase 40 ready to merge.

### Out

- Reintroducing the retired TUI or the old macOS `rumps` menubar runtime.
- Depending on OS notification centers as the primary experience. Native
  notifications can be a fallback, but the goal is HoldSpeak-owned presence
  windows with consistent states.
- A full settings/preferences app for the desktop host. Minimal config knobs
  are acceptable; deep customization is a later phase.
- Changing the dictation routing/rewriting behavior from Phase 39.
- Changing meeting intel/plugin contracts or artifact data shapes.
- Persisting detailed per-utterance telemetry in the DB. Presence is runtime
  state first; durable metrics are a later telemetry question.

## Exit Criteria (Evidence Required)

- [ ] `/api/runtime/status` and `/ws` expose a normalized runtime activity
      payload with state, source, timestamp, detail, and last error; existing
      callers keep working. (HS-40-01)
- [ ] A desktop presence host can run with the web runtime and show native-like
      transient status windows on macOS and Linux, with a documented fallback
      when the required desktop stack is unavailable. (HS-40-02/03)
- [ ] Holding and releasing the voice hotkey produces visible native and web
      transitions: ready → listening/recording → transcribing/processing →
      typing or idle/error; the native window disappears after the terminal
      state instead of remaining on screen. (HS-40-03/04/05)
- [ ] Meeting status transitions appear natively and in the web dashboard
      without a reload: start, live recording, segment arrival, intel/plugin
      work, proposal arrival, stop/saving, saved. (HS-40-04/05)
- [ ] The native/web UI is responsive and accessible: no text overlap, no
      layout shift in fixed controls, reduced-motion users do not get pulsing
      animations, and web has `role="status"`/polite updates where appropriate.
      (HS-40-03/04/06)
- [ ] The desktop renderer has an explicit visibility policy: `idle` is hidden,
      active transitions are visible, resolved states linger briefly, and no
      persistent floating window remains when HoldSpeak is idle. (HS-40-03/06)
- [ ] Focused backend, desktop-host, and frontend tests cover state derivation
      and websocket handling; screenshots/smoke artifacts are captured for
      desktop and web states. (HS-40-06)
- [ ] Documentation and PMO tracking are updated in the same commit(s);
      `final-summary.md` is written at phase close. (HS-40-07)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` and the relevant
      web build/test commands are run; no new default network/LLM call is
      introduced. (all)

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-40-01 | Runtime activity event contract | implemented in `/tmp` | [story-01-runtime-activity-event-contract.md](./story-01-runtime-activity-event-contract.md) | `tests/unit/test_runtime_activity.py`; `tests/unit/test_web_runtime.py` |
| HS-40-02 | Desktop presence host | implemented in `/tmp` | [story-02-desktop-presence-host.md](./story-02-desktop-presence-host.md) | `tests/unit/test_desktop_presence.py` |
| HS-40-03 | Native-style status window renderer | implemented in `/tmp` | [story-03-native-status-window-renderer.md](./story-03-native-status-window-renderer.md) | `tests/unit/test_desktop_presence.py` |
| HS-40-04 | Web cockpit reference indicator | implemented in `/tmp` | [story-04-web-cockpit-reference-indicator.md](./story-04-web-cockpit-reference-indicator.md) | `npm run shots`; [evidence-story-06.md](./evidence-story-06.md) |
| HS-40-05 | Dictation + meeting activity mapping | implemented in `/tmp` | [story-05-dictation-meeting-activity-mapping.md](./story-05-dictation-meeting-activity-mapping.md) | `tests/unit/test_web_runtime.py` |
| HS-40-06 | Desktop + web verification | done | [story-06-desktop-web-verification.md](./story-06-desktop-web-verification.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-40-07 | Closeout + final-summary | done | [story-07-closeout.md](./story-07-closeout.md) | [final-summary.md](./final-summary.md) |

## Where We Are

This is a planning scaffold only. Recon found the right seams: `WebRuntime`
already owns `runtime_status["voice_state"]`, transcription loading state,
last transcription/error, the shared `VoiceTypingSession` floor, meeting
lifecycle callbacks, and the `MeetingWebServer.broadcast(...)` websocket.
The dashboard already consumes `/api/runtime/status`, `/api/state`, and live
messages in `web/src/scripts/dashboard-app.js`. The desktop host should not
invent its own state path; it should subscribe to the same local status API.

Implementation is in `/tmp` rather than the live checkout. The shared runtime
activity contract, websocket broadcast, optional desktop host, transient-window
policy runner, renderer view model, compact optional Tk window, web dashboard
presence card, and dictation/meeting mapping are now present in the temp
worktree. HS-40-06 has automated evidence: full non-metal pytest, focused
unit/doc tests, ruff, Python compile, CI-safe desktop renderer-view fixture,
Astro build, and browser screenshots for the runtime dashboard on desktop and
mobile. After installing `python-tk@3.13`, interactive Tk smoke completed, a
frontmost-app focus smoke kept `Terminal` active before/after the transient
window cycle, and `scripts/desktop_presence_shots.py` captured native
per-state PNGs plus a contact sheet. The remaining live-merge work is applying
the temp changes after Phase 39's dirty work is resolved.

## Active Risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Desktop host adds heavy or fragile GUI dependencies to every install | Medium | Keep GUI deps optional; runtime degrades to web-only when unavailable | `holdspeak` cannot start on a headless/server install |
| Native window behavior differs too much across macOS/Linux desktops | Medium | Test a small fixed set of behaviors: show/update/hide/focus-safe; document fallback | One platform cannot show a non-disruptive transient window |
| Native window accidentally becomes a persistent idle widget | Medium | Treat `idle` as hidden in the renderer contract and test show→linger→hide sequences | A window remains visible after dictation/meeting activity resolves |
| Presence UI duplicates existing meeting/intel chips instead of clarifying them | Medium | Start with a single normalized state model; audit current labels before adding new ones | Users see two conflicting statuses for the same action |
| Hotkey press/release status is not observable enough from current callbacks | Medium | Add small status transitions in `WebRuntime` around existing begin/end/transcribe paths; avoid touching audio internals unless required | The UI cannot distinguish held/listening from transcribing |
| Websocket-only state misses reload/reconnect cases | Low-Med | Keep `/api/runtime/status` as the source of truth; websocket is an update path | Refresh shows stale/incorrect presence |
| UI motion becomes distracting | Low | Animate only the dot/ring, respect reduced motion, keep dimensions stable | Screenshot review shows layout shift or excessive pulsing |
| Phase 39 overlaps dictation telemetry changes | Medium | Treat Phase 39 telemetry as optional input; HS-40-01 owns the presence contract only | HS-40 needs Phase 39 unfinished code to pass tests |

## Decisions Made (This Phase)

- 2026-06-05 — Proposal keeps the **web runtime as the state owner**, but adds
  a **desktop presence host** — the user wants native-like macOS/Linux windows
  for background voice typing, not only in-page indicators.
- 2026-06-05 — Do **not revive the old menubar/TUI** — HS-32 retired those
  interactive runtimes. This phase adds a small subscriber/renderer for
  presence, while `WebRuntime` remains the owner of capture, typing, meeting,
  websocket, and settings.
- 2026-06-05 — Native presence windows are **transient, not persistent** —
  user clarification. The renderer pops in for meaningful activity, updates
  while work is happening, lingers briefly on success/no-op/error, then
  hides/destroys itself. No idle always-on overlay.
- 2026-06-05 — Proposal keeps Phase 40 **separate from active Phase 39** —
  the live checkout is already on `phase-39/hs-39-01-multi-pass-rewriting`
  with uncommitted work, so this exploratory scaffold lives in `/tmp`.
- 2026-06-05 — Presence state is **runtime state, not durable telemetry** —
  this keeps the first pass lightweight and avoids DB churn.

## Decisions Deferred

- **Desktop toolkit choice?** Trigger: HS-40-02 implementation. Default:
  choose the smallest optional dependency that can show a focus-safe transient
  window on macOS and Linux; if no acceptable single toolkit exists, implement
  a platform adapter boundary and ship one platform first with the other
  documented as blocked.
- **Tray icon?** Trigger: users need a persistent affordance to reopen the
  dashboard or pause indicators. Default: out of scope for Phase 40 unless the
  chosen desktop toolkit makes it nearly free.
- **Audio level meters?** Trigger: user wants visual VU feedback for mic/system
  input. Default: phase shows activity states first, not real-time waveform
  metering.
- **Persistent activity history?** Trigger: users ask "what happened to my
  last dictation?" after reload/restart. Default: only last runtime event and
  last transcription/error are kept.
