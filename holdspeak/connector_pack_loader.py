"""Discovery + loader for connector packs.

HS-13-04. Phase 11 / 13's first-party packs live under
`holdspeak.connector_packs.*`; this module adds local-user
packs dropped into `~/.holdspeak/connector_packs/`. The loader
imports each `.py` file as a Python module, requires it to
export `MANIFEST: ConnectorManifest`, runs `validate_manifest`
on the payload (already done at pack-import time, but re-checked
here so a malformed pack doesn't crash discovery), and merges
the result into the runtime registry alongside first-party
packs.

The `~/.holdspeak/connector_packs/` directory is the trust
boundary — code dropped there runs in-process with the user's
own permissions. Sandboxing is *not* a goal here: a pack file
under the user's home dir is by definition code the user has
chosen to trust. The loader's job is honest discovery, not
isolation:

  - log every pack it discovers and its validation state,
  - surface `validate_manifest` errors in a structured form
    instead of crashing the runtime,
  - reject ids that collide with a first-party pack so a user
    pack cannot silently shadow shipped behaviour,
  - tag each registered pack with its `source`
    (`first-party` / `user`) so the API + doctor can show it.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .connector_packs import ALL_PACKS as FIRST_PARTY_PACKS
from .connector_sdk import (
    ConnectorManifest,
    ConnectorManifestError,
    validate_manifest,
)

log = logging.getLogger(__name__)

DEFAULT_USER_PACK_DIR: Path = Path.home() / ".holdspeak" / "connector_packs"
USER_PACK_ENV_VAR: str = "HOLDSPEAK_USER_PACKS_DIR"


# Sources a registered pack can come from. The string values
# are stable — the API surfaces them verbatim.
SOURCE_FIRST_PARTY: str = "first-party"
SOURCE_USER: str = "user"


@dataclass(frozen=True)
class RegisteredPack:
    """One pack the runtime knows about.

    `module` is the Python module object the pack came from
    (first-party packs are imported eagerly; user packs are
    loaded by spec). `file_path` is the source file (None for
    first-party packs that came from the package source tree)."""

    manifest: ConnectorManifest
    source: str
    module: Any = None
    file_path: Optional[Path] = None


@dataclass(frozen=True)
class DiscoveryError:
    """A pack the loader refused, with enough context to fix it."""

    file_path: Optional[Path]
    pack_id: Optional[str]
    code: str
    message: str

    def __str__(self) -> str:
        where = str(self.file_path) if self.file_path else "<n/a>"
        ident = self.pack_id or "<unknown>"
        return f"{where} (id={ident}): {self.code} — {self.message}"


@dataclass(frozen=True)
class DiscoveryResult:
    """Output of one discovery pass: what loaded, what didn't."""

    packs: tuple[RegisteredPack, ...] = ()
    errors: tuple[DiscoveryError, ...] = ()

    def by_id(self) -> dict[str, RegisteredPack]:
        return {p.manifest.id: p for p in self.packs}


# ───────────────────────── User-pack discovery ────────────────────────


def _resolve_user_pack_dir(
    explicit: Optional[Path] = None,
) -> Path:
    if explicit is not None:
        return Path(explicit)
    env_value = os.environ.get(USER_PACK_ENV_VAR)
    if env_value:
        return Path(env_value)
    return DEFAULT_USER_PACK_DIR


def discover_user_packs(
    directory: Path,
    *,
    forbidden_ids: frozenset[str] = frozenset(),
) -> tuple[tuple[RegisteredPack, ...], tuple[DiscoveryError, ...]]:
    """Walk `directory`, load every `.py` file that exports a
    `MANIFEST`, and return `(packs, errors)`.

    Any exception raised while importing a pack is captured as
    a `DiscoveryError` instead of propagating — discovery never
    crashes the runtime. `forbidden_ids` collects ids that would
    collide with first-party packs; matches are rejected with a
    distinct error code so the operator sees that the first-party
    pack won.
    """
    if not directory.exists():
        return ((), ())
    if not directory.is_dir():
        return (
            (),
            (
                DiscoveryError(
                    file_path=directory,
                    pack_id=None,
                    code="not_a_directory",
                    message=(
                        f"User-pack path {directory} is not a directory; "
                        "skipped."
                    ),
                ),
            ),
        )

    packs: list[RegisteredPack] = []
    errors: list[DiscoveryError] = []
    seen_ids: set[str] = set()

    for path in sorted(directory.iterdir()):
        if path.suffix != ".py" or path.name.startswith("_"):
            continue
        try:
            module = _load_module_from_path(path)
        except Exception as exc:  # noqa: BLE001 — discovery never crashes
            errors.append(
                DiscoveryError(
                    file_path=path,
                    pack_id=None,
                    code="import_failed",
                    message=f"could not import: {exc}",
                )
            )
            continue

        manifest = getattr(module, "MANIFEST", None)
        if manifest is None:
            errors.append(
                DiscoveryError(
                    file_path=path,
                    pack_id=None,
                    code="no_manifest",
                    message="module does not export MANIFEST",
                )
            )
            continue

        try:
            validated = (
                manifest
                if isinstance(manifest, ConnectorManifest)
                else validate_manifest(manifest)
            )
            # Even if it's already a ConnectorManifest, re-validate via
            # to_payload() so a hand-crafted instance with bad fields
            # still trips the validator.
            validated = validate_manifest(validated.to_payload())
        except ConnectorManifestError as exc:
            for entry in exc.errors:
                errors.append(
                    DiscoveryError(
                        file_path=path,
                        pack_id=getattr(manifest, "id", None),
                        code=entry.code,
                        message=str(entry),
                    )
                )
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append(
                DiscoveryError(
                    file_path=path,
                    pack_id=getattr(manifest, "id", None),
                    code="manifest_error",
                    message=f"manifest could not be validated: {exc}",
                )
            )
            continue

        if validated.id in forbidden_ids:
            errors.append(
                DiscoveryError(
                    file_path=path,
                    pack_id=validated.id,
                    code="id_collision_first_party",
                    message=(
                        f"id {validated.id!r} collides with a first-party "
                        "pack; user pack rejected — first-party wins."
                    ),
                )
            )
            continue

        if validated.id in seen_ids:
            errors.append(
                DiscoveryError(
                    file_path=path,
                    pack_id=validated.id,
                    code="id_collision_user_pack",
                    message=(
                        f"id {validated.id!r} already loaded from another "
                        "user pack; this duplicate was skipped."
                    ),
                )
            )
            continue
        seen_ids.add(validated.id)

        packs.append(
            RegisteredPack(
                manifest=validated,
                source=SOURCE_USER,
                module=module,
                file_path=path,
            )
        )
        log.info("loaded user connector pack %s from %s", validated.id, path)

    return tuple(packs), tuple(errors)


def _load_module_from_path(path: Path) -> Any:
    # Use a synthetic module name in a private namespace so user
    # packs don't accidentally shadow first-party imports if a
    # filename collides.
    module_name = f"holdspeak._user_connector_packs.{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


# ───────────────────────── Registry assembly ──────────────────────────


def build_registry(
    user_packs_dir: Optional[Path] = None,
) -> DiscoveryResult:
    """Build the runtime pack registry: first-party + user packs.

    First-party packs always win. User packs that pass
    `validate_manifest` and don't collide with a first-party id
    are merged in; everything else lands in the result's
    `errors` tuple so doctor / `/activity` can render it.
    """
    first_party_packs: list[RegisteredPack] = []
    first_party_ids: set[str] = set()
    for pack_module in FIRST_PARTY_PACKS:
        manifest: ConnectorManifest = pack_module.MANIFEST
        first_party_packs.append(
            RegisteredPack(
                manifest=manifest,
                source=SOURCE_FIRST_PARTY,
                module=pack_module,
                file_path=None,
            )
        )
        first_party_ids.add(manifest.id)

    resolved_dir = _resolve_user_pack_dir(user_packs_dir)
    user_packs, errors = discover_user_packs(
        resolved_dir,
        forbidden_ids=frozenset(first_party_ids),
    )

    return DiscoveryResult(
        packs=tuple(first_party_packs) + tuple(user_packs),
        errors=errors,
    )


__all__ = [
    "DEFAULT_USER_PACK_DIR",
    "USER_PACK_ENV_VAR",
    "SOURCE_FIRST_PARTY",
    "SOURCE_USER",
    "DiscoveryError",
    "DiscoveryResult",
    "RegisteredPack",
    "build_registry",
    "discover_user_packs",
]
