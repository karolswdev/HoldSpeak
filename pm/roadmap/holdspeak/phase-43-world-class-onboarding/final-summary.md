# Phase 43 — World-Class Onboarding & First-Run UX — Final Summary

- **Phase opened:** 2026-06-06
- **Phase closed:** 2026-06-06
- **Stories shipped:** 6 (HS-43-01 … HS-43-06)

## Goal — was it met?

On direct user feedback that the Phase-42 first-run, while functional, was **not
world-class** — "boring cards with an accent on the left," a status checklist
instead of a real wizard, a settings form dump, and — worst — desktop presence
behind an **env var** with no UI toggle.

**Yes — reimagined as a world-class layer on the Phase-42 plumbing** (no rewrite:
the same `/api/setup/status`, `first_run` milestone, `runtime_activity` WS, and
trust data drive it).

### The before / after

- **Before (Phase 42):** `pm/.../phase-42-first-run-delight/evidence/setup_page.png`
  — a flat checklist of identical left-accent cards.
- **After (Phase 43):** the full-screen **`/welcome` wizard** —
  `evidence/wizard_welcome.png` · `wizard_permissions.png` · `wizard_model.png` ·
  `wizard_dictation_live.png` · `wizard_dictation_win.png` · `wizard_presence.png`
  · `wizard_done.png` — plus the redesigned `settings_*.png`.

### Proven by a dogfood

```
1. fresh `/` -> /welcome
2. permissions: system check shown
3. model: selected GGUF -> config backend = 'llama_cpp'
4. first dictation: It worked. ('my first words in holdspeak')
5. presence: toggled on -> config.presence.enabled = True (no env var)
6. you're set: celebration shown
7. Open HoldSpeak -> dashboard
WIZARD DOGFOOD OK — fresh clone → guided wizard → first dictation, zero file edits
```

## What shipped (by story)

| Story | Outcome |
|---|---|
| HS-43-01 | The **wizard shell** — a full-screen `/welcome` takeover: a step-progress rail, funnel/one-step-at-a-time, directional motion (reduced-motion safe), Step N-of-M + Back/Skip, **focus-to-heading** a11y, SVG glyphs; a cinematic **Welcome**, a live **Permissions** system-check, a celebratory **Done**. (+ a fix: dynamic OS label, never "Mac"; meetings in the pitch.) |
| HS-43-02 | The **Model picker** — a `role="radiogroup"` of the four backends that persists via `/api/settings` + a one-click **Test** (HS-42-06 endpoint). Every wizard step is now real. |
| HS-43-03 | The **first-dictation reward** — a live mic-ripple ring keyed off the WS + the actual configured hotkey, then a **celebration** (check-burst + sparks + the transcript revealed) on a real dictation; reduced-motion safe. |
| HS-43-04 | **Presence is a config-backed UI toggle** — `config.presence.enabled`, `desktop_presence_enabled(config_enabled=…)` (config OR the demoted env override), a `_sync_desktop_presence()` that **starts/stops the HUD live** on a settings change. **The env var is dead as the path.** |
| HS-43-05 | **Settings redesigned** — the form dump → a sectioned left-nav + **search** + Common/Advanced progressive disclosure, with the presence toggle in it. |
| HS-43-06 | **Closeout** — the `/` guard sends a first-run user to the wizard (`/welcome`); the CLI nudge + docs lead with it; the dogfood; this summary; the PR. |

## Exit criteria — final state

- [x] A full-screen wizard replaces the checklist; one step at a time; Step N-of-M;
      Skip/Back; focus-to-heading; reduced-motion safe.
- [x] The first-dictation step is a real **reward** moment (celebration + transcript).
- [x] Desktop presence is a **UI toggle** (config-backed); the env var is no longer
      the only path; live start/stop; proven by tests + a screenshot.
- [x] Settings is sectioned/searchable/progressive — no form dump.
- [x] A richer component language is visible (distinct per-step treatments, a real
      switch, selection tiles, a celebration — not the one left-accent card).
- [x] All optional off ⇒ local-first + byte-identical; suite green; **0** `_built/`.
- [x] Docs + dogfood + `final-summary.md`; PR opened/merged.

## Verification

- Full suite **2319 passed, 16 skipped** at close (2317 at HS-43-01; +tests across
  the phase). Every story added committed tests; no real network/LLM call in the
  default suite; **0** `holdspeak/static/_built/` files tracked.

## Notes

- `/setup` (Phase 42) stays as the **returning-user status surface** (and the
  hard-blocked redirect target); `/welcome` is the **first-run takeover**.
- Design direction drawn from the `ui-ux-pro-max` skill (Funnel/progressive
  disclosure, Step N-of-M, Skip+Back, focus management, 150–300ms motion +
  reduced-motion, SVG-not-emoji, minimal Signal glow).
