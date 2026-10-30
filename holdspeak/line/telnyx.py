"""A thin Telnyx API v2 client for the Line's setup (LINE-3b, LINE design §8).

Bearer the provisioning key from the hub's keystore
(``calls.line.telnyx_api_key``, :mod:`holdspeak.line.secrets`). Every call has
a timeout, and every log line and error goes through the redactor with the
key itself taken out first: this module never prints the key.

The field names are Telnyx's OpenAPI spec
(``team-telnyx/openapi`` ``openapi/spec3.json``, read 2026-10-29):

- ``GET  /balance``                                        → ``data.{balance, available_credit, currency}``
- ``GET  /outbound_voice_profiles?filter[name][contains]`` and ``POST /outbound_voice_profiles {name}``
- ``GET  /credential_connections?filter[connection_name][contains]``,
  ``POST /credential_connections {connection_name, user_name, password, sip_uri_calling_preference, outbound}``,
  ``PATCH /credential_connections/{id} {password}``
- ``GET  /available_phone_numbers?filter[country_code]&filter[national_destination_code]&filter[features]&filter[limit]``
  → ``data[].{phone_number, cost_information.{monthly_cost, upfront_cost, currency}}``
- ``POST /number_orders {phone_numbers: [{phone_number}], connection_id}`` (money: the owner's press only)
- ``GET  /phone_numbers?filter[phone_number]`` and ``PATCH /phone_numbers/{id} {connection_id}``

``HOLDSPEAK_TELNYX_API`` names another base URL (the tests' fake Telnyx,
``tests/fixtures/fake_telnyx.py``). Tests never reach api.telnyx.com.
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from ..logging_config import get_logger
from ..redaction import redact_error

log = get_logger("line.telnyx")

API_ENV = "HOLDSPEAK_TELNYX_API"
DEFAULT_API = "https://api.telnyx.com/v2"
TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def api_base() -> str:
    return (os.environ.get(API_ENV, "").strip() or DEFAULT_API).rstrip("/")


class TelnyxError(RuntimeError):
    """A Telnyx answer that is not a success, or no answer. ``status`` is the
    HTTP status (0: no answer); ``detail`` is Telnyx's own words, redacted."""

    def __init__(self, status: int, detail: str, *, code: str = "") -> None:
        super().__init__(detail)
        self.status, self.detail, self.code = int(status), detail, code


class Telnyx:
    def __init__(self, key: str, *, base: Optional[str] = None, transport: Optional[httpx.BaseTransport] = None) -> None:
        if not key:
            raise ValueError("a Telnyx API key is required")
        self._key = key
        self._client = httpx.Client(base_url=base or api_base(), timeout=TIMEOUT, transport=transport,
                                    headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Telnyx":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _safe(self, text: object) -> str:
        return redact_error(str(text).replace(self._key, "[redacted]"), 300)

    def _call(self, method: str, path: str, *, params: Any = None, body: Any = None) -> Any:
        try:
            answer = self._client.request(method, path, params=params, json=body)
        except httpx.HTTPError as exc:
            detail = self._safe(f"{type(exc).__name__}: {exc}")
            log.warning(f"telnyx {method} {path}: no answer ({detail})")
            raise TelnyxError(0, detail) from None
        if answer.status_code >= 400:
            title, code = "", ""
            try:
                errors = (answer.json() or {}).get("errors") or []
                first = errors[0] if errors and isinstance(errors[0], dict) else {}
                title = str(first.get("detail") or first.get("title") or "")
                code = str(first.get("code") or "")
            except ValueError:
                title = answer.text[:200]
            detail = self._safe(title or f"HTTP {answer.status_code}")
            log.warning(f"telnyx {method} {path}: {answer.status_code} {detail}")
            raise TelnyxError(answer.status_code, detail, code=code)
        try:
            return answer.json() if answer.content else {}
        except ValueError:
            raise TelnyxError(answer.status_code, "Telnyx did not answer with JSON") from None

    # ── reads ────────────────────────────────────────────────────────

    def balance(self) -> dict[str, Any]:
        return dict(self._call("GET", "/balance").get("data") or {})

    def find_profile(self, name: str) -> Optional[dict[str, Any]]:
        rows = self._call("GET", "/outbound_voice_profiles", params={"filter[name][contains]": name}).get("data") or []
        return next((dict(row) for row in rows if row.get("name") == name), None)

    def find_connection(self, name: str) -> Optional[dict[str, Any]]:
        rows = self._call("GET", "/credential_connections",
                          params={"filter[connection_name][contains]": name}).get("data") or []
        return next((dict(row) for row in rows if row.get("connection_name") == name), None)

    def available_numbers(self, area: str, *, country: str = "US", limit: int = 10) -> list[dict[str, Any]]:
        params = [("filter[country_code]", country), ("filter[features]", "voice"), ("filter[limit]", str(limit))]
        if area:
            params.append(("filter[national_destination_code]", area))
        return [dict(row) for row in self._call("GET", "/available_phone_numbers", params=params).get("data") or []]

    def find_number(self, phone_number: str) -> Optional[dict[str, Any]]:
        digits = "".join(ch for ch in phone_number if ch.isdigit())
        rows = self._call("GET", "/phone_numbers", params={"filter[phone_number]": digits}).get("data") or []
        return next((dict(row) for row in rows if row.get("phone_number") == phone_number), None)

    # ── writes ───────────────────────────────────────────────────────

    def create_profile(self, name: str) -> dict[str, Any]:
        return dict(self._call("POST", "/outbound_voice_profiles", body={"name": name}).get("data") or {})

    def create_connection(self, *, name: str, user: str, password: str, profile_id: str) -> dict[str, Any]:
        body = {"connection_name": name, "user_name": user, "password": password,
                "sip_uri_calling_preference": "disabled",
                "outbound": {"outbound_voice_profile_id": profile_id}}
        return dict(self._call("POST", "/credential_connections", body=body).get("data") or {})

    def set_connection_password(self, connection_id: str, password: str) -> dict[str, Any]:
        return dict(self._call("PATCH", f"/credential_connections/{connection_id}",
                               body={"password": password}).get("data") or {})

    def order_number(self, phone_number: str, *, connection_id: str = "") -> dict[str, Any]:
        """BUYS the number (money). Only the owner's press reaches this."""
        body: dict[str, Any] = {"phone_numbers": [{"phone_number": phone_number}]}
        if connection_id:
            body["connection_id"] = connection_id
        return dict(self._call("POST", "/number_orders", body=body).get("data") or {})

    def assign(self, number_id: str, connection_id: str) -> dict[str, Any]:
        return dict(self._call("PATCH", f"/phone_numbers/{number_id}",
                               body={"connection_id": connection_id}).get("data") or {})


__all__ = ["API_ENV", "DEFAULT_API", "Telnyx", "TelnyxError", "api_base"]
