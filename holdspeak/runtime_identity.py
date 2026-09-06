"""Loaded-runtime identity and the repair diagnoses (HS-200-02, contract C1).

A user can inspect a fresh Git checkout while an *older* process keeps serving
an *older* bundle over the same database. Nothing in the product used to say
so: ``/api/runtime/status`` reported a start time and a URL, and the only
build string anywhere was ``holdspeak.__version__`` — which does not move per
commit.

This module answers "what is actually loaded?" with facts captured **once, at
process start, in memory**:

- ``backend_version`` / ``backend_revision`` — the package version plus the
  revision this process loaded (a baked stamp if the package carries one, else
  the working tree's HEAD read once at start, else ``unknown``).
- ``process_start`` / ``pid`` — this process, not the checkout.
- ``frontend_build`` — the build id stamped into the bundle by the Vite build
  (``holdspeak/static/_built/build-id.json``), read at start.
- ``database_id`` — an opaque, stable identity for the database file. The raw
  path is carried separately and belongs to diagnostics only.
- ``schema_version_expected`` / ``schema_version_loaded`` — the constant this
  process was built against, and what the database actually held at start.
- ``config_revision`` — a digest of the active configuration file. A digest,
  never its content: no secret is reproducible from it.

C1's law is the reason for the capture-once rule: *a later Git checkout cannot
change the identity reported by an already running process*. Everything here is
read from disk exactly once and then frozen; the only values re-read later are
the ones a diagnosis **compares against** (the bundle stamp on disk now, the
database's schema version now).
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logging_config import get_logger

log = get_logger("runtime_identity")

UNKNOWN = "unknown"

#: The bundle stamp the Vite build writes next to the emitted assets.
BUILD_STAMP_NAME = "build-id.json"

#: A stamp a packaged build may bake beside the module tree.
_BACKEND_STAMP_PATH = Path(__file__).resolve().parent / "_build_stamp.json"

# ── Repair diagnoses (C1). The token is what the Desk shows; the detail is
# diagnostics-only. Tokens are caps mono by UX canon, never a sentence.
STALE_BUNDLE = "STALE BUNDLE"
TWO_RUNTIMES = "TWO RUNTIMES"
SCHEMA_AHEAD = "SCHEMA AHEAD"
SCHEMA_BEHIND = "SCHEMA BEHIND"

_DIAGNOSIS_IDS = {
    STALE_BUNDLE: "stale_bundle",
    TWO_RUNTIMES: "two_runtimes",
    SCHEMA_AHEAD: "schema_ahead",
    SCHEMA_BEHIND: "schema_behind",
}


def built_dir() -> Path:
    """Where the served bundle lives (the Vite ``outDir``)."""
    return Path(__file__).resolve().parent / "static" / "_built"


def read_bundle_build_id(directory: Optional[Path] = None) -> str:
    """The build id stamped into a bundle directory, or ``""`` when absent.

    Absent is a real answer, not an error: a checkout that has never run
    ``npm run build`` has no stamp, and that is itself a STALE BUNDLE finding.
    """
    import json

    stamp = (directory or built_dir()) / BUILD_STAMP_NAME
    try:
        data = json.loads(stamp.read_text(encoding="utf-8"))
    except Exception:
        return ""
    value = data.get("build_id") if isinstance(data, dict) else None
    return str(value).strip() if value else ""


def _digest(*parts: object, length: int = 16) -> str:
    joined = "|".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def database_identity(db_path: Path) -> str:
    """An opaque, stable identity for a database file.

    Derived from the resolved path and the file's device+inode, so the same
    file keeps its identity across restarts and a *replaced* file (a restore)
    honestly reads as a different database. Never reversible to the path.
    """
    resolved = Path(db_path).expanduser()
    try:
        resolved = resolved.resolve()
    except OSError:  # pragma: no cover - unresolvable path
        pass
    try:
        stat = resolved.stat()
    except OSError:
        return _digest("absent", resolved)
    return _digest(resolved, stat.st_dev, stat.st_ino)


def config_revision(config_path: Optional[Path] = None) -> str:
    """A digest of the active configuration file, or ``unknown``.

    A digest of the file's bytes: a changed setting changes the revision, and
    no value — least of all a token — can be read back out of it.
    """
    if config_path is None:
        try:
            from .config.core import _active_config_file

            config_path = _active_config_file()
        except Exception:  # pragma: no cover - config import failure
            return UNKNOWN
    try:
        raw = Path(config_path).expanduser().read_bytes()
    except OSError:
        return UNKNOWN
    return hashlib.sha256(raw).hexdigest()[:16]


def _baked_backend_revision() -> tuple[str, str]:
    """A revision baked into the package at build time, if one exists."""
    import json

    env = (os.environ.get("HOLDSPEAK_BACKEND_REVISION") or "").strip()
    if env:
        return env, "env"
    try:
        data = json.loads(_BACKEND_STAMP_PATH.read_text(encoding="utf-8"))
    except Exception:
        return "", ""
    revision = data.get("revision") if isinstance(data, dict) else None
    return (str(revision).strip(), "stamp") if revision else ("", "")


def _working_tree_revision() -> str:
    """HEAD of the checkout this module was loaded from, read once.

    Read at *capture* time only. Once captured it is frozen, which is precisely
    what lets an already running process keep reporting the revision it loaded
    after the tree moves on.
    """
    repo = Path(__file__).resolve().parent.parent
    if not (repo / ".git").exists():
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


@dataclass(frozen=True)
class RuntimeIdentity:
    """What this process actually loaded. Immutable once captured."""

    backend_version: str
    backend_revision: str
    backend_revision_source: str
    process_start: str
    pid: int
    frontend_build: str
    database_id: str
    database_path: str
    schema_version_expected: Optional[int]
    schema_version_loaded: Optional[int]
    config_revision: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def public_dict(self) -> dict[str, Any]:
        """The ordinary-surface view: no filesystem path, no pid.

        C1: "Detailed process and filesystem information stays in diagnostics."
        """
        payload = self.to_dict()
        payload.pop("database_path", None)
        payload.pop("pid", None)
        return payload


_IDENTITY: Optional[RuntimeIdentity] = None


def _default_db_path() -> Path:
    # Resolved through the module attribute, never bound at import: the tests
    # and the glass rigs monkeypatch ``db.core.DEFAULT_DB_PATH``.
    from .db import core as db_core

    return Path(db_core.DEFAULT_DB_PATH).expanduser()


def capture_runtime_identity(
    *,
    db_path: Optional[Path] = None,
    started_at: Optional[datetime] = None,
    force: bool = False,
) -> RuntimeIdentity:
    """Capture the loaded identity once and cache it for the process lifetime.

    Idempotent by design: a second call returns the first capture. ``force`` is
    the test seam (and the only way to re-capture), never a product path.
    """
    global _IDENTITY
    if _IDENTITY is not None and not force:
        return _IDENTITY

    from . import __version__
    from .db.core import read_schema_version
    from .db.schema import SCHEMA_VERSION

    path = Path(db_path).expanduser() if db_path is not None else _default_db_path()

    revision, source = _baked_backend_revision()
    if not revision:
        revision = _working_tree_revision()
        source = "git" if revision else ""
    if not revision:
        revision, source = UNKNOWN, UNKNOWN

    try:
        loaded_schema = read_schema_version(path)
    except Exception as exc:  # pragma: no cover - never block startup on a probe
        log.warning(f"runtime_identity: schema probe failed ({exc})")
        loaded_schema = None

    _IDENTITY = RuntimeIdentity(
        backend_version=str(__version__),
        backend_revision=revision,
        backend_revision_source=source,
        process_start=(started_at or datetime.now()).isoformat(),
        pid=os.getpid(),
        frontend_build=read_bundle_build_id(),
        database_id=database_identity(path),
        database_path=str(path),
        schema_version_expected=int(SCHEMA_VERSION),
        schema_version_loaded=loaded_schema,
        config_revision=config_revision(),
    )
    return _IDENTITY


def current_runtime_identity() -> RuntimeIdentity:
    """The captured identity, capturing lazily if a reader arrives first."""
    return capture_runtime_identity()


def reset_runtime_identity() -> None:
    """Drop the cached capture. Test seam only."""
    global _IDENTITY
    _IDENTITY = None


def _diagnosis(token: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"id": _DIAGNOSIS_IDS[token], "token": token, "detail": detail, **extra}


def diagnose(
    identity: Optional[RuntimeIdentity] = None,
    *,
    bundle_dir: Optional[Path] = None,
    db_path: Optional[Path] = None,
    ownership: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """The specific repair diagnoses for this running process.

    Each compares the *captured* identity against what is on disk **now**:

    - ``STALE BUNDLE`` — the bundle now served differs from the one this
      process started with, or no bundle stamp exists at all.
    - ``TWO RUNTIMES`` — this process does not own the database lock, so a
      second hub holds it (see :mod:`holdspeak.runtime_lock`).
    - ``SCHEMA AHEAD`` / ``SCHEMA BEHIND`` — the database's schema version
      against the version this process was built for.
    """
    identity = identity or current_runtime_identity()
    findings: list[dict[str, Any]] = []

    on_disk = read_bundle_build_id(bundle_dir)
    if not on_disk:
        findings.append(
            _diagnosis(
                STALE_BUNDLE,
                "No bundle stamp on disk. Build the web bundle: npm --prefix web run build.",
                loaded=identity.frontend_build,
                on_disk="",
            )
        )
    elif on_disk != identity.frontend_build:
        findings.append(
            _diagnosis(
                STALE_BUNDLE,
                "This process started with a different bundle than the one on disk. Restart the hub.",
                loaded=identity.frontend_build,
                on_disk=on_disk,
            )
        )

    # `held is False` on purpose, never falsiness: a process that never claimed
    # reports `held: None` — unknown, and an unknown is not a finding.
    if ownership is not None and ownership.get("held") is False:
        owner = ownership.get("owner") or {}
        findings.append(
            _diagnosis(
                TWO_RUNTIMES,
                "Another hub owns this database; scheduled work runs in that process only.",
                owner_pid=owner.get("pid"),
                owner_port=owner.get("port"),
                owner_started=owner.get("process_start"),
            )
        )

    expected = identity.schema_version_expected
    path = Path(db_path).expanduser() if db_path is not None else Path(identity.database_path)
    try:
        from .db.core import read_schema_version

        loaded = read_schema_version(path)
    except Exception:  # pragma: no cover - never fail a status read on a probe
        loaded = identity.schema_version_loaded
    if expected is not None and loaded is not None and loaded != expected:
        token = SCHEMA_AHEAD if loaded > expected else SCHEMA_BEHIND
        findings.append(
            _diagnosis(
                token,
                "The database schema and this build disagree. Restore a backup or run the current build.",
                loaded=loaded,
                expected=expected,
            )
        )

    return findings


def identity_report(
    *,
    detailed: bool,
    bundle_dir: Optional[Path] = None,
    db_path: Optional[Path] = None,
    ownership: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """The served payload. ``detailed`` is the diagnostics surface."""
    identity = current_runtime_identity()
    if ownership is None:
        from .runtime_lock import ownership_snapshot

        ownership = ownership_snapshot()
    findings = diagnose(
        identity, bundle_dir=bundle_dir, db_path=db_path, ownership=ownership
    )
    payload: dict[str, Any] = {
        "identity": identity.to_dict() if detailed else identity.public_dict(),
        "repair": [f["token"] for f in findings],
        "owns_database": bool(ownership.get("held")) if ownership else None,
    }
    if detailed:
        payload["diagnoses"] = findings
        payload["ownership"] = ownership
        payload["bundle_on_disk"] = read_bundle_build_id(bundle_dir)
    return payload
