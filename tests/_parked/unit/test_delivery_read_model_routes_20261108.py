"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/unit/test_delivery_read_model.py``: test_events_route_replays_from_the_cursor. Not collected.
"""
from __future__ import annotations
"""Delivery collector + read model + route tests (HS-94-02).

Two disciplines side by side:

- the END-TO-END class runs the VENDORED dw at `.githooks/dw` as a
  real subprocess against a real scratch rails repo (the counterpart
  contract discipline, tests/unit/test_dw_counterpart_contract.py);
- the behavioral classes use a counting fake runner (the
  mission-control seam) to PROVE the §11 economics: single-flight
  coalescing, cached reads that never shell out, last-known-good
  retention, and per-capability schema degradation.
"""


import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery import DeliveryCollector, DeliveryRegistry
from holdspeak.delivery.read_model import compose_cursor, parse_cursor
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery import build_delivery_router

REPO_ROOT = Path(__file__).resolve().parents[2]
DW = REPO_ROOT / ".githooks" / "dw"

SECRET_ORIGIN = "https://robot:hush-token-7@example.test/owner/rails.git"

# ── fixtures: real scratch repos ─────────────────────────────────────

PHASE_TABLE = """# Phase 1 — Alpha

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| DM-1-01 | First thing | in-progress | [story-01-first.md](story-01-first.md) | [evidence-story-01.md](evidence-story-01.md) |
"""

STORY = """# DM-1-01 - First thing

- **Status:** in-progress

The story body.
"""

EVIDENCE = """# Evidence — DM-1-01

- **Story:** DM-1-01

Narrative proof.
"""

README = """# Demo

- **Story ID prefix:** DM

**Current phase:** [Phase 1](phase-1-alpha/current-phase-status.md)
"""


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True, capture_output=True, text=True,
    )


def _make_rails_repo(tmp_path: Path, name: str = "rails") -> Path:
    repo = tmp_path / name
    phase = repo / "pm" / "roadmap" / "demo" / "phase-1-alpha"
    phase.mkdir(parents=True)
    (repo / "pm" / "roadmap" / "demo" / "README.md").write_text(README, encoding="utf-8")
    (phase / "current-phase-status.md").write_text(PHASE_TABLE, encoding="utf-8")
    (phase / "story-01-first.md").write_text(STORY, encoding="utf-8")
    (phase / "evidence-story-01.md").write_text(EVIDENCE, encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed rails fixture")
    _git(repo, "remote", "add", "origin", SECRET_ORIGIN)
    return repo


def _make_plain_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")
    return repo


def _registry(tmp_path: Path) -> DeliveryRegistry:
    return DeliveryRegistry(
        tmp_path / "registry.json", map_path=tmp_path / "absent-map.json"
    )


def _real_dw_argv(root: Path) -> list[str]:
    return [sys.executable, str(DW), "--root", str(root)]


def _dw(root: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(DW), "--root", str(root), *args],
        capture_output=True, text=True,
    )


# ── fixtures: the counting fake dw ───────────────────────────────────

def _caps_doc(feed_schema: int = 1, events_schema: int = 2) -> dict:
    return {
        "capabilities_schema": 1,
        "schemas": {
            "feed_schema": feed_schema,
            "events_schema": events_schema,
            "sessions_schema": 1,
            "evidence_schema": 1,
        },
        "statuses": ["backlog", "ready", "in-progress", "blocked", "done"],
        "done_statuses": ["done"],
        "verbs": ["story.status", "story.create"],
        "features": {"events_cursor": True},
    }


def _feed_doc(tree: str = "t1") -> dict:
    return {
        "feed_schema": 1,
        "generated_at_tree": tree,
        "projects": [
            {
                "slug": "demo",
                "prefix": "DM",
                "current_phase": {"number": 1, "title": "Alpha", "status": "open",
                                  "stories_done": 0, "stories_total": 1},
                "next_story": None,
                "phases": [],
                "stories": [
                    {"story_id": "DM-1-01", "title": "First thing",
                     "status": "in-progress", "phase": 1, "evidence_exists": True},
                ],
                "warnings": 0,
            }
        ],
    }


class FakeDw:
    """A per-repo fake dw with an append-only event journal and a call
    counter — the seam that proves invocation economics."""

    def __init__(self):
        self.calls: list[tuple[str, str]] = []  # (verb, cwd)
        self.docs: dict[str, dict[str, dict]] = {}  # cwd -> verb -> doc
        self.events: dict[str, list[dict]] = {}  # cwd -> journal
        self.broken: set[str] = set()
        self.protocol_incompatible: set[str] = set()
        self.delay: float = 0.0
        self._lock = threading.Lock()

    def add_repo(self, path: Path, *, caps=None, feed=None) -> None:
        cwd = str(path)
        self.docs[cwd] = {
            "capabilities": caps or _caps_doc(),
            "state": feed or _feed_doc(),
        }
        self.events.setdefault(cwd, [])

    def emit(self, path: Path, event: dict) -> None:
        self.events[str(path)].append(event)

    def __call__(self, argv, cwd=None):
        verb = next(
            (a for a in argv if a in ("capabilities", "state", "events")), "?"
        )
        with self._lock:
            self.calls.append((verb, str(cwd)))
        if self.delay:
            time.sleep(self.delay)
        if str(cwd) in self.broken:
            return SimpleNamespace(returncode=3, stdout="", stderr="boom")
        if str(cwd) in self.protocol_incompatible and verb == "capabilities":
            return SimpleNamespace(returncode=2, stdout="", stderr="invalid choice")
        repo_docs = self.docs.get(str(cwd))
        if repo_docs is None:
            return SimpleNamespace(returncode=1, stdout="", stderr="unknown repo")
        if verb == "events":
            after = 0
            if "--after" in argv:
                after = int(argv[argv.index("--after") + 1])
            journal = self.events[str(cwd)]
            fresh = [
                {**event, "event_id": str(index)}
                for index, event in enumerate(journal, start=1)
                if index > after
            ]
            doc = {
                "events_schema": 2,
                "source_cursor": str(len(journal)),
                "events": fresh,
            }
        else:
            doc = repo_docs[verb]
        return SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")


def _fake_collector(tmp_path, fake, repos, **kwargs):
    registry = _registry(tmp_path)
    for label, repo in repos:
        registry.register(str(repo), label=label)
        fake.add_repo(repo.resolve())
    collector = DeliveryCollector(
        registry,
        runner=fake,
        dw_argv_factory=lambda root: ["dw"],
        max_age_seconds=kwargs.pop("max_age_seconds", 3600.0),
        **kwargs,
    )
    return collector


def _walk_strings(node) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            out.append(str(key))
            out.extend(_walk_strings(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_walk_strings(item))
    elif isinstance(node, str):
        out.append(node)
    return out


def assert_wire_clean(payload, tmp_path: Path) -> None:
    """The §12/§13 walk: no raw path, no credential, in ANY wire text."""
    for text in _walk_strings(payload):
        assert str(tmp_path) not in text, text
        assert "hush-token-7" not in text, text
        assert "robot:" not in text, text


# ── end to end against the real vendored dw ─────────────────────────


# ── §11 economics with the counting fake ─────────────────────────────


# ── the routes ───────────────────────────────────────────────────────


def _route_client(tmp_path, fake, repos):
    registry_path = tmp_path / "route-registry.json"
    registry = DeliveryRegistry(registry_path, map_path=tmp_path / "absent.json")
    for label, repo in repos:
        registry.register(str(repo), label=label)
        fake.add_repo(repo.resolve())
    collector = DeliveryCollector(
        registry, runner=fake, dw_argv_factory=lambda root: ["dw"],
        max_age_seconds=3600.0,
    )
    app = FastAPI()
    app.include_router(
        build_delivery_router(WebContext(get_state=lambda: {}), collector=collector)
    )
    return TestClient(app), collector


class TestDeliveryRoutes:
    def test_events_route_replays_from_the_cursor(self, tmp_path):
        fake = FakeDw()
        repo = _make_plain_repo(tmp_path, "r1")
        client, collector = _route_client(tmp_path, fake, [("demo", repo)])
        first = client.get("/api/delivery/events").json()
        assert first["delivery_schema"] == 1
        assert first["events"] == []

        fake.emit(repo.resolve(), {"ts": "t", "event": "gate_refusal",
                                   "project": "demo", "story": "DM-1-01",
                                   "detail": {"rule": "story-evidence"}, "tree": "t"})
        collector.invalidate()
        client.get("/api/delivery/snapshot")
        replay = client.get(
            "/api/delivery/events", params={"after": first["cursor"]}
        ).json()
        assert [e["event"] for e in replay["events"]] == ["gate_refusal"]
        assert_wire_clean(replay, tmp_path)
        drained = client.get(
            "/api/delivery/events", params={"after": replay["cursor"]}
        ).json()
        assert drained["events"] == []
