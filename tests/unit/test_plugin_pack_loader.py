"""HS-35-02 — plugin-pack loader + registration tests.

Discovery walks a user-pack directory, imports each `.py` file, validates
the manifest + factory, and merges the results alongside first-party
packs. Registration puts each pack's plugin on a `PluginHost` next to the
built-ins. The loader must:

  - never crash on a malformed pack — surface a structured `DiscoveryError`,
  - require both `MANIFEST` and a callable `create_plugin()`,
  - reject ids that collide with a first-party pack / built-in,
  - reject duplicates inside the user dir (first one wins),
  - tag every registered pack with its `source`,
  - leave the 14 built-ins' registration + routing identical.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.plugin_pack_loader import (
    SOURCE_USER,
    DiscoveryResult,
    RegisteredPluginPack,
    build_registry,
    discover_user_packs,
    load_and_register_plugin_packs,
    register_discovered_plugins,
)
from holdspeak.plugin_sdk import validate_manifest
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.host import PluginHost

# ──────────────────────────── Pack sources ────────────────────────────


_VALID_USER_PACK = """from holdspeak.plugin_sdk import validate_manifest

MANIFEST = validate_manifest({
    "id": "user_demo",
    "label": "Demo user plugin",
    "version": "0.1.0",
    "kind": "synthesizer",
    "intents": ["incident"],
})


class DemoPlugin:
    id = "user_demo"
    version = "0.1.0"
    kind = "synthesizer"

    def run(self, context):
        return {"summary": "demo", "confidence_hint": 1.0}


def create_plugin():
    return DemoPlugin()
"""

_NO_MANIFEST_PACK = """# Forgot to export MANIFEST.
def create_plugin():
    return None
"""

_NO_FACTORY_PACK = """from holdspeak.plugin_sdk import validate_manifest

MANIFEST = validate_manifest({
    "id": "no_factory",
    "label": "No factory",
    "version": "0.1.0",
    "kind": "synthesizer",
})
"""

_BAD_MANIFEST_PACK = """from holdspeak.plugin_sdk import validate_manifest

# kind=frobnicator is not a known plugin kind — validate_manifest raises
# at import, which the loader catches as import_failed.
MANIFEST = validate_manifest({
    "id": "bad_user_pack",
    "label": "Bad user pack",
    "version": "0.1.0",
    "kind": "frobnicator",
})


def create_plugin():
    return None
"""

_IMPORT_RAISES_PACK = """raise RuntimeError("intentional failure for the loader test")
"""

_ID_MISMATCH_PACK = """from holdspeak.plugin_sdk import validate_manifest

MANIFEST = validate_manifest({
    "id": "claims_one",
    "label": "Mismatch",
    "version": "0.1.0",
    "kind": "synthesizer",
})


class Wrong:
    id = "actually_another"
    version = "0.1.0"

    def run(self, context):
        return {}


def create_plugin():
    return Wrong()
"""

_COLLIDING_BUILTIN_PACK = """from holdspeak.plugin_sdk import validate_manifest

# decision_capture is a built-in plugin id — a user pack must not shadow it.
MANIFEST = validate_manifest({
    "id": "decision_capture",
    "label": "Sneaky shadow",
    "version": "0.1.0",
    "kind": "synthesizer",
})


class Shadow:
    id = "decision_capture"

    def run(self, context):
        return {}


def create_plugin():
    return Shadow()
"""


@pytest.fixture
def user_pack_dir(tmp_path: Path) -> Path:
    return tmp_path / "plugin_packs"


# ──────────────────────────── Discovery ───────────────────────────────


def test_missing_directory_is_silent(user_pack_dir: Path) -> None:
    packs, errors = discover_user_packs(user_pack_dir)
    assert packs == ()
    assert errors == ()


def test_valid_user_pack_loads_with_user_source(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert errors == ()
    assert len(packs) == 1
    assert packs[0].source == SOURCE_USER
    assert packs[0].manifest.id == "user_demo"
    assert packs[0].manifest.intents == ("incident",)
    assert packs[0].file_path == user_pack_dir / "demo.py"
    assert callable(packs[0].create_plugin)


def test_pack_without_manifest_is_rejected(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "nope.py").write_text(_NO_MANIFEST_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert packs == ()
    assert [e.code for e in errors] == ["no_manifest"]


def test_pack_without_factory_is_rejected(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "nofac.py").write_text(_NO_FACTORY_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert packs == ()
    assert [e.code for e in errors] == ["no_plugin_factory"]
    assert errors[0].pack_id == "no_factory"


def test_invalid_manifest_is_rejected_without_crashing(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "bad.py").write_text(_BAD_MANIFEST_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    # validate_manifest runs at import → loader catches it as import_failed.
    assert packs == ()
    assert [e.code for e in errors] == ["import_failed"]
    assert "unknown_kind" in errors[0].message


def test_pack_that_raises_at_import_does_not_crash(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "explosive.py").write_text(_IMPORT_RAISES_PACK)
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert {p.manifest.id for p in packs} == {"user_demo"}
    assert any(e.code == "import_failed" for e in errors)


def test_id_collision_with_forbidden_is_rejected(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "shadow.py").write_text(_COLLIDING_BUILTIN_PACK)

    packs, errors = discover_user_packs(
        user_pack_dir, forbidden_ids=frozenset({"decision_capture"})
    )

    assert packs == ()
    assert [e.code for e in errors] == ["id_collision_first_party"]
    assert errors[0].pack_id == "decision_capture"


def test_duplicate_user_pack_ids_keep_first(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "a_demo.py").write_text(_VALID_USER_PACK)
    (user_pack_dir / "b_demo.py").write_text(_VALID_USER_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert [p.manifest.id for p in packs] == ["user_demo"]
    assert [e.code for e in errors] == ["id_collision_user_pack"]


def test_underscored_files_are_skipped(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "__init__.py").write_text("")
    (user_pack_dir / "_helpers.py").write_text("VALUE = 1")
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)

    packs, errors = discover_user_packs(user_pack_dir)

    assert {p.manifest.id for p in packs} == {"user_demo"}
    assert errors == ()


def test_env_override_directory(user_pack_dir: Path, monkeypatch) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)
    monkeypatch.setenv("HOLDSPEAK_USER_PLUGIN_PACKS_DIR", str(user_pack_dir))

    result = build_registry()

    assert "user_demo" in result.by_id()


# ─────────────── Discovery via the committed fixture pack ──────────────


def test_committed_fixture_pack_loads() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "plugin_packs"
    packs, errors = discover_user_packs(fixture_dir)

    by_id = {p.manifest.id: p for p in packs}
    assert "example_user_plugin" in by_id
    assert errors == ()


# ─────────────────────────── Registration ─────────────────────────────


def _host_with_builtins() -> PluginHost:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    return host


def test_register_discovered_plugin_runs_on_host(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "demo.py").write_text(_VALID_USER_PACK)
    host = _host_with_builtins()
    before = set(host.list_plugins())

    registered, errors = load_and_register_plugin_packs(
        host, user_packs_dir=user_pack_dir, forbidden_ids=frozenset(before)
    )

    assert registered == ["user_demo"]
    assert errors == []
    assert host.get_plugin("user_demo") is not None
    # The registered pack plugin actually dispatches through the host.
    result = host.execute(
        "user_demo",
        context={"transcript": "one two three"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="h-1",
    )
    assert result.status == "success"
    assert result.output == {"summary": "demo", "confidence_hint": 1.0}


def test_registration_skips_id_already_on_host() -> None:
    host = _host_with_builtins()
    pack = RegisteredPluginPack(
        manifest=validate_manifest(
            {
                "id": "decision_capture",
                "label": "x",
                "version": "0.1.0",
                "kind": "synthesizer",
            }
        ),
        create_plugin=lambda: None,
        source="user",
    )
    registered, errors = register_discovered_plugins(
        host, DiscoveryResult(packs=(pack,))
    )
    assert registered == []
    assert [e.code for e in errors] == ["id_collision_builtin"]


def test_registration_flags_id_mismatch(user_pack_dir: Path) -> None:
    user_pack_dir.mkdir()
    (user_pack_dir / "mismatch.py").write_text(_ID_MISMATCH_PACK)
    host = PluginHost(default_timeout_seconds=0.5)

    registered, errors = load_and_register_plugin_packs(
        host, user_packs_dir=user_pack_dir
    )

    assert registered == []
    assert [e.code for e in errors] == ["plugin_id_mismatch"]
    assert host.get_plugin("claims_one") is None


# ──────────────────────── Built-ins unchanged ─────────────────────────


def test_first_party_registry_is_empty_today() -> None:
    """The 14 built-ins stay hardcoded; no first-party packs ship yet."""
    result = build_registry(user_packs_dir=Path("/nonexistent/plugin/packs"))
    assert result.packs == ()
    assert result.errors == ()


def test_builtins_register_identically_with_no_packs() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    registered = register_builtin_plugins(host)
    # Discovery against an empty/nonexistent dir adds nothing.
    added, errors = load_and_register_plugin_packs(
        host,
        user_packs_dir=Path("/nonexistent/plugin/packs"),
        forbidden_ids=frozenset(registered),
    )
    assert added == []
    assert errors == []
    assert set(host.list_plugins()) == set(registered)
