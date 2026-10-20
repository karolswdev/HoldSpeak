from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.config import Config
from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.setup_service import SetupService


OWNER = Principal(PrincipalKind.OWNER, "owner")


class _LocalSpeech:
    def status(self, principal):
        return {
            "state": "not_started",
            "speech": {"ready": False},
            "files": [{"key": "whisper", "label": "Whisper", "size_bytes": 42_000_000}],
        }

    def start(self, principal, *, only):
        return {"started": list(only)}


class _Defaults:
    def __init__(self):
        self.used = []

    def proposals(self):
        return [{"id": "small", "label": "Small engine", "host": "huggingface.co"}]

    def use_proposal(self, principal, proposal_id):
        self.used.append(proposal_id)
        return {"used": proposal_id}


class _Onboarding:
    def connections_detect(self, principal):
        return {"candidates": [{"id": "github", "provider": "github", "account": "owner", "connected": False, "verb": "Use it"}]}

    def calendar_detect(self, principal):
        return {"sources": 0, "candidates": [{"id": "work", "label": "Work calendar", "in_use": False, "verb": "Use it"}]}

    def agents_detect(self, principal):
        return {"agents": [{"id": "claude", "label": "Claude", "installed": True, "ready": False}]}

    def connections_use(self, principal, payload):
        return {"connected": payload["id"]}

    def calendar_use(self, principal, payload):
        return {"used": payload["id"]}


class _EmptyOnboarding:
    def connections_detect(self, principal):
        return {
            "candidates": [],
            "tools": {"gh": {"installed": False}, "acli": {"installed": False}},
        }

    def calendar_detect(self, principal):
        return {"macos": {"state": "not_determined"}, "sources": 0, "candidates": []}

    def agents_detect(self, principal):
        return {"agents": [
            {"id": "claude", "label": "Claude Code", "installed": False},
            {"id": "codex", "label": "Codex", "installed": False},
            {"id": "pi", "label": "pi", "installed": False},
        ]}


class _People:
    def __init__(self):
        self.created = []
        self.state = "ready"
        self.setup_calls = 0

    def readiness_state(self):
        return self.state

    def setup(self, principal):
        self.setup_calls += 1
        self.state = "ready"

    def suggestions(self, principal, *, db):
        return [{"key": "theo-lindqvist", "name": "Theo Lindqvist", "relationship_kind": "direct_report"}]

    def list_relationships(self, principal):
        return [{"id": "p1", "display_name": "Mira Okafor", "relationship_kind": "direct_report"}]

    def create_relationship(self, principal, payload):
        self.created.append(payload)
        return {"id": payload["display_name"].lower().replace(" ", "-"), **payload}


def _service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = Database(tmp_path / "holdspeak.db")
    cfg = tmp_path / "config.json"
    import holdspeak.config as config_module

    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg)
    Config().save()
    defaults = _Defaults()
    people = _People()
    service = SetupService(
        db,
        local_ai_setup_service=_LocalSpeech(),
        inference_default_service=defaults,
        onboarding_service=_Onboarding(),
        people_service=people,
        home_provider=lambda: tmp_path,
    )
    return service, defaults, people


def test_found_projects_existing_readers_and_keeps_use_as_owner_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    service, defaults, people = _service(tmp_path, monkeypatch)

    answer = service.found(OWNER)
    rows = {row["id"]: row for row in answer["rows"]}

    assert rows["speech"]["action"] == "speech"
    assert rows["speech"]["egress_host"] == "huggingface.co"
    assert rows["engine:small"]["action"] == "engine"
    assert rows["connection:github"]["verb"] == "Use it"
    assert rows["calendar:work"]["action"] == "calendar"
    assert rows["agents"]["action"] == "agents"
    assert answer["owner_name"] == ""
    assert answer["people"][0]["display_name"] == "Mira Okafor"
    assert answer["suggestions"][0]["name"] == "Theo Lindqvist"

    assert service.use_found(OWNER, "engine:small") == {"used": "small", "state": "ready"}
    assert defaults.used == ["small"]
    result = service.add_people(OWNER, "Theo Lindqvist, Ada Lovelace")
    assert [item["display_name"] for item in people.created] == ["Theo Lindqvist", "Ada Lovelace"]
    assert len(result["relationships"]) == 2


def test_add_people_initializes_an_unconfigured_people_store_on_the_explicit_press(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    service, _defaults, people = _service(tmp_path, monkeypatch)
    people.state = "unconfigured"

    service.add_people(OWNER, "Mira Okafor")

    assert people.setup_calls == 1


def test_found_on_empty_mac_keeps_speech_found_and_missing_integrations_truthful(tmp_path: Path):
    db = Database(tmp_path / "holdspeak.db")
    service = SetupService(
        db, home_provider=lambda: tmp_path, onboarding_service=_EmptyOnboarding(),
    )

    answer = service.found(OWNER)
    rows = {row["id"]: row for row in answer["rows"]}

    assert rows["speech"]["state"] == "found"
    assert rows["speech"]["action"] == "speech"
    assert [row["id"] for row in answer["rows"] if row["state"] == "found"] == ["speech", "owner"]
    assert rows["connection:github:not-found"]["state"] == "does_not_work"
    assert rows["connection:jira:not-found"]["reason"] == "Install acli and sign in to use Jira"
    assert rows["connection:confluence:not-found"]["state"] == "does_not_work"
    assert rows["calendar:not-found"]["reason"] == "No calendar is ready to use"
    assert rows["agents:not-found"]["state"] == "does_not_work"



def test_setup_rows_are_declared_on_the_shared_http_contract_only() -> None:
    from holdspeak import operations

    expected = {
        "setup.found": ("read", False, False, "found"),
        "setup.use": ("write", True, True, "use_row"),
        "setup.people.add": ("write", True, False, "add_people"),
        "setup.lan.scan": ("read", True, True, "scan_lan"),
    }
    by_name = {descriptor.name: descriptor for descriptor in operations.DESCRIPTORS}
    for name, (effect, owner_press, blocking_io, method) in expected.items():
        descriptor = by_name[name]
        assert descriptor.effect == effect
        assert descriptor.owner_only is True
        assert descriptor.owner_press is owner_press
        assert descriptor.blocking_io is blocking_io
        assert descriptor.method == method
        assert all(not exposure.startswith("mcp:") for exposure in descriptor.exposure)


def test_setup_contract_binds_all_four_calls_to_one_service_instance() -> None:
    from holdspeak import operations

    class FakeSetup:
        def found(self, principal): return {"rows": []}
        def use_row(self, principal, id, payload=None): return {"id": id}
        def add_people(self, principal, names): return {"relationships": []}
        def scan_lan(self, principal): return {"rows": [], "checkedAt": "now"}

    target = FakeSetup()
    registry = operations.bind_available({"setup_service": target})
    assert {name for name in registry.operations if name.startswith("setup.")} == {
        "setup.found", "setup.use", "setup.people.add", "setup.lan.scan",
    }
    assert all(registry.target(name) is target for name in registry.operations if name.startswith("setup."))
