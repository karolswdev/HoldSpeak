"""The Delivery Source + Worktree registry (HS-94-02).

PLATFORM-CONTRACT §3: all wire IDs are opaque; a source's identity
derives from a repository fingerprint computed over credential-free
canonical git metadata (normalized origin URL with user info and
tokens removed, plus the first-commit sha where present), and a
worktree resolves through ``git rev-parse --git-common-dir`` — never
by assuming ``.git`` is a directory.

The registry persists at ``~/.holdspeak/delivery_sources.json``
(``registry_schema: 1``). Filesystem paths live in this file and in
memory ONLY — ``to_wire()`` is the single projection clients ever
see, and it carries labels, opaque IDs, and display branches (§12,
§13). On first run the v1 project map
(``~/.holdspeak/delivery_workbench.json``) imports non-destructively:
each mapped path becomes a source + worktree; the v1 file is never
rewritten (§14 rule 7).

ID collision rules the shapes guarantee:

- several worktrees of one clone share a ``source_id`` (same git
  common dir) but get distinct ``worktree_id``s (the id hashes the
  worktree's resolved path);
- two clones of the same upstream (same fingerprint) get distinct
  ``source_id``s (the id hashes the clone's common-dir key);
- the same fingerprint on another node cannot collide either: every
  registry carries a random per-registry ``instance`` salt, and the
  nullable ``node_id`` field is reserved for the Phase-94 node link.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlsplit

REGISTRY_SCHEMA = 1
DEFAULT_REGISTRY_PATH = Path.home() / ".holdspeak" / "delivery_sources.json"
GIT_TIMEOUT_SECONDS = 10

GitRunner = Callable[..., "subprocess.CompletedProcess[str]"]

_SCP_LIKE = re.compile(r"^(?:(?P<user>[^@/]+)@)?(?P<host>[^:/]+):(?P<path>(?!//).+)$")


class RegistryError(ValueError):
    """A typed registration refusal — the message is client-safe
    (classified, never echoing a filesystem path)."""


def _default_git_runner(argv: list[str], cwd: Optional[str] = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=GIT_TIMEOUT_SECONDS,
    )


def normalize_git_url(url: str) -> str:
    """Credential-free canonical form of a git remote URL (§3.1):
    user info and tokens stripped, host lowercased, trailing ``/``
    and ``.git`` dropped. scp-like ``user@host:path`` becomes
    ``ssh://host/path``."""
    text = (url or "").strip()
    if not text:
        return ""
    if "://" in text:
        parts = urlsplit(text)
        host = (parts.hostname or "").lower()
        port = f":{parts.port}" if parts.port else ""
        norm = f"{parts.scheme.lower()}://{host}{port}{parts.path}"
    else:
        scp = _SCP_LIKE.match(text)
        if scp:
            norm = f"ssh://{scp.group('host').lower()}/{scp.group('path')}"
        else:
            norm = text
    norm = norm.rstrip("/")
    if norm.endswith(".git"):
        norm = norm[:-4]
    return norm


def _short_hash(*parts: str) -> str:
    joined = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()[:16]


@dataclass
class WorktreeRecord:
    worktree_id: str
    path: str  # server-side only; never in to_wire()
    branch: str  # display only, captured at registration

    def to_wire(self) -> dict[str, Any]:
        return {"worktree_id": self.worktree_id, "branch": self.branch}

    def to_stored(self) -> dict[str, Any]:
        return {
            "worktree_id": self.worktree_id,
            "path": self.path,
            "branch": self.branch,
        }


@dataclass
class SourceRecord:
    source_id: str
    label: str
    fingerprint: str
    clone_key: str  # server-side only: hash of the resolved common dir
    node_id: Optional[str] = None  # reserved for the node link (HS-94-03)
    worktrees: list[WorktreeRecord] = field(default_factory=list)

    @property
    def primary_path(self) -> Optional[str]:
        return self.worktrees[0].path if self.worktrees else None

    def to_wire(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "node_id": self.node_id,
            "label": self.label,
            "fingerprint": self.fingerprint,
            "worktrees": [wt.to_wire() for wt in self.worktrees],
        }

    def to_stored(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "node_id": self.node_id,
            "label": self.label,
            "fingerprint": self.fingerprint,
            "clone_key": self.clone_key,
            "worktrees": [wt.to_stored() for wt in self.worktrees],
        }


class DeliveryRegistry:
    """Versioned Delivery Source registry with a one-time,
    non-destructive v1 project-map import."""

    def __init__(
        self,
        path: Optional[Path] = None,
        *,
        map_path: Optional[Path] = None,
        git_runner: Optional[GitRunner] = None,
    ) -> None:
        self._path = Path(path) if path else DEFAULT_REGISTRY_PATH
        self._map_path = map_path
        self._run = git_runner or _default_git_runner
        self._instance = uuid.uuid4().hex
        self._sources: list[SourceRecord] = []
        self._load_or_import()

    # ── persistence ──────────────────────────────────────────────

    def _load_or_import(self) -> None:
        raw: Any = None
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            raw = None
        if isinstance(raw, dict) and raw.get("registry_schema") == REGISTRY_SCHEMA:
            self._instance = str(raw.get("instance") or self._instance)
            self._sources = [
                self._source_from_stored(entry)
                for entry in raw.get("sources") or []
                if isinstance(entry, dict)
            ]
            return
        # Fresh registry: import the v1 map without touching it.
        self._import_v1_map()
        self._save()

    @staticmethod
    def _source_from_stored(entry: dict[str, Any]) -> SourceRecord:
        return SourceRecord(
            source_id=str(entry.get("source_id") or ""),
            label=str(entry.get("label") or ""),
            fingerprint=str(entry.get("fingerprint") or ""),
            clone_key=str(entry.get("clone_key") or ""),
            node_id=entry.get("node_id"),
            worktrees=[
                WorktreeRecord(
                    worktree_id=str(wt.get("worktree_id") or ""),
                    path=str(wt.get("path") or ""),
                    branch=str(wt.get("branch") or ""),
                )
                for wt in entry.get("worktrees") or []
                if isinstance(wt, dict)
            ],
        )

    def _import_v1_map(self) -> None:
        from ..missioncontrol_bridge import load_project_map

        project_map = load_project_map(self._map_path)
        for name, repo_path in sorted(project_map.get("projects", {}).items()):
            try:
                self.register(repo_path, label=name, save=False)
            except RegistryError:
                continue  # a dead map row is not an import failure

    def _save(self) -> None:
        doc = {
            "registry_schema": REGISTRY_SCHEMA,
            "instance": self._instance,
            "sources": [source.to_stored() for source in self._sources],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    # ── git resolution ───────────────────────────────────────────

    def _git(self, worktree: Path, *args: str) -> Optional[str]:
        try:
            proc = self._run(["git", "-C", str(worktree), *args], str(worktree))
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0:
            return None
        return (proc.stdout or "").strip() or None

    def _resolve_common_dir(self, worktree: Path) -> Optional[Path]:
        out = self._git(worktree, "rev-parse", "--git-common-dir")
        if not out:
            return None
        common = Path(out)
        if not common.is_absolute():
            common = worktree / common
        return common.resolve()

    def _fingerprint(self, worktree: Path, clone_key: str) -> str:
        origin = normalize_git_url(
            self._git(worktree, "config", "--get", "remote.origin.url") or ""
        )
        first_line = self._git(
            worktree, "rev-list", "--max-parents=0", "--max-count=1", "HEAD"
        )
        first_sha = (first_line or "").splitlines()[0] if first_line else ""
        if origin or first_sha:
            canonical = f"origin={origin}\nroot={first_sha}"
        else:
            # No remote and no commits: a local-only identity. The clone
            # key is already a hash, so no path enters the fingerprint.
            canonical = f"commondir={clone_key}"
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    # ── the public surface ───────────────────────────────────────

    def sources(self) -> list[SourceRecord]:
        return list(self._sources)

    def get(self, source_id: str) -> Optional[SourceRecord]:
        for source in self._sources:
            if source.source_id == source_id:
                return source
        return None

    def register(
        self, path: str, *, label: Optional[str] = None, save: bool = True
    ) -> tuple[SourceRecord, WorktreeRecord]:
        """Register a worktree path (server-resolved, §10 POST flow).
        Idempotent: an already-registered worktree returns its
        existing records; a new worktree of a known clone joins that
        source. Refusals are typed and path-free."""
        candidate = Path(str(path or "")).expanduser()
        if not candidate.is_dir():
            raise RegistryError("path is not a directory")
        common = self._resolve_common_dir(candidate)
        if common is None:
            raise RegistryError("path is not a git worktree")
        clone_key = hashlib.sha256(str(common).encode("utf-8")).hexdigest()
        resolved = str(candidate.resolve())
        branch = self._git(candidate, "rev-parse", "--abbrev-ref", "HEAD") or ""

        source = next(
            (s for s in self._sources if s.clone_key == clone_key), None
        )
        if source is None:
            fingerprint = self._fingerprint(candidate, clone_key)
            source = SourceRecord(
                source_id="src_"
                + _short_hash(self._instance, fingerprint, clone_key),
                label=label or candidate.name,
                fingerprint=fingerprint,
                clone_key=clone_key,
            )
            self._sources.append(source)
        elif label:
            source.label = label

        worktree = next(
            (wt for wt in source.worktrees if wt.path == resolved), None
        )
        if worktree is None:
            worktree = WorktreeRecord(
                worktree_id="wt_" + _short_hash(source.source_id, resolved),
                path=resolved,
                branch=branch,
            )
            source.worktrees.append(worktree)
        else:
            worktree.branch = branch or worktree.branch
        if save:
            self._save()
        return source, worktree

    def to_wire(self) -> dict[str, Any]:
        """The registry view a client may see: labels + opaque IDs,
        no filesystem paths (§13)."""
        return {
            "registry_schema": REGISTRY_SCHEMA,
            "sources": [source.to_wire() for source in self._sources],
        }
