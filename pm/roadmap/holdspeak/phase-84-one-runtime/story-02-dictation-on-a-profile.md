# HS-84-02 — Dictation runs on a profile

- **Project:** holdspeak
- **Phase:** 84
- **Status:** backlog
- **Depends on:** HS-84-01
- **Unblocks:** HS-84-03, HS-84-05
- **Owner:** unassigned

## Problem

The DIR-01 dictation pipeline is the other legacy consumer: its LLM leg is
constructed straight from `LLMRuntimeConfig.openai_compatible_base_url` /
`openai_compatible_model` / `openai_compatible_api_key_env`
(`holdspeak/config.py:328-344` → `plugins/dictation/assembly.py:128` →
`plugins/dictation/runtime.py:190`). Same shape as a profile, typed by hand
in a second place, with its own key convention. It should resolve through
the HS-84-01 seam.

## Scope

- In: `LLMRuntimeConfig.profile_id: Optional[str]` (config-version-safe,
  rides `/api/settings` like the existing runtime fields).
- In: pipeline assembly resolves the endpoint shape through the HS-84-01
  resolver when the knob is set; unset ⇒ today's `openai_compatible_*`
  construction, byte-identical.
- In: the resolver's optional-lookup posture proves out here — dictation
  assembly may run on CLI paths; when no profiles lookup is available the
  legacy shape wins and the reason says so.
- Out: settings UI (HS-84-03), doctor wording (HS-84-04), guidance text in
  `plugins/dictation/guidance.py` (rides HS-84-03/05 with the docs), any
  transcription/typing behavior.

## Acceptance criteria

- [ ] Knob unset ⇒ assembled pipeline runtime kwargs byte-identical to
  today (test).
- [ ] Knob set to a valid `openAICompatible` profile ⇒ the LLM leg carries
  the profile's base_url/model and prefers `HOLDSPEAK_PROFILE_<ID>_KEY`
  (test at the assembly seam, no model loaded).
- [ ] Dangling id / no lookup available ⇒ legacy shape + named reason,
  never a crash (test).
- [ ] `holdspeak/setup_runtime.py` and `setup_status.py` (which read
  `openai_compatible_base_url` for display) report the *effective* shape,
  not a stale raw field, when a profile is set.
- [ ] No existing dictation test needed modification.

## Test plan

- Unit: new cases beside the existing assembly/runtime tests
  (`uv run pytest -q tests/unit -k "dictation and (assembly or runtime)"`,
  read the output).
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: n/a — HS-84-05 walks a real dictation rewrite on `.43`.

## Notes / open questions

- If the setup_status change wants to name the profile (not just the URL),
  keep the wording minimal here — HS-84-04 owns the honest-reporting pass;
  this story only has to stop it lying.
