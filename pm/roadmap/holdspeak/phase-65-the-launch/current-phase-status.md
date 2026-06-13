# Phase 65 — The Launch

**Status:** scaffolded (0/4). Opened 2026-06-13 on owner direction ("Let's
launch!"): cut v0.3.0 through the existing tag-triggered trusted-publishing
machinery, behind a real pre-flight, with the announcement kit drafted for
the owner.

**Last updated:** 2026-06-13 (scaffolded — ground truth: PyPI at 0.2.2, the
release workflow proven by the 0.2.x cuts, CI has no Playwright, the .43
rig alive.)

## The thesis — why this phase

Everything since Phase 50 pointed here: install/upgrade safety, scrubbed
docs, the positioning canon, the comparison section, Quiet Trust, and a
current front door. v0.2.2 is fourteen phases stale on PyPI. The launch is
overdue and the machinery already exists; the work is the pre-flight, the
cut, and the words.

## Goal

v0.3.0 live on PyPI, installed and verified from PyPI on a fresh venv; a
GitHub release with real notes; every route proven to load clean; the
announcement drafts in the owner's hands.

## Scope

- **In:** the all-routes zero-page-error pre-flight (HS-65-01); the
  release cut + install proofs on both OSes (HS-65-02); the announcement
  kit (HS-65-03); the tag + publish + from-PyPI verification (HS-65-04).
- **Out:** posting the announcements (the owner's button); new features;
  the journal-banner question (open, separate).

## Exit criteria (evidence required)

- The route sweep is green locally and skip-clean in CI; anything it
  found is fixed. (HS-65-01)
- v0.3.0 builds with the bundle present and installs to a working doctor
  on fresh venvs on macOS and .43. (HS-65-02)
- The kit reads in canon voice; release notes ready. (HS-65-03)
- Tag pushed, workflow green, `pip install holdspeak==0.3.0` from PyPI
  verified, GitHub release published. (HS-65-04)

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-65-01 | Pre-flight: every route loads clean | backlog | none |
| HS-65-02 | The release cut | backlog | HS-65-01 |
| HS-65-03 | The announcement kit | backlog | none |
| HS-65-04 | Closeout: tag, publish, verify | backlog | HS-65-01..03 |

## Where we are

Scaffolded. Next is **HS-65-01 — pre-flight**.
