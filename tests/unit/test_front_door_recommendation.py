"""HS-156-01 -- Front Door recommendation engine unit tests.

Fixture truth tables, completeness law, probe boundary, and cloud exclusion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.services.front_door_service import (
    ASSIGNMENT_GROUPS,
    PACK_BALANCED,
    PACK_FULL,
    PACK_LIGHT,
    recommend,
    _human_size,
)


# ── Fixture helpers ──────────────────────────────────────────────────────

_16GB = 16 * 1024 ** 3
_32GB = 32 * 1024 ** 3
_8GB = 8 * 1024 ** 3

# The two downloadable catalog presets (from inference_setup_catalog.py)
PRESET_QWEN35_4B = {
    "kind": "local_artifact_preset",
    "id": "preset_local_qwen35_4b_gguf_q4km",
    "experience": "quick",
    "label": "Quick local Qwen",
    "summary": "Fast local Thought interviews and everyday writing.",
    "runtime_id": "llama_cpp_prompt_v1",
    "runtime_min_revision": "0.3.34",
    "format": "gguf",
    "boundary": "same_device",
    "activation": "download",
    "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
    "source": {
        "repository": "unsloth/Qwen3.5-4B-GGUF",
        "revision": "e87f176479d0855a907a41277aca2f8ee7a09523",
        "filename": "Qwen3.5-4B-Q4_K_M.gguf",
        "file_sha256": "sha256:1d203c2196991da08bc5b191ab4727516f476f3167e3276f75a0c5257493aadb",
        "manifest_sha256": "sha256:8eeea91e273c731f889a47405d49651dc4dcb90bc98b9a08af8135d1af44a4a8",
        "download_bytes": 2_740_937_888,
        "installed_bytes": 2_740_937_888,
        "peak_free_bytes": 5_750_000_000,
        "license": "Apache-2.0",
    },
    "platforms": ["darwin_arm64", "linux_x86_64", "linux_aarch64"],
    "applicability": {"state": "applicable", "reason": None},
}

PRESET_QWEN35_08B = {
    "kind": "local_artifact_preset",
    "id": "preset_local_qwen35_08b_gguf_q4km",
    "experience": "quick",
    "label": "Tiny local Qwen",
    "summary": "A 0.8B local model for intent, routing, and lightweight work.",
    "runtime_id": "llama_cpp_prompt_v1",
    "runtime_min_revision": "0.3.34",
    "format": "gguf",
    "boundary": "same_device",
    "activation": "download",
    "context": {"recommended_tokens": 8192, "ceiling_tokens": 8192},
    "source": {
        "repository": "unsloth/Qwen3.5-0.8B-GGUF",
        "revision": "6ab461498e2023f6e3c1baea90a8f0fe38ab64d0",
        "filename": "Qwen3.5-0.8B-Q4_K_M.gguf",
        "file_sha256": "sha256:bd258782e35f7f458f8aced1adc053e6e92e89bc735ba3be89d38a06121dc517",
        "manifest_sha256": "sha256:ec6d18c20bccb7db96fd368b275ce3017d84046e8573b1ebc7854bed83ce348b",
        "download_bytes": 532_517_120,
        "installed_bytes": 532_517_120,
        "peak_free_bytes": 1_200_000_000,
        "license": "Apache-2.0",
    },
    "platforms": ["darwin_arm64", "linux_x86_64", "linux_aarch64"],
    "applicability": {"state": "applicable", "reason": None},
}

BOTH_PRESETS = [PRESET_QWEN35_08B, PRESET_QWEN35_4B]


def _hw(*, apple_silicon: bool = True, total_memory_bytes: int = _16GB) -> dict[str, Any]:
    """Build a hardware snapshot fixture."""
    return {
        "capability": {
            "system": "darwin",
            "architecture": "arm64",
            "apple_silicon": apple_silicon,
            "total_memory_bytes": total_memory_bytes,
            "logical_cpu_count": 10,
            "unified_memory": True if apple_silicon else None,
            "accelerators": ["metal"] if apple_silicon else [],
        },
        "observation": {
            "available_memory_bytes": total_memory_bytes // 2,
            "storage_available_bytes": 100_000_000_000,
        },
        "detection": {"state": "available", "reason": None},
    }


def _no_probe(base_url: str) -> bool:
    """A probe that always says unreachable (no network)."""
    return False


def _always_reachable(base_url: str) -> bool:
    """A probe that always says reachable."""
    return True


def _group_ids_from_pack(pack: dict[str, Any]) -> set[str]:
    """Extract the assignment group ids covered by a pack's display lines."""
    return {
        line["group_id"]
        for line in pack["display_lines"]
        if "group_id" in line
    }


def _jobs_from_pack(pack: dict[str, Any]) -> set[str]:
    """Extract the special job names (speech, tts) from a pack's display lines."""
    return {
        line["job"]
        for line in pack["display_lines"]
        if "job" in line
    }


def _pack_by_id(packs: list[dict[str, Any]], pack_id: str) -> dict[str, Any] | None:
    for p in packs:
        if p["id"] == pack_id:
            return p
    return None


# ── (a) 16 GB Apple Silicon, no endpoints ────────────────────────────────

class Test16GBAppleSiliconNoEndpoints:
    """Fixture truth table: 16 GB Apple Silicon, no endpoints, llama.cpp available."""

    def _recommend(self) -> dict[str, Any]:
        return recommend(
            hardware=_hw(apple_silicon=True, total_memory_bytes=_16GB),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[],
            has_llama_cpp=True,
            has_mlx=True,
            probe=_no_probe,
        )

    def test_returns_three_packs(self) -> None:
        result = self._recommend()
        assert len(result["packs"]) == 3

    def test_pack_ids(self) -> None:
        result = self._recommend()
        ids = [p["id"] for p in result["packs"]]
        assert ids == ["light", "balanced", "full"]

    def test_balanced_is_recommended(self) -> None:
        result = self._recommend()
        balanced = _pack_by_id(result["packs"], "balanced")
        assert balanced is not None
        assert balanced["recommended"] is True
        # Light and full are not recommended
        light = _pack_by_id(result["packs"], "light")
        assert light is not None
        assert light["recommended"] is False
        full = _pack_by_id(result["packs"], "full")
        assert full is not None
        assert full["recommended"] is False

    def test_light_uses_smallest_preset(self) -> None:
        """Light pack should use the 0.8B model (smallest)."""
        result = self._recommend()
        light = _pack_by_id(result["packs"], "light")
        assert light is not None
        plan_presets = [
            e["preset_id"] for e in light["plan"] if e.get("kind") == "catalog_download"
        ]
        # All seven groups get the same smallest preset
        assert all(p == "preset_local_qwen35_08b_gguf_q4km" for p in plan_presets)

    def test_balanced_uses_appropriate_preset_for_16gb(self) -> None:
        """Balanced pack: 16GB should fit the 4B model comfortably (peak * 1.5 = 8.6GB < 16GB)."""
        result = self._recommend()
        balanced = _pack_by_id(result["packs"], "balanced")
        assert balanced is not None
        plan_presets = [
            e["preset_id"] for e in balanced["plan"] if e.get("kind") == "catalog_download"
        ]
        # 16GB >= 5.75GB * 1.5 = 8.625GB, so the 4B fits comfortably
        assert all(p == "preset_local_qwen35_4b_gguf_q4km" for p in plan_presets)

    def test_full_uses_largest_fitting_preset(self) -> None:
        """Full pack: 16GB fits the 4B model (peak 5.75GB < 16GB)."""
        result = self._recommend()
        full = _pack_by_id(result["packs"], "full")
        assert full is not None
        plan_presets = [
            e["preset_id"] for e in full["plan"] if e.get("kind") == "catalog_download"
        ]
        assert all(p == "preset_local_qwen35_4b_gguf_q4km" for p in plan_presets)

    def test_all_seven_groups_covered(self) -> None:
        """Every pack covers all seven groups."""
        result = self._recommend()
        expected_groups = {gid for gid, _ in ASSIGNMENT_GROUPS}
        for pack in result["packs"]:
            covered = _group_ids_from_pack(pack)
            assert covered == expected_groups, f"Pack {pack['id']} missing groups: {expected_groups - covered}"

    def test_speech_and_tts_in_every_pack(self) -> None:
        """Every pack includes speech and TTS."""
        result = self._recommend()
        for pack in result["packs"]:
            jobs = _jobs_from_pack(pack)
            assert "speech" in jobs, f"Pack {pack['id']} missing speech"
            assert "tts" in jobs, f"Pack {pack['id']} missing tts"

    def test_light_speech_is_base_whisper(self) -> None:
        result = self._recommend()
        light = _pack_by_id(result["packs"], "light")
        assert light is not None
        speech_plans = [e for e in light["plan"] if e.get("job") == "speech"]
        assert len(speech_plans) == 1
        assert speech_plans[0]["whisper_name"] == "base"

    def test_balanced_speech_is_small_whisper_at_16gb(self) -> None:
        result = self._recommend()
        balanced = _pack_by_id(result["packs"], "balanced")
        assert balanced is not None
        speech_plans = [e for e in balanced["plan"] if e.get("job") == "speech"]
        assert len(speech_plans) == 1
        assert speech_plans[0]["whisper_name"] == "small"

    def test_display_lines_include_mlx_appropriate_labels(self) -> None:
        """Display lines should include human-readable labels with sizes."""
        result = self._recommend()
        light = _pack_by_id(result["packs"], "light")
        assert light is not None
        # Check that display lines have source_label containing the preset label
        group_lines = [l for l in light["display_lines"] if "group_id" in l]
        for line in group_lines:
            assert "Qwen" in line["source_label"]  # Catalog preset label contains "Qwen"
            assert line["provenance"] == "catalog_preset"

    def test_total_download_bytes_is_calculated(self) -> None:
        result = self._recommend()
        for pack in result["packs"]:
            calculated = sum(e.get("download_bytes", 0) for e in pack["plan"])
            assert pack["total_download_bytes"] == calculated

    def test_facts_reflect_hardware(self) -> None:
        result = self._recommend()
        facts = result["facts"]
        assert facts["apple_silicon"] is True
        assert facts["total_memory_bytes"] == _16GB
        assert facts["has_llama_cpp"] is True
        assert facts["has_mlx"] is True
        assert facts["has_cloud_credential"] is False
        assert facts["endpoints"] == []
        assert facts["probed_urls"] == []


# ── (b) 32 GB Apple Silicon ──────────────────────────────────────────────

class Test32GBAppleSilicon:
    """Fixture truth table: 32 GB Apple Silicon, no endpoints."""

    def _recommend(self) -> dict[str, Any]:
        return recommend(
            hardware=_hw(apple_silicon=True, total_memory_bytes=_32GB),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[],
            has_llama_cpp=True,
            has_mlx=True,
            probe=_no_probe,
        )

    def test_returns_three_packs(self) -> None:
        result = self._recommend()
        assert len(result["packs"]) == 3

    def test_balanced_uses_larger_model_for_32gb(self) -> None:
        """32GB fits the 4B comfortably (peak*1.5 = 8.6GB << 32GB)."""
        result = self._recommend()
        balanced = _pack_by_id(result["packs"], "balanced")
        assert balanced is not None
        plan_presets = [
            e["preset_id"] for e in balanced["plan"] if e.get("kind") == "catalog_download"
        ]
        assert all(p == "preset_local_qwen35_4b_gguf_q4km" for p in plan_presets)

    def test_full_uses_largest_for_32gb(self) -> None:
        """Full on 32GB: the 4B model (largest available in catalog)."""
        result = self._recommend()
        full = _pack_by_id(result["packs"], "full")
        assert full is not None
        plan_presets = [
            e["preset_id"] for e in full["plan"] if e.get("kind") == "catalog_download"
        ]
        assert all(p == "preset_local_qwen35_4b_gguf_q4km" for p in plan_presets)

    def test_full_whisper_is_medium_at_32gb(self) -> None:
        """Full pack at 32GB should use medium whisper."""
        result = self._recommend()
        full = _pack_by_id(result["packs"], "full")
        assert full is not None
        speech_plans = [e for e in full["plan"] if e.get("job") == "speech"]
        assert len(speech_plans) == 1
        assert speech_plans[0]["whisper_name"] == "medium"

    def test_balanced_whisper_is_small_at_32gb(self) -> None:
        """Balanced pack at 32GB should use small whisper."""
        result = self._recommend()
        balanced = _pack_by_id(result["packs"], "balanced")
        assert balanced is not None
        speech_plans = [e for e in balanced["plan"] if e.get("job") == "speech"]
        assert len(speech_plans) == 1
        assert speech_plans[0]["whisper_name"] == "small"


# ── (c) Machine with reachable endpoint + legacy GGUF ────────────────────

class TestEndpointAndLegacyGGUF:
    """Fixture truth table: a machine with a reachable known endpoint + legacy GGUF."""

    ENDPOINT = {
        "id": "lab-server-43",
        "name": "Home lab (.43)",
        "base_url": "http://192.168.1.43:8080",
        "model": "qwen3.5-8b",
    }

    LEGACY_GGUF = "~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf"
    LEGACY_GGUF_LABEL = "Qwen3.5-9B-Instruct-Q6_K.gguf"

    def _recommend(self, *, reachable: bool = True) -> dict[str, Any]:
        def probe(url: str) -> bool:
            return reachable and url == "http://192.168.1.43:8080"

        return recommend(
            hardware=_hw(apple_silicon=True, total_memory_bytes=_16GB),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[self.ENDPOINT],
            legacy_gguf_path=self.LEGACY_GGUF,
            legacy_gguf_label=self.LEGACY_GGUF_LABEL,
            has_llama_cpp=True,
            has_mlx=True,
            probe=probe,
        )

    def test_reachable_endpoint_becomes_pack_ingredient(self) -> None:
        """When the endpoint is reachable, it appears as pack ingredients with provenance."""
        result = self._recommend(reachable=True)
        for pack in result["packs"]:
            group_lines = [l for l in pack["display_lines"] if "group_id" in l]
            # All groups should use the endpoint since it's priority 1
            for line in group_lines:
                assert line["provenance"] == "known_endpoint"
                assert "192.168.1.43:8080" in line["source_label"]

    def test_endpoint_provenance_in_facts(self) -> None:
        result = self._recommend(reachable=True)
        facts = result["facts"]
        assert len(facts["endpoints"]) == 1
        ep = facts["endpoints"][0]
        assert ep["reachable"] is True
        assert ep["base_url"] == "http://192.168.1.43:8080"
        assert ep["name"] == "Home lab (.43)"

    def test_unreachable_endpoint_excluded_with_reason(self) -> None:
        """Unreachable endpoint has a reason and is not used in packs."""
        result = self._recommend(reachable=False)
        facts = result["facts"]
        assert len(facts["endpoints"]) == 1
        ep = facts["endpoints"][0]
        assert ep["reachable"] is False
        assert ep["reason"] is not None  # Has a reason

        # Since the endpoint is unreachable, packs should fall back to
        # legacy GGUF or catalog presets
        for pack in result["packs"]:
            group_lines = [l for l in pack["display_lines"] if "group_id" in l]
            for line in group_lines:
                # Should use legacy_config (priority 2) since endpoint is down
                assert line["provenance"] in ("legacy_config", "catalog_preset")

    def test_unreachable_uses_legacy_gguf(self) -> None:
        """When endpoint is unreachable, falls back to legacy GGUF."""
        result = self._recommend(reachable=False)
        for pack in result["packs"]:
            group_lines = [l for l in pack["display_lines"] if "group_id" in l]
            # Legacy GGUF is priority 2
            for line in group_lines:
                assert line["provenance"] == "legacy_config"
                assert "Legacy local model" in line["source_label"] or self.LEGACY_GGUF_LABEL in line["source_label"]

    def test_legacy_gguf_path_in_facts(self) -> None:
        result = self._recommend(reachable=False)
        facts = result["facts"]
        assert facts["legacy_gguf_path"] == self.LEGACY_GGUF
        assert facts["legacy_gguf_label"] == self.LEGACY_GGUF_LABEL


# ── Completeness law ─────────────────────────────────────────────────────

class TestCompletenessLaw:
    """A pack is always COMPLETE (all seven groups + speech + TTS) or not offered."""

    def test_incomplete_pack_not_offered(self) -> None:
        """With no runtime and no endpoints, no packs can be completed."""
        result = recommend(
            hardware=_hw(apple_silicon=True, total_memory_bytes=_16GB),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[],
            has_llama_cpp=False,  # No llama.cpp
            has_mlx=False,
            probe=_no_probe,
        )
        # Without llama.cpp and no endpoints, no pack can be completed
        assert len(result["packs"]) == 0

    def test_every_offered_pack_has_all_groups(self) -> None:
        """Every pack that IS offered covers all seven groups."""
        result = recommend(
            hardware=_hw(apple_silicon=True, total_memory_bytes=_16GB),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[],
            has_llama_cpp=True,
            probe=_no_probe,
        )
        expected_groups = {gid for gid, _ in ASSIGNMENT_GROUPS}
        for pack in result["packs"]:
            covered = _group_ids_from_pack(pack)
            assert covered == expected_groups, f"Pack {pack['id']} is incomplete: {expected_groups - covered}"
            jobs = _jobs_from_pack(pack)
            assert "speech" in jobs
            assert "tts" in jobs

    def test_pack_with_only_endpoint_is_complete(self) -> None:
        """An endpoint-only pack (no local runtimes) is still complete."""
        ep = {"id": "test-ep", "name": "Test", "base_url": "http://test:8080"}
        result = recommend(
            hardware=_hw(apple_silicon=False, total_memory_bytes=_8GB),
            catalog_entries=[],  # No catalog entries
            known_endpoints=[ep],
            has_llama_cpp=False,
            has_mlx=False,
            probe=_always_reachable,
        )
        assert len(result["packs"]) >= 1
        for pack in result["packs"]:
            covered = _group_ids_from_pack(pack)
            expected_groups = {gid for gid, _ in ASSIGNMENT_GROUPS}
            assert covered == expected_groups


# ── Probe boundary ───────────────────────────────────────────────────────

class TestProbeBoundary:
    """Only explicitly-known endpoints are probed (no network-wide scan)."""

    def test_only_known_endpoints_probed(self) -> None:
        """The probe function is called ONLY with URLs from known_endpoints."""
        probed: list[str] = []

        def spy_probe(base_url: str) -> bool:
            probed.append(base_url)
            return True

        endpoints = [
            {"id": "ep1", "name": "Server 1", "base_url": "http://192.168.1.43:8080"},
            {"id": "ep2", "name": "Server 2", "base_url": "http://10.0.0.5:8080"},
        ]
        recommend(
            hardware=_hw(),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=endpoints,
            has_llama_cpp=True,
            probe=spy_probe,
        )
        # Exactly those two URLs were probed, and no others
        assert sorted(probed) == sorted([
            "http://192.168.1.43:8080",
            "http://10.0.0.5:8080",
        ])

    def test_no_probing_without_endpoints(self) -> None:
        """With no endpoints, the probe is never called."""
        probed: list[str] = []

        def spy_probe(base_url: str) -> bool:
            probed.append(base_url)
            return True

        recommend(
            hardware=_hw(),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[],
            has_llama_cpp=True,
            probe=spy_probe,
        )
        assert probed == []

    def test_reachable_unreachable_pair(self) -> None:
        """Feed a fake reachable/unreachable pair, verify both are probed."""
        probed: list[str] = []

        def selective_probe(base_url: str) -> bool:
            probed.append(base_url)
            return base_url == "http://reachable:8080"

        endpoints = [
            {"id": "good", "name": "Reachable", "base_url": "http://reachable:8080"},
            {"id": "bad", "name": "Unreachable", "base_url": "http://unreachable:8080"},
        ]
        result = recommend(
            hardware=_hw(),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=endpoints,
            has_llama_cpp=True,
            probe=selective_probe,
        )
        # Both probed
        assert len(probed) == 2
        assert "http://reachable:8080" in probed
        assert "http://unreachable:8080" in probed
        # Facts reflect both
        reachable = [e for e in result["facts"]["endpoints"] if e["reachable"]]
        unreachable = [e for e in result["facts"]["endpoints"] if not e["reachable"]]
        assert len(reachable) == 1
        assert reachable[0]["id"] == "good"
        assert len(unreachable) == 1
        assert unreachable[0]["id"] == "bad"
        assert unreachable[0]["reason"] is not None


# ── No-credential cloud exclusion ────────────────────────────────────────

class TestNoCredentialCloudExclusion:
    """Cloud path never appears in a pack unless a credential already exists."""

    def test_no_cloud_without_credential(self) -> None:
        """Without has_cloud_credential, no pack uses cloud sources."""
        result = recommend(
            hardware=_hw(),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[],
            has_llama_cpp=True,
            has_cloud_credential=False,
            probe=_no_probe,
        )
        for pack in result["packs"]:
            for entry in pack["plan"]:
                assert entry.get("kind") != "cloud", (
                    f"Pack {pack['id']} has a cloud entry without credential"
                )

    def test_facts_record_no_credential(self) -> None:
        result = recommend(
            hardware=_hw(),
            catalog_entries=BOTH_PRESETS,
            known_endpoints=[],
            has_llama_cpp=True,
            has_cloud_credential=False,
            probe=_no_probe,
        )
        assert result["facts"]["has_cloud_credential"] is False


# ── Utility tests ────────────────────────────────────────────────────────

class TestHumanSize:
    def test_bytes(self) -> None:
        assert _human_size(500) == "500 B"

    def test_kilobytes(self) -> None:
        assert _human_size(1024) == "1 KB"

    def test_megabytes(self) -> None:
        assert _human_size(142_000_000) == "135 MB"

    def test_gigabytes(self) -> None:
        assert _human_size(2_740_937_888) == "2.6 GB"


# ── Route test through real app ──────────────────────────────────────────

class TestFrontDoorRoute:
    """Integration: GET /api/front-door/recommendation via the real FastAPI app."""

    def _client(self, tmp_path: Path) -> Any:
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient

        from holdspeak.config import Config
        from holdspeak.db import Database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
        from holdspeak.web.context import WebContext
        from holdspeak.web.routes.front_door import build_front_door_router

        OWNER = Principal(PrincipalKind.OWNER, "front-door-test-owner")
        AGENT = Principal(PrincipalKind.AGENT, "front-door-test-agent")

        db = Database(tmp_path / "front-door.db")
        setup = InferenceSetupApplicationService(
            db,
            config_provider=Config,
            home_provider=lambda: tmp_path / "home",
        )
        app = FastAPI()

        @app.middleware("http")
        async def principal(request: Request, call_next):
            request.state.principal = OWNER if request.headers.get("x-owner") == "yes" else AGENT
            return await call_next(request)

        web_ctx = WebContext(
            get_state=lambda: {},
            inference_setup_service=setup,
        )
        app.include_router(build_front_door_router(web_ctx))
        return TestClient(app)

    def test_owner_gets_recommendation(self, tmp_path: Path) -> None:
        """Owner can GET the recommendation endpoint."""
        client = self._client(tmp_path)
        response = client.get("/api/front-door/recommendation", headers={"x-owner": "yes"})
        assert response.status_code == 200
        data = response.json()
        assert "packs" in data
        assert "facts" in data
        assert isinstance(data["packs"], list)
        assert isinstance(data["facts"], dict)

    def test_non_owner_denied(self, tmp_path: Path) -> None:
        """Non-owner gets 403."""
        client = self._client(tmp_path)
        response = client.get("/api/front-door/recommendation")
        assert response.status_code == 403
        assert response.json()["code"] == "front_door_owner_required"

    def test_facts_include_hardware_info(self, tmp_path: Path) -> None:
        """Facts include hardware detection."""
        client = self._client(tmp_path)
        response = client.get("/api/front-door/recommendation", headers={"x-owner": "yes"})
        assert response.status_code == 200
        facts = response.json()["facts"]
        assert "apple_silicon" in facts
        assert "total_memory_bytes" in facts
        assert "endpoints" in facts
        assert "probed_urls" in facts
