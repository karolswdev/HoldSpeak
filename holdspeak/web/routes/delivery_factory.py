"""The factory's declared profile, discovery and owner launch routes."""
from __future__ import annotations
from fastapi import APIRouter
from ..context import WebContext
from . import delivery_declared


def build_delivery_factory_router(ctx: WebContext) -> APIRouter:
    return delivery_declared.router(ctx, ("delivery.factory_profiles", "delivery.factory_discover",
        "delivery.factory_launch"), module=__name__)
