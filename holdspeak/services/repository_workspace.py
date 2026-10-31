"""Pure local repository/worktree operations used by the repository routes.

The DeliveryRegistry is the authority for source and worktree identity.  This
module resolves that exact registered path, performs bounded local Git/file
operations, and leaves HTTP status/error serialization to the route adapter.
"""
from __future__ import annotations

import difflib
import hashlib
import os
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Optional

from ..delivery import DeliveryRegistry

GIT_TIMEOUT_SECONDS = 30
MAX_DIFF_BYTES = 128 * 1024
MAX_UNTRACKED_FILE_BYTES = 1024 * 1024
MAX_FILE_READ_BYTES = 1024 * 1024


class RepositoryWorkspaceError(ValueError):
    """A named repository/worktree operation refusal."""

    def __init__(self, message: str, *, status_code: int = 409) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RepositoryPathError(ValueError):
    """A path was not safe to use inside the selected worktree."""


class RepositoryDiffError(ValueError):
    """A diff cannot be produced for the selected path/content."""


def _run_git(
    root: Path,
    *args: str,
    input_text: Optional[str] = None,
    binary: bool = False,
) -> subprocess.CompletedProcess[Any]:
    """Run one bounded Git subprocess, preserving text or raw-byte output."""
    options: dict[str, Any] = {
        "cwd": str(root),
        "stdin": subprocess.DEVNULL if input_text is None else None,
        "capture_output": True,
        "timeout": GIT_TIMEOUT_SECONDS,
    }
    if binary:
        options["text"] = False
    else:
        options.update(input=input_text, text=True, errors="replace")
    return subprocess.run(["git", *args], **options)


def run_git(
    root: Path, *args: str, input_text: Optional[str] = None
) -> subprocess.CompletedProcess[str]:
    return _run_git(root, *args, input_text=input_text)


def run_git_bytes(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """Run Git without allowing its pathname quoting to alter the result."""
    return _run_git(root, *args, binary=True)


def validate_worktree_root(path: str) -> Path:
    """Validate a requested registration path without touching the registry.

    ``DeliveryRegistry.register`` intentionally accepts any directory inside a
    Git checkout so callers can discover the checkout's common identity.  The
    repository route, however, promises that the requested path itself is the
    worktree root.  Keep that route preflight pure so a refused subdirectory
    cannot be persisted as a source before the normal registry write begins.
    """
    candidate = Path(str(path or "")).expanduser()
    try:
        candidate = candidate.resolve()
    except (OSError, RuntimeError):
        raise RepositoryWorkspaceError("path is not a directory", status_code=400) from None
    if not candidate.is_dir():
        raise RepositoryWorkspaceError("path is not a directory", status_code=400)
    try:
        probe = run_git(candidate, "rev-parse", "--show-toplevel")
    except (OSError, subprocess.TimeoutExpired):
        raise RepositoryWorkspaceError("path is not a git worktree", status_code=400) from None
    if probe.returncode or not probe.stdout.strip():
        raise RepositoryWorkspaceError("path is not a git worktree", status_code=400)
    try:
        actual_root = Path(probe.stdout.strip()).expanduser().resolve()
    except (OSError, RuntimeError):
        raise RepositoryWorkspaceError("path is not a git worktree", status_code=400) from None
    if actual_root != candidate:
        raise RepositoryWorkspaceError("path must be a git worktree root", status_code=400)
    return candidate


def resolve_worktree(
    registry: DeliveryRegistry,
    source_id: str,
    worktree_id: Optional[str] = None,
) -> tuple[Any, Path]:
    """Resolve only the selected source's registered worktree.

    The selected directory must still be a real Git worktree whose actual
    top-level path equals the registered path.  This prevents a removed or
    mismatched worktree from walking up into a parent repository.
    """
    source = registry.get(source_id)
    if source is None:
        raise RepositoryWorkspaceError("repository not found", status_code=404)
    if worktree_id is None:
        if not source.primary_path:
            raise RepositoryWorkspaceError("repository not found", status_code=404)
        selected = source.worktrees[0]
    else:
        selected = next(
            (worktree for worktree in source.worktrees if worktree.worktree_id == worktree_id),
            None,
        )
        if selected is None:
            raise RepositoryWorkspaceError("worktree not found", status_code=404)

    try:
        root = Path(selected.path).expanduser().resolve()
    except OSError:
        raise RepositoryWorkspaceError("worktree unavailable", status_code=404) from None
    if not root.is_dir():
        raise RepositoryWorkspaceError("worktree unavailable", status_code=404)
    try:
        probe = run_git(root, "rev-parse", "--show-toplevel")
    except (OSError, subprocess.TimeoutExpired):
        raise RepositoryWorkspaceError("worktree unavailable", status_code=404) from None
    if probe.returncode or not probe.stdout.strip():
        raise RepositoryWorkspaceError("worktree unavailable", status_code=404)
    try:
        actual_root = Path(probe.stdout.strip()).expanduser().resolve()
    except OSError:
        raise RepositoryWorkspaceError("worktree unavailable", status_code=404) from None
    if actual_root != root:
        raise RepositoryWorkspaceError("worktree mismatch", status_code=409)
    return source, root


def safe_path(root: Path, value: str) -> Path:
    """Resolve a contained repo-relative path, refusing traversal and internals."""
    raw = str(value or "")
    candidate = PurePosixPath(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts or "\\" in raw:
        raise RepositoryPathError("path traversal refused")
    if ".git" in candidate.parts:
        raise RepositoryPathError("repository internals refused")
    root = root.resolve()
    target = (root / Path(*candidate.parts)).resolve()
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise RepositoryPathError("path traversal refused") from exc
    if ".git" in relative.parts:
        raise RepositoryPathError("repository internals refused")
    return target


def status_relative_path(root: Path, value: str) -> str:
    """Validate a Git-known path lexically without dereferencing symlinks."""
    raw = str(value or "")
    candidate = PurePosixPath(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts or "\\" in raw:
        raise RepositoryPathError("path traversal refused")
    if ".git" in candidate.parts:
        raise RepositoryPathError("repository internals refused")
    # Keep this lexical: status must still report a dirty symlink whose target
    # is outside the worktree, while reads/writes use safe_path and refuse it.
    return candidate.as_posix()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def read_text_bytes(target: Path) -> tuple[bytes, str]:
    """Read bounded regular UTF-8 content without loading a huge file."""
    try:
        info = target.lstat()
    except OSError as exc:
        raise OSError("file not found") from exc
    if not stat.S_ISREG(info.st_mode):
        raise OSError("file is not a regular file")
    with target.open("rb") as handle:
        content = handle.read(MAX_FILE_READ_BYTES + 1)
    if len(content) > MAX_FILE_READ_BYTES:
        raise OSError("file is too large")
    return content, content.decode("utf-8")


def atomic_write(target: Path, content: bytes) -> None:
    """Replace a file in its parent directory while retaining its mode."""
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
    temporary: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=str(target.parent), prefix=f".{target.name}.", delete=False
        ) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def status_code(raw: str) -> str | None:
    pair = raw[:2]
    if pair == "??":
        return "?"
    for code in pair:
        if code in {"M", "A", "D"}:
            return code
    return None


def _decode_git_path(raw: bytes) -> str:
    """Decode a verbatim Git pathname using the host filesystem encoding."""
    return os.fsdecode(raw)


def _nul_paths(raw: bytes) -> list[str]:
    return [_decode_git_path(path) for path in raw.split(b"\0") if path]


def _porcelain_records(root: Path) -> tuple[bool, list[tuple[str, str]]]:
    """Return porcelain status codes and current paths without Git quoting.

    With ``status --porcelain=v1 -z``, rename/copy records carry the new path
    first and the old path as the following NUL-delimited field.  Only the new
    path is a current worktree path; consuming the old field prevents it from
    being mistaken for another status record.
    """
    proc = run_git_bytes(
        root, "status", "--porcelain=v1", "--untracked-files=all", "-z"
    )
    if proc.returncode:
        return False, []
    fields = proc.stdout.split(b"\0")
    records: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field or len(field) < 4 or field[2:3] != b" ":
            continue
        code = field[:2].decode("ascii", errors="replace")
        path = _decode_git_path(field[3:])
        if "R" in code or "C" in code:
            # The NUL form emits the old pathname after the current/new one.
            if index < len(fields):
                index += 1
        records.append((code, path))
    return True, records


def porcelain(root: Path) -> dict[str, str | None]:
    ok, records = _porcelain_records(root)
    if not ok:
        return {}
    statuses: dict[str, str | None] = {}
    for code, path in records:
        statuses[path] = status_code(code)
    return statuses


def repository_changes(root: Path) -> list[dict[str, str | None]]:
    ok, records = _porcelain_records(root)
    if not ok:
        raise RepositoryWorkspaceError("git status failed", status_code=409)
    changes: list[dict[str, str | None]] = []
    for code, path in records:
        index_status, worktree_status = code[0], code[1]
        try:
            relative = status_relative_path(root, path)
        except RepositoryPathError:
            continue
        changes.append({
            "path": relative,
            "status": status_code(code),
            "index_status": index_status,
            "worktree_status": worktree_status,
        })
    return changes


def repository_tree(root: Path, prefix: str) -> list[dict[str, Any]]:
    proc = run_git_bytes(root, "ls-tree", "-r", "--name-only", "-z", "HEAD")
    tracked = _nul_paths(proc.stdout) if proc.returncode == 0 else []
    statuses = porcelain(root)
    paths = set(tracked) | set(statuses)
    normalized_prefix = prefix.strip("/")
    children: dict[str, dict[str, Any]] = {}
    for raw in paths:
        try:
            safe_path(root, raw)
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


def repository_status(root: Path) -> dict[str, Any]:
    branch = run_git(root, "branch", "--show-current").stdout.strip() or "detached"
    changes = repository_changes(root)
    ahead = behind = 0
    counts = run_git(root, "rev-list", "--left-right", "--count", "@{upstream}...HEAD")
    if counts.returncode == 0:
        try:
            behind, ahead = (int(value) for value in counts.stdout.split())
        except ValueError:
            pass
    return {
        "branch": branch,
        "dirty": len(changes),
        "ahead": ahead,
        "behind": behind,
        "changes": changes,
    }


def _bounded_diff(text: str) -> tuple[str, bool]:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= MAX_DIFF_BYTES:
        return text, False
    clipped = encoded[:MAX_DIFF_BYTES].decode("utf-8", errors="ignore")
    return clipped, True


def _untracked_paths(root: Path, relative: Optional[str] = None) -> list[str]:
    args = ["ls-files", "--others", "--exclude-standard", "-z"]
    if relative:
        args.extend(["--", relative])
    proc = run_git_bytes(root, *args)
    if proc.returncode:
        raise RepositoryDiffError("git diff failed")
    result: list[str] = []
    for path in _nul_paths(proc.stdout):
        try:
            target = safe_path(root, path)
        except ValueError:
            continue
        if target.is_file():
            result.append(target.relative_to(root).as_posix())
    return result


def _untracked_diff(root: Path, paths: list[str]) -> str:
    chunks: list[str] = []
    for relative in paths:
        target = safe_path(root, relative)
        try:
            info = target.lstat()
        except OSError:
            continue
        if not stat.S_ISREG(info.st_mode):
            raise RepositoryDiffError(f"binary diff unsupported: {relative}")
        if info.st_size > MAX_UNTRACKED_FILE_BYTES:
            raise RepositoryDiffError(f"diff file too large: {relative}")
        raw = target.read_bytes()
        if b"\x00" in raw[:8192]:
            raise RepositoryDiffError(f"binary diff unsupported: {relative}")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RepositoryDiffError(f"binary diff unsupported: {relative}") from exc
        lines = text.splitlines(keepends=True)
        chunks.extend(
            difflib.unified_diff(
                [], lines, fromfile="/dev/null", tofile=f"b/{relative}", lineterm="\n"
            )
        )
    return "".join(chunks)


def repository_diff(
    root: Path,
    *,
    relative: Optional[str] = None,
    staged: bool = False,
) -> tuple[str, bool]:
    selected = None
    if relative:
        selected = safe_path(root, relative)
        if selected.exists() and selected.is_dir():
            raise RepositoryDiffError("path is a directory")
        relative = selected.relative_to(root).as_posix()
    args = ["diff", "--no-ext-diff", "--no-color"]
    if staged:
        args.insert(1, "--cached")
    if relative:
        args.extend(["--", relative])
    proc = run_git(root, *args)
    if proc.returncode not in (0, 1):
        raise RepositoryDiffError("git diff failed")
    text = proc.stdout
    if not staged:
        text += _untracked_diff(root, _untracked_paths(root, relative))
    if not text and selected is not None and not selected.exists():
        tracked = run_git(root, "ls-files", "--error-unmatch", "--", relative or "")
        if tracked.returncode:
            raise RepositoryDiffError("file not found")
    if "Binary files" in text:
        binary_path = relative
        if not binary_path:
            name_args = ["diff", "--name-only", "--no-ext-diff"]
            if staged:
                name_args.insert(1, "--cached")
            names = _nul_paths(run_git_bytes(root, *name_args, "-z").stdout)
            binary_path = names[0] if names else None
        suffix = f": {binary_path}" if binary_path else ""
        raise RepositoryDiffError(f"binary diff unsupported{suffix}")
    return _bounded_diff(text)


def stage_paths(root: Path, paths: list[str]) -> list[str]:
    proc = run_git(root, "add", "--", *paths)
    if proc.returncode:
        raise RepositoryWorkspaceError("git stage failed", status_code=409)
    return paths


def commit_changes(root: Path, message: str) -> dict[str, Any]:
    proc = run_git(root, "commit", "-m", message)
    if proc.returncode:
        raise RepositoryWorkspaceError("git commit failed", status_code=409)
    return {"committed": True, "summary": proc.stdout.strip()}


def list_branches(root: Path) -> list[str]:
    proc = run_git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    if proc.returncode:
        raise RepositoryWorkspaceError("git branch list failed", status_code=409)
    return [line for line in proc.stdout.splitlines() if line]


def checkout_branch(root: Path, branch: str) -> dict[str, Any]:
    if not branch or branch.startswith("-"):
        raise RepositoryWorkspaceError("branch invalid", status_code=400)
    if branch not in list_branches(root):
        raise RepositoryWorkspaceError("branch not found", status_code=404)
    proc = run_git(root, "switch", branch)
    if proc.returncode:
        raise RepositoryWorkspaceError("git checkout failed", status_code=409)
    return repository_status(root)
