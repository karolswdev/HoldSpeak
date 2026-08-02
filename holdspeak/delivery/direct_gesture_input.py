"""Direct-owner-gesture adapter onto the existing ``process.input@1``."""
from __future__ import annotations

import threading
import uuid
from typing import Any

from ..operation_policy import POLICY_VERSION
from ..principals import Principal, PrincipalKind


class ProcessInputRefused(RuntimeError):
    def __init__(self, reason: str, *, result: Any = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.result = result


class _Services:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._targets: Any = None
        self._commands: Any = None
        self._database_id: int | None = None

    def targets(self) -> Any:
        with self._lock:
            if self._targets is None:
                from .. import coder_steering
                from .terminal import TerminalTargetRegistry

                self._targets = TerminalTargetRegistry(
                    resolver=lambda target, runner=None: coder_steering.resolve_pane_identity(
                        target, runner=runner
                    )
                )
            return self._targets

    def commands(self) -> Any:
        from ..db import get_database

        database = get_database()
        with self._lock:
            if self._commands is None or self._database_id != id(database):
                from ..db.delivery_receipts import NodeReceiptLedger
                from .commands import HubCommandService, NodeCommandProcessor

                ledger = database.db_path.with_name(
                    f"{database.db_path.stem}-direct-gesture-node-ledger.db"
                )
                self._commands = HubCommandService(
                    repo=database.delivery_receipts,
                    processor=NodeCommandProcessor(
                        node_id="local",
                        targets=self.targets(),
                        ledger=NodeReceiptLedger(ledger),
                    ),
                    local_node_id="local",
                )
                self._database_id = id(database)
            return self._commands


_SERVICES = _Services()


def submit_process_input_from_owner_gesture(
    *,
    pane: str,
    text: str,
    session_key: str = "",
    agent: str = "",
    principal: Principal | None = None,
) -> dict[str, Any]:
    """Bind one pane generation and synchronously receipt the owner's send."""
    owner = principal or Principal(PrincipalKind.OWNER, "owner-session")
    if owner.kind is not PrincipalKind.OWNER:
        raise ProcessInputRefused("process_input_owner_direct_gesture_required")
    issued = _SERVICES.targets().issue(pane)
    unresolved_reason = f"process_target_{issued.get('status') or 'unresolved'}"
    command_id = str(uuid.uuid4())
    command = {
        "node_id": "local",
        "target_id": issued.get("target_id") or f"unresolved_{command_id[:16]}",
        "target_generation": issued.get("target_generation") or "unresolved",
        "command_id": command_id,
        "operation": {"family": "coder_steering", "verb": "terminal.text"},
        "payload": {
            "session_key": session_key or f"pane:{pane}",
            "text": text,
            "agent": agent,
            "submit": True,
            "grounding_refs": [],
            "expected_pane_id": issued.get("pane_id") or "",
        },
    }
    authority = {
        "outcome": "allowed",
        "authority_basis": "direct_gesture",
        "reason_code": "dictation_commit_allowed",
        "policy_version": POLICY_VERSION,
        "mode": "direct",
    }
    response = _SERVICES.commands().submit_process_input(
        command,
        owner,
        authority_snapshot=authority,
        include_result=True,
    )
    result = dict(response.get("result") or {})
    result.update(
        {
            "command_id": response["command_id"],
            "operation_id": response["operation_id"],
            "receipt": response.get("receipt"),
            "target_ref": f"process:{command['target_id']}",
            "expected_generation": command["target_generation"],
        }
    )
    receipt = response.get("receipt") or {}
    if str(receipt.get("state") or "") != "succeeded":
        fallback_reason = (
            unresolved_reason
            if issued.get("status") != "issued"
            else "process_input_refused"
        )
        raise ProcessInputRefused(
            str(receipt.get("outcome") or fallback_reason),
            result=result,
        )
    return result


__all__ = ["ProcessInputRefused", "submit_process_input_from_owner_gesture"]
