"""Git plumbing shared by the gate engine and the contract generator."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .model import DwError
from .paths import read_text, rel, roadmap_dir

_STATUS_LINE_RE = re.compile(r"^- \*\*Status:\*\*\s*(.+)$")


def run_git(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None


def head_sha(root: Path) -> str | None:
    out = run_git(root, "rev-parse", "--verify", "HEAD")
    return out.strip() if out else None


def current_branch(root: Path) -> str:
    out = run_git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if out and out.strip():
        return out.strip()
    return "detached"


def write_tree(root: Path) -> str | None:
    out = run_git(root, "write-tree")
    return out.strip() if out else None


def index_blob(root: Path, path: str) -> str | None:
    return run_git(root, "show", f":0:{path}")


def head_blob(root: Path, path: str) -> str | None:
    return run_git(root, "show", f"HEAD:{path}")


def status_of(content: str | None) -> str | None:
    if content is None:
        return None
    for line in content.splitlines():
        m = _STATUS_LINE_RE.match(line)
        if m:
            return m.group(1).strip().lower()
    return None


def staged_entries(root: Path) -> list[tuple[str, str, str | None]]:
    """Return (status, path, old_path) tuples from the staged diff.

    Renames yield ('R', new_path, old_path). NUL-separated parsing keeps
    paths with spaces intact.
    """
    out = run_git(root, "diff", "--cached", "--name-status", "-z", "-M")
    if out is None:
        return []
    tokens = out.split("\0")
    entries: list[tuple[str, str, str | None]] = []
    i = 0
    while i < len(tokens):
        status = tokens[i]
        if not status:
            i += 1
            continue
        kind = status[0]
        if kind in {"R", "C"}:
            old_path = tokens[i + 1] if i + 1 < len(tokens) else ""
            new_path = tokens[i + 2] if i + 2 < len(tokens) else ""
            if new_path:
                entries.append((kind, new_path, old_path))
            i += 3
        else:
            path = tokens[i + 1] if i + 1 < len(tokens) else ""
            if path:
                entries.append((kind, path, None))
            i += 2
    return entries


def in_rewrite_state(root: Path) -> bool:
    git_dir = (run_git(root, "rev-parse", "--git-dir") or "").strip()
    if not git_dir:
        return False
    gd = Path(git_dir)
    if not gd.is_absolute():
        gd = root / gd
    return (
        (gd / "rebase-merge").is_dir()
        or (gd / "rebase-apply").is_dir()
        or (gd / "CHERRY_PICK_HEAD").is_file()
        or (gd / "REVERT_HEAD").is_file()
    )


def roadmap_prefix(root: Path) -> str | None:
    try:
        rd = roadmap_dir(root)
    except DwError:
        return None
    prefix = rel(rd, root).replace(os.sep, "/")
    return prefix.rstrip("/") + "/"


def config_value(root: Path, key: str) -> str | None:
    """Parse a simple KEY=value assignment from .githooks/pre-commit.config.

    Only plain (optionally quoted) assignments are recognized; computed
    bash still reaches the gate through the environment via the shim.
    The last assignment wins, matching bash sourcing.
    """
    cfg = root / ".githooks" / "pre-commit.config"
    if not cfg.is_file():
        return None
    pattern = re.compile(r"^\s*(?:export\s+)?" + re.escape(key) + r"=([\"']?)(.*?)\1\s*$")
    value: str | None = None
    try:
        for line in read_text(cfg).splitlines():
            m = pattern.match(line)
            if m:
                value = m.group(2)
    except OSError:
        return None
    return value


def enabled_flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "yes", "true", "on"}
