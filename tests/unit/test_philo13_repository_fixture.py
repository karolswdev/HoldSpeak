"""PHILO-13 B0: the Repository/Delivery input is a real tiny repo."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from holdspeak.delivery import DeliveryCollector, DeliveryRegistry
from holdspeak.delivery.dossiers import DossierService
from scripts.philo13_walk_fixture import (
    PROJECT_SLUG,
    REPOSITORY_LABEL,
    STORY_ID,
    create_repository_fixture,
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _run_dw(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(root / ".githooks" / "dw"), "--root", str(root), *args],
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )


def test_repository_fixture_uses_real_registry_collector_dossier_and_dw(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "graph-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    fixture = create_repository_fixture(home)
    repo = Path(fixture["path"])
    source_file = repo / "atlas_repository.py"
    source_bytes = source_file.read_bytes()
    head = _git(repo, "rev-parse", "HEAD")

    assert fixture == {
        "path": str(repo),
        "label": REPOSITORY_LABEL,
        "project_slug": PROJECT_SLUG,
        "story_id": STORY_ID,
        "git_head": head,
    }
    assert head == fixture["git_head"]
    assert source_bytes
    assert b"Repository window reads this fixture." in source_bytes
    assert (repo / ".githooks" / "dw").read_bytes() == (
        Path(__file__).resolve().parents[2] / ".githooks" / "dw"
    ).read_bytes()
    assert (repo / ".githooks" / "dw_pmo" / "manifest.py").is_file()
    assert repo.resolve().is_relative_to(home.resolve())

    capabilities = _run_dw(repo, "capabilities", "--json")
    state = _run_dw(repo, "state", "--json")
    manifest = _run_dw(
        repo, "evidence", "manifest", PROJECT_SLUG, STORY_ID, "--json"
    )
    assert capabilities.returncode == 0, capabilities.stderr
    assert state.returncode == 0, state.stderr
    assert manifest.returncode == 0, manifest.stderr
    assert json.loads(capabilities.stdout)["capabilities_schema"] == 1
    state_doc = json.loads(state.stdout)
    story_rows = state_doc["projects"][0]["stories"]
    assert any(row["story_id"] == STORY_ID and row["status"] == "ready" for row in story_rows)
    manifest_doc = json.loads(manifest.stdout)
    assert manifest_doc["project"] == PROJECT_SLUG
    assert manifest_doc["story_id"] == STORY_ID
    assert manifest_doc["source_revision"]["head_sha"] == head

    registry = DeliveryRegistry(
        home / "delivery-sources.json", map_path=home / "missing-map.json"
    )
    source, worktree = registry.register(str(repo), label=fixture["label"])
    assert source.label == REPOSITORY_LABEL
    assert worktree.path == str(repo.resolve())
    assert source.primary_path == str(repo.resolve())

    collector = DeliveryCollector(registry, max_age_seconds=60)
    snapshot = collector.snapshot()
    row = snapshot["sources"][0]
    assert row["status"] == "live"
    assert row["label"] == REPOSITORY_LABEL
    assert any(project["slug"] == PROJECT_SLUG for project in row["projects"])
    assert any(
        story["story_id"] == STORY_ID
        for project in row["projects"]
        if project["slug"] == PROJECT_SLUG
        for story in project["stories"]
    )

    service = DossierService(registry, max_age_seconds=60)
    dossier = service.story_dossier(source.source_id, PROJECT_SLUG, STORY_ID)
    assert dossier["project"] == PROJECT_SLUG
    assert dossier["story_id"] == STORY_ID
    assert dossier["source_revision"]["head_sha"] == head
    assert dossier["story"]["state"] == "ready"
    assert "Repository window" in dossier["story"]["markdown"]


def test_repository_fixture_refuses_reuse_and_symlinked_home(
    tmp_path: Path,
) -> None:
    home = tmp_path / "graph-home"
    home.mkdir()
    create_repository_fixture(home)
    with pytest.raises(FileExistsError):
        create_repository_fixture(home)

    linked_home = tmp_path / "linked-home"
    linked_home.symlink_to(home, target_is_directory=True)
    with pytest.raises(ValueError, match="must not be a symlink"):
        create_repository_fixture(linked_home)
