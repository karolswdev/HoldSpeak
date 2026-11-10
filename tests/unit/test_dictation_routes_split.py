"""Dictation routes use declared operations and keep static template routes reachable."""

from holdspeak import operations
from holdspeak.web.context import WebContext
from holdspeak.web.routes.dictation import build_dictation_router


def test_dictation_routes_come_from_their_declared_rows():
    router = build_dictation_router(WebContext(get_state=dict))
    rows = {
        row.http: row for row in operations.DICTATION_OPERATIONS if row.http is not None
    }
    found = set()
    for route in router.routes:
        for method in route.methods:
            key = (method, route.path)
            assert key in rows
            assert key not in found
            assert route.endpoint.__name__ == rows[key].handler
            found.add(key)


def test_template_creation_precedes_the_block_id_route():
    router = build_dictation_router(WebContext(get_state=dict))
    paths = [route.path for route in router.routes]
    assert paths.index("/api/dictation/blocks/from-template") < paths.index(
        "/api/dictation/blocks/{block_id}"
    )
