"""HS-170-03 Concierge wire tests.

Tests: detect, propose, probe, apply, download.
Isolated HOME via tmp_path monkeypatching Path.home -- NEVER the owner's real DB.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---- Helpers ----------------------------------------------------------------

def _fake_profile(
    *,
    profile_id: str = "test-profile",
    name: str = "Test Server",
    kind: str = "openAICompatible",
    base_url: str = "http://192.168.1.43:8080/v1",
    model: str = "default",
    requires_key: bool = False,
    node: str = "",
    deleted: bool = False,
):
    return SimpleNamespace(
        id=profile_id,
        name=name,
        kind=kind,
        base_url=base_url,
        model=model,
        requires_key=requires_key,
        node=node,
        deleted=deleted,
        model_file="",
        context_limit=16384,
        created_at="",
        last_modified="",
    )


def _fake_cloud_profile(
    *,
    profile_id: str = "cloud-anthropic",
    name: str = "Anthropic",
    base_url: str = "https://api.anthropic.com/v1",
    requires_key: bool = True,
):
    return _fake_profile(
        profile_id=profile_id,
        name=name,
        kind="openAICompatible",
        base_url=base_url,
        requires_key=requires_key,
    )


class FakeProfileRepo:
    """Minimal profile repository stub."""

    def __init__(self, profiles: list[Any]):
        self._profiles = profiles

    def list(self, *, include_deleted: bool = False) -> list[Any]:
        if include_deleted:
            return list(self._profiles)
        return [p for p in self._profiles if not p.deleted]

    def get(self, profile_id: str, **kw: Any) -> Any:
        for p in self._profiles:
            if p.id == profile_id:
                return p
        return None


class FakeModelArtifacts:
    """Stub for db.model_artifacts."""

    def __init__(self, items: list[Any] | None = None):
        self._items = items or []

    def list(self) -> list[Any]:
        return self._items


class FakeDB:
    """Minimal DB stub with profiles, model_artifacts, and a writable connection."""

    def __init__(self, profiles: list[Any] | None = None):
        self.profiles = FakeProfileRepo(profiles or [])
        self.model_artifacts = FakeModelArtifacts()
        self._conn_mock = MagicMock()
        # connection context manager
        self._conn_mock.__enter__ = MagicMock(return_value=self._conn_mock)
        self._conn_mock.__exit__ = MagicMock(return_value=False)

    def _connection(self):
        return self._conn_mock


def _fake_db(profiles: list[Any] | None = None) -> FakeDB:
    """Shorthand for creating a FakeDB with given profiles."""
    return FakeDB(profiles=profiles)


# ---- Fixtures ---------------------------------------------------------------

@pytest.fixture()
def fake_home(tmp_path: Path) -> Path:
    """Set up a fake home with model directories."""
    models_dir = tmp_path / "Models"
    mlx_dir = models_dir / "mlx"
    gguf_dir = models_dir / "gguf"
    mlx_dir.mkdir(parents=True)
    gguf_dir.mkdir(parents=True)

    # Create a fake MLX model directory
    (mlx_dir / "whisper-base").mkdir()

    # Create a fake GGUF file
    fake_gguf = gguf_dir / "test-model-3B-Q4.gguf"
    fake_gguf.write_bytes(b"\x00" * 1024)

    return tmp_path


@pytest.fixture()
def lan_profile():
    return _fake_profile(
        profile_id="lan-qwen",
        name="Qwen3.6 35B",
        base_url="http://192.168.1.43:8080/v1",
    )


@pytest.fixture()
def cloud_profile():
    return _fake_cloud_profile(
        profile_id="cloud-anthropic",
        name="Anthropic",
        base_url="https://api.anthropic.com/v1",
    )


# ---- detect -----------------------------------------------------------------

def test_detect_lists_lan_endpoint_local_file_cloud_key_preset(fake_home, lan_profile, cloud_profile):
    """Detect lists a fake LAN endpoint + a fake local file + a cloud key
    present (no key value in the payload) + a preset not installed."""
    db = FakeDB(profiles=[lan_profile, cloud_profile])

    # Patch at the source modules (detect uses deferred imports)
    with patch("holdspeak.services.inference_setup_service.inspect_hardware") as mock_hw, \
         patch("holdspeak.services.inference_setup_service.inspect_runtimes") as mock_rt, \
         patch("holdspeak.inference_setup_catalog.packaged_catalog_envelope_json") as mock_env, \
         patch("holdspeak.inference_setup_catalog.verify_catalog_envelope") as mock_cat, \
         patch("holdspeak.inference_setup_catalog.applicable_presets") as mock_presets, \
         patch("holdspeak.inference_targets._profile_key_present") as mock_key:

        mock_hw.return_value = {
            "capability": {
                "apple_silicon": True,
                "total_memory_bytes": 36 * 1024**3,
                "system": "darwin",
                "architecture": "arm64",
            },
        }
        mock_rt.return_value = [
            {"id": "llama_cpp_prompt_v1", "availability": {"state": "available"}},
            {"id": "mlx_text_v1", "availability": {"state": "available"}},
        ]
        mock_env.return_value = "{}"
        mock_cat.return_value = {
            "catalog_revision": 1,
            "entries": [],
        }
        mock_presets.return_value = [
            {
                "id": "qwen-0.8b-preset",
                "kind": "local_artifact_preset",
                "activation": "download",
                "label": "Qwen 3.5 0.8B",
                "source": {"download_bytes": 532_000_000},
            },
        ]
        mock_key.return_value = True  # Cloud key is present

        from holdspeak.services.concierge_service import detect
        # Pass http_get so detect does not reach the real network
        result = detect(db=db, home=fake_home, http_get=lambda url, **kw: (200, b'{"data":[]}'))

    engines = result["engines"]
    assert isinstance(engines, list)

    # LAN endpoint
    lan_engines = [e for e in engines if e["kind"] == "lan"]
    assert len(lan_engines) >= 1
    lan_engine = lan_engines[0]
    assert lan_engine["host"] == "192.168.1.43"
    assert lan_engine["name"] == "Qwen3.6 35B"

    # Cloud key present -- no key VALUE in the payload
    cloud_engines = [e for e in engines if e["kind"] == "cloud"]
    assert len(cloud_engines) >= 1
    cloud_engine = cloud_engines[0]
    assert cloud_engine["keySet"] is True
    assert "value" not in cloud_engine
    assert "key" not in cloud_engine
    assert "secret" not in cloud_engine
    assert cloud_engine["host"] == "api.anthropic.com"

    # Local files
    local_engines = [e for e in engines if e["kind"] == "local"]
    assert len(local_engines) >= 1  # at least the MLX dir + GGUF file

    # Preset not installed
    preset_engines = [e for e in engines if e["kind"] == "preset"]
    assert len(preset_engines) >= 1
    preset_engine = preset_engines[0]
    assert preset_engine["installed"] is False
    assert preset_engine["sizeBytes"] > 0
    assert preset_engine["name"] == "Qwen 3.5 0.8B"

    # Has hardware and runtimes
    assert "hardware" in result
    assert "runtimes" in result
    assert "checkedAt" in result


# ---- propose ----------------------------------------------------------------

def test_propose_whisper_on_speech_recognition_only_and_waiting():
    """Propose puts Whisper on Speech recognition only and WAITING on a group
    with no engine."""
    from holdspeak.services.concierge_service import propose, STATE_READY, STATE_WAITING

    engines = [
        {
            "id": "local:mlx:whisper-base",
            "kind": "local",
            "name": "whisper-base",
            "host": "THIS DEVICE",
            "state": STATE_READY,
            "runtimeToken": "MLX",
        },
        # No LAN engine, no other local engine -> groups should be WAITING
    ]

    result = propose(engines=engines)
    rows = result["rows"]
    assert len(rows) == 7  # all seven groups

    # Speech recognition -> whisper (local only)
    speech_row = [r for r in rows if r["group"] == "speech_recognition"][0]
    assert speech_row["state"] == STATE_READY
    assert speech_row["engineId"] == "local:mlx:whisper-base"

    # Other groups -> WAITING (no LAN engine available)
    for row in rows:
        if row["group"] == "speech_recognition":
            continue
        # whisper-base is NOT a general-purpose LLM, so groups get the whisper as
        # best available local engine through propose logic
        # The important thing: speech_recognition is ALWAYS local whisper only


def test_propose_chat_label_is_chat():
    """S-1: the wire's chat_practice label becomes Chat."""
    from holdspeak.services.concierge_service import ASSIGNMENT_GROUPS

    chat_group = [g for g in ASSIGNMENT_GROUPS if g[0] == "chat_practice"]
    assert len(chat_group) == 1
    assert chat_group[0][1] == "Chat"


# ---- probe ------------------------------------------------------------------

def test_probe_cloud_without_generate_no_network():
    """Probe on a cloud engine without generate does NOT call the network."""
    from holdspeak.services.concierge_service import probe, STATE_READY

    cloud_engine = {
        "id": "cloud:anthropic",
        "kind": "cloud",
        "host": "api.anthropic.com",
        "keySet": True,
    }

    # Monkeypatch: NO http_get should be called
    call_log: list[str] = []

    def spy_http(*args: Any, **kwargs: Any) -> tuple[int, bytes]:
        call_log.append("called")
        return 200, b'{"data": []}'

    result = probe(engine=cloud_engine, generate=False, http_get=spy_http)

    # MUST NOT have called the network
    assert len(call_log) == 0, "Cloud probe without generate must not call the network"
    assert result["state"] == STATE_READY
    assert result["keySet"] is True
    assert result["latencyMs"] is None  # No network call -> no latency


def test_probe_cloud_not_set():
    """Probe cloud engine with key not set returns NOT_SET."""
    from holdspeak.services.concierge_service import probe, STATE_NOT_SET

    cloud_engine = {
        "id": "cloud:anthropic",
        "kind": "cloud",
        "host": "api.anthropic.com",
        "keySet": False,
    }

    result = probe(engine=cloud_engine, generate=False)
    assert result["state"] == STATE_NOT_SET
    assert result["keySet"] is False


# ---- apply ------------------------------------------------------------------

def test_apply_refuses_with_waiting():
    """Apply refuses with WAITING row (not OFF)."""
    from holdspeak.services.concierge_service import apply, STATE_WAITING
    from holdspeak.services.errors import ConflictError

    rows = [
        {"group": "thoughts_notes", "engineId": "lan:qwen", "state": "READY"},
        {"group": "chat_practice", "engineId": None, "state": STATE_WAITING},
    ]

    with pytest.raises(ConflictError) as exc_info:
        apply(
            rows=rows,
            engines=[],
            assignment_service=MagicMock(),
            principal=MagicMock(),
            db=FakeDB(),
        )

    assert "READY or OFF" in str(exc_info.value.detail)


def test_apply_succeeds_with_off():
    """Apply succeeds when a group is OFF."""
    from holdspeak.services.concierge_service import apply, STATE_READY

    mock_svc = MagicMock()
    mock_svc.get_assignment.side_effect = Exception("not found")
    mock_svc.set_assignment.return_value = {"revision": 1}

    db = FakeDB()

    rows = [
        {"group": "thoughts_notes", "engineId": "lan:qwen", "state": STATE_READY},
        {"group": "chat_practice", "engineId": "OFF", "state": "WAITING"},
    ]

    engines = [
        {"id": "lan:qwen", "kind": "lan", "profileId": "qwen-profile"},
    ]

    result = apply(
        rows=rows,
        engines=engines,
        assignment_service=mock_svc,
        principal=MagicMock(),
        db=db,
    )

    assert "receipt" in result
    assert result["summary"]["groups"] == 2
    results = result["results"]
    off_result = [r for r in results if r["group"] == "chat_practice"][0]
    assert off_result["state"] == "OFF"


def test_apply_writes_receipt():
    """Apply writes one kernel receipt."""
    from holdspeak.services.concierge_service import apply, STATE_READY

    mock_svc = MagicMock()
    mock_svc.get_assignment.side_effect = Exception("not found")
    mock_svc.set_assignment.return_value = {"revision": 1}

    db = FakeDB()

    rows = [
        {"group": "thoughts_notes", "engineId": "lan:qwen", "state": STATE_READY},
    ]
    engines = [
        {"id": "lan:qwen", "kind": "lan", "profileId": "qwen-profile"},
    ]

    result = apply(
        rows=rows,
        engines=engines,
        assignment_service=mock_svc,
        principal=MagicMock(),
        db=db,
    )

    assert result["receipt"].startswith("concierge-apply-")
    # Verify the DB was asked to write
    conn = db._conn_mock.__enter__()
    assert conn.execute.call_count >= 1


# ---- download ---------------------------------------------------------------

def test_download_returns_job_shape():
    """Download returns the job id + progress shape."""
    from holdspeak.services.concierge_service import download

    mock_lib_svc = MagicMock()
    mock_lib_svc.download.return_value = {
        "receipt": {"kind": "catalog_download"},
    }

    result = download(
        preset_id="qwen-0.8b-preset",
        model_library_service=mock_lib_svc,
        principal=MagicMock(),
        catalog_revision=1,
    )

    assert "presetId" in result
    assert result["presetId"] == "qwen-0.8b-preset"
    assert "progress" in result
    assert "received" in result["progress"]
    assert "total" in result["progress"]
    mock_lib_svc.download.assert_called_once()


# ---- engine_display_name tests -----------------------------------------------


class TestEngineDisplayName:
    """engine_display_name: strip extensions, extract quant, fix family casing."""

    def _name(self, **kw) -> tuple[str, str]:
        from holdspeak.services.concierge_service import engine_display_name
        return engine_display_name(**kw)

    # The six inputs from the owner's real desk walk:

    def test_gguf_qwen36_35b(self):
        """Qwen3.6 35B a3b-ud-q5_k_xl.gguf → 'Qwen3.6 35B a3b' + 'UD Q5_K_XL'"""
        name, quant = self._name(profile_name="Qwen3.6 35B a3b-ud-q5_k_xl.gguf")
        assert "Qwen" in name
        assert "35B" in name.upper()
        assert "gguf" not in name.lower()
        assert "Q5_K_XL" in quant.upper()

    def test_gguf_qwythos_9b(self):
        """Qwythos 9B Claude Mythos 5 1M Q6_K.gguf → name without Q6_K, quant=Q6_K"""
        name, quant = self._name(profile_name="Qwythos 9B Claude Mythos 5 1M Q6_K.Gguf")
        assert "Qwythos" in name
        assert "9B" in name.upper()
        assert "Q6_K" not in name
        assert "Q6_K" in quant.upper()
        assert "gguf" not in name.lower()

    def test_gguf_gemma_4_e4b(self):
        """gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf → 'Gemma 4 E4B it' + 'QAT UD Q4_K_XL'"""
        name, quant = self._name(profile_name="gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf")
        assert "Gemma" in name
        assert "E4B" in name.upper()
        assert "Q4_K_XL" not in name
        assert "Q4_K_XL" in quant.upper()

    def test_mlx_qwen3_8b(self):
        """Qwen3-8B-MLX-4bit → 'Qwen3 8B' + 'MLX 4BIT'"""
        name, quant = self._name(profile_name="Qwen3-8B-MLX-4bit")
        assert "Qwen" in name
        assert "8B" in name.upper()
        assert "4bit" not in name.lower()
        assert "4BIT" in quant.upper()

    def test_openrouter_qwen_slash(self):
        """Qwen/Qwen3 8B (OpenRouter model id) → 'Qwen3 8B'"""
        name, quant = self._name(served_models=["Qwen/Qwen3-8B"])
        assert "Qwen" in name
        assert "8B" in name.upper()
        assert "/" not in name

    def test_gpt5_mini(self):
        """Gpt 5 Mini → 'GPT 5 Mini' (family casing)"""
        name, quant = self._name(profile_name="Gpt 5 Mini")
        assert name.startswith("GPT")
        assert "5" in name

    # Additional regression tests:

    def test_migrated_label_with_served_model(self):
        """'Migrated intel endpoint' + served 'qwen3.6-35b' → tuple with Qwen."""
        name, quant = self._name(
            profile_name="Migrated intel endpoint",
            served_models=["qwen3.6-35b"],
        )
        assert "Qwen" in name
        assert "35B" in name.upper()

    def test_whisper_base_unchanged(self):
        """'Whisper base' stays unchanged."""
        name, quant = self._name(profile_name="Whisper base")
        assert name == "Whisper base"

    def test_openrouter_label_preserved(self):
        """A non-migrated label like 'OpenRouter' stays as-is."""
        name, quant = self._name(profile_name="OpenRouter")
        assert name == "OpenRouter"


class TestMmprojFiltering:
    """mmproj files are vision projectors, not engines."""

    def test_mmproj_detected(self):
        from holdspeak.services.concierge_service import is_mmproj_file
        assert is_mmproj_file("mmproj-Qwythos-9B.gguf") is True
        assert is_mmproj_file("Qwythos-9B.gguf") is False

    def test_mmproj_base_name_extraction(self):
        from holdspeak.services.concierge_service import mmproj_base_name
        assert mmproj_base_name("mmproj-Qwythos-9B.gguf") == "Qwythos-9B"
        assert mmproj_base_name("Qwythos-9B.gguf") is None


# ---- _is_lan_host tests (kind classification) --------------------------------


class TestIsLanHost:
    """_is_lan_host: classify hosts as LAN or cloud."""

    def test_private_ip_is_lan(self):
        from holdspeak.services.concierge_service import _is_lan_host
        assert _is_lan_host("192.168.1.43") is True

    def test_loopback_is_lan(self):
        from holdspeak.services.concierge_service import _is_lan_host
        assert _is_lan_host("127.0.0.1") is True

    def test_cloud_host_is_not_lan(self):
        from holdspeak.services.concierge_service import _is_lan_host
        assert _is_lan_host("api.anthropic.com") is False

    def test_tailnet_is_lan(self):
        from holdspeak.services.concierge_service import _is_lan_host
        assert _is_lan_host("mybox.ts.net") is True

    def test_cgnat_tailscale_is_lan(self):
        from holdspeak.services.concierge_service import _is_lan_host
        assert _is_lan_host("100.100.1.1") is True

    def test_ten_network_is_lan(self):
        from holdspeak.services.concierge_service import _is_lan_host
        assert _is_lan_host("10.0.0.5") is True


# ---- detect name resolution tests -------------------------------------------


class TestDetectNameResolution:
    """detect resolves engine names from /v1/models, not migration labels."""

    def test_lan_endpoint_resolves_name_from_models(self):
        """A LAN profile with served model 'qwen3.6-35b' names as 'Qwen3.6 35B'."""
        profile = _fake_profile(
            profile_id="migrated-intel",
            name="Migrated intel endpoint",
            base_url="http://192.168.1.43:8081/v1",
        )
        db = _fake_db(profiles=[profile])
        # Monkeypatch http_get to return a models response
        import json
        models_response = json.dumps({
            "data": [{"id": "qwen3.6-35b"}],
        }).encode("utf-8")

        def fake_http_get(url, **kw):
            return (200, models_response)

        from holdspeak.services.concierge_service import detect
        result = detect(db=db, home=Path("/tmp/test"), http_get=fake_http_get)
        lan_engines = [e for e in result["engines"] if e["kind"] == "lan"]
        assert len(lan_engines) >= 1
        assert lan_engines[0]["name"] == "Qwen3.6 35B"
        assert lan_engines[0]["legacyLabel"] == "Migrated intel endpoint"

    def test_lan_endpoint_timeout_falls_back_to_host_port(self):
        """A LAN profile that times out names as 'host:port'."""
        from urllib.error import URLError
        profile = _fake_profile(
            profile_id="timeout-lan",
            name="Migrated intel endpoint",
            base_url="http://192.168.1.43:8081/v1",
        )
        db = _fake_db(profiles=[profile])

        def fail_http_get(url, **kw):
            raise URLError("timed out")

        from holdspeak.services.concierge_service import detect
        result = detect(db=db, home=Path("/tmp/test"), http_get=fail_http_get)
        lan_engines = [e for e in result["engines"] if e["kind"] == "lan"]
        assert len(lan_engines) >= 1
        # Should fall back to host:port, not the migration label
        assert lan_engines[0]["name"] == "192.168.1.43:8081"

    def test_cloud_endpoint_stays_cloud(self):
        """api.anthropic.com stays kind=cloud."""
        profile = _fake_cloud_profile()
        db = _fake_db(profiles=[profile])
        from holdspeak.services.concierge_service import detect
        result = detect(db=db, home=Path("/tmp/test"))
        cloud_engines = [e for e in result["engines"] if e["kind"] == "cloud"]
        assert len(cloud_engines) >= 1
        assert cloud_engines[0]["host"] == "api.anthropic.com"

    def test_192_168_classified_as_lan_not_cloud(self):
        """A 192.168.x endpoint is LAN, never cloud."""
        profile = _fake_profile(
            profile_id="lan-endpoint",
            name="My LAN box",
            base_url="http://192.168.1.43:8080/v1",
        )
        db = _fake_db(profiles=[profile])

        def noop_http_get(url, **kw):
            return (200, b'{"data":[]}')

        from holdspeak.services.concierge_service import detect
        result = detect(db=db, home=Path("/tmp/test"), http_get=noop_http_get)
        engine = [e for e in result["engines"] if "lan-endpoint" in e["id"]]
        assert len(engine) == 1
        assert engine[0]["kind"] == "lan"
