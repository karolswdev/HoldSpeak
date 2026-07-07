# HS-84-03 — Settings pick, not type

- **Project:** holdspeak
- **Phase:** 84
- **Status:** done
- **Depends on:** HS-84-01, HS-84-02
- **Unblocks:** HS-84-05
- **Owner:** unassigned

## Problem

With both pipelines profile-capable, `/settings` still teaches the old
world: the meeting-intel section and the dictation-runtime section each ask
the user to type a base URL, a model name, and a key env var by hand
(`holdspeak/web/routes/system/settings.py:586` round-trips the raw fields;
the web settings page renders them). That is the third and fourth place to
author an endpoint. The settings surface should offer the profiles the user
already has, wear the pick's egress badge at the decision point, and send
authoring to `/profiles`.

## Scope

- In: the meeting-intel settings section becomes a profile picker: "Runs
  on: [Hub engine ▾ / <profile>…]" writing `meeting.intel_profile_id`; the
  local/auto/cloud provider control stays.
- In: the dictation-runtime section gets the same picker writing
  `dictation.runtime.profile_id`.
- In: each picker wears the picked target's egress badge (local / cloud +
  host — Phase 62 canon: a badge, never prose) and a "Manage profiles" door
  to `/profiles`.
- In: the raw `intel_cloud_*` / `openai_compatible_*` endpoint inputs leave
  the settings UI (the config fields survive as fallback per the phase
  design). `/api/settings` keeps accepting them so nothing breaks headless.
- In: screenshots of both sections, empty-profiles state included (the
  picker with no profiles offers the door, not a dead dropdown).
- Out: any other settings section; the `/profiles` page itself (it already
  authors shape correctly); key entry of any kind (keys are env-only, per
  canon — the picker may *state* "key: set on the hub / missing", read-only,
  if cheap).

## Acceptance criteria

- [ ] Both sections author by picker; saving round-trips the two new knobs
  through `/api/settings` (route test).
- [ ] No input in the settings UI accepts a base URL, model name, or key
  env for these two pipelines (page-content test).
- [ ] The badge shown matches the HS-84-04/hub-derived posture for the pick
  (local profile ⇒ local badge; endpoint profile ⇒ cloud + host).
- [ ] Empty-profiles state screenshot-verified alongside the populated one.
- [ ] Existing settings tests pass unmodified or with changes limited to
  the two sections.

## Test plan

- Unit: settings route round-trip tests
  (`uv run pytest -q tests/unit -k settings`, read the output).
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py`; rebuild
  the web bundle to verify (`web/`), commit source only.
- Manual / device: screenshot both sections in both states before the PR.

## Notes / open questions

- The settings page is the existing page-class surface — restyle nothing
  beyond the two sections; no new Alpine (standing rule); if the sections
  live in partials/modules, keep the Phase-54 density pattern.
- **Two surfaces, not one page (recorded):** the dictation runtime's
  endpoint fields never lived on `/settings` — they live on the `/dictation`
  Runtime tab (`RuntimeSection.astro` + `scripts/dictation/runtime.js`). The
  story's pickers landed on both surfaces; `/settings` owns meeting intel,
  the Runtime tab owns dictation. The API-key read-only state was skipped
  (keys are env-only; the picker shows nothing about them — the doctor
  names a missing `HOLDSPEAK_PROFILE_<ID>_KEY` in HS-84-04).
- **Screenshot pass caught a real bug:** the Alpine `x-model` select
  displayed "Hub default" while the model held the assigned id — the
  classic x-model + late `x-for` options race. Fixed with `:selected` on
  the option; the rig now asserts `input_value()` so it can't regress.
