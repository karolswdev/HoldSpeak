# HS-84-01 — Meeting intelligence runs on a profile

- **Project:** holdspeak
- **Phase:** 84
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-84-02, HS-84-03, HS-84-04
- **Owner:** unassigned

## Problem

Meeting intelligence is the hub's oldest model consumer and still resolves
"where do I run" from four hand-typed config fields
(`MeetingConfig.intel_provider` / `intel_cloud_base_url` / `intel_cloud_model`
/ `intel_cloud_api_key_env`, `holdspeak/config.py:126-143`) via
`build_configured_meeting_intel` (`holdspeak/intel/providers.py:210-222`).
Meanwhile the profile-aware constructor already exists and is production-
tested on the ask/recipes path (`build_meeting_intel_for_profile`,
`providers.py:232-253`) — meeting intel just never adopted it. This story
gives meeting intel a `profile_id` and carves the ONE resolution seam the
rest of the phase reuses.

## Scope

- In: `MeetingConfig.intel_profile_id: Optional[str]` (config-version-safe
  round trip through `/api/settings`, like every other field).
- In: a resolver in `holdspeak/intel/providers.py` that generalizes
  `build_meeting_intel_for_profile`: given a profile id + an optional
  profiles lookup, produce the effective endpoint shape (base_url, model,
  key env via `profile_key_env`, context limit) with the pinned resolution
  order — valid profile → legacy config shape → local. A missing/deleted
  profile falls back and surfaces a named reason (consumed by HS-84-04).
- In: `build_configured_meeting_intel` honors `intel_profile_id` for the
  cloud leg; `intel_provider` local/auto/cloud semantics untouched.
- Out: dictation (HS-84-02), settings UI (HS-84-03), doctor/egress wording
  (HS-84-04), any change to the ask/recipes call sites (already correct).

## Acceptance criteria

- [ ] `intel_profile_id` unset ⇒ `build_configured_meeting_intel` output is
  byte-identical to today (test constructs both and compares the kwargs).
- [ ] Set to an `openAICompatible` profile ⇒ the cloud leg runs on the
  profile's base_url/model with `HOLDSPEAK_PROFILE_<ID>_KEY` preferred and
  the legacy env as fallback (test).
- [ ] Set to an `onDevice`/`desktop` profile or a dangling id ⇒ legacy
  fallback with a machine-readable reason, never a crash (test).
- [ ] The resolution-order matrix (provider local/auto/cloud × profile
  set/valid/dangling) is test-pinned in one place.
- [ ] No existing intel test needed modification.

## Test plan

- Unit: new cases in `tests/unit/` beside the existing intel provider tests
  (`uv run pytest -q tests/unit -k "intel or provider"` and read the output).
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py` before
  the PR.
- Manual / device: n/a — the live proof is HS-84-05's walk on `.43`.

## Notes / open questions

- The resolver must not force a DB import at module import time
  (`providers.py` is imported early); take the profiles lookup as a
  parameter or resolve lazily, matching how the ask route passes shapes in.
