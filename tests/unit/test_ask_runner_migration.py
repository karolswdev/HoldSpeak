"""HS-131-03 Ask runner migration and mechanical bypass fence."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.ask_projection import materialize
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import ASK_PAYLOAD_SCHEMA_VERSION, ASK_SERVICE_CONTRACT, ASK_SERVICE_SCHEMA_VERSION, AskService

OWNER = Principal(PrincipalKind.OWNER, "owner")
#: The classic runner path is the unrouted Thought's now; an answer runs
#: through the engine door (``test_ask_engine_door.py``).
CLASSIC = "thought.interview"


class Engine:
    active_provider = "test-provider"
    active_model = "test-model"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run_prompt(self, **kwargs):
        self.calls.append(kwargs)
        return "runner answer"


@pytest.fixture
def rig(tmp_path: Path, monkeypatch, local_model_present):
    db = Database(tmp_path / "ask-runner.db")
    # HS-200-03: `local_model_present` substitutes the ONE readiness predicate
    # both `_this_machine_readiness()` and `this_machine_target_from_model_path()`
    # ask. Patching only the former left the second path reading the developer's
    # `~/Models` tree, so this test refused with `target_unavailable` on every
    # machine that did not have that exact GGUF file.
    engine = Engine()
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    broker = _configure(db)
    return db, broker, engine






