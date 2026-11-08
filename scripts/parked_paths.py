"""A path a park moved: its twin under a ``_parked/`` directory.

2026-11-08 (the test-speed subtraction): a citation, ledger or baseline that
names a file is not wrong when the file was PARKED, only when it is gone. The
guards that check a cited path resolve a missing one to its parked twin (the
same file name under a ``_parked/`` directory beside it or below one of its
parents), so a park never turns them red and a typo or a deletion still does.
"""
from __future__ import annotations

from pathlib import Path


def parked_twin(root: Path, relative: str) -> str | None:
    """The repository-relative path of ``relative``'s parked twin, or None."""
    path = Path(relative)
    if not path.name or path.is_absolute():
        return None
    for parent in path.parents:
        base = root / parent
        if not base.is_dir():
            continue
        for twin in sorted(base.rglob(path.name)):
            rel = twin.relative_to(root)
            if "_parked" in rel.parts and twin.is_file():
                return rel.as_posix()
        if parent == Path("."):
            break
        if len(parent.parts) <= 1:
            break
    return None


def resolve(root: Path, relative: str) -> str:
    """``relative`` when it is in the tree, else its parked twin when there
    is one, else ``relative`` (still missing)."""
    if (root / relative).exists():
        return relative
    return parked_twin(root, relative) or relative
