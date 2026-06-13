# Phase 65 — Agent Brief (read this first)

**Phase 65 — The Launch** for HoldSpeak. Opened on owner direction ("Let's
launch!"). The roadmap's last standing strategic row: cut **v0.3.0** for
real, prove it installs clean, and hand the owner the announcement kit.

## 0. Mission

Fourteen phases of product (P51–P64) reach PyPI as v0.3.0 through the
existing release machinery, with a pre-flight gate worthy of strangers
installing it, and announcement drafts in the canon voice ready for the
owner to post. The posting itself stays the owner's button.

## 1. The one thing you must not get wrong

**The tag is the publish.** `.github/workflows/release.yml` publishes to
PyPI via OIDC trusted publishing on any `v*` tag push — irreversible (PyPI
versions cannot be reused). The tag is cut ONLY at closeout, from the
merged main, after the full pre-flight is green. Everything before that
moment must be reversible.

## 2. Rules (the standing set)

PMO gate; no `Co-Authored-By`; cadence per shipping commit; one PR, branch
`phase-65-the-launch`, merged on green; full suite via
`--ignore=tests/e2e/test_metal.py`; Linux proofs live on .43; docs under
the voice guard.

## 3. Ground truth (verified at scaffold)

- PyPI has 0.2.1 + 0.2.2 (trusted publisher registered; the 0.2.x
  releases went through this exact workflow). pyproject says 0.2.2.
- `release.yml`: tag push → Node 22 web build → sdist + wheel (the wheel
  bundle-presence check is in the workflow) → twine check → publish.
- CHANGELOG.md is Keep-a-Changelog; 0.3.0 must summarize P51–P64
  (voice commands, activity pre-briefing, frontend+backend decompositions,
  meeting/transcript import + facets, Qlippy, the front door, languages +
  the spoken-symbol dictionary, the wake word, Send to Slack, Quiet
  Trust, two decomposition-phase production-bug fixes).
- CI has NO Playwright — the pre-flight route sweep must
  `importorskip` and skip cleanly without browsers; the evidence run is
  local.
- The Phase-62 lesson motivating pre-flight: a SyntaxError shipped on
  /welcome for ~19 phases because only dogfooded pages ever had a
  zero-page-error assertion.
- The .43 rig is alive (Phase 62/63 used it); a fresh-venv wheel install
  proof there satisfies the Linux-proofs-live rule.

## 4. Stories

- **HS-65-01 — pre-flight: every route loads clean.** A test sweeping
  EVERY web route in Chromium asserting zero uncaught page errors
  (CI-skippable, run locally for evidence). Run it; fix anything it
  finds (the Phase-62 precedent says expect surprises).
- **HS-65-02 — the release cut.** pyproject → 0.3.0; the CHANGELOG 0.3.0
  entry; README/doc version-claims check; build the wheel locally
  exactly as the workflow does (web bundle present), prove a fresh-venv
  install reaches `holdspeak doctor` on macOS AND on .43 (real metal).
- **HS-65-03 — the announcement kit.** GitHub release notes + Show HN +
  lobste.rs + r/LocalLLaMA drafts, canon voice (one copilot two modes /
  developers / honest comparisons), stored under the phase folder for
  the owner. A demo-GIF attempt for the README is allowed but gated on
  quality (honest fallback: skip and say so).
- **HS-65-04 — closeout.** PR merged on green → tag v0.3.0 on the merge
  commit → the workflow publishes → verify `pip install holdspeak==0.3.0`
  from PyPI in a fresh venv reaches doctor → GitHub release published
  with the notes → final-summary; README cadence; memory.

## 5. Gotchas

- Wheel-from-source needs `HOLDSPEAK_SKIP_WEB_BUILD=1` + a prebuilt
  bundle (see the workflow); a combined `uv build` produces a bundle-less
  wheel.
- The version appears in README prose? (0.2.2 mentions were scrubbed in
  the PyPI-README pass — verify none crept back.)
- The tag must be on the MERGE commit on main, not the branch head.
- PyPI propagation takes a minute or two; poll the JSON API before the
  fresh-install verification.
- Announcement drafts are internal artifacts (the voice guard does not
  scan pm/), but write them to canon anyway — they ARE the public voice.
