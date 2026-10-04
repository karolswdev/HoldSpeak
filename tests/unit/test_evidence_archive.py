"""The evidence archive (owner ruling 2026-10-04; ``pm/ARCHIVE.md``).

The manifest is trusted by the Roadmap route and by the doc link check, so it
is checked here: its hash is pinned, no entry is in the tree, and every entry
is on the archive tag. The Roadmap route shows a link to an archived file as
no issue and a link to a file that is in no list as an issue, through the
real ``dw check``.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import holdspeak.web.routes.roadmaps as roadmaps

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "pm" / "archive-manifest.txt"
TAG = "evidence-2026-10-04"


def _entries() -> list[str]:
    return [line for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]


def test_the_manifest_hash_is_the_one_the_archive_doc_names() -> None:
    doc = (REPO / "pm" / "ARCHIVE.md").read_text(encoding="utf-8")
    named = re.search(r"Manifest SHA-256: `([0-9a-f]{64})`", doc)
    assert named, "pm/ARCHIVE.md must name the manifest SHA-256"
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == named.group(1)


def test_no_manifest_entry_is_in_the_tree() -> None:
    entries = _entries()
    assert len(entries) == len(set(entries))
    present = [name for name in entries if (REPO / name).exists()]
    assert present == [], "a file in the tree is not archived; take it out of the manifest"


def test_every_manifest_entry_is_on_the_archive_tag() -> None:
    listed = subprocess.run(
        ["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", "-z", TAG],
        capture_output=True, timeout=120,
    )
    if listed.returncode != 0:
        pytest.skip(f"tag {TAG} is not in this clone (git fetch origin tag {TAG})")
    on_tag = set(listed.stdout.decode("utf-8").split("\0"))
    missing = [name for name in _entries() if name not in on_tag]
    assert missing == []


def _scratch_roadmap(root: Path) -> None:
    """A project whose evidence links one archived shot and one missing shot."""
    shutil.copytree(REPO / ".githooks", root / ".githooks", ignore=shutil.ignore_patterns("_parked"))
    phase = root / "pm" / "roadmap" / "demo" / "phase-1-alpha"
    phase.mkdir(parents=True)
    (root / "pm" / "roadmap" / "demo" / "README.md").write_text(
        "# Demo\n\n**Current phase:** [phase-1-alpha](phase-1-alpha/current-phase-status.md)\n", encoding="utf-8")
    (phase / "current-phase-status.md").write_text(
        "# Phase 1\n\n| ID | Story | Status | Story file | Evidence |\n|---|---|---|---|---|\n"
        "| DEMO-1-01 | First | done | [story-01-first](./story-01-first.md) "
        "| [evidence-story-01](./evidence-story-01.md) |\n", encoding="utf-8")
    (phase / "final-summary.md").write_text("# Closed\n", encoding="utf-8")
    (phase / "story-01-first.md").write_text("# DEMO-1-01 — First\n\n- **Project:** demo\n- **Phase:** 1\n- **Status:** done\n", encoding="utf-8")
    (phase / "evidence-story-01.md").write_text(
        "# Evidence DEMO-1-01\n\n![archived](./assets/archived.png)\n\n![missing](./assets/missing.png)\n",
        encoding="utf-8")
    (root / "pm" / "archive-manifest.txt").write_text(
        "pm/roadmap/demo/phase-1-alpha/assets/archived.png\n", encoding="utf-8")


def test_the_roadmap_hides_an_archived_link_and_reports_a_missing_one(tmp_path: Path) -> None:
    _scratch_roadmap(tmp_path)
    code, output = roadmaps._run(tmp_path, "check", "demo")
    # The real checker reports both links: the filter has something to do.
    assert "broken asset reference: ./assets/archived.png" in output, output
    assert "broken asset reference: ./assets/missing.png" in output, output

    project = roadmaps._project(tmp_path, "demo")
    assert project is not None
    assert not any("archived.png" in issue for issue in project["issues"])
    assert any("missing.png" in issue for issue in project["issues"])
    assert project["health"] != "green"


def test_a_project_with_only_archived_links_is_green(tmp_path: Path) -> None:
    line = "ERROR pm/roadmap/demo/phase-1-alpha/evidence-story-01.md: broken asset reference: ./assets/archived.png"
    (tmp_path / "pm").mkdir()
    (tmp_path / "pm" / "archive-manifest.txt").write_text(
        "pm/roadmap/demo/phase-1-alpha/assets/archived.png\n", encoding="utf-8")
    issues = roadmaps._issues(line, tmp_path)
    assert issues == []
    assert roadmaps._health(1, issues) == "green"
    assert roadmaps._health(2, issues) == "red"
    # No manifest, or no repo root: the report stays.
    assert len(roadmaps._issues(line)) == 1
    assert len(roadmaps._issues(line.replace("archived", "other"), tmp_path)) == 1
