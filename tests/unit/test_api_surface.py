"""HS-72-02 — the API surface, read from the live app (Phase 72, One Spine).

The manifest is derived at check time from the REAL assembled app and the
real call sites; no copy is committed (2026-11-08: ``docs/api-surface.json``
and ``docs/API_SURFACE.md`` are generated on demand by
``scripts/gen_api_surface.py``). These tests assert invariants:

1. **Clients only call routes the app serves.** Every extracted iOS/web call
   template matches a served route — a Swift or web call to a misspelled or
   removed path fails here.
2. **Every dynamic web call resolves to a route.**
3. **Non-vacuity.** The manifest carries the load-bearing routes and the
   consumer split.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="the manifest enumerates the real app")

REPO = Path(__file__).parents[2]

_spec = importlib.util.spec_from_file_location(
    "gen_api_surface", REPO / "scripts" / "gen_api_surface.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_spec and gen)  # type: ignore[union-attr]


@pytest.fixture(scope="module")
def live() -> dict:
    return gen.build_manifest()


def test_every_dynamic_web_call_resolves_to_a_route(live) -> None:
    """A web call whose path is built at run time is tagged by hand
    (gen_api_surface's table) or it is unresolved: none may be."""
    assert live["unresolved_dynamic_calls"]["web"] == [], (
        "web calls whose route the census cannot name: "
        f"{live['unresolved_dynamic_calls']['web']}")


# Web calls to a path the app does not serve, each a single named defect.
# Strict: a fix fails here until its entry is removed.
KNOWN_UNSERVED_WEB_CALLS = {
    # The park in 96b8a3884 ("no client reads") took the route out, but
    # web/src/features/project-room/door/api.ts calls it through
    # `${PROVIDERS}/confluence/discover…`, which the census did not follow then.
    "GET /api/providers/confluence/discover*",
}


def test_clients_only_call_served_routes(live) -> None:
    unmatched = live["unmatched_calls"]
    assert not unmatched["ios"], (
        "the iOS client calls paths the app does not serve: "
        f"{unmatched['ios']}")
    assert set(unmatched["web"]) == KNOWN_UNSERVED_WEB_CALLS, (
        "the web app calls paths the app does not serve (or a known one was "
        f"fixed: remove its entry): {unmatched['web']}")


def test_manifest_is_not_vacuous(live) -> None:
    paths = {r["path"] for r in live["routes"]}
    # Load-bearing routes that must exist as long as the product does.
    for expected in ("/api/sync/pull", "/api/sync/push", "/api/dictation/remote",
                     "/api/meetings", "/ws", "/health"):
        assert expected in paths, f"manifest lost {expected}"
    ios_routes = {r["path"] for r in live["routes"] if "ios" in r["consumers"]}
    web_routes = {r["path"] for r in live["routes"] if "web" in r["consumers"]}
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


def test_a_dynamic_call_tags_nothing_by_itself(live) -> None:
    source = 'await apiFetch(`/api/${path}/${encodeURIComponent(id)}`, { method: "DELETE" });\n'
    assert gen.web_call_sites(source) == {("DELETE", "/api/*/*")}
    assert gen.extract_from_text(source) == set()
    routes = _routes(("DELETE", "/api/notes/{note_id}"), ("GET", "/api/cadence/loops/{loop_id}"))
    assert _web_tagged(routes, source) == set()
    loop = next(r for r in live["routes"] if r["path"] == "/api/cadence/loops/{loop_id}"
                and r["methods"] == ["GET"])
    assert "web" not in loop["consumers"]


def test_a_dynamic_call_with_no_hand_entry_is_listed_unresolved() -> None:
    routes = _routes(("DELETE", "/api/notes/{note_id}"))
    for route in routes:
        route["consumers"] = []
    found = [{"file": "web/src/a.ts", "method": "DELETE", "path": "/api/*/*"}]
    assert gen.apply_web_dynamic_calls(routes, [], found) == found
    hand = [{"site": "web/src/a.ts:9", "method": "DELETE",
             "routes": ["/api/notes/{note_id}"], "why": "w"}]
    assert gen.apply_web_dynamic_calls(routes, hand, found) == []
    assert routes[0]["consumers"] == ["web"]
    with pytest.raises(ValueError):
        gen.apply_web_dynamic_calls(routes, [{**hand[0], "method": "PUT"}], found)


def test_the_hand_resolved_dynamic_calls_tag_their_routes(live) -> None:
    hand = live["web_dynamic_calls"]["resolved_by_hand"]
    assert {(e["site"].split(":")[0], e["method"]) for e in hand} >= {
        ("web/src/desk/store/dataSlice.ts", "DELETE"),
        ("web/src/desk/components/DeskFilingStrip.tsx", "PUT"),
        ("web/src/desk/components/DeskFilingStrip.tsx", "DELETE"),
        ("web/src/pages/cores/history/DoorSection.tsx", "POST"),
    }
    assert live["unresolved_dynamic_calls"]["web"] == []
    web = {(m, r["path"]) for r in live["routes"] if "web" in r["consumers"] for m in r["methods"]}
    for entry in hand:
        for path in entry["routes"]:
            assert (entry["method"], path) in web


def test_a_table_row_takes_the_method_its_key_sends() -> None:
    source = (
        "export function updateUrl(kind: string, id: string): string | null {\n"
        "  const urls = {\n"
        "    note: `/api/notes/${id}`,\n"
        "    project: `/api/projects/${id}`,\n"
        "  } satisfies Record<string, string>;\n"
        "  return (urls as Record<string, string>)[kind] ?? null;\n"
        "}\n"
        "async function update(kind: string, id: string) {\n"
        "  const url = updateUrl(kind, id);\n"
        "  if (!url) return;\n"
        '  await apiRequest(url, { method: kind === "project" ? "PATCH" : "PUT" });\n'
        "}\n"
        "async function create(kind: string) {\n"
        "  const posts = {\n"
        '    note: ["/api/notes", "note"],\n'
        "  };\n"
        "  const [url, wireKey] = posts[kind];\n"
        '  await apiRequest(url, { method: "POST" });\n'
        "}\n"
    )
    assert gen.web_call_sites(source) == {
        ("PUT", "/api/notes/*"),
        ("PATCH", "/api/projects/*"),
        ("POST", "/api/notes"),
    }


def test_a_path_helper_a_wrapper_and_a_verb_parameter_are_followed() -> None:
    source = (
        "const base = (id: string) => `/api/programs/${id}`;\n"
        "export function read(id: string) { return apiFetch<Program>(base(id)); }\n"
        'export function patch(id: string) { return apiFetch(base(id), { method: "PATCH" }); }\n'
        'export const LOCAL_PATH = "/api/setup/local-ai";\n'
        "const act = useCallback(async (path: string) => {\n"
        '  await apiFetch<X>(path, { method: "POST" });\n'
        "}, []);\n"
        "const go = () => act(LOCAL_PATH);\n"
        "function verbEndpoint(node: string, verb: string): { url: string } {\n"
        "  return { url: `/api/coders/relay/${node}/${verb}` };\n"
        "}\n"
        "async function arm(node: string) {\n"
        '  const { url } = verbEndpoint(node, "arm");\n'
        '  await apiRequest(url, { method: "POST" });\n'
        "}\n"
        "async function steer(node: string) {\n"
        '  const { url } = verbEndpoint(node, "steer");\n'
        '  await apiRequest(url, { method: "POST" });\n'
        "}\n"
    )
    assert gen.web_call_sites(source) == {
        (gen.UNNAMED, "/api/programs/*"),
        ("PATCH", "/api/programs/*"),
        ("POST", "/api/setup/local-ai"),
        ("POST", "/api/coders/relay/*/arm"),
        ("POST", "/api/coders/relay/*/steer"),
    }


def test_a_url_builder_is_followed_into_each_template_and_call() -> None:
    """``${base(id)}/x``, ``${at(id)}/x``, ``repoUrl(id, "/x")`` and ``${CONST}/x``."""
    source = (
        "const base = (id: string) => `/api/programs/${encodeURIComponent(id)}`;\n"
        'export const start = (id: string) => apiFetch(`${base(id)}/start`, { method: "POST" });\n'
        "export const text = (id: string) => apiFetch(`${base(id)}/text`);\n"
        "const repoUrl = (repositoryId: string, suffix = \"\") =>\n"
        "  `/api/repositories/${encodeURIComponent(repositoryId)}${suffix}`;\n"
        'export const stage = (id: string) => apiFetch(repoUrl(id, "/stage"), { method: "POST" });\n'
        "export const tree = (id: string, s: string) => apiFetch(repoUrl(id, `/tree${s}`));\n"
        "export const one = (id: string) => apiFetch(repoUrl(id));\n"
        'const PROVIDERS = "/api/providers";\n'
        "export const jira = () => apiFetch(`${PROVIDERS}/jira/discover`);\n"
    )
    assert gen.web_call_sites(source) == {
        ("POST", "/api/programs/*/start"),
        (gen.UNNAMED, "/api/programs/*/text"),
        ("POST", "/api/repositories/*/stage"),
        (gen.UNNAMED, "/api/repositories/*/tree*"),
        (gen.UNNAMED, "/api/repositories/*"),
        (gen.UNNAMED, "/api/providers"),
        (gen.UNNAMED, "/api/providers/jira/discover"),
    }


def test_a_builder_built_on_a_builder_and_an_imported_builder() -> None:
    owner = (
        "export const LAUNCH = (id: string) => `/api/agent/launches/${encodeURIComponent(id)}`;\n"
        "export const DELIVER = (id: string) => `${LAUNCH(id)}/deliver`;\n"
    )
    user = (
        'import { DELIVER, LAUNCH } from "./owner";\n'
        "await apiFetch(LAUNCH(id));\n"
        'await apiFetch(DELIVER(id), { method: "POST" });\n'
    )
    exported = gen.exported_builders([owner])
    assert gen.web_call_sites(owner) == set()  # the definitions alone send nothing
    assert gen.web_call_sites(user, exported) == {
        (gen.UNNAMED, "/api/agent/launches/*"),
        ("POST", "/api/agent/launches/*/deliver"),
    }
    assert gen.web_call_sites(user) == set()  # not imported: not followed


def test_a_literal_union_parameter_fills_candidates_only() -> None:
    """``${verb}`` typed ``"start" | "park"`` gives one candidate per value;
    a candidate the app does not serve is dropped, not reported."""
    source = (
        "const base = (id: string) => `/api/programs/${id}`;\n"
        'export type Verb = "start" | "park";\n'
        "export async function programVerb(id: string, verb: Verb) {\n"
        '  return apiFetch(`${base(id)}/${verb}`, { method: "POST" });\n'
        "}\n"
    )
    candidates: set[tuple[str, str]] = set()
    assert gen.web_call_sites(source, (), candidates) == set()
    assert candidates == {("POST", "/api/programs/*/start"), ("POST", "/api/programs/*/park")}


def test_the_census_follows_the_real_builders(live) -> None:
    """Routes reached only through a builder carry the web tag."""
    web = {(m, r["path"]) for r in live["routes"] if "web" in r["consumers"] for m in r["methods"]}
    for expected in (
        ("POST", "/api/programs/{program_id}/start"),            # ${base(id)} + a Verb union
        ("POST", "/api/recordings/{recording_id}/retry"),        # ${at(id)}
        ("POST", "/api/repositories/{repository_id}/stage"),     # repoUrl(id, "/stage")
        ("GET", "/api/projects/{project_id}/briefs/route"),      # ${project(id)}
        ("POST", "/api/notes/{note_id}/outcomes/find"),          # ${base(noteId)}
        ("POST", "/api/agent/launches/{launch_id}/deliver"),     # a builder on a builder
        ("POST", "/api/setup/local-ai/cancel"),                  # ${LOCAL_AI_PATH}
    ):
        assert expected in web, expected


def test_parked_code_is_not_read() -> None:
    assert not any("_parked" in p.parts for p in gen._web_files())
    # web.routes.desk_parked is live (it serves /api/desk/parked); a parked
    # module sits in a ``_parked`` package.
    assert not any("._parked." in f".{r['module']}." for r in gen.build_app_routes())
