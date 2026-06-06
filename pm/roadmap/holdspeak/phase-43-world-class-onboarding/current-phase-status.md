# Phase 43 — World-Class Onboarding & First-Run UX

**Status:** CLOSED ✅ (6/6). Opened 2026-06-06. On direct user feedback that the
Phase-42 first-run UX, while functional, is **not world-class** — "boring cards
with an accent on the left", a status checklist instead of a real **wizard**, a
settings **form dump**, and — worst — desktop presence gated behind an **env
var** (`HOLDSPEAK_DESKTOP_PRESENCE=1`) with no UI toggle.

**Direction (user):** *Full world-class first-run* + *build your best* (iterate on
screenshots, no mockup gate). Phase 42 built the **plumbing** (`/api/setup/status`,
the `first_run` milestone, the live magic-moment, the trust data) — Phase 43 is
the **world-class UX layer** on those bones, not a rewrite.

**Last updated:** 2026-06-06 (phase opened; design direction pulled from the
`ui-ux-pro-max` skill — Funnel/progressive disclosure, one thing per step, Step
N-of-M, Skip+Back user freedom, focus-to-heading on transition, 150–300ms
ease-out motion + reduced-motion, SVG-not-emoji, minimal Signal glow for the
reward moment).

## Goal

Replace the boring-checklist first run with a **genuinely delightful, full-screen
step-by-step wizard**, make **desktop presence a one-click UI toggle** (kill the
env var as the path), **redesign Settings** (sectioned/searchable/progressive),
and establish a **richer component language** beyond the one left-accent-card
motif. World-class, not competent.

## Non-negotiable invariants

- **The Phase-42 plumbing is reused, not rewritten** — the wizard is driven by the
  same `/api/setup/status` + the `first_run` milestone + the `runtime_activity` WS.
- **Local-first + byte-identical** with everything off; the default suite makes no
  real network/LLM call; 0 `_built/` tracked.
- **Accessibility is not optional** — visible focus, focus-to-heading on step
  change, `prefers-reduced-motion`, SVG glyphs (no emoji as structural icons),
  Skip/Back on every step.

## Scope

### In
- A full-screen **first-run wizard** (`/welcome`) — Welcome → Permissions →
  Model → First dictation → Presence → Done — distinct visual treatment per step,
  real motion, a celebratory first-dictation reward (HS-43-01/02/03).
- **Presence as a config-backed UI toggle** — a `config.presence` field + a real
  switch that enables it (env var demoted to a power-user override) (HS-43-04).
- **Settings, redesigned** — sectioned nav, search, Common/Advanced progressive
  disclosure, inline help (HS-43-05).
- **Closeout** — docs, dogfood, screenshots, PR (HS-43-06).

### Out
- New backend intelligence; new dictation features.
- Removing `/setup` (it stays as the returning-user "needs attention" surface; the
  wizard is the *first-run* takeover).

## Exit criteria (evidence required)
- [ ] A full-screen wizard replaces the first-run checklist; one thing per step;
      Step N-of-M; Skip/Back; focus-to-heading; reduced-motion safe.
- [ ] The first-dictation step is a real **reward** moment (celebration, the
      transcript revealed), reduced-motion safe.
- [ ] Desktop presence is a **UI toggle** (config-backed); the env var is no longer
      the only path; proven by a test + a screenshot.
- [ ] Settings is sectioned/searchable/progressive — no single-scroll form dump.
- [ ] A richer component language is visible (distinct per-step treatments, not the
      one left-accent card).
- [ ] All optional off ⇒ local-first + byte-identical; suite green; 0 `_built/`.
- [ ] Docs + dogfood + `final-summary.md`; PR opened/merged.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-43-01 | Wizard shell + motion + a11y (Welcome) | done | [story-01-wizard-shell.md](./story-01-wizard-shell.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-43-02 | Permissions + Model steps | done | [story-02-permissions-model.md](./story-02-permissions-model.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-43-03 | First-dictation reward + Done | done | [story-03-first-dictation-reward.md](./story-03-first-dictation-reward.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-43-04 | Presence as a UI toggle (kill the env var) | done | [story-04-presence-toggle.md](./story-04-presence-toggle.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-43-05 | Settings redesign | done | [story-05-settings-redesign.md](./story-05-settings-redesign.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-43-06 | Closeout (docs + dogfood + PR) | done | [story-06-closeout.md](./story-06-closeout.md) | [evidence-story-06.md](./evidence-story-06.md) |

## Where we are

**Phase opened 2026-06-06**, branched `phase-43-world-class-onboarding` off `main`
(post Phase-42 merge, PR #20). Design direction taken from the `ui-ux-pro-max`
skill. **HS-43-01** (the wizard shell — full-screen takeover, the step-progress
rail, directional motion, focus management, and the Welcome step) is the entry
point and the first visible proof of the new aesthetic. **HS-43-04 shipped (2026-06-06, prioritized on user ask — "especially kill that env var"):** desktop presence is now a **config-backed one-click UI toggle** — `PresenceConfig.enabled` + `config.presence`, `desktop_presence_enabled(config_enabled=…)` (config OR the demoted env override), a `_sync_desktop_presence()` that **starts/stops the host live** on a settings change (no relaunch), the `/api/settings` PUT reconstructs `presence`, and the wizard Presence step is a real switch + a lit HUD preview that PUTs the flag. Proven live (toggle → `config.presence.enabled: True` on disk) + 7 tests. The env var is gone as the path. **HS-43-03 shipped (2026-06-06):** the first-dictation **reward moment** — a live mic target whose concentric rings ripple in the accent (keyed off the `runtime_activity` WS), the **actual configured hotkey** in a `<kbd>` (read from `/api/settings`), and on a real `dictation_typed` a celebration: a green check-burst + sparks, "It worked." in display type, and the transcript revealed in a quote. Reduced-motion safe; focus moves to the win heading. Two screenshots (live ripple + the win). **HS-43-02 shipped (2026-06-06):** the Model step is a real selectable **radiogroup** of the four backends (Basic / Apple MLX / GGUF / OpenAI-compatible) — selecting one persists via `/api/settings` (pipeline + backend), with a one-click **Test my runtime** (reusing HS-42-06's endpoint) + the copyable install. **Every wizard step is now real (no placeholders).** **HS-43-05 shipped (2026-06-06):** the Settings **form dump** is retired — `/settings` is sectioned (a sticky left-nav: Appearance · Voice typing · Desktop presence · Meetings & intel · Cloud & advanced), **searchable** (typing flattens to matching fields via per-field keywords), and **progressive** (a Common/Advanced disclosure), with the **config-backed presence toggle** living in it. Same `/api/settings` contract; save round-trip proven live (+ presence → disk); pure `fieldVisible` view-model + a test. **HS-43-06 — Phase 43 CLOSED ✅ (6/6):** the wizard is now the first-run path (the `/` guard sends first-run users to `/welcome`; the CLI nudge + Getting Started lead with it), proven by `scripts/dogfood_wizard.py` → **WIZARD DOGFOOD OK** (fresh `/` → wizard → GGUF select → "It worked" → presence toggle (no env var) → dashboard, **zero file edits**); before/after captured; suite **2319/16**; `final-summary.md`. Branch `phase-43-world-class-onboarding` — open a PR to `main`.

## Decisions made (this phase)
- **Full world-class first-run** in one phase (user) + **build-your-best**, iterate
  on screenshots (no mockup-approval gate).
- The wizard is a **separate full-screen route** (`/welcome`), not a re-skin of the
  `/setup` dashboard — `/setup` stays as the returning-user status surface.
- Presence becomes **config-backed** with a UI toggle; the env var is demoted to an
  override, not removed (power users + headless).
