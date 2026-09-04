# HS-168-03 - The Connections face: Settings → Connections

- **Project:** holdspeak
- **Phase:** 168
- **Status:** done
- **Depends on:** HS-168-01, HS-168-02
- **Unblocks:** HS-168-04, HS-168-05
- **Owner:** unassigned

## Problem

There is no place on the desk that shows what is connected and what
to do about it. Settings → Integrations (SettingsCore.tsx:1043) is
credentials + mesh; the calendar hides under Meetings; GitHub and
Jira have no home at all.

## Scope

- **In:** the D1 face built to the ratified mockups from the barrel
  only: the Settings module the design named (rename or new; every
  `openSurfaceWindow("configure-settings", …)` caller from the 01
  census updated, deep links tested); one ChoiceCard per tool with
  StateChip + ProvenanceChip + the ONE next verb; the sign-in fold
  (mono well, COPY as a TransportKey, Recheck); Jira Add account as
  the 166 fold; the calendar card routing to the 146 flow; the
  model-hosts LINK card to the 156 front door; CREDENTIALS and MESH
  groups kept with their tests; EgressChip on every check naming the
  host; absent/degraded states; both widths; the mic where text is
  typed. Reads `GET /api/connections` only.
- **Out:** the interview (04); any credential capture.

## Acceptance criteria

- [x] The face composes barrel species only (zero hand-rolled rows, zero sentences); the four states render as designed at 1440 and 393.
- [x] Every deep-link caller updated and pinned; the credentials + mesh tests green.
- [x] Glass rig shots read by the orchestrator at true size before the flip.

## Delivered (2026-09-04)

`web/src/pages/cores/connections/` (ConnectionsPane + api client +
layout css) rendered at the top of the `integrations` tile, whose id
stays and whose label is now `Connections` in settingsPrefs.tsx AND
applications.ts; the TOOLS group as one full-width row per tool from
`GET /api/connections` only (no derivation on the face); GitHub's
sign-in fold (the command in a well, COPY at the right edge, primary
Recheck + ONE EgressChip beside the verb); the Jira connection rows
in the 166 grammar + the ghost Add account card with labelled Site /
Email wells and the mic; Calendar (inline SVG emblem) → Meetings;
Models → the models tile; CREDENTIALS + MESH untouched beneath; the
pane foot Receipt + the host last contacted, or `local · Not
checked`. Two orchestrator rounds paid on the shots (seven bounces:
an emoji emblem, a duplicated egress chip, COPY jammed on the
command, unlabelled Jira wells, the identity line splitting at 393,
no connected leg, and a POST to a route that does not exist — caught
by test_api_surface). Shots (assets/story-03-shots/): cold + fold +
recheck on an isolated HOME; connected-real at 1440 + 393 on the
owner's real gh + acli (GitHub `Connected · karolswdev`, the Jira row
with the full host, the foot naming the site last contacted). Gates
read by the orchestrator: vitest 190/190 (pages/cores); api-surface
5/5; glass 4 cold + 2 real; web baseline zero branch-new (with 04's
in-flight files stashed). Riders: the emojiGuard sweeps only desk/
(pages/cores/ is unswept — 07 ledgers it); StringGadget's `label`
is aria-only (a visible label needed a wrapper); the tile glyph
stays `secret`.

## Test plan

- **Vitest:** web/src/pages/cores/__tests__/connections*.test.tsx (states, verbs, deep links).
- **Glass:** tests/e2e/test_hs168_connections_glass.py (build-first; both widths; the fold; recheck).
- **Baseline:** `uv run python scripts/check_web_baseline.py --run` zero branch-new.
