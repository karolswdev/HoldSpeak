# Phase 65 — The Launch: final summary

**Closed:** 2026-06-13 on owner direction ("Let's launch!"). The roadmap's
last standing strategic row. HoldSpeak v0.3.0 is on PyPI.

## What shipped

- **A pre-flight that earned itself instantly.** The all-routes
  zero-page-error sweep (the Phase-62 precedent made a gate) found two
  dead-on-arrival page bugs no test or dogfood had reached: `/activity`'s
  page JS had been DEAD since Phase 9/10 (a spurious leading `<script>`
  tag broke its `?raw`+`new Function` eval — a static shell for ~55
  phases) and `/companion` threw on every first paint. Both fixed; the
  activity page is functionally restored.
- **v0.3.0 cut and proven.** pyproject → 0.3.0, a CHANGELOG entry
  covering the fourteen phases since 0.2.x, and a wheel (built exactly as
  the release workflow does, bundle present, twine clean) that installs
  to a clean `holdspeak doctor` on fresh venvs on macOS AND real .43
  Linux metal.
- **The announcement kit.** Release notes plus Show HN / lobste.rs /
  r/LocalLLaMA drafts in canon voice, handed to the owner to post.
- **The publish.** A `v0.3.0` tag on the merged main triggered the OIDC
  trusted-publishing workflow; PyPI serves 0.3.0; a fresh-venv
  `pip install holdspeak==0.3.0` from PyPI was verified; the GitHub
  release is live with the notes.

## The honest calls

- The demo GIF took the documented fallback: the speak-and-type hero
  moment is a one-take manual screencast, and a staged fake would break
  the project's honesty bar. The README's real screenshots carry it.
- A first .43 install run showed environmental failures (dev-DB
  pollution triggering the Phase-50 refuse-newer safety, a missing
  optional extra, headless SSH); the isolated-HOME rerun is the true
  fresh-machine proof.

## Numbers

- Final suite: **2777 passed, 17 skipped** (+2: the pre-flight sweep).
- 4 stories, one commit each, plus the scaffold; PR #55 merged on green;
  v0.3.0 tagged, published, and verified from PyPI.

## Where this leaves the project

The launch row is done; HoldSpeak is installable as a real release. The
owner has the announcement drafts. Open threads, none blocking: the
journal trust banner (the Phase-64 quiet-trust question) and the
`web/routes/meetings.py` decomposition watch item.
