"""The Delivery Workbench counterpart contract (HS-94-01).

These tests exercise the vendored rails at `.githooks/dw` — the
operative counterpart this repo ships — against real scratch git
repos built in tmp_path (the CI-vs-local dw trap: never the repo's
own roadmap, never a dw on PATH). Covered: linked-worktree event
emission (`.git` as a FILE), cursor-addressable event reads,
`dw capabilities --json`, the evidence manifest for standard and
self-hosted roadmap layouts, and manifest-bound asset streaming
with typed refusals. Python only, bounded, no network.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GITHOOKS = REPO_ROOT / ".githooks"
DW = GITHOOKS / "dw"

if str(GITHOOKS) not in sys.path:
    sys.path.insert(0, str(GITHOOKS))

from dw_pmo import events as dw_events  # noqa: E402
from dw_pmo import manifest as dw_manifest  # noqa: E402

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"not-really-a-png" * 4

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

Narrative proof, plus one passing and one failing captured run.

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

README = """# Demo

- **Story ID prefix:** DM

**Current phase:** [Phase 1](phase-1-alpha/current-phase-status.md)
"""


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _make_repo(tmp_path: Path, self_hosted: bool = False) -> Path:
    """A real scratch rails repo: git-initialized, one project, one
    phase, one in-progress story with evidence and assets."""
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
    (phase / "story-01-first.md").write_text(STORY, encoding="utf-8")
    (phase / "evidence-story-01.md").write_text(EVIDENCE, encoding="utf-8")
    (phase / "assets" / "proof.png").write_bytes(PNG_BYTES)
    (phase / "assets" / "notes.txt").write_text("plain notes\n", encoding="utf-8")
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


def _make_worktree(repo: Path, tmp_path: Path) -> Path:
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-b", "hs94-side", str(wt))
    return wt


def _dw(root: Path, *args: str, binary: bool = False):
    return subprocess.run(
        [sys.executable, str(DW), "--root", str(root), *args],
        capture_output=True,
        text=not binary,
    )


# ── D1: worktree truth — events survive `.git` being a FILE ──────────


class TestWorktreeTruth:
    def test_linked_worktree_git_file_still_journals(self, tmp_path):
        repo = _make_repo(tmp_path)
        wt = _make_worktree(repo, tmp_path)
        assert (wt / ".git").is_file()  # the regression's precondition
        dw_events.emit(
            wt, "story_status", project="demo", story="DM-1-01",
            detail={"from": "ready", "to": "in-progress"}, tree="t1",
        )
        journal = repo / ".git" / "pmo-events.jsonl"
        assert journal.is_file(), "event silently no-oped in the linked worktree"
        assert len(dw_events.read_events(wt)) == 1

    def test_all_worktrees_share_one_event_stream(self, tmp_path):
        repo = _make_repo(tmp_path)
        wt = _make_worktree(repo, tmp_path)
        dw_events.emit(repo, "phase_created", project="demo",
                       detail={"phase": 1}, tree="t1")
        dw_events.emit(wt, "phase_closed", project="demo",
                       detail={"phase": 1}, tree="t2")
        primary_view = dw_events.read_events(repo)
        worktree_view = dw_events.read_events(wt)
        assert primary_view == worktree_view
        assert [e["event"] for e in primary_view] == ["phase_created", "phase_closed"]
        # One resolved journal for both roots — the common git dir.
        assert (
            dw_events.events_path(repo).resolve()
            == dw_events.events_path(wt).resolve()
            == (repo / ".git" / "pmo-events.jsonl").resolve()
        )

    def test_non_repo_root_neither_writes_nor_raises(self, tmp_path):
        loose = tmp_path / "loose"
        loose.mkdir()
        dw_events.emit(loose, "phase_created", project="x",
                       detail={"phase": 1}, tree="t")
        assert not (loose / ".git").exists()
        assert dw_events.read_events(loose) == []
        assert dw_events.events_path(loose) is None

    def test_cli_flip_and_capture_in_worktree_emit_cursor_events(self, tmp_path):
        repo = _make_repo(tmp_path)
        wt = _make_worktree(repo, tmp_path)
        flipped = _dw(wt, "story", "status", "demo", "1", "DM-1-01", "blocked")
        assert flipped.returncode == 0, flipped.stderr
        captured = _dw(wt, "evidence", "capture", "demo", "1", "DM-1-01",
                       "--", "echo", "hello")
        assert captured.returncode == 0, captured.stderr
        # Cursor-addressable from the PRIMARY checkout: one stream.
        out = _dw(repo, "events", "--json", "--after", "0")
        assert out.returncode == 0, out.stderr
        envelope = json.loads(out.stdout)
        assert envelope["events_schema"] == 2
        kinds = [e["event"] for e in envelope["events"]]
        assert "story_status" in kinds and "evidence_capture" in kinds
        assert envelope["source_cursor"] == str(len(envelope["events"]))
        assert all(e["event_id"] for e in envelope["events"])


# ── D4: cursor semantics — no duplicates, no gaps ────────────────────


class TestCursorSemantics:
    def _emit_n(self, repo: Path, n: int, start: int = 0) -> None:
        for i in range(start, start + n):
            dw_events.emit(repo, "phase_created", project="demo",
                           detail={"phase": i}, tree=f"t{i}")

    def test_after_returns_only_newer_no_dup_no_gap(self, tmp_path):
        repo = _make_repo(tmp_path)
        self._emit_n(repo, 3)
        first = dw_events.read_events_after(repo)
        assert [e["event_id"] for e in first["events"]] == ["1", "2", "3"]
        assert first["source_cursor"] == "3"
        self._emit_n(repo, 2, start=3)
        second = dw_events.read_events_after(repo, int(first["source_cursor"]))
        assert [e["event_id"] for e in second["events"]] == ["4", "5"]
        assert second["source_cursor"] == "5"
        replay = dw_events.read_events_after(repo)
        assert [e["event_id"] for e in replay["events"]] == ["1", "2", "3", "4", "5"]

    def test_malformed_lines_never_shift_the_cursor(self, tmp_path):
        repo = _make_repo(tmp_path)
        self._emit_n(repo, 2)
        journal = dw_events.events_path(repo)
        with journal.open("a", encoding="utf-8") as handle:
            handle.write("this is not json\n")
        self._emit_n(repo, 1, start=2)
        envelope = dw_events.read_events_after(repo, 2)
        assert [e["event_id"] for e in envelope["events"]] == ["4"]
        assert envelope["source_cursor"] == "4"

    def test_legacy_json_form_is_unchanged(self, tmp_path):
        repo = _make_repo(tmp_path)
        self._emit_n(repo, 2)
        out = _dw(repo, "events", "--json")
        assert out.returncode == 0, out.stderr
        doc = json.loads(out.stdout)
        assert isinstance(doc, list) and len(doc) == 2
        assert all("event_id" not in e for e in doc)  # v1 shape untouched

    def test_non_numeric_cursor_is_a_typed_error(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = _dw(repo, "events", "--json", "--after", "opaque-nonsense")
        assert out.returncode != 0
        assert "cursor" in out.stderr


# ── D3: capabilities — the compatibility handshake ───────────────────


class TestCapabilities:
    def test_capabilities_shape(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = _dw(repo, "capabilities", "--json")
        assert out.returncode == 0, out.stderr
        doc = json.loads(out.stdout)
        assert doc["capabilities_schema"] == 1
        assert doc["schemas"] == {
            "feed_schema": 1,
            "events_schema": 2,
            "sessions_schema": 1,
            "evidence_schema": 1,
        }
        for status in ("backlog", "ready", "in-progress", "blocked", "done"):
            assert status in doc["statuses"]
        assert "done" in doc["done_statuses"]
        assert "story.status" in doc["verbs"] and "story.create" in doc["verbs"]
        assert "evidence.manifest" in doc["commands"]
        assert doc["roadmap_dir"] == "pm/roadmap"
        assert doc["features"]["events_cursor"] is True

    def test_capabilities_names_the_self_hosted_roadmap_root(self, tmp_path):
        repo = _make_repo(tmp_path, self_hosted=True)
        doc = json.loads(_dw(repo, "capabilities", "--json").stdout)
        assert doc["roadmap_dir"] == "pmo-roadmap/pm/roadmap"


# ── D5: evidence manifest ────────────────────────────────────────────


class TestEvidenceManifest:
    def _manifest(self, repo: Path) -> dict:
        out = _dw(repo, "evidence", "manifest", "demo", "DM-1-01", "--json")
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout)

    def test_manifest_lists_the_dossier(self, tmp_path):
        repo = _make_repo(tmp_path)
        doc = self._manifest(repo)
        assert doc["evidence_schema"] == 1
        assert doc["bundle_id"].startswith("bundle-")
        assert doc["project"] == "demo"
        assert doc["phase"] == 1
        assert doc["story_id"] == "DM-1-01"
        assert doc["status"] == "in-progress"
        roles = {m["role"] for m in doc["members"]}
        assert {"story_markdown", "evidence_markdown", "phase_status", "asset"} <= roles
        member_ids = {m["asset_id"] for m in doc["members"]}
        assert doc["trace"]["story_asset_id"] in member_ids
        assert doc["trace"]["evidence_asset_id"] in member_ids
        assert doc["trace"]["phase_status_asset_id"] in member_ids
        assert doc["trace"]["final_summary_asset_id"] is None
        for member in doc["members"]:
            assert member["sha256"].startswith("sha256:")
            assert member["bytes"] > 0
        by_name = {Path(m["path"]).name: m for m in doc["members"]}
        assert by_name["proof.png"]["media_type"] == "image/png"
        assert by_name["notes.txt"]["media_type"] == "text/plain"
        assert by_name["evidence-story-01.md"]["media_type"] == "text/markdown"
        assert doc["summary"] == {
            "passing_captures": 1, "failing_captures": 1, "assets": 2,
        }
        assert doc["source_revision"]["head_sha"]

    def test_captured_runs_are_parsed(self, tmp_path):
        repo = _make_repo(tmp_path)
        runs = self._manifest(repo)["captured_runs"]
        assert [(r["command"], r["exit_code"]) for r in runs] == [
            ("pytest -q tests/unit", 0),
            ("pytest -q tests/broken", 1),
        ]
        assert runs[0]["timestamp"] == "2026-07-11T10:00:00Z"

    def test_manifest_resolves_the_self_hosted_layout(self, tmp_path):
        repo = _make_repo(tmp_path, self_hosted=True)
        doc = self._manifest(repo)
        assert doc["story_id"] == "DM-1-01"
        assert doc["members"]
        for member in doc["members"]:
            assert member["path"].startswith("pmo-roadmap/pm/roadmap/")

    def test_final_summary_joins_a_closed_phase_dossier(self, tmp_path):
        repo = _make_repo(tmp_path)
        (_phase_dir(repo) / "final-summary.md").write_text(
            "# Final summary\n\nShipped.\n", encoding="utf-8"
        )
        doc = self._manifest(repo)
        roles = {m["role"] for m in doc["members"]}
        assert "final_summary" in roles
        assert doc["trace"]["final_summary_asset_id"] is not None


# ── D5: manifest-bound asset streaming with typed refusals ───────────


class TestEvidenceAsset:
    def _manifest(self, repo: Path) -> dict:
        out = _dw(repo, "evidence", "manifest", "demo", "DM-1-01", "--json")
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout)

    def test_asset_streams_exact_bytes_by_id_and_by_path(self, tmp_path):
        repo = _make_repo(tmp_path)
        doc = self._manifest(repo)
        png = next(m for m in doc["members"] if m["path"].endswith("proof.png"))
        by_id = _dw(repo, "evidence", "asset", "DM-1-01", png["asset_id"], binary=True)
        assert by_id.returncode == 0, by_id.stderr
        assert by_id.stdout == PNG_BYTES
        by_path = _dw(repo, "evidence", "asset", "DM-1-01", png["path"], binary=True)
        assert by_path.stdout == PNG_BYTES

    def test_bundle_id_resolves_the_same_dossier(self, tmp_path):
        repo = _make_repo(tmp_path)
        doc = self._manifest(repo)
        png = next(m for m in doc["members"] if m["path"].endswith("proof.png"))
        out = _dw(repo, "evidence", "asset", doc["bundle_id"], png["asset_id"], binary=True)
        assert out.returncode == 0, out.stderr
        assert out.stdout == PNG_BYTES

    def test_traversal_and_absolute_paths_are_not_in_manifest(self, tmp_path):
        repo = _make_repo(tmp_path)
        (tmp_path / "secret.md").write_text("SECRET", encoding="utf-8")
        for evil in (
            "pm/roadmap/../../../secret.md",
            "/etc/hosts",
            "../secret.md",
        ):
            out = _dw(repo, "evidence", "asset", "DM-1-01", evil, binary=True)
            assert out.returncode != 0
            assert b"not_in_manifest" in out.stderr
            assert out.stdout == b""

    def test_symlink_is_never_a_member_and_never_streams(self, tmp_path):
        repo = _make_repo(tmp_path)
        secret = tmp_path / "outside-secret.txt"
        secret.write_text("SECRET", encoding="utf-8")
        link_rel = "pm/roadmap/demo/phase-1-alpha/assets/leak.txt"
        (repo / link_rel).symlink_to(secret)
        doc = self._manifest(repo)
        assert all(m["path"] != link_rel for m in doc["members"])
        out = _dw(repo, "evidence", "asset", "DM-1-01", link_rel, binary=True)
        assert out.returncode != 0
        assert b"refused" in out.stderr
        assert b"SECRET" not in out.stdout

    def test_oversize_asset_is_listed_but_refused(self, tmp_path):
        repo = _make_repo(tmp_path)
        big = _phase_dir(repo) / "assets" / "big.bin"
        big.write_bytes(b"\0" * (dw_manifest.MAX_ASSET_BYTES + 1))
        doc = self._manifest(repo)
        member = next(m for m in doc["members"] if m["path"].endswith("big.bin"))
        assert member["bytes"] == dw_manifest.MAX_ASSET_BYTES + 1
        out = _dw(repo, "evidence", "asset", "DM-1-01", member["asset_id"], binary=True)
        assert out.returncode != 0
        assert b"oversize" in out.stderr
        assert out.stdout == b""

    def test_unknown_story_or_bundle_dies_by_name(self, tmp_path):
        repo = _make_repo(tmp_path)
        out = _dw(repo, "evidence", "asset", "DM-9-99", "anything")
        assert out.returncode != 0
        assert "no story or evidence bundle" in out.stderr
