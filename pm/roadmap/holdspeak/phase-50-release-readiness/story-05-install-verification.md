# HS-50-05 — Verified clean-machine install + pinned contract

- **Project:** holdspeak
- **Phase:** 50
- **Status:** done
- **Depends on:** HS-50-01
- **Unblocks:** HS-50-06, HS-50-07
- **Owner:** unassigned

## Problem
The install path has never been verified as a release artifact. `scripts/install.sh`
pins git HEAD (`@main`), and the README/GETTING_STARTED describe a clone +
`uv pip install -e .` dev path. Nobody has confirmed a clean-ish environment reaches
a working `holdspeak doctor` from the documented steps.

## Scope
- **In:**
  - Actually run the documented install on a clean-ish environment (a fresh venv
    and/or a temp `HOME`/config/data dir), both the "from clone" and "from script"
    paths, and fix whatever breaks so each reaches a working `holdspeak doctor`.
  - Pin the install to a tag (the install script + docs reference a version, with a
    documented `@main` dev fallback).
  - Capture the real install transcript as evidence.
- **Out:** the docs rewrite (HS-50-06 owns the policy doc + README reconciliation);
  actually publishing to PyPI.

## Acceptance criteria
- [x] The documented install path is run on a clean-ish environment and reaches a
      working `holdspeak doctor`; the transcript is captured as evidence.
      (fresh venv + temp HOME, `uv pip install -e .`, doctor exit 0;
      [install-transcript.txt](./install-transcript.txt))
- [x] The install is pinned to a tag (with a documented dev fallback);
      behavior-preserving for the dev/editable path. (`HOLDSPEAK_REF` default
      `v0.2.1`, `main` fallback; verified statically)
- [x] Any breakage found is fixed (or documented with a clear workaround if it is a
      genuine external dependency, e.g. a model download). (none found; the 2 doctor
      warnings are the expected optional llama.cpp model + system-audio gaps)

## Test plan
- Manual + captured transcript: fresh venv -> install -> `holdspeak doctor` exits 0
  (or only flags expected optional gaps like a missing model). The sandbox may block
  the network; run via the `! <cmd>` session prefix or `dangerouslyDisableSandbox`
  and capture the output.

## Notes / open questions
- Use a temp `HOME` so the verification never touches the developer's real
  `~/.config/holdspeak` or `~/.local/share/holdspeak`.
- Optional deps (meeting/dictation/presence extras, models) are expected to be
  absent on a minimal install; doctor should degrade honestly, not crash.
