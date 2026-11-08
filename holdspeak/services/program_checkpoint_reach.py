"""HS-S35 (earlier D04): a checkpoint's recoverability, seen now, beside
its stored ref (2026-11-08).

A checkpoint row keeps the ref its pin wrote (``refs/holdspeak/checkpoints/
<step>/<n>``) and the commit it named (``ref_commit``). That record is
history: it is never rewritten. Whether the ref still names that commit
NOW is a separate fact, read on each Program read:

- ``reachable``: the ref names the stored commit;
- ``moved``: the ref names another commit (the stored commit is not what
  a Start from here would read);
- ``not_found``: the ref is gone (a prune, a removed repository);
- ``not_read``: git could not answer (no repository, a timeout).

A stored ref is never perpetual availability, and a later pin is a new
row with its own ref, never this one. The checkpoint refs are hidden refs
the runner writes into the Program's own repository with ``update-ref``
(``program_runner.ProgramRunner.pin_checkpoint``); they are never pushed,
so the read asks that repository, not origin. One bounded
``git for-each-ref`` answers every row of a Program; a Program with no
pinned row runs no git at all.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("program_checkpoint_reach")

REACH_TIMEOUT_SECONDS = 5
REACHABLE, MOVED, NOT_FOUND, NOT_READ = "reachable", "moved", "not_found", "not_read"

Run = Callable[..., Any]


def _words(state: str, commit: str) -> str:
    if state == REACHABLE:
        return f"checkpoint {commit} · reachable"
    if state == MOVED:
        return "stored, the ref now names another commit"
    if state == NOT_FOUND:
        return "stored, not found in the repository"
    return "stored, not read"


def live_refs(repo_root: Optional[str], run: Run) -> Optional[dict[str, str]]:
    """Every checkpoint ref the repository holds now, ``{ref: commit}``;
    ``None`` when git could not answer."""
    from .program_runner import CHECKPOINT_REFS

    root = str(repo_root or "")
    if not root or not Path(root).is_dir():
        return None
    try:
        proc = run(["git", "-C", root, "for-each-ref", "--format=%(refname) %(objectname)", f"{CHECKPOINT_REFS}/"],
                   cwd=root, timeout=REACH_TIMEOUT_SECONDS)
    except Exception as exc:  # no git, a timeout: the fact is "not read"
        log.debug(f"checkpoint refs not read: {exc}")
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    refs: dict[str, str] = {}
    for line in str(getattr(proc, "stdout", "") or "").splitlines():
        name, _, commit = line.strip().partition(" ")
        if name and commit:
            refs[name] = commit
    return refs


def project(rows: list[dict[str, Any]], repo_root: Optional[str], run: Run) -> list[dict[str, Any]]:
    """Each pinned row with ``reach`` and ``reach_words`` beside its stored
    ``ref`` and ``ref_commit`` (both left as stored). Rows with no ref are
    returned as they are."""
    if not any(row.get("ref") for row in rows):
        return rows
    refs = live_refs(repo_root, run)
    out = []
    for row in rows:
        ref, commit = str(row.get("ref") or ""), str(row.get("ref_commit") or "")
        if not ref:
            out.append(row)
            continue
        if refs is None:
            state = NOT_READ
        elif ref not in refs:
            state = NOT_FOUND
        elif commit and refs[ref] != commit:
            state = MOVED
        else:
            state = REACHABLE
        out.append({**row, "reach": state, "reach_words": _words(state, commit or (refs or {}).get(ref, ""))})
    return out


__all__ = ["MOVED", "NOT_FOUND", "NOT_READ", "REACHABLE", "live_refs", "project"]
