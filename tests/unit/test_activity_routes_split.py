"""HS-34-02: lock the activity route table after the sub-package split.

The 1,319-line / 38-handler `web/routes/activity.py` became a `routes/activity/`
sub-package (ledger / rules / enrichment / candidates / plugin_jobs) composed
behind a stable `build_activity_router(ctx)`. This asserts the full (path, method)
set is exactly what it was before the split — the behavior-preserving contract.
"""

from __future__ import annotations

from holdspeak.web.context import WebContext
from holdspeak.web.routes.activity import build_activity_router

_EXPECTED_ROUTES = {
    ("/api/activity/status", "GET"),
    ("/api/activity/records", "GET"),
    ("/api/activity/records", "DELETE"),
    ("/api/activity/refresh", "POST"),
    ("/api/activity/settings", "PUT"),
    ("/api/activity/domains", "POST"),
    ("/api/activity/domains/{domain}", "DELETE"),
    ("/api/activity/project-rules", "GET"),
    ("/api/activity/project-rules", "POST"),
    ("/api/activity/project-rules/{rule_id}", "PUT"),
    ("/api/activity/project-rules/{rule_id}", "DELETE"),
    ("/api/activity/project-rules/preview", "POST"),
    ("/api/activity/project-rules/apply", "POST"),
    ("/api/activity/enrichment/connectors", "GET"),
    ("/api/activity/enrichment/connectors/{connector_id}", "PUT"),
    ("/api/activity/extension/events", "POST"),
    ("/api/activity/enrichment/connectors/{connector_id}/dry-run", "GET"),
    ("/api/activity/enrichment/connectors/{connector_id}/annotations", "DELETE"),
    ("/api/activity/enrichment/connectors/{connector_id}/candidates", "DELETE"),
    ("/api/activity/annotations", "GET"),
    ("/api/activity/briefing", "GET"),
    ("/api/activity/enrichment/pipelines/{pipeline_id}/run", "POST"),
    ("/api/activity/enrichment/connectors/{connector_id}/runs", "GET"),
    ("/api/activity/enrichment/github/preview", "GET"),
    ("/api/activity/enrichment/github/run", "POST"),
    ("/api/activity/enrichment/jira/preview", "GET"),
    ("/api/activity/enrichment/jira/run", "POST"),
    ("/api/activity/meeting-candidates/preview", "GET"),
    ("/api/activity/meeting-candidates", "GET"),
    ("/api/activity/meeting-candidates", "POST"),
    ("/api/activity/meeting-candidates", "DELETE"),
    ("/api/activity/meeting-candidates/{candidate_id}/status", "PUT"),
    ("/api/activity/meeting-candidates/{candidate_id}/start", "POST"),
    ("/api/plugin-jobs", "GET"),
    ("/api/plugin-jobs/summary", "GET"),
    ("/api/plugin-jobs/process", "POST"),
    ("/api/plugin-jobs/{job_id}/retry-now", "POST"),
    ("/api/plugin-jobs/{job_id}/cancel", "POST"),
}


def _router_route_set() -> set[tuple[str, str]]:
    ctx = WebContext.__new__(WebContext)
    router = build_activity_router(ctx)
    pairs: set[tuple[str, str]] = set()
    for route in router.routes:
        for method in route.methods:  # type: ignore[attr-defined]
            if method in {"HEAD", "OPTIONS"}:
                continue
            pairs.add((route.path, method))  # type: ignore[attr-defined]
    return pairs


def test_activity_route_table_is_unchanged_after_split() -> None:
    assert _router_route_set() == _EXPECTED_ROUTES


def test_activity_route_count_is_stable() -> None:
    assert len(_router_route_set()) == len(_EXPECTED_ROUTES) == 38
