# Evidence — HS-72-02 — The API surface, declared

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## Files touched

- `scripts/gen_api_surface.py` — the generator: enumerates the REAL assembled
  app (the same `MeetingWebServer(WebRuntimeCallbacks(...))` construction the
  route pre-flight uses, so nothing can hide), extracts consumer call sites
  from `apple/Sources` + `apple/App` (Swift string literals, `\(…)`
  interpolations → wildcards) and `web/src` (`js/ts/astro` literals, `${…}` →
  wildcards; unterminated interpolations truncate to prefix fragments), and
  tags every route `ios`/`web`/both/server-only.
- `docs/api-surface.json` — the committed manifest: **229 routes** (incl. the
  two WebSocket routes `/ws` + `/api/devices/audio` and the static mount),
  each with methods, defining module, consumers. `unmatched_calls` empty on
  both surfaces.
- `docs/API_SURFACE.md` — the generated human view, grouped by defining
  module. Passes the full doc-drift guard (no dashes-in-prose, no roadmap
  vocabulary, no dangling links).
- `tests/unit/test_api_surface.py` — the snapshot guard: committed manifest ==
  live app (regenerate-command in the failure message), committed markdown ==
  rendered manifest, clients-only-call-served-routes, non-vacuity pins
  (`/api/sync/pull`, `/ws`, `/health`, the ios/web consumer floors), and an
  extractor-sees-real-call-sites canary.

## The measured surface (what the prose docs used to guess)

- 229 routes; **44 consumed by iOS**, **151 consumed by the web**, the rest
  server-only/pages/static. `docs/ARCHITECTURE.md`'s hand-written "narrow
  iPad client" description undercounts by roughly half — correcting it is
  HS-72-10, now with a generated artifact to link instead of a hand list.
- Generator bugs caught during calibration: FastAPI's WS wrapper is
  `APIWebSocketRoute` (a naive `WebSocketRoute` check silently dropped `/ws`
  from the manifest); Swift log/format strings with spaces leaked in as
  paths; JS template literals with nested parens (`${projectRootParam(…`)
  cannot close under a regex and are truncated to prefix fragments matched
  segment-wise.

## Verification artifacts

- `uv run python scripts/gen_api_surface.py` → "wrote docs/api-surface.json
  (229 routes)", zero unmatched-call warnings.
- `uv run pytest -q tests/unit/test_api_surface.py` → **5 passed**.
- `uv run pytest -q tests/unit/test_doc_drift_guard.py` → **15 passed** (the
  generated markdown is inside the guarded corpus).
- **Deliberate-drift red proofs (both directions), reverted:**
  - Added a scratch route (`/api/sync/scratch-drift-proof`) without
    regenerating → `test_committed_manifest_matches_the_live_app` failed
    with the regenerate hint.
  - Added a Swift literal calling `api/nonexistent/scratch-drift-proof` →
    `test_clients_only_call_served_routes` failed naming the path.
  - Both reverted; 5/5 green after.
- Full python suite at ship: **3056 passed, 38 skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] A committed, generated manifest with per-route consumers exists
      (`docs/api-surface.json` + `docs/API_SURFACE.md`).
- [x] Snapshot tests fail on undeclared routes (proven red).
- [x] Snapshot tests fail on client calls to undeclared paths (proven red).
- [x] Consumer extraction is real (call-site-derived, canary-guarded), not
      hand-maintained.

## Deviations from plan

- **Routers were NOT converted to `APIRouter(prefix=...)`.** The story
  allowed conversion "where the diff is mechanical"; with the manifest in
  place the conversion adds a large cosmetic diff across 12 routers without
  changing the declared surface (the manifest diff would be empty by
  definition). Skipped deliberately; if a later story touches a router
  wholesale (HS-72-06 splits `meetings.py`), it adopts the prefix style
  there.
- Consumer tags mark **fetch/WS call sites**, not page navigations — HTML
  page routes read "server only" by design (a navigation is not an API
  consumer).

## Follow-ups

- HS-72-03 regenerates the manifest as its rename proof (the diff must show
  exactly the eleven moved routes).
- HS-72-10 rewrites `docs/ARCHITECTURE.md`'s client sections to link the
  manifest instead of hand-listing routes.
