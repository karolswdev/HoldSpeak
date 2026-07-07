# HS-84-04 — The honest doctor + one egress derivation

- **Project:** holdspeak
- **Phase:** 84
- **Status:** backlog
- **Depends on:** HS-84-01, HS-84-02
- **Unblocks:** HS-84-05
- **Owner:** unassigned

## Problem

Egress truth is derived in at least three places today:
`intel_egress_posture` reads the *config* provider only
(`holdspeak/intel/providers.py:256` — profile-blind), the ask route builds
its own `{scope, host}` dicts (`web/routes/primitives/ask.py:390-401`), and
`cadence.py` carries a hard-coded local dict. With profiles now feeding two
more pipelines, a profile-blind doctor would report "Local only" while a
profile ships transcripts to an endpoint — exactly the dishonesty this
product refuses. One derivation, everywhere.

## Scope

- In: one profile-aware egress helper (shape: `{scope, host?, label?}`)
  that takes an effective runtime shape (from the HS-84-01 resolver) and is
  the single source for doctor, `/api/setup/status`, and the route badges;
  the existing dicts in `ask.py` / `cadence.py` / `intel_egress_posture`
  converge on it.
- In: `holdspeak doctor` + `/api/setup/status` name, per pipeline (meeting
  intel, dictation), the profile it resolves to and the resulting posture —
  including the dangling-id fallback ("assigned profile missing — running
  on <fallback>") as a visible WARN/FAIL, and a note when a profile's
  `requires_key` is set but `HOLDSPEAK_PROFILE_<ID>_KEY` is absent.
- Out: any new UI; the badge *renderers* (cards/threads already render
  hub-reported badges); changing what counts as local vs cloud.

## Acceptance criteria

- [ ] One helper; the ask route's badge, cadence's local dict, and the
  doctor posture all call it (grep + tests).
- [ ] Doctor names the resolved profile per pipeline; test-pinned for:
  unset (legacy local), unset (legacy cloud), profile-cloud, dangling id,
  requires_key-without-key.
- [ ] The setup-status drift guard still holds (every doctor FAIL surfaces
  in `/api/setup/status` — `holdspeak/setup_status.py` adapter contract).
- [ ] Wire shapes of existing badge consumers unchanged (existing route
  tests pass unmodified).

## Test plan

- Unit: doctor/setup-status cases
  (`uv run pytest -q tests/ -k doctor`, read the output) + new helper tests.
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: n/a — HS-84-05's walk reads the doctor output live.

## Notes / open questions

- `intel_egress_posture`'s prose strings are user-facing via doctor; keep
  the badge-not-prose rule for UI surfaces, but doctor's terminal lines may
  stay sentences (they already are).
