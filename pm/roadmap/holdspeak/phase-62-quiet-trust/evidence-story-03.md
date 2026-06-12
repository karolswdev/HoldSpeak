# Evidence — HS-62-03: Docs + re-shot screenshots

**Date:** 2026-06-12
**Verdict:** done. The docs describe the badge instead of quoting privacy
paragraphs, the POSITIONING voice rule is canon, and all seven user-facing
screenshots showing the old copy were re-shot from live runs — including
the native overlay on the real .43 Linux desktop.

## Doc changes

- `docs/README.md`: the Qlippy line now says cards carry "an egress badge
  that shows where its data goes".
- `README.md`: three image alts + the card-pair caption rewritten to the
  badge ("The exact preview, the destination on the badge, your call.").
- `docs/MEETING_MODE_GUIDE.md`: three aftercare image alts stopped quoting
  retired notes.
- `docs/GETTING_STARTED.md`: the welcome alt's quoted footer is now
  "Local · 127.0.0.1".
- `docs/internal/POSITIONING.md`: the voice rule — **"Egress is a badge,
  not prose"** (owner direction, Phase 62): UI cards and notifications use
  the badge, never reassurance sentences; the trust surfaces, the single
  welcome pitch line, and reference docs may explain once; behavioral
  warnings stay. (The typing guide's Qlippy section was already rewritten
  in HS-62-01, bound to its lock.)

## Re-shot screenshots (all reviewed by eye)

Via `reshoot_story03.py` (live server + Chromium, every shot
content-asserted before capture, zero page errors):
`presence/qlippy-decision-card.png` (the six-line paragraph became one
"☁ github" pill), `presence/qlippy-learned-card.png` ("⌂ Local"),
`aftercare/followup-draft.png` ("Preview and copy only."),
`aftercare/send-to-slack.png` (the one-line approve note),
`aftercare/file-as-issue.png` (the new proposal-note + per-target guard),
`screenshots/welcome.png` (rail foot "Local · 127.0.0.1").

Via `reshoot_story03_linux.py` on **real .43 metal** (the standing rule:
Linux proofs run live): the tree rsynced to the rig, the REAL production
wiring (`build_desktop_presence_host` → GTK WebKit overlay) hosted a real
filed proposal's card on the real Xorg desktop, photographed with `import`
from the root window → `presence/qlippy-native-overlay.png` (408x460, the
badge visible over a real Firefox window — same framing as the original).

## A real pre-existing bug found and fixed

The re-shoot's zero-page-error gate caught a JS error on `/welcome` (and
`/` via the first-run redirect) that **pre-exists this phase on main**
(verified in a clean worktree of the Phase-61 merge): `welcome.astro` used
`@click="copy(\"…\")"` — HTML does not honor backslash-escaped quotes, so
the attribute truncated and Alpine parsed `copy(`, a SyntaxError on every
load; that Phase-43 copy button never worked. Fixed with a template
literal; the wizard now loads with zero page errors.

## Proof

- `reshoot_story03.py` RESULT: PASS (7/7 checks, zero page errors).
- The doc guard within the full suite: **2768 passed, 17 skipped**.
- Build clean; 0 `_built/` tracked.
