"""Evidence dossiers + safe asset browsing (HS-94-05).

Every class runs the REAL vendored dw at `.githooks/dw` as a
subprocess against real scratch rails repos built in tmp_path (the
counterpart-contract discipline) — standard layout, self-hosted
layout, and a linked git worktree. Covered: dossier completeness with
sanitized Markdown, pass/fail captured-run distinction, the
bundle-keyed manifest cache (bounded, revision-aware, honest offline),
phase-dossier laziness proven by subprocess count, every typed
refusal mapped to HTTP (404/409/413/503), range/ETag behavior on the
asset proxy, the no-path wire walk, and the grounding adapter's
capped blocks.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery import DeliveryRegistry
from holdspeak.delivery.dossiers import (
    DossierRefusal,
    DossierService,
    _default_runner,
    hydrate_dossier_refs,
    sanitize_markdown,
)
from holdspeak.grounding import GROUNDING_TRANSCRIPT_CAP
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_dossiers import build_delivery_dossiers_router

REPO_ROOT = Path(__file__).resolve().parents[2]
GITHOOKS = REPO_ROOT / ".githooks"
DW = GITHOOKS / "dw"

if str(GITHOOKS) not in sys.path:
    sys.path.insert(0, str(GITHOOKS))

from dw_pmo.manifest import MAX_ASSET_BYTES  # noqa: E402

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"not-really-a-png" * 4
JSON_BYTES = b'{"walk": "w1", "ok": true}\n'
LOG_BYTES = b"line one\nline two\n"
NOTES_BYTES = b"plain notes\n"

PHASE_TABLE = """# Phase 1 — Alpha

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| DM-1-01 | First thing | in-progress | [story-01-first.md](story-01-first.md) | [evidence-story-01.md](evidence-story-01.md) |
| DM-1-02 | Second thing | done | [story-02-second.md](story-02-second.md) | [evidence-story-02.md](evidence-story-02.md) |
"""

STORY_01 = (
    """# DM-1-01 - First thing

- **Status:** in-progress

The story body.

<script>alert("owned")</script>
<img src=x onerror="alert(1)">
<!-- secret html comment -->

```text
<b>kept-in-fence</b>
```

Closing prose.
"""
)

STORY_02 = (
    "# DM-1-02 - Second thing\n\n- **Status:** done\n\nLong body.\n\n"
    + ("pad " * 4000)
    + "\n"
)

EVIDENCE_01 = """# Evidence — DM-1-01

- **Story:** DM-1-01

Narrative proof, one passing and one failing captured run.

### Captured run — 2026-07-11T10:00:00Z

- **Command:** `pytest -q tests/unit`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** deadbeef

```text
ok
```

### Captured run — 2026-07-11T11:00:00Z

- **Command:** `pytest -q tests/broken`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** deadbeef

```text
boom
```
"""

EVIDENCE_02 = """# Evidence — DM-1-02

- **Story:** DM-1-02

Done proof.
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


def _make_repo(tmp_path: Path, self_hosted: bool = False) -> Path:
    repo = tmp_path / ("rails-selfhosted" if self_hosted else "rails")
    roadmap = (
        repo / "pmo-roadmap" / "pm" / "roadmap"
        if self_hosted
        else repo / "pm" / "roadmap"
    )
    phase = roadmap / "demo" / "phase-1-alpha"
    (phase / "assets").mkdir(parents=True)
    (roadmap / "demo" / "README.md").write_text(README, encoding="utf-8")
    (phase / "current-phase-status.md").write_text(PHASE_TABLE, encoding="utf-8")
    (phase / "story-01-first.md").write_text(STORY_01, encoding="utf-8")
    (phase / "story-02-second.md").write_text(STORY_02, encoding="utf-8")
    (phase / "evidence-story-01.md").write_text(EVIDENCE_01, encoding="utf-8")
    (phase / "evidence-story-02.md").write_text(EVIDENCE_02, encoding="utf-8")
    (phase / "assets" / "proof.png").write_bytes(PNG_BYTES)
    (phase / "assets" / "walk.json").write_bytes(JSON_BYTES)
    (phase / "assets" / "run.log").write_bytes(LOG_BYTES)
    (phase / "assets" / "notes.txt").write_bytes(NOTES_BYTES)
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed rails fixture")
    return repo


def _phase_dir(repo: Path, self_hosted: bool = False) -> Path:
    roadmap = (
        repo / "pmo-roadmap" / "pm" / "roadmap"
        if self_hosted
        else repo / "pm" / "roadmap"
    )
    return roadmap / "demo" / "phase-1-alpha"


def _real_dw_argv(root: Path) -> list[str]:
    return [sys.executable, str(DW), "--root", str(root)]


class FlakyRunner:
    """Delegates to the real runner until flipped down (node offline)."""

    def __init__(self) -> None:
        self.down = False

    def __call__(self, argv, cwd=None, *, binary=False):
        if self.down:
            raise OSError("node offline")
        return _default_runner(argv, cwd, binary=binary)


def _service(
    tmp_path: Path,
    repo: Path,
    *,
    label: str = "Demo rails",
    runner=None,
    max_age_seconds: float = 3600.0,
    max_entries: int = 64,
) -> tuple[DossierService, str]:
    registry = DeliveryRegistry(
        tmp_path / "registry.json", map_path=tmp_path / "absent-map.json"
    )
    source, _wt = registry.register(str(repo), label=label)
    service = DossierService(
        registry,
        runner=runner,
        dw_argv_factory=_real_dw_argv,
        max_age_seconds=max_age_seconds,
        max_entries=max_entries,
    )
    return service, source.source_id


def _client(service: DossierService) -> TestClient:
    app = FastAPI()
    app.include_router(
        build_delivery_dossiers_router(
            WebContext(get_state=lambda: {}), service=service
        )
    )
    return TestClient(app)


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


def assert_no_paths(payload, tmp_path: Path) -> None:
    """The §12/§13 walk: no absolute path, no repo-relative member
    path, and no `path` key anywhere on the wire."""
    if isinstance(payload, dict):
        assert "path" not in payload
        for value in payload.values():
            assert_no_paths(value, tmp_path)
    elif isinstance(payload, list):
        for item in payload:
            assert_no_paths(item, tmp_path)
    elif isinstance(payload, str):
        assert str(tmp_path) not in payload, payload
        assert "pm/roadmap/" not in payload, payload


def _asset_calls(service: DossierService) -> int:
    return sum(1 for verb, _src in service.dw_calls if verb == "asset")


def _manifest_calls(service: DossierService) -> int:
    return sum(1 for verb, _src in service.dw_calls if verb == "manifest")


# ── the story dossier ────────────────────────────────────────────────


class TestStoryDossier:
    def test_dossier_completeness(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        dossier = service.story_dossier(source_id, "demo", "DM-1-01")

        assert dossier["dossier_schema"] == 1
        assert dossier["bundle_id"].startswith("bundle-")
        assert dossier["bundle_changed"] is False
        assert dossier["freshness"] == "live"
        assert dossier["project"] == "demo"
        assert dossier["story_id"] == "DM-1-01"
        assert dossier["phase"] == 1
        assert dossier["status"] == "in-progress"
        assert dossier["source_revision"]["head_sha"]
        assert dossier["source_revision"]["index_tree"]
        assert dossier["summary"]["assets"] == 4

        roles = {m["role"] for m in dossier["members"]}
        assert {"story_markdown", "evidence_markdown", "phase_status", "asset"} <= roles
        for member in dossier["members"]:
            assert member["sha256"].startswith("sha256:")
            assert member["bytes"] > 0
            assert member["media_type"]
        by_label = {m["label"]: m for m in dossier["members"]}
        assert by_label["proof.png"]["media_type"] == "image/png"
        assert by_label["walk.json"]["media_type"] == "application/json"
        assert by_label["run.log"]["media_type"] == "text/plain"

        trace = dossier["trace"]
        member_ids = {m["asset_id"] for m in dossier["members"]}
        assert trace["story_asset_id"] in member_ids
        assert trace["evidence_asset_id"] in member_ids
        assert trace["phase_status_asset_id"] in member_ids

        assert dossier["story"]["state"] == "ready"
        assert dossier["evidence"][0]["state"] == "ready"
        assert "Narrative proof" in dossier["evidence"][0]["markdown"]
        assert_no_paths(dossier, tmp_path)

    def test_story_markdown_is_sanitized_but_fences_survive(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        markdown = service.story_dossier(source_id, "demo", "DM-1-01")["story"][
            "markdown"
        ]
        assert "The story body." in markdown
        assert "Closing prose." in markdown
        assert "<b>kept-in-fence</b>" in markdown  # fenced output is data
        assert "<script" not in markdown
        assert "alert(" not in markdown
        assert "onerror" not in markdown
        assert "secret html comment" not in markdown

    def test_captured_runs_pass_fail_distinct(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        runs = service.story_dossier(source_id, "demo", "DM-1-01")["captured_runs"]
        assert [(r["command"], r["exit_code"], r["passed"]) for r in runs] == [
            ("pytest -q tests/unit", 0, True),
            ("pytest -q tests/broken", 1, False),
        ]
        assert runs[0]["timestamp"] == "2026-07-11T10:00:00Z"
        summary = service.story_dossier(source_id, "demo", "DM-1-01")["summary"]
        assert summary["passing_captures"] == 1
        assert summary["failing_captures"] == 1

    def test_self_hosted_layout_resolves(self, tmp_path):
        repo = _make_repo(tmp_path, self_hosted=True)
        service, source_id = _service(tmp_path, repo, label="Self hosted")
        dossier = service.story_dossier(source_id, "demo", "DM-1-01")
        assert dossier["story_id"] == "DM-1-01"
        assert dossier["story"]["state"] == "ready"
        assert_no_paths(dossier, tmp_path)  # pmo-roadmap/... never leaks

    def test_linked_worktree_resolves(self, tmp_path):
        repo = _make_repo(tmp_path)
        wt = tmp_path / "wt"
        _git(repo, "worktree", "add", "-b", "hs94-side", str(wt))
        assert (wt / ".git").is_file()  # the linked-worktree precondition
        service, source_id = _service(tmp_path, wt, label="Worktree")
        dossier = service.story_dossier(source_id, "demo", "DM-1-01")
        assert dossier["story_id"] == "DM-1-01"
        assert dossier["members"]
        assert_no_paths(dossier, tmp_path)

    def test_unknown_story_and_project_are_typed_404(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        missing = client.get(
            "/api/delivery/stories/demo/DM-9-99/dossier",
            params={"source": source_id},
        )
        assert missing.status_code == 404
        assert missing.json()["refusal"] == "not_found"
        wrong_project = client.get(
            "/api/delivery/stories/ghost/DM-1-01/dossier",
            params={"source": source_id},
        )
        assert wrong_project.status_code == 404

    def test_route_scans_sources_without_a_source_param(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, _source_id = _service(tmp_path, repo)
        client = _client(service)
        response = client.get("/api/delivery/stories/demo/DM-1-01/dossier")
        assert response.status_code == 200
        body = response.json()
        assert body["story_id"] == "DM-1-01"
        assert_no_paths(body, tmp_path)


# ── the manifest cache ───────────────────────────────────────────────


class TestManifestCache:
    def test_cached_window_never_shells_out_again(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo, max_age_seconds=3600.0)
        first = service.story_dossier(source_id, "demo", "DM-1-01")
        manifest_count = _manifest_calls(service)
        asset_count = _asset_calls(service)
        assert manifest_count == 1
        assert asset_count == 2  # story doc + evidence doc, hydrated once
        second = service.story_dossier(source_id, "demo", "DM-1-01")
        assert second["bundle_id"] == first["bundle_id"]
        assert _manifest_calls(service) == manifest_count  # cache hit
        assert _asset_calls(service) == asset_count  # docs cached too

    def test_index_tree_change_is_a_new_bundle_with_honest_marker(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo, max_age_seconds=0.0)
        old = service.story_dossier(source_id, "demo", "DM-1-01")
        old_bundle = old["bundle_id"]

        phase = _phase_dir(repo)
        (phase / "evidence-story-01.md").write_text(
            EVIDENCE_01 + "\nMore proof.\n", encoding="utf-8"
        )
        _git(repo, "add", "-A")  # index tree moved => new bundle

        fresh = service.story_dossier(source_id, "demo", "DM-1-01")
        assert fresh["bundle_id"] != old_bundle
        stale_view = service.manifest_for_bundle(old_bundle)
        assert stale_view.bundle_changed is True
        assert stale_view.live_bundle_id == fresh["bundle_id"]
        # The superseded manifest metadata stays visible (§13).
        assert stale_view.entry.manifest["members"]

    def test_cache_is_bounded(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo, max_entries=1)
        first = service.story_dossier(source_id, "demo", "DM-1-01")
        service.story_dossier(source_id, "demo", "DM-1-02")
        assert len(service._entries) == 1  # LRU-evicted down to the bound
        try:
            service.manifest_for_bundle(first["bundle_id"])
            raise AssertionError("evicted bundle should refuse")
        except DossierRefusal as refusal:
            assert refusal.code == "not_found"

    def test_offline_source_keeps_manifest_visible_as_unavailable(self, tmp_path):
        repo = _make_repo(tmp_path)
        runner = FlakyRunner()
        service, source_id = _service(
            tmp_path, repo, runner=runner, max_age_seconds=0.0
        )
        warm = service.story_dossier(source_id, "demo", "DM-1-01")
        assert warm["freshness"] == "live"

        runner.down = True
        offline = service.story_dossier(source_id, "demo", "DM-1-01")
        assert offline["freshness"] == "unavailable"
        assert offline["detail"]  # classified, never empty
        assert offline["members"] == warm["members"]  # metadata retained
        assert offline["story"]["state"] == "ready"  # hydrated docs retained
        assert_no_paths(offline, tmp_path)

    def test_never_seen_offline_source_is_503(self, tmp_path):
        repo = _make_repo(tmp_path)
        runner = FlakyRunner()
        runner.down = True
        service, source_id = _service(tmp_path, repo, runner=runner)
        client = _client(service)
        response = client.get(
            "/api/delivery/stories/demo/DM-1-01/dossier",
            params={"source": source_id},
        )
        assert response.status_code == 503
        assert response.json()["refusal"] == "unavailable"


# ── the asset proxy ──────────────────────────────────────────────────


def _dossier_and_member(client, label: str, source_id: str):
    dossier = client.get(
        "/api/delivery/stories/demo/DM-1-01/dossier",
        params={"source": source_id},
    ).json()
    member = next(m for m in dossier["members"] if m["label"] == label)
    return dossier, member


class TestAssetProxy:
    def test_streams_manifest_typed_bytes_with_etag(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier, png = _dossier_and_member(client, "proof.png", source_id)
        url = f"/api/delivery/evidence/{dossier['bundle_id']}/{png['asset_id']}"

        response = client.get(url)
        assert response.status_code == 200
        assert response.content == PNG_BYTES
        assert response.headers["content-type"].startswith("image/png")
        assert response.headers["etag"] == png["sha256"]
        assert response.headers["accept-ranges"] == "bytes"

        cached = client.get(url, headers={"If-None-Match": png["sha256"]})
        assert cached.status_code == 304

        _, walk = _dossier_and_member(client, "walk.json", source_id)
        json_response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{walk['asset_id']}"
        )
        assert json_response.content == JSON_BYTES
        assert json_response.headers["content-type"].startswith("application/json")
        _, log = _dossier_and_member(client, "run.log", source_id)
        log_response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{log['asset_id']}"
        )
        assert log_response.content == LOG_BYTES
        assert log_response.headers["content-type"].startswith("text/plain")

    def test_range_requests(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier, notes = _dossier_and_member(client, "notes.txt", source_id)
        url = f"/api/delivery/evidence/{dossier['bundle_id']}/{notes['asset_id']}"
        size = len(NOTES_BYTES)

        partial = client.get(url, headers={"Range": "bytes=0-4"})
        assert partial.status_code == 206
        assert partial.content == b"plain"
        assert partial.headers["content-range"] == f"bytes 0-4/{size}"

        open_ended = client.get(url, headers={"Range": "bytes=6-"})
        assert open_ended.status_code == 206
        assert open_ended.content == NOTES_BYTES[6:]

        suffix = client.get(url, headers={"Range": "bytes=-6"})
        assert suffix.status_code == 206
        assert suffix.content == NOTES_BYTES[-6:]

        beyond = client.get(url, headers={"Range": f"bytes={size + 50}-"})
        assert beyond.status_code == 416
        assert beyond.headers["content-range"] == f"bytes */{size}"

        malformed = client.get(url, headers={"Range": "bytes=0-4,6-9"})
        assert malformed.status_code == 200  # documented multi-range fallback
        assert malformed.content == NOTES_BYTES

    def test_not_in_manifest_and_unknown_bundle_are_404(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier, _ = _dossier_and_member(client, "proof.png", source_id)

        bogus_asset = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/a-doesnotexist"
        )
        assert bogus_asset.status_code == 404
        assert bogus_asset.json()["refusal"] == "not_in_manifest"

        bogus_bundle = client.get(
            "/api/delivery/evidence/bundle-doesnotexist/a-whatever"
        )
        assert bogus_bundle.status_code == 404
        assert bogus_bundle.json()["refusal"] == "not_found"
        for body in (bogus_asset.json(), bogus_bundle.json()):
            assert_no_paths(body, tmp_path)

    def test_symlink_swap_refuses_and_leaks_nothing(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier = client.get(
            "/api/delivery/stories/demo/DM-1-01/dossier",
            params={"source": source_id},
        ).json()
        evidence_id = dossier["trace"]["evidence_asset_id"]

        secret = tmp_path / "outside-secret.txt"
        secret.write_text("SECRET-BYTES", encoding="utf-8")
        target = _phase_dir(repo) / "evidence-story-01.md"
        target.unlink()
        target.symlink_to(secret)  # worktree swap: index tree unchanged

        response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{evidence_id}"
        )
        assert response.status_code == 404
        # An escaping link trips the root check first; either way, typed 404.
        assert response.json()["refusal"] == "outside_root"
        assert b"SECRET-BYTES" not in response.content

    def test_in_repo_symlink_refuses_as_symlink(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier = client.get(
            "/api/delivery/stories/demo/DM-1-01/dossier",
            params={"source": source_id},
        ).json()
        evidence_id = dossier["trace"]["evidence_asset_id"]
        target = _phase_dir(repo) / "evidence-story-01.md"
        target.unlink()
        target.symlink_to(_phase_dir(repo) / "story-02-second.md")

        response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{evidence_id}"
        )
        assert response.status_code == 404
        assert response.json()["refusal"] == "symlink"
        assert b"pad pad" not in response.content  # link target never streams

    def test_removed_member_is_404(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier, notes = _dossier_and_member(client, "notes.txt", source_id)
        (_phase_dir(repo) / "assets" / "notes.txt").unlink()
        response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{notes['asset_id']}"
        )
        assert response.status_code == 404
        assert response.json()["refusal"] == "not_in_manifest"

    def test_oversize_asset_listed_but_413(self, tmp_path):
        repo = _make_repo(tmp_path)
        big = _phase_dir(repo) / "assets" / "big.bin"
        big.write_bytes(b"\0" * (MAX_ASSET_BYTES + 1))
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier, member = _dossier_and_member(client, "big.bin", source_id)
        assert member["bytes"] == MAX_ASSET_BYTES + 1  # listed honestly
        response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{member['asset_id']}"
        )
        assert response.status_code == 413
        assert response.json()["refusal"] == "oversize"

    def test_stale_bundle_is_409_hub_detected(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo, max_age_seconds=0.0)
        client = _client(service)
        dossier, png = _dossier_and_member(client, "proof.png", source_id)
        (_phase_dir(repo) / "story-01-first.md").write_text(
            STORY_01 + "\nMoved on.\n", encoding="utf-8"
        )
        _git(repo, "add", "-A")
        response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{png['asset_id']}"
        )
        assert response.status_code == 409
        body = response.json()
        assert body["refusal"] == "bundle_changed"
        assert body["manifest"]["members"]  # metadata preserved (§13)
        assert_no_paths(body, tmp_path)

    def test_stale_bundle_is_409_dw_detected(self, tmp_path):
        # With a warm cache the hub does not know the tree moved; the
        # counterpart's own bundle check refuses and the hub maps it.
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo, max_age_seconds=3600.0)
        view = service.manifest_for_story(source_id, "demo", "DM-1-01")
        png_id = next(
            m["asset_id"]
            for m in view.entry.manifest["members"]
            if m["label"] == "proof.png"
        )
        (_phase_dir(repo) / "story-01-first.md").write_text(
            STORY_01 + "\nMoved on again.\n", encoding="utf-8"
        )
        _git(repo, "add", "-A")
        try:
            service.open_asset(view.entry.bundle_id, png_id)
            raise AssertionError("stale bundle should refuse")
        except DossierRefusal as refusal:
            assert refusal.code == "bundle_changed"
            assert refusal.http_status == 409

    def test_content_change_without_tree_motion_is_hash_mismatch_409(
        self, tmp_path
    ):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        dossier, notes = _dossier_and_member(client, "notes.txt", source_id)
        # Unstaged edit: same index tree => same bundle, different bytes.
        (_phase_dir(repo) / "assets" / "notes.txt").write_bytes(
            b"tampered mid-read\n"
        )
        response = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{notes['asset_id']}"
        )
        assert response.status_code == 409
        assert response.json()["refusal"] == "hash_mismatch"
        assert b"tampered" not in response.content

    def test_offline_node_asset_is_503_while_manifest_stays(self, tmp_path):
        repo = _make_repo(tmp_path)
        runner = FlakyRunner()
        service, source_id = _service(
            tmp_path, repo, runner=runner, max_age_seconds=0.0
        )
        client = _client(service)
        dossier, png = _dossier_and_member(client, "proof.png", source_id)

        runner.down = True
        asset = client.get(
            f"/api/delivery/evidence/{dossier['bundle_id']}/{png['asset_id']}"
        )
        assert asset.status_code == 503
        assert asset.json()["refusal"] == "unavailable"
        # The dossier read still answers, marked unavailable.
        still = client.get(
            "/api/delivery/stories/demo/DM-1-01/dossier",
            params={"source": source_id},
        )
        assert still.status_code == 200
        assert still.json()["freshness"] == "unavailable"
        assert still.json()["members"]


# ── the phase dossier ────────────────────────────────────────────────


class TestPhaseDossier:
    def test_groups_story_dossiers_and_final_summary(self, tmp_path):
        repo = _make_repo(tmp_path)
        (_phase_dir(repo) / "final-summary.md").write_text(
            "# Final summary\n\nShipped.\n", encoding="utf-8"
        )
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        response = client.get(
            "/api/delivery/phases/demo/1/dossier", params={"source": source_id}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["phase_dossier_schema"] == 1
        assert body["phase"] == 1
        assert body["status"] == "closed"
        assert [s["story_id"] for s in body["stories"]] == ["DM-1-01", "DM-1-02"]
        for story in body["stories"]:
            assert story["state"] == "ready"
            assert story["members"]
            assert "story" not in story  # metadata only, no doc bodies
            assert "evidence" not in story
        first, second = body["stories"]
        assert first["status"] == "in-progress"
        assert second["status"] == "done"
        assert [r["passed"] for r in first["captured_runs"]] == [True, False]
        summary = body["final_summary"]
        assert summary is not None
        assert summary["media_type"] == "text/markdown"
        assert summary["bundle_id"] == first["bundle_id"]
        assert_no_paths(body, tmp_path)

    def test_phase_route_reads_no_assets(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        response = client.get(
            "/api/delivery/phases/demo/1/dossier", params={"source": source_id}
        )
        assert response.status_code == 200
        verbs = [verb for verb, _src in service.dw_calls]
        assert verbs.count("state") == 1
        assert verbs.count("manifest") == 2  # one per story
        assert verbs.count("asset") == 0  # laziness: zero byte reads

    def test_unknown_phase_is_404(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        client = _client(service)
        response = client.get(
            "/api/delivery/phases/demo/9/dossier", params={"source": source_id}
        )
        assert response.status_code == 404
        assert response.json()["refusal"] == "not_found"


# ── the grounding adapter ────────────────────────────────────────────


class TestGroundingAdapter:
    def test_dossier_members_hydrate_capped_rails_blocks(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        blocks, unknown = hydrate_dossier_refs(
            [
                {"source": source_id, "project": "demo",
                 "kind": "story", "id": "DM-1-02"},
                {"source": source_id, "project": "demo",
                 "kind": "evidence", "id": "DM-1-01"},
            ],
            service,
        )
        assert unknown == []
        story_block, evidence_block = blocks

        # The same shape the rails picker produces (grounding_rails).
        assert story_block.kind == "rails:story"
        assert story_block.ref == "DM-1-02"
        assert story_block.subtitle == "Demo rails/demo"
        assert len(story_block.text) <= GROUNDING_TRANSCRIPT_CAP + 100
        assert story_block.text.endswith(
            f"[rail object cut at {GROUNDING_TRANSCRIPT_CAP} chars]"
        )

        assert evidence_block.kind == "rails:evidence"
        assert "Narrative proof" in evidence_block.text
        assert str(tmp_path) not in story_block.text + evidence_block.text

    def test_unknown_refs_come_back_as_tokens(self, tmp_path):
        repo = _make_repo(tmp_path)
        service, source_id = _service(tmp_path, repo)
        blocks, unknown = hydrate_dossier_refs(
            [
                {"source": source_id, "project": "demo",
                 "kind": "phase", "id": "1"},  # not a dossier member kind
                {"source": source_id, "project": "demo",
                 "kind": "story", "id": "DM-9-99"},
                {"source": "src_ghost", "project": "demo",
                 "kind": "story", "id": "DM-1-01"},
                "garbage",
            ],
            service,
        )
        assert blocks == []
        assert unknown == ["phase:1", "story:DM-9-99", "story:DM-1-01", "garbage"]


# ── sanitizer unit coverage ──────────────────────────────────────────


class TestSanitizeMarkdown:
    def test_strips_html_outside_fences_only(self):
        text = (
            "# Title\n\n<div class=x>boxed</div>\n\n```html\n<div>raw</div>\n```\n"
            "\n<!-- note -->tail\n"
        )
        cleaned = sanitize_markdown(text)
        assert "<div class=x>" not in cleaned
        assert "boxed" in cleaned
        assert "<div>raw</div>" in cleaned  # fenced = preserved
        assert "note" not in cleaned.replace("tail", "")
        assert "tail" in cleaned

    def test_autolinks_survive(self):
        assert (
            sanitize_markdown("see <https://example.test/a> now")
            == "see <https://example.test/a> now"
        )
