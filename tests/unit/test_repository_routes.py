"""HS-113-06 repository drawer routes: real git fixture and containment checks."""
from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.delivery import DeliveryRegistry
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
