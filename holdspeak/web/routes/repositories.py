"""Local git repository drawer routes (HS-113-06).

Repository ids are DeliveryRegistry source ids.  The registry retains the local
worktree path server-side, while every response keeps that path off the wire.
All git invocations use argv subprocesses in the resolved worktree; file verbs
also resolve and contain their requested path before touching disk.
"""
from __future__ import annotations

import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...delivery import DeliveryRegistry
from ...delivery.registry import RegistryError
from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.repositories")
GIT_TIMEOUT_SECONDS = 30


class RegisterRepositoryRequest(BaseModel):
    source_id: Optional[str] = None
    path: Optional[str] = None
    label: Optional[str] = None


class WriteFileRequest(BaseModel):
    content: str


class StageRequest(BaseModel):
    paths: list[str] = Field(default_factory=list)


class CommitRequest(BaseModel):
    message: str


class CheckoutRequest(BaseModel):
    branch: str


def _error(status: int, error: str) -> JSONResponse:
    return JSONResponse({"error": error}, status_code=status)


def _run(root: Path, *args: str, input_text: Optional[str] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(root),
        input=input_text,
        stdin=subprocess.DEVNULL if input_text is None else None,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=GIT_TIMEOUT_SECONDS,
    )


def _source_root(registry: DeliveryRegistry, source_id: str) -> tuple[Any, Path] | None:
    source = registry.get(source_id)
    if source is None or not source.primary_path:
        return None
    root = Path(source.primary_path).resolve()
    return source, root


def _safe_path(root: Path, value: str) -> Path:
    """Return a contained repo-relative path or raise ValueError.

    Reject traversal syntax before resolving so ``a/../b`` is not silently
    accepted even when it would resolve under the root.
    """
    raw = str(value or "")
    candidate = PurePosixPath(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts or "\\" in raw:
        raise ValueError("path traversal refused")
    target = (root / Path(*candidate.parts)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("path traversal refused") from exc
    return target


def _status_code(raw: str) -> str | None:
    pair = raw[:2]
    if pair == "??":
        return "?"
    for code in pair:
        if code in {"M", "A", "D"}:
            return code
    return None


def _porcelain(root: Path) -> dict[str, str | None]:
    proc = _run(root, "status", "--porcelain=v1", "--untracked-files=all")
    if proc.returncode:
        return {}
    statuses: dict[str, str | None] = {}
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        # Rename/copy porcelain is `old -> new`; the visible current file wins.
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[-1]
        statuses[path] = _status_code(line)
    return statuses


def _tree(root: Path, prefix: str) -> list[dict[str, Any]]:
    proc = _run(root, "ls-tree", "-r", "--name-only", "HEAD")
    tracked = proc.stdout.splitlines() if proc.returncode == 0 else []
    statuses = _porcelain(root)
    paths = set(tracked) | set(statuses)
    normalized_prefix = prefix.strip("/")
    children: dict[str, dict[str, Any]] = {}
    for raw in paths:
        try:
            _safe_path(root, raw)
        except ValueError:
            continue
        relative = PurePosixPath(raw)
        parts = relative.parts
        if normalized_prefix:
            prefix_parts = PurePosixPath(normalized_prefix).parts
            if parts[: len(prefix_parts)] != prefix_parts:
                continue
            parts = parts[len(prefix_parts) :]
        if not parts:
            continue
        name = parts[0]
        child_path = "/".join((*PurePosixPath(normalized_prefix).parts, name))
        if len(parts) > 1:
            children[name] = {"name": name, "path": child_path, "type": "dir", "status": None}
            continue
        modified = None
        local = root / raw
        if local.exists() and local.is_file():
            try:
                modified = datetime.fromtimestamp(local.stat().st_mtime, timezone.utc).isoformat()
            except OSError:
                pass
        children[name] = {
            "name": name,
            "path": child_path,
            "type": "file",
            "status": statuses.get(raw),
            "modified": modified,
        }
    return sorted(children.values(), key=lambda item: (item["type"] != "dir", item["name"].lower()))


def _repo_status(root: Path) -> dict[str, Any]:
    branch = _run(root, "branch", "--show-current").stdout.strip() or "detached"
    dirty_files = _porcelain(root)
    ahead = behind = 0
    counts = _run(root, "rev-list", "--left-right", "--count", "@{upstream}...HEAD")
    if counts.returncode == 0:
        try:
            behind, ahead = (int(value) for value in counts.stdout.split())
        except ValueError:
            pass
    return {"branch": branch, "dirty": len(dirty_files), "ahead": ahead, "behind": behind}


def build_repositories_router(
    ctx: WebContext,
    *,
    registry: Optional[DeliveryRegistry] = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
) -> APIRouter:
    _ = ctx
    router = APIRouter()
    holder: dict[str, DeliveryRegistry | None] = {"registry": registry}

    def _registry() -> DeliveryRegistry:
        if holder["registry"] is None:
            holder["registry"] = DeliveryRegistry(registry_path, map_path=map_path)
        return holder["registry"]

    def _root_or_404(repository_id: str) -> tuple[Any, Path] | JSONResponse:
        result = _source_root(_registry(), repository_id)
        return result if result is not None else _error(404, "repository not found")

    @router.get("/api/repositories")
    async def api_repositories() -> Any:
        def list_repositories() -> dict[str, Any]:
            rows = []
            for source in _registry().sources():
                if not source.primary_path:
                    continue
                root = Path(source.primary_path).resolve()
                rows.append({
                    "kind": "repository",
                    "id": source.source_id,
                    "name": source.label,
                    "source_id": source.source_id,
                    "branch": _repo_status(root)["branch"],
                    "created_at": "",
                })
            return {"repositories": rows}
        try:
            return await asyncio.to_thread(list_repositories)
        except Exception as exc:
            log.error("repository list failed: %s", exc)
            return _error(500, "repository list failed")

    @router.post("/api/repositories")
    async def api_register_repository(body: RegisterRepositoryRequest) -> Any:
        def register() -> dict[str, Any]:
            registry = _registry()
            if body.source_id:
                found = _source_root(registry, body.source_id)
                if found is None:
                    raise KeyError("repository not found")
                source, root = found
            elif body.path:
                source, _ = registry.register(body.path, label=body.label)
                root = Path(source.primary_path or "").resolve()
            else:
                raise RegistryError("source_id or path required")
            return {
                "repository": {
                    "kind": "repository",
                    "id": source.source_id,
                    "name": source.label,
                    "source_id": source.source_id,
                    "branch": _repo_status(root)["branch"],
                    "created_at": "",
                }
            }
        try:
            return await asyncio.to_thread(register)
        except KeyError:
            return _error(404, "repository not found")
        except RegistryError as exc:
            return _error(400, str(exc))
        except Exception as exc:
            log.error("repository registration failed: %s", exc)
            return _error(500, "repository registration failed")

    @router.get("/api/repositories/{repository_id}/tree")
    async def api_repository_tree(repository_id: str, path: str = "") -> Any:
        def tree() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                prefix = _safe_path(root, path).relative_to(root).as_posix() if path else ""
            except ValueError:
                return _error(400, "path traversal refused")
            return {"files": _tree(root, prefix)}
        return await asyncio.to_thread(tree)

    @router.get("/api/repositories/{repository_id}/file/{path:path}")
    async def api_repository_file(repository_id: str, path: str) -> Any:
        def read() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                target = _safe_path(root, path)
                if not target.is_file():
                    return _error(404, "file not found")
                return {"path": path, "content": target.read_text(encoding="utf-8")}
            except ValueError:
                return _error(400, "path traversal refused")
            except (OSError, UnicodeDecodeError):
                return _error(409, "file is not readable text")
        return await asyncio.to_thread(read)

    @router.put("/api/repositories/{repository_id}/file/{path:path}")
    async def api_repository_write_file(repository_id: str, path: str, body: WriteFileRequest) -> Any:
        def write() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                target = _safe_path(root, path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body.content, encoding="utf-8")
                return {"path": path, "written": True}
            except ValueError:
                return _error(400, "path traversal refused")
            except OSError:
                return _error(409, "file write failed")
        return await asyncio.to_thread(write)

    @router.post("/api/repositories/{repository_id}/stage")
    async def api_repository_stage(repository_id: str, body: StageRequest) -> Any:
        def stage() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            if not body.paths:
                return _error(400, "files required")
            try:
                paths = [_safe_path(root, path).relative_to(root).as_posix() for path in body.paths]
            except ValueError:
                return _error(400, "path traversal refused")
            proc = _run(root, "add", "--", *paths)
            if proc.returncode:
                return _error(409, "git stage failed")
            return {"staged": paths}
        return await asyncio.to_thread(stage)

    @router.post("/api/repositories/{repository_id}/commit")
    async def api_repository_commit(repository_id: str, body: CommitRequest) -> Any:
        def commit() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            message = body.message.strip()
            if not message:
                return _error(400, "commit message required")
            proc = _run(root, "commit", "-m", message)
            if proc.returncode:
                return _error(409, "git commit failed")
            return {"committed": True, "summary": proc.stdout.strip()}
        return await asyncio.to_thread(commit)

    @router.get("/api/repositories/{repository_id}/status")
    async def api_repository_status(repository_id: str) -> Any:
        def status() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            return _repo_status(root)
        return await asyncio.to_thread(status)

    @router.get("/api/repositories/{repository_id}/branches")
    async def api_repository_branches(repository_id: str) -> Any:
        def branches() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            proc = _run(root, "for-each-ref", "--format=%(refname:short)", "refs/heads")
            if proc.returncode:
                return _error(409, "git branch list failed")
            return {"branches": [line for line in proc.stdout.splitlines() if line]}
        return await asyncio.to_thread(branches)

    @router.post("/api/repositories/{repository_id}/checkout")
    async def api_repository_checkout(repository_id: str, body: CheckoutRequest) -> Any:
        def checkout() -> Any:
            resolved = _root_or_404(repository_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            branch = body.branch.strip()
            if not branch or branch.startswith("-"):
                return _error(400, "branch invalid")
            available = _run(root, "for-each-ref", "--format=%(refname:short)", "refs/heads")
            if branch not in available.stdout.splitlines():
                return _error(404, "branch not found")
            proc = _run(root, "switch", branch)
            if proc.returncode:
                return _error(409, "git checkout failed")
            return _repo_status(root)
        return await asyncio.to_thread(checkout)

    return router
