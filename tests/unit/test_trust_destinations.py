from __future__ import annotations

from holdspeak.commands.doctor import _check_trust_destinations
from holdspeak.config import Config
from holdspeak.trust_destinations import destination_inventory, destination_registry


REQUIRED = {
    "id", "name", "operation", "enabled", "destination", "boundary", "data_class",
    "authority_basis", "background_ability", "revoke_action", "last_receipt",
}


def test_registry_is_complete_and_inventory_is_secret_free() -> None:
    config = Config()
    config.meeting.slack_webhook_url = "https://hooks.slack.test/services/SECRET"
    config.meeting.companion_webhook_url = "https://example.test/SECRET"
    config.meeting.intel_retry_failure_webhook_url = "https://alerts.test/SECRET"
    config.cadence_telegram.enabled = True
    config.cadence_telegram.bot_token = "TELEGRAM-SECRET"
    inventory = destination_inventory(config)
    assert len(inventory) == len(destination_registry())
    assert all(REQUIRED <= row.keys() for row in inventory)
    rendered = repr(inventory)
    for secret in ("services/SECRET", "example.test/SECRET", "alerts.test/SECRET", "TELEGRAM-SECRET"):
        assert secret not in rendered


def test_doctor_uses_registry_names_for_enabled_destinations() -> None:
    config = Config()
    config.meeting.slack_webhook_url = "https://hooks.slack.com/services/a/b/c"
    check = _check_trust_destinations(config)
    assert check.status == "WARN"
    assert next(row["name"] for row in destination_registry() if row["id"] == "slack") in check.detail


def test_default_inventory_has_no_external_destination_enabled() -> None:
    config = Config()
    assert not any(row["enabled"] for row in destination_inventory(config))
    assert _check_trust_destinations(config).status == "PASS"
