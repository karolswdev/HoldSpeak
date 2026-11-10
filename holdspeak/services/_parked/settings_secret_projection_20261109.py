# Parked: Settings uses CredentialService's one secret map and redaction projection.
from __future__ import annotations
from typing import Any

SECRET_PATHS = {
    "web_token": ("meeting", "web_auth_token"),
    "device_psk": ("device", "psk"),
    "telegram_bot_token": ("cadence_telegram", "bot_token"),
    "telegram_pairing_code": ("cadence_telegram", "pairing_code"),
    "failure_webhook_url": ("meeting", "intel_retry_failure_webhook_url"),
    "failure_webhook_credential": (
        "meeting",
        "intel_retry_failure_webhook_header_value",
    ),
    "companion_webhook_url": ("meeting", "companion_webhook_url"),
}


def redacted_settings(
    config: Config, *, include_meeting_placement: bool = True
) -> dict[str, Any]:
    """Return settings safe for transport.

    ``include_meeting_placement`` is intentionally decided by the settings
    service's per-family migration marker.  Once Meeting routes are assigned,
    recalculating this legacy placement projection would be a fresh mutable
    selector hidden inside a harmless-looking GET.
    """
    from holdspeak.config import (
        LEGACY_ENDPOINT_FIELDS,
        MACHINE_ID_KEY,
        calendar_sources_summary,
        calendar_subscription_summary,
    )

    payload = deepcopy(config.to_dict())
    # HS-200-41: the machine identity is custody's answer to "same desk?", not
    # a setting anyone configures. It is opaque and it stays on the hub — the
    # ask-task DTO carries the here/elsewhere verdict and never the token, and
    # this is the other wire it would otherwise ride out on.
    payload.pop(MACHINE_ID_KEY, None)
    cal = payload.get("calendar", {})
    if isinstance(cal, dict) and "subscription" not in cal:
        cal["subscription"] = cal["sources"][0]["url"] if cal.get("sources") else ""
    payload[REVISION_KEY] = settings_revision(config)
    # HS-146-03 retirement: _calendar_subscription is the legacy single-source
    # fact kept alive for SettingsCore.tsx, the walk script, and e2e seeds until
    # story 03 retires it. _calendar_sources is the canonical per-source truth.
    payload[CALENDAR_SUBSCRIPTION_KEY] = (
        calendar_subscription_summary(config.calendar.sources[0].url)
        if config.calendar.sources
        else calendar_subscription_summary("")
    )
    payload[CALENDAR_SOURCES_KEY] = calendar_sources_summary(config.calendar.sources)
    # HS-201: ordinary Web Record does not run live meeting analysis. Keep the
    # legacy persisted knob out of the wire's active posture; a later explicit
    # summary route owns any analysis request.
    meeting_payload = payload.get("meeting")
    if isinstance(meeting_payload, dict):
        meeting_payload["intel_enabled"] = False
        # Keep the dataclass byte so old config files load, but never expose
        # the retired Settings webhook field.
        meeting_payload.pop("slack_webhook_url", None)
    if include_meeting_placement:
        # The provenance rides both the read and the write's echo, so a surface
        # that changes the dial sees the new placement without a reload.
        payload[PLACEMENT_KEY] = {"meeting": meeting_placement_summary(config)}
    for path, fields in LEGACY_ENDPOINT_FIELDS.items():
        node: Any = payload
        for part in path.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict):
            for field in fields:
                node.pop(field, None)
    states = {}
    for secret_id, (section, field) in SECRET_PATHS.items():
        section_data = payload.get(section)
        if not isinstance(section_data, dict):
            continue
        value = str(section_data.pop(field, "") or "")
        state = {"configured": bool(value)}
        if secret_id in {
            "failure_webhook_url",
            "companion_webhook_url",
        }:
            host = urlparse(value).hostname
            if host:
                state["destination"] = host.lower()
        states[secret_id] = state
    payload["_secrets"] = states
    # Calls (2026-10-28): the passphrase is write only; the read says whether
    # one is set.
    calls_payload = payload.get("calls")
    if isinstance(calls_payload, dict):
        calls_payload["passphrase_set"] = bool(calls_payload.pop("passphrase", ""))
        # Phone (2026-10-28): the faces ask the hub's phone only when it is
        # on (HOLDSPEAK_PHONE=off mounts no /api/phone route: no 404 read).
        from ..phone import phone_on

        calls_payload["phone_on"] = phone_on()
        # The Line (2026-10-29): its two secrets live in the hub's keystore;
        # the read says where each one is, never its value.
        line_payload = calls_payload.get("line")
        if isinstance(line_payload, dict):
            from ..line import secrets as line_secrets

            account = line_payload.get("account")
            if isinstance(account, dict):
                account.pop("password", None)
            line_payload.pop("telnyx_api_key", None)
            line_payload["secrets"] = line_secrets.presence()
    return payload


def strip_secret_mutations(payload: dict[str, Any]) -> dict[str, Any]:
    clean = deepcopy(payload)
    clean.pop("_secrets", None)
    for section, field in SECRET_PATHS.values():
        if isinstance(clean.get(section), dict):
            clean[section].pop(field, None)
    if isinstance(clean.get("meeting"), dict):
        clean["meeting"].pop("intel_retry_failure_webhook_header_name", None)
        # A stale Settings client may echo this retained field. It is ignored
        # on writes even after the credential registration is removed.
        clean["meeting"].pop("slack_webhook_url", None)
    return clean
