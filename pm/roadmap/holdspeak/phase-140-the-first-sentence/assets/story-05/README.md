# HS-140-05 local browser acceptance

Run on 2026-08-18 against fresh local bare hubs, each with its own temporary
`HOME` and empty database. The harness constructed `MeetingWebServer` directly;
it did **not** call `scripts/walk_working_desk.py`, `DeskService.seed()`, or its
`_populate()` Phase-132 demo fixture. The temporary homes were removed after the
run; the owner’s state was never opened or changed.

## Ordinary fresh-owner Continue later

`ordinary-continue-chair-1440x900.png` and
`ordinary-continue-reload-chair-393x900.png` are the real fresh-owner path:
open the initial arrival, click **Continue later**, wait for the normal Chair,
then reload.

- The normal Chair appears once, with one menu bar, and remains normal after
  reload. Continue opens no pullout.
- The ordinary Continue handoff itself created the six drawers. The API then
  returned Inbox, Personal, Work, Meetings, Decisions, and Reference.
- The normal Chair does not try to repeat the six drawers as lane cards.
  They are discoverable on the existing Floor: see
  `ordinary-default-drawers-floor-1440x900.png` and
  `ordinary-default-drawers-floor-393x900.png`, reached through the normal
  Floor toggle after return.
- At both 1440×900 and 393×900, `documentElement.scrollWidth` and
  `body.scrollWidth` equal the viewport (1440 and 393 respectively); no page
  or console errors occurred.

The first genuine mobile run found a 464px document width at a 393px viewport:
populated Chair lanes retained their automatic grid minimum, and top chrome
could not shrink its privacy/clock prose. The responsive lane and chrome
constraints were corrected before the authoritative screenshots above were
captured; no global overflow masking was used.

## Controlled transcript Keep on the same ordinary hub

`ordinary-keep-controlled-transcript-1440x900.png` and
`ordinary-keep-controlled-transcript-393x900.png` use that same bare ordinary
hub but explicitly control only the browser dictation seam: Chromium’s fake
microphone plus a page-local fake `/ws/dictation/stream` final returns
`Controlled transcript for Keep.` This is a simulation of transcription, not a
claim of physical microphone or local-model success.

At both widths, **Keep as Note** transitions to one normal Chair, one menu bar,
and exactly one `First dictation` pullout; document/body widths equal the
viewport and no page or console errors occurred.
