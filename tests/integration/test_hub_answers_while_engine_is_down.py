"""Lane HUB TIMEOUTS (2026-10-27): an engine that does not answer never holds the desk.

Live finding: away from his LAN, the owner's desk opened two windows that read
Loading for good; every read of the hub was still pending after 15 s. Two hub
routes probed the engine ON the event loop (GET /api/concierge/detect, GET
/api/front-door/recommendation), so while a probe waited for its timeout the
hub answered nothing else. This rig points three engine profiles at a server
that takes the connection and never answers (a black hole, on this machine so
the result does not depend on the network), assigns one, fires the probing
reads and, at the same time, the desk's own reads. The desk's reads answer
within 2 s.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot

TOKEN = "glass-test"


def _call(base: str, path: str, method: str = "GET", body: Any = None) -> tuple[str, int, float]:
    data = json.dumps(body).encode() if body is not None else (b"{}" if method == "POST" else None)
    request = urllib.request.Request(
        base + path, data=data, method=method,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - the rig's own hub
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    return path, status, time.monotonic() - started


@pytest.fixture()
def black_hole():
    """A server that takes every connection and never sends a byte."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(64)
    try:
        yield f"http://127.0.0.1:{server.getsockname()[1]}"
    finally:
        server.close()


@pytest.fixture()
def hub(tmp_path, monkeypatch):
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


def _seed(base: str, black_hole: str, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import setup_runtime
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    # The define's own check answers at once (it is not what this rig proves).
    real = setup_runtime._default_http_json
    monkeypatch.setattr(setup_runtime, "_default_http_json",
                        lambda url, **_: (200, json.dumps({"data": [{"id": "qwen"}]}).encode()))
    for index in range(3):
        _, status, _ = _call(base, "/api/inference/model-library/define-endpoint", "POST", {"secret": None, "draft": {
            "request_id": f"bh-{index}", "profile_id": f"lan-bh-{index}", "expected_profile_revision": 0,
            "label": f"LAN model {index}", "provider_family": "openai_compatible", "model": "qwen",
            "endpoint": f"{black_hole}/v{index}", "requires_key": False,
        }})
        assert status == 200
    monkeypatch.setattr(setup_runtime, "_default_http_json", real)

    db = get_database()
    InferenceAssignmentService(db).set_assignment(Principal(PrincipalKind.OWNER, "rig"), {
        "command_id": "bh-summary", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
        "entries": [{"profile_id": "lan-bh-0", "profile_revision": 1}],
    })
    now = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, intel_status, capture_status)"
            " VALUES ('m-bh', ?, ?, 'Standup', 300, 'disabled', 'finalized')", (now, now))


DESK_READS = (
    "/api/settings/hub",
    "/api/meetings/m-bh?include_parked=true",
    "/api/calendar/sources",
    "/api/people/relationships",
    "/api/desk/needs-you?fresh=1",
)
PROBING_READS = ("/api/concierge/detect", "/api/front-door/recommendation")


def test_the_desk_reads_answer_while_the_engine_is_a_black_hole(hub, black_hole, monkeypatch):
    _seed(hub, black_hole, monkeypatch)
    with cf.ThreadPoolExecutor(8) as pool:
        probing = [pool.submit(_call, hub, path) for path in PROBING_READS * 2]
        time.sleep(0.3)  # the probes are in flight
        desk = [pool.submit(_call, hub, path) for path in DESK_READS]
        desk.append(pool.submit(_call, hub, "/api/meetings/m-bh/ready/read", "POST"))
        answered = [future.result() for future in desk]
        probed = [future.result() for future in probing]
    for path, status, seconds in answered:
        assert status == 200, path
        assert seconds < 2.0, f"{path} took {seconds:.2f} s while an engine did not answer"
    # The probing reads answered too, inside their own bounds.
    for path, status, seconds in probed:
        assert status == 200, path
        assert seconds < 10.0, (path, seconds)


def test_a_second_detection_answers_from_the_last_check(hub, black_hole, monkeypatch):
    _seed(hub, black_hole, monkeypatch)
    _, _, first = _call(hub, "/api/concierge/detect")
    _, status, second = _call(hub, "/api/concierge/detect")
    assert status == 200 and second < 1.0, (first, second)
    request = urllib.request.Request(
        hub + "/api/concierge/detect", headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - the rig's own hub
        rows = [row for row in json.loads(response.read())["engines"] if str(row.get("profileId", "")).startswith("lan-bh")]
    assert rows and all(row["state"] == "UNREACHABLE" for row in rows), rows


def test_an_engine_call_connects_within_three_seconds():
    """The model clients get a connect bound; the read keeps the call's budget."""
    from holdspeak.net_bounds import CONNECT_SECONDS, engine_timeout

    timeout = engine_timeout(180.0)
    assert timeout.connect == CONNECT_SECONDS == 3.0
    assert timeout.read == 180.0
    assert engine_timeout(1.5).connect == 1.5


def test_meeting_intel_hands_its_client_the_connect_bound(monkeypatch):
    import holdspeak.intel as intel_pkg
    from holdspeak.intel.engine import MeetingIntel

    seen: dict[str, Any] = {}
    monkeypatch.setattr(intel_pkg, "OpenAI", lambda **kwargs: seen.update(kwargs) or object())
    intel = MeetingIntel(provider="cloud", cloud_model="m", cloud_api_key_env="",
                         cloud_base_url="http://10.255.255.1:9/v1")
    intel._active_provider = "cloud"
    intel._ensure_openai_client_loaded()
    assert seen["timeout"].connect == 3.0
    assert seen["timeout"].read == intel.cloud_timeout_seconds
