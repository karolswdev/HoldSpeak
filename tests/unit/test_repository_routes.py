"""HS-113-06 repository drawer routes: real git fixture and containment checks."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import quote
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery import DeliveryRegistry
from holdspeak.services import repository_workspace
from holdspeak.web.context import WebContext
from holdspeak.web.routes.repositories import _safe_path, build_repositories_router


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _git_output(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _context() -> WebContext:
    return WebContext(get_state=lambda: {}, broadcast=lambda *_: None)


def _client(tmp_path: Path) -> tuple[TestClient, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.test")
    _git(root, "config", "user.name", "Test")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (root / "README.md").write_text("seed\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "seed")
    registry = DeliveryRegistry(tmp_path / "registry.json", map_path=tmp_path / "missing.json")
    registry.register(str(root), label="Fixture")
    app = FastAPI()
    app.include_router(build_repositories_router(_context(), registry=registry))
    return TestClient(app), root


def test_repository_tree_status_stage_and_commit(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]

    files = client.get(f"/api/repositories/{repository_id}/tree").json()["files"]
    assert [row["name"] for row in files] == ["src", "README.md"]
    nested = client.get(f"/api/repositories/{repository_id}/tree?path=src").json()["files"]
    assert nested[0]["path"] == "src/main.py"

    assert client.put(
        f"/api/repositories/{repository_id}/file/src/main.py",
        json={"content": "print('changed')\n"},
    ).status_code == 200
    assert client.get(f"/api/repositories/{repository_id}/status").json()["dirty"] == 1
    assert client.post(
        f"/api/repositories/{repository_id}/stage", json={"paths": ["src/main.py"]}
    ).status_code == 200
    assert client.post(
        f"/api/repositories/{repository_id}/commit", json={"message": "change main"}
    ).status_code == 200
    assert _git_output(root, "log", "-1", "--format=%s") == "change main"


def test_repository_file_routes_refuse_traversal(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    # HTTP normalizes `..` path segments before FastAPI can route them; the
    # shared guard protects every file verb once it receives a path.
    for path in ("../outside.txt", "/outside.txt", "src/../outside.txt"):
        try:
            _safe_path(root, path)
        except ValueError as exc:
            assert str(exc) == "path traversal refused"
        else:
            raise AssertionError(f"accepted traversal path: {path}")
    response = client.post(
        f"/api/repositories/{repository_id}/stage", json={"paths": ["../outside.txt"]}
    )
    assert response.status_code == 400
    assert response.json()["error"] == "path traversal refused"


def test_repository_tree_distinguishes_missing_file_and_empty_directory(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    tree = f"/api/repositories/{repository_id}/tree"

    # A registered source can change while a view retains its location. The
    # browser needs this distinction to keep Back/Retry after a lost folder.
    (root / "empty").mkdir()
    empty = client.get(f"{tree}?path=empty")
    assert empty.status_code == 200
    assert empty.json() == {"files": []}

    missing = client.get(f"{tree}?path=removed")
    assert missing.status_code == 404
    assert missing.json() == {"error": "directory not found"}

    file_path = client.get(f"{tree}?path=README.md")
    assert file_path.status_code == 400
    assert file_path.json() == {"error": "path is not a directory"}

    root_dot = client.get(f"{tree}?path=.")
    assert root_dot.status_code == 200
    assert root_dot.json() == client.get(tree).json()

    traversal = client.get(f"{tree}?path=src%2F..%2FREADME.md")
    assert traversal.status_code == 400
    assert traversal.json() == {"error": "path traversal refused"}


def _worktree_client(tmp_path: Path) -> tuple[TestClient, Path, Path, str, str, DeliveryRegistry]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.test")
    _git(root, "config", "user.name", "Test")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("primary\n", encoding="utf-8")
    (root / "README.md").write_text("primary readme\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "seed")
    worktree = tmp_path / "agent-worktree"
    _git(root, "worktree", "add", "-b", "agent-change", str(worktree), "HEAD")

    registry = DeliveryRegistry(tmp_path / "registry.json", map_path=tmp_path / "missing.json")
    source, primary = registry.register(str(root), label="Fixture")
    registered_source, selected = registry.register(str(worktree), label="Fixture")
    assert registered_source.source_id == source.source_id
    assert primary.worktree_id != selected.worktree_id
    app = FastAPI()
    app.include_router(build_repositories_router(_context(), registry=registry))
    return TestClient(app), root, worktree, source.source_id, selected.worktree_id, registry


def test_repository_worktree_scope_reads_writes_diff_stage_and_commit_in_place(tmp_path: Path) -> None:
    client, root, worktree, source_id, worktree_id, _ = _worktree_client(tmp_path)
    scoped = f"?worktree_id={worktree_id}"

    (worktree / "src" / "main.py").write_text("worktree\n", encoding="utf-8")
    primary_read = client.get(f"/api/repositories/{source_id}/file/src/main.py")
    scoped_read = client.get(f"/api/repositories/{source_id}/file/src/main.py{scoped}")
    assert primary_read.status_code == 200
    assert primary_read.json()["content"] == "primary\n"
    assert scoped_read.status_code == 200
    assert scoped_read.json()["content"] == "worktree\n"
    assert scoped_read.json()["sha256"] == hashlib.sha256(b"worktree\n").hexdigest()

    unknown = client.get(
        f"/api/repositories/{source_id}/file/src/main.py?worktree_id=wt_unknown"
    )
    assert unknown.status_code == 404
    assert unknown.json() == {"error": "worktree not found"}

    status = client.get(f"/api/repositories/{source_id}/status{scoped}").json()
    assert status["dirty"] == 1
    assert status["changes"] == [{
        "path": "src/main.py",
        "status": "M",
        "index_status": " ",
        "worktree_status": "M",
    }]
    diff = client.get(f"/api/repositories/{source_id}/diff{scoped}&path=src/main.py")
    assert diff.status_code == 200
    assert "-primary" in diff.json()["diff"]
    assert "+worktree" in diff.json()["diff"]

    current_sha = scoped_read.json()["sha256"]
    written = client.put(
        f"/api/repositories/{source_id}/file/src/main.py{scoped}",
        json={"content": "edited in worktree\n", "expected_sha256": current_sha},
    )
    assert written.status_code == 200
    assert client.get(f"/api/repositories/{source_id}/file/src/main.py").json()["content"] == "primary\n"
    assert (worktree / "src" / "main.py").read_text(encoding="utf-8") == "edited in worktree\n"

    staged = client.post(
        f"/api/repositories/{source_id}/stage", json={"paths": ["src/main.py"], "worktree_id": worktree_id}
    )
    assert staged.status_code == 200
    staged_status = client.get(f"/api/repositories/{source_id}/status{scoped}").json()
    assert staged_status["changes"][0]["index_status"] == "M"
    assert staged_status["changes"][0]["worktree_status"] == " "
    committed = client.post(
        f"/api/repositories/{source_id}/commit", json={"message": "worktree change", "worktree_id": worktree_id}
    )
    assert committed.status_code == 200
    assert _git_output(worktree, "log", "-1", "--format=%s") == "worktree change"
    assert _git_output(root, "log", "-1", "--format=%s") == "seed"


def test_repository_route_refreshes_worktree_registered_by_separate_factory_instance(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.test")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("primary\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "seed")
    worktree = tmp_path / "agent-worktree"
    _git(root, "worktree", "add", "-b", "agent-change", str(worktree), "HEAD")

    registry_path = tmp_path / "registry.json"
    map_path = tmp_path / "missing.json"
    seed = DeliveryRegistry(registry_path, map_path=map_path)
    source, _ = seed.register(str(root), label="Fixture")

    app = FastAPI()
    app.include_router(
        build_repositories_router(
            _context(), registry_path=registry_path, map_path=map_path
        )
    )
    client = TestClient(app)

    # Force the router's initial read before the factory instance changes the
    # persisted registry, then verify a scoped route sees the new worktree.
    assert client.get("/api/repositories").status_code == 200
    factory_registry = DeliveryRegistry(registry_path, map_path=map_path)
    registered_source, selected = factory_registry.register(str(worktree), label="Fixture")
    assert registered_source.source_id == source.source_id

    response = client.get(
        f"/api/repositories/{source.source_id}/file/README.md"
        f"?worktree_id={selected.worktree_id}"
    )
    assert response.status_code == 200
    assert response.json()["content"] == "primary\n"


def test_repository_route_bootstraps_legacy_project_map_on_first_read(tmp_path: Path) -> None:
    _unused_client, root = _client(tmp_path)
    registry_path = tmp_path / "registry.json"
    map_path = tmp_path / "delivery_workbench.json"
    registry_path.unlink()
    map_path.write_text(
        json.dumps({"projects": {"legacy": str(root)}, "default": str(root)}),
        encoding="utf-8",
    )

    app = FastAPI()
    app.include_router(
        build_repositories_router(
            _context(), registry_path=registry_path, map_path=map_path
        )
    )
    client = TestClient(app)

    response = client.get("/api/repositories")
    assert response.status_code == 200
    repositories = response.json()["repositories"]
    assert len(repositories) == 1
    assert repositories[0]["name"] == "legacy"
    assert registry_path.exists()


def test_repository_registration_refuses_git_subdirectory_without_persisting_source(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.test")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("seed\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "seed")
    subdirectory = root / "src"
    subdirectory.mkdir()

    registry_path = tmp_path / "registry.json"
    registry = DeliveryRegistry(registry_path, map_path=tmp_path / "missing.json")
    before = registry_path.read_bytes()
    app = FastAPI()
    app.include_router(build_repositories_router(_context(), registry=registry))

    response = TestClient(app).post(
        "/api/repositories", json={"path": str(subdirectory), "label": "Invalid subdirectory"}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "path must be a git worktree root"}
    assert registry_path.read_bytes() == before
    assert registry.sources() == []


def test_repository_git_paths_preserve_special_names_and_renames(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    names = [
        "space name.txt",
        'quote"file.txt',
        "noné.txt",
        "line\nname.txt",
        "old -> name.txt",
    ]
    for index, name in enumerate(names):
        (root / name).write_text(f"seed {index}\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "special names")

    changed = names[1]
    (root / changed).write_text("changed\n", encoding="utf-8")
    renamed = "new -> name.txt"
    _git(root, "mv", names[4], renamed)
    untracked = "untracked -> é\nname.txt"
    (root / untracked).write_text("untracked content\n", encoding="utf-8")

    tree_paths = {row["path"] for row in client.get(
        f"/api/repositories/{repository_id}/tree"
    ).json()["files"]}
    assert set(names[:4]) | {renamed, untracked} <= tree_paths

    changes = client.get(f"/api/repositories/{repository_id}/status").json()["changes"]
    changed_paths = {row["path"] for row in changes}
    assert {changed, renamed, untracked} <= changed_paths
    assert names[4] not in changed_paths

    encoded = quote(changed, safe="")
    read = client.get(f"/api/repositories/{repository_id}/file/{encoded}")
    assert read.status_code == 200
    assert read.json()["content"] == "changed\n"

    diff = client.get(
        f"/api/repositories/{repository_id}/diff", params={"path": untracked}
    )
    assert diff.status_code == 200
    assert "untracked content" in diff.json()["diff"]


def test_repository_diff_reports_special_tracked_binary_name_verbatim(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    name = 'binary "noné" ->.bin'
    target = root / name
    target.write_bytes(b"before\x00binary")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "binary special name")
    target.write_bytes(b"after\x00binary")

    response = client.get(f"/api/repositories/{repository_id}/diff")
    assert response.status_code == 409
    assert response.json() == {"error": f"binary diff unsupported: {name}"}


def test_repository_worktree_only_special_path_stays_in_selected_worktree(
    tmp_path: Path,
) -> None:
    client, _root, worktree, source_id, worktree_id, _registry = _worktree_client(tmp_path)
    name = "worktree only -> café\n.txt"
    (worktree / name).write_text("worktree-only\n", encoding="utf-8")

    primary_tree = client.get(f"/api/repositories/{source_id}/tree").json()["files"]
    scoped_tree = client.get(
        f"/api/repositories/{source_id}/tree",
        params={"worktree_id": worktree_id},
    ).json()["files"]
    assert name not in {row["path"] for row in primary_tree}
    assert name in {row["path"] for row in scoped_tree}

    primary_changes = client.get(f"/api/repositories/{source_id}/status").json()["changes"]
    scoped_changes = client.get(
        f"/api/repositories/{source_id}/status",
        params={"worktree_id": worktree_id},
    ).json()["changes"]
    assert name not in {row["path"] for row in primary_changes}
    assert name in {row["path"] for row in scoped_changes}

    diff = client.get(
        f"/api/repositories/{source_id}/diff",
        params={"worktree_id": worktree_id, "path": name},
    )
    assert diff.status_code == 200
    assert "worktree-only" in diff.json()["diff"]


def test_repository_file_conflict_retains_original_and_preserves_mode(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    target = root / "README.md"
    original = client.get(f"/api/repositories/{repository_id}/file/README.md").json()
    target.chmod(0o750)
    target.write_text("changed outside the editor\n", encoding="utf-8")
    conflict = client.put(
        f"/api/repositories/{repository_id}/file/README.md",
        json={"content": "must not win\n", "expected_sha256": original["sha256"]},
    )
    assert conflict.status_code == 409
    assert target.read_text(encoding="utf-8") == "changed outside the editor\n"

    current_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    response = client.put(
        f"/api/repositories/{repository_id}/file/README.md",
        json={"content": "safe replacement\n", "expected_sha256": current_sha},
    )
    assert response.status_code == 200
    assert os.stat(target).st_mode & 0o777 == 0o750
    assert response.json()["sha256"] == hashlib.sha256(b"safe replacement\n").hexdigest()


def test_repository_atomic_replace_failure_retains_original_and_cleans_temp(
    tmp_path: Path,
) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    target = root / "README.md"
    target.chmod(0o751)
    original = target.read_bytes()
    original_mode = os.stat(target).st_mode & 0o777

    with patch.object(repository_workspace.os, "replace", side_effect=OSError("replace failed")):
        response = client.put(
            f"/api/repositories/{repository_id}/file/README.md",
            json={"content": "must not publish\n"},
        )
    assert response.status_code == 409
    assert response.json() == {"error": "file write failed"}
    assert target.read_bytes() == original
    assert os.stat(target).st_mode & 0o777 == original_mode
    assert list(root.glob(".README.md.*")) == []


def test_repository_status_reports_external_symlink_dirty_without_following_it(
    tmp_path: Path,
) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (root / "link.txt").symlink_to(outside)
    (root / "git-link.txt").symlink_to(root / ".git" / "config")

    status = client.get(f"/api/repositories/{repository_id}/status")
    assert status.status_code == 200
    assert status.json()["dirty"] == 2
    assert {item["path"] for item in status.json()["changes"]} == {"link.txt", "git-link.txt"}
    assert client.get(f"/api/repositories/{repository_id}/file/link.txt").status_code == 400
    assert client.get(f"/api/repositories/{repository_id}/file/git-link.txt").status_code == 400
    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_repository_worktree_gone_or_mismatched_never_falls_back_to_parent(
    tmp_path: Path,
) -> None:
    client, root, worktree, source_id, worktree_id, registry = _worktree_client(tmp_path)
    selected = next(wt for wt in registry.get(source_id).worktrees if wt.worktree_id == worktree_id)
    selected.path = str(tmp_path / "removed-worktree")
    gone = client.get(f"/api/repositories/{source_id}/file/README.md?worktree_id={worktree_id}")
    assert gone.status_code == 404
    assert gone.json() == {"error": "worktree unavailable"}

    nested = root / "nested-path"
    nested.mkdir()
    selected.path = str(nested)
    mismatch = client.get(f"/api/repositories/{source_id}/file/README.md?worktree_id={worktree_id}")
    assert mismatch.status_code == 409
    assert mismatch.json() == {"error": "worktree mismatch"}


def test_repository_paths_reject_internal_traversal_and_external_symlinks(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (root / "link.txt").symlink_to(outside)
    (root / "git-link.txt").symlink_to(root / ".git" / "config")

    for path in (".git/config", "link.txt", "git-link.txt"):
        response = client.get(f"/api/repositories/{repository_id}/file/{path}")
        assert response.status_code == 400
    write = client.put(
        f"/api/repositories/{repository_id}/file/link.txt", json={"content": "nope\n"}
    )
    assert write.status_code == 400
    assert outside.read_text(encoding="utf-8") == "outside\n"

    diff = client.get(f"/api/repositories/{repository_id}/diff?path=../outside.txt")
    assert diff.status_code == 400
    internal = client.get(f"/api/repositories/{repository_id}/diff?path=.git/config")
    assert internal.status_code == 400
    internal_link = client.get(f"/api/repositories/{repository_id}/diff?path=git-link.txt")
    assert internal_link.status_code == 400


def test_repository_diff_includes_untracked_text_and_names_binary_or_oversize_failures(
    tmp_path: Path,
) -> None:
    client, root = _client(tmp_path)
    repository_id = client.get("/api/repositories").json()["repositories"][0]["id"]
    (root / "new.txt").write_text("new line\n", encoding="utf-8")
    diff = client.get(f"/api/repositories/{repository_id}/diff")
    assert diff.status_code == 200
    assert "new line" in diff.json()["diff"]
    assert diff.json()["truncated"] is False

    (root / "binary.bin").write_bytes(b"header\x00binary")
    binary = client.get(f"/api/repositories/{repository_id}/diff?path=binary.bin")
    assert binary.status_code == 409
    assert binary.json() == {"error": "binary diff unsupported: binary.bin"}

    (root / "large.txt").write_text("x" * (1024 * 1024 + 1), encoding="utf-8")
    large = client.get(f"/api/repositories/{repository_id}/diff?path=large.txt")
    assert large.status_code == 409
    assert large.json() == {"error": "diff file too large: large.txt"}

    (root / "massive.txt").write_text("y" * (1024 * 1024 + 1), encoding="utf-8")
    read = client.get(f"/api/repositories/{repository_id}/file/massive.txt")
    assert read.status_code == 409
    assert read.json() == {"error": "file is not readable text"}
