# Phase 84 — One Runtime: final summary

- **Phase opened:** 2026-07-07
- **Phase closed:** 2026-07-07 (opened and shipped the same day)
- **Stories shipped:** 5/5

## Goal — was it met?

*"Every place the hub runs a model resolves through the ONE RuntimeProfile
layer; a raw endpoint URL is typed in exactly one place — the profile
editor."* **Yes.** The live walk is the proof in one run: a profile authored
once in the `/profiles` editor drove an agent chat, a meeting-intel artifact
reroute, and a dictation rewrite, with doctor naming it for both pipelines —
and no endpoint URL entered anywhere else.

## What the phase shipped

- **HS-84-01 — Meeting intelligence runs on a profile:**
  `meeting.intel_profile_id` + the resolver seam (`effective_intel_cloud`),
  adopted by ALL FOUR config→cloud-shape sites (plugins' default
  constructor + capability probe, the live session, the deferred-queue
  drain, the CLI); dangling/none falls back to the legacy shape
  byte-identically, with a named reason.
- **HS-84-02 — Dictation runs on a profile:**
  `dictation.runtime.profile_id` through the same rule (extracted as
  `_apply_runtime_profile`; the shared shape renamed `EffectiveEndpoint`).
  Recorded decision: an ADOPTED profile also selects the
  `openai_compatible` backend; every fallback leaves the configured backend
  untouched. The setup probe and trust block report the effective endpoint.
- **HS-84-03 — Settings pick, not type:** the `/settings` cloud section and
  the `/dictation` Runtime tab each author by a "Runs on" picker + egress
  badge + the `/profiles` door; the raw base-URL/model/key-env inputs left
  the UI. The eyeball pass caught a real Alpine `x-model` + late `x-for`
  select-display race, fixed and regression-asserted.
- **HS-84-04 — The honest doctor + one egress derivation:**
  `endpoint_egress` is the one badge constructor (routes/cadence/audit,
  wire shapes byte-equal); the run badge reports the EFFECTIVE endpoint
  (the find: it read the raw legacy field while the engine ran on the
  assigned profile); the "Runtime profiles" doctor check names per-pipeline
  resolution, dangling WARNs, and missing per-profile keys as the exact
  `HOLDSPEAK_PROFILE_<ID>_KEY`.
- **HS-84-05 — Docs + the live walk:** five guides re-taught
  ("author once, pick everywhere"; config fields documented as the
  fallback), guards 143/143; the six-beat walk on the real hub → `.43`.

## The finds of the phase

1. **Candidate S was mostly already shipped** (the scaffold survey): the
   contract, sync kind, CRUD, per-agent assignment, and both authoring
   surfaces landed earlier under HSM Phase 24 / the mesh / Phase 83 — the
   BACKLOG row had rotted. The phase became the honest remainder.
2. **The stale badge** (HS-84-04): once meeting intel adopted profiles, the
   default-cloud run badge could name the wrong host. Fixed at the shared
   derivation, test-pinned.
3. **The Alpine select race** (HS-84-03): the picker displayed "Hub
   default" while the model held the assignment. `:selected` + an
   `input_value()` assertion in the rig.

## Stories shipped

| ID | Title | PR |
|----|-------|----|
| HS-84-01 | Meeting intelligence runs on a profile | #287 |
| HS-84-02 | Dictation runs on a profile | #288 |
| HS-84-03 | Settings pick, not type | #289 |
| HS-84-04 | The honest doctor + one egress derivation | #290 |
| HS-84-05 | Docs + the live walk | the closing PR |

(The phase scaffold + BACKLOG reconciliation merged as #286.)

## Decisions

- Adopted profile ⇒ `openai_compatible` backend for dictation (assignment
  is "run it there"); fallbacks never touch the configured backend.
- **Legacy config fields stay** as the documented fallback shape
  (`intel_cloud_*`, `openai_compatible_*`): headless setups write them,
  they cost one resolver branch, and deleting them is migration pain with
  no behavior win. Parked deliberately, not filed as a phase.

## Numbers

Six PRs; 38 new tests across four files + one smoke updated; full suite
grew 3212 → 3250; docs/voice guards 143; 8 committed screenshots; two rigs
stay in `scripts/` (`screenshot_hs84_settings_pickers.py`,
`walk_hs84_live.py`) as regression rigs.

## Handoff to the next phase

- Available now: one resolver (`effective_intel_cloud` /
  `effective_dictation_llm` over `_apply_runtime_profile`), one badge
  constructor (`endpoint_egress`), the "Runtime profiles" doctor check, and
  pickers on both endpoint sections.
- Ops note for live proofs: restart the hub on merged code with
  `HOLDSPEAK_WEB_PORT=8765` pinned (a plain restart can fall back to an
  ephemeral port while 8765 is in TIME_WAIT).
- Read first: this file, then [BACKLOG.md](../BACKLOG.md) row S for the
  full shipped-where map of the profiles arc.
