# Settings audit and repair — 2026-10-14

Owner report: populated Meetings preferences were hard to use; calendar name
became an eventkit identifier and an unrelated model-migration refusal filled
the footer. Scope: every Settings module and its nested account/setup flows.
Base eef72f987 (#1203), one combined Settings release.

## Audit coverage

| Surface | Bounded source/interaction audit | Actual before capture |
| --- | --- | --- |
| Settings home | discovery, wings, states, posture | 1440 and 393 |
| Voice | hotkey, language, typing, symbols, wake, advanced | 1440 and 393 |
| Meetings | summary, capture, all calendar operations, export, advanced | 1440 and 393; actual ordinary save |
| Rhythm | cadence, brief, Telegram, advanced | 1440 and 393 |
| Sounds & Presence | sounds, presence, mascot, browser/server speech | 1440 and 393 |
| Wallpaper | selection, preview, unsupported live controls | 1440 and 393 |
| People | identity read/save, aliases, agent access and environment lock | 1440 and 393 |
| System | runtime, remote credentials/grants, reset, device fields | 1440 and 393 |
| Engines | #1203 hosting/trial regression, existing Switchboard retained | 1440 and 393 |
| Accounts | GitHub/Jira/Confluence, add/check/copy, calendar chooser, credentials | 1440 and 393 |
| Destinations | missing account, draft custody, validation, setup recovery | source and focused interaction checks; populated live checks pending |
| Guide | known/unknown/error readiness, fix actions, runtime check | 1440 and 393 |

Source audit is not a claim that every advanced control ran on real hardware.
The actual before audit uses frozen #1203 source in
`/Users/karol/dev/tools/wt-settings-trials-20261014/.tmp/settings-audit/before-{1440,393}/`.
Each observation contains 12 rendered states, original screenshots, real
producer setup and isolated HOME/DB provenance. Both ordinary Auto export saves
returned HTTP200 but erased Work's name and dropped disabled Personal. Root
read the observations and phone module shots plus the exact damaged calendar
shot. No page errors occurred. Native calendar access was disabled.

## Repairs

[Settled brief and file lanes](BRIEF.md). [Backend causes and focused proof](backend-audit.md).
Main face and satellite audit records follow their frozen implementation.

Use the existing Settings window, components and control species. Preserve
calendar sources and model assignment authority on save; persist Rhythm and
device preferences; use named rows and compact form width; keep ordinary
preferences visible; show failed edits and account drafts with Retry; restore
an erased native name only through explicit authoritative reselection.

Native direction sources: main-canvas/ and satellite-canvas/. Root viewed
main desktop/phone and corrected light-material satellite desktop/phone before
product edits. Initial satellite Vite host lacked React aliases; corrected in
scratch config. Initial satellite canvas used wrong fill/min-width; corrected
before implementation. These are synthetic direction material, not product
or owner proof. Direction PNGs live under `.tmp/settings-audit/`.

## Verification and limits

Backend: 30 focused integration checks and four native-calendar cases passed,
with failing regressions before edits. Root read the exact red/green output.
Graph/metadata focused validation: first root definition had an invalid edge
ID and omitted the required metadata replacement field. Definitions corrected;
651 checks then passed. No validator changed or waiver used.

The independent finished-change source review found six concrete recovery
defects. One author correction round repaired all six: latest edit on Retry,
native access with an existing feed, URL Add write coordination, retained
preference refusal across secret/control-mode saves, refused URL draft custody,
and the shared Project Room check caller. The single source re-check is RATIFY;
the original DO-NOT-RATIFY and its evidence remain in [review.md](review.md).
This is an independent Sol review, not Muad'Dib's check. Root also found and
fixed missing visible footer Retry and a false loopback import destination in
the first rebuilt phone capture.

The first combined quick check was RED: 12 face expectations/fixture failures,
two inherited Python verification defects, the native Back button material and
seven scanner hits on compact JSX configuration expressions. Existing calendar
checks now follow Edit and Import image while retaining exact payload/refusal
assertions. Account doubles persist their accepted Recheck response before the
new refresh GET. Clipboard checks await the actual library Copy result. Focused
compatibility runs passed 32 main and 81 account/Project Room cases. The Python
causes and producer-backed repair are in [audit-python.md](audit-python.md).
Root read those diffs and logs. No scanner, ceiling or assertion fence changed.

After the independent re-check, bounded root release followups use the library
Back button without its legacy class, format the seven JSX rows conventionally
(raw-ID total 18 → 11, ceiling 17), and allow the full Accounts host to wrap.
Root read these source seams; no further independent review is claimed.
The actual populated Add capture retained both fields and displayed refusal;
the first rig's exact-text locator included the chip icon and was corrected to
wait for its actual Retry. A missing destination folder correctly returned 400;
the final walk explicitly checks retained input, creates the temporary folder,
then saves it through the real route. Neither was a product success failure.

## Owner visual rejection — revision in progress

The owner reviewed the screenshots and rejected their visual quality, then
confirmed that the Workbench style must stay. Merge and deployment stopped.
The functional audit remains useful, but these faces are not accepted as the
finished design. The next pass changes composition, type hierarchy, proportions,
phone density, provider identity and the way setup details open. It retains
the existing window/material/component framework and all repaired writes.

The pre-revision checks are GREEN: 3635 web tests, 1131 affected Python checks,
107 desk sweeps (two existing xfails), 15 canon guards, production build and
frontend TypeScript. Producer-backed graph walks pass at1440/393; their first
attempt used an obsolete Button selector, corrected to the actual input and
revalidated with585 graph checks. Actual release-{1440,393} walks pass18states
each, including newest-edit Retry at32/31ms; Accounts walks pass5states each.
The shipping Accounts followup checks full-host wrapping and uncompressed
buttons. These are functional/geometry results, not visual acceptance.

No PR, merge or local hub deployment has occurred for this audit yet.
Owner acceptance, actual EventKit permission/read, real account
sign-in, physical mic/hotkey/audio devices, speech/model quality, screenshot
inference, external sends, remote devices and actual scheduled firing remain
unverified. Existing calendar refresh status is inferred from old events rather
than a persisted latest-read outcome; no new refresh framework was added.
Already dropped source identities cannot be recovered from damaged config.
