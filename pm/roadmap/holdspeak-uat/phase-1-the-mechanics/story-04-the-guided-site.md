# HSU-1-04 — The guided site

- **Project:** holdspeak-uat
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSU-1-03
- **Owner:** unassigned

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
    the four verdict verbs (pass / fail / partial / skip), a note
    field, screenshot attach (file drop; stored under
    `uat/_runs/<run_id>/shots/`), elapsed time per step. Mid-run
    conductor actions (restart, node kill) execute visibly between
    steps with their own status line.
  - **Verdict persistence** — every verdict written to the run DB the
    moment it is cast (HSU-1-01 schema); a browser refresh or a
    product crash mid-sitting loses nothing; the sitting resumes at
    the first unanswered step.
  - **Sitting end** — the score, straight into the debrief (HSU-1-05).
  - Speak-to-fill mic on the note field **when the product under test
    is up** (riding its transcribe route), honestly absent when it is
    not (the deferred-decision default from the phase doc).
- Out: the debrief packet content (HSU-1-05), scenario authoring UI
  (YAML is the authoring surface; Phase 2 may revisit), multi-user
  anything.

## Acceptance criteria

- [ ] `uat/web/` builds; the conductor serves it; the full loop —
      home → setup → staged world → walkthrough → sitting end — works
      against a real staged run.
- [ ] Verdicts + notes + screenshots persist per step; killing the
      browser mid-sitting and reopening resumes at the right step with
      all prior verdicts intact.
- [ ] A staging failure (bad deck that cannot even boot) renders
      honestly with the log tail and offers retry/abort — never a
      spinner.
- [ ] A mid-run action (`bad-endpoint` restart, node kill) is visible
      in the walkthrough as it happens.
- [ ] The visual bar holds: no overflow at laptop widths, real
      hover/active/disabled states, dark-first; screenshots committed
      as evidence.
- [ ] Component/store tests green (`npm test` in `uat/web/`); the
      conductor's site-serving + verdict routes green under
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
  product is being deliberately broken.
- "No prose in the UI" applies to the chrome (labels state WHAT);
  scenario `do`/`expect` text is content, not chrome.
