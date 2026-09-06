"""Fixture MCP server entry for HS-165-05 walk test.

Runs the real holdspeak MCP sidecar with ONE fixture seam: the watch
snapshot fetcher reads from a JSON file (HOLDSPEAK_TEST_SNAPSHOT_FILE)
instead of calling the gh CLI.  The subprocess boundary, JSON-RPC
protocol, auth, tool dispatch, and service composition are all real.

Usage:
    HOLDSPEAK_TEST_SNAPSHOT_FILE=/path/to/snapshot.json \
        uv run python -m tests.integration._mcp_walk_server
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

from holdspeak.principals import Principal


def _fixture_fetcher(
    principal: Principal,
    *,
    connector_id: str,
    query_kind: str,
    query: dict[str, Any],
) -> list[dict[str, Any]]:
    """Read the snapshot from the file at HOLDSPEAK_TEST_SNAPSHOT_FILE."""
    path = os.environ.get("HOLDSPEAK_TEST_SNAPSHOT_FILE", "")
    if not path or not os.path.exists(path):
        raise RuntimeError(
            f"HOLDSPEAK_TEST_SNAPSHOT_FILE={path!r} does not exist"
        )
    with open(path) as f:
        return json.load(f)


def main() -> int:
    """Boot the real sidecar with the fixture fetcher injected."""
    import holdspeak.services.watch_sources as ws_mod
    import holdspeak.mcp.families.project as proj_fam
    from holdspeak.services.watch_service import WatchService
    from holdspeak.mcp.server import serve

    # Patch the module-level _watch_service factory to inject the
    # fixture fetcher into every WatchService instance it creates.
    _original_watch_service = proj_fam._watch_service

    def _patched_watch_service():
        from holdspeak.db import get_database
        db = get_database()
        return WatchService(db, snapshot_fetcher=_fixture_fetcher)

    proj_fam._watch_service = _patched_watch_service

    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
