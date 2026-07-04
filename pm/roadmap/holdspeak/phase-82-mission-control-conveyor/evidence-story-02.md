# Evidence — HS-82-02 — The bridge relays the three documents

**Status:** done (2026-07-04).

## The move

`holdspeak/missioncontrol_bridge.py` (the core: project-map reader,
CLI resolution in the Phase-12 pack's order, schema checks at the
door, typed `live | compatibility | unavailable` statuses) +
`holdspeak/web/routes/missioncontrol.py` (the three routes, thin,
`runner`/`map_path` as test seams per the design §1) + registration
in `web/routes/__init__.py` and `web_server.py`.

The documents are relayed byte-honest: the state test asserts the
served `feed` equals the fake CLI's document verbatim, no
reshaping. Schema drift (`feed_schema` 2, `sessions_schema` 99)
comes back as `compatibility` with a "proven against" detail; a
dead CLI as `unavailable` with the stderr tail; a timeout as
`unavailable`; the events `tail` clamps to the design's 1..100.

## Proof

- `uv run --extra test pytest tests/unit/test_web_routes_missioncontrol.py`
  — **11 passed** (map reader honesty, byte-honest relay,
  compatibility, unavailable, timeout, desk-global sessions, tail
  clamp).
- `uv run --extra test pytest tests/unit` — **2422 passed, 2
  skipped** (the llama_cpp skip is environmental, pre-existing).
- `uv run --extra dev ruff check …` — clean.

## What the repo's own guards taught (kept in, per the honesty bar)

1. The doc-drift guard failed the first run: `docs/` is user-facing
   and refuses roadmap vocabulary and em-dashes. The design doc
   moved to `docs/internal/MISSION_CONTROL_DESK.md` in this commit,
   with every phase-file link updated. The guard was right.
2. The API-surface guard failed next: the HTTP surface is a
   committed artifact. Regenerated
   (`uv run python scripts/gen_api_surface.py`) — 235 routes, now
   including the three `/api/missioncontrol/*` reads.
