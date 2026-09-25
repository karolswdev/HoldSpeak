"""PHILO-7-02: an ADMITTED desk write's envelope = the envelope it had on main + ``operation_id`` + ``receipt``.

``plain`` strips the two kernel fields (checking they are well formed when
present) so a compatibility assertion compares the envelope main gave.
"""
from __future__ import annotations

from typing import Any


def plain(body: Any) -> Any:
    if not isinstance(body, dict) or "receipt" not in body:
        return body
    rest = dict(body)
    receipt, operation_id = rest.pop("receipt"), rest.pop("operation_id")
    assert isinstance(receipt, dict) and receipt.get("operation_id") == operation_id, body
    assert receipt.get("state") in {"succeeded", "refused", "failed"}, receipt
    return rest
