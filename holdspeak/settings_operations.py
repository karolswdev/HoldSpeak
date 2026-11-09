"""The Settings window's credential verbs on the one declared contract (2026-11-11).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one
``CredentialService`` verb once: its call, its HTTP method and path. The
routes are produced by ``web/routes/system/settings_secrets.py`` through
``OperationRegistry.invoke``.

A credential is a security surface: every row is owner-only and the owner's
own press (``authority="config"``). No row has an MCP tool, so no agent and
no thread reaches a key. The answer is the redacted state of every secret
(``present``, ``destination``), never key material.
"""
from __future__ import annotations

from typing import Any

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

_PRINCIPAL = "derived by the transport (HTTP auth middleware); owner only"
_REFUSALS = _CONTRACT_REFUSALS + (
    "owner_required",
    "NotFound: unknown secret setting",
    "ValidationError: the value is refused (empty, not a URL, not rotatable)",
)
_RESULT = "success and secrets: the redacted state of every secret (present, destination); never key material"
# Declared, not enforced: an enforced admission runs the kernel path, whose
# receipt records the arguments, and the arguments of a replace hold the key.
_ADMISSION = Admission("admitted", "Config: the owner's press writes one credential in the settings file.", enforced=False)


def _replace(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    body = {key: value for key, value in args.items() if key != "secret_id"}
    return {"success": True, "secrets": service.replace(principal, args.get("secret_id"), args.get("value"), body)}


def _rotate(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return {"success": True, "secrets": service.rotate(principal, args.get("secret_id"))}


def _delete(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return {"success": True, "secrets": service.delete(principal, args.get("secret_id"))}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Any, description: str) -> OperationDescriptor:
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write", result=_RESULT, refusals=_REFUSALS,
        completion="synchronous; GET /api/settings reads the redacted state back",
        exposure=(f"http:{http[0]} {http[1]}",), service="credential_service", method=method,
        owner_only=True, owner_press=True, admission=_ADMISSION,
        call=call, http=http, handler=handler, authority="config",
    )


_S = "/api/settings/secrets/{secret_id}"
SETTINGS_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("settings.secret.replace", "replace", ("PUT", _S), "api_replace_secret", _replace,
        "Replace one credential in the settings file (a token, a key, a webhook)."),
    _op("settings.secret.rotate", "rotate", ("POST", _S + "/rotate"), "api_rotate_secret", _rotate,
        "Rotate one rotatable credential (the web token, the device key, the Telegram pairing code)."),
    _op("settings.secret.delete", "delete", ("DELETE", _S), "api_delete_secret", _delete,
        "Remove one credential from the settings file."),
)


__all__ = ["SETTINGS_OPERATIONS"]
