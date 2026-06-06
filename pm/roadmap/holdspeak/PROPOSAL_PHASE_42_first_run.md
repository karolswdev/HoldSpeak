# Proposal — Phase 42 — First-Run Delight & Daily Confidence

**Prepared:** 2026-06-06
**Repo state reviewed:** `main` through Phase 41 (Runtime Presence Indicators) merge.
**Status:** proposal (not yet a phase folder). Claims below were verified against
the live code — see *Grounding* at the end.
**Primary lens:** make HoldSpeak feel like a polished personal tool in the first
ten minutes, then stay reassuring during daily use.

---

## Executive recommendation

The area that most needs care is **arrival** — the first-run and setup-confidence
loop — not another deep capability.

HoldSpeak now has the hard parts: real voice typing, meeting intelligence, plugin
artifacts, actuators, persistent dictation memory, a serious web runtime, and
native desktop presence on macOS/Linux. The remaining user-facing weakness is that
a new or returning user must still assemble the product mentally from docs,
`holdspeak doctor`, several web tabs, optional extras, environment flags, model
setup, OS permissions, and the local-first trust posture.

That is the wrong shape for a product that should feel like a marvel. The marvel is:

> I install it, it opens, it tells me exactly what is ready, it fixes what it can,
> it gives me one safe path to a verified first dictation, and it always tells me
> what's happening and what can leave my machine.

This phase is built around a single, **measurable** product promise.

### The promise (and the bar)

> **A user goes from fresh clone to a verified first dictation — with visible
> privacy/trust state and zero file editing — inside one guided local cockpit.**

**Stellar is measurable.** The phase headline is a captured
**time-to-first-successful-dictation (TTFD)** on a fresh clone, zero file edits,
on both macOS and Linux — the Phase-42 equivalent of the before/after headline that
anchored Phases 36 and 39. Target: **under 10 minutes, ≤ 1 primary action per
screen**, with the deterministic legs proven in CI and the real-app leg captured as
a dogfood.

---

## Why this is the highest-value work now

### 1. Product depth is ahead of the product entrance

Verified in the repo:

- `/dictation` opens to the **Blocks** tab — an expert authoring surface — as the
  first thing a newcomer sees (`web/src/scripts/dictation-app.js:13`,
  `activeSection: "blocks"`). The "Readiness" tab exists but isn't the landing.
- `web/src/layouts/AppLayout.astro:89` still ships an **interim Settings drawer**:
  *"Global settings are consolidating here… The full move from History → Settings
  lands in HS-30-08."* There is **no real `/settings` route**. That's live product
  debt now, not just IA debt.
- There is **no** setup / welcome / onboarding surface. The dashboard
  (`web/src/pages/index.astro`) shows meeting UI at idle — no "needs attention."
- The runtime cockpit exposes many knobs (backend, model path, OpenAI-compatible
  endpoint, target profile, latency budget, rewrite passes, correction memory,
  detection threshold). Powerful, but expert-shaped on entry.
- Phase 41 added excellent desktop presence — but it's opt-in via
  `HOLDSPEAK_DESKTOP_PRESENCE=1` + optional extras + platform caveats, i.e. invisible
  unless you already know to look.

None of these are bad alone. Together they make HoldSpeak feel like a highly capable
**workshop** rather than a finished daily **tool**.

### 2. Local-first trust needs a visible cockpit, not just docs

HoldSpeak's privacy posture is a core differentiator, and the code already treats
egress seriously — loopback bind + lazy auth token (`config.web_auth_token`),
`intel_egress_posture()`, connector permission manifests, actuator approval. But that
truth is scattered across `doctor`, docs, and several tabs. It should be **one calm,
ambient surface** inside the product (see the ambient trust chip in HS-42-05).

### 3. First success should be instrumented and honestly proven

The most important user moment is **not** "configured a model." It is:

> I held the key, spoke, released, and useful text appeared in **the app I meant to
> use**.

That last clause is the whole game — and it's why the first-success test cannot be a
textarea in our own browser tab. The guided flow proves the real path, with an honest
fallback ladder when a leg fails (see HS-42-04).

---

## Phase 42 — First-Run Delight & Daily Confidence

### Goal

Build a guided, web-first setup-and-confidence layer that takes a user from install
to **verified first dictation**, then gives them one trustworthy place to understand
runtime health, privacy/egress state, desktop presence, model readiness, and the next
action.

Product-facing. It adds **no new intelligence features**. It makes existing capability
feel coherent, safe, and delightful — and it deletes the interim-shell debt that makes
the product feel unfinished.

### Non-negotiable invariants

- **Reuse, don't duplicate.** `/api/setup/status` is an **adapter** over the existing
  structured sources (`collect_doctor_checks()`, `/api/dictation/readiness`,
  `intel_egress_posture()`, `detect_presence_platform()`), never a second doctor. A
  test asserts **every doctor `FAIL` surfaces as a setup section** so they can't drift.
- **Never nag a healthy user.** When setup is healthy, the welcome route yields to the
  dashboard instantly; setup-mode shows only on first run or `needs_attention`.
- **Local-first stays default + byte-identical.** With every optional feature off,
  behavior is unchanged. The setup status read is cheap — no large model loads, endpoint
  preflight is opt-in/time-boxed.

### What "first run" means (locked in HS-42-01)

A run is **first** when there's no persisted **first-success milestone** (preferred) or
no config file at all. The milestone is a single durable marker (cheap — there's already
a DB and repository pattern; a one-row `milestones`/`first_success` record). This makes
"first run" survive across the inevitable second launch, and lets a healthy returning
user skip straight to work.

---

## Scope

### In

- A **setup-state contract** (`GET /api/setup/status`) composing doctor checks,
  dictation readiness, runtime status, trust/egress posture, web bind/auth, and presence
  capability into one UI-friendly model — plus the `first_run` milestone.
- **Global settings completion** — finish the History → Settings migration into a real
  shell `/settings` surface and **delete the interim drawer copy**. (Sequenced early so
  later surfaces land on a finished shell, not more scaffolding.)
- A **Welcome / Setup** route (`/setup`, and `/` renders setup-mode when
  `needs_attention`) — functional, not marketing: status, one primary action, progress,
  deep links. Plus a **CLI nudge**: `holdspeak`'s first lines point at the setup URL
  using the same status data, so the terminal→browser handoff is seamless.
- A guided **First Dictation Test** that verifies the **real** path: mic → transcription
  → processing → insertion into an external app, with an honest clipboard/focused
  fallback ladder.
- A **Trust & Privacy** surface — a persistent, ambient **shell header chip**
  (local-only ▸ configured-endpoint ▸ writes-need-approval) that opens a full panel, so
  posture is always visible (mirroring the Phase-41 ambient philosophy).
- A **runtime model setup assistant** — guided backend/model choices with validation,
  copyable commands only when needed, and endpoint preflight; links into (does not hide)
  the advanced cockpit.
- **Presence onboarding** — make Phase-41 presence discoverable: availability + tier
  detection, an in-UI live preview, the focus invariant in one line, and the exact
  install command for `.[presence]` + Linux typelibs.
- A restrained **PixelLab setup-asset pass**: one strong character-building visual + tiny
  state icons only where they aid scanning. No mascot wall.
- **Evidence:** screenshots, setup-status unit/integration tests, a headless first-run
  API test, the deterministic transcription leg over the committed fixture WAV, and a
  real first-dictation dogfood with the TTFD measurement.

### Out

- New LLM features, plugins, actuator kinds, or connector packs.
- Turning desktop presence on by default.
- PyPI publish (a separate release story if/when wanted).
- Cloud sync, accounts, telemetry, crash reporting, remote onboarding.
- Rewriting the dictation cockpit — it stays; the first-run route guides users into it
  only when needed.

---

## Story plan (resequenced — shell before surfaces)

| ID | Story | Purpose |
|---|---|---|
| HS-42-01 | **Setup-state contract + `first_run` milestone** | One backend shape (`GET /api/setup/status`) composing doctor/readiness/runtime/egress/auth/presence; the durable first-success marker; the "no duplicate doctor" adapter + drift test. |
| HS-42-02 | **Global settings completion** | Finish History → Settings into a real `/settings` shell surface; delete the interim drawer copy + `#settings` indirection. Lands the clean shell the later surfaces sit in. |
| HS-42-03 | **Welcome / Setup route + CLI nudge** | Signal-styled first-run surface (`/setup`; `/` → setup-mode when `needs_attention`): status, one primary action, progress, deep links, one restrained PixelLab visual. CLI first-lines point at the setup URL. |
| HS-42-04 | **Guided first dictation test (real app)** | Prove mic→transcription→processing→insertion into an **external** app, with an honest clipboard/focused fallback ladder. Deterministic leg in CI via the fixture WAV; real-app leg as dogfood. |
| HS-42-05 | **Trust & Privacy — ambient chip + panel** | A persistent shell header posture chip (local-only/configured-endpoint/writes-need-approval) opening a full panel: bind/auth, intel local-vs-cloud, endpoints, connectors, actuators, file locations — in plain language. |
| HS-42-06 | **Runtime model setup assistant** | Guided basic/Apple-local/GGUF/OpenAI-compatible choices with validation + endpoint preflight + copyable commands; links into the advanced cockpit, never hides it. |
| HS-42-07 | **Presence onboarding** | Surface Phase-41 presence as a guided optional enhancement: availability + platform tier, live in-UI preview, focus invariant, exact install command. |
| HS-42-08 | **First-run evidence + docs closeout** | TTFD headline capture (macOS + Linux), screenshots, Getting Started/User Guide lead with the guided path, doc drift-guard + link-check, `final-summary.md`. |

**Stellar core (delivers the promise on its own):** HS-42-01 → 02 → 03 → 04. If energy
flags, 05/06/07 are stellar *depth* that could slip to a Phase 43 without breaking the
promise — but the chosen scope is all eight in one phase.

---

## Detailed recommendations

### HS-42-01 — Setup-state contract + `first_run` milestone

`GET /api/setup/status` returns a stable, UI-friendly model:

```json
{
  "overall": "ready|needs_attention|blocked",
  "first_run": true,
  "primary_action": { "id": "grant_mic_permission",
                      "label": "Enable microphone access",
                      "route": "/setup#microphone" },
  "sections": [
    { "id": "microphone", "label": "Microphone",
      "status": "pass|warn|fail|unknown",
      "detail": "Default input: MacBook Pro Microphone",
      "fix": "System Settings → Privacy & Security → Microphone" }
  ],
  "trust": {
    "web_bind": "127.0.0.1", "auth_token_set": true,
    "transcript_egress": "none|configured|possible",
    "configured_endpoints": [], "actuators_enabled": false,
    "connectors_enabled": []
  },
  "presence": { "enabled": false, "available": true,
                "tier": "hud|notification|tray|none", "reason": null }
}
```

Implementation guidance:

- **Adapter, not a reimplementation.** Compose `collect_doctor_checks()` (already a
  structured `list[DoctorCheck(name,status,detail,fix)]`), `/api/dictation/readiness`,
  `intel_egress_posture()`, and `detect_presence_platform()`. Keep check IDs stable.
- **The drift invariant:** a test asserts every doctor `FAIL` maps to a setup section —
  the doctor stays the single source of check truth.
- **`first_run`** = absence of the durable first-success milestone (preferred) or no
  config file. Add a one-row durable marker via the existing repository pattern.
- **Cheap by default.** No large LLM loads; endpoint preflight opt-in/time-boxed.

Evidence: unit tests for status composition + the doctor-FAIL→section drift test;
integration test for the route; ready/blocked snapshot fixtures.

### HS-42-02 — Global settings completion

Concrete debt retirement, sequenced **before** the new surfaces so they sit on a clean
shell.

- Move global settings into a real `/settings` route (and/or the shell drawer) opened
  from the gear; keep page-local settings where they're truly page-local.
- **Delete** the `AppLayout.astro` "consolidating / History → Settings" copy; keep
  `#settings` working or replace it with a stable route.
- Guard: `rg "History → Settings|consolidating|HS-30-08"` returns nothing in live product
  (frozen PMO history excluded).

Evidence: settings route/drawer screenshot; entry integration test; the `rg` guard.

### HS-42-03 — Welcome / Setup route + CLI nudge

- `/` renders **setup-mode** when `needs_attention`; `/setup` is the addressable
  full-checklist deep link. A healthy user never sees a wall; a blocked user can't miss it.
- Top line: "Ready for voice typing" or "3 things need attention." Exactly **one** primary
  action. Checklist: Microphone, Hotkey, Text insertion, Transcription, Web runtime,
  Model/runtime, Privacy, Presence. "Try first dictation" becomes primary only when the
  core path is ready. A local-only badge near every setup flow.
- **CLI nudge:** `holdspeak`'s first terminal lines use the same setup-status data —
  e.g. `Open http://127.0.0.1:PORT/setup — 3 things need attention` — so the
  terminal→browser handoff is seamless (onboarding starts before the browser opens).
- One restrained PixelLab visual (a HoldSpeak operator at a terminal with a mic/hotkey
  signal, or a compact "local cockpit" scene). No marketing hero, no field wall, no raw
  doctor dump, no decorative overload.

Evidence: desktop + mobile screenshots; empty/fail/ready states; PixelLab provenance in
`docs/assets/pixellab/README.md`; a focus-order/contrast a11y check.

### HS-42-04 — Guided first dictation test (real app)

The phase's beating heart. Two honest legs:

- **(a) Deterministic leg (CI-provable):** mic→transcription→processing over the committed
  `tests/fixtures/core_path_smoke_16k.wav`, shown in-UI (transcript → processed output).
- **(b) Real-app leg (the magic moment):** "Focus your editor and hold the key" → record →
  insert → a detectable confirmation. This proves text lands in **another** app, not our
  textarea.

Honest fallback ladder: hotkey fails on Wayland → focused fallback; synthetic typing
fails → clipboard/manual paste (framed as a supported mode, not a failure); backend
unavailable → route to model setup; mic permission missing → OS-specific instructions.

Evidence: fixture-WAV test for leg (a); leg (b) as a manual dogfood frame on macOS or
Linux; the TTFD timing starts here.

### HS-42-05 — Trust & Privacy — ambient chip + panel

Posture should be **ambient**, like presence — not a page you remember to visit.

- A persistent **shell header chip**: `Local only` / `Configured endpoint` /
  `Writes need approval` / `Needs attention`, color-keyed, opening the full panel.
- The panel answers, in plain language: is the runtime loopback-only? is the auth token
  set? is meeting intel local/cloud/disabled? which OpenAI-compatible endpoint is
  configured? which connector packs are enabled? are actuators enabled, and which can
  write externally? what can leave the machine right now? where do DB/config/`.hs` files
  live? Layered disclosure — summary first, details expandable.

Evidence: tests for the status mapping (local/cloud/actuator/connector); screenshots of
default local-only and configured-endpoint states.

### HS-42-06 — Runtime model setup assistant

Guided choices — **Basic voice typing only · Local Apple Silicon · Local GGUF/llama.cpp ·
OpenAI-compatible endpoint** — each showing the required extra, the model path/endpoint,
whether it affects dictation/intel/both, a Test button with a clear result, and copyable
commands only when needed. Links into the advanced Runtime cockpit; never removes the
advanced fields.

Evidence: validation + endpoint-preflight-failure tests; a screenshot per backend choice.

### HS-42-07 — Presence onboarding

Phase 41 made presence strong; make it discoverable. Detect availability + whether the
extras are installed; preview the presence card in-UI; explain the tier (macOS/X11/wlroots
→ floating HUD; Wayland GNOME/KDE → tray + notification) honestly via the Phase-41
detector; the focus invariant in one line; the exact `.[presence]` + Linux typelib
commands when missing.

Evidence: platform/tier display-mapping tests; default-off and active/available screenshots.

### HS-42-08 — First-run evidence + docs closeout

Docs lead with: install → launch → open Setup → complete first dictation → then choose
intelligent typing / meeting / presence / companion. Hand-edited JSON/YAML stops being
the primary path. The **TTFD headline** (measured, macOS + Linux, zero file edits) is the
closeout demo.

Evidence: link-check + doc drift-guard; embedded screenshots; PixelLab provenance;
`final-summary.md`; full/scoped suite + named unrun hardware tests.

---

## UX principles

1. **One primary action per state.** Blocked → show the next fix, not every setting.
2. **No mystery states.** Listening / transcribing / typing / fallback / cloud-capable /
   local-only must be visible.
3. **Plain trust language.** "This transcript can be sent to http://…" beats abstract
   security copy.
4. **Respect the expert.** Keep advanced knobs; don't lead with them.
5. **Reward first success.** The first successful dictation visibly closes the loop.
6. **Make fallback feel intentional**, not like a failure.
7. **Don't over-decorate.** Polish comes from responsiveness, clarity, and calm status.

---

## Acceptance criteria

- [ ] A fresh launch exposes setup-mode (or `/setup`) without requiring docs; a **healthy
      returning user is not nagged** (route yields to the dashboard).
- [ ] `GET /api/setup/status` composes core checks, runtime readiness, trust posture, and
      presence availability, and is an **adapter over `collect_doctor_checks()`** — a test
      proves every doctor `FAIL` surfaces as a setup section.
- [ ] `first_run` is backed by a durable first-success milestone (survives relaunch).
- [ ] A guided first-dictation test proves the **real external-app** path (deterministic
      leg in CI; real-app leg dogfooded) with pass/fail/remediation.
- [ ] Privacy/egress state is visible **ambiently** (shell chip) without opening
      `docs/SECURITY.md`.
- [ ] Global settings live at a real surface; **no live copy says "consolidating" or
      "History → Settings."**
- [ ] Runtime model setup has guided paths for basic/local/GGUF/OpenAI-compatible; the
      advanced cockpit remains.
- [ ] Desktop presence is discoverable and accurately tiered by platform.
- [ ] Restrained PixelLab treatment: one primary visual + supporting state icons only.
- [ ] With all optional features off, default behavior is local-first and byte-identical.
- [ ] **TTFD measured and captured** (fresh clone, zero file edits, macOS + Linux) as the
      closeout headline; evidence includes screenshots, setup-status tests, docs updates,
      and `final-summary.md`.

---

## Verification plan

Backend (existing):

```bash
uv run pytest -q tests/unit/test_doctor_command.py \
  tests/integration/test_web_dictation_readiness_api.py \
  tests/integration/test_web_dictation_settings_api.py
```

New (expected):

```bash
uv run pytest -q tests/unit/test_setup_status.py            # composition + first_run
uv run pytest -q tests/unit/test_setup_status_doctor_drift.py  # every FAIL → a section
uv run pytest -q tests/integration/test_web_setup_status_api.py
uv run pytest -q tests/integration/test_web_setup_route.py
uv run pytest -q tests/unit/test_trust_posture_view_model.py
```

Frontend:

```bash
cd web && npm run build && npm run shots
```

Closeout:

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py
```

Hardware/manual: real mic + OS permission flows stay manual/hardware-gated where CI can't
prove them; the fixture WAV covers the deterministic transcription leg; capture at least
one real first-dictation dogfood (with the TTFD stopwatch) on macOS or Linux.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Setup API becomes a second doctor | `/api/setup/status` is an adapter over `collect_doctor_checks()`; a drift test asserts every FAIL surfaces. |
| First-run route turns into a marketing page | Keep it a tool surface: checklist, status, one next action, the test flow. |
| Trust panel overwhelms with security detail | Ambient chip + layered disclosure (summary first, details expandable). |
| Model assistant hides expert controls | It links into the existing Runtime cockpit; advanced fields stay. |
| Presence onboarding over-promises on Wayland | Use the Phase-41 platform detector; show tier honestly. |
| Healthy users get nagged | `first_run` milestone + `needs_attention` gating; route yields to the dashboard. |
| Phase too broad (all eight) | Ship in story order; 01→04 is the stellar core that already delivers the promise; 05–07 are depth. |

---

## Grounding (claims verified against the code, 2026-06-06)

- `/dictation` defaults to **Blocks** — `web/src/scripts/dictation-app.js:13`,
  `web/src/pages/dictation.astro:26`. Tabs: Readiness, Blocks, Project KB, Project Context,
  Agent Hooks, Runtime, Memory, Dry-run.
- Interim Settings drawer + "History → Settings / consolidating / HS-30-08" copy live at
  `web/src/layouts/AppLayout.astro:89`; `#settings` deep-link at line 146; **no** real
  `/settings` page.
- No setup/welcome/onboarding page exists; pages are activity, companion, design/*,
  dictation, docs/dictation-runtime, history, index, presence. Dashboard shows meeting UI
  at idle (no "needs attention").
- Reusable data confirmed: `holdspeak/commands/doctor.py` —
  `DoctorCheck(name,status,detail,fix)` + `collect_doctor_checks() -> list[DoctorCheck]`
  (25 checks); `GET /api/dictation/readiness` in `holdspeak/web/routes/dictation/pipeline.py`;
  `intel_egress_posture()` in `holdspeak/intel/providers.py` (surfaced via
  `web_runtime._intel_egress_payload()`).
- Fixture WAV: `tests/fixtures/core_path_smoke_16k.wav` (HS-32-04 core-path smoke).
- Trust config in `holdspeak/config.py`: `web_auth_token`, `intel_enabled`/`intel_provider`,
  `intel_cloud_*`, `LLMRuntimeConfig.backend`/`openai_compatible_base_url`, `allow_actuators`,
  `allowed_actuators`, `webhook_allowed_hosts`.

---

## Final position

HoldSpeak's core is now strong enough that the biggest remaining product risk isn't
capability — it's **arrival**. If Phase 42 lands as described, the app stops asking users
to understand its architecture before they experience its value, and the privacy posture
that makes it special becomes something you can *see*, not just read. That is the right
care to take now.
