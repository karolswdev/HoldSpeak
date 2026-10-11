#!/usr/bin/env python3
"""Record the hub's own answers for the palette face tests (the test diet, 2026-10-11).

``web/src/desk/__tests__/palette.app.test.tsx`` ("Enter on the first row
opens that note") replays these answers through a mocked ``apiFetch``. Every
answer comes from the real hub (``MeetingWebServer`` through ``TestClient``)
on an isolated HOME and database, with the seed of
``tests/e2e/test_palette_enter_opens_the_note_glass.py``: one note titled
``Ledger cutover risks``, made by the notes route. Nothing is typed by hand,
so no field the face reads can be invented (the SCAR LAW). Each read keeps
its status: a route that refuses on this hub is replayed as that refusal.

One boot, in order:
  1. the note is made (``POST /api/notes``);
  2. the reads before Develop: the notes list, the note's thought status
     (``ordinary``), and the reads its window makes;
  3. the owner's Develop (``POST /api/thoughts/adopt``, the request
     ``NotePullout`` sends);
  4. the reads after Develop: the notes list, the thought status
     (``thought``), and the reads the Thought window makes.

Run it again when a producer's answer shape changes:

    HOME=$(mktemp -d) uv run python scripts/record_chrome_palette.py

It writes ``web/src/desk/__tests__/fixtures/palette-enter/recorded.json``.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "unit"))

from test_philo5_the_loop import _boot  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402

OUT = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "palette-enter" / "recorded.json"

TITLE = "Ledger cutover risks"
BODY = "- reconciliation job slow\n- rollback plan owner: Jordan"

# The reads the note window and the Thought window make on mount (found by
# replaying the face with an empty table and listing every path it asked for).
# `{note}` and `{thought}` are filled in after the seed.
# The desk's own read (``loadAll`` in web/src/desk/api.ts), both phases.
DESK_GETS = (
    "/api/notes", "/api/meetings?limit=24", "/api/sync/pull?limit=50", "/api/decisions", "/api/recipes",
    "/api/kbs", "/api/directories", "/api/chains", "/api/workflows", "/api/workbenches", "/api/projects",
    "/api/inference-targets", "/api/models", "/api/threads", "/api/roadmaps", "/api/repositories",
    "/api/coders/status", "/api/desk/needs-you", "/api/people/relationships", "/api/channels/destinations",
)
NOTE_GETS = (*DESK_GETS, "/api/thoughts/for-note/{note}")
THOUGHT_GETS = (
    *DESK_GETS,
    "/api/thoughts/for-note/{note}",
    "/api/thoughts/{thought}/workbench",
    "/api/thoughts/{thought}/context",
    "/api/thoughts/{thought}/original",
)


def _read(client: Any, path: str) -> dict[str, Any]:
    """One GET as the face receives it: the status and the hub's body."""
    response = client.get(path)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return {"status": response.status_code, "body": body}


def _ok(response: Any, path: str) -> Any:
    assert response.status_code in (200, 201), (path, response.status_code, response.text[:300])
    return response.json()


def record() -> dict[str, Any]:
    with pytest.MonkeyPatch.context() as mp:
        root = Path(tempfile.mkdtemp(prefix="palette-enter-"))
        hub = _boot(root, mp)
        try:
            c = hub.client
            note = _ok(c.post("/api/notes", json={"title": TITLE, "body_markdown": BODY, "tags": []}), "POST /api/notes")["note"]
            fill = {"note": note["id"]}
            before = {p.format(**fill): _read(c, p.format(**fill)) for p in NOTE_GETS}
            status = before[f"/api/thoughts/for-note/{note['id']}"]["body"]
            assert status["ownership"] == "ordinary", status
            pre = status["source_precondition"]
            adopt_body = {
                "request_id": "palette-enter-develop",
                "note_id": note["id"],
                "expected_source_content_sha256": pre["content_sha256"],
                "expected_source_last_modified": pre["last_modified"],
            }
            adopted = _ok(c.post("/api/thoughts/adopt", json=adopt_body), "POST /api/thoughts/adopt")
            fill["thought"] = adopted["thought"]["id"]
            after = {p.format(**fill): _read(c, p.format(**fill)) for p in THOUGHT_GETS}
            assert after[f"/api/thoughts/for-note/{note['id']}"]["body"]["ownership"] == "thought", after
            return {
                "note_id": note["id"],
                "thought_id": fill["thought"],
                "title": TITLE,
                "before": before,
                "adopt": {"request": adopt_body, "answer": adopted},
                "after": after,
            }
        finally:
            from holdspeak.db import reset_database

            reset_database()
            composition.install(composition.bare(label="record"))


def main() -> None:
    data = record()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}: {sorted(data['before'])} + {sorted(data['after'])}")


if __name__ == "__main__":
    main()
