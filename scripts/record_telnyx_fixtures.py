#!/usr/bin/env python3
"""Record the hub's own Telnyx setup answers for the faces (LINE-3b; the test
diet's SCAR LAW: nothing typed by hand, every field a face reads is the hub's).

It runs the real Calls and Settings routes on a FastAPI ``TestClient`` in a
fresh HOME against the fake Telnyx (``tests/fixtures/fake_telnyx.py``, a real
HTTP server whose answers are written from Telnyx's API reference). No live
Telnyx call is made.

    HOME=$(mktemp -d) uv run python scripts/record_telnyx_fixtures.py

It writes ``web/src/desk/calls/__fixtures__/line.telnyx.*.json``.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "web" / "src" / "desk" / "calls" / "__fixtures__"
KEY = "KEY0123456789abcdefTELNYX"


def record(root: Path) -> dict[str, Any]:
    os.environ["HOLDSPEAK_CHANNEL_KEYSTORE_FILE"] = str(root / "keys.json")
    for key in ("TELNYX_API_KEY", "HOLDSPEAK_LINE_SIP_PASSWORD", "HOLDSPEAK_AI_PHONE", "HOLDSPEAK_LINE", "HOLDSPEAK_CALLS"):
        os.environ.pop(key, None)

    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    import holdspeak.line.supervisor as supervisor
    import holdspeak.web.routes.calls as calls_routes
    from holdspeak.db import get_database
    from holdspeak.line import secrets as line_secrets
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.settings_service import SettingsService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.settings import build_settings_router
    from tests.fixtures.fake_telnyx import running_fake_telnyx

    supervisor.find_baresip = lambda *a, **k: "/opt/homebrew/bin/baresip"  # type: ignore[assignment]
    owner = Principal(PrincipalKind.OWNER, "line-owner")
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = owner
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, broadcast=lambda kind, data: None,
                     settings_service=SettingsService(get_database()), credential_service=object())
    app.include_router(calls_routes.build_calls_router(ctx))
    app.include_router(build_settings_router(ctx))
    client = TestClient(app)

    def get(path: str, **params: Any) -> Any:
        answer = client.get(path, params=params or None)
        assert answer.status_code == 200, (path, answer.status_code, answer.text[:300])
        return answer.json()

    def post(path: str, body: Any = None) -> Any:
        answer = client.post(path, json=body or {})
        assert answer.status_code == 200, (path, answer.status_code, answer.text[:300])
        return answer.json()

    def refused(path: str, body: Any = None) -> Any:
        answer = client.post(path, json=body or {})
        assert answer.status_code >= 400, answer.text
        return {"status": answer.status_code, "body": answer.json()}

    def put(patch: dict[str, Any]) -> Any:
        answer = client.put("/api/settings", json=patch)
        assert answer.status_code == 200 and answer.json().get("success", True) is not False, answer.text[:300]
        return answer.json()

    out: dict[str, Any] = {}
    with running_fake_telnyx(key=KEY) as fake:
        os.environ["HOLDSPEAK_TELNYX_API"] = fake.url
        # His desk: the Line on this Mac, a Telnyx number chosen, no key yet.
        put({"owner": {"name": "Karol"}, "calls": {"enabled": True, "passphrase": "blue heron",
                                                  "allowed_numbers": ["sip:karol@karol-iphone"],
                                                  "line": {"adapter": "line", "where": "this_mac",
                                                           "account": {"kind": "telnyx"}}}})
        out["line.telnyx.settings.noKey.json"] = get("/api/settings")["calls"]
        out["line.telnyx.status.noKey.json"] = get("/api/calls/line/telnyx/status")
        out["line.telnyx.connect.noKey.json"] = refused("/api/calls/line/telnyx/connect")
        # A wrong key: Telnyx refuses; the hub says what failed, what is kept, the next action.
        line_secrets.write(line_secrets.TELNYX_API_KEY, "KEY-wrong")
        out["line.telnyx.connect.keyRefused.json"] = refused("/api/calls/line/telnyx/connect")
        # Step 1: his key saved through Settings (the keystore).
        put({"calls": {"line": {"telnyx_api_key": KEY}}})
        out["line.telnyx.settings.keySaved.json"] = get("/api/settings")["calls"]
        out["line.telnyx.status.keySaved.json"] = get("/api/calls/line/telnyx/status")
        # Step 2: Connect.
        out["line.telnyx.connect.json"] = post("/api/calls/line/telnyx/connect")
        out["line.telnyx.settings.connected.json"] = get("/api/settings")["calls"]
        out["line.telnyx.status.connected.json"] = get("/api/calls/line/telnyx/status")
        # Step 3: Find numbers in 212, Buy (refused without the confirm's quote), Buy, Assign.
        found = get("/api/calls/line/telnyx/numbers", area="212")
        out["line.telnyx.numbers.212.json"] = found
        row = found["numbers"][0]
        out["line.telnyx.buy.noPress.json"] = refused("/api/calls/line/telnyx/buy", {"phone_number": row["phone_number"]})
        bought = post("/api/calls/line/telnyx/buy", {"phone_number": row["phone_number"], "quote": row["quote"]})
        out["line.telnyx.buy.json"] = bought
        out["line.telnyx.assign.json"] = post("/api/calls/line/telnyx/assign", {"phone_number": row["phone_number"]})
        out["line.telnyx.settings.assigned.json"] = get("/api/settings")["calls"]
        out["line.telnyx.status.assigned.json"] = get("/api/calls/line/telnyx/status")
        os.environ.pop("HOLDSPEAK_TELNYX_API", None)
        password = line_secrets.read(line_secrets.SIP_PASSWORD)

    text = json.dumps(out)
    assert KEY not in text and "KEY-wrong" not in text and password and password not in text, "a secret in a read"
    return out


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        recorded = record(Path(tmp))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in recorded.items():
        (OUT / name).write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO) / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
