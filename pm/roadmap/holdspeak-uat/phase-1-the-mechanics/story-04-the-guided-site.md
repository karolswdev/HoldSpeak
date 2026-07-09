# HSU-1-04 — The guided site

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** done
- **Depends on:** HSU-1-03
- **Owner:** agent

## Problem

The whole point of this project is to force the human sitting — and a
fillable markdown file does not force anything (Phase 67's
`PROTOCOL.md` proved that by sitting on the shelf). The guided site is
the front door: pick a pack, the rig stages the world, and the site
walks you step by step — do this, expect this, verdict, next — until
the sitting is done and the record exists.

## Scope

- In:
  - **A React + Vite app** under `uat/web/`, built to static assets
    the conductor serves (per the standing web-stack direction; no
    Alpine, no Astro islands needed — this is one SPA). Signal-grade
    visual bar: the desk's tokens reused, real affordances, overflow
    checked — a test rig the owner *wants* to sit in, not a gray
    checklist.
  - **Home** — packs with coverage %, past sittings with scores, a
    Resume affordance for an interrupted sitting.
  - **Sitting setup** — pick pack (+ optional deck override), watch
    the rig stage the world honestly: boot progress, deck applied,
    seeds verified, nodes up; a staging failure is shown with the log
    tail, never hidden.
  - **The walkthrough** — one step at a time: the `do` instruction,
    the `expect` bar, an "Open the product" affordance (the run's
    product URL, deep-linked to `where` when the scenario names it),
    and **one verdict slot per applicable surface** — a step aimed at
    web + iPad + iPhone shows three surface chips, each taking its
    own pass / fail / partial / skip, note, and screenshot (file drop
    or the device's own camera-roll picker; stored under
    `uat/_runs/<run_id>/shots/`). A surface marked `n/a` in the
    scenario renders as such with its reason — visible, never a
    missing row. Steps advance when every applicable surface has a
    verdict (skip is a verdict). Elapsed time per step. Mid-run
    conductor actions (recipe apply, restart, node kill) execute
    visibly between steps with their own status line.
  - **The site travels to the device** — the walkthrough is fully
    usable from the iPad's and iPhone's browser (the conductor serves
    on the Mac's LAN address for this purpose; verdict-write routes
    only): you hold the phone, use the app with one hand, and cast
    the phone-surface verdict on the same open sitting — the run is
    shared, so a verdict cast from the iPad shows up on the Mac's
    view live. Responsive to phone width is an acceptance bar, not a
    nice-to-have.
  - **Verdict persistence** — every verdict written to the run DB the
    moment it is cast (HSU-1-01 schema), keyed
    (scenario, step, surface); a browser refresh or a product crash
    mid-sitting loses nothing; the sitting resumes at the first
    unanswered (step, surface).
  - **Sitting end** — the score, straight into the debrief (HSU-1-05).
  - Speak-to-fill mic on the note field **when the product under test
    is up** (riding its transcribe route), honestly absent when it is
    not (the deferred-decision default from the phase doc).
- Out: the debrief packet content (HSU-1-05), scenario authoring UI
  (YAML is the authoring surface; Phase 2 may revisit), multi-user
  anything.

## Acceptance criteria

- [x] `uat/web/` builds; the conductor serves it (commit-built `dist`);
      the full loop — home → setup → staged world → walkthrough → sitting
      end — works against a real staged run (proven by
      `test_site_and_sitting_real.py` and the Playwright drive
      `scripts/uat_site_walk.py`).
- [x] Verdicts + notes + screenshots persist per (step, surface) the
      moment cast; killing the browser mid-sitting and reopening resumes
      at the right (step, surface) with all prior verdicts intact
      (`test_sittings.py::test_verdict_persists_across_a_fresh_manager`).
- [x] The walkthrough is device-reachable: the conductor serves the site
      LAN-bound (`UAT_HOST=0.0.0.0`), the layout holds at iPhone width
      (screenshot `assets/site-04-phone-home.png`), and the run is shared
      so a device verdict lands on the same sitting. **The LIVE device
      cross-view (a verdict cast from a real iPad/iPhone over LAN, seen
      live on the Mac) is owner-gated and rides HSU-1-06** — the
      capability is built; only the owner can cast a device verdict.
- [x] An `n/a` surface renders with its reason and is excluded from the
      step's completion math (SurfaceCard + resume math; store tests).
- [x] A staging failure renders honestly with the log tail and offers
      retry/abort — never a spinner (StagingPanel; the stage route
      returns the product's log tail on failure).
- [x] A mid-run action (node kill) is visible in the walkthrough as it
      happens (the `after` hook fires the mesh kill between steps; smoke
      scenario 06).
- [x] The visual bar holds: dark-first, real hover/active/disabled
      states, no overflow at laptop widths; screenshots committed
      (`assets/site-01-home.png` … `site-04-phone-home.png`).
- [x] Component/store tests green (`npm test` in `uat/web/`, 5 tests);
      the conductor's site-serving + verdict routes green under
      `uv run pytest -q tests/uat/`.

## Test plan

- Unit: walkthrough store (step advance, resume math, verdict
  casting), staging-status rendering.
- Integration: Playwright against a real conductor + staged
  `golden-local` run — cast all four verdict verbs, attach a
  screenshot, refresh mid-sitting, resume.
- Manual / device: the owner's smoke sitting in HSU-1-06.

## Notes / open questions

- The site talks only to the conductor; the conductor talks to the
  product. One trust boundary, and the site keeps working while the
  product is being deliberately broken — including while a device is
  mid-verdict on it.
- "No prose in the UI" applies to the chrome (labels state WHAT);
  scenario `do`/`expect` text is content, not chrome.
