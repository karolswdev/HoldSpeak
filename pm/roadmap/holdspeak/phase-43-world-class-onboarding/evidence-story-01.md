# Evidence — HS-43-01 — Wizard shell + Welcome

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-43-world-class-onboarding`
- **Owner:** unassigned

## What shipped

The boring first-run checklist is replaced by a **full-screen, step-by-step
wizard** at `/welcome` — the first proof of the new world-class aesthetic.

### The shell — `web/src/pages/welcome.astro` + `welcome-app.js`

- **Full-screen takeover** (not the AppLayout dashboard): a dark-OLED canvas with
  a radial accent glow, a left **progress rail** (Welcome → Permissions → Model →
  First dictation → Presence → You're set) with a connecting line, the active step
  glowing orange and completed steps a green check, and a "Local · 127.0.0.1 ·
  nothing leaves your machine" footer.
- **Funnel / one step at a time**, driven by the Phase-42 plumbing
  (`/api/setup/status` + the `runtime_activity` WS) — no backend rewrite.
- **Motion** — directional slide+fade between steps (forward/back), 300ms
  ease-out, fully `prefers-reduced-motion` safe (collapses to a fast crossfade).
- **Accessibility** — Step N-of-M, **Back + Skip** on every step (user freedom),
  **focus moves to the step heading** on each transition, visible focus rings,
  SVG glyphs (no emoji as structural icons).
- **Distinct treatment per step** (escape the one left-accent card): the **Welcome**
  step is cinematic — an animated soundwave glyph + a huge Space-Grotesk headline
  ("Hold a key. / Speak. / *Watch it type.*" with a glowing accent line) + a lead;
  the **Permissions** step is a live system check — status tiles (Microphone · Text
  insertion · Hotkey) that poll `/api/setup/status` and flip checking→green-Ready;
  the **Done** step is a celebratory check-burst.
- Server route `GET /welcome` (build-agnostic fallback).

Model / First-dictation / Presence steps are scaffolded placeholders, filled in by
HS-43-02 / 03 / 04.

## Verification

- **Live (Playwright) screenshots:**
  [`wizard_welcome.png`](./evidence/wizard_welcome.png) (the cinematic welcome),
  [`wizard_permissions.png`](./evidence/wizard_permissions.png) (the live system
  check — all green on this Mac, the rail showing Welcome done / Permissions
  active), [`wizard_done.png`](./evidence/wizard_done.png) (the celebratory close).

## Tests run

```
uv run pytest -q tests/integration/test_web_welcome_wizard.py     → 2 passed
```

- `test_welcome_route_serves_the_wizard` — `GET /welcome` 200, build-agnostic.
- `test_wizard_is_a_funnel_with_a11y_and_reduced_motion` — Step N-of-M, Back/Skip,
  focus-to-heading, `prefers-reduced-motion`, and the six steps.

Full suite: see the HS-43-01 commit message.

## Acceptance criteria

- [x] `/welcome` is a full-screen wizard (not a dashboard) with a progress rail +
      one step at a time; the route serves the built page (build-agnostic).
- [x] Distinct per-step visual treatment; directional motion; reduced-motion safe.
- [x] Step N-of-M, Back + Skip, focus-to-heading on transition; SVG glyphs.
- [x] The Welcome + live Permissions + Done steps render; suite green.
