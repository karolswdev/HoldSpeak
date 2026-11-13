"""The local git repository drawer as a service (HS-113-06; declared 2026-11-09).

Repository ids are DeliveryRegistry source ids. The registry keeps the local
worktree path on the hub; no answer carries that path. Every git call is an
argv subprocess in the resolved worktree; the file verbs resolve and contain
the requested path before they touch the disk.

``holdspeak/repository_operations.py`` declares one operation per verb; the
routes (``web/routes/repositories.py``) and the MCP tools are produced from
those rows. A refusal is :class:`RepositoryRefused`: its status and its words,
which the routes answer as ``{"error": words}``.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Optional

from ..delivery import DeliveryRegistry
from ..delivery.registry import RegistryError
from ..logging_config import get_logger
from .errors import ServiceError
from .repository_workspace import (
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
    run_git,
    safe_path,
    sha256_bytes,
    stage_paths,
    validate_worktree_root,
)

log = get_logger("services.repository_drawer")


#: The refusal's code by its status (an MCP caller reads the code).
_CODES = {400: "validation_error", 403: "forbidden", 404: "not_found", 409: "conflict", 422: "validation_error"}


class RepositoryRefused(ServiceError):
    """A named refusal with its HTTP status (``{"error": detail}`` on the wire)."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(_CODES.get(status, "repository_failed"), detail, context={"status": status})
        self.status = status


def _flag(value: Any) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)


def _scope(query_id: Optional[str], body_id: Optional[str]) -> Optional[str]:
    if query_id is not None and body_id is not None and query_id != body_id:
        raise RepositoryRefused(400, "worktree scope conflict")
    return query_id if query_id is not None else body_id


def _contained(root: Path, path: str) -> Path:
    try:
        return safe_path(root, path)
    except ValueError as exc:
        raise RepositoryRefused(400, str(exc)) from exc


def _workspace(call: Any) -> Any:
    try:
        return call()
    except RepositoryWorkspaceError as exc:
        raise RepositoryRefused(exc.status_code, exc.message) from exc


class RepositoryDrawerService:
    """The repository drawer's verbs over one DeliveryRegistry.

    ``registry``: an injected registry (tests, composed callers) stays
    authoritative with its in-memory changes. Without one, each read takes a
    side-effect-free snapshot from disk and each write loads a fresh writable
    registry, so a worktree another registry instance registered is seen.
    """

    def __init__(self, db: Any = None, *, observer: Any = None, registry: Optional[DeliveryRegistry] = None,
                 registry_path: Optional[Path] = None, map_path: Optional[Path] = None) -> None:
        self._db = db
        self._observer = observer
        self._registry = registry
        self._registry_path = registry_path
        self._map_path = map_path
        self._lock = threading.Lock()
        self._bootstrapped = registry is not None

    # ── the registry ────────────────────────────────────────────────────

    def _bootstrap(self) -> None:
        """The one-time legacy-map import, on the first production read."""
        if self._bootstrapped:
            return
        with self._lock:
            if self._bootstrapped:
                return
            # The constructor runs only for this first bootstrap; later reads
            # use read_only_snapshot, so a read never re-imports or rewrites.
            DeliveryRegistry(self._registry_path, map_path=self._map_path)
            self._bootstrapped = True

    def _read_registry(self) -> DeliveryRegistry:
        if self._registry is not None:
            return self._registry
        self._bootstrap()
        return DeliveryRegistry.read_only_snapshot(self._registry_path)

    def _write_registry(self) -> DeliveryRegistry:
        if self._registry is not None:
            return self._registry
        current = DeliveryRegistry(self._registry_path, map_path=self._map_path)
        self._bootstrapped = True
        return current

    def _root(self, repository_id: str, worktree_id: Optional[str] = None) -> Path:
        _, root = _workspace(lambda: resolve_worktree(self._read_registry(), repository_id, worktree_id))
        return root

    @staticmethod
    def _row(source: Any, root: Path) -> dict[str, Any]:
        return {"kind": "repository", "id": source.source_id, "name": source.label,
                "source_id": source.source_id, "branch": repository_status(root)["branch"], "created_at": ""}

    # ── the verbs ───────────────────────────────────────────────────────

    def list_repositories(self, principal: Any) -> dict[str, Any]:
        del principal
        try:
            rows = []
            current = self._read_registry()
            for source in current.sources():
                if not source.primary_path:
                    continue
                try:
                    _, root = resolve_worktree(current, source.source_id)
                except RepositoryWorkspaceError:
                    continue
                rows.append(self._row(source, root))
            return {"repositories": rows}
        except Exception as exc:
            log.error("repository list failed: %s", exc)
            raise RepositoryRefused(500, "repository list failed") from exc

    @staticmethod
    def registration_arguments(args: dict[str, Any]) -> dict[str, Any]:
        result = dict(args)
        if args.get("source_id"):
            result.pop("path", None)
            result.pop("label", None)
        return result

    @staticmethod
    def checkout_arguments(args: dict[str, Any]) -> dict[str, Any]:
        return {**args, **({"branch": args["branch"].strip()} if isinstance(args.get("branch"), str) else {})}

    def resolve_workspace_arguments(self, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
        _source, _root, identity = _workspace(lambda: resolve_worktree(self._read_registry(),
            str(args.get("repository_id") or ""), _scope(args.get("query_worktree_id"), args.get("worktree_id")),
            with_identity=True))
        return {**args, "worktree_id": identity}

    def resolve_commit_arguments(self, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
        import hashlib
        resolved = self.resolve_workspace_arguments(principal, args)
        root = self._root(resolved["repository_id"], resolved["worktree_id"])
        raw = run_git(root, "diff", "--cached", "--raw", "-z", "--no-ext-diff", "--no-textconv")
        names = run_git(root, "diff", "--cached", "--name-only", "-z", "--no-ext-diff", "--no-textconv")
        if raw.returncode or names.returncode:
            raise RepositoryRefused(409, "The staged files cannot be read.")
        revision = hashlib.sha256(raw.stdout.encode()).hexdigest()
        if args.get("expected_index") is not None and args["expected_index"] != revision:
            raise RepositoryRefused(409, "The staged files changed. Read again.")
        return {**resolved, "message": args["message"].strip() if isinstance(args.get("message"), str) else args.get("message"),
                "file_count": len([name for name in names.stdout.split("\0") if name]), "expected_index": revision}

    def register(self, principal: Any, source_id: Optional[str] = None, path: Optional[str] = None,
                 label: Optional[str] = None) -> dict[str, Any]:
        prepared = self.registration_arguments({"source_id": source_id, "path": path, "label": label})
        source_id, path, label = prepared.get("source_id"), prepared.get("path"), prepared.get("label")
        del principal
        try:
            # Registry writes are serialized. Each production write starts
            # from disk, so a worktree another instance registered stays.
            with self._lock:
                if source_id:
                    current = self._write_registry()
                    try:
                        source, root = resolve_worktree(current, source_id)
                    except RepositoryWorkspaceError as exc:
                        if exc.status_code == 404:
                            raise RepositoryRefused(404, "repository not found") from exc
                        raise RegistryError(exc.message) from exc
                elif path:
                    # Preflight before the writable registry: a Git
                    # subdirectory must not leave a persisted unusable source.
                    validate_worktree_root(path)
                    current = self._write_registry()
                    source, worktree = current.register(path, label=label)
                    try:
                        _, root = resolve_worktree(current, source.source_id, worktree.worktree_id)
                    except RepositoryWorkspaceError as exc:
                        raise RegistryError(exc.message) from exc
                else:
                    raise RegistryError("source_id or path required")
            return {"repository": self._row(source, root)}
        except RepositoryRefused:
            raise
        except RepositoryWorkspaceError as exc:
            raise RepositoryRefused(exc.status_code, exc.message) from exc
        except RegistryError as exc:
            raise RepositoryRefused(400, str(exc)) from exc
        except Exception as exc:
            log.error("repository registration failed: %s", exc)
            raise RepositoryRefused(500, "repository registration failed") from exc

    def tree(self, principal: Any, repository_id: str, path: str = "",
             worktree_id: Optional[str] = None) -> dict[str, Any]:
        del principal
        root = self._root(repository_id, worktree_id)
        directory = _contained(root, path) if path else root
        if not directory.exists():
            raise RepositoryRefused(404, "directory not found")
        if not directory.is_dir():
            raise RepositoryRefused(400, "path is not a directory")
        relative = directory.relative_to(root)
        prefix = "" if relative == Path(".") else relative.as_posix()
        return {"files": repository_tree(root, prefix)}

    def read_file(self, principal: Any, repository_id: str, path: str,
                  worktree_id: Optional[str] = None) -> dict[str, Any]:
        del principal
        root = self._root(repository_id, worktree_id)
        target = _contained(root, path)
        try:
            if not target.is_file():
                raise RepositoryRefused(404, "file not found")
            content, text = read_text_bytes(target)
        except RepositoryRefused:
            raise
        except ValueError as exc:
            raise RepositoryRefused(400, str(exc)) from exc
        except (OSError, UnicodeDecodeError) as exc:
            raise RepositoryRefused(409, "file is not readable text") from exc
        return {"path": path, "content": text, "sha256": sha256_bytes(content)}

    def write_file(self, principal: Any, repository_id: str, path: str, content: Any,
                   expected_sha256: Optional[str] = None, worktree_id: Optional[str] = None,
                   query_worktree_id: Optional[str] = None) -> dict[str, Any]:
        del principal
        if not isinstance(content, str):
            raise RepositoryRefused(422, "content required")
        root = self._root(repository_id, _scope(query_worktree_id, worktree_id))
        target = _contained(root, path)
        try:
            if target.exists() and not target.is_file():
                raise RepositoryRefused(409, "file write failed")
            encoded = content.encode("utf-8")
            if expected_sha256 is not None:
                if not target.exists():
                    raise RepositoryRefused(409, "file changed before write")
                current, _ = read_text_bytes(target)
                expected = str(expected_sha256).strip()
                if expected.startswith("sha256:"):
                    expected = expected[7:]
                if expected != sha256_bytes(current):
                    raise RepositoryRefused(409, "file changed before write")
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(target, encoded)
        except RepositoryRefused:
            raise
        except ValueError as exc:
            raise RepositoryRefused(400, str(exc)) from exc
        except (OSError, UnicodeDecodeError) as exc:
            raise RepositoryRefused(409, "file write failed") from exc
        return {"path": path, "written": True, "sha256": sha256_bytes(encoded)}

    def diff(self, principal: Any, repository_id: str, worktree_id: Optional[str] = None,
             path: Optional[str] = None, staged: Any = False) -> dict[str, Any]:
        del principal
        root = self._root(repository_id, worktree_id)
        try:
            text, truncated = repository_diff(root, relative=path, staged=_flag(staged))
        except ValueError as exc:
            message = str(exc)
            if message in {"path traversal refused", "repository internals refused", "path is a directory"}:
                raise RepositoryRefused(400, message) from exc
            if message == "file not found":
                raise RepositoryRefused(404, message) from exc
            raise RepositoryRefused(409, message) from exc
        return {"diff": text, "truncated": truncated}

    def stage(self, principal: Any, repository_id: str, paths: Any = None, worktree_id: Optional[str] = None,
              query_worktree_id: Optional[str] = None) -> dict[str, Any]:
        del principal
        root = self._root(repository_id, _scope(query_worktree_id, worktree_id))
        if not paths:
            raise RepositoryRefused(400, "files required")
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            raise RepositoryRefused(422, "paths is a list of file paths")
        relative = [_contained(root, path).relative_to(root).as_posix() for path in paths]
        return {"staged": _workspace(lambda: stage_paths(root, relative))}

    def commit(self, principal: Any, repository_id: str, message: Any = None, worktree_id: Optional[str] = None,
               query_worktree_id: Optional[str] = None, expected_index: Optional[str] = None) -> dict[str, Any]:
        if not isinstance(message, str):
            raise RepositoryRefused(422, "message required")
        if expected_index is not None:
            resolved = self.resolve_commit_arguments(principal, {"repository_id": repository_id, "message": message,
                "worktree_id": worktree_id, "query_worktree_id": query_worktree_id, "expected_index": expected_index})
            worktree_id = resolved["worktree_id"]
        root = self._root(repository_id, _scope(query_worktree_id, worktree_id))
        words = message.strip()
        if not words:
            raise RepositoryRefused(400, "commit message required")
        return _workspace(lambda: commit_changes(root, words))

    def status(self, principal: Any, repository_id: str, worktree_id: Optional[str] = None) -> dict[str, Any]:
        del principal
        root = self._root(repository_id, worktree_id)
        return _workspace(lambda: repository_status(root))

    def branches(self, principal: Any, repository_id: str, worktree_id: Optional[str] = None) -> dict[str, Any]:
        del principal
        root = self._root(repository_id, worktree_id)
        return {"branches": _workspace(lambda: list_branches(root))}

    def checkout(self, principal: Any, repository_id: str, branch: Any = None, worktree_id: Optional[str] = None,
                 query_worktree_id: Optional[str] = None) -> dict[str, Any]:
        del principal
        if not isinstance(branch, str):
            raise RepositoryRefused(422, "branch required")
        root = self._root(repository_id, _scope(query_worktree_id, worktree_id))
        return _workspace(lambda: checkout_branch(root, branch.strip()))


__all__ = ["RepositoryDrawerService", "RepositoryRefused"]
