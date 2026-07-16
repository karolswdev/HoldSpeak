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

from __future__ import annotations

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


class TestRealDwEndToEnd:
    def test_snapshot_and_event_replay_from_a_real_rails_repo(self, tmp_path):
        repo = _make_rails_repo(tmp_path)
        registry = _registry(tmp_path)
        registry.register(str(repo), label="Demo rails")
        collector = DeliveryCollector(
            registry, dw_argv_factory=_real_dw_argv, max_age_seconds=3600.0
        )

        snap = collector.snapshot()
        assert snap["delivery_schema"] == 1
        assert snap["revision"].startswith("rev_")
        assert snap["cursor"].startswith("cur_")
        source = snap["sources"][0]
        assert source["status"] == "live"
        assert source["label"] == "Demo rails"
        assert source["capabilities"]["schemas"]["feed_schema"] == 1
        assert source["capabilities"]["disabled"] == []
        stories = source["projects"][0]["stories"]
        assert [s["story_id"] for s in stories] == ["DM-1-01"]
        assert_wire_clean(snap, tmp_path)

        # Rail motion: a real flip through the real CLI...
        first_cursor = snap["cursor"]
        flipped = _dw(repo, "story", "status", "demo", "1", "DM-1-01", "blocked")
        assert flipped.returncode == 0, flipped.stderr
        collector.invalidate()
        moved = collector.snapshot()
        assert moved["revision"] != snap["revision"]
        assert moved["sources"][0]["projects"][0]["stories"][0]["status"] == "blocked"

        # ...replays from the composed cursor without a fresh dw run.
        calls_before = collector.events_after(first_cursor)
        assert [e["event"] for e in calls_before["events"]] == ["story_status"]
        assert calls_before["events"][0]["source_id"] == source["source_id"]
        assert collector.events_after(moved["cursor"])["events"] == []
        assert_wire_clean(calls_before, tmp_path)


# ── §11 economics with the counting fake ─────────────────────────────


class TestSingleFlight:
    def test_concurrent_readers_cost_the_same_as_one(self, tmp_path):
        fake = FakeDw()
        fake.delay = 0.02
        collector = _fake_collector(
            tmp_path, fake, [("demo", _make_plain_repo(tmp_path, "r1"))]
        )
        collector.snapshot()  # initial collection
        baseline = len(fake.calls)
        assert baseline == 3  # capabilities + state + events

        collector.invalidate()
        barrier = threading.Barrier(10)

        def read():
            barrier.wait()
            return collector.snapshot()

        with ThreadPoolExecutor(max_workers=10) as pool:
            snaps = list(pool.map(lambda _: read(), range(10)))
        assert len(fake.calls) - baseline == 3  # ten readers, one flight
        assert all(s["revision"] == snaps[0]["revision"] for s in snaps)

    def test_cached_snapshot_read_never_shells_out(self, tmp_path):
        fake = FakeDw()
        collector = _fake_collector(
            tmp_path, fake, [("demo", _make_plain_repo(tmp_path, "r1"))]
        )
        collector.snapshot()
        count = len(fake.calls)
        for _ in range(25):
            collector.snapshot()
        assert len(fake.calls) == count  # zero subprocesses on the cache

    def test_events_replay_never_shells_out(self, tmp_path):
        fake = FakeDw()
        collector = _fake_collector(
            tmp_path, fake, [("demo", _make_plain_repo(tmp_path, "r1"))]
        )
        snap = collector.snapshot()
        count = len(fake.calls)
        for _ in range(10):
            collector.events_after(snap["cursor"])
            collector.events_after("")
        assert len(fake.calls) == count


class TestFailureRetention:
    def test_one_source_failing_keeps_last_known_good(self, tmp_path):
        fake = FakeDw()
        repo_a = _make_plain_repo(tmp_path, "alpha")
        repo_b = _make_plain_repo(tmp_path, "beta")
        collector = _fake_collector(
            tmp_path, fake, [("alpha", repo_a), ("beta", repo_b)]
        )
        healthy = collector.snapshot()
        assert [s["status"] for s in healthy["sources"]] == ["live", "live"]
        beta_row = healthy["sources"][1]
        assert beta_row["observed_at"]

        fake.broken.add(str(repo_b.resolve()))
        collector.invalidate()
        degraded = collector.snapshot()
        alpha, beta = degraded["sources"]
        assert alpha["status"] == "live"  # a failing peer erases nothing
        assert beta["status"] == "stale"
        assert beta["detail"] == "dw exited 3"  # classified, path-free
        assert beta["projects"] == beta_row["projects"]  # last-known-good
        assert beta["observed_at"] == beta_row["observed_at"]
        assert len(degraded["sources"]) == 2

    def test_never_observed_failure_is_unavailable(self, tmp_path):
        fake = FakeDw()
        repo = _make_plain_repo(tmp_path, "alpha")
        collector = _fake_collector(tmp_path, fake, [("alpha", repo)])
        fake.broken.add(str(repo.resolve()))
        snap = collector.snapshot()
        row = snap["sources"][0]
        assert row["status"] == "unavailable"
        assert row["projects"] is None  # None, never a fake empty array

    def test_missing_dw_cli_is_unavailable(self, tmp_path):
        fake = FakeDw()
        repo = _make_plain_repo(tmp_path, "alpha")
        registry = _registry(tmp_path)
        registry.register(str(repo), label="alpha")
        collector = DeliveryCollector(
            registry, runner=fake, dw_argv_factory=lambda root: None,
            max_age_seconds=3600.0,
        )
        row = collector.snapshot()["sources"][0]
        assert row["status"] == "unavailable"
        assert row["detail"] == "no dw CLI"
        assert fake.calls == []


class TestSchemaCompatibility:
    def test_unsupported_feed_schema_disables_only_projects(self, tmp_path):
        fake = FakeDw()
        repo_a = _make_plain_repo(tmp_path, "alpha")
        repo_b = _make_plain_repo(tmp_path, "beta")
        collector = _fake_collector(
            tmp_path, fake, [("alpha", repo_a), ("beta", repo_b)]
        )
        fake.docs[str(repo_b.resolve())]["capabilities"] = _caps_doc(feed_schema=99)
        fake.emit(repo_b.resolve(), {"ts": "t", "event": "story_status",
                                     "project": "demo", "story": "DM-1-01",
                                     "detail": {}, "tree": "t"})
        snap = collector.snapshot()
        alpha, beta = snap["sources"]
        assert alpha["status"] == "live"
        assert beta["status"] == "incompatible"
        assert beta["capabilities"]["disabled"] == ["projects"]
        assert beta["projects"] is None
        # The events capability still flows for the incompatible source.
        replay = collector.events_after("")
        assert [e["event"] for e in replay["events"]] == ["story_status"]

    def test_unsupported_events_schema_disables_only_events(self, tmp_path):
        fake = FakeDw()
        repo = _make_plain_repo(tmp_path, "alpha")
        collector = _fake_collector(tmp_path, fake, [("alpha", repo)])
        fake.docs[str(repo.resolve())]["capabilities"] = _caps_doc(events_schema=1)
        row = collector.snapshot()["sources"][0]
        assert row["status"] == "incompatible"
        assert row["capabilities"]["disabled"] == ["events"]
        assert row["projects"] is not None  # the feed still populated

    def test_unknown_capabilities_schema_never_crashes_the_snapshot(self, tmp_path):
        fake = FakeDw()
        repo_a = _make_plain_repo(tmp_path, "alpha")
        repo_b = _make_plain_repo(tmp_path, "beta")
        collector = _fake_collector(
            tmp_path, fake, [("alpha", repo_a), ("beta", repo_b)]
        )
        fake.docs[str(repo_b.resolve())]["capabilities"] = {"capabilities_schema": 9}
        snap = collector.snapshot()
        assert snap["sources"][0]["status"] == "live"
        assert snap["sources"][1]["status"] == "incompatible"


class TestRevisionAndCursor:
    def test_one_revision_covers_all_collections(self, tmp_path):
        fake = FakeDw()
        repo_a = _make_plain_repo(tmp_path, "alpha")
        repo_b = _make_plain_repo(tmp_path, "beta")
        collector = _fake_collector(
            tmp_path, fake, [("alpha", repo_a), ("beta", repo_b)]
        )
        snap = collector.snapshot()
        assert len({snap["revision"]}) == 1
        # The cursor composes BOTH per-source cursors from this pass.
        per_source = parse_cursor(snap["cursor"])
        assert set(per_source) == {s["source_id"] for s in snap["sources"]}

    def test_unchanged_payload_keeps_its_revision(self, tmp_path):
        fake = FakeDw()
        collector = _fake_collector(
            tmp_path, fake, [("alpha", _make_plain_repo(tmp_path, "r1"))]
        )
        first = collector.snapshot()
        collector.invalidate()
        second = collector.snapshot()
        assert second["revision"] == first["revision"]

    def test_data_motion_changes_the_revision_and_cursor(self, tmp_path):
        fake = FakeDw()
        repo = _make_plain_repo(tmp_path, "r1")
        collector = _fake_collector(tmp_path, fake, [("alpha", repo)])
        first = collector.snapshot()
        fake.emit(repo.resolve(), {"ts": "t", "event": "story_status",
                                   "project": "demo", "story": "DM-1-01",
                                   "detail": {"from": "a", "to": "b"}, "tree": "t"})
        collector.invalidate()
        second = collector.snapshot()
        assert second["revision"] != first["revision"]
        assert second["cursor"] != first["cursor"]
        replay = collector.events_after(first["cursor"])
        assert len(replay["events"]) == 1
        assert collector.events_after(second["cursor"])["events"] == []

    def test_cursor_roundtrip_and_garbage_tolerance(self):
        composed = compose_cursor({"src_a": "3", "src_b": "0"})
        assert parse_cursor(composed) == {"src_a": "3", "src_b": "0"}
        assert parse_cursor("") == {}
        assert parse_cursor("not-a-cursor") == {}
        assert parse_cursor("cur_!!!") == {}


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
    def test_snapshot_route_serves_the_read_model_with_etag(self, tmp_path):
        fake = FakeDw()
        client, _ = _route_client(
            tmp_path, fake, [("demo", _make_plain_repo(tmp_path, "r1"))]
        )
        response = client.get("/api/delivery/snapshot")
        assert response.status_code == 200
        body = response.json()
        assert body["delivery_schema"] == 1
        assert response.headers["etag"] == body["revision"]
        assert body["sources"][0]["status"] == "live"
        assert_wire_clean(body, tmp_path)

        not_modified = client.get(
            "/api/delivery/snapshot",
            headers={"If-None-Match": body["revision"]},
        )
        assert not_modified.status_code == 304

    def test_polling_the_snapshot_never_triggers_fresh_dw_runs(self, tmp_path):
        fake = FakeDw()
        client, _ = _route_client(
            tmp_path, fake, [("demo", _make_plain_repo(tmp_path, "r1"))]
        )
        client.get("/api/delivery/snapshot")
        count = len(fake.calls)
        for _ in range(10):
            assert client.get("/api/delivery/snapshot").status_code == 200
        assert len(fake.calls) == count

    def test_sources_route_is_the_registry_view(self, tmp_path):
        fake = FakeDw()
        client, _ = _route_client(
            tmp_path, fake, [("demo", _make_plain_repo(tmp_path, "r1"))]
        )
        client.get("/api/delivery/snapshot")
        body = client.get("/api/delivery/sources").json()
        assert body["registry_schema"] == 1
        row = body["sources"][0]
        assert row["label"] == "demo"
        assert row["status"] == "live"
        assert row["source_id"].startswith("src_")
        assert_wire_clean(body, tmp_path)

    def test_register_source_by_path_and_typed_refusal(self, tmp_path):
        fake = FakeDw()
        client, collector = _route_client(
            tmp_path, fake, [("demo", _make_plain_repo(tmp_path, "r1"))]
        )
        newcomer = _make_plain_repo(tmp_path, "r2")
        fake.add_repo(newcomer.resolve())
        created = client.post(
            "/api/delivery/sources",
            json={"path": str(newcomer), "label": "Newcomer"},
        )
        assert created.status_code == 200
        body = created.json()
        assert body["success"] is True
        assert body["source"]["label"] == "Newcomer"
        assert_wire_clean(body, tmp_path)
        # Registration invalidated the cache: the next snapshot sees both.
        snap = client.get("/api/delivery/snapshot").json()
        assert len(snap["sources"]) == 2

        loose = tmp_path / "loose"
        loose.mkdir()
        refused = client.post("/api/delivery/sources", json={"path": str(loose)})
        assert refused.status_code == 400
        assert str(tmp_path) not in refused.json()["error"]

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
