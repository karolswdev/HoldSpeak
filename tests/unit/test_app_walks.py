"""Every native app carries its own walk (owner, 2026-11-09).

An application names its walk in ``web/src/desk/applications.ts`` (``walk:
"<name>"``, and ``CHAIR_WALKS`` for Needs you); the script is
``web/src/desk/walks/<name>.walk.json`` in the Walk's own format. Each script
is a valid walk for the hub (``walk_service.validate_script``), each part it
marks exists in the desk source, ``scripts/walk.py apps`` composes the apps
into one linked walk, and the desk's Show me test replays this hub's own
answers for an app walk (``web/src/desk/walk/__fixtures__/appwalk.*.json``;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites them, else this test fences their shape).
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import briefing_service as briefing_module
from holdspeak.services import walk_service as walk_module
from holdspeak.services.walk_service import WalkService, validate_script
from holdspeak.web.routes.walks import build_walks_router

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "src"
WALKS = WEB / "desk" / "walks"
FIXTURES = WEB / "desk" / "walk" / "__fixtures__"
RECORDED_TOKEN = "Rec0rdedAppWalkT0kenRec0rdedAppWalkT0kenRec"
OWNER = Principal(PrincipalKind.OWNER, "owner-session")



def _walk_script() -> Any:
    spec = importlib.util.spec_from_file_location("walk_script", ROOT / "scripts" / "walk.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _source() -> str:
    parts = []
    for path in WEB.rglob("*.tsx"):
        if "__tests__" in path.parts or "_parked" in path.parts or path.name.endswith(".test.tsx"):
            continue
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _scripts() -> dict[str, dict[str, Any]]:
    return {path.name.removesuffix(".walk.json"): json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(WALKS.glob("*.walk.json"))}


def test_every_declared_walk_keeps_its_parts_and_questions_valid() -> None:
    declared = _walk_script().declared_walks()
    scripts = _scripts()
    assert declared, "the manifest declares no walks"
    assert set(scripts) == set(declared), "a walk file with no app, or an app with no walk file"
    applications = (WEB / "desk" / "applications.ts").read_text(encoding="utf-8")
    for name, script in scripts.items():
        clean = validate_script(script)
        assert clean["steps"] == script["steps"], f"{name}: the hub would store other steps"
        steps = script["steps"]
        asks = [step["ask"] for step in steps if "ask" in step]
        assert asks and "ask" in steps[-1], f"{name}: end with the owner's answer"
        assert len({ask["ref"] for ask in asks}) == len(asks), f"{name}: an answer must identify one question"
        assert all(ask["question"] and len(set(ask["choices"])) == len(ask["choices"]) for ask in asks)
        # An in-place tour can select another pane of the same app.
        assert all(step["open"]["app"] == script["open"]["app"] for step in steps if "open" in step), name
        # The app it opens in a linked walk exists on the desk.
        app = script["open"]["app"]
        assert app == "chair:needs" or f'action: "{app}"' in applications or f'windowId: "{app}"' in applications, app


def test_every_part_a_walk_marks_exists_in_the_desk_source() -> None:
    source = _source()
    for name, script in _scripts().items():
        for step in script["steps"]:
            target = step["highlight"]["target"]
            if target.startswith("."):
                found = re.search(rf'className=[{{"`][^>]*\b{re.escape(target[1:])}\b', source)
            else:
                # `data-testid="x"`, `testId="x"`, a species' default `testId = "x"`,
                # or a Rail group's `testId: "x"` (the Rail draws it as the group's test id).
                found = re.search(rf'(?:data-testid|testId)\s*[=:]\s*(?:"{re.escape(target)}"|{{"{re.escape(target)}"}})', source)
            assert found, f"{name}: no part {target} in the desk"


def test_walk_py_apps_keeps_each_apps_order_and_questions() -> None:
    walk = _walk_script()
    composed = walk.compose_apps()
    clean = validate_script(composed)
    opens = [step["open"] for step in clean["steps"] if "open" in step]
    scripts = _scripts()
    from itertools import groupby
    app_order = [scripts[name]["open"]["app"] for name in walk.declared_walks()]
    assert [app for app, _ in groupby(o["app"] for o in opens)] == app_order
    refs = [step["ask"]["ref"] for step in clean["steps"] if "ask" in step]
    expected = [step["ask"]["ref"] for script in scripts.values() for step in script["steps"] if "ask" in step]
    assert sorted(refs) == sorted(expected), "composition lost or repeated an owner's question"
    # The Room opens his first project; a walk with no project skips the step.
    assert {"app": "open-project-memory", "scope": "@first-project"} in opens


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(value[0])] if value else []
    return type(value).__name__


def _fixture(name: str, answer: Any, token: str) -> None:
    """The hub's own answer, stored for the desk test (never typed by hand)."""
    scrubbed = json.loads(json.dumps(answer).replace(token, RECORDED_TOKEN))
    path = FIXTURES / name
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps(scrubbed, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = json.loads(path.read_text())
    assert _shape(stored) == _shape(scrubbed), f"{name}: not the hub's shape"


def test_an_app_walk_is_made_read_and_answered_through_the_one_walk_record(tmp_path, monkeypatch) -> None:
    service = WalkService(home=tmp_path)
    monkeypatch.setattr(walk_module, "default_walk_service", lambda: service)
    monkeypatch.setattr(briefing_module, "MISSES", briefing_module._Misses())
    app = FastAPI()

    @app.middleware("http")
    async def _edge(request, call_next):
        if not request.url.path.startswith(("/w/", "/api/w/")):
            request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_walks_router(None))  # type: ignore[arg-type]
    client = TestClient(app, follow_redirects=False)

    script = _scripts()["programs"]
    # Show me posts the title and the steps (in place it opens nothing).
    made = client.post("/api/walks", json={"title": script["title"], "steps": script["steps"]})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    _fixture("appwalk.create.json", made.json(), token)
    page = client.get(f"/api/w/{token}")
    assert page.status_code == 200 and page.json()["steps"] == script["steps"]
    _fixture("appwalk.page.json", page.json(), token)
    answered = client.post(f"/api/w/{token}/answer", json={"ref": "programs-feel", "choice": "Keep"})
    assert answered.status_code == 200, answered.text
    _fixture("appwalk.answer.json", answered.json(), token)
    read = service.read(made.json()["id"])
    assert read["answers"]["programs-feel"]["choice"] == "Keep"
