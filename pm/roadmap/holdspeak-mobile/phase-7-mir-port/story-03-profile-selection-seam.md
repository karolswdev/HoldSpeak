# HSM-7-03 — Profile-selection seam

- **Project:** holdspeak-mobile
- **Phase:** 7
- **Status:** backlog
- **Depends on:** HSM-7-01, HSM-0-01
- **Unblocks:** HSM-8-04, HSM-9-02
- **Owner:** unassigned

## Problem

The host UI (iPad Phase 8, iPhone Phase 9) needs to set and read the active MIR
profile for a meeting, but it must do so without reaching into the routing engine
internals — and the profile has to live where the Phase-0 contract says, on the
`Meeting`, so it round-trips and syncs like any other field.

## Scope

- **In:** carrying the active profile on the `Meeting` per the Phase-0 contract;
  a Runtime-Core seam (read/write the active profile) a host UI can drive without
  touching the engine; the default (Balanced) when unset.
- **Out:** the host screen/picker itself (Phases 8–9). The routing logic
  (HSM-7-01). Per-window profile override (deferred — one profile per meeting for
  v1).

## Acceptance criteria

- [ ] The active profile is a field on the `Meeting` per the Phase-0 contract
      (cite the HSM-0-01 catalog entry); it round-trips through persistence and
      validates against the schema.
- [ ] A host UI can read and set the profile through the Runtime-Core seam without
      importing or depending on the routing engine internals.
- [ ] An unset profile defaults to Balanced.
- [ ] Setting the profile changes which routing the engine applies on the next
      generation (the seam is wired, not decorative).

## Test plan

- Unit: set profile on a `Meeting` → persist → reload → profile intact + schema
  valid; the routing engine reads the set profile.
- Manual: n/a (UI is Phases 8–9; this is the seam).

## Notes / open questions

- If the profile needs to live somewhere other than the `Meeting`, escalate to
  the Phase-0 contract (HSM-0-03) rather than adding a side-table (phase risk).
- Per-window profile override (MIR-F-007 on desktop) is parked for v1 — one
  profile per `Meeting` (phase deferred decision).
