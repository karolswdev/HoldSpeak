# HS-146-03 — The settings list editor (joy surface)

- **Project:** holdspeak
- **Phase:** 146
- **Status:** ready
- **Depends on:** HS-146-02
- **Unblocks:** HS-146-05
- **Owner:** unassigned

## Problem

Settings→Meetings CALENDAR is one StringGadget + one EgressChip
(`SettingsCore.tsx:766-785`). It cannot hold two calendars, and this
surface is under the owner's joyful-setup magnifying glass —
ugly-but-lawful is rejected.

## Scope

### In (settled design row 5)

- The CALENDAR GadgetGroup becomes a `GadgetTable` list editor (the
  proven spoken-symbols idiom, `SettingsCore.tsx:621-665`): per row a
  label StringGadget (mic), url StringGadget (mic), enabled
  CheckGadget; add mints `{id: uuid4, label: "", url: "",
  enabled: true}`; in-world "REMOVE?" delete verb; no modals.
- Egress truth: one EgressChip per HTTPS-enabled source, the
  no-egress fact otherwise (`calendarEgressChipProps`
  :119-133 reworked for the list).
- `core-types.ts` calendar types updated.
- The beauty pass follows the functional pass before shots go up.

### Out

- Rail provenance (04); docs (05).

## Acceptance criteria

1. Add → type url (or speak it) → save → the source appears with its
   egress chip; two sources render as two rows.
2. Disable and remove are single in-world verbs; refusals in-flow.
3. Both widths clean (1440/393): no overflow, the working band holds.
4. The Door's Connect-calendar affordance still lands on this
   surface and reads correctly with the new editor.

## Test plan

`web/src/pages/cores/__tests__/SettingsCalendar.test.tsx` reworked
(render, add/remove/toggle, per-source chips); shots at both widths
delivered with story 05's set.
