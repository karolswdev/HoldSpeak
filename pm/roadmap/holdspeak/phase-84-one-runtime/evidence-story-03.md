# Evidence — HS-84-03 — Settings pick, not type

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-84-03-settings-pick-not-type` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `web/src/pages/settings.astro` — the Cloud & advanced section's three raw
  inputs (Cloud model / API key env var / OpenAI-compatible base URL) replaced
  by the "Runs on" picker (`#set-intel-profile`, bound to
  `meeting.intel_profile_id`) + the egress chip + the "Manage profiles →"
  door; `.runs-on-row`/`.egress-chip` styles.
- `web/src/scripts/settings-app.js` — `profiles` loaded best-effort from
  `/api/profiles`; `profileOptionLabel`/`intelEgressBadge` helpers (picked ⇒
  `☁ host` / `⌂ hub engine`; unset ⇒ the honest legacy posture); save
  normalizes the knob; legacy-field validation skipped when a profile is
  picked.
- `web/src/components/dictation/RuntimeSection.astro` — the three
  `rt-openai-*` inputs replaced by the "Runs on profile" picker + badge +
  door; the timeout stays, relabeled "Endpoint timeout seconds".
- `web/src/scripts/dictation/runtime.js` — profiles cached on `rtState`,
  picker rendered with a `— missing` ghost option for a dangling assignment,
  badge updates on change, the meta banner names `runs on: <profile>`, and
  the save payload sends `profile_id` instead of the legacy endpoint fields
  (the settings route preserves saved values when omitted).
- `scripts/screenshot_hs84_settings_pickers.py` — the story's rig: real app,
  scratch DB, Playwright; shoots both sections in both states and ASSERTS
  the claims (badge text, raw inputs absent, banner, picker display value).
- `tests/integration/test_web_server.py` — the /settings smoke updated from
  the removed raw-field string to the new picker facts (the one change, in
  the affected section, per the story's AC).
- `pm/roadmap/holdspeak/phase-84-one-runtime/screenshots/` — 4 committed
  PNGs (`settings-cloud` / `dictation-runtime` × `empty` / `picked`).

## Verification artifacts

- `uv run python scripts/screenshot_hs84_settings_pickers.py` →
  **HS-84-03 SCREENSHOTS OK** with every claim asserted (badge equals
  `☁ 192.168.1.43:8080`, `#set-intel-profile` displays the assigned profile,
  raw base-URL inputs count 0 on both surfaces, banner carries `runs on:`).
- `cd web && npm run build` → 17 pages, complete; `npx vitest run` →
  **57 passed**. Bundle rebuilt to verify; source only committed.
- Guards + settings suites: `uv run pytest -q tests/unit -k "settings or
  density or page"` → **54 passed**.
- `uv run pytest -q tests/integration/test_web_server.py` → **93 passed**
  (after the one smoke update below).
- Full suite `uv run pytest -q --ignore=tests/e2e/test_metal.py`: the first
  run finished **1 failed, 3236 passed, 37 skipped** — the failure was the
  /settings smoke asserting the REMOVED raw-field string ("OpenAI-compatible
  base URL"), i.e. the story doing its job; after the one-test update the
  full re-run is green: **3237 passed, 37 skipped, 2 warnings in 244.35s**.

## Acceptance criteria — re-checked

- [x] Both sections author by picker; the two knobs round-trip through
  `/api/settings` — pickers proven live by the rig; the round-trip itself
  was pinned by HS-84-01/02's route tests (`test_settings_route_round_trips_
  intel_profile_id` / `_dictation_profile_id`).
- [x] No input accepts a base URL, model name, or key env for the two
  pipelines — asserted in the rig (`#rt-openai-base-url` count 0, the
  settings placeholder gone) and in the updated smoke test.
- [x] The badge matches the derived posture — asserted: picked LAN profile ⇒
  `☁ 192.168.1.43:8080`; unset + local provider ⇒ `⌂ local` (visible in the
  empty-state shot).
- [x] Empty-profiles state screenshot-verified alongside the populated one —
  4 PNGs committed; empty pickers offer `Hub default` / `None — backend
  above` + the door, not a dead dropdown.
- [x] Existing settings tests pass with changes limited to the two sections —
  exactly one test updated (the /settings smoke pinning the removed string).

## Deviations from plan

- The dictation endpoint fields turned out to live on the `/dictation`
  Runtime tab, not `/settings` — the pickers landed on both real surfaces
  (recorded in the story Notes).
- The optional read-only "key: set on the hub" state was skipped — keys stay
  invisible here; HS-84-04's doctor names a missing per-profile key.
- The eyeball pass caught a REAL bug: the Alpine `x-model` select displayed
  "Hub default" while the model held the assigned id (x-model + late `x-for`
  options race). Fixed with `:selected`; the rig now asserts
  `input_value()` so it cannot regress silently.

## Follow-ups

- HS-84-05's docs must reteach the two sections ("author a profile once,
  pick it everywhere") — the guides still describe typing a base URL.
- The screenshot rig stays in `scripts/` as this story's regression rig.
