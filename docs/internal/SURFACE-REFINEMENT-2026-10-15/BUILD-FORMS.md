# Forms build — 2026-10-15

**FROZEN — HOLD FOR SHIP.** Built after root's canvas/design signal. Root
owns live 1440/393, combined quick and release. No stage or commit performed.
Latest focused result after root's live layout/copy correction: **49 passed**.
The later shared Pad padding correction awaits root's browser/quick proof.

## Changes and settled amendment

- Schedule uses one Recording inset, full Title/When/Cron rows, bounded
  Mode/Duration, StringGadget's native datetime input with the deliberate
  `colorScheme: light`, and existing mics. SurfaceFooter owns Cancel,
  Schedule, Saving and concise failure receipts. The five draft keys,
  empty values, future-time validation, timezone, Once/Recurring and
  pending/newer/reopened-operation custody remain in the existing writer.
- Destination forms use named inset groups and their local action slot.
  To/Cc are auto-growing PadGadgets, saved addresses display one per line,
  and parsing accepts commas, CR and LF, with trimming/filtering and order
  preserved. Auto-name uses the first parsed address. Pad tests use labels.
- Root's additional live email-edit finding is fixed in the frontend only.
  `fromDestination` retains the exact saved key ref. The effective ref stays
  that ref while provider and normalized From match the original identity;
  a changed identity uses the existing canonical naming rule.
- Edit locally checks the saved destination with existing `wire.check`.
  `_email_state` (`holdspeak/services/channel_service.py:236`) reads the
  local key and stored send state; it does not call the provider. Only
  `ready`, `sender_accepted`, `sender_not_verified`, and `key_changed`
  establish present. Only `email_key_missing` establishes absent.
  Locked/not-native/transport/unrelated states remain unavailable, with
  CANNOT READ KEY, the named reason and Retry beside SecretRow. Reading key
  names the pending state. The map receives the exact checked ref.
- Request generation and current identity fence old responses after a
  sender/provider change, unmount, retry or key replacement. No backend,
  shared kit, schema, account setup, provider probe or external-send change.

Owned edits: `web/src/desk/components/ScheduleCreateWindow.tsx`,
`web/src/pages/cores/connections/Destinations.tsx`, and the two focused test
files below. The initial build needed no CSS; root later extended this lane
to the shared Pad text reservation below. `chair.app.test.tsx` was run unchanged.

## Focused execution proof

Every command went through `.tmp/surface-refinement/locked.py`: temporary
HOME, machine test lock, isolation switches. No browser/build/install,
pytest, owner DB/Keychain, hardware, external send or capture was run here.

Collection (exit 0; 47 actual test entries):

```sh
python3 .tmp/surface-refinement/locked.py forms-collect-final --web ./node_modules/.bin/vitest list src/desk/components/__tests__/scheduleCreate.test.tsx src/desk/__tests__/destinations.app.test.tsx src/desk/__tests__/chair.app.test.tsx
```

`.tmp/surface-refinement/forms-collect-final.log` includes:

```text
src/desk/components/__tests__/scheduleCreate.test.tsx > new schedule draft custody > keeps microphone controls in both time modes and rejects a past time without losing it
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > wraps recipient editors and saves comma and newline lists in their entered order
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > checks the saved email key locally and edits with its exact legacy ref without replacing the key
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > keeps an unreadable saved email key disabled with email_key_missing and retries its local read
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > keeps an unreadable saved email key disabled with email_key_store_locked and retries its local read
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > keeps an unreadable saved email key disabled with email_key_store_not_native and retries its local read
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > keeps an unreadable saved email key disabled with no_answer and retries its local read
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > ignores a pending saved-key check after the sender and provider change
src/desk/__tests__/chair.app.test.tsx > The capture bar: Schedule > Cancel closes the window and posts nothing; Create posts the title, closes the window and loads the saved row
```

Before product fixes, the same three-file run (`forms-red`, using `vitest
run` instead of `list`) exited 1: **9 failed, 38 passed; 2 failed files,
1 passed**. Failures reproduced the intended missing microphones/footer,
wrapping/parsing, saved-key edit and check/retry behavior. Log:
`.tmp/surface-refinement/forms-red.log`.

First post-fix run had 45 passed/2 failed because the new microphone queries
omitted the real unsupported-browser suffix. Corrected queries accept that
named state; no microphone API was faked and no product workaround was added.
The suffix is `· NO MICROPHONE IN THIS BROWSER` in jsdom.

Initial settled-build command:

```sh
python3 .tmp/surface-refinement/locked.py forms-green-final --web ./node_modules/.bin/vitest run src/desk/components/__tests__/scheduleCreate.test.tsx src/desk/__tests__/destinations.app.test.tsx src/desk/__tests__/chair.app.test.tsx
```

Initial settled-build run tail (`.tmp/surface-refinement/forms-green-final.log`):

```text
 Test Files  3 passed (3)
      Tests  47 passed (47)
   Start at  02:03:26
   Duration  3.48s (transform 1.98s, setup 218ms, import 2.85s, tests 3.86s, environment 593ms)
```

The legacy-ref regression asserts the exact saved `key_ref`, `replaces`,
recipient order, rendered completion and **no key PUT**. The pending-check
case changes both sender and provider, ignores the old reply, then saves
with the new canonical key ref. Existing draft/account/failure/check
regressions remain green. Recorded hub fixtures supply the email/list/key
answers; tests never read a native Keychain.

## Provider-cache correction — final source review

Root found that a legacy key ref can be shared by two providers, while the
native key identity is `provider:ref`
(`holdspeak/services/channel_email.py:477`). Ref-only UI knowledge let one
provider skip its Check and reuse the other's present status. Email cache
keys now include provider and exact ref for local Check results, successful
key saves, optional list `key_present` seeding, validity and SecretRow state.
Slack keeps its previous raw-ref cache identity. Saved payload refs remain
exact. Root's three ByRole compiler corrections in the tests are preserved.

New collected regression:

```text
src/desk/__tests__/destinations.app.test.tsx > the email destination setup > checks a shared legacy key ref separately for each email provider
```

It opens a SendGrid destination with a present legacy key, then a Resend
destination with the same ref and no key. Resend must make its own Check,
show NO KEY and keep Save disabled. Reopening SendGrid keeps its independent
known-present state without another Check. No key PUT occurs.

Collection (`forms-provider-collect.log`, exit 0, 48 entries) and runs used
the same three approved files and the isolated lock helper:

```sh
python3 .tmp/surface-refinement/locked.py forms-provider-collect --web ./node_modules/.bin/vitest list src/desk/components/__tests__/scheduleCreate.test.tsx src/desk/__tests__/destinations.app.test.tsx src/desk/__tests__/chair.app.test.tsx
python3 .tmp/surface-refinement/locked.py forms-provider-red --web ./node_modules/.bin/vitest run src/desk/components/__tests__/scheduleCreate.test.tsx src/desk/__tests__/destinations.app.test.tsx src/desk/__tests__/chair.app.test.tsx
python3 .tmp/surface-refinement/locked.py forms-provider-green --web ./node_modules/.bin/vitest run src/desk/components/__tests__/scheduleCreate.test.tsx src/desk/__tests__/destinations.app.test.tsx src/desk/__tests__/chair.app.test.tsx
```

The red exited 1 with **1 failed, 47 passed**: Resend's Check was skipped
after the SendGrid cache hit. Final actual run tail
(`.tmp/surface-refinement/forms-provider-green.log`, exit 0):

```text
 Test Files  3 passed (3)
      Tests  48 passed (48)
   Start at  02:13:01
   Duration  3.36s (transform 1.89s, setup 198ms, import 2.75s, tests 3.77s, environment 593ms)
```

## Live layout/copy correction — root observation

Root's live `.tmp/surface-refinement/after-final-393/email-recipients.png`
showed recipient wells only 177 px wide. Settings' legacy high-specificity
row rules (`web/src/pages/cores/settings.css:321`, `:371`) overrode the
library's full-row columns. All twelve DestForm `controlWidth="full"` rows
now also use the existing `wide` flag, which those same Settings rules
already honor. No CSS or framework change was made. A regression visits all
six channel forms and checks every full row has `data-wide="true"`.

Root's `after-final-1440/schedule-save-refused.png` and
`after-final-393/schedule-save-refused.png` also showed the failure receipt
truncated. It is now **Not saved · Kept**, retaining the failed-save and
draft-custody facts in the existing footer. The exact receipt assertion was
updated. Root owns the final live check of these bounded corrections.

Collected regression in `.tmp/surface-refinement/forms-layout-collect.log`:

```text
src/desk/__tests__/destinations.app.test.tsx > the Destinations group > keeps full destination rows wide under the Settings layout rules
```

The same three approved files were collected then run under the isolated
lock helper. `forms-layout-red.log` exited 1 with **2 failed, 47 passed**,
for the missing wide flags and old receipt. Final command:

```sh
python3 .tmp/surface-refinement/locked.py forms-layout-green --web ./node_modules/.bin/vitest run src/desk/components/__tests__/scheduleCreate.test.tsx src/desk/__tests__/destinations.app.test.tsx src/desk/__tests__/chair.app.test.tsx
```

Final actual tail (`.tmp/surface-refinement/forms-layout-green.log`, exit 0):

```text
 Test Files  3 passed (3)
      Tests  49 passed (49)
   Start at  02:20:38
   Duration  3.41s (transform 1.85s, setup 202ms, import 2.82s, tests 3.93s, environment 589ms)
```

## Shared Pad text reservation — root's final phone observation

Root's `.tmp/surface-refinement/after-release-393/email-recipients.png`
showed Cc characters behind the 44 px mic. The Pad's generic 26 px right
padding did not reserve the phone mic, and the Desk textarea skin could
override that padding. Root authorized only this shared CSS seam.

`web/src/desk/surface/gadgets.css` now explicitly scopes the reservation to
`.desk-next .gadget-pad textarea`: desktop uses `--size-icon-md + --space-2`
(20 px mic plus 8 px for its inset/text gap); the existing `surface`
container query at 419 px uses `--desk-button-hit-size + --space-2`
(44 + 8 px). No JS, framework, consumer override or other style changed.

No new test was added or run for this CSS-only correction. Root owns the
computed textarea padding/mic geometry assertion, two-size shots, and final
quick rerun. The preceding 49-test result proves the earlier forms work,
not this overlap repair. CSS and lane are frozen; HOLD FOR SHIP.

## Related Resend test selector — combined quick finding

Root's combined quick reported 3711 passed/1 failed: the existing Resend
form test still queried the removed `dest-to` hook. Root approved that test
file as an additional focused scope. Only its recipient query changed to
`getByLabelText("To", { exact: true })`; Resend provider selection, secret
save, egress and body assertions remain intact. No product code changed.

Collection waited for the active machine lock, then listed these four tests
(`.tmp/surface-refinement/forms-resend-collect.log`, exit 0):

```text
src/features/channels/__tests__/resendProvider.test.tsx > the provider words > names the provider that accepted the email
src/features/channels/__tests__/resendProvider.test.tsx > the provider words > shows the provider's host as the egress and its activity page as the far side
src/features/channels/__tests__/resendProvider.test.tsx > the provider words > keeps each provider's key under its own name
src/features/channels/__tests__/resendProvider.test.tsx > the Destination form > picks Resend: its key row, its key save, its egress, its save body
```

Exact focused commands:

```sh
python3 .tmp/surface-refinement/locked.py forms-resend-collect --web ./node_modules/.bin/vitest list src/features/channels/__tests__/resendProvider.test.tsx
python3 .tmp/surface-refinement/locked.py forms-resend-green --web ./node_modules/.bin/vitest run src/features/channels/__tests__/resendProvider.test.tsx
```

Actual run tail (`.tmp/surface-refinement/forms-resend-green.log`, exit 0):

```text
 Test Files  1 passed (1)
      Tests  4 passed (4)
   Start at  02:28:42
   Duration  1.16s (transform 513ms, setup 57ms, import 667ms, tests 200ms, environment 167ms)
```

## Unknowns for root's close

No live shots, geometry, hit ownership, scroll depth, native calendar popup,
actual voice capture or production save was verified by this worker.
Unmount/replacement stale fencing is source-reviewed; the focused delayed
response regression exercises sender/provider change. The green run emits
jsdom's existing `HTMLCanvasElement.getContext` not-implemented stderr from
DeskIcon, but exits 0 with all 49 tests passed. No extra suite was run.
