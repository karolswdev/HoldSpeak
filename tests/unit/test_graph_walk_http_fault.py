"""PHILO-3-01: the rig's `http_fault` boundary is performed at the browser, or blocks."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("graph_walk_http_fault", REPO / "scripts/graph_walk.py")
gw = importlib.util.module_from_spec(_spec)
sys.modules["graph_walk_http_fault"] = gw
_spec.loader.exec_module(gw)


class _Route:
    def __init__(self, method: str, url: str) -> None:
        self.request = type("R", (), {"method": method, "url": url})()
        self.fulfilled: dict | None = None
        self.fell_back = False

    def fulfill(self, **kw):
        self.fulfilled = kw

    def fallback(self):
        self.fell_back = True


class _Page:
    url = "http://127.0.0.1:1/?token=t"

    def __init__(self) -> None:
        self.handler = None
        self.unrouted: list[str] = []

    def route(self, pattern, handler):
        assert pattern == "**/*"
        self.handler = handler

    def unroute(self, pattern):
        self.unrouted.append(pattern)
        self.handler = None


class _Hub:
    url = "http://127.0.0.1:1"


def _prov():
    return {"fixture_hashes": {}, "boundary_substitutions": [], "restarts": []}


def test_http_fault_blocks_without_a_page():
    with pytest.raises(gw.Blocked) as raised:
        gw.run_step({"kind": "boundary", "label": "x", "substitute": "http_fault",
                     "method": "POST", "path": "/api/decisions", "status": 500},
                    page=None, hub=None, provenance=_prov())
    assert "browser boundary" in str(raised.value)


def test_http_fault_answers_only_the_named_request_times_then_falls_back():
    page, prov = _Page(), _prov()
    record = gw.run_step({"kind": "boundary", "label": "hub fault", "substitute": "http_fault",
                          "method": "POST", "path": "/api/decisions", "status": 500, "times": 1},
                         page=page, hub=None, provenance=prov)
    other = _Route("GET", "http://127.0.0.1:1/api/decisions")
    page.handler(other)
    assert other.fell_back and other.fulfilled is None
    hit = _Route("POST", "http://127.0.0.1:1/api/decisions?token=t")
    page.handler(hit)
    assert hit.fulfilled["status"] == 500
    again = _Route("POST", "http://127.0.0.1:1/api/decisions")
    page.handler(again)
    assert again.fell_back
    assert record["fulfilled"] == ["http://127.0.0.1:1/api/decisions?token=t"]
    assert prov["boundary_substitutions"][0]["substitute"] == "http_fault"


def test_http_fault_matches_the_hub_origin_only():
    page, prov = _Page(), _prov()
    gw.run_step({"kind": "boundary", "label": "f", "substitute": "http_fault",
                 "method": "POST", "path": "/api/decisions", "status": 500, "times": 5},
                page=page, hub=_Hub(), provenance=prov)
    for foreign in ("http://127.0.0.1:2/api/decisions",      # another port
                    "https://127.0.0.1:1/api/decisions",     # another scheme
                    "http://example.com/api/decisions"):     # another host
        route = _Route("POST", foreign)
        page.handler(route)
        assert route.fell_back and route.fulfilled is None, foreign
    own = _Route("POST", "http://127.0.0.1:1/api/decisions")
    page.handler(own)
    assert own.fulfilled["status"] == 500


def test_http_fault_lift_removes_the_faults_and_is_recorded():
    page, prov = _Page(), _prov()
    gw.run_step({"kind": "boundary", "label": "f", "substitute": "http_fault",
                 "method": "GET", "path": "/api/decisions", "status": 500, "times": 99},
                page=page, hub=_Hub(), provenance=prov)
    record = gw.run_step({"kind": "boundary", "label": "hub back", "substitute": "http_fault_lift"},
                         page=page, hub=_Hub(), provenance=prov)
    assert page.unrouted == ["**/*"] and page.handler is None
    assert "unroute" in record["seam"]
    assert [b["substitute"] for b in prov["boundary_substitutions"]] == ["http_fault", "http_fault_lift"]
    with pytest.raises(gw.Blocked):
        gw.run_step({"kind": "boundary", "label": "x", "substitute": "http_fault_lift"},
                    page=None, hub=None, provenance=_prov())
