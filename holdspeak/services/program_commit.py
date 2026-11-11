"""The immutable change identity an owner's commit answer was shown."""
from __future__ import annotations
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping


def commit_binding(step: Mapping[str, Any]) -> dict[str, Any]:
    facts = step.get("facts") or {}
    hold = facts.get("held_commit") or {}
    worktree = Path(str(step.get("worktree") or ""))
    revision = None
    if step.get("worktree"):
        def git(*args: str) -> bytes:
            return subprocess.run(["git", "-C", str(worktree), *args], check=True, capture_output=True, timeout=10).stdout
        try:
            digest = hashlib.sha256(b"program-commit/v1\0")
            def add(data: bytes) -> None:
                digest.update(len(data).to_bytes(8, "big")); digest.update(data)
            add(git("rev-parse", "HEAD"))
            add(git("diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD"))
            for raw in sorted(git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")):
                if not raw:
                    continue
                path = worktree / os.fsdecode(raw)
                add(json.dumps(os.fsdecode(raw)).encode())
                mode = path.lstat().st_mode
                add(f"{stat.S_IFMT(mode)}:{mode & 0o111}".encode())
                add(os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes())
            revision = digest.hexdigest()
        except (OSError, subprocess.SubprocessError):
            pass  # An unproved worktree never receives an Allow.
    return {"hold_id": hold.get("proposal_id"), "change_revision": revision}
