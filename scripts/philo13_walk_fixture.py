"""Build the small repository input used by the Phase 13 B0 walk.

The graph rig owns the temporary ``HOME`` passed to this helper.  The helper
keeps all writes below that directory, copies the real Delivery Workbench
reader into the input repository, and gives the product a real git repository
and roadmap to read.  It does not seed HoldSpeak state or provide HTTP
responses.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

REPOSITORY_LABEL = "Atlas Desk"
PROJECT_SLUG = "atlas-desk"
STORY_ID = "ATLAS-1-01"
FIXTURE_DIR_NAME = "atlas-desk-repository"

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DW_SOURCE = _REPO_ROOT / ".githooks" / "dw"
_DW_PMO_SOURCE = _REPO_ROOT / ".githooks" / "dw_pmo"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _require_real_directory(path: Path, *, label: str) -> Path:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    if not path.exists() or not path.is_dir():
        raise ValueError(f"{label} must be an existing directory")
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"{label} must resolve to a directory")
    return resolved


def _assert_source_tree_is_real(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError(f"vendored source is a symlink: {path}")
    for child in path.rglob("*"):
        if child.is_symlink():
            raise RuntimeError(f"vendored source contains a symlink: {child}")


def _target(root: Path, relative: str) -> Path:
    candidate = root / Path(relative)
    if not _within(candidate, root):
        raise ValueError(f"fixture target escapes fixture root: {relative!r}")
    return candidate


def _write_text(root: Path, relative: str, text: str) -> None:
    target = _target(root, relative)
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"fixture target already exists: {relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _copy_file(root: Path, source: Path, relative: str) -> None:
    if source.is_symlink() or not source.is_file():
        raise RuntimeError(f"vendored file is not a regular file: {source}")
    target = _target(root, relative)
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"fixture target already exists: {relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _copy_tree(root: Path, source: Path, relative: str) -> None:
    if source.is_symlink() or not source.is_dir():
        raise RuntimeError(f"vendored directory is not a real directory: {source}")
    target = _target(root, relative)
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"fixture target already exists: {relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        target,
        symlinks=False,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def _run_git(root: Path, *args: str, capture: bool = False) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "git failed").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail[:300]}")
    return (completed.stdout or "").strip() if capture else ""


def _run_dw(root: Path, *args: str) -> str:
    completed = subprocess.run(
        [str(root / ".githooks" / "dw"), "--root", str(root), *args],
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "dw failed").strip()
        raise RuntimeError(f"fixture dw {' '.join(args)} failed: {detail[:300]}")
    return completed.stdout


def _roadmap_files() -> dict[str, str]:
    phase = f"pm/roadmap/{PROJECT_SLUG}/phase-1-atlas"
    return {
        f"pm/roadmap/{PROJECT_SLUG}/README.md": (
            "# Atlas Desk\n\n"
            "- **Story ID prefix:** ATLAS\n\n"
            "**Current phase:** [Phase 1](phase-1-atlas/current-phase-status.md)\n"
        ),
        f"{phase}/current-phase-status.md": (
            "# Phase 1 — Atlas repository\n\n"
            "| ID | Story | Status | Story file | Evidence |\n"
            "|---|---|---|---|---|\n"
            f"| {STORY_ID} | Repository input | ready | "
            "[story-01-repository-input.md](story-01-repository-input.md) | - |\n"
        ),
        f"{phase}/story-01-repository-input.md": (
            f"# {STORY_ID} - Repository input\n\n"
            "- **Status:** ready\n\n"
            "A small repository source is available to the Repository window.\n"
        ),
    }


def _validate_head(head: str) -> str:
    if not _SHA_RE.fullmatch(head):
        raise RuntimeError(f"fixture git HEAD is not a full commit SHA: {head!r}")
    return head


def create_repository_fixture(home: Path) -> dict[str, Any]:
    """Create one real Delivery Workbench repository below ``home``.

    ``home`` is the graph walk's isolated HOME.  The function refuses an
    existing fixture directory so a caller cannot accidentally reuse a stale
    repository.  The return value contains only JSON-compatible scalars:
    ``path``, ``label``, ``project_slug``, ``story_id`` and ``git_head``.
    """

    isolated_home = _require_real_directory(Path(home), label="graph-walk HOME")
    fixture = isolated_home / FIXTURE_DIR_NAME
    if not _within(fixture, isolated_home):
        raise ValueError("fixture path escapes graph-walk HOME")
    if fixture.exists() or fixture.is_symlink():
        raise FileExistsError(f"repository fixture already exists: {fixture}")

    _assert_source_tree_is_real(_DW_SOURCE)
    _assert_source_tree_is_real(_DW_PMO_SOURCE)
    fixture.mkdir()

    _copy_file(fixture, _DW_SOURCE, ".githooks/dw")
    _copy_tree(fixture, _DW_PMO_SOURCE, ".githooks/dw_pmo")
    _write_text(
        fixture,
        "atlas_repository.py",
        '"""Small source file for the Atlas Desk Repository window."""\n\n'
        'ATLAS_REPOSITORY_MESSAGE = "Repository window reads this fixture."\n',
    )
    for relative, contents in _roadmap_files().items():
        _write_text(fixture, relative, contents)

    _run_git(fixture, "init", "-q", "-b", "main")
    _run_git(fixture, "config", "user.name", "Atlas Fixture")
    _run_git(fixture, "config", "user.email", "atlas-fixture@example.invalid")
    _run_git(
        fixture,
        "add",
        "--",
        ".githooks/dw",
        ".githooks/dw_pmo",
        "atlas_repository.py",
        f"pm/roadmap/{PROJECT_SLUG}",
    )
    _run_git(fixture, "commit", "-q", "-m", "seed Atlas Desk repository fixture")

    # Let the copied, real DW reader reject malformed fixture inputs before
    # the product sees them.  These are pure reads after the git commit.
    _run_dw(fixture, "check", PROJECT_SLUG)
    _run_dw(fixture, "state", "--json")
    head = _validate_head(_run_git(fixture, "rev-parse", "HEAD", capture=True))

    return {
        "path": str(fixture),
        "label": REPOSITORY_LABEL,
        "project_slug": PROJECT_SLUG,
        "story_id": STORY_ID,
        "git_head": head,
    }


__all__ = [
    "FIXTURE_DIR_NAME",
    "PROJECT_SLUG",
    "REPOSITORY_LABEL",
    "STORY_ID",
    "create_repository_fixture",
]
