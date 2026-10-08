"""A Project knows its repository (PHILO-15 16, bounce B38).

The Door's GitHub row names a repository (``owner/name``). At create time the
owner's press REGISTERS it for the Project (``project.repository.register``,
an owner-only admitted kernel operation, one receipt). Nothing is cloned then.
The first Hand to agent of an item in that Project clones it (``gh repo clone``,
egress to github.com) into the HoldSpeak clone root, as its own admitted kernel
operation (``project.repository.clone``, one receipt), registers the clone as a
Delivery Source, and the launch goes on in a new worktree beside it.

The registrations live in ``~/.holdspeak/project_repositories.json``
(``{schema, projects: {project_id: {repository, registered_at, source_id?,
cloned_at?}}}``); the clones in ``~/.holdspeak/repositories/<owner>/<name>/<name>``
(the worktrees are siblings of the clone, so each repository has its own
folder). Paths stay on the hub: a state read gives the face words, never a path.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..timestamps import utc_now
from .errors import ServiceError

STORE_SCHEMA = 1
#: The host a clone reads from (the confirm line's egress chip).
CLONE_HOST = "github.com"
CLONE_TIMEOUT_SECONDS = 600

_REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9_.-]{1,100}$")
_GITHUB_PREFIXES = ("https://github.com/", "http://github.com/", "git@github.com:", "github.com/")

#: ``runner(argv, env) -> CompletedProcess``: the clone's process edge (a test
#: passes a fake ``gh``).
CloneRunner = Callable[[list[str], Mapping[str, str]], Any]


def default_store_path() -> Path:
    return Path.home() / ".holdspeak" / "project_repositories.json"


def default_clone_root() -> Path:
    return Path.home() / ".holdspeak" / "repositories"


def normalize_repository(value: Any) -> str:
    """``owner/name`` from what the Door holds (also a GitHub URL); refused by name."""
    text = str(value or "").strip()
    for prefix in _GITHUB_PREFIXES:
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
            break
    text = text.strip("/")
    if text.endswith(".git"):
        text = text[: -len(".git")]
    if not _REPOSITORY.match(text) or any(part in {".", ".."} for part in text.split("/")):
        raise ServiceError("repository_invalid", "Name the repository as owner/name.", context={"status": 400})
    return text


def clone_url(repository: str) -> str:
    """The one URL a clone reads: https://github.com/<owner>/<name>."""
    return f"https://{CLONE_HOST}/{repository}"


def _origin_of(path: Path) -> str:
    """The clone's origin, credential-free and without ``.git`` (lower case),
    read from its ``.git/config`` (a file read, no process)."""
    from ..delivery.registry import normalize_git_url

    try:
        text = (path / ".git" / "config").read_text(encoding="utf-8")
    except OSError:
        return ""
    section, url = "", ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            section = stripped
        elif section == '[remote "origin"]' and stripped.startswith("url") and "=" in stripped:
            url = stripped.split("=", 1)[1].strip()
            break
    url = normalize_git_url(url) if url else ""
    url = url[:-len(".git")] if url.endswith(".git") else url
    if url and "://" not in url:
        url = "https://" + url
    return url.lower()


def _gh_clone(argv: list[str], env: Mapping[str, str]) -> Any:
    """The real clone: ``gh repo clone`` (gh's own git credential, no prompt)."""
    return subprocess.run(
        argv, capture_output=True, text=True, errors="replace",
        timeout=CLONE_TIMEOUT_SECONDS, env=dict(env), stdin=subprocess.DEVNULL,
    )


class StoreNotRead(ServiceError):
    """``repository_store_unreadable``: the registrations file exists and cannot be read."""

    def __init__(self) -> None:
        super().__init__(
            "repository_store_unreadable",
            "The Project repository registrations cannot be read; nothing was changed.",
            context={"status": 409},
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectRepositories:
    """The registrations file and the clone root. Paths resolve at call time,
    so an isolated HOME (a test, a rehearsal) is honoured."""

    def __init__(
        self,
        *,
        store_path: Optional[Path] = None,
        clone_root: Optional[Path] = None,
        runner: Optional[CloneRunner] = None,
    ) -> None:
        self._store_path = Path(store_path) if store_path else None
        self._clone_root = Path(clone_root) if clone_root else None
        #: None: the module's ``_gh_clone``, read at call time (a test patches it).
        self._runner = runner

    @property
    def store_path(self) -> Path:
        return self._store_path or default_store_path()

    @property
    def clone_root(self) -> Path:
        return self._clone_root or default_clone_root()

    # ── the registrations ───────────────────────────────────────────

    def _read(self) -> dict[str, Any]:
        """The registrations. An absent file is empty; a file that cannot be
        read (an OS error, broken JSON, another schema) is NOT READ: it
        refuses by name, so nothing reads it as "no registration" and no
        registration writes over it (Astra r1 on #1000, finding 2)."""
        path = self.store_path
        if not path.exists():
            return {"schema": STORE_SCHEMA, "projects": {}}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise StoreNotRead() from exc
        if not isinstance(raw, dict) or raw.get("schema") != STORE_SCHEMA or not isinstance(raw.get("projects"), dict):
            raise StoreNotRead()
        return raw

    def get(self, project_id: Optional[str]) -> Optional[dict[str, Any]]:
        if not project_id:
            return None
        record = self._read()["projects"].get(str(project_id))
        if not isinstance(record, dict) or not record.get("repository"):
            return None
        return dict(record)

    def put(self, project_id: str, record: Mapping[str, Any]) -> dict[str, Any]:
        doc = self._read()
        doc["projects"][str(project_id)] = dict(record)
        path = self.store_path
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)
        return dict(record)

    # ── the clone ───────────────────────────────────────────────────

    def clone_path(self, repository: str) -> Path:
        owner, name = repository.split("/", 1)
        return self.clone_root / owner / name / name

    def is_cloned(self, repository: str) -> bool:
        return (self.clone_path(repository) / ".git").exists()

    def clone(self, repository: str) -> Path:
        """Clone ``repository`` into its folder (egress to github.com). A folder
        that is already a clone is kept as it is."""
        target = self.clone_path(repository)
        if (target / ".git").exists():
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        # No prompt can hang the hub; gh gives git its own credential.
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GH_PROMPT_DISABLED"] = "1"
        # The clone goes to the host the face names (GITHUB.COM), never to a
        # GH_HOST the environment chose: the full URL and the host, both bound
        # (Astra r1 on #1000, finding 1).
        env["GH_HOST"] = CLONE_HOST
        argv = ["gh", "repo", "clone", clone_url(repository), str(target), "--", "--quiet"]
        try:
            proc = (self._runner or _gh_clone)(argv, env)
        except FileNotFoundError as exc:
            raise ServiceError("gh_not_installed", "The GitHub CLI (gh) is not installed.",
                               context={"status": 409}) from exc
        except subprocess.TimeoutExpired as exc:
            raise ServiceError("clone_timed_out", f"The clone of {repository} did not end in time.",
                               context={"status": 409}) from exc
        if getattr(proc, "returncode", 1) != 0 or not (target / ".git").exists():
            raise ServiceError("clone_failed", f"The clone of {repository} failed.", context={"status": 409})
        origin = _origin_of(target)
        if origin != clone_url(repository).lower():
            # The clone is not the disclosed one: it is parked beside, never used.
            parked = target.with_name(f"{target.name}.not-github-{int(utc_now().timestamp())}")
            os.replace(target, parked)
            raise ServiceError("clone_host_mismatch",
                               f"The clone of {repository} did not come from {CLONE_HOST}.",
                               context={"status": 409})
        return target


def home_label(path: str) -> str:
    """A path as the face shows it: the hub's home folder is ``~``."""
    for home in dict.fromkeys((str(Path.home()), str(Path.home().resolve()))):
        if path == home or path.startswith(home + "/"):
            return "~" + path[len(home):]
    return path


def watched_repositories(db: Any, project_id: Optional[str]) -> list[str]:
    """The GitHub repositories the Project's Room watches (the Door's watches)."""
    if not project_id:
        return []
    found: list[str] = []
    with db._connection() as conn:
        for row in conn.execute(
            "SELECT query_json FROM connector_watches WHERE project_id=? AND connector_id IN ('gh','github')",
            (project_id,),
        ):
            try:
                repo = (json.loads(row[0] or "{}") or {}).get("repository")
            except ValueError:
                repo = None
            if repo and str(repo) not in found:
                found.append(str(repo))
    return found


def registered_source(record: Optional[Mapping[str, Any]], registry: Any) -> Any:
    """The Delivery Source the registration's clone was registered as, when it still is."""
    source_id = str((record or {}).get("source_id") or "")
    if not source_id:
        return None
    source = registry.get(source_id)
    return source if source is not None and getattr(source, "primary_path", None) else None


def repository_state(
    db: Any, project_id: str, repositories: ProjectRepositories, registry: Any = None,
) -> dict[str, Any]:
    """What the face shows: the registered repository, CLONED or not, and the
    watched repositories a Project with no registration could register."""
    try:
        record = repositories.get(project_id)
    except StoreNotRead:
        # NOT READ, never "none": the face says so and offers Retry.
        return {"project_id": project_id, "repository": None, "registered": False, "cloned": False,
                "registered_at": None, "cloned_at": None, "folder": None,
                "watched": watched_repositories(db, project_id), "host": CLONE_HOST, "store": "not_read"}
    repository = str(record["repository"]) if record else None
    source = registered_source(record, registry) if (record and registry is not None) else None
    cloned = bool(record) and (repositories.is_cloned(repository or "") or source is not None)
    # Where the clone lives (Astra r2 on PR 1000): the owner finds the folder
    # after a refused launch. The hub's home reads as `~`.
    folder = None
    if cloned:
        folder = home_label(str(source.primary_path) if source is not None
                            else str(repositories.clone_path(repository or "")))
    return {
        "project_id": project_id,
        "repository": repository,
        "registered": record is not None,
        "cloned": cloned,
        "registered_at": (record or {}).get("registered_at"),
        "cloned_at": (record or {}).get("cloned_at"),
        "folder": folder,
        "watched": watched_repositories(db, project_id),
        "host": CLONE_HOST,
        "store": "read",
    }


def register(db: Any, repositories: ProjectRepositories, project_id: str, repository: Any) -> dict[str, Any]:
    """Register ``repository`` for the Project (the kernel operation's write)."""
    name = normalize_repository(repository)
    with db._connection() as conn:
        row = conn.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
    if row is None:
        raise ServiceError("project_unknown", f"No Project {project_id}.", context={"status": 404})
    prior = repositories.get(project_id)
    record: dict[str, Any] = {"repository": name, "registered_at": _now()}
    if prior and prior.get("repository") == name:
        # The same repository again: its clone (and when it was made) stays known.
        record = {**prior, "repository": name}
    repositories.put(project_id, record)
    return record


__all__ = [
    "CLONE_HOST",
    "ProjectRepositories",
    "StoreNotRead",
    "clone_url",
    "default_clone_root",
    "default_store_path",
    "normalize_repository",
    "register",
    "registered_source",
    "repository_state",
    "watched_repositories",
]
