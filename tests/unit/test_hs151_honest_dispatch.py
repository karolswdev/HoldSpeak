"""HS-151-01/02 — the honest dispatch: structured output, 400-fallback, named owners.

A stub OpenAI-compatible server that mimics the .43 pin (server-level
``--json-schema {"line": ...}`` pin that swallows prompt-level JSON pleas):
bare requests get ``{"line": "..."}``; request-level ``json_schema`` is honoured.

Tests:
  1. The OLD shape (no response_format) → {"line"} → empty/failed intel.
  2. The NEW shape (with response_format) → structured intel succeeds.
  3. The 400-reject path fires the named signal exactly once.
  4. The _extract_json line-recovery heuristic (counsel S1).
  5. Named-owner parsing pins (story 02).
  6. Named-owner canary: stub server round-trip with named owners.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.request import Request, urlopen

import pytest

import holdspeak.intel as intel_module
from holdspeak.intel import (
    INTEL_JSON_SCHEMA,
    INTEL_SCHEMA,
    MeetingIntel,
    _coerce_action_items,
    _extract_json,
    intel_response_format,
)
from holdspeak.intel.engine import (
    _COMPAT_NO_RESPONSE_FORMAT,
    _response_format_compatibility_retry,
    endpoint_rejects_response_format,
    forget_endpoint_dialects,
)
from holdspeak.intel.models import ActionItem
from holdspeak.kernel.provider_signals import ProviderCompatibilityRetry

pytestmark = pytest.mark.timeout(30, method="signal")


# ------------------------------------------------------------------- constants

GOOD_INTEL = {
    "topics": ["Budget review", "Q3 planning"],
    "action_items": [
        {"task": "Send the RFC", "owner": "Ewa", "due": "Friday"},
        {"task": "Update runbook", "owner": "Marek", "due": None},
    ],
    "summary": "Ewa and Marek discussed the budget.",
}

LINE_RESPONSE = {"line": "Ewa will send the RFC, and Marek will update the runbook."}

LINE_WITH_EMBEDDED_ACTIONS = {
    "line": 'action_items: [{"task": "Send RFC", "owner": "Ewa", "due": null}], summary: "discussed the budget"'
}

TRANSCRIPT = (
    "Ewa: OK so I'll send the RFC by Friday.\n"
    "Marek: And I'll update the runbook.\n"
    "Ewa: Great, let's review the budget numbers too.\n"
)

NAMED_OWNER_TRANSCRIPT = (
    "Ewa: I'll handle the deployment.\n"
    "Marek: And Jan Kowalski will review the architecture.\n"
    "Ewa: Sounds good, I'll also update the runbook.\n"
)

NAMED_OWNER_INTEL = {
    "topics": ["Deployment", "Architecture review"],
    "action_items": [
        {"task": "Handle deployment", "owner": "Ewa", "due": None},
        {"task": "Review architecture", "owner": "Jan Kowalski", "due": None},
        {"task": "Update runbook", "owner": "Me", "due": None},
    ],
    "summary": "Ewa, Marek, and Jan discussed deployment and architecture.",
}


# --------------------------------------------------------- stub pin server

class _PinServerHandler(BaseHTTPRequestHandler):
    """Mimics the .43 server-level ``--json-schema {"line": ...}`` pin.

    - Bare request (no ``response_format``) returns ``{"line": "..."}``.
    - Request WITH ``response_format.json_schema`` returns the GOOD_INTEL shape.
    - A ``reject_response_format`` class attr can force a 400 for testing.
    """

    reject_response_format: bool = False
    named_owner_mode: bool = False

    def do_POST(self) -> None:  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("content-length") or "0"))
        body = json.loads(raw.decode("utf-8"))

        if "response_format" in body:
            if self.reject_response_format:
                error = json.dumps({
                    "error": {
                        "message": "Unsupported parameter: response_format with json_schema",
                        "type": "invalid_request_error",
                    }
                }).encode("utf-8")
                self.send_response(400)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(error)))
                self.end_headers()
                self.wfile.write(error)
                return
            # Honour request-level json_schema: return structured intel.
            intel = NAMED_OWNER_INTEL if self.named_owner_mode else GOOD_INTEL
            payload = json.dumps({
                "choices": [{"message": {"content": json.dumps(intel)}}]
            }).encode("utf-8")
        else:
            # Bare request: the server-level pin swallows the prompt.
            payload = json.dumps({
                "choices": [{"message": {"content": json.dumps(LINE_RESPONSE)}}]
            }).encode("utf-8")

        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # silence


class _HttpCompletions:
    """Minimal OpenAI-like completions object for the stub server."""

    def __init__(self, *, base_url: str, api_key: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def create(self, **kwargs: Any) -> Any:
        import types

        is_stream = kwargs.pop("stream", False)
        data = json.dumps(kwargs, default=str).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                result = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            # Propagate HTTP errors with status codes for the compat retry.
            from urllib.error import HTTPError

            if isinstance(exc, HTTPError):
                body = exc.read().decode("utf-8", errors="replace")
                error = type(exc)(
                    exc.url, exc.code, f"{body}", exc.headers, exc.fp
                )
                error.status_code = exc.code
                raise error from exc
            raise

        # Build a SimpleNamespace that looks like an openai.ChatCompletion.
        choices = result.get("choices", [])
        content = choices[0]["message"]["content"] if choices else ""

        if is_stream:
            # Simulate streaming: yield the content as a single chunk.
            def _stream():
                yield types.SimpleNamespace(
                    choices=[
                        types.SimpleNamespace(
                            delta=types.SimpleNamespace(content=content)
                        )
                    ]
                )
            return _stream()

        ns_choices = []
        for ch in choices:
            msg = ch.get("message", {})
            ns_choices.append(
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content=msg.get("content", ""))
                )
            )
        return types.SimpleNamespace(choices=ns_choices)


class _HttpClient:
    """Minimal OpenAI-like client for the stub server."""

    def __init__(self, **kwargs: Any) -> None:
        self.chat = type(
            "_Chat",
            (),
            {
                "completions": _HttpCompletions(
                    base_url=kwargs.get("base_url", ""),
                    api_key=kwargs.get("api_key", ""),
                    timeout=kwargs.get("timeout", 10),
                )
            },
        )()


@pytest.fixture
def pin_server():
    """Start and yield a stub pin server, then shut it down."""
    _PinServerHandler.reject_response_format = False
    _PinServerHandler.named_owner_mode = False
    server = HTTPServer(("127.0.0.1", 0), _PinServerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def _make_engine(pin_server: HTTPServer, monkeypatch: Any) -> MeetingIntel:
    """Build a MeetingIntel engine pointing at the stub server."""
    port = pin_server.server_port
    monkeypatch.setattr(intel_module, "OpenAI", _HttpClient)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-no-key-required")
    forget_endpoint_dialects()
    return MeetingIntel(
        provider="cloud",
        cloud_model="stub-pin-model",
        cloud_base_url=f"http://127.0.0.1:{port}/v1",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_timeout_seconds=5,
    )


# ------------------------------------------------------------------- schema constant tests

class TestIntelSchemaConstant:
    """The ONE schema constant is well-formed and carries the named-owner shape."""

    def test_schema_has_required_top_level_keys(self) -> None:
        assert set(INTEL_SCHEMA) == {"topics", "action_items", "summary"}

    def test_action_items_carry_named_owner_shape(self) -> None:
        item = INTEL_SCHEMA["action_items"][0]
        assert "task" in item
        assert "owner" in item
        assert "due" in item
        # The owner placeholder carries the named-owner shape (counsel M4).
        assert "name" in item["owner"].lower() or "person" in item["owner"].lower()

    def test_json_schema_matches_constant(self) -> None:
        props = INTEL_JSON_SCHEMA["properties"]
        assert set(props) == {"topics", "action_items", "summary"}
        item_props = props["action_items"]["items"]["properties"]
        assert set(item_props) == {"task", "owner", "due"}
        # owner is string|null (the named-owner shape).
        assert item_props["owner"]["type"] == ["string", "null"]

    def test_response_format_is_well_formed(self) -> None:
        fmt = intel_response_format()
        assert fmt["type"] == "json_schema"
        assert fmt["json_schema"]["name"] == "meeting_intel"
        assert fmt["json_schema"]["strict"] is True
        assert fmt["json_schema"]["schema"] is INTEL_JSON_SCHEMA


# ------------------------------------------------------------------- pin server tests

class TestPinServerOldShape:
    """The OLD shape (no response_format) gets {"line"} and produces empty intel."""

    def test_bare_request_returns_line_response(self, pin_server: HTTPServer) -> None:
        """The stub server returns {"line": ...} for bare requests."""
        port = pin_server.server_port
        data = json.dumps({"model": "m", "messages": []}).encode("utf-8")
        req = Request(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            data=data,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:  # noqa: S310
            result = json.loads(resp.read().decode())
        content = json.loads(result["choices"][0]["message"]["content"])
        assert "line" in content
        assert "action_items" not in content

    def test_old_dispatch_produces_empty_intel(
        self, pin_server: HTTPServer, monkeypatch: Any
    ) -> None:
        """Pre-151 dispatch (no response_format) against the pin → empty intel.

        We simulate the old path by passing response_format=None through the
        engine's _chat_completion_text.
        """
        engine = _make_engine(pin_server, monkeypatch)
        # Manually call the old path: no response_format.
        engine._ensure_model_loaded()
        from holdspeak.intel.parsing import _json_only_messages

        messages = _json_only_messages(TRANSCRIPT)
        raw_text = engine._chat_completion_text(
            messages, temperature=0.2, max_tokens=3000, response_format=None
        )
        data = _extract_json(raw_text)
        # The pin server returns {"line": ...}, which has no action_items.
        assert data is not None
        assert "line" in data
        assert "action_items" not in data or data.get("action_items") == []


class TestPinServerNewShape:
    """The NEW shape (with response_format) succeeds against the pin."""

    def test_new_dispatch_returns_structured_intel(
        self, pin_server: HTTPServer, monkeypatch: Any
    ) -> None:
        engine = _make_engine(pin_server, monkeypatch)
        result = engine.analyze(TRANSCRIPT, stream=False)
        assert result.summary != ""
        assert len(result.action_items) >= 1
        assert any(item.owner == "Ewa" for item in result.action_items)
        assert len(result.topics) >= 1

    def test_streaming_also_sends_response_format(
        self, pin_server: HTTPServer, monkeypatch: Any
    ) -> None:
        engine = _make_engine(pin_server, monkeypatch)
        stream = engine.analyze(TRANSCRIPT, stream=True)
        results = list(stream)
        # The last item is the IntelResult.
        from holdspeak.intel.models import IntelResult as IR

        final = [r for r in results if isinstance(r, IR)]
        assert len(final) == 1
        assert final[0].summary != ""
        assert len(final[0].action_items) >= 1


class TestResponseFormat400Fallback:
    """The 400-reject path fires the named signal exactly once (counsel M1)."""

    def test_400_fires_compat_signal_once(
        self, pin_server: HTTPServer, monkeypatch: Any
    ) -> None:
        _PinServerHandler.reject_response_format = True
        engine = _make_engine(pin_server, monkeypatch)
        engine._ensure_model_loaded()
        from holdspeak.intel.parsing import _json_only_messages

        messages = _json_only_messages(TRANSCRIPT)
        with pytest.raises(ProviderCompatibilityRetry) as exc_info:
            engine._chat_completion_text(
                messages,
                temperature=0.2,
                max_tokens=3000,
                response_format=intel_response_format(),
            )
        assert exc_info.value.mode == "no_response_format"

        # The endpoint is now recorded as rejecting response_format.
        endpoint_key = engine._cloud_endpoint_key()
        assert endpoint_rejects_response_format(endpoint_key)

        # Second call omits response_format and succeeds (returns {"line": ...}).
        raw_text = engine._chat_completion_text(
            messages,
            temperature=0.2,
            max_tokens=3000,
            response_format=intel_response_format(),
        )
        data = _extract_json(raw_text)
        assert data is not None
        # Without response_format, the server returns {"line": ...}.
        assert "line" in data

    def test_compat_retry_detects_response_format_400(self) -> None:
        """The _response_format_compatibility_retry function catches 400s naming response_format."""
        forget_endpoint_dialects()
        exc = type("BadRequest", (Exception,), {"status_code": 400})(
            "Unsupported parameter: response_format with json_schema"
        )
        assert _response_format_compatibility_retry("test:endpoint", exc) is True
        # Second call is a real failure (already speaking the dialect).
        assert _response_format_compatibility_retry("test:endpoint", exc) is False

    def test_compat_retry_ignores_non_400(self) -> None:
        forget_endpoint_dialects()
        exc = type("ServerError", (Exception,), {"status_code": 500})(
            "response_format error"
        )
        assert _response_format_compatibility_retry("test:endpoint2", exc) is False

    def test_compat_retry_ignores_400_without_response_format(self) -> None:
        forget_endpoint_dialects()
        exc = type("BadRequest", (Exception,), {"status_code": 400})(
            "Invalid model parameter"
        )
        assert _response_format_compatibility_retry("test:endpoint3", exc) is False


# --------------------------------------------------------- line-recovery heuristic (counsel S1)

class TestLineRecoveryHeuristic:
    """The _extract_json line-recovery heuristic still fires for bare endpoints."""

    def test_line_with_embedded_action_items_recovers(self) -> None:
        """When the model returns {"line": "... action_items: [...] ..."}, recover."""
        raw = json.dumps(LINE_WITH_EMBEDDED_ACTIONS)
        result = _extract_json(raw)
        assert result is not None
        assert "action_items" in result
        assert isinstance(result["action_items"], list)
        assert len(result["action_items"]) > 0
        assert result["action_items"][0]["task"] == "Send RFC"

    def test_line_without_embedded_actions_passes_through(self) -> None:
        """A plain {"line": "..."} without embedded structure passes through."""
        raw = json.dumps(LINE_RESPONSE)
        result = _extract_json(raw)
        assert result is not None
        assert "line" in result
        # No recovery triggered: no action_items key.
        assert "action_items" not in result or result.get("action_items") == LINE_RESPONSE.get("action_items")

    def test_line_with_summary_recovers_summary(self) -> None:
        text = json.dumps({"line": 'action_items: [{"task": "x", "owner": null, "due": null}], summary: "short"'})
        result = _extract_json(text)
        assert result is not None
        assert result.get("summary") == "short"


# --------------------------------------------------------- named-owner parsing pins (story 02)

class TestNamedOwnerParsing:
    """Parsing pins for named owners (_coerce_action_items)."""

    def test_multi_word_name_passes_verbatim(self) -> None:
        items = _coerce_action_items([
            {"task": "Review architecture", "owner": "Jan Kowalski", "due": None}
        ])
        assert len(items) == 1
        assert items[0].owner == "Jan Kowalski"

    def test_me_casing_variants_pass_through(self) -> None:
        for variant in ("Me", "ME", "me", "mE"):
            items = _coerce_action_items([
                {"task": "task", "owner": variant, "due": None}
            ])
            assert items[0].owner == variant

    def test_remote_casing_variants_pass_through(self) -> None:
        for variant in ("Remote", "REMOTE", "remote", "rEmOtE"):
            items = _coerce_action_items([
                {"task": "task", "owner": variant, "due": None}
            ])
            assert items[0].owner == variant

    def test_null_string_becomes_none(self) -> None:
        items = _coerce_action_items([
            {"task": "task", "owner": "null", "due": None}
        ])
        assert items[0].owner is None

    def test_empty_string_becomes_none(self) -> None:
        items = _coerce_action_items([
            {"task": "task", "owner": "", "due": None}
        ])
        assert items[0].owner is None

    def test_none_becomes_none(self) -> None:
        items = _coerce_action_items([
            {"task": "task", "owner": None, "due": None}
        ])
        assert items[0].owner is None

    def test_strips_whitespace(self) -> None:
        items = _coerce_action_items([
            {"task": "task", "owner": "  Ewa S.  ", "due": None}
        ])
        assert items[0].owner == "Ewa S."


# --------------------------------------------------------- named-owner canary (story 02 AC 3)

class TestNamedOwnerCanary:
    """Through the stub pin-server, a transcript naming two people round-trips
    into action_items rows with review_state=pending and verbatim named owners."""

    def test_named_owner_canary(
        self, pin_server: HTTPServer, monkeypatch: Any
    ) -> None:
        _PinServerHandler.named_owner_mode = True
        engine = _make_engine(pin_server, monkeypatch)
        result = engine.analyze(NAMED_OWNER_TRANSCRIPT, stream=False)
        assert result.error is None or result.error == ""
        assert len(result.action_items) >= 2

        owners = {item.owner for item in result.action_items}
        assert "Ewa" in owners
        assert "Jan Kowalski" in owners

        for item in result.action_items:
            assert item.review_state == "pending"
            assert item.task != ""


# --------------------------------------------------------- forget_endpoint_dialects

class TestForgetEndpointDialects:
    """forget_endpoint_dialects clears both dialect sets."""

    def test_clears_both(self) -> None:
        _COMPAT_NO_RESPONSE_FORMAT.add("test:key")
        forget_endpoint_dialects()
        assert not endpoint_rejects_response_format("test:key")


# --------------------------------------------------------- interplay pins (story 02)

class TestNamedOwnerInterplay:
    """Service-level read-only assertions: intel-born named owners and the people layer."""

    @pytest.fixture
    def people_service(self, tmp_path: Any) -> Any:
        import os

        os.environ["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] = str(tmp_path / "test.keystore")
        from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
        from holdspeak.services.people_service import PeopleService

        store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
        store.initialize()
        return PeopleService(store)

    def test_unmapped_named_owner_has_no_person_label(self, people_service: Any) -> None:
        """An intel-born named owner with no alias gesture has no person mapping."""
        from holdspeak.principals import Principal, PrincipalKind

        owner = Principal(PrincipalKind.OWNER, "interplay-owner")
        result = people_service.resolve_relationship_by_owner("Ewa")
        assert result["state"] == "ready"
        assert result["relationship"] is None  # unmapped: no person_label

    def test_mapped_named_owner_has_person_label(self, people_service: Any) -> None:
        """After the REAL alias gesture, an intel-born named owner resolves to a person."""
        from holdspeak.principals import Principal, PrincipalKind

        owner = Principal(PrincipalKind.OWNER, "interplay-owner")
        relationship = people_service.create_relationship(owner, {"display_name": "Ewa Kowalska"})
        people_service.link_owner_alias(owner, relationship["id"], "Ewa")

        result = people_service.resolve_relationship_by_owner("Ewa")
        assert result["state"] == "ready"
        assert result["relationship"] is not None
        assert result["relationship"]["display_name"] == "Ewa Kowalska"

    def test_me_reserved_cannot_map(self, people_service: Any) -> None:
        """'Me' from intel cannot be mapped (reserved refusal)."""
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.people_service import PeopleServiceError

        owner = Principal(PrincipalKind.OWNER, "interplay-owner")
        relationship = people_service.create_relationship(owner, {"display_name": "Leader"})
        with pytest.raises(PeopleServiceError) as exc_info:
            people_service.link_owner_alias(owner, relationship["id"], "Me")
        assert "reserved" in str(exc_info.value)

    def test_remote_reserved_cannot_map(self, people_service: Any) -> None:
        """'Remote' from intel cannot be mapped (reserved refusal)."""
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.people_service import PeopleServiceError

        owner = Principal(PrincipalKind.OWNER, "interplay-owner")
        relationship = people_service.create_relationship(owner, {"display_name": "Counterpart"})
        with pytest.raises(PeopleServiceError) as exc_info:
            people_service.link_owner_alias(owner, relationship["id"], "Remote")
        assert "reserved" in str(exc_info.value)

    def test_me_casing_variants_all_reserved(self, people_service: Any) -> None:
        """All casing variants of 'Me' are reserved."""
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.people_service import PeopleServiceError

        owner = Principal(PrincipalKind.OWNER, "interplay-owner")
        relationship = people_service.create_relationship(owner, {"display_name": "Test"})
        for variant in ("ME", "me", "mE"):
            with pytest.raises(PeopleServiceError):
                people_service.link_owner_alias(owner, relationship["id"], variant)

    def test_multi_word_name_maps_normally(self, people_service: Any) -> None:
        """A multi-word name like 'Jan Kowalski' maps without issue."""
        from holdspeak.principals import Principal, PrincipalKind

        owner = Principal(PrincipalKind.OWNER, "interplay-owner")
        relationship = people_service.create_relationship(owner, {"display_name": "Jan Kowalski"})
        people_service.link_owner_alias(owner, relationship["id"], "Jan Kowalski")

        result = people_service.resolve_relationship_by_owner("Jan Kowalski")
        assert result["state"] == "ready"
        assert result["relationship"] is not None
        assert result["relationship"]["display_name"] == "Jan Kowalski"


# --------------------------------------------------------- wire_metal_intel binder resolve test

class TestWireMetalIntelBinderResolve:
    """A fresh HOME wired by wire_metal_intel lets MeetingDeferredQueueBinder.prepare() resolve."""

    def test_wired_home_lets_binder_prepare_resolve(self, tmp_path: Any) -> None:
        """Dry resolve: the binder can resolve the route plan for meeting.deferred_analysis."""
        import os

        home = tmp_path / "wired-home"
        home.mkdir()
        old_home = os.environ.get("HOME")
        try:
            from scripts.wire_metal_intel import wire

            wire(home, base_url="http://127.0.0.1:9999/v1", model="test-model")

            from holdspeak.db import Database
            from holdspeak.services.inference_assignment_service import InferenceAssignmentService
            from holdspeak.services.inference_route_plan_service import (
                ROUTE_PLANNING_AUTHORITY,
                InferenceRoutePlanService,
            )
            from holdspeak.principals import Principal, PrincipalKind
            from holdspeak.meeting_session.deferred_bound import PARENT_KIND, queue_service_principal

            db_path = home / ".holdspeak" / "holdspeak.db"
            db = Database(db_path)
            assignments = InferenceAssignmentService(db)
            plans = InferenceRoutePlanService(db)

            # The route plan resolves for the SERVICE principal (the queue worker).
            principal = queue_service_principal()
            import time

            resolved = plans.resolve_route_plan_for_feature(
                ROUTE_PLANNING_AUTHORITY,
                feature_principal=principal,
                parent_kind=PARENT_KIND,
                capability_id="meeting.deferred_analysis",
                invocation_id="test-invocation",
                deadline_at=time.time() + 600,
            )
            # The resolve must succeed (not raise) and return a route with entries.
            assert resolved is not None
            assert "retry_policy" in resolved
        finally:
            if old_home is not None:
                os.environ["HOME"] = old_home
