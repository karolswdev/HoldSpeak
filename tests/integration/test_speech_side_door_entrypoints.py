"""HS-131-15 production-entry proofs for browser and CLI synthetic text."""

from __future__ import annotations

import io
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.plugins.dictation.assembly as assembly
from holdspeak.commands.dictation import run_dictation_command
from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.speech_session import cli_owner_principal
from holdspeak.web.context import WebContext
from holdspeak.web.routes.dictation.pipeline import build_pipeline_router


INPUT_SENTINEL = "SPEECH_SIDE_DOOR_INPUT_7D92"
PROVIDER_SENTINEL = "SPEECH_SIDE_DOOR_PROVIDER_4A31"
PROFILE_ID = "speech-side-door-provider"
BASE_URL = "https://speech-side-door.invalid/v1"
MODEL = "speech-side-door-model"


class _ProviderRuntime:
    backend = "openai_compatible"

    def __init__(self, *, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model
        self.calls: list[str] = []

    def load(self) -> None:
        return None

    def info(self) -> dict[str, Any]:
        return {"backend": self.backend}

    def classify(self, prompt: str, _schema: Any, **_kwargs: Any) -> dict[str, Any]:
        self.calls.append(prompt)
        return {
            "matched": True,
            "block_id": "provider_block",
            "confidence": 0.95,
            "extras": {"provider_note": PROVIDER_SENTINEL},
        }


class _OrderedStream(io.StringIO):
    def __init__(self, events: list[tuple[str, Any]]) -> None:
        super().__init__()
        self._events = events

    def write(self, value: str) -> int:
        self._events.append(("write", value))
        return super().write(value)


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".holdspeak").mkdir(parents=True)
    (root / ".holdspeak" / "blocks.yaml").write_text(
        """\
version: 1
blocks:
  - id: provider_block
    description: Provider-backed admission proof
    match:
      examples: [\"route this provider request\"]
    inject:
      mode: append
      template: \"{raw_text}\"
""",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        '[project]\nname = "speech-side-door-proof"\n', encoding="utf-8"
    )
    return root


def _rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database = Database(tmp_path / "speech-side-door.db")
    database.profiles.upsert(
        profile_id=PROFILE_ID,
        name=PROFILE_ID,
        kind="openAICompatible",
        base_url=BASE_URL,
        model=MODEL,
    )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)

    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router"]
    config.dictation.runtime.profile_id = PROFILE_ID
    config.meeting.web_auth_token = "speech-side-door-owner-token"
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))

    events: list[tuple[str, Any]] = []
    runtimes: list[_ProviderRuntime] = []

    def factory(**kwargs: Any) -> _ProviderRuntime:
        events.append(("factory", dict(kwargs)))
        runtime = _ProviderRuntime(
            base_url=str(kwargs["endpoint_base_url"]),
            model=str(kwargs["endpoint_model"]),
        )
        runtimes.append(runtime)
        return runtime

    monkeypatch.setattr(assembly, "build_runtime", factory)
    return database, config, events, runtimes


def _assert_parent_child_receipts(database: Database) -> None:
    with database._connection() as connection:
        parents = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM kernel_operations WHERE name='dictation.session'"
            )
        ]
        children = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM kernel_operations WHERE name='inference.invoke'"
            )
        ]
        receipts = {
            row["operation_id"]: dict(row)
            for row in connection.execute("SELECT * FROM kernel_receipts")
        }
    assert len(parents) == 1
    assert len(children) == 1
    parent, child = parents[0], children[0]
    assert child["parent_operation_id"] == parent["operation_id"]
    assert receipts[parent["operation_id"]]["outcome"] == "succeeded"
    assert receipts[child["operation_id"]]["outcome"] == "succeeded"
    assert child["target_ref"].startswith("deployment-revision:")
    revision_id = child["target_ref"].removeprefix("deployment-revision:")
    revision = database.deployment_revisions.get(revision_id)
    assert revision is not None
    assert revision.endpoint == BASE_URL
    assert revision.model == MODEL


def _assert_kernel_hygiene(database: Database) -> None:
    with database._connection() as connection:
        for table in (
            "kernel_operations",
            "kernel_receipts",
            "kernel_journal",
            "kernel_parent_runs",
        ):
            for row in connection.execute(f"SELECT * FROM {table}"):
                blob = "|".join(str(value) for value in dict(row).values())
                assert INPUT_SENTINEL not in blob, table
                assert PROVIDER_SENTINEL not in blob, table
                assert "speech-side-door-owner-token" not in blob, table


def test_browser_dry_run_owns_one_parent_child_revision_and_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _config, events, runtimes = _rig(tmp_path, monkeypatch)
    project = _project(tmp_path)
    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        from holdspeak.principals import Principal, PrincipalKind

        request.state.principal = Principal(PrincipalKind.OWNER, "browser-proof")
        return await call_next(request)

    app.include_router(
        build_pipeline_router(WebContext(get_state=lambda: {}), project_doc_suggestions={})
    )
    response = TestClient(app).post(
        "/api/dictation/dry-run",
        json={"utterance": INPUT_SENTINEL, "project_root": str(project)},
    )

    assert response.status_code == 200, response.text
    assert response.json()["final_text"] == INPUT_SENTINEL
    assert response.json()["stages"][0]["intent"]["extras"] == {
        "provider_note": PROVIDER_SENTINEL
    }
    assert [kind for kind, _value in events] == ["factory"]
    assert len(runtimes) == 1 and len(runtimes[0].calls) == 1
    _assert_parent_child_receipts(database)
    _assert_kernel_hygiene(database)


def test_cli_dry_run_authenticates_discloses_then_constructs_and_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, config, events, runtimes = _rig(tmp_path, monkeypatch)
    project = _project(tmp_path)
    monkeypatch.chdir(project)
    monkeypatch.setenv("HOLDSPEAK_TOKEN", "speech-side-door-owner-token")
    stream = _OrderedStream(events)

    result = run_dictation_command(
        SimpleNamespace(dictation_action="dry-run", text=INPUT_SENTINEL),
        stream=stream,
        principal=cli_owner_principal(config),
        config_snapshot=config,
    )

    assert result == 0
    output = stream.getvalue()
    assert "egress: cloud" in output
    assert f"input: {INPUT_SENTINEL!r}" in output
    assert "final_text:" in output
    factory_index = next(index for index, event in enumerate(events) if event[0] == "factory")
    egress_index = next(
        index
        for index, event in enumerate(events)
        if event[0] == "write" and "egress:" in event[1]
    )
    assert egress_index < factory_index
    body_writes = [
        value for kind, value in events if kind == "write" and "final_text:" in value
    ]
    assert len(body_writes) == 1
    assert len(runtimes) == 1 and len(runtimes[0].calls) == 1
    _assert_parent_child_receipts(database)
    _assert_kernel_hygiene(database)


def test_cli_stdout_publication_settles_success_before_cancellation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A complete model-derived stdout body cannot sit over a cancelled parent."""
    import holdspeak.speech_session as speech_session

    database, config, events, _runtimes = _rig(tmp_path, monkeypatch)
    project = _project(tmp_path)
    monkeypatch.chdir(project)
    monkeypatch.setenv("HOLDSPEAK_TOKEN", "speech-side-door-owner-token")

    body_entered = threading.Event()
    cancellation_started = threading.Event()
    cancellation_done = threading.Event()
    captured: dict[str, Any] = {}
    cancel_threads: list[threading.Thread] = []
    real_entry = speech_session.SpeechEntry

    def cancel() -> None:
        cancellation_started.set()
        captured["entry"].cancel()
        cancellation_done.set()

    class BlockingStream(_OrderedStream):
        def write(self, value: str) -> int:
            if "final_text:" in value:
                body_entered.set()
                canceller = threading.Thread(target=cancel)
                cancel_threads.append(canceller)
                canceller.start()
                assert cancellation_started.wait(5)
                assert not cancellation_done.wait(
                    0.05
                ), "cancellation crossed stdout publication"
            return super().write(value)

    def capture_entry(session: Any) -> Any:
        entry = real_entry(session)
        captured["entry"] = entry
        return entry

    monkeypatch.setattr(speech_session, "SpeechEntry", capture_entry)
    stream = BlockingStream(events)
    result = run_dictation_command(
        SimpleNamespace(dictation_action="dry-run", text=INPUT_SENTINEL),
        stream=stream,
        principal=cli_owner_principal(config),
        config_snapshot=config,
    )
    for canceller in cancel_threads:
        canceller.join(5)

    assert result == 0, stream.getvalue()
    assert body_entered.is_set()
    assert cancellation_done.is_set()
    assert "final_text:" in stream.getvalue()
    with database._connection() as connection:
        receipt = connection.execute(
            "SELECT r.outcome FROM kernel_receipts r "
            "JOIN kernel_operations o ON o.operation_id=r.operation_id "
            "WHERE o.name='dictation.session' ORDER BY o.created_at DESC LIMIT 1"
        ).fetchone()
    assert receipt["outcome"] == "succeeded"
