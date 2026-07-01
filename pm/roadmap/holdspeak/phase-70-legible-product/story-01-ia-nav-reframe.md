# HS-70-01 — The IA spine: nav reframe to the two modes + Studio

- **Status:** done
- **Priority:** HIGH (the spine — everything hangs off it)
- **Depends on:** owner decisions A + B (confirmed at scaffold)
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## Goal

Replace the flat ~14-item nav with the four-destination model that expresses
the story in the chrome itself: **Home · Dictation · Meetings · Studio▾ ·
Settings.** After this story, the mental model is legible before a user
clicks anything.

## Scope

- Rework `web/src/components/TopNav.astro` to the four primaries + Settings.
- **Studio** is one collapsed group (a menu/disclosure), containing Workbench,
  Agent Desk, Cadence, Commands, Profiles, Presence. It reads as "advanced,"
  visually secondary to the two modes. It does not expand by default and is
  not where a fresh user lands.
- Nav labels use the canonical names (POSITIONING §"Canonical feature names"):
  "Dictation," "Meetings" (not "History"), "Settings." "Home" and "Studio"
  are the two new labels this phase introduces (Studio is registered as a
  canonical name in HS-70-08).
- Active-state + keyboard nav + mobile/narrow behavior preserved; the Studio
  group is reachable by keyboard.
- No page moves yet — this story is the frame. The per-mode consolidation is
  HS-70-04/05, Studio's landing is HS-70-06, first-run is HS-70-03. Routes
  keep working (nav just points at them under the new grouping).

## Proof required

Screenshot of the new nav on ≥3 pages (wide + narrow); the Studio group
collapsed and expanded; every existing route still reachable (route
pre-flight green). A short before/after of the nav.

## Done

Shipped and screenshot-proven. `TopNav.astro` is reframed to `Home · Dictation ·
Meetings · Studio ▾` + the ⚙ Settings tail; Studio is a native `<details>`
disclosure (zero JS, keyboard-native) holding the seven browsable advanced
surfaces behind an "ADVANCED" eyebrow, auto-opening on an active Studio route.
The `Route` union updated in lockstep (AppLayout + TopNav); four page `current=`
slugs retargeted (`home`/`meetings`, `+cadence`). Two transitional calls recorded
for later stories: Activity is parked in Studio (folds into Dictation in HS-70-04);
Presence is excluded from the nav (a nav-less overlay → dead-end) and stays in
Settings. No routes moved/added. Four nav states screenshot-verified (wide
collapsed / wide expanded / `/workbench` auto-open+active / mobile inline); route
pre-flight 2 passed; build green (17 pages). See
[evidence-story-01.md](./evidence-story-01.md).
