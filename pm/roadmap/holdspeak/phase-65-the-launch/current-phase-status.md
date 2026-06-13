# Phase 65 — The Launch

**Status:** in progress (3/4). Opened 2026-06-13 on owner direction ("Let's
launch!"): cut v0.3.0 through the existing tag-triggered trusted-publishing
machinery, behind a real pre-flight, with the announcement kit drafted for
the owner.

**Last updated:** 2026-06-13 (**HS-65-03 done:** the announcement kit —
GitHub release notes + Show HN / lobste.rs / r/LocalLLaMA drafts, all in
canon voice (one copilot two modes / developers / named honest
comparisons / honest 0.x limits), `<REPO_URL>` left for the owner, posting
explicitly the owner's button. The demo GIF took the documented honest
fallback: the speak-and-type hero moment needs real audio + a real target
app + a screencast (a one-take manual capture), and a staged fake would
break the honesty bar — the README's existing real screenshots + the pixel
loop carry the visual story. Prior: **HS-65-02 done:** pyproject → 0.3.0; the
CHANGELOG [0.3.0] entry summarizes P51–P64 in canon voice; no stale version
claims in prose. The wheel built exactly as release.yml does it (194
`static/_built/` entries; twine check PASSED) installs clean in a fresh venv
to a working `holdspeak doctor` on **both** macOS (20/0 fail) and **real
.43 Linux metal** (22/0 fail, version 0.3.0, faster-whisper resolving, real
X11 hotkey + injection) — the standing Linux-proofs-live rule. Suite **2777
passed, 17 skipped**. Prior: **HS-65-01 done:** the all-routes pre-flight
(11 page routes in Chromium, zero-page-error per route; a coverage guard so
no new page escapes; CI-skip-clean) — and it paid off instantly, catching
TWO dead-on-arrival bugs no dogfood had reached: `/activity`'s JS had a
spurious leading `<script>` tag (dead since HS-9/10 — the page never ran
`load()`, a static shell for ~55 phases; fixed, now fires all 5 API calls)
and `/companion`'s x-for read `status.blockers` while status was null on
first paint (fixed with optional chaining). Suite **2777 passed, 17
skipped** (+2). Earlier: scaffolded — ground truth: PyPI at 0.2.2, the
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
| HS-65-01 | Pre-flight: every route loads clean | done | none |
| HS-65-02 | The release cut | backlog | HS-65-01 |
| HS-65-03 | The announcement kit | done | none |
| HS-65-04 | Closeout: tag, publish, verify | backlog | HS-65-01..03 |

## Where we are

Pre-flight, cut, and kit all done. Next is **HS-65-04 — closeout**: merge
on green, then tag v0.3.0 on the merge commit → trusted publishing →
verify `pip install holdspeak==0.3.0` from PyPI.
