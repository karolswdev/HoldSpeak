"""The hub's delivery construction: the node link, terminal targets and commands.

Split from :mod:`holdspeak.runtime.hub_composition` (the density budget). It
fills the delivery fields of the :class:`HubComposition` that
:func:`~holdspeak.runtime.hub_composition.compose_hub` built.
"""

from __future__ import annotations

from typing import Optional

from holdspeak.runtime.hub_composition import HubComposition


def compose_delivery(hub: HubComposition, *, auth_token: Optional[str]) -> HubComposition:
    """Build the delivery link, terminal targets and the hub command service.

    One shared NodeLinkState feeds both the node link and the terminal command
    claim leg: commands issued at the hub reach a remote node through the same
    authenticated long-poll. The terminal command service is the node router's
    command_source. ``_create_app`` calls this at the point it built them
    before, between the router mounts.
    """
    from holdspeak.delivery.node_link import NodeLinkState
    from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
    from holdspeak.delivery.terminal import TerminalTargetRegistry
    from holdspeak.db import get_database as _get_delivery_db
    from holdspeak.db.delivery_receipts import NodeReceiptLedger

    # The pairing store compose_hub gave the mesh service: one custody handle.
    _delivery_link = NodeLinkState(hub.node_token_store, web_token=auth_token)
    _delivery_targets = TerminalTargetRegistry()
    hub.signin_targets["targets"] = _delivery_targets
    _delivery_live = hub.web_ctx.delivery_service.terminal_live_service(
        targets=_delivery_targets
    )
    from holdspeak.kernel.runtime import _service as _kernel_service

    _delivery_cmd = HubCommandService(
        repo=_get_delivery_db().delivery_receipts,
        processor=NodeCommandProcessor(
            node_id="local",
            targets=_delivery_targets,
            ledger=NodeReceiptLedger(None),
        ),
        local_node_id="local",
        kernel_broker=_kernel_service(),
    )
    _delivery_link.command_source = _delivery_cmd.claim_for_node

    hub.delivery_link = _delivery_link
    hub.delivery_targets = _delivery_targets
    hub.delivery_cmd = _delivery_cmd
    hub.delivery_live = _delivery_live
    return hub
