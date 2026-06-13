# Evidence — HS-65-04: Closeout — tag, publish, verify

**Date:** 2026-06-13
**Verdict:** done. HoldSpeak v0.3.0 is published on PyPI, verified by a
from-PyPI fresh-venv install, and the GitHub release is live.

## The sequence (the tag is the publish, done once, from merged main)

1. **PR #55 merged on green** (6/6 checks: Unit, Integration, E2E, Linux
   Smoke, Route screenshots, All Tests Summary). Merge commit `c87b743`
   on main; pyproject confirmed 0.3.0 and the CHANGELOG [0.3.0] entry
   present there before tagging.
2. **`v0.3.0` tagged on `c87b743` and pushed.** No prior v0.3.0 tag
   existed; v0.2.1 / v0.2.2 were the predecessors.
3. **The release workflow ran and succeeded** (run 27454387301, ~57s):
   Node 22 web build → sdist + wheel with the bundle present → twine
   check → OIDC trusted publish to PyPI.
4. **PyPI serves 0.3.0** (confirmed via the JSON API:
   `info.version == "0.3.0"`).
5. **From-PyPI install verified**: a fresh venv,
   `pip install holdspeak==0.3.0` straight from PyPI →
   `holdspeak.__version__ == "0.3.0"`, the web bundle present in the
   installed package (`static/_built/index.html` exists), and
   `holdspeak doctor` → **Runtime: HoldSpeak 0.3.0**, **22 passed, 1
   warning, 0 failed** (the one warning is the optional `openai` package,
   expected on a clean machine).
6. **The GitHub release is published** with the user-facing notes:
   https://github.com/karolswdev/HoldSpeak/releases/tag/v0.3.0

## Handed to the owner

The announcement drafts (`announcement-kit.md`) are ready to post; posting
is the owner's button, as scoped.

## Proof

- The from-PyPI doctor summary above is the test: a stranger running
  `pip install holdspeak` today gets a working 0.3.0.
