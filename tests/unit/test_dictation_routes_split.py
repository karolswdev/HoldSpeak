"""HS-34-01: lock the dictation route table after the sub-package split.

The 1,607-line `web/routes/dictation.py` became a `routes/dictation/` sub-package
(intents / agent / project_docs / blocks / kb / pipeline) composed behind a stable
`build_dictation_router(ctx)`. This asserts the **full (path, method) set is
exactly** what it was before the split — the decomposition's behavior-preserving
contract. (Phase 34's shared route-table invariant; HS-34-02 adds its own.)
"""

from __future__ import annotations

from holdspeak.web.context import WebContext
from holdspeak.web.routes.dictation import build_dictation_router

# The canonical dictation route table (captured from the pre-split module).
_EXPECTED_ROUTES = {
    ("/api/intents/control", "GET"),
    ("/api/intents/profile", "PUT"),
    ("/api/intents/override", "PUT"),
    ("/api/intents/preview", "POST"),
    ("/api/dictation/project-context", "GET"),
    ("/api/dictation/agent-context", "GET"),
    ("/api/dictation/agent-hooks", "GET"),
    ("/api/dictation/agent-context/clear", "POST"),
    ("/api/dictation/agent-context/summarize", "POST"),
    ("/api/dictation/project-hs", "GET"),
    ("/api/dictation/project-hs", "PUT"),
    ("/api/dictation/project-doc-suggestion", "GET"),
    ("/api/dictation/project-doc-suggestion/apply", "POST"),
    ("/api/dictation/project-doc-suggestion/dismiss", "POST"),
    ("/api/dictation/block-templates", "GET"),
    ("/api/dictation/blocks", "GET"),
    ("/api/dictation/blocks", "POST"),
    ("/api/dictation/blocks/from-template", "POST"),
    ("/api/dictation/blocks/{block_id}", "PUT"),
    ("/api/dictation/blocks/{block_id}", "DELETE"),
    ("/api/dictation/project-kb", "GET"),
    ("/api/dictation/project-kb", "PUT"),
    ("/api/dictation/project-kb/starter", "POST"),
    ("/api/dictation/project-kb", "DELETE"),
    ("/api/dictation/readiness", "GET"),
    ("/api/dictation/dry-run", "POST"),
    # HS-39-02: session correction memory capture + list.
    ("/api/dictation/corrections", "GET"),
    ("/api/dictation/corrections", "POST"),
}


def _router_route_set() -> set[tuple[str, str]]:
    # A bare WebContext is enough: handlers read ctx only at request time, not
    # at router-build time.
    ctx = WebContext.__new__(WebContext)
    router = build_dictation_router(ctx)
    pairs: set[tuple[str, str]] = set()
    for route in router.routes:
        for method in route.methods:  # type: ignore[attr-defined]
            if method in {"HEAD", "OPTIONS"}:
                continue
            pairs.add((route.path, method))  # type: ignore[attr-defined]
    return pairs


def test_dictation_route_table_is_unchanged_after_split() -> None:
    assert _router_route_set() == _EXPECTED_ROUTES


def test_dictation_route_count_is_stable() -> None:
    assert len(_router_route_set()) == len(_EXPECTED_ROUTES) == 28
