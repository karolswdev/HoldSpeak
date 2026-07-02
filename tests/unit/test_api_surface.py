"""HS-72-02 — the API surface, declared (Phase 72, One Spine).

The HTTP surface is a committed artifact now (``docs/api-surface.json`` +
``docs/API_SURFACE.md``), generated from the REAL assembled app with per-route
consumers extracted from the real call sites. These tests keep it honest:

1. **The committed manifest matches the live app + call sites.** Adding,
   removing or renaming a route (or a client call) without regenerating fails
   here with a one-command fix.
2. **Clients only call routes the app serves.** Every extracted iOS/web call
   template matches a served route (the committed ``unmatched_calls`` must be
   empty) — a Swift or web call to a misspelled/removed path fails CI.
3. **Non-vacuity.** The manifest carries the load-bearing routes and the
   consumer split the repo's docs used to hand-maintain (and get wrong).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="the manifest enumerates the real app")

REPO = Path(__file__).parents[2]
MANIFEST = REPO / "docs" / "api-surface.json"
MANIFEST_MD = REPO / "docs" / "API_SURFACE.md"

_spec = importlib.util.spec_from_file_location(
    "gen_api_surface", REPO / "scripts" / "gen_api_surface.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_spec and gen)  # type: ignore[union-attr]


@pytest.fixture(scope="module")
def committed() -> dict:
    assert MANIFEST.exists(), (
        "docs/api-surface.json is missing — generate it: "
        "uv run python scripts/gen_api_surface.py"
    )
    return json.loads(MANIFEST.read_text())


@pytest.fixture(scope="module")
def live() -> dict:
    return gen.build_manifest()


def test_committed_manifest_matches_the_live_app(committed, live) -> None:
    assert committed["routes"] == live["routes"], (
        "the committed API-surface manifest drifted from the live app/call "
        "sites — regenerate: uv run python scripts/gen_api_surface.py"
    )


def test_committed_markdown_matches_the_manifest(committed) -> None:
    assert MANIFEST_MD.read_text() == gen.render_markdown(committed), (
        "docs/API_SURFACE.md drifted from the manifest — regenerate: "
        "uv run python scripts/gen_api_surface.py"
    )


def test_clients_only_call_served_routes(live) -> None:
    unmatched = live["unmatched_calls"]
    assert not unmatched["ios"], (
        "the iOS client calls paths the app does not serve: "
        f"{unmatched['ios']}")
    assert not unmatched["web"], (
        "the web app calls paths the app does not serve: "
        f"{unmatched['web']}")


def test_manifest_is_not_vacuous(committed) -> None:
    paths = {r["path"] for r in committed["routes"]}
    # Load-bearing routes that must exist as long as the product does.
    for expected in ("/api/sync/pull", "/api/sync/push", "/api/dictation/remote",
                     "/api/meetings", "/ws", "/health"):
        assert expected in paths, f"manifest lost {expected}"
    ios_routes = {r["path"] for r in committed["routes"] if "ios" in r["consumers"]}
    web_routes = {r["path"] for r in committed["routes"] if "web" in r["consumers"]}
    # The split ARCHITECTURE.md used to undercount, now measured:
    assert "/api/dictation/remote" in ios_routes
    assert "/api/sync/pull" in ios_routes
    assert "/api/dictation/dry-run" in web_routes
    assert len(ios_routes) >= 20, "the iOS consumer extraction went dark"
    assert len(web_routes) >= 80, "the web consumer extraction went dark"


def test_extractors_see_the_real_call_sites() -> None:
    """A moved/emptied source tree must fail loudly, not pass vacuously."""
    ios = gen.extract_ios_calls()
    web = gen.extract_web_calls()
    assert "/api/companion/status" in ios or "/api/coders/status" in ios, (
        "iOS extraction lost the coder-board calls — did the client move?")
    assert any(c.startswith("/api/dictation/") for c in web)
    assert len(ios) >= 15 and len(web) >= 60
