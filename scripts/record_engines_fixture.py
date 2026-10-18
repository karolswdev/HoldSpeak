#!/usr/bin/env python3
"""Record the hub's own answers for the Engines face tests (Betterment E2).

``web/src/features/runson/__tests__/engines.app.test.tsx`` replays these
answers through a mocked ``apiFetch``. Every answer comes from the real hub
(``MeetingWebServer`` through ``TestClient``) on an isolated HOME and
database, with the fake ``claude`` of ``tests/fixtures/fake_agent_cli.py``
first on PATH and a stored (fake) Claude Code token in that HOME. The
owner's real CLIs are off PATH, so no real CLI runs and nothing is typed by
hand (the SCAR LAW).

Run it again when an answer's shape changes:

    HOME=$(mktemp -d) uv run python scripts/record_engines_fixture.py

It writes ``web/src/features/runson/__tests__/fixtures/engines.recorded.json``.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests" / "unit"))
os.environ.setdefault("HOLDSPEAK_TEST_NO_REAL_CLI", "1")

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402
from tests.fixtures.fake_agent_cli import install_fake_agent_clis, set_mode  # noqa: E402

OUT = REPO / "web" / "src" / "features" / "runson" / "__tests__" / "fixtures" / "engines.recorded.json"

#: The reads the Engines window makes (useRunsOn: the roster, then detection).
GETS = ("/api/inference/assignments", "/api/concierge/detect")
CONNECT = "/api/inference/model-library/connect-cli-engine"


def _get(hub: Any, path: str) -> Any:
    response = hub.client.get(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _post(hub: Any, path: str, body: dict[str, Any]) -> Any:
    response = hub.client.post(path, json=body)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _gets(hub: Any) -> dict[str, Any]:
    return {path: _get(hub, path) for path in GETS}


def _close() -> None:
    from holdspeak.db import reset_database

    reset_database()
    composition.install(composition.bare(label="record"))


def _hub(mp: pytest.MonkeyPatch, name: str, *, claude: bool, codex: bool = False) -> Any:
    root = Path(tempfile.mkdtemp(prefix=f"engines-{name}-"))
    hub = seeds._boot(root, mp)
    bin_dir = install_fake_agent_clis(root / "bin")
    hub.bin_dir = bin_dir
    if not codex:
        (bin_dir / "codex").unlink()
    if not claude:
        (bin_dir / "claude").unlink()
    # Only the fake: this machine's own claude/codex stay off PATH.
    mp.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    mp.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    folder = root / ".claude"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": "fake-token"}}))
    return hub


def nothing_found() -> dict[str, Any]:
    """No agent CLI on PATH: the Found section is absent."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _hub(mp, "none", claude=False)
        try:
            return {"gets": _gets(hub)}
        finally:
            _close()


def found_then_added() -> dict[str, Any]:
    """A signed-in fake Claude Code: found, Add, two answers, then a limit."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _hub(mp, "claude", claude=True)
        try:
            before = _gets(hub)
            draft = {"request_id": "record-add", "profile_id": "agent-claude",
                     "expected_profile_revision": 0, "preset": "claude"}
            added = _post(hub, CONNECT, {"draft": draft})
            after_add = _gets(hub)
            assign = {
                "command_id": "record-assign", "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "ask.answer"},
                "entries": [{"profile_id": added["provider"]["profile_id"],
                             "profile_revision": int(added["provider"]["profile_revision"])}],
            }
            _post(hub, "/api/inference/assignments/set", assign)
            for prompt in ("One", "Two"):
                _post(hub, "/api/ask", {"prompt": prompt})
            spent = _gets(hub)
            limit = {"request_id": "record-limit", "profile_id": "agent-claude",
                     "expected_profile_revision": int(added["provider"]["profile_revision"]),
                     "preset": "claude", "label": "Claude Code", "model": "default", "spend_limit_usd": 0.5}
            limited = _post(hub, CONNECT, {"draft": limit})
            after_limit = _gets(hub)
            # The CLI says it has no sign-in ("Please run /login"): the row says so.
            set_mode(hub.bin_dir, "claude", "fail")
            hub.client.post("/api/ask", json={"prompt": "Three"})
            return {"steps": [
                {"name": "found", "gets": before},
                {"name": "add", "post": CONNECT, "body": draft, "answer": added, "gets": after_add},
                {"name": "spent", "gets": spent},
                {"name": "limit", "post": CONNECT, "body": limit, "answer": limited, "gets": after_limit},
                {"name": "signedOut", "gets": _gets(hub)},
            ]}
        finally:
            _close()


def codex_added() -> dict[str, Any]:
    """A fake Codex added: it cannot stop a run at a limit, nor report a cost."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _hub(mp, "codex", claude=False, codex=True)
        try:
            _post(hub, CONNECT, {"draft": {"request_id": "record-codex", "profile_id": "agent-codex",
                                           "expected_profile_revision": 0, "preset": "codex"}})
            return {"gets": _gets(hub)}
        finally:
            _close()


DEFINE = "/api/inference/model-library/define-endpoint"
#: The address the face test types; the stub's real port is scrubbed to it.
STUB_URL = "http://127.0.0.1:8099/v1"


def three_models() -> dict[str, Any]:
    """Betterment E3: one server with three models (the owner's llama.cpp
    shape). Check lists all three; two of them become two engines."""
    import threading
    from http.server import ThreadingHTTPServer

    from tests.integration.test_desk_engines import _ThreeModels

    server = ThreadingHTTPServer(("127.0.0.1", 0), _ThreeModels)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/v1"

    def scrub(value: Any) -> Any:
        text = json.dumps(value).replace(f"127.0.0.1:{port}", "127.0.0.1:8099").replace(
            f"127-0-0-1-{port}", "127-0-0-1-8099")
        return json.loads(text)

    def draft(model: str, context: int | None) -> dict[str, Any]:
        # endpointDraft.ts: the id is host + model.
        slug = model.replace(".", "-")
        return {"request_id": f"record-{slug}", "profile_id": f"engine-127-0-0-1-{port}-{slug}",
                "expected_profile_revision": 0, "label": f"127.0.0.1:{port}",
                "provider_family": "openai_compatible", "model": model, "endpoint": url,
                "requires_key": False, "context_tokens": context}

    with pytest.MonkeyPatch.context() as mp:
        hub = _hub(mp, "three", claude=False)
        try:
            before = _gets(hub)
            checked = _post(hub, "/api/setup/discover-models", {"base_url": url, "check_tools": True})
            contexts = checked.get("contexts", {})
            steps = [{"name": "open", "gets": before}, {"name": "check", "answer": checked}]
            for model in ("alpha-7b", "gamma-3b"):
                body = draft(model, contexts.get(model))
                answer = _post(hub, DEFINE, {"draft": body, "secret": None})
                steps.append({"name": model, "post": DEFINE, "body": body, "answer": answer, "gets": _gets(hub)})
            return scrub({"steps": steps})
        finally:
            _close()
            server.shutdown()
            server.server_close()


def main() -> None:
    only = sys.argv[1:]
    scenarios = {
        "nothingFound": nothing_found,
        "claude": found_then_added,
        "codex": codex_added,
        "threeModels": three_models,
    }
    # `record_engines_fixture.py threeModels` records one scenario and keeps
    # the others as they are.
    fixture = json.loads(OUT.read_text()) if only and OUT.exists() else {}
    fixture["recordedBy"] = "scripts/record_engines_fixture.py"
    for name, record in scenarios.items():
        if not only or name in only:
            fixture[name] = record()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
