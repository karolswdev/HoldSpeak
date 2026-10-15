# Forms audit — 2026-10-15

Source inspection at base `a81364a0d`. Product unchanged; no tests, build,
install, browser or owner-state access. **HOLD for root's settled canvas/design.**
Read TWO-BRAINS, ORCHESTRATION, Constitution, UX-CANON, CLAUDE fast cycle,
this pass's BRIEF, and prior AUDIT-EDITORS items 5/6. Anchors below are current.

## Confirmed candidates

**Schedule recording.** `web/src/desk/components/ScheduleCreateWindow.tsx:165`
still uses an instructional sentence for its legend. When hand-wraps a raw
`datetime-local` input (`:186`), Cron removes its mic (`:203`), save failure
is a sentence (`:146`, rendered in a paragraph at `:218`), and local inline
flex owns the action row (`:227`). These fail Tenets 3/5/6 and UX-CANON A3/B/D.
Current kit already has inset groups/actions, row width variants, and
`StringGadget type` (`web/src/desk/surface/contract.md:39`, `gadgets.tsx:285`);
no new mechanism is needed. Phone date width/popup and actual focus remain
unverified.

**Email recipients.** `web/src/pages/cores/connections/Destinations.tsx:261`
and `:262` use single-line StringGadget for To/Cc. Saved arrays rejoin with
commas (`:90`); long values cannot be read together inside those editors.
The form uses default rows (`:203`, `:295`). This fails Tenets 3/5/7 and
UX-CANON D's wrapping-value rule. PadGadget supplies wrapping, mic and
`autoGrow` (`web/src/desk/surface/gadgets.tsx:363`, `:398`). Its API has **no
inputProps/test-id forwarding**: existing `dest-to` assertions must become
label-based if root authorizes that test edit; do not change the shared kit
just to retain the hook. Runtime clipping is still a candidate, not observed.

## Active opening and producer paths for root's live pass

- Schedule: Chair footer `[data-testid="arrival-schedule"]`
  (`ChairHome.tsx:3159`) → `openScheduleCreate()` → window
  `[id="schedule:__create__"]` (`ScheduleCreateWindow.tsx:152`). Mounted by
  `web/src/desk/DeskApp.tsx:270` once arrival is complete. Fields are named
  Title, Mode, When / Cron expression, Duration; submit is
  `[data-testid="schedule-create-submit"]`. `handleSubmit` (`:95`) calls
  `createSchedule`; slice `web/src/desk/store/scheduledRecordingSlice.ts:41`
  POSTs `/api/scheduled-recordings`, then reloads. Producer:
  `holdspeak/web/routes/scheduled_recordings.py:67` →
  `ScheduledRecordingService.create_schedule` (`:171` in its service file).
- Destinations: Settings → Accounts (`SettingsCore.tsx:253`, module
  `integrations`) mounts the group at `:2438`. Selectors:
  `[data-testid="destinations"]`, `dest-add`, form Channel=Email; saved row
  Details → `dest-edit` → `dest-form`. SendWell's Add destination also calls
  `requestDestinationsFocus()` and opens `configure-settings/integrations`
  (`web/src/desk/surface/send/SendWell.tsx:556`). Destination reads/saves/checks
  use `/api/channels/destinations[/{id}/check]`
  (`web/src/features/channels/channels.ts:586`), routed to
  `channel.destinations/save_destination/check_destination`
  (`holdspeak/web/routes/channels.py:95`). Account reads use `/api/connections`
  (`web/src/pages/cores/connections/api.ts:160`). Recorded email/list/check
  answers already exist in `web/src/desk/__tests__/fixtures/destinations-wire/`.

## Boundaries and focused tests to approve

Keep Schedule's five draft keys, empty time/Cron, pending-save custody and
reopened-form identity guard (`ScheduleCreateWindow.tsx:73`, `:130`). Keep
local timezone, future-time validation, Once/Recurring, duration and enabled
payload. Do not schedule an owner capture for inspection.

Keep destination comma-to-address conversion (`Destinations.tsx:111`, `:192`),
replacement/parking semantics, account setup with the draft mounted,
SecretRow and key secrecy, EgressChip beside Save/Check, read/refusal/Retry
states. Check reflects the sender's last known answer; it is not a test send.
No Keychain write, provider check or external send is needed for this pass.

Primary existing focused files proposed for root's allowlist:

- `web/src/desk/components/__tests__/scheduleCreate.test.tsx`: six draft,
  pending-operation, refusal and recurring/empty-Cron cases (`:28`).
- `web/src/desk/__tests__/destinations.app.test.tsx`: account-read/setup and
  field saves (`:174`), email key secrecy/save and sender-check states (`:236`).

Additional existing coverage if root chooses it: `chair.app.test.tsx:488`
(real Chair opening, Cancel, save/reload using recorded hub answers), and
`deskRemembers2.philo1307.test.tsx:229`, `:330` (reload custody and empty time).
These are source descriptions, not collected or green claims. Collect and
run only root-approved scope through `.tmp/surface-refinement/locked.py`.

Tuesday: the architect should see all recipient values and schedule fields
with their names and a clear save outcome. Root still owes live 1440/393,
hit/focus/scroll/date-popup observations, settled canvas and release checks.
