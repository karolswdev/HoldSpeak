# Attention dismissal and useful interruptions

Owner reported the pictured Dictation needs review popup could not go away,
then questioned its use case. Read-only live aggregate showed13 already
dismissed warnings and19 more with the same wording. Dismiss was writing,
then immediately replacing the visible card with another historical warning.

## Change

Dictation journal projections no longer feed Qlippy. Journal/Attention rows
remain. Other attention Dismiss writes only the visible presentation and
quiets older popup backlog in that tab, including remount/reload when session
storage is available. Newer eligible attention can show. Pending and failed
writes retain the exact visible row and a library Try again action. A denied
storage fallback survives remount, not a full reload. No source records or
presence settings changed.

## Verification

Root read the focused collection and actual run:14 tests in3 files pass
(ambientDismiss7, doorless1, projection store6). They cover exclusion, mixed
feeds, dismissal/refresh race, exact refused Retry, remount/reload, denied
storage and runtime learning cards. Release TypeScript exits0.
Complete quick GREEN: build,300 web in52 files,66 affected architecture/doc
assertions,107 Desk sweeps (two existing xfails),17 canon guards. One inherited
Python invalid-escape SyntaxWarning is present; no test failure is waived.
Logs under `.tmp/attention-dismiss/`; root read actual tails.

[Settled behavior and owner amendment](DESIGN.md). [Delegated source
counsel](REVIEW.md) RATIFY: no blocking finding; not formal postmerge review.
The existing ambient feed samples only four newest attention items, so an
older fifth eligible item behind dictation entries may not produce a popup.
It remains in Attention. This repair does not claim exhaustive delivery.
Full main tape, remote CI and owner acceptance remain separate.

Actual production interaction observations at1440 and393 each captured six
states, build25e46e6442fc78ac:19 real persisted synthetic journal warnings
produce no popup before/after reload; a different actionable source shows;
one Dismiss removes its visible row and closes the popup while two untouched
items remain; reload stays quiet; genuinely newer eligible attention can show.
Root read provenance/observations and actual no-popup/dismiss shots at both
widths. No page errors. Fixture rows use real journal/audit repositories in
an isolated hub HOME/DB; this is UI/presentation evidence, not dictation or
coder execution. Outputs `walk-final-1440/`, `walk-393/`. The first desktop
rig stopped on a case-sensitive expected fixture label; correcting only that
assertion and replaying fresh passed. Final metadata claims66 also pass;
generated documentation is current.
