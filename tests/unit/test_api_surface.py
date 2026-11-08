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


def test_committed_unresolved_calls_match_the_live_sources(committed, live) -> None:
    assert committed["unresolved_dynamic_calls"] == live["unresolved_dynamic_calls"], (
        "the committed unresolved dynamic calls drifted from web/src — "
        "regenerate: uv run python scripts/gen_api_surface.py"
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
    assert "/api/coders/status" in ios, (
        "iOS extraction lost the coder-board calls — did the client move?")
    assert any(c.startswith("/api/dictation/") for c in web)
    assert len(ios) >= 15 and len(web) >= 60


def test_committed_openapi_matches_reference_app() -> None:
    """Declared schemas remain real; raw Request semantics remain outside them."""
    declared = json.loads((REPO / "docs/generated/openapi.json").read_text())
    live = gen.build_reference_app().openapi()
    # Export provenance is documentation metadata, not a server schema field.
    declared["info"].pop("x-philo-note")
    declared["info"].pop("x-source-snapshot")
    assert declared == live, "OpenAPI drift: run scripts/philo_openapi_reference.py with isolated HOME"


_RESOURCE_ROUTE = "/api/projects/{project_id}/resources/{resource_ref:path}"


def test_a_nested_template_literal_maps_to_its_route() -> None:
    """``${…}`` with a template inside reads whole: each one is a path param."""
    source = (
        "await apiFetch(\n"
        "  `/api/projects/${encodeURIComponent(project.id)}/resources/"
        "${encodeURIComponent(`note:${noteId}`)}`,\n"
        '  { method: "PUT", json: { relationship: "related" } },\n'
        ");\n"
    )
    calls = gen.extract_from_text(source)
    assert "/api/projects/*/resources/*" in calls
    assert any(gen._route_matches(c, _RESOURCE_ROUTE) for c in calls)


def test_a_path_in_a_variable_one_line_above_is_found() -> None:
    source = (
        "const url = `/api/briefs/${encodeURIComponent(briefId)}/keep`;\n"
        'await apiFetch(url, { method: "POST" });\n'
    )
    calls = gen.extract_from_text(source)
    assert calls == {"/api/briefs/*/keep"}
    assert gen._route_matches("/api/briefs/*/keep", "/api/briefs/{brief_id}/keep")


def test_a_plain_string_still_maps() -> None:
    calls = gen.extract_from_text('await apiFetch("/api/dictation/dry-run?x=1");')
    assert calls == {"/api/dictation/dry-run"}


def test_a_non_api_string_is_ignored() -> None:
    source = (
        'const label = "Add to project";\n'
        "const note = `note:${noteId}`;\n"
        "const href = `https://example.com/api/${id}`;\n"
    )
    assert gen.extract_from_text(source) == set()


def _routes(*rows: tuple[str, str]) -> list[dict]:
    return [{"path": path, "methods": [method], "module": "m"} for method, path in rows]


def _web_tagged(routes: list[dict], source: str) -> set[tuple[str, str]]:
    calls = {
        site for site in gen.web_call_sites(source) if not gen._is_dynamic(site[1])
    }
    tagged, _, _ = gen.match_consumers(routes, set(), calls)
    return {(r["methods"][0], r["path"]) for r in tagged if "web" in r["consumers"]}


def test_a_put_call_does_not_tag_the_get_route_of_the_same_path() -> None:
    routes = _routes(("GET", "/api/notes/{note_id}"), ("PUT", "/api/notes/{note_id}"))
    source = 'await apiFetch(`/api/notes/${id}`, { method: "PUT", json: {} });\n'
    assert _web_tagged(routes, source) == {("PUT", "/api/notes/{note_id}")}


def test_a_delete_route_with_no_web_delete_call_is_server_only() -> None:
    routes = _routes(("GET", "/api/chains/{chain_id}"), ("DELETE", "/api/chains/{chain_id}"))
    source = "const chain = await apiFetch(`/api/chains/${id}`);\n"
    assert _web_tagged(routes, source) == {("GET", "/api/chains/{chain_id}")}


def test_the_method_comes_from_a_ternary_a_helper_or_a_variable_use() -> None:
    source = (
        'await apiFetch(`/api/kbs/${a}`, { method: on ? "DELETE" : "PUT" });\n'
        "await apiDelete(`/api/skills/${b}`);\n"
        "const url = `/api/briefs/${c}/keep`;\n"
        'await apiFetch(url, { method: "POST" });\n'
    )
    assert gen.web_call_sites(source) == {
        ("DELETE", "/api/kbs/*"),
        ("PUT", "/api/kbs/*"),
        ("DELETE", "/api/skills/*"),
        ("POST", "/api/briefs/*/keep"),
    }


def test_a_route_named_in_a_comment_is_not_a_call() -> None:
    source = "// POST /api/sync/push\n/** `/api/cadence/brief` */\n"
    assert gen.web_call_sites(source) == set()


def test_a_dynamic_call_tags_nothing_and_is_listed_unresolved(live) -> None:
    source = 'await apiFetch(`/api/${path}/${encodeURIComponent(id)}`, { method: "DELETE" });\n'
    assert gen.web_call_sites(source) == {("DELETE", "/api/*/*")}
    assert gen.extract_from_text(source) == set()
    routes = _routes(("DELETE", "/api/notes/{note_id}"), ("GET", "/api/cadence/loops/{loop_id}"))
    assert _web_tagged(routes, source) == set()
    assert {
        "file": "web/src/desk/store/dataSlice.ts",
        "method": "DELETE",
        "path": "/api/*/*",
    } in live["unresolved_dynamic_calls"]["web"]
    loop = next(r for r in live["routes"] if r["path"] == "/api/cadence/loops/{loop_id}"
                and r["methods"] == ["GET"])
    assert "web" not in loop["consumers"]
