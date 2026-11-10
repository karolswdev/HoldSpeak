# Parked: the Line writes credentials through CredentialService, never a settings patch.
from __future__ import annotations
from typing import Any

def _keep_line_secrets(calls_data: dict[str, Any]) -> str:
    """The Line (2026-10-29): ``calls.line.account.password`` (the SIP
    password) and ``calls.line.telnyx_api_key`` are write only: each goes into
    the hub's keystore and never into the config file. A value of ``null``
    forgets it. The read's ``secrets`` is not a field. An error, or ``""``."""
    line = calls_data.get("line")
    if not isinstance(line, dict):
        return ""
    from ..line import secrets as line_secrets

    line.pop("secrets", None)
    account = line.get("account") if isinstance(line.get("account"), dict) else {}
    writes = []
    for slot, path in line_secrets.SETTINGS_FIELDS.items():
        node: Any = calls_data
        for part in path[1:-1]:
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict) and path[-1] in node:
            writes.append((slot, node.pop(path[-1])))
    for slot, value in writes:
        if value is not None and not str(value).strip():
            continue  # an empty field keeps the saved secret
        try:
            line_secrets.write(slot, None if value is None else str(value).strip())
        except Exception:
            return "The keystore is not available on this machine, so the secret was not saved."
        if slot == line_secrets.SIP_PASSWORD:
            account["password_ref"] = slot if value is not None else ""
    return ""
