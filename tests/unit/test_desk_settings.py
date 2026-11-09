"""Settings and Setup on the declared contract: the three Codex findings on #2127.

1. ``setup.runtime.probe`` reaches a remote runtime with its stored key: it is
   egress, owner only and his press, so no agent and no thread reaches it.
2. ``settings.update`` is owner only, and a non-owner settings patch that names
   a credential is refused (``credential_in_settings_patch``) before any write.
3. A credential replacement is recorded without its value: no pipeline event
   and no receipt holds the secret, whatever its format.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "settings-owner")
AGENT = Principal(PrincipalKind.AGENT, "launched-agent")
#: No known secret format (no prefix, no key shape): redaction cannot catch it.
SECRET = "plain-words-ochre-lantern-4417"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(fake / "keys.json"))
    monkeypatch.delenv("TELNYX_API_KEY", raising=False)
    monkeypatch.delenv("HOLDSPEAK_LINE_SIP_PASSWORD", raising=False)
    monkeypatch.setattr(config_module, "CONFIG_FILE", fake / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", fake / "holdspeak.db")
    reset_database()
    yield fake
    reset_database()


def _whole_database(db) -> str:
    with db._connection() as conn:
        return "\n".join(conn.iterdump())


def test_the_runtime_probe_is_egress_and_refuses_an_agent() -> None:
    from holdspeak import operations
    from holdspeak.kernel.channel_send import owner_press_operations
    from holdspeak.mcp.tool_authority import EGRESS, TOOL_AUTHORITY
    from holdspeak.operations import OperationOwnerRequired

    probe = {d.name: d for d in operations.DESCRIPTORS}["setup.runtime.probe"]
    assert probe.owner_only and probe.owner_press and probe.authority == "egress"
    assert "No network call" not in probe.description
    assert TOOL_AUTHORITY[probe.tool_name] == EGRESS
    assert "setup.runtime.probe" in owner_press_operations()

    class FakeSetup:
        def test_runtime(self, principal):  # pragma: no cover - an agent never reaches it
            raise AssertionError("an agent reached the probe")

    registry = operations.bind_available({"setup_service": FakeSetup()})
    with pytest.raises(OperationOwnerRequired):
        registry.invoke(AGENT, "setup.runtime.probe", {})


def test_an_agent_cannot_write_a_credential_through_a_settings_patch(home) -> None:
    from holdspeak import operations
    from holdspeak.db import get_database
    from holdspeak.line import secrets
    from holdspeak.operations import OperationOwnerRequired
    from holdspeak.services.errors import ValidationError
    from holdspeak.services.settings_service import SettingsService

    service = SettingsService(get_database())
    registry = operations.bind_available({"settings_service": service})
    patch = {"calls": {"line": {"telnyx_api_key": SECRET, "account": {"password": SECRET}}}}
    # The operation: owner only, on every transport.
    assert {d.name: d for d in operations.DESCRIPTORS}["settings.update"].owner_only
    with pytest.raises(OperationOwnerRequired):
        registry.invoke(AGENT, "settings.update", {"patch": patch})
    # The service: a non-owner patch that names a credential is refused before any write.
    with pytest.raises(ValidationError) as refused:
        service.update_settings(AGENT, patch)
    assert refused.value.code == "credential_in_settings_patch"
    assert "calls.line.telnyx_api_key" in refused.value.detail and SECRET not in refused.value.detail
    with pytest.raises(ValidationError) as refused:
        service.update_settings(AGENT, {"cadence_telegram": {"bot_token": SECRET}})
    assert refused.value.code == "credential_in_settings_patch"
    assert secrets.read(secrets.TELNYX_API_KEY) == "" and secrets.read(secrets.SIP_PASSWORD) == ""
    # The owner's Calls face still saves the Line's secrets through his patch.
    assert service.update_settings(OWNER, patch).get("success") is not False
    assert secrets.read(secrets.TELNYX_API_KEY) == SECRET


def test_a_replaced_secret_is_in_no_pipeline_event_and_no_receipt(home) -> None:
    from holdspeak import operations
    from holdspeak.db import get_database
    from holdspeak.services.credential_service import CredentialService
    from holdspeak.services.settings_service import SettingsService
    from holdspeak.services.sqlite_observer import SQLiteObserver

    db = get_database()
    observer = SQLiteObserver(db._connection)
    registry = operations.bind_available({
        "credential_service": CredentialService(db, observer=observer),
        "settings_service": SettingsService(db, observer=observer),
    })
    answer, receipt = registry.invoke_receipted(
        OWNER, "settings.secret.replace", {"secret_id": "telegram_bot_token", "value": SECRET})
    assert answer["secrets"]["telegram_bot_token"]["configured"] is True
    assert SECRET not in repr(receipt)
    # The owner's Line patch through settings.update: its secret is withheld too.
    registry.invoke(OWNER, "settings.update", {"patch": {"calls": {"line": {"account": {"password": SECRET}}}}})
    with db._connection() as conn:
        rows = conn.execute("SELECT service, method, args_summary FROM pipeline_events").fetchall()
    methods = {(row[0], row[1]) for row in rows}
    assert {("CredentialService", "replace"), ("SettingsService", "update_settings")} <= methods
    replace_args = next(row[2] for row in rows if row[1] == "replace")
    assert "telegram_bot_token" in replace_args and "<withheld>" in replace_args
    assert SECRET not in _whole_database(db)
