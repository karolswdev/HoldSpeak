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
    def __init__(self) -> None:
        self.handler = None

    def route(self, pattern, handler):
        assert pattern == "**/*"
        self.handler = handler


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
