"""Work attempt routes (HS-94-04).

The §10 attempt surface: ``POST /api/delivery/attempts`` attaches
exact work with explicit refs (provenance is always ``manual`` here —
a client cannot mint launch/rider/contract provenance), and
``GET /api/delivery/attempts`` projects the durable rows with states,
provenance, and replayable history. Reads sweep the emitted rider
claims first (bounded, best-effort) so an agent whose hooks claimed a
Story appears as an exact attempt without any write from the client.

The §12/§13 rules ride every handler: refusals are typed and
path-free, wire rows carry opaque IDs only, and blocking work runs
off the event loop (the Phase-85 rule). Service assembly is lazy so
importing/mounting the router has no side effects. 2026-11-09 (one
contract): both routes are produced from the ``delivery.attempts`` and
``delivery.attempt_create`` rows; the bodies are
``DeliveryService.list_attempts`` and ``create_attempt``.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..context import WebContext
from . import delivery_declared


def build_delivery_attempts_router(ctx: WebContext) -> APIRouter:
    """The attempt routes; the attempt service, the launch sweep and their
    test seams live on ``ctx.delivery_service`` (``DeliveryService.configure``)."""
    return delivery_declared.router(
        ctx, ("delivery.attempt_create", "delivery.attempts"), module=__name__,
    )
