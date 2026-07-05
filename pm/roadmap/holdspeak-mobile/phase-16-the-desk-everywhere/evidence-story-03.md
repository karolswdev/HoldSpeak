# Evidence — HSM-16-03 (the desktop hub surface for organization)

**Recorded done on the 2026-07-04 resume survey — pre-paid.**

The hub owns and serves the organization layer:

- `holdspeak/web/routes/primitives/` — `directories.py`, `kbs.py` (plus `notes.py`,
  `recipes.py`, `chains.py`, `workflows.py`, `profiles.py` and the shared `_shared.py` router
  pattern): CRUD over the canonical store, landed in Primitive Framework wave 2 ("the API
  stitch") and extended through wave 4's directory promotion.
- `holdspeak/web/routes/sync.py` — `GET /api/sync/pull` + `POST /api/sync/push` carry the
  organization kinds in the one `ChangeSet` envelope.
- The web desk (the front door, `web/src/desk/`) reads the same store — zones/directories and
  KBs render from the hub's truth, satisfying the story's "the web reads the same store" unblock.

Fresh targeted run, 2026-07-04:
`uv run pytest tests/unit/test_web_routes_primitives.py tests/unit/test_web_routes_sync.py
tests/unit/test_web_routes_sync_primitives.py tests/unit/test_db_primitives.py
tests/unit/test_primitive_contract.py` → **66 passed in 4.73s**.
