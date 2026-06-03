"""`.hs` project-context loader for `agent_context` (HS-34-03)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .models import (
    DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
    DEFAULT_CONTEXT_MAX_BYTES,
    DEFAULT_CONTEXT_PER_FILE_MAX_BYTES,
    HS_CONTEXT_DIR,
    HS_CONTEXT_FILE_KEYS,
    HS_CONTEXT_FILES,
    HS_FLAT_CONTEXT_FILES,
    HS_IGNORE_FILE,
    _SECRET_CONTEXT_RE,
)


@dataclass(frozen=True)
class RepoRoot:
    root: Path
    anchor: str
    project_name: str


def detect_repo_root(start: Path) -> RepoRoot | None:
    """Walk upward and detect a repo/project root for agent hook state."""

    cur = start if start.is_dir() else start.parent
    try:
        cur = cur.resolve()
    except OSError:
        cur = cur.absolute()
    home = Path.home().resolve()

    while True:
        for marker, anchor in (
            (".hs", "holdspeak"),
            (".hs_context", "holdspeak-flat"),
            (".git", "git"),
            (".holdspeak", "holdspeak-legacy"),
        ):
            if (cur / marker).exists():
                return RepoRoot(root=cur, anchor=anchor, project_name=_derive_project_name(cur))
        if cur == home:
            return None
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def load_hs_project_context(
    project_root: Path,
    *,
    max_bytes: int = DEFAULT_CONTEXT_MAX_BYTES,
    per_file_max_bytes: int = DEFAULT_CONTEXT_PER_FILE_MAX_BYTES,
) -> dict[str, Any]:
    """Load repo-local HoldSpeak context using a small fixed convention."""

    root = project_root.expanduser()
    hs_dir = root / HS_CONTEXT_DIR
    payload: dict[str, Any] = {
        "root": str(root),
        "context_dir": str(hs_dir),
        "exists": hs_dir.is_dir() or any((root / name).is_file() for name in HS_FLAT_CONTEXT_FILES),
        "files": {},
        "ignore": [],
        "flat_files": {},
        "skipped": [],
        "warnings": [],
        "write_policy": {
            "canonical": ".hs/ files are editable from the web UI after user action.",
            "flat": ".hs_* files are read-only compatibility inputs; migrate edits into .hs/.",
            "automatic_writes": False,
        },
        "truncated": False,
    }
    if not payload["exists"]:
        return payload

    remaining = max(0, max_bytes)
    files: dict[str, dict[str, Any]] = {}
    flat_files: dict[str, dict[str, Any]] = {}

    for flat_name, canonical_name in HS_FLAT_CONTEXT_FILES.items():
        path = root / flat_name
        if not path.is_file():
            continue
        result = _read_context_entry(
            path,
            min(remaining, 16_000 if canonical_name == "ignore" else per_file_max_bytes),
            source="flat",
        )
        if result.get("skipped"):
            payload["skipped"].append(result)
            payload["warnings"].append(f"Skipped {flat_name}: {result.get('reason')}")
            continue
        content = str(result.get("content") or "")
        remaining = max(0, remaining - len(content.encode("utf-8")))
        flat_files[flat_name] = {
            "path": str(path),
            "canonical_name": canonical_name,
            "content": content,
            "truncated": bool(result.get("truncated")),
            "read_only": True,
        }
        if canonical_name == "ignore":
            payload["ignore"] = _parse_ignore_lines(content)
            if canonical_name not in files:
                files[canonical_name] = {
                    "path": str(path),
                    "content": content,
                    "truncated": bool(result.get("truncated")),
                    "source": "flat",
                    "read_only": True,
                }
        elif canonical_name not in files:
            files[canonical_name] = {
                "path": str(path),
                "content": content,
                "truncated": bool(result.get("truncated")),
                "source": "flat",
                "read_only": True,
            }
        if result.get("truncated"):
            payload["truncated"] = True

    for name in HS_CONTEXT_FILES:
        path = hs_dir / name
        if not path.is_file():
            continue
        # Avoid letting one large file starve later canonical files. The
        # global budget still caps total prompt material.
        result = _read_context_entry(path, min(remaining, per_file_max_bytes), source="directory")
        if result.get("skipped"):
            payload["skipped"].append(result)
            payload["warnings"].append(f"Skipped .hs/{name}: {result.get('reason')}")
            continue
        content = str(result.get("content") or "")
        remaining = max(0, remaining - len(content.encode("utf-8")))
        files[name] = {
            "path": str(path),
            "content": content,
            "truncated": bool(result.get("truncated")),
            "source": "directory",
            "read_only": False,
        }
        if result.get("truncated"):
            payload["truncated"] = True
    payload["files"] = files
    payload["flat_files"] = flat_files

    ignore_path = hs_dir / HS_IGNORE_FILE
    if ignore_path.is_file():
        result = _read_context_entry(ignore_path, min(remaining, 16_000), source="directory")
        if result.get("skipped"):
            payload["skipped"].append(result)
            payload["warnings"].append(f"Skipped .hs/{HS_IGNORE_FILE}: {result.get('reason')}")
        else:
            content = str(result.get("content") or "")
            payload["ignore"] = _parse_ignore_lines(content)
            files[HS_IGNORE_FILE] = {
                "path": str(ignore_path),
                "content": content,
                "truncated": bool(result.get("truncated")),
                "source": "directory",
                "read_only": False,
            }
        if result.get("truncated"):
            payload["truncated"] = True

    return payload


def compact_hs_project_context(context: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a template-friendly `.hs/` context mapping for `ProjectContext`."""

    if not context.get("exists"):
        return None
    compact: dict[str, Any] = {}
    files = context.get("files")
    if isinstance(files, dict):
        for filename, key in HS_CONTEXT_FILE_KEYS.items():
            entry = files.get(filename)
            if not isinstance(entry, dict):
                continue
            content = str(entry.get("content") or "").strip()
            if content:
                compact[key] = content
    ignore = context.get("ignore")
    if isinstance(ignore, list):
        compact["ignore"] = [str(item) for item in ignore if str(item).strip()]
    rendered = render_hs_context_for_prompt(context).strip()
    if rendered:
        compact["prompt_context"] = rendered
    compact["context_dir"] = str(context.get("context_dir") or "")
    compact["truncated"] = bool(context.get("truncated"))
    return compact


def render_hs_context_for_prompt(context: Mapping[str, Any]) -> str:
    """Render loaded `.hs/` context as compact prompt material."""

    if not context.get("exists"):
        return ""
    parts: list[str] = []
    files = context.get("files")
    if isinstance(files, dict):
        for name in HS_CONTEXT_FILES:
            entry = files.get(name)
            if not isinstance(entry, dict):
                continue
            content = str(entry.get("content") or "").strip()
            if not content:
                continue
            parts.append(f"## .hs/{name}\n{content}")
    ignore = context.get("ignore")
    if isinstance(ignore, list) and ignore:
        parts.append("## .hs/ignore\n" + "\n".join(f"- {item}" for item in ignore))
    return "\n\n".join(parts)


def _normalize_project_root(project_root: str | Path | None) -> str | None:
    if project_root is None:
        return None
    raw = str(project_root).strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    try:
        return str(path.resolve())
    except OSError:
        return str(path.absolute())


def _derive_project_name(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        name = _read_toml_name(pyproject, ("project", "name"))
        if name:
            return name
    package_json = root / "package.json"
    if package_json.is_file():
        try:
            raw = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = None
        if isinstance(raw, dict) and isinstance(raw.get("name"), str) and raw["name"].strip():
            return raw["name"].strip()
    return root.name


def _read_toml_name(path: Path, dotted: tuple[str, ...]) -> str | None:
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        return None
    try:
        with path.open("rb") as handle:
            data: Any = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    cursor: Any = data
    for key in dotted:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor.strip() if isinstance(cursor, str) and cursor.strip() else None


def _read_text_budget(path: Path, budget: int) -> tuple[str, bool]:
    if budget <= 0:
        return "", True
    try:
        raw = path.read_bytes()
    except OSError:
        return "", False
    truncated = len(raw) > budget
    if truncated:
        raw = raw[:budget]
    return raw.decode("utf-8", errors="replace"), truncated


def _read_context_entry(path: Path, budget: int, *, source: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": f"read_error:{exc.__class__.__name__}",
        }
    if len(raw) > DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES:
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": "too_large",
            "size_bytes": len(raw),
            "max_bytes": DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
        }
    if b"\x00" in raw:
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": "binary",
            "size_bytes": len(raw),
        }
    truncated = len(raw) > budget
    if truncated:
        raw = raw[: max(0, budget)]
    content = raw.decode("utf-8", errors="replace")
    if _SECRET_CONTEXT_RE.search(content):
        return {
            "path": str(path),
            "source": source,
            "skipped": True,
            "reason": "possible_secret",
            "size_bytes": len(raw),
        }
    return {
        "path": str(path),
        "source": source,
        "content": content,
        "truncated": truncated,
    }


def _parse_ignore_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
