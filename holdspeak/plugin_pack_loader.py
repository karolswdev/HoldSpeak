"""Discovery + loader for meeting-intel plugin packs.

HS-35-02. The twin of `holdspeak/connector_pack_loader.py`, for plugins.
First-party packs live under `holdspeak.plugin_packs.*`; this module adds
local-user packs dropped into `~/.holdspeak/plugin_packs/`. The loader
imports each `.py` file as a module, requires it to export
`MANIFEST: PluginManifest` + a `create_plugin()` factory, re-runs
`validate_manifest` on the payload (so a malformed pack doesn't crash
discovery), and merges the result into a registry alongside first-party
packs. `register_discovered_plugins` then registers each pack's plugin on
a `PluginHost` next to the built-ins.

`~/.holdspeak/plugin_packs/` is the trust boundary — code dropped there
runs in-process with the user's own permissions. Sandboxing is *not* a
goal: a pack file under the user's home dir is by definition code the user
has chosen to trust. The loader's job is honest discovery, not isolation:

  - log every pack it discovers and its validation state,
  - surface `validate_manifest` (and import/factory) errors as structured
    `DiscoveryError`s instead of crashing the runtime,
  - reject ids that collide with a first-party pack or a built-in plugin so
    a user pack cannot silently shadow shipped behaviour,
  - tag each registered pack with its `source` (`first-party` / `user`).

**Behavior-preserving:** the 14 built-ins keep their hardcoded
registration + routing. Packs *augment* the host registry; they do not
modify the built-ins or the router chains.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .plugin_packs import ALL_PACKS as FIRST_PARTY_PACKS
from .plugin_sdk import (
    PluginManifest,
    PluginManifestError,
    validate_manifest,
)

log = logging.getLogger(__name__)

DEFAULT_USER_PACK_DIR: Path = Path.home() / ".holdspeak" / "plugin_packs"
USER_PACK_ENV_VAR: str = "HOLDSPEAK_USER_PLUGIN_PACKS_DIR"

# Sources a registered pack can come from. The string values are stable —
# any API/doctor surface shows them verbatim.
SOURCE_FIRST_PARTY: str = "first-party"
SOURCE_USER: str = "user"


@dataclass(frozen=True)
class RegisteredPluginPack:
    """One plugin pack the runtime knows about.

    `create_plugin` is the pack's zero-arg factory returning a `HostPlugin`
    instance. `module` is the Python module the pack came from; `file_path`
    is the source file (None for first-party packs from the package tree).
    """

    manifest: PluginManifest
    create_plugin: Callable[[], Any]
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

    packs: tuple[RegisteredPluginPack, ...] = ()
    errors: tuple[DiscoveryError, ...] = ()

    def by_id(self) -> dict[str, RegisteredPluginPack]:
        return {p.manifest.id: p for p in self.packs}


# ───────────────────────── User-pack discovery ────────────────────────


def _resolve_user_pack_dir(explicit: Optional[Path] = None) -> Path:
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
) -> tuple[tuple[RegisteredPluginPack, ...], tuple[DiscoveryError, ...]]:
    """Walk `directory`, load every `.py` file that exports a `MANIFEST`
    + `create_plugin`, and return `(packs, errors)`.

    Any exception raised while importing a pack is captured as a
    `DiscoveryError` instead of propagating — discovery never crashes the
    runtime. `forbidden_ids` collects ids that would collide with a
    first-party pack or a built-in plugin; matches are rejected with a
    distinct code so the operator sees that the shipped plugin won.
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
                    message=f"User-pack path {directory} is not a directory; skipped.",
                ),
            ),
        )

    packs: list[RegisteredPluginPack] = []
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
            base = (
                manifest
                if isinstance(manifest, PluginManifest)
                else validate_manifest(manifest)
            )
            # Re-validate via to_payload() so a hand-crafted instance with
            # bad fields still trips the validator.
            validated = validate_manifest(base.to_payload())
        except PluginManifestError as exc:
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

        factory = getattr(module, "create_plugin", None)
        if not callable(factory):
            errors.append(
                DiscoveryError(
                    file_path=path,
                    pack_id=validated.id,
                    code="no_plugin_factory",
                    message="module does not export a callable create_plugin()",
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
                        f"id {validated.id!r} collides with a first-party pack "
                        "or built-in plugin; user pack rejected — shipped wins."
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
                        f"id {validated.id!r} already loaded from another user "
                        "pack; this duplicate was skipped."
                    ),
                )
            )
            continue
        seen_ids.add(validated.id)

        packs.append(
            RegisteredPluginPack(
                manifest=validated,
                create_plugin=factory,
                source=SOURCE_USER,
                module=module,
                file_path=path,
            )
        )
        log.info("loaded user plugin pack %s from %s", validated.id, path)

    return tuple(packs), tuple(errors)


def _load_module_from_path(path: Path) -> Any:
    # Synthetic module name in a private namespace so user packs don't
    # accidentally shadow first-party imports if a filename collides.
    module_name = f"holdspeak._user_plugin_packs.{path.stem}"
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
    *,
    forbidden_ids: frozenset[str] = frozenset(),
) -> DiscoveryResult:
    """Build the pack registry: first-party + user packs.

    First-party packs always win. User packs that pass `validate_manifest`,
    expose a `create_plugin` factory, and don't collide with a first-party
    pack id (or any id in `forbidden_ids`, e.g. the built-in plugin ids) are
    merged in; everything else lands in the result's `errors` tuple.
    """
    first_party_packs: list[RegisteredPluginPack] = []
    first_party_ids: set[str] = set()
    for pack_module in FIRST_PARTY_PACKS:
        manifest: PluginManifest = pack_module.MANIFEST
        first_party_packs.append(
            RegisteredPluginPack(
                manifest=manifest,
                create_plugin=pack_module.create_plugin,
                source=SOURCE_FIRST_PARTY,
                module=pack_module,
                file_path=None,
            )
        )
        first_party_ids.add(manifest.id)

    resolved_dir = _resolve_user_pack_dir(user_packs_dir)
    user_packs, user_errors = discover_user_packs(
        resolved_dir,
        forbidden_ids=frozenset(first_party_ids) | forbidden_ids,
    )

    return DiscoveryResult(
        packs=tuple(first_party_packs) + tuple(user_packs),
        errors=tuple(user_errors),
    )


def register_discovered_plugins(
    host: Any,
    result: DiscoveryResult,
) -> tuple[list[str], list[DiscoveryError]]:
    """Register every discovered pack's plugin onto `host`.

    Returns `(registered_ids, errors)`. A pack whose id is already on the
    host (a built-in or an earlier pack), whose factory raises, or whose
    produced plugin's id doesn't match its manifest is skipped with a
    structured error — registration never crashes. The result's existing
    discovery errors are carried through.
    """
    registered: list[str] = []
    errors: list[DiscoveryError] = list(result.errors)

    for pack in result.packs:
        pack_id = pack.manifest.id
        if host.get_plugin(pack_id) is not None:
            errors.append(
                DiscoveryError(
                    file_path=pack.file_path,
                    pack_id=pack_id,
                    code="id_collision_builtin",
                    message=(
                        f"id {pack_id!r} is already registered on the host "
                        "(a built-in or earlier pack); pack plugin skipped."
                    ),
                )
            )
            continue
        try:
            plugin = pack.create_plugin()
        except Exception as exc:  # noqa: BLE001 — registration never crashes
            errors.append(
                DiscoveryError(
                    file_path=pack.file_path,
                    pack_id=pack_id,
                    code="factory_failed",
                    message=f"create_plugin() raised: {exc}",
                )
            )
            continue
        produced_id = str(getattr(plugin, "id", "")).strip()
        if produced_id != pack_id:
            errors.append(
                DiscoveryError(
                    file_path=pack.file_path,
                    pack_id=pack_id,
                    code="plugin_id_mismatch",
                    message=(
                        f"create_plugin() returned a plugin with id "
                        f"{produced_id!r}, expected {pack_id!r}."
                    ),
                )
            )
            continue
        try:
            host.register(plugin)
        except Exception as exc:  # noqa: BLE001
            errors.append(
                DiscoveryError(
                    file_path=pack.file_path,
                    pack_id=pack_id,
                    code="register_failed",
                    message=f"host.register() rejected the plugin: {exc}",
                )
            )
            continue
        registered.append(pack_id)
        log.info("registered %s plugin pack %s", pack.source, pack_id)

    return registered, errors


def load_and_register_plugin_packs(
    host: Any,
    *,
    user_packs_dir: Optional[Path] = None,
    forbidden_ids: frozenset[str] = frozenset(),
) -> tuple[list[str], list[DiscoveryError]]:
    """Convenience: build the registry then register on `host`.

    `forbidden_ids` should carry the built-in plugin ids so a user pack
    can't shadow a built-in even via the manifest layer. Returns
    `(registered_ids, errors)`.
    """
    result = build_registry(user_packs_dir, forbidden_ids=forbidden_ids)
    return register_discovered_plugins(host, result)


__all__ = [
    "DEFAULT_USER_PACK_DIR",
    "USER_PACK_ENV_VAR",
    "SOURCE_FIRST_PARTY",
    "SOURCE_USER",
    "DiscoveryError",
    "DiscoveryResult",
    "RegisteredPluginPack",
    "build_registry",
    "discover_user_packs",
    "register_discovered_plugins",
    "load_and_register_plugin_packs",
]
