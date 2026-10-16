# Owner density feedback: delivered and reviewed

2026-10-16 — Astra formal review after merge, with independent Sol counsel.

PR #1223 merged as `6788a92f1e2b49732a05797b136a27eabc290ba1` at 20:18:30 UTC.
The verified branch and merged commit have the same tree
`b1d4bf09103c6e3c7a908998da9497ce8feec993`. Source digest and built/served stamp
are `ca987454c0b44162`. Normal deployment waited for meeting inactive and voice
idle, then replaced PID 79705 with PID 96844 from
`/Users/karol/dev/tools/wt-desk-density-motion-20261016`, port 8765.
Health, Desk, Conductor and Models each returned 200. Jupiter and dependency
worktrees remain. Tests and walks used separate temporary HOME/database paths.

VERDICT: RATIFY

FINDINGS: No actionable finding in the merged change. The original artifact
footer had zero initial top clearance; final actual walks show at least 7 px
top / 6 px bottom on desktop, clear button hits through 400/600/320 px sizing,
true movement from y=100 back to the actual top boundary y=28, and saved
geometry on reload. Desktop art is 48 px, Dock art 24 px and Dock height 60 px.
Phone top 44 px, Dock 56 px, Copy and More remain reachable. Task inline marks
render correctly. Exact Copy and before/after artifact reads agree.
These changes serve Tenets 3/5/6/7 using the existing library.

CONDITIONS: None for this bounded delivery.

MISSED: Earlier full-tape fixture drift is repaired separately below; it does
not establish that the whole tape is green.

TUESDAY: The owner can read and copy the artifact without resizing to make
footer clearance, move the window to the top bar, and use the denser desktop.

UNKNOWN: Dictate execution, native/provider actions and the owner's aesthetic
acceptance were not exercised by these isolated reading/layout walks. The
full regression tape remains red; six newly observed B failures are not yet
attributed, alongside the inherited failures. No whole-product acceptance.

Proof in the density worktree: `.tmp/feedback/after1440/` (8 states),
`after393/` (3 states and phone More shot), `quick-density-final.log`,
`source-build-equality.json`, `deployment.json`. Root read the actual shots;
independent Sol counsel also read both final observations and screenshots.
Quick GREEN: 4,168 web / 109 sweep / 17 canon. TypeScript and token generation pass.
Direction and earlier reproduction: [FOLLOWUP-DENSITY.md](FOLLOWUP-DENSITY.md).

## Full-tape fixture follow-up

B run 38950387547 completed with 103 failures and 16,327 passes; 96 failure names
also occur in earlier run 38897233198. Direct attribution to PR #1220:
FollowThroughCard now intentionally emits nullable `deferred_until` and
`snoozed_until`. The recorded honest-faces board lacked both fields on its
two cards; the recorded people commitment lacked them too. That commitment's
missing `provenance.source_ref: null` already failed in the prior tape.

The forward fix changes only those seven expected JSON fields. It does not
weaken the comparison or change production behavior. Both exact producer
fence tests were collected and pass against real isolated services; 32 focused
web consumer tests pass. Their standard jsdom canvas warning remains.

The fixture worktree is `/Users/karol/dev/tools/wt-flagship-fixture-sync-20261016`.
Its `.tmp/feedback/` contains collection, producer and consumer logs.
Ordinary quick GREEN (`quick-fixtures.log`): both named producer checks,
109 desktop/phone sweeps and 17 canon checks pass. The served
product remains the verified density release; this fixture-only change adds
no runtime behavior.
