"""The Line port: wire, enrolment, state and Telnyx on the hub's one CallsService.

HTTP carries a node credential as a held input. The code exchange stays public
and HTTP-only: possession of an unspent owner-minted code is its authority.
An agent cannot use either protocol. No credential storage changes here.
"""
from __future__ import annotations

from typing import Any

from ..logging_config import get_logger
from ..principals import PrincipalKind
from ..services.errors import ServiceError
from . import line_on, setup
from .enrol import CODES, EnrolError, enrolled, redeem, revoke, wire_node
from .hub import LINE_HUB

log = get_logger("line.service")


def _refused(reason: str, words: str, status: int) -> ServiceError:
    return ServiceError(reason, words, context={"status": status})


class LineService:
    def __init__(self, calls: Any) -> None:
        self.calls = calls
        self.store: Any = None

    def configure(self, *, store: Any) -> None:
        """The composition's existing node store, shared with delivery and mesh."""
        self.store = store

    @staticmethod
    def _on() -> None:
        if not line_on():
            raise _refused("off", "line_off", 409)

    @staticmethod
    def _node(principal: Any, body: dict[str, Any], credential: Any) -> str:
        from ..operations import OperationOwnerRequired

        kind = getattr(principal, "kind", None)
        if kind not in (PrincipalKind.OWNER, PrincipalKind.LINE_NODE):
            raise OperationOwnerRequired("calls.line.wire")
        # A Line principal must carry the authenticated credential from the
        # edge, never a node name supplied by the body alone.
        if kind is PrincipalKind.LINE_NODE and (credential is None or credential.scope != "calls.line"):
            raise _refused("usage", "node is required", 400)
        named = str(body.get("node") or "").strip()[:64]
        node = wire_node(credential, named) or ""
        if not node:
            raise _refused("usage", "node is required", 400)
        return node

    def hello(self, principal: Any, body: dict[str, Any], credential: Any) -> dict[str, Any]:
        self._on()
        node = self._node(principal, body, credential)
        return LINE_HUB.hello(
            node, lines=body.get("lines") if isinstance(body.get("lines"), list) else [],
            version=str(body.get("version") or ""),
            active_call=body.get("active_call") if isinstance(body.get("active_call"), dict) else None,
            machine=body.get("machine") if isinstance(body.get("machine"), dict) else None)

    def events(self, principal: Any, body: dict[str, Any], credential: Any) -> dict[str, Any]:
        self._on()
        node = self._node(principal, body, credential)
        events = [e for e in (body.get("events") or []) if isinstance(e, dict)][:200]
        return {"acked": LINE_HUB.post_events(node, events)}

    def next(self, principal: Any, body: dict[str, Any], credential: Any) -> Any:
        """Validate off-loop; the transport awaits the poll on its own loop.

        Cancellation still removes the waiter's future in LineHub.next.
        """
        self._on()
        node = self._node(principal, body, credential)
        try:
            after, wait = int(body.get("after") or 0), float(body.get("wait_s") or 0)
        except (TypeError, ValueError):
            raise _refused("usage", "after and wait_s are numbers", 400) from None
        return LINE_HUB.next(node, after=after, wait=wait)

    def codes(self, node: str, hub: str) -> dict[str, Any]:
        try:
            minted = CODES.mint(node)
        except EnrolError as exc:
            raise _refused(exc.reason, str(exc), 400) from exc
        minted["hub"] = hub
        minted["command"] = f"holdspeak line enrol --hub {hub} --code {minted['code']} --node {minted['node']}"
        return minted

    def enrol(self, principal: Any, code: str) -> dict[str, Any]:
        from ..operations import OperationOwnerRequired

        if getattr(principal, "kind", None) not in (PrincipalKind.NONE, PrincipalKind.OWNER):
            raise OperationOwnerRequired("calls.line.enrol")
        self._on()
        if self.store is None:
            raise _refused("no_store", "This hub has no node store.", 409)
        try:
            answer = redeem(CODES, self.store, code)
        except EnrolError as exc:
            raise _refused(exc.reason, str(exc), 401) from exc
        log.info(f"line node enrolled: {answer['node']}")
        return answer

    def nodes(self) -> dict[str, Any]:
        from ..calls.service import _settings, line_status
        from .adapter import Line

        cfg = _settings()
        rows = []
        for row in enrolled(self.store):
            status = line_status(Line(row["node"]), cfg)
            rows.append({**row, "state": status["state"], "words": status["words"],
                         "machine": status.get("machine") or {}})
        return {"nodes": rows}

    def revoke(self, node: str) -> dict[str, Any]:
        try:
            done = self.store is not None and revoke(self.store, node)
        except EnrolError as exc:
            raise _refused(exc.reason, str(exc), 400) from exc
        if not done:
            raise _refused("not_found", "No such Line node.", 404)
        return {"node": node, "revoked": True}

    def status(self) -> dict[str, Any]:
        from ..calls.service import _settings, line_status

        return line_status(self.calls._phone_fn() if line_on() else None, _settings())

    def telnyx_status(self) -> dict[str, Any]:
        self._on()
        return setup.TELNYX_SETUP.status()

    def telnyx_connect(self) -> dict[str, Any]:
        self._on()
        return setup.TELNYX_SETUP.connect()

    def telnyx_numbers(self, area: str) -> dict[str, Any]:
        self._on()
        return setup.TELNYX_SETUP.numbers(area)

    def telnyx_buy(self, principal: Any, phone_number: str, quote: str) -> dict[str, Any]:
        self._on()
        return setup.TELNYX_SETUP.buy(principal, phone_number, quote)

    def telnyx_assign(self, phone_number: str) -> dict[str, Any]:
        self._on()
        return setup.TELNYX_SETUP.assign(phone_number)
