# Evidence — HSM-24-05 (web authors + uses profiles)

**Date:** 2026-06-28
**Story:** [story-05-web-profiles.md](./story-05-web-profiles.md)
**Result:** DONE. The web flagship is now a first-class authoring port for runtime profiles, at parity
with the Apple advanced screen — list + editor + per-agent "Runs on" picker — with the API key held by
the hub, never the browser. Full `uv run pytest` **3039 passed, 0 failed**; web built clean; the
rendered surfaces were Playwright-screenshotted with **0 page errors**.

## What shipped

**The `/profiles` surface (new):**
- `web/src/pages/profiles.astro` + `web/src/scripts/profiles-app.js` — a "Runtime Profiles" page: a
  card grid (name, kind, the shared egress badge, endpoint/model/context, or model-file) + a drawer
  editor (segmented Endpoint / On-device, base URL, model, context window, "Needs an API key").
- CRUD over the hub's `GET/POST/PUT/DELETE /api/profiles` (the routes 24-04 shipped). SHAPE only.
- **Key custody = the hub.** A cloud profile shows `requires_key` + the env var to set on the hub
  (`HOLDSPEAK_PROFILE_<id>_KEY`) and states "The browser never sees it." There is no key field and no
  key flow over the wire — a tighter never-sync posture than the plan's "hand it to the hub" (see the
  story's divergence note).
- **Honest n/a:** an on-device (GGUF) profile renders "⌂ On device" + "Unavailable — runs on a
  device." (a browser can't host a GGUF).

**The desk agent editor (per-agent assignment):**
- `web/src/pages/desk.astro` + `web/src/scripts/desk-app.js` — the agent form gains a "Runs on:
  [Profile ▾]" select (default "Hub default"), with a live egress hint for the chosen profile and an
  "Add a profile →" link when none exist; the agent card shows the assigned profile as an egress chip.
- `submitAgent` sends `profile_id`; `fromWireAgent` reads it; `loadProfiles` joins `loadAll`.

**Navigation + a pre-existing bug fix:**
- `TopNav.astro` / `AppLayout.astro` — "Profiles" added to the Configure group; the `Route` type
  gains `profiles`.
- **Fixed a dead nav link:** the TopNav linked `/desk` but the hub had no `/desk` route (the desk was
  reachable only at `/_built/desk/`). Added a real `/desk` page route in `pages.py` and brought both
  `/desk` and `/profiles` under the launch pre-flight (`PAGE_ROUTES`). This is the exact class of bug
  the pre-flight exists to catch; the desk had simply never been a `pages.py` route, so it had escaped
  the sweep.

## Acceptance criteria → proof

- **Web can author profiles + assign agents + run them; key custodian is the hub, never the browser.**
  The `/profiles` page does full CRUD over `/api/profiles`; the desk assigns `agent.profile_id`; the
  hub's `/api/agents/{id}/run` already resolves it (24-04). The editor has no key field — the secret
  is the hub's env var. ✅
- **n/a for device-only kinds on web.** On-device profile cards render "Unavailable — runs on a
  device." and the editor's on-device branch states the same. ✅
- **Route coverage.** `test_preflight_covers_every_html_route` passes with `/desk` + `/profiles` now
  served and listed; `npm run build` emits `/profiles/index.html` + `/desk/index.html`. ✅
- **No page errors.** A Playwright pass over `/profiles` (list + editor) and `/desk` (cards + agent
  form with the picker) reported **0 page errors** and the styles apply on the runtime-rendered DOM
  (screenshots captured: profiles list, profiles editor, desk cards, desk agent form). ✅
- **No blast radius.** Full `uv run pytest` 3039 passed (Python unchanged except the new `/desk` +
  `/profiles` page routes; web is source-only, bundle gitignored). ✅

## Screenshots

Captured under the session scratchpad (web bundle + screenshots are gitignored; the source is the
record): `profiles_list.png`, `profiles_editor.png`, `desk_cards.png`, `desk_agent_form.png`. The
agent card shows the "OpenRouter · Claude Sonnet" chip; the form shows the "Runs on" select with the
☁ openrouter.ai egress hint; the profile editor shows the on-the-hub key reference.

## Honest note

A live end-to-end run from the browser against a real cloud endpoint (a real key in
`HOLDSPEAK_PROFILE_<id>_KEY`) is the hub operator's walk; the authoring + assignment + resolution path
is proven by the route tests (24-04) with a fake intel and by the screenshot pass here.
