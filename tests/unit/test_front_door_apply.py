"""HS-156-02 -- Front Door apply engine unit tests.

Plan execution, idempotency, fault injection, fence (no-parallel-authority),
and the LAN endpoint provenance test.
"""
from __future__ import annotations

import ast
import inspect
import json
import re
import textwrap
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.services.front_door_service import (
    ASSIGNMENT_GROUPS,
    ITEM_DONE,
    ITEM_FAILED,
    ITEM_QUEUED,
    ITEM_RUNNING,
    PACK_BALANCED,
    PACK_FULL,
    PACK_LIGHT,
    PLAN_DONE,
    PLAN_FAILED,
    PLAN_RUNNING,
    _make_apply_items,
    apply_pack,
    recommend,
)


# ── Fixture helpers ──────────────────────────────────────────────────────

_16GB = 16 * 1024 ** 3
_32GB = 32 * 1024 ** 3

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

ENDPOINT_43 = {
    "id": "lab-server-43",
    "name": "Home lab (.43)",
    "base_url": "http://192.168.1.43:8080",
    "model": "qwen3.5-8b",
}


def _hw(*, apple_silicon: bool = True, total_memory_bytes: int = _16GB) -> dict[str, Any]:
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


def _endpoint_pack() -> dict[str, Any]:
    """Build a pack that uses the .43 endpoint for all groups."""
    result = recommend(
        hardware=_hw(),
        catalog_entries=BOTH_PRESETS,
        known_endpoints=[ENDPOINT_43],
        has_llama_cpp=True,
        has_mlx=True,
        probe=lambda url: True,
    )
    balanced = next(p for p in result["packs"] if p["id"] == "balanced")
    return balanced


def _catalog_pack() -> dict[str, Any]:
    """Build a pack that downloads catalog presets for all groups."""
    result = recommend(
        hardware=_hw(),
        catalog_entries=BOTH_PRESETS,
        known_endpoints=[],
        has_llama_cpp=True,
        has_mlx=True,
        probe=lambda url: False,
    )
    balanced = next(p for p in result["packs"] if p["id"] == "balanced")
    return balanced


class FakeDB:
    """Minimal in-memory fake for the Database + FrontDoorApplyRepository."""

    class FakeFrontDoorRepo:
        def __init__(self):
            self._plans: dict[str, dict[str, Any]] = {}

        def create_plan(self, *, pack_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
            plan_id = "fdap_" + uuid.uuid4().hex
            now = "2026-08-30T12:00:00.000000Z"
            plan = {
                "id": plan_id,
                "pack_id": pack_id,
                "status": "running",
                "items": items,
                "created_at": now,
                "updated_at": now,
            }
            self._plans[plan_id] = plan
            return dict(plan)

        def get_plan(self, plan_id: str) -> dict[str, Any] | None:
            plan = self._plans.get(plan_id)
            return dict(plan) if plan else None

        def get_latest_plan(self) -> dict[str, Any] | None:
            if not self._plans:
                return None
            latest = max(self._plans.values(), key=lambda p: p["created_at"])
            return dict(latest)

        def update_plan(self, plan_id: str, *, status: str, items: list[dict[str, Any]]) -> None:
            if plan_id in self._plans:
                self._plans[plan_id]["status"] = status
                self._plans[plan_id]["items"] = items

        def get_plan_by_pack(self, pack_id: str) -> dict[str, Any] | None:
            for plan in self._plans.values():
                if plan["pack_id"] == pack_id:
                    return dict(plan)
            return None

    def __init__(self):
        self.front_door = self.FakeFrontDoorRepo()


class FakeModelLibraryService:
    """Tracks calls to download and define_endpoint without hitting real services."""

    def __init__(self, *, fail_on_call: int | None = None):
        self.downloads: list[dict[str, Any]] = []
        self.endpoints: list[dict[str, Any]] = []
        self._call_count = 0
        self._fail_on_call = fail_on_call

    def _maybe_fail(self):
        self._call_count += 1
        if self._fail_on_call is not None and self._call_count >= self._fail_on_call:
            raise RuntimeError(f"Injected failure on call {self._call_count}")

    def download(self, principal: Any, body: dict[str, Any]) -> dict[str, Any]:
        self._maybe_fail()
        self.downloads.append(body)
        return {
            "receipt": {
                "kind": "model_library_add",
                "message": "Added to the Model Library.",
                "assignments_unchanged": True,
            },
            "acquisition": {
                "catalog_id": body.get("catalog_id"),
                "status": "ready",
            },
        }

    def define_endpoint(self, principal: Any, draft: dict[str, Any], secret: Any = None) -> dict[str, Any]:
        self._maybe_fail()
        self.endpoints.append(draft)
        return {
            "receipt": {
                "kind": "model_library_provider",
                "message": "Endpoint defined.",
            },
            "profile": {
                "profile_id": draft["profile_id"],
                "revision": 1,
            },
        }

    @staticmethod
    def require_owner(principal):
        pass


class FakeAssignmentService:
    """Tracks calls to set_assignment without hitting real DB."""

    def __init__(self, *, fail_on_group: str | None = None):
        self.assignments: list[dict[str, Any]] = []
        self._fail_on_group = fail_on_group

    def set_assignment(self, principal: Any, body: dict[str, Any]) -> dict[str, Any]:
        group_id = body.get("scope", {}).get("group_id", "")
        if self._fail_on_group and group_id == self._fail_on_group:
            raise RuntimeError(f"Injected assignment failure for group {group_id}")
        self.assignments.append(body)
        return {
            "schema": "InferenceAssignment@1",
            "scope": body["scope"],
            "revision": body["expected_revision"] + 1,
            "sha256": "sha256:test",
        }

    def get_assignment(self, principal: Any, scope: dict[str, Any]) -> dict[str, Any]:
        # Return revision 0 (no existing assignment)
        from holdspeak.services.errors import NotFound
        raise NotFound("inference assignment", f"group:{scope.get('group_id', '')}")


class FakePrincipal:
    def __init__(self):
        from holdspeak.principals import PrincipalKind
        self.kind = PrincipalKind.OWNER
        self.identity = "test-owner"


OWNER = FakePrincipal()


# ── Test classes ─────────────────────────────────────────────────────────

class TestMakeApplyItems:
    """Plan entry conversion to durable apply items."""

    def test_all_items_start_queued(self) -> None:
        entries = [{"kind": "endpoint", "group_id": "meetings"}]
        items = _make_apply_items(entries)
        assert len(items) == 1
        assert items[0]["status"] == ITEM_QUEUED
        assert items[0]["ordinal"] == 0

    def test_preserves_entry_data(self) -> None:
        entries = [
            {"kind": "catalog_download", "preset_id": "p1", "group_id": "agents_tools"},
            {"kind": "whisper_model", "job": "speech"},
        ]
        items = _make_apply_items(entries)
        assert len(items) == 2
        assert items[0]["entry"]["kind"] == "catalog_download"
        assert items[1]["entry"]["kind"] == "whisper_model"


class TestApplyEndpointPack:
    """Apply a pack whose groups all use a known LAN endpoint."""

    def test_endpoint_pack_reaches_done(self) -> None:
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result["status"] == PLAN_DONE

    def test_endpoint_defined_for_each_unique_endpoint(self) -> None:
        """All seven group items share one endpoint, so define_endpoint is called once per unique plan entry with kind=endpoint."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        # Each group gets its own define_endpoint call (each plan entry is independent)
        endpoint_items = [
            e for e in pack["plan"] if e.get("kind") == "endpoint"
        ]
        assert len(lib.endpoints) == len(endpoint_items)

    def test_assignments_set_for_all_groups(self) -> None:
        """All seven groups get assigned."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        assigned_groups = {
            a["scope"]["group_id"] for a in assign.assignments
        }
        expected_groups = {gid for gid, _ in ASSIGNMENT_GROUPS}
        assert assigned_groups == expected_groups

    def test_plan_persisted_in_db(self) -> None:
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        stored = db.front_door.get_plan(result["plan_id"])
        assert stored is not None
        assert stored["status"] == PLAN_DONE

    def test_receipts_for_every_step(self) -> None:
        """Every item in the plan has a receipt after completion."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        for item in result["items"]:
            assert item["status"] == ITEM_DONE, f"Item {item['ordinal']} not done: {item['status']}"
            assert item["receipt"] is not None, f"Item {item['ordinal']} has no receipt"

    def test_endpoint_provenance_label(self) -> None:
        """The LAN endpoint wires via define-endpoint with provenance."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        # The define_endpoint call should include the endpoint URL
        assert len(lib.endpoints) > 0
        for draft in lib.endpoints:
            assert "192.168.1.43" in draft["endpoint"]
            assert draft["provider_family"] == "openai_compatible"
            assert "Front Door" in draft["label"]


class TestApplyCatalogPack:
    """Apply a pack that downloads catalog presets."""

    def test_catalog_pack_reaches_done(self) -> None:
        pack = _catalog_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result["status"] == PLAN_DONE

    def test_downloads_triggered_for_catalog_entries(self) -> None:
        pack = _catalog_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        download_items = [
            e for e in pack["plan"] if e.get("kind") == "catalog_download"
        ]
        assert len(lib.downloads) == len(download_items)
        for dl in lib.downloads:
            assert "catalog_id" in dl
            assert dl["catalog_revision"] == 4


class TestFaultInjection:
    """Kill the apply mid-plan and verify resumability."""

    def test_failure_names_the_error(self) -> None:
        """Fault injection after item N -> plan shows the failure."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService(fail_on_call=3)
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result["status"] == PLAN_FAILED
        failed_items = [i for i in result["items"] if i["status"] == ITEM_FAILED]
        assert len(failed_items) == 1
        assert failed_items[0]["error"] is not None
        assert "Injected failure" in failed_items[0]["error"]

    def test_reapply_completes_remainder(self) -> None:
        """Re-apply after failure completes the unfinished items."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService(fail_on_call=3)
        assign = FakeAssignmentService()

        # First apply fails
        result1 = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result1["status"] == PLAN_FAILED
        done_count_before = sum(1 for i in result1["items"] if i["status"] == ITEM_DONE)

        # Replace with a working service and re-apply
        lib2 = FakeModelLibraryService()
        assign2 = FakeAssignmentService()
        result2 = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib2,
            assignment_service=assign2,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result2["status"] == PLAN_DONE

    def test_nothing_double_created(self) -> None:
        """Items completed before the fault are not re-executed on resume."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib_failing = FakeModelLibraryService(fail_on_call=4)
        assign = FakeAssignmentService()

        # First apply: some succeed, then fail
        result1 = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib_failing,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result1["status"] == PLAN_FAILED
        first_endpoint_calls = len(lib_failing.endpoints)

        # Re-apply with working service
        lib_working = FakeModelLibraryService()
        assign2 = FakeAssignmentService()
        result2 = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib_working,
            assignment_service=assign2,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result2["status"] == PLAN_DONE
        # The working service should only get calls for the REMAINING items,
        # not the ones already done
        second_endpoint_calls = len(lib_working.endpoints)
        total_endpoint_items = sum(
            1 for e in pack["plan"] if e.get("kind") == "endpoint"
        )
        assert first_endpoint_calls + second_endpoint_calls == total_endpoint_items


class TestAssignmentFaultInjection:
    """Assignment-specific fault injection."""

    def test_assignment_failure_leaves_plan_failed(self) -> None:
        """If assignment fails, the plan records the failure."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService(fail_on_group="meetings")
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        assert result["status"] == PLAN_FAILED
        failed_items = [i for i in result["items"] if i["status"] == ITEM_FAILED]
        assert len(failed_items) >= 1


class TestNoParallelAuthorityFence:
    """The apply path contains no direct DB writes to library/assignment tables."""

    def _scan_apply_source(self) -> list[str]:
        """Scan the apply engine code for direct table writes."""
        source_path = Path(__file__).resolve().parents[2] / "holdspeak" / "services" / "front_door_service.py"
        source = source_path.read_text()

        # Find the apply engine section (after "Apply engine" comment)
        marker = "# -- Apply engine (HS-156-02)"
        idx = source.find(marker)
        if idx < 0:
            # Try alternate marker
            marker = "Apply engine"
            idx = source.find(marker)
        if idx < 0:
            pytest.fail("Could not find apply engine section in front_door_service.py")

        apply_source = source[idx:]
        violations: list[str] = []

        # Forbidden patterns: direct SQL writes to assignment or library tables
        forbidden_tables = [
            "inference_assignments",
            "inference_assignment_heads",
            "inference_assignment_revisions",
            "model_profile_revisions",
            "model_profile_binding_heads",
            "inference_model_acquisitions",
            "inference_deployments",
            "deployment_revisions",
        ]

        for i, line in enumerate(apply_source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            lowered = stripped.lower()
            for table in forbidden_tables:
                if table in lowered and ("insert" in lowered or "update" in lowered or "delete" in lowered):
                    violations.append(f"line {i}: {stripped[:80]}")
            # Also check for conn.execute with INSERT/UPDATE
            if "conn.execute" in stripped and ("INSERT" in stripped or "UPDATE" in stripped or "DELETE" in stripped):
                # Allow writes to front_door_apply_plans (that is our own table)
                if "front_door_apply_plans" not in stripped:
                    violations.append(f"line {i}: direct DB write: {stripped[:80]}")

        return violations

    def test_no_direct_db_writes_to_library_or_assignment_tables(self) -> None:
        """The apply engine uses only service calls, never direct DB writes."""
        violations = self._scan_apply_source()
        if violations:
            msg = (
                "The apply engine contains direct DB writes to library/assignment tables.\n"
                "The apply path must use only the existing service seams.\n\n"
                "Violations:\n"
            )
            for v in violations:
                msg += f"  {v}\n"
            pytest.fail(msg)

    def test_apply_functions_call_service_methods_only(self) -> None:
        """Verify the apply functions reference service.download, service.define_endpoint,
        and assignment_service.set_assignment -- not raw DB access."""
        source_path = Path(__file__).resolve().parents[2] / "holdspeak" / "services" / "front_door_service.py"
        source = source_path.read_text()

        marker = "Apply engine"
        idx = source.find(marker)
        assert idx >= 0, "Apply engine section not found"

        apply_source = source[idx:]

        # The apply engine should reference service methods
        assert "model_library_service" in apply_source
        assert "assignment_service" in apply_source
        assert "define_endpoint" in apply_source
        assert "set_assignment" in apply_source or "apply_starter_bundle" in apply_source

        # It should NOT import raw DB models or connection helpers
        for forbidden in ["_connection()", "conn.execute"]:
            if forbidden in apply_source:
                # Check it is not in the front_door repo (our own persistence is ok)
                # The apply engine delegates to db.front_door which is its own table
                lines_with = [
                    line for line in apply_source.splitlines()
                    if forbidden in line and "front_door" not in line
                ]
                assert not lines_with, f"Apply engine uses forbidden pattern '{forbidden}': {lines_with}"


class TestLANEndpointProvenance:
    """The .43-shaped ingredient wires via define-endpoint with provenance."""

    def test_endpoint_carries_provenance_label(self) -> None:
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        # Every define_endpoint call should carry a label with the URL
        for draft in lib.endpoints:
            assert "label" in draft
            assert "Front Door" in draft["label"]
            assert draft["provider_family"] == "openai_compatible"
            # The endpoint URL should have /v1 appended
            assert draft["endpoint"].endswith("/v1")

    def test_endpoint_profile_id_is_deterministic(self) -> None:
        """The profile_id includes the endpoint id for traceability."""
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        for draft in lib.endpoints:
            assert draft["profile_id"].startswith("front-door-ep-")


class TestSpeechAndTTSBuiltIn:
    """Speech and TTS items are built-in and need no external provisioning."""

    def test_builtin_items_marked_done_immediately(self) -> None:
        pack = _endpoint_pack()
        db = FakeDB()
        lib = FakeModelLibraryService()
        assign = FakeAssignmentService()
        result = apply_pack(
            pack=pack,
            db=db,
            model_library_service=lib,
            assignment_service=assign,
            principal=OWNER,
            catalog_revision=4,
        )
        # Find the whisper and kokoro items
        for item in result["items"]:
            entry_kind = item.get("entry", {}).get("kind", "")
            if entry_kind in ("whisper_model", "kokoro_tts"):
                assert item["status"] == ITEM_DONE
                assert item["receipt"] is not None


class TestApplyRoute:
    """Integration: POST /api/front-door/apply via the real FastAPI app."""

    def _client(self, tmp_path: Path) -> Any:
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient

        from holdspeak.db import Database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
        from holdspeak.web.context import WebContext
        from holdspeak.web.routes.front_door import build_front_door_router

        OWNER = Principal(PrincipalKind.OWNER, "apply-test-owner")
        AGENT = Principal(PrincipalKind.AGENT, "apply-test-agent")

        db = Database(tmp_path / "apply-test.db")
        setup = InferenceSetupApplicationService(
            db,
            config_provider=lambda: __import__("holdspeak.config", fromlist=["Config"]).Config(),
            home_provider=lambda: tmp_path / "home",
        )
        app = FastAPI()

        @app.middleware("http")
        async def principal_middleware(request: Request, call_next):
            request.state.principal = OWNER if request.headers.get("x-owner") == "yes" else AGENT
            return await call_next(request)

        web_ctx = WebContext(
            get_state=lambda: {},
            inference_setup_service=setup,
            model_library_service=FakeModelLibraryService(),
            inference_assignment_service=FakeAssignmentService(),
        )
        app.include_router(build_front_door_router(web_ctx))
        return TestClient(app)

    def test_post_apply_non_owner_denied(self, tmp_path: Path) -> None:
        client = self._client(tmp_path)
        response = client.post(
            "/api/front-door/apply",
            json={"pack_id": "balanced"},
        )
        assert response.status_code == 403

    def test_post_apply_missing_pack_id(self, tmp_path: Path) -> None:
        client = self._client(tmp_path)
        response = client.post(
            "/api/front-door/apply",
            json={},
            headers={"x-owner": "yes"},
        )
        assert response.status_code == 400

    def test_get_apply_no_plan(self, tmp_path: Path) -> None:
        client = self._client(tmp_path)
        response = client.get(
            "/api/front-door/apply",
            headers={"x-owner": "yes"},
        )
        assert response.status_code == 200
        assert response.json()["plan"] is None

    def test_get_apply_non_owner_denied(self, tmp_path: Path) -> None:
        client = self._client(tmp_path)
        response = client.get("/api/front-door/apply")
        assert response.status_code == 403


class TestPlanPersistence:
    """Plan persistence through the DB repository."""

    def test_plan_created_and_readable(self, tmp_path: Path) -> None:
        from holdspeak.db import Database
        db = Database(tmp_path / "persist.db")
        items = [{"ordinal": 0, "entry": {"kind": "endpoint"}, "status": "queued", "receipt": None, "error": None}]
        plan = db.front_door.create_plan(pack_id="balanced", items=items)
        assert plan["id"].startswith("fdap_")
        assert plan["pack_id"] == "balanced"
        assert plan["status"] == "running"

        read_back = db.front_door.get_plan(plan["id"])
        assert read_back is not None
        assert read_back["id"] == plan["id"]
        assert read_back["items"] == items

    def test_plan_update_persists(self, tmp_path: Path) -> None:
        from holdspeak.db import Database
        db = Database(tmp_path / "update.db")
        items = [{"ordinal": 0, "entry": {"kind": "endpoint"}, "status": "queued", "receipt": None, "error": None}]
        plan = db.front_door.create_plan(pack_id="balanced", items=items)

        items[0]["status"] = "done"
        db.front_door.update_plan(plan["id"], status="done", items=items)

        read_back = db.front_door.get_plan(plan["id"])
        assert read_back["status"] == "done"
        assert read_back["items"][0]["status"] == "done"

    def test_latest_plan(self, tmp_path: Path) -> None:
        from holdspeak.db import Database
        db = Database(tmp_path / "latest.db")
        items = [{"ordinal": 0, "entry": {"kind": "test"}, "status": "queued", "receipt": None, "error": None}]
        db.front_door.create_plan(pack_id="light", items=items)
        plan2 = db.front_door.create_plan(pack_id="balanced", items=items)

        latest = db.front_door.get_latest_plan()
        assert latest is not None
        assert latest["pack_id"] == plan2["pack_id"]

    def test_plan_by_pack(self, tmp_path: Path) -> None:
        from holdspeak.db import Database
        db = Database(tmp_path / "bypack.db")
        items = [{"ordinal": 0, "entry": {"kind": "test"}, "status": "queued", "receipt": None, "error": None}]
        db.front_door.create_plan(pack_id="light", items=items)
        db.front_door.create_plan(pack_id="balanced", items=items)

        result = db.front_door.get_plan_by_pack("light")
        assert result is not None
        assert result["pack_id"] == "light"
