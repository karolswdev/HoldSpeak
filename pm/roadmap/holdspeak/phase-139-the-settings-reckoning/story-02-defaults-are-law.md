# HS-139-02 — Defaults are law

- **Project:** holdspeak
- **Phase:** 139
- **Status:** done
- **Depends on:** 139-01
- **Unblocks:** 139-05
- **Owner:** delegated Opus worker; orchestrator adjudicates

## Problem

Twelve dials expose choices that have exactly one sane answer (census
disposition DEFAULT, rows 6, 9, 11, 16, 19, 20, 33, 34, 37, 41, 42, 46,
54). A dial nobody should ever move is complexity tax.

## Scope

- **In:** remove the dials and pin the values: model size (seed's
  choice), warm_on_start=true, pipeline.enabled=true,
  corrections_enabled=true, journal_enabled=true, journal_retention=500,
  mic_label="Me", remote_label="Remote", cross_meeting_recognition=true,
  web_auto_open=true, intel_enabled=true, intel_deferred_enabled=true,
  mir_enabled=true. Where a field is load-bearing at runtime, keep the
  config field with the pinned default but remove it from the settings
  surface and service-writable set; where it is pure preference, delete
  the field entirely (worker judgment, named per field in the report).
- **Out:** any behavior change beyond the pinned value being the value.

## Acceptance criteria

- [ ] None of the twelve render anywhere on the settings surface.
- [ ] Runtime behavior with the pinned values matches today's
  default-configured behavior (focused tests named per subsystem).
- [ ] `settings.update` refuses (or ignores with a named refusal) writes
  to removed keys — no silent accept of a dial that no longer exists.

## Test plan

- **Unit:** settings service write-refusal tests; per-subsystem focused
  tests (dictation assembly, meeting session, MIR glue) green.
- **Web:** settings vitest updated.
