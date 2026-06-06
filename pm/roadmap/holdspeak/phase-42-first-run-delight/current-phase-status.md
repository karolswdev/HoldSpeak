# Phase 42 — First-Run Delight & Daily Confidence

**Status:** IN PROGRESS (4/8 stories). Opened 2026-06-06. Direction chosen by the
user: the product depth is now ahead of the product **entrance** — make
**arrival** stellar. A user should go from fresh clone to a verified first
dictation, with visible privacy/trust state and **zero file editing**, inside one
guided local cockpit.

**Last updated:** 2026-06-06 (**HS-42-04 done** — the magic-moment proof: a
guided `/setup` first-dictation panel (steps + readiness row + **live WS
feedback** → "✓ It worked, text landed in your app" + transcript on a real
dictation) + a fallback ladder, and the durable `FIRST_DICTATION_SUCCESS`
milestone set at the real dictation-success points (`first_run` flips false, `/`
stops nagging). 3 milestone tests + a live Playwright magic-moment + 3
screenshots; suite **2294/16**. **HS-42-03 done** — the welcome/setup surface: a
Signal `/setup` page driven by `/api/setup/status` (brand-mark hero + dynamic
headline + progress + one primary action + needs-attention list + ready grid +
Privacy/Presence cards), a `/` first-run guard (redirect to `/setup` only when
`first_run|blocked` — never nag a healthy user), and a CLI launch nudge. Proven
live; +5 tests; suite **2291/16**. **HS-42-02 done** — the interim
"consolidating / History → Settings" drawer retired into a real shell-level
**`/settings`** page (Signal cards + sticky save bar); gear→`/settings`; History
settings tab removed; server route serves the built page; save round-trip proven
live; +3 tests, 3 settings-as-tab tests updated in lockstep. **HS-42-01 done** —
the setup-state contract + `first_run` milestone.
`holdspeak/setup_status.py::build_setup_status` composes
one `GET /api/setup/status` snapshot as an **adapter** over the existing sources
(`collect_doctor_checks()` 1:1 → sections; `intel_egress_posture()` + config →
trust; `detect_presence_platform()` → presence) with a single `primary_action`
and `overall` verdict; cheap by construction (doctor gained `skip_network=True`,
so the cloud preflight is a neutral "not run" instead of a 4s HTTP probe — the
CLI keeps the live preflight). The durable `first_run` is a new `milestones`
table + `MilestoneRepository` (`db.milestones`); it survives a restart (canonical
schema snapshot regenerated). Route `build_setup_router` registered.
**+22 tests** (composition / drift-guard "every FAIL surfaces" / route shape /
milestone persist-across-restart / cheapness); full suite **2283 passed, 16
skipped**; new files ruff-clean. Next: **HS-42-02** (global settings completion).
Phase opened + scaffolded off the reviewed, repo-grounded proposal
[`PROPOSAL_PHASE_42_first_run.md`](../PROPOSAL_PHASE_42_first_run.md).)

## Goal

Build a guided, web-first setup-and-confidence layer that takes a user from
install to **verified first dictation**, then gives them one trustworthy place to
understand runtime health, privacy/egress state, desktop presence, model
readiness, and the next action. Product-facing: **no new intelligence features** —
it makes existing capability feel coherent, safe, and delightful, and it deletes
the interim-shell debt that makes the product feel unfinished.

### The promise (measurable)

> A user goes from fresh clone to a verified first dictation — with visible
> privacy/trust state and **zero file editing** — inside one guided local cockpit.

**Stellar is measurable.** The phase headline is a captured
**time-to-first-successful-dictation (TTFD)** on a fresh clone, zero file edits,
on both macOS and Linux — the Phase-42 equivalent of the before/after that
anchored Phases 36 and 39. Target: **under 10 minutes, ≤ 1 primary action per
screen**, deterministic legs proven in CI, the real-app leg captured as a dogfood.

## Non-negotiable invariants

- **Reuse, don't duplicate.** `/api/setup/status` is an **adapter** over the
  existing structured sources — `collect_doctor_checks()` (already a
  `list[DoctorCheck]`), `GET /api/dictation/readiness`, `intel_egress_posture()`,
  `detect_presence_platform()` — never a second doctor. A test asserts **every
  doctor `FAIL` surfaces as a setup section** so they can't drift.
- **Never nag a healthy user.** When setup is healthy the welcome route yields to
  the dashboard instantly; setup-mode shows only on first run or `needs_attention`.
- **Local-first stays default + byte-identical.** Every optional feature off ⇒
  behavior unchanged. The status read is cheap (no large model loads; endpoint
  preflight is opt-in/time-boxed).

## What "first run" means

A run is **first** when there's no persisted **first-success milestone**
(preferred) or no config file. The milestone is a single durable marker (the DB +
repository pattern already exists), so "first run" survives the inevitable second
launch and a healthy returning user skips straight to work.

## Scope

### In

- The **setup-state contract** (`GET /api/setup/status`) + the `first_run`
  milestone (HS-42-01).
- **Global settings completion** — finish History → Settings into a real
  `/settings` surface; delete the interim drawer copy (HS-42-02).
- The **Welcome / Setup** route (`/setup`; `/` → setup-mode when
  `needs_attention`) + a **CLI nudge** (HS-42-03).
- The guided **First Dictation Test** proving the **real external-app** path with
  an honest fallback ladder (HS-42-04).
- The **Trust & Privacy** ambient shell chip + panel (HS-42-05).
- The **runtime model setup assistant** (HS-42-06).
- **Presence onboarding** (HS-42-07).
- **Evidence + docs closeout** with the TTFD headline (HS-42-08).
- A restrained **PixelLab setup-asset pass** (one strong visual + tiny state
  icons), woven through 03/08.

### Out

- New LLM features, plugins, actuator kinds, or connector packs.
- Turning desktop presence on by default.
- PyPI publish (a separate release story if/when wanted).
- Cloud sync, accounts, telemetry, crash reporting, remote onboarding.
- Rewriting the dictation cockpit — it stays; the first-run route guides users
  into it only when needed.

## Exit criteria (evidence required)

- [ ] Fresh launch exposes setup-mode (or `/setup`) without docs; a healthy
      returning user is **not** nagged (route yields to the dashboard).
- [ ] `GET /api/setup/status` composes core checks + readiness + trust + presence
      and is an **adapter over `collect_doctor_checks()`** — a test proves every
      doctor `FAIL` surfaces as a setup section.
- [ ] `first_run` is backed by a durable first-success milestone (survives relaunch).
- [ ] A guided first-dictation test proves the **real external-app** path
      (deterministic leg in CI; real-app leg dogfooded) with pass/fail/remediation.
- [ ] Privacy/egress state is visible **ambiently** (shell chip), not doc-only.
- [ ] Global settings live at a real surface; **no live copy says "consolidating"
      or "History → Settings."**
- [ ] Runtime model setup has guided basic/local/GGUF/OpenAI-compatible paths; the
      advanced cockpit remains.
- [ ] Desktop presence is discoverable and accurately tiered per platform.
- [ ] Restrained PixelLab treatment (one primary visual + supporting icons only).
- [ ] All optional features off ⇒ default local-first + byte-identical.
- [ ] **TTFD measured + captured** (fresh clone, zero file edits, macOS + Linux) as
      the closeout headline; screenshots + setup-status tests + docs + `final-summary.md`.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-42-01 | Setup-state contract + `first_run` milestone | done | [story-01-setup-state-contract.md](./story-01-setup-state-contract.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-42-02 | Global settings completion | done | [story-02-global-settings-completion.md](./story-02-global-settings-completion.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-42-03 | Welcome / Setup route + CLI nudge | done | [story-03-welcome-setup-route.md](./story-03-welcome-setup-route.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-42-04 | Guided first dictation test (real app) | done | [story-04-guided-first-dictation.md](./story-04-guided-first-dictation.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-42-05 | Trust & Privacy — ambient chip + panel | backlog | [story-05-trust-privacy-panel.md](./story-05-trust-privacy-panel.md) | — |
| HS-42-06 | Runtime model setup assistant | backlog | [story-06-runtime-model-assistant.md](./story-06-runtime-model-assistant.md) | — |
| HS-42-07 | Presence onboarding | backlog | [story-07-presence-onboarding.md](./story-07-presence-onboarding.md) | — |
| HS-42-08 | First-run evidence + docs closeout | backlog | [story-08-closeout-docs-evidence.md](./story-08-closeout-docs-evidence.md) | — |

## Where we are

**Phase opened 2026-06-06**, branched `phase-42-first-run-delight` off `main`
(post Phase-41 merge, PR #19). Scaffolded from the reviewed proposal — every
load-bearing claim was verified against the live code first (the `/dictation`
Blocks default, the `AppLayout` interim Settings drawer, the absence of any setup
surface, and the reusable `collect_doctor_checks()` / readiness / egress / presence
sources). Resequenced from the proposal so the shell debt (HS-42-02) is retired
**before** the new surfaces sit on it. **HS-42-01 shipped (2026-06-06)** — the
backend spine: `build_setup_status` (an adapter over the doctor/readiness/egress/
presence sources, cheap via `skip_network`), the durable `first_run` milestone
(`db.milestones`, survives restart), and `GET /api/setup/status`. +22 tests;
suite **2283/16**. **HS-42-02 shipped (2026-06-06)** — the interim
"consolidating / History → Settings" drawer is **retired** into a real,
shell-level **`/settings`** page (Signal cards: Appearance/Core/Cloud-intel,
local chip, sticky save bar), the gear links to it, the History settings tab is
removed (read-only `loadSettings` kept for the intel-alert getters), and the
server `/settings` route serves the built page. **Save round-trip proven live**
(set→save→reload→disk all 37) + a screenshot; +3 tests, 3 old settings-as-tab
tests updated in lockstep. **HS-42-03 shipped (2026-06-06)** — the first real
first-run surface: a Signal `/setup` welcome page (brand-mark hero + dynamic
headline + 20/22 progress + one bright **primary action** + a "Needs attention"
list + a first-dictation CTA + a "Ready" grid + Privacy/Presence cards), driven
by `/api/setup/status`; a `/` **first-run guard** (redirects to `/setup` only
when `first_run|blocked` — a healthy returning user keeps the dashboard); and a
**CLI launch nudge**. Proven live (Playwright redirect both ways + stdout
capture) + a screenshot; +5 tests; suite **2291/16**. **HS-42-04 shipped
(2026-06-06)** — the magic-moment proof: a guided `/setup` first-dictation panel
(3 steps + a readiness mini-row + **live `runtime_activity` WS feedback** that
flips to a green "✓ It worked — text landed in your app" + the transcript on a
real `dictation_typed`/`dictation_delivered`) + an honest fallback ladder; and
the durable **`FIRST_DICTATION_SUCCESS` milestone** set at the two real
dictation-success points in `_transcribe_and_type` (so `first_run` flips false
and `/` stops nagging). 3 milestone-wiring tests + a live Playwright magic-moment
+ 3 screenshots; suite **2294/16**. The real-mic leg is the HS-42-08 dogfood.
Next: **HS-42-05** (ambient trust chip + panel).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| `/api/setup/status` becomes a second doctor | Medium | Adapter over `collect_doctor_checks()`; a drift test asserts every FAIL surfaces | Check logic forks from the doctor |
| Healthy returning users get nagged by setup-mode | Medium | `first_run` milestone + `needs_attention` gating; route yields to the dashboard | A configured user lands on a checklist |
| Phase too broad (all eight) | Medium | Ship in story order; 01→04 is the stellar core that already delivers the promise; 05–07 are depth | Stories smear into a "polish" blob |
| First-success test proves the wrong surface | Medium | Real external-app leg is the centerpiece; the browser leg is honestly the deterministic half | "Verified" but only in our own textarea |
| PixelLab assets overwhelm a tool surface | Low | One primary visual + tiny state icons; no mascot wall | Decoration competes with the checklist |

## Decisions made (this phase)

- **All eight stories in one phase** (user, 2026-06-06) — over a "stellar core (4)
  now + depth (43)" split. The arrival story ships whole.
- **Shell before surfaces** — settings-completion resequenced to HS-42-02 so the
  welcome route + trust chip land on a finished shell.
- **Trust is ambient** — a persistent shell header chip (not a panel you must find),
  mirroring the Phase-41 ambient-presence philosophy.
- **`first_run` = a durable first-success milestone** (survives relaunch), not a
  per-process guess.

## Decisions deferred

- ~~**`/setup` route vs `/` setup-mode**~~ — **resolved HS-42-03:** `/setup` is
  the addressable full-checklist surface; `/` redirects to it only when
  `first_run|blocked` (a mere WARN does **not** redirect — never nag a healthy
  returning user).
- **Where the first-success milestone lives** (a `milestones` table vs reusing an
  existing repo) — trigger HS-42-01 — default: a small durable marker via the
  existing repository pattern.
- **Real-app first-success confirmation mechanism** (clipboard round-trip vs an
  in-app echo target) — trigger HS-42-04 — default: the most reliable
  platform-portable signal, chosen during the story.
