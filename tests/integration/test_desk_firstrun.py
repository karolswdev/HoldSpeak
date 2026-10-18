"""First run, against a real hub: the hub half of the first-run browser walks
(the test diet, PHILO-17 final lane A, 2026-10-11).

Each test boots a real hub (``tests/e2e/glass_infra._boot``: a real
MeetingWebServer, an isolated HOME and DB, every isolation switch), drives it
over HTTP in the order the first-run face does, asserts the facts the browser
walk asserted on the hub, and records the hub's answers. The face half,
``web/src/desk/firstrun/__tests__/firstrun.app.test.tsx``, renders the real
``FirstRun`` on those recorded answers (SCAR LAW: never a typed hub answer).

Each run fences the stored answers' SHAPE against the hub's
(``tests/integration/test_desk_agents_wire._same_shape``);
``HOLDSPEAK_WIRE_WRITE=1`` rewrites them under
``web/src/desk/__tests__/fixtures/firstrun-<scenario>/``.
"""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot
from tests.integration.test_desk_agents_wire import _same_shape, _scrub, _shape
from tests.integration.test_desk_runs_on_hub import STUB_HOST, TOOLS_MODEL, _ToolsEngine, _key_for

TOKEN = "firstrun-hub"
REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures"
#: The reads the first-run face makes (FirstRun and its cards, the
#: Concierge controller of "Use a server on my network"), and the Engines
#: window's one more read (betterment ST0: Engines after the press).
FACE_READS = (
    "/api/setup/local-ai", "/api/settings", "/api/onboarding/calendar", "/api/onboarding/connections",
    "/api/onboarding/agents", "/api/concierge/detect", "/api/inference/assignments", "/api/inference/defaults",
    "/api/door", "/api/memory/meaning-search",
)

pytestmark = pytest.mark.timeout(120, method="thread")


def _call(base: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def _ok(base: str, method: str, path: str, body: Any = None) -> Any:
    status, payload = _call(base, method, path, body)
    assert status < 300, (status, path, payload)
    return payload


class _Recorder:
    """Stores (or fences) one scenario's answers: ``<stage>|<METHOD> <path>``."""

    def __init__(self, scenario: str, tmp_path: Path, base: str, engine: str | None = None) -> None:
        self.dir = FIXTURES / f"firstrun-{scenario}"
        self.tmp_path, self.base, self.engine = tmp_path, base, engine

    def _scrubbed(self, payload: Any) -> Any:
        value = _scrub(payload, self.tmp_path, self.base)
        if not self.engine:
            return value
        port = self.engine.split("://", 1)[1].split("/")[0].split(":")[1]
        text = json.dumps(value).replace(f"127.0.0.1:{port}", STUB_HOST)
        return json.loads(text.replace(f"127-0-0-1-{port}", "127-0-0-1-8099"))

    def keep(self, name: str, payload: Any) -> Any:
        scrubbed = self._scrubbed(payload)
        path = self.dir / f"{name}.json"
        if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "_": f"The hub's own answer, captured by {Path(__file__).relative_to(REPO)}; "
                     "HOLDSPEAK_WIRE_WRITE=1 rewrites it.",
                "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "wire": scrubbed,
            }, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
        diffs = _same_shape(_shape(json.loads(path.read_text())["wire"]), _shape(scrubbed))
        assert not diffs, f"{path.name}: the stored answer is not the hub's shape: {diffs[:10]}"
        return payload

    def reads(self, stage: str) -> dict[str, Any]:
        out = {path: _ok(self.base, "GET", path) for path in FACE_READS}
        out["POST /api/concierge/propose"] = _ok(self.base, "POST", "/api/concierge/propose")
        for path, payload in out.items():
            key = path if path.startswith("POST ") else f"GET {path}"
            self.keep(f"{stage}{key.replace(' ', '').replace('/', '_')}", payload)
        return out


@pytest.fixture()
def tools_engine():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ToolsEngine)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()


def test_a_lan_box_as_default_keeps_the_speech_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tools_engine: str,
) -> None:
    """replaces: tests/e2e/test_philo15_10_engine_truth_glass.py::TestColdFirstRun::test_the_lan_box_keeps_the_speech_download (hub half)

    The cold Mac (no Whisper the hub can see). "Use a server on my network":
    Check, then the press that defines the engine and selects it for
    summaries, setting the Default once. The Default is assigned; speech is
    still to download.
    """
    empty = tmp_path / "hf-empty"
    empty.mkdir()
    monkeypatch.setenv("HF_HOME", str(empty))
    monkeypatch.setenv("HF_HUB_CACHE", str(empty / "hub"))
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        rec = _Recorder("lan", tmp_path, base, tools_engine)
        cold = rec.reads("0-cold")
        assert cold["/api/setup/local-ai"]["speech"]["state"] in {"will_download", "not_covered"}, cold

        checked = _ok(base, "POST", "/api/setup/discover-models",
                      {"base_url": tools_engine, "check_tools": True})
        assert checked["ok"] is True and checked["models"] == [TOOLS_MODEL] and checked["tools"] == "yes"
        rec.keep("check", checked)
        key = _key_for(tools_engine)
        defined = rec.keep("define", _ok(base, "POST", "/api/inference/model-library/define-endpoint", {
            "draft": {
                "request_id": "firstrun-lan", "profile_id": key, "expected_profile_revision": 0,
                "label": tools_engine.split("://", 1)[1].split("/")[0], "provider_family": "openai_compatible",
                "model": TOOLS_MODEL, "endpoint": tools_engine, "requires_key": False,
            },
            "secret": None,
        }))
        selection = rec.keep("select", _ok(base, "POST", "/api/concierge/summary-selection", {
            "commandId": "firstrun-lan-summary",
            "expectedAssignmentRevision": cold["/api/concierge/detect"]["summaryAssignment"]["assignmentRevision"],
            "profileId": defined["provider"]["profile_id"],
            "profileRevision": defined["provider"]["profile_revision"],
            "setDefault": True,
        }))
        assert selection["result"]["state"] == "READY" and selection["defaultSet"] is True, selection

        after = rec.reads("1-used")
        glob = next(r for r in after["/api/inference/assignments"]["rows"] if r["id"] == "global")
        assert glob["status"] == "assigned", glob
        # Betterment ST0: the press made the chat server the Default for
        # every job, speech included, and Engines said TOOL INCOMPATIBLE and
        # 1 BROKEN. Speech never inherits a chat server: it stays unassigned,
        # and no job is broken.
        rows = {r["id"]: r for r in after["/api/inference/assignments"]["rows"]}
        speech = rows["speech_recognition"]
        assert speech["status"] == "no_assignment", speech
        assert speech["assignment"] is None and speech["inherited_from"] is None, speech
        # A job some of whose work the engine cannot do is LIMITED, never
        # BROKEN: the engine still serves part of every assigned group.
        roster = after["/api/inference/assignments"]
        for row in rows.values():
            if row["id"] == "global" or row["assignment"] is None:
                continue
            work = {t["id"] for t in roster["task_overrides"] if t["group"]["id"] == row["id"]}
            blocked = {
                i.get("capability_id") for i in row["assignment"]["issues"] if i["severity"] == "blocking"
            }
            assert work - blocked, (row["id"], blocked)
        for group in ("thoughts_notes", "writing_dictation", "meetings", "background"):
            assert rows[group]["assignment"] is not None, rows[group]
        repairs = after["/api/concierge/detect"].get("repairs") or []
        assert not [r for r in repairs if "speech_recognition" in (r.get("groups") or [])], repairs
        # Speech is still missing: the download stays.
        assert after["/api/setup/local-ai"]["speech"]["state"] in {"will_download", "not_covered"}, after
    finally:
        server.stop()


class _Mac:
    """EventKit says denied until he allows it; the System Settings open is counted."""

    def __init__(self) -> None:
        self.state = "denied"
        self.opens = 0

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import holdspeak.macos_calendar as macos

        monkeypatch.setattr(macos, "access_state", lambda: self.state)
        monkeypatch.setattr(macos, "list_calendars", lambda: [])
        monkeypatch.setattr(macos, "open_privacy_settings", self.open)

    def open(self) -> bool:
        self.opens += 1
        return True


def test_a_denied_calendar_has_a_way_forward(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_philo15_04_small_gaps_glass.py::TestCalendarDenied::test_denied_has_a_way_forward (hub half)

    macOS Calendar access denied (EventKit and the System Settings open are
    doubles in the hub process): the hub says denied; his press opens
    System Settings once; he allows it there and the next read moves on.
    """
    mac = _Mac()
    mac.install(monkeypatch)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        rec = _Recorder("calendar-denied", tmp_path, base)
        before = rec.reads("0-denied")
        assert before["/api/onboarding/calendar"]["macos"]["state"] == "denied", before["/api/onboarding/calendar"]

        opened = rec.keep("open-settings", _ok(base, "POST", "/api/onboarding/calendar/macos/settings", {}))
        assert mac.opens == 1, mac.opens
        assert opened.get("success") is not False, opened

        mac.state = "full_access"
        allowed = rec.reads("1-allowed")["/api/onboarding/calendar"]
        assert allowed["macos"]["state"] == "full_access", allowed
        assert mac.opens == 1, "a read never opens System Settings"
    finally:
        server.stop()
