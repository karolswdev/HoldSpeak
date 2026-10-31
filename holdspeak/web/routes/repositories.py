"""Local git repository drawer routes (HS-113-06).

Repository ids are DeliveryRegistry source ids.  The registry retains the local
worktree path server-side, while every response keeps that path off the wire.
All git invocations use argv subprocesses in the resolved worktree; file verbs
also resolve and contain their requested path before touching disk.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...delivery import DeliveryRegistry
from ...delivery.registry import RegistryError
from ...logging_config import get_logger
from ...services.repository_workspace import (
    RepositoryWorkspaceError,
    atomic_write,
    checkout_branch,
    commit_changes,
    list_branches,
    read_text_bytes,
    repository_diff,
    repository_status,
    repository_tree,
    resolve_worktree,
    safe_path,
    sha256_bytes,
    stage_paths,
    validate_worktree_root,
)
from ..context import WebContext

log = get_logger("web.routes.repositories")


class RegisterRepositoryRequest(BaseModel):
    source_id: Optional[str] = None
    path: Optional[str] = None
    label: Optional[str] = None


class WriteFileRequest(BaseModel):
    content: str
    expected_sha256: Optional[str] = None
    worktree_id: Optional[str] = None


class StageRequest(BaseModel):
    paths: list[str] = Field(default_factory=list)
    worktree_id: Optional[str] = None


class CommitRequest(BaseModel):
    message: str
    worktree_id: Optional[str] = None


class CheckoutRequest(BaseModel):
    branch: str
    worktree_id: Optional[str] = None


def _error(status: int, error: str) -> JSONResponse:
    return JSONResponse({"error": error}, status_code=status)


def _path_error(exc: ValueError) -> JSONResponse:
    return _error(400, str(exc))


def _scope_id(query_id: Optional[str], body_id: Optional[str]) -> str | None | JSONResponse:
    if query_id is not None and body_id is not None and query_id != body_id:
        return _error(400, "worktree scope conflict")
    return query_id if query_id is not None else body_id


_safe_path = safe_path


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
    injected_registry = registry is not None
    registry_lock = threading.Lock()
    bootstrap: dict[str, bool] = {"complete": injected_registry}

    def _bootstrap_registry() -> None:
        """Preserve the old one-time legacy-map import on first production read."""
        if bootstrap["complete"]:
            return
        with registry_lock:
            if bootstrap["complete"]:
                return
            # The constructor is intentionally used only for this first lazy
            # bootstrap.  Subsequent reads use read_only_snapshot below, so a
            # route read cannot re-import or rewrite legacy state.
            DeliveryRegistry(registry_path, map_path=map_path)
            bootstrap["complete"] = True

    def _read_registry() -> DeliveryRegistry:
        """Read the latest persisted registry for production route calls.

        A factory/launch may register a worktree through another registry
        instance after this router was built.  An injected registry remains
        authoritative for tests and composed callers, including their
        in-memory mutations; the default route composition gets a side-effect
        free snapshot on every operation instead of retaining stale state.
        """
        if injected_registry:
            current = holder["registry"]
            assert current is not None
            return current
        _bootstrap_registry()
        return DeliveryRegistry.read_only_snapshot(registry_path)

    def _write_registry() -> DeliveryRegistry:
        """Load a fresh writable registry before a route mutation."""
        if injected_registry:
            current = holder["registry"]
            assert current is not None
            return current
        current = DeliveryRegistry(registry_path, map_path=map_path)
        bootstrap["complete"] = True
        return current

    def _root_or_404(
        repository_id: str, worktree_id: Optional[str] = None
    ) -> tuple[Any, Path] | JSONResponse:
        try:
            return resolve_worktree(_read_registry(), repository_id, worktree_id)
        except RepositoryWorkspaceError as exc:
            return _error(exc.status_code, exc.message)

    @router.get("/api/repositories")
    async def api_repositories() -> Any:
        def list_repositories() -> dict[str, Any]:
            rows = []
            current = _read_registry()
            for source in current.sources():
                if not source.primary_path:
                    continue
                try:
                    _, root = resolve_worktree(current, source.source_id)
                except RepositoryWorkspaceError:
                    continue
                rows.append({
                    "kind": "repository",
                    "id": source.source_id,
                    "name": source.label,
                    "source_id": source.source_id,
                    "branch": repository_status(root)["branch"],
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
            # Registry writes are serialized per router.  Each production
            # mutation starts from disk so a factory instance that registered
            # a worktree cannot be overwritten by this route's stale copy.
            with registry_lock:
                if body.source_id:
                    current = _write_registry()
                    try:
                        source, root = resolve_worktree(current, body.source_id)
                    except RepositoryWorkspaceError as exc:
                        if exc.status_code == 404:
                            raise KeyError(exc.message) from exc
                        raise RegistryError(exc.message) from exc
                elif body.path:
                    # Preflight before loading/mutating the writable registry:
                    # a Git subdirectory must not leave a persisted unusable
                    # source after this route refuses it.
                    validate_worktree_root(body.path)
                    current = _write_registry()
                    source, worktree = current.register(body.path, label=body.label)
                    try:
                        _, root = resolve_worktree(
                            current, source.source_id, worktree.worktree_id
                        )
                    except RepositoryWorkspaceError as exc:
                        raise RegistryError(exc.message) from exc
                else:
                    raise RegistryError("source_id or path required")
            return {
                "repository": {
                    "kind": "repository",
                    "id": source.source_id,
                    "name": source.label,
                    "source_id": source.source_id,
                    "branch": repository_status(root)["branch"],
                    "created_at": "",
                }
            }
        try:
            return await asyncio.to_thread(register)
        except KeyError:
            return _error(404, "repository not found")
        except RepositoryWorkspaceError as exc:
            return _error(exc.status_code, exc.message)
        except RegistryError as exc:
            return _error(400, str(exc))
        except Exception as exc:
            log.error("repository registration failed: %s", exc)
            return _error(500, "repository registration failed")

    @router.get("/api/repositories/{repository_id}/tree")
    async def api_repository_tree(
        repository_id: str, path: str = "", worktree_id: Optional[str] = None
    ) -> Any:
        def tree() -> Any:
            resolved = _root_or_404(repository_id, worktree_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                directory = _safe_path(root, path) if path else root
            except ValueError as exc:
                return _path_error(exc)
            if not directory.exists():
                return _error(404, "directory not found")
            if not directory.is_dir():
                return _error(400, "path is not a directory")
            relative = directory.relative_to(root)
            prefix = "" if relative == Path(".") else relative.as_posix()
            return {"files": repository_tree(root, prefix)}
        return await asyncio.to_thread(tree)

    @router.get("/api/repositories/{repository_id}/file/{path:path}")
    async def api_repository_file(
        repository_id: str, path: str, worktree_id: Optional[str] = None
    ) -> Any:
        def read() -> Any:
            resolved = _root_or_404(repository_id, worktree_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                target = _safe_path(root, path)
                if not target.is_file():
                    return _error(404, "file not found")
                content, text = read_text_bytes(target)
                return {
                    "path": path,
                    "content": text,
                    "sha256": sha256_bytes(content),
                }
            except ValueError as exc:
                return _path_error(exc)
            except (OSError, UnicodeDecodeError):
                return _error(409, "file is not readable text")
        return await asyncio.to_thread(read)

    @router.put("/api/repositories/{repository_id}/file/{path:path}")
    async def api_repository_write_file(
        repository_id: str,
        path: str,
        body: WriteFileRequest,
        worktree_id: Optional[str] = None,
    ) -> Any:
        def write() -> Any:
            scope = _scope_id(worktree_id, body.worktree_id)
            if isinstance(scope, JSONResponse):
                return scope
            resolved = _root_or_404(repository_id, scope)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                target = _safe_path(root, path)
                if target.exists() and not target.is_file():
                    return _error(409, "file write failed")
                encoded = body.content.encode("utf-8")
                if body.expected_sha256 is not None:
                    if not target.exists():
                        return _error(409, "file changed before write")
                    current, _ = read_text_bytes(target)
                    expected = str(body.expected_sha256).strip()
                    if expected.startswith("sha256:"):
                        expected = expected[7:]
                    if expected != sha256_bytes(current):
                        return _error(409, "file changed before write")
                target.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(target, encoded)
                return {
                    "path": path,
                    "written": True,
                    "sha256": sha256_bytes(encoded),
                }
            except ValueError as exc:
                return _path_error(exc)
            except (OSError, UnicodeDecodeError):
                return _error(409, "file write failed")
        return await asyncio.to_thread(write)

    @router.get("/api/repositories/{repository_id}/diff")
    async def api_repository_diff(
        repository_id: str,
        worktree_id: Optional[str] = None,
        path: Optional[str] = None,
        staged: bool = False,
    ) -> Any:
        def diff() -> Any:
            resolved = _root_or_404(repository_id, worktree_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                text, truncated = repository_diff(root, relative=path, staged=staged)
                return {"diff": text, "truncated": truncated}
            except ValueError as exc:
                message = str(exc)
                if message in {"path traversal refused", "repository internals refused"}:
                    return _path_error(exc)
                if message == "path is a directory":
                    return _error(400, message)
                if message == "file not found":
                    return _error(404, message)
                return _error(409, message)
        return await asyncio.to_thread(diff)

    @router.post("/api/repositories/{repository_id}/stage")
    async def api_repository_stage(
        repository_id: str, body: StageRequest, worktree_id: Optional[str] = None
    ) -> Any:
        def stage() -> Any:
            scope = _scope_id(worktree_id, body.worktree_id)
            if isinstance(scope, JSONResponse):
                return scope
            resolved = _root_or_404(repository_id, scope)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            if not body.paths:
                return _error(400, "files required")
            try:
                paths = [_safe_path(root, path).relative_to(root).as_posix() for path in body.paths]
            except ValueError as exc:
                return _path_error(exc)
            try:
                return {"staged": stage_paths(root, paths)}
            except RepositoryWorkspaceError as exc:
                return _error(exc.status_code, exc.message)
        return await asyncio.to_thread(stage)

    @router.post("/api/repositories/{repository_id}/commit")
    async def api_repository_commit(
        repository_id: str, body: CommitRequest, worktree_id: Optional[str] = None
    ) -> Any:
        def commit() -> Any:
            scope = _scope_id(worktree_id, body.worktree_id)
            if isinstance(scope, JSONResponse):
                return scope
            resolved = _root_or_404(repository_id, scope)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            message = body.message.strip()
            if not message:
                return _error(400, "commit message required")
            try:
                return commit_changes(root, message)
            except RepositoryWorkspaceError as exc:
                return _error(exc.status_code, exc.message)
        return await asyncio.to_thread(commit)

    @router.get("/api/repositories/{repository_id}/status")
    async def api_repository_status(
        repository_id: str, worktree_id: Optional[str] = None
    ) -> Any:
        def status() -> Any:
            resolved = _root_or_404(repository_id, worktree_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                return repository_status(root)
            except RepositoryWorkspaceError as exc:
                return _error(exc.status_code, exc.message)
        return await asyncio.to_thread(status)

    @router.get("/api/repositories/{repository_id}/branches")
    async def api_repository_branches(
        repository_id: str, worktree_id: Optional[str] = None
    ) -> Any:
        def branches() -> Any:
            resolved = _root_or_404(repository_id, worktree_id)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            try:
                return {"branches": list_branches(root)}
            except RepositoryWorkspaceError as exc:
                return _error(exc.status_code, exc.message)
        return await asyncio.to_thread(branches)

    @router.post("/api/repositories/{repository_id}/checkout")
    async def api_repository_checkout(
        repository_id: str, body: CheckoutRequest, worktree_id: Optional[str] = None
    ) -> Any:
        def checkout() -> Any:
            scope = _scope_id(worktree_id, body.worktree_id)
            if isinstance(scope, JSONResponse):
                return scope
            resolved = _root_or_404(repository_id, scope)
            if isinstance(resolved, JSONResponse):
                return resolved
            _, root = resolved
            branch = body.branch.strip()
            try:
                return checkout_branch(root, branch)
            except RepositoryWorkspaceError as exc:
                return _error(exc.status_code, exc.message)
        return await asyncio.to_thread(checkout)

    return router
